from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .models import Autorizacion, RegistroAcceso, Discrepancia, SolicitudExtension
from accounts.decorators import role_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from datetime import datetime, timedelta
from django.utils import timezone

# Create your views here.

@login_required
@role_required('oficial_acceso')
def dashboard(request):
    # Autorizaciones activas
    autorizaciones_list = Autorizacion.objects.filter(
        estado='activa'
    ).select_related('solicitud').order_by('-valida_hasta')
    
    # Registros de acceso procesados por este oficial
    registros_list = RegistroAcceso.objects.filter(
        oficial_acceso=request.user
    ).select_related('autorizacion').order_by('-timestamp')
    
    # Estadísticas del día actual
    today = datetime.now().date()
    
    # Estadísticas generales
    stats = {
        'autorizaciones_activas': autorizaciones_list.count(),
        'autorizaciones_vencen_hoy': autorizaciones_list.filter(
            valida_hasta__date=today
        ).count(),
        'accesos_procesados_hoy': registros_list.filter(
            timestamp__date=today
        ).count(),
        'ingresos_autorizados_hoy': registros_list.filter(
            timestamp__date=today,
            tipo_acceso='ingreso',
            estado='autorizado'
        ).count(),
        'salidas_registradas_hoy': registros_list.filter(
            timestamp__date=today,
            tipo_acceso='salida',
            estado='autorizado'
        ).count(),
        'accesos_denegados_hoy': registros_list.filter(
            timestamp__date=today,
            estado='denegado'
        ).count(),
        'discrepancias_reportadas': Discrepancia.objects.filter(
            reportada_por=request.user,
            creada_el__date=today
        ).count(),
    }
    
    # Calcular porcentaje de autorización
    if stats['accesos_procesados_hoy'] > 0:
        stats['porcentaje_autorizacion'] = round(
            ((stats['ingresos_autorizados_hoy'] + stats['salidas_registradas_hoy']) / 
             stats['accesos_procesados_hoy']) * 100
        )
    else:
        stats['porcentaje_autorizacion'] = 0
    
    # Autorizaciones que vencen pronto (próximas 2 horas)
    vencen_pronto = autorizaciones_list.filter(
        valida_hasta__lte=datetime.now() + timedelta(hours=2)
    ).count()
    stats['vencen_pronto'] = vencen_pronto
    
    # Paginación
    paginator_aut = Paginator(autorizaciones_list, 10)
    page_aut = request.GET.get('aut_page')
    autorizaciones = paginator_aut.get_page(page_aut)

    paginator_reg = Paginator(registros_list, 10)
    page_reg = request.GET.get('reg_page')
    ultimos_registros = paginator_reg.get_page(page_reg)

    context = {
        'user': request.user,
        'autorizaciones': autorizaciones,
        'ultimos_registros': ultimos_registros,
        'stats': stats
    }

    return render(request, 'control_acceso/dashboard.html', context)

@login_required
@role_required('oficial_acceso')
def verificar_qr(request):
    """Vista para verificar códigos QR escaneados"""
    autorizacion = None
    error_message = None

    # Aceptar código por GET (desde escaneo) o POST (desde formulario)
    codigo_qr = request.GET.get('codigo', '') or request.POST.get('codigo_qr', '')
    codigo_qr = codigo_qr.strip()

    if codigo_qr:
        try:
            import json
            # Intentar decodificar como JSON (QR completo)
            try:
                qr_data = json.loads(codigo_qr)
                codigo = qr_data.get('codigo')
                uuid_code = qr_data.get('uuid')
            except json.JSONDecodeError:
                # Si no es JSON, asumir que es solo el código
                codigo = codigo_qr
                uuid_code = None

            # Buscar autorización
            if uuid_code:
                autorizacion = Autorizacion.objects.filter(uuid=uuid_code).first()
            else:
                autorizacion = Autorizacion.objects.filter(codigo=codigo).first()

            if not autorizacion:
                error_message = "Código de autorización no encontrado"
            else:
                # Actualizar estado si está vencida
                if autorizacion.estado == 'activa' and autorizacion.valida_hasta < timezone.now():
                    autorizacion.estado = 'vencida'
                    autorizacion.save()

                # Verificar estado - pero permitir ver la información
                if autorizacion.estado != 'activa':
                    error_message = f"⚠️ Autorización {autorizacion.get_estado_display()}"
                elif autorizacion.valida_desde > timezone.now():
                    error_message = "⏳ Autorización aún no válida (inicia el {})".format(
                        autorizacion.valida_desde.strftime('%d/%m/%Y %H:%M')
                    )

        except Exception as e:
            error_message = f"Error al procesar código QR: {str(e)}"
    
    context = {
        'autorizacion': autorizacion,
        'error_message': error_message,
        'user': request.user
    }
    return render(request, 'control_acceso/verificar_qr.html', context)

@login_required
@require_POST
@role_required('oficial_acceso')
def autorizar_ingreso(request, codigo):
    """Autorizar el ingreso de un vehículo"""
    try:
        autorizacion = Autorizacion.objects.get(codigo=codigo, estado='activa')
        
        # Validar que esté vigente
        if autorizacion.valida_hasta < timezone.now():
            autorizacion.estado = 'vencida'
            autorizacion.save()
            messages.error(request, "Autorización vencida")
            return redirect('control_acceso:dashboard')
        
        # Obtener datos del formulario
        vehiculo_placa = request.POST.get('vehiculo_placa', '')
        conductor_nombre = request.POST.get('conductor_nombre', '')
        observaciones = request.POST.get('observaciones', '')
        
        # Crear registro de acceso
        registro = RegistroAcceso.objects.create(
            autorizacion=autorizacion,
            oficial_acceso=request.user,
            tipo_acceso='ingreso',
            vehiculo_placa=vehiculo_placa,
            conductor_nombre=conductor_nombre,
            estado='autorizado',
            documento_verificado=True,
            vehiculo_verificado=True,
            conductor_verificado=True,
            observaciones=observaciones,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, f"¡Ingreso autorizado exitosamente! Registro: {registro.id}")
        
    except Autorizacion.DoesNotExist:
        messages.error(request, "Autorización no encontrada o inactiva")
    except Exception as e:
        messages.error(request, f"Error al autorizar ingreso: {str(e)}")
    
    return redirect('control_acceso:dashboard')

@login_required
@require_POST
@role_required('oficial_acceso')
def denegar_acceso(request, codigo):
    """Denegar el acceso de un vehículo"""
    try:
        autorizacion = Autorizacion.objects.get(codigo=codigo)
        
        # Obtener datos del formulario
        vehiculo_placa = request.POST.get('vehiculo_placa', '')
        conductor_nombre = request.POST.get('conductor_nombre', '')
        motivo_denegacion = request.POST.get('motivo_denegacion', '')
        
        # Crear registro de acceso denegado
        registro = RegistroAcceso.objects.create(
            autorizacion=autorizacion,
            oficial_acceso=request.user,
            tipo_acceso='ingreso',
            vehiculo_placa=vehiculo_placa,
            conductor_nombre=conductor_nombre,
            estado='denegado',
            motivo_denegacion=motivo_denegacion,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.warning(request, f"Acceso denegado. Registro: {registro.id}")
        
    except Autorizacion.DoesNotExist:
        messages.error(request, "Autorización no encontrada")
    except Exception as e:
        messages.error(request, f"Error al denegar acceso: {str(e)}")
    
    return redirect('control_acceso:dashboard')

@login_required
@require_POST
@role_required('oficial_acceso')
def reportar_discrepancia(request, codigo):
    """Reportar una discrepancia durante el control de acceso"""
    try:
        autorizacion = Autorizacion.objects.get(codigo=codigo)
        
        # Crear registro de acceso primero
        vehiculo_placa = request.POST.get('vehiculo_placa', '')
        conductor_nombre = request.POST.get('conductor_nombre', '')
        
        registro = RegistroAcceso.objects.create(
            autorizacion=autorizacion,
            oficial_acceso=request.user,
            tipo_acceso='ingreso',
            vehiculo_placa=vehiculo_placa,
            conductor_nombre=conductor_nombre,
            estado='pendiente',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Crear discrepancia
        tipo_discrepancia = request.POST.get('tipo_discrepancia', 'otros')
        descripcion = request.POST.get('descripcion', '')
        
        discrepancia = Discrepancia.objects.create(
            registro_acceso=registro,
            reportada_por=request.user,
            tipo_discrepancia=tipo_discrepancia,
            descripcion=descripcion
        )
        
        messages.warning(request, f"Discrepancia reportada: {discrepancia.codigo}")
        
    except Autorizacion.DoesNotExist:
        messages.error(request, "Autorización no encontrada")
    except Exception as e:
        messages.error(request, f"Error al reportar discrepancia: {str(e)}")

    return redirect('control_acceso:dashboard')

@login_required
@role_required('oficial_acceso')
def listar_autorizaciones(request):
    """Vista para listar todas las autorizaciones activas"""

    # Obtener parámetros de filtro
    busqueda = request.GET.get('q', '')
    estado_filtro = request.GET.get('estado', '')

    # Consulta base - todas las autorizaciones
    autorizaciones_queryset = Autorizacion.objects.select_related(
        'solicitud', 'solicitud__empresa', 'solicitud__solicitante'
    ).order_by('-creada_el')

    # Aplicar filtros de búsqueda
    if busqueda:
        autorizaciones_queryset = autorizaciones_queryset.filter(
            Q(codigo__icontains=busqueda) |
            Q(empresa_nombre__icontains=busqueda) |
            Q(empresa_rnc__icontains=busqueda) |
            Q(representante_nombre__icontains=busqueda) |
            Q(puerto_nombre__icontains=busqueda)
        )

    # Aplicar filtro por estado
    if estado_filtro and estado_filtro != 'todas':
        autorizaciones_queryset = autorizaciones_queryset.filter(estado=estado_filtro)
    elif not estado_filtro:
        # Por defecto mostrar solo las activas
        autorizaciones_queryset = autorizaciones_queryset.filter(estado='activa')

    # Estadísticas
    today = datetime.now().date()
    stats = {
        'total': Autorizacion.objects.count(),
        'activas': Autorizacion.objects.filter(estado='activa').count(),
        'vencidas': Autorizacion.objects.filter(estado='vencida').count(),
        'revocadas': Autorizacion.objects.filter(estado='revocada').count(),
        'vencen_hoy': autorizaciones_queryset.filter(
            estado='activa',
            valida_hasta__date=today
        ).count(),
    }

    # Paginación
    per_page = request.GET.get('per_page', '25')
    try:
        per_page = int(per_page)
        if per_page not in [10, 25, 50, 100]:
            per_page = 25
    except (ValueError, TypeError):
        per_page = 25

    paginator = Paginator(autorizaciones_queryset, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'user': request.user,
        'autorizaciones': page_obj,
        'stats': stats,
        'busqueda': busqueda,
        'estado_filtro': estado_filtro,
        'is_paginated': page_obj.has_other_pages(),
        'tiene_filtros': bool(busqueda or estado_filtro)
    }

    return render(request, 'control_acceso/listar_autorizaciones.html', context)


# Vista pública para verificar QR (sin login requerido)
def verificar_autorizacion_publica(request, uuid):
    """Vista pública para verificar una autorización escaneando el QR"""
    try:
        autorizacion = Autorizacion.objects.select_related('solicitud', 'solicitud__empresa').get(uuid=uuid)

        # Actualizar estado si está vencida
        autorizacion.actualizar_estado()

        # Verificar vigencia
        ahora = timezone.now()
        es_valida = autorizacion.esta_vigente()

        # Calcular información adicional
        if autorizacion.estado == 'activa':
            if autorizacion.valida_desde > ahora:
                mensaje_estado = "⏳ Autorización programada para el futuro"
                color_estado = "#f39c12"
            elif autorizacion.valida_hasta < ahora:
                mensaje_estado = "⏰ Autorización vencida"
                color_estado = "#e74c3c"
            else:
                mensaje_estado = "✅ Autorización válida y activa"
                color_estado = "#27ae60"
        elif autorizacion.estado == 'vencida':
            mensaje_estado = "⏰ Autorización vencida"
            color_estado = "#e74c3c"
        elif autorizacion.estado == 'revocada':
            mensaje_estado = "🚫 Autorización revocada"
            color_estado = "#c0392b"
        else:
            mensaje_estado = f"ℹ️ Estado: {autorizacion.get_estado_display()}"
            color_estado = "#95a5a6"

        context = {
            'autorizacion': autorizacion,
            'es_valida': es_valida,
            'mensaje_estado': mensaje_estado,
            'color_estado': color_estado,
            'dias_restantes': autorizacion.dias_restantes() if es_valida else 0,
            'ahora': ahora,
        }

        return render(request, 'control_acceso/verificar_autorizacion_publica.html', context)

    except Autorizacion.DoesNotExist:
        context = {
            'error': True,
            'mensaje_error': 'Código de autorización no válido o no encontrado',
        }
        return render(request, 'control_acceso/verificar_autorizacion_publica.html', context)


# ============================================================================
# VISTAS PARA EXTENSIÓN DE VALIDEZ
# ============================================================================

@login_required
@role_required('solicitante', 'evaluador', 'supervisor', 'admin_tic')
def solicitar_extension(request, autorizacion_id):
    """Vista para solicitar extensión de validez de una autorización"""
    autorizacion = get_object_or_404(Autorizacion, id=autorizacion_id)

    # Verificar permisos: solicitante solo de su empresa
    if request.user.role == 'solicitante':
        if not request.user.empresa or autorizacion.solicitud.empresa != request.user.empresa:
            messages.error(request, 'No tienes permisos para solicitar extensión de esta autorización.')
            return redirect('solicitudes:mis_autorizaciones')

    # Verificar que la autorización esté activa
    if autorizacion.estado != 'activa':
        messages.error(request, f'No se puede solicitar extensión de una autorización {autorizacion.get_estado_display()}.')
        return redirect('solicitudes:mis_autorizaciones')

    # Verificar si ya tiene una solicitud de extensión pendiente
    if autorizacion.solicitudes_extension.filter(estado='pendiente').exists():
        messages.warning(request, 'Ya existe una solicitud de extensión pendiente para esta autorización.')
        return redirect('solicitudes:mis_autorizaciones')

    if request.method == 'POST':
        fecha_vencimiento_solicitada = request.POST.get('fecha_vencimiento_solicitada')
        motivo = request.POST.get('motivo', '').strip()

        # Validaciones
        if not fecha_vencimiento_solicitada:
            messages.error(request, 'Debes especificar la nueva fecha de vencimiento.')
            return redirect('control_acceso:solicitar_extension', autorizacion_id=autorizacion_id)

        if not motivo or len(motivo) < 20:
            messages.error(request, 'El motivo debe tener al menos 20 caracteres.')
            return redirect('control_acceso:solicitar_extension', autorizacion_id=autorizacion_id)

        try:
            # Convertir fecha
            fecha_nueva = timezone.make_aware(datetime.strptime(fecha_vencimiento_solicitada, '%Y-%m-%dT%H:%M'))

            # Validar que la nueva fecha sea posterior a la actual
            if fecha_nueva <= autorizacion.valida_hasta:
                messages.error(request, 'La nueva fecha debe ser posterior a la fecha de vencimiento actual.')
                return redirect('control_acceso:solicitar_extension', autorizacion_id=autorizacion_id)

            # Crear solicitud de extensión
            solicitud_ext = SolicitudExtension.objects.create(
                autorizacion=autorizacion,
                fecha_vencimiento_actual=autorizacion.valida_hasta,
                fecha_vencimiento_solicitada=fecha_nueva,
                motivo=motivo,
                solicitada_por=request.user
            )

            messages.success(
                request,
                f'Solicitud de extensión creada exitosamente con código {solicitud_ext.codigo}. '
                f'Será revisada por un supervisor.'
            )

            # Enviar notificación por email
            from notificaciones.services.email_service import EmailService
            contexto = {
                'codigo_extension': solicitud_ext.codigo,
                'codigo_autorizacion': autorizacion.codigo,
                'empresa': autorizacion.empresa_nombre,
                'fecha_actual': autorizacion.valida_hasta.strftime('%d/%m/%Y %H:%M'),
                'fecha_solicitada': fecha_nueva.strftime('%d/%m/%Y %H:%M'),
                'dias_extension': solicitud_ext.dias_extension_solicitados,
                'motivo': motivo,
                'solicitada_por': request.user.get_full_name(),
            }

            EmailService.enviar_notificacion(
                codigo_evento='extension_solicitada',
                contexto=contexto,
                destinatarios_roles=['supervisor', 'direccion']
            )

            return redirect('solicitudes:mis_autorizaciones')

        except ValueError:
            messages.error(request, 'Formato de fecha inválido.')
            return redirect('control_acceso:solicitar_extension', autorizacion_id=autorizacion_id)

    # GET - Mostrar formulario
    context = {
        'autorizacion': autorizacion,
        'dias_restantes': autorizacion.dias_restantes(),
    }

    return render(request, 'control_acceso/extensiones/solicitar.html', context)


@login_required
@role_required('supervisor', 'direccion')
def listar_extensiones_pendientes(request):
    """Vista para listar solicitudes de extensión pendientes"""

    # Filtros
    busqueda = request.GET.get('q', '')
    estado_filtro = request.GET.get('estado', 'pendiente')

    # Query base
    extensiones = SolicitudExtension.objects.select_related(
        'autorizacion',
        'solicitada_por',
        'procesada_por'
    ).order_by('-creada_el')

    # Aplicar filtros
    if busqueda:
        extensiones = extensiones.filter(
            Q(codigo__icontains=busqueda) |
            Q(autorizacion__codigo__icontains=busqueda) |
            Q(autorizacion__empresa_nombre__icontains=busqueda) |
            Q(motivo__icontains=busqueda)
        )

    if estado_filtro and estado_filtro != 'todas':
        extensiones = extensiones.filter(estado=estado_filtro)

    # Estadísticas
    stats = {
        'total': SolicitudExtension.objects.count(),
        'pendientes': SolicitudExtension.objects.filter(estado='pendiente').count(),
        'aprobadas': SolicitudExtension.objects.filter(estado='aprobada').count(),
        'rechazadas': SolicitudExtension.objects.filter(estado='rechazada').count(),
    }

    # Paginación
    paginator = Paginator(extensiones, 20)
    page = request.GET.get('page')
    extensiones_page = paginator.get_page(page)

    context = {
        'extensiones': extensiones_page,
        'stats': stats,
        'busqueda': busqueda,
        'estado_filtro': estado_filtro,
    }

    return render(request, 'control_acceso/extensiones/listar.html', context)


@login_required
@role_required('supervisor', 'direccion')
def aprobar_extension(request, extension_id):
    """Vista para aprobar una solicitud de extensión"""
    extension = get_object_or_404(SolicitudExtension, id=extension_id)

    # Verificar que esté pendiente
    if extension.estado != 'pendiente':
        messages.warning(request, f'Esta solicitud ya fue {extension.get_estado_display()}.')
        return redirect('control_acceso:listar_extensiones_pendientes')

    if request.method == 'POST':
        observaciones = request.POST.get('observaciones', '').strip()

        # Aprobar la extensión
        extension.aprobar(usuario=request.user, observaciones=observaciones)

        messages.success(
            request,
            f'Extensión {extension.codigo} aprobada exitosamente. '
            f'La autorización {extension.autorizacion.codigo} ahora vence el '
            f'{extension.fecha_vencimiento_solicitada.strftime("%d/%m/%Y %H:%M")}.'
        )

        # Enviar notificación por email
        from notificaciones.services.email_service import EmailService

        # Obtener emails del solicitante y admins de la empresa
        destinatarios = [extension.solicitada_por.email] if extension.solicitada_por.email else []
        empresa_emails = [
            user.email for user in extension.autorizacion.solicitud.empresa.usuarios.filter(es_admin_empresa=True)
            if user.email
        ]
        destinatarios.extend(empresa_emails)

        if destinatarios:
            contexto = {
                'codigo_extension': extension.codigo,
                'codigo_autorizacion': extension.autorizacion.codigo,
                'empresa': extension.autorizacion.empresa_nombre,
                'fecha_nueva': extension.fecha_vencimiento_solicitada.strftime('%d/%m/%Y %H:%M'),
                'dias_extension': extension.dias_extension_solicitados,
                'aprobada_por': request.user.get_full_name(),
                'observaciones': observaciones,
            }

            EmailService.enviar_notificacion(
                codigo_evento='extension_aprobada',
                contexto=contexto,
                destinatarios_adicionales=destinatarios,
                forzar_destinatarios=True
            )

        return redirect('control_acceso:listar_extensiones_pendientes')

    # GET - Mostrar formulario
    context = {
        'extension': extension,
    }

    return render(request, 'control_acceso/extensiones/aprobar.html', context)


@login_required
@role_required('supervisor', 'direccion')
def rechazar_extension(request, extension_id):
    """Vista para rechazar una solicitud de extensión"""
    extension = get_object_or_404(SolicitudExtension, id=extension_id)

    # Verificar que esté pendiente
    if extension.estado != 'pendiente':
        messages.warning(request, f'Esta solicitud ya fue {extension.get_estado_display()}.')
        return redirect('control_acceso:listar_extensiones_pendientes')

    if request.method == 'POST':
        motivo_rechazo = request.POST.get('motivo_rechazo', '').strip()

        if not motivo_rechazo or len(motivo_rechazo) < 10:
            messages.error(request, 'El motivo del rechazo debe tener al menos 10 caracteres.')
            return redirect('control_acceso:rechazar_extension', extension_id=extension_id)

        # Rechazar la extensión
        extension.rechazar(usuario=request.user, motivo_rechazo=motivo_rechazo)

        messages.success(request, f'Extensión {extension.codigo} rechazada.')

        # Enviar notificación por email
        from notificaciones.services.email_service import EmailService

        destinatarios = [extension.solicitada_por.email] if extension.solicitada_por.email else []
        empresa_emails = [
            user.email for user in extension.autorizacion.solicitud.empresa.usuarios.filter(es_admin_empresa=True)
            if user.email
        ]
        destinatarios.extend(empresa_emails)

        if destinatarios:
            contexto = {
                'codigo_extension': extension.codigo,
                'codigo_autorizacion': extension.autorizacion.codigo,
                'empresa': extension.autorizacion.empresa_nombre,
                'motivo_rechazo': motivo_rechazo,
                'rechazada_por': request.user.get_full_name(),
            }

            EmailService.enviar_notificacion(
                codigo_evento='extension_rechazada',
                contexto=contexto,
                destinatarios_adicionales=destinatarios,
                forzar_destinatarios=True
            )

        return redirect('control_acceso:listar_extensiones_pendientes')

    # GET - Mostrar formulario
    context = {
        'extension': extension,
    }

    return render(request, 'control_acceso/extensiones/rechazar.html', context)


@login_required
def historial_extensiones(request, autorizacion_id):
    """Vista para ver el historial de extensiones de una autorización"""
    autorizacion = get_object_or_404(Autorizacion, id=autorizacion_id)

    # Verificar permisos
    if request.user.role == 'solicitante':
        if not request.user.empresa or autorizacion.solicitud.empresa != request.user.empresa:
            messages.error(request, 'No tienes permisos para ver este historial.')
            return redirect('solicitudes:mis_autorizaciones')

    # Obtener todas las extensiones de esta autorización
    extensiones = autorizacion.solicitudes_extension.select_related(
        'solicitada_por',
        'procesada_por'
    ).order_by('-creada_el')

    context = {
        'autorizacion': autorizacion,
        'extensiones': extensiones,
    }

    return render(request, 'control_acceso/extensiones/historial.html', context)
