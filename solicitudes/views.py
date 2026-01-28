from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .forms import SolicitudForm, VehiculoFormSet, DocumentoFormSet
from accounts.models import Empresa
from accounts.decorators import role_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from .models import Solicitud, SolicitudPersonal, Puerto, LugarPuerto, MotivoAcceso
from empresas.models import Personal
from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone
import json
from django.http import JsonResponse

def verificar_solicitud_completa(solicitud, request):
    """
    Verifica si una solicitud está completa para ser enviada.
    Retorna lista de elementos faltantes o lista vacía si está completa.
    """
    elementos_faltantes = []

    # 1. Verificar datos básicos de la solicitud
    if not solicitud.puerto_destino:
        elementos_faltantes.append("Puerto de destino")
    if not solicitud.motivo_acceso:
        elementos_faltantes.append("Servicio a ofrecer")
    if not solicitud.fecha_ingreso:
        elementos_faltantes.append("Fecha de ingreso")
    if not solicitud.hora_ingreso:
        elementos_faltantes.append("Hora de ingreso")
    if not solicitud.fecha_salida:
        elementos_faltantes.append("Fecha de salida")
    if not solicitud.hora_salida:
        elementos_faltantes.append("Hora de salida")
    if not solicitud.descripcion or len(solicitud.descripcion.strip()) < 10:
        elementos_faltantes.append("Descripción detallada (mínimo 10 caracteres)")

    # 2. Verificar vigencia del contrato de la empresa
    if solicitud.empresa and hasattr(solicitud.empresa, 'fecha_expiracion_contrato'):
        if solicitud.empresa.fecha_expiracion_contrato:
            from django.utils import timezone
            if solicitud.empresa.fecha_expiracion_contrato < timezone.now().date():
                elementos_faltantes.append(f"Contrato de empresa vencido el {solicitud.empresa.fecha_expiracion_contrato}")

    # 3. Verificar personal asignado
    personal_asignado = solicitud.personal_asignado.count()
    if personal_asignado == 0:
        elementos_faltantes.append("Al menos una persona asignada")

    # 4. Verificar vehículos
    vehiculos_asignados = solicitud.vehiculo_set.count()
    if vehiculos_asignados == 0:
        elementos_faltantes.append("Al menos un vehículo")

    # 5. Verificar documentos básicos de la solicitud
    documentos_solicitud = solicitud.documentos.count()
    if documentos_solicitud == 0:
        elementos_faltantes.append("Documentos de la solicitud")

    # 6. Verificar documentos críticos de personal
    personal_sin_cedula = []
    personal_sin_documentos = []

    for sp in solicitud.personal_asignado.all():
        personal = sp.personal

        # Verificar cédula (obligatoria)
        if not personal.documentos.filter(tipo_documento='cedula').exists():
            personal_sin_cedula.append(personal.nombre)

        # Verificar otros documentos mínimos
        documentos_count = personal.documentos.count()
        if documentos_count == 0:
            personal_sin_documentos.append(personal.nombre)

        # Verificar vigencia de documentos
        documentos_vencidos = []
        for doc in personal.documentos.all():
            if not doc.esta_vigente:
                documentos_vencidos.append(f"{personal.nombre} - {doc.get_tipo_documento_display()}")

        if documentos_vencidos:
            elementos_faltantes.extend([f"Documento vencido: {doc}" for doc in documentos_vencidos])

    # Agregar elementos faltantes de personal
    if personal_sin_cedula:
        elementos_faltantes.append(f"Cédula de identidad: {', '.join(personal_sin_cedula)}")

    if personal_sin_documentos:
        elementos_faltantes.append(f"Documentos de personal: {', '.join(personal_sin_documentos)}")

    # 7. Verificar documentos críticos de vehículos
    vehiculos_sin_registro = []
    vehiculos_sin_documentos = []

    for vehiculo in solicitud.vehiculo_set.all():
        # Verificar registro (obligatorio)
        if not vehiculo.documentos.filter(tipo_documento='registro').exists():
            vehiculos_sin_registro.append(vehiculo.placa)

        # Verificar otros documentos mínimos
        documentos_count = vehiculo.documentos.count()
        if documentos_count == 0:
            vehiculos_sin_documentos.append(vehiculo.placa)

        # Verificar vigencia de documentos
        documentos_vencidos = []
        for doc in vehiculo.documentos.all():
            if not doc.esta_vigente:
                documentos_vencidos.append(f"{vehiculo.placa} - {doc.get_tipo_documento_display()}")

        if documentos_vencidos:
            elementos_faltantes.extend([f"Documento vencido: {doc}" for doc in documentos_vencidos])

    # Agregar elementos faltantes de vehículos
    if vehiculos_sin_registro:
        elementos_faltantes.append(f"Registro de vehículo: {', '.join(vehiculos_sin_registro)}")

    if vehiculos_sin_documentos:
        elementos_faltantes.append(f"Documentos de vehículos: {', '.join(vehiculos_sin_documentos)}")

    return elementos_faltantes

# Create your views here.

@login_required
@role_required('solicitante')
def dashboard(request):
    # Obtener todas las solicitudes del usuario
    solicitudes_list = request.user.solicitudes.select_related('empresa', 'puerto_destino', 'motivo_acceso').all()
    
    # Estadísticas del mes actual
    today = datetime.now().date()
    first_day_month = today.replace(day=1)
    
    # Contadores por estado
    stats = {
        'total_solicitudes': solicitudes_list.count(),
        'solicitudes_mes': solicitudes_list.filter(creada_el__date__gte=first_day_month).count(),
        'pendientes': solicitudes_list.filter(estado__in=['pendiente', 'en_revision']).count(),
        'aprobadas': solicitudes_list.filter(estado='aprobada').count(),
        'documentos_faltantes': solicitudes_list.filter(estado='documentos_faltantes').count(),
        'borradores': solicitudes_list.filter(estado='borrador').count(),
        'activas': solicitudes_list.filter(estado__in=['pendiente', 'en_revision', 'aprobada']).count(),
    }
    
    # Calcular porcentaje de aprobación
    total_evaluadas = solicitudes_list.filter(estado__in=['aprobada', 'rechazada']).count()
    if total_evaluadas > 0:
        stats['porcentaje_aprobacion'] = round((stats['aprobadas'] / total_evaluadas) * 100)
    else:
        stats['porcentaje_aprobacion'] = 0
    
    # Verificar autorizaciones (simulado por ahora)
    from control_acceso.models import Autorizacion
    try:
        autorizaciones = Autorizacion.objects.filter(
            solicitud__solicitante=request.user,
            estado='activa'
        )
        stats['autorizaciones_activas'] = autorizaciones.count()
        stats['autorizaciones_por_vencer'] = autorizaciones.filter(
            valida_hasta__lte=today + timedelta(days=7)
        ).count()
    except:
        stats['autorizaciones_activas'] = 0
        stats['autorizaciones_por_vencer'] = 0
    
    # Paginación
    paginator = Paginator(solicitudes_list, 10)
    page_number = request.GET.get('page')
    solicitudes = paginator.get_page(page_number)
    
    context = {
        'user': request.user,
        'solicitudes': solicitudes,
        'stats': stats
    }
    
    return render(request, 'solicitudes/dashboard.html', context)

@login_required
@role_required('solicitante')
def nueva_solicitud(request):
    if request.method == 'POST':
        form = SolicitudForm(request.POST, user=request.user)
        vehiculo_formset = VehiculoFormSet(request.POST, prefix='vehiculos')
        documento_formset = DocumentoFormSet(request.POST, request.FILES, prefix='documentos')
        
        if form.is_valid() and vehiculo_formset.is_valid() and documento_formset.is_valid():
            try:
                with transaction.atomic():
                    # Guardar la solicitud
                    solicitud = form.save(commit=False)
                    solicitud.solicitante = request.user
                    
                    # Asignar empresa del usuario si existe
                    if request.user.empresa:
                        solicitud.empresa = request.user.empresa
                    else:
                        # Si el usuario no tiene empresa asignada, crear una por defecto
                        empresa, created = Empresa.objects.get_or_create(
                            rnc=request.user.cedula_rnc,
                            defaults={
                                'nombre': f"Empresa de {request.user.get_display_name()}",
                                'email': request.user.email,
                                'representante_legal': request.user
                            }
                        )
                        solicitud.empresa = empresa
                        # Asignar la empresa al usuario para futuras solicitudes
                        request.user.empresa = empresa
                        request.user.save()
                    
                    solicitud.estado = 'borrador'  # Comienza como borrador
                    solicitud.save()
                    
                    # Guardar servicios solicitados (ManyToMany)
                    form.save_m2m()
                    
                    # Guardar vehículos
                    vehiculo_formset.instance = solicitud
                    vehiculo_formset.save()
                    
                    # Guardar documentos
                    documento_formset.instance = solicitud
                    documentos = documento_formset.save(commit=False)
                    for documento in documentos:
                        documento.nombre_original = documento.archivo.name
                        documento.tamaño = documento.archivo.size
                        documento.save()
                    
                    # Procesar personal asignado
                    personal_data = []
                    form_index = 0
                    
                    while f'personal-{form_index}-nombre' in request.POST or f'personal-{form_index}-id' in request.POST:
                        personal_id = request.POST.get(f'personal-{form_index}-id')
                        
                        if personal_id:  # Personal existente
                            try:
                                personal = Personal.objects.get(id=personal_id)
                                rol_operacion = request.POST.get(f'personal-{form_index}-rol_operacion', '')
                                
                                # Crear relación solicitud-personal
                                SolicitudPersonal.objects.create(
                                    solicitud=solicitud,
                                    personal=personal,
                                    rol_operacion=rol_operacion
                                )
                            except Personal.DoesNotExist:
                                pass
                        else:  # Nuevo personal
                            nombre = request.POST.get(f'personal-{form_index}-nombre', '').strip()
                            cedula = request.POST.get(f'personal-{form_index}-cedula', '').strip()
                            
                            if nombre and cedula:
                                # Verificar si ya existe por cédula
                                personal, created = Personal.objects.get_or_create(
                                    cedula=cedula,
                                    defaults={
                                        'nombre': nombre,
                                        'cargo': request.POST.get(f'personal-{form_index}-cargo', ''),
                                        'licencia_conducir': request.POST.get(f'personal-{form_index}-licencia', ''),
                                        'telefono': request.POST.get(f'personal-{form_index}-telefono', ''),
                                    }
                                )
                                
                                rol_operacion = request.POST.get(f'personal-{form_index}-rol_operacion', '')
                                
                                # Crear relación solicitud-personal
                                SolicitudPersonal.objects.create(
                                    solicitud=solicitud,
                                    personal=personal,
                                    rol_operacion=rol_operacion
                                )
                        
                        form_index += 1
                    
                    # Si es envío final, validar completitud
                    if 'enviar_solicitud' in request.POST:
                        # Verificar si la solicitud está completa
                        elementos_faltantes = verificar_solicitud_completa(solicitud, request)
                        
                        if elementos_faltantes:
                            # Si hay elementos faltantes, mostrar modal con opciones
                            
                            # Si el usuario elige guardar borrador desde el modal
                            if 'guardar_borrador_modal' in request.POST:
                                messages.success(request, f"¡Borrador guardado exitosamente! Elementos pendientes: {len(elementos_faltantes)}")
                                return redirect('solicitudes:dashboard')
                            
                            # Si no, mostrar el modal de validación
                            context = {
                                'form': form,
                                'vehiculo_formset': vehiculo_formset,
                                'documento_formset': documento_formset,
                                'elementos_faltantes': elementos_faltantes,
                                'solicitud_id': solicitud.id,  # Para poder continuarla
                                'show_validation_modal': True
                            }
                            messages.warning(request, "Solicitud incompleta. Complete todos los elementos faltantes antes de enviar.")
                            return render(request, 'solicitudes/nueva_solicitud.html', context)
                        else:
                            # Si está completa, enviar
                            solicitud.estado = 'pendiente'
                            solicitud.enviada_el = datetime.now()
                            solicitud.save()
                            messages.success(request, "¡Solicitud enviada exitosamente para revisión!")
                    else:
                        messages.success(request, "¡Borrador guardado exitosamente!")
                    
                    return redirect('solicitudes:dashboard')
                    
            except Exception as e:
                messages.error(request, f"Error al procesar la solicitud: {str(e)}")
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = SolicitudForm(user=request.user)
        vehiculo_formset = VehiculoFormSet(prefix='vehiculos')
        documento_formset = DocumentoFormSet(prefix='documentos')
    
    context = {
        'form': form,
        'vehiculo_formset': vehiculo_formset,
        'documento_formset': documento_formset,
    }
    return render(request, 'solicitudes/nueva_solicitud.html', context)

@login_required
@role_required('solicitante')
def detalle_solicitud(request, solicitud_id):
    solicitud = request.user.solicitudes.select_related('empresa').filter(id=solicitud_id).first()
    if not solicitud:
        return redirect('solicitudes:dashboard')
    return render(request, 'solicitudes/detalle_solicitud.html', {'solicitud': solicitud})

@login_required
@role_required('solicitante')
def editar_solicitud(request, solicitud_id):
    solicitud = request.user.solicitudes.filter(id=solicitud_id, estado__in=['borrador', 'recibido', 'pendiente', 'documentos_faltantes']).first()
    if not solicitud:
        messages.error(request, "No tienes permiso para editar esta solicitud.")
        return redirect('solicitudes:dashboard')
    if request.method == 'POST':
        form = SolicitudForm(request.POST, instance=solicitud, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "¡Solicitud actualizada exitosamente!")
            return redirect('solicitudes:detalle_solicitud', solicitud_id=solicitud.id)
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = SolicitudForm(instance=solicitud, user=request.user)
    return render(request, 'solicitudes/editar_solicitud.html', {'form': form, 'solicitud': solicitud})

@login_required
@role_required('solicitante')
def borrar_solicitud(request, solicitud_id):
    solicitud = request.user.solicitudes.filter(id=solicitud_id, estado__in=['borrador', 'recibido', 'pendiente']).first()
    if not solicitud:
        messages.error(request, "No tienes permiso para borrar esta solicitud.")
        return redirect('solicitudes:dashboard')
    if request.method == 'POST':
        solicitud.delete()
        messages.success(request, "¡Solicitud eliminada exitosamente!")
        return redirect('solicitudes:dashboard')
    return render(request, 'solicitudes/borrar_solicitud.html', {'solicitud': solicitud})

@login_required
@role_required('solicitante')
def mis_borradores(request):
    """Vista para mostrar solo las solicitudes en estado borrador"""
    borradores_list = request.user.solicitudes.filter(estado='borrador').select_related('empresa', 'puerto_destino', 'motivo_acceso').order_by('-creada_el')
    
    # Paginación
    paginator = Paginator(borradores_list, 10)
    page_number = request.GET.get('page')
    borradores = paginator.get_page(page_number)
    
    context = {
        'user': request.user,
        'borradores': borradores,
        'total_borradores': borradores_list.count()
    }
    
    return render(request, 'solicitudes/mis_borradores.html', context)

@login_required
@role_required('solicitante')
def mis_solicitudes(request):
    """Vista para mostrar todas las solicitudes del usuario"""
    # Obtener parámetros de filtro
    estado_filtro = request.GET.get('estado', '')

    # Estados simplificados para el solicitante (solo ve estos 3 + borrador)
    ESTADOS_SOLICITANTE_CHOICES = [
        ('borrador', 'Borrador'),
        ('recibida', 'Recibida'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]

    # Mapeo de estado visible a estados internos para filtrar
    MAPEO_FILTRO_SOLICITANTE = {
        'borrador': ['borrador'],
        'recibida': ['recibido', 'sin_asignar', 'pendiente', 'en_revision', 'documentos_faltantes', 'escalada'],
        'aprobada': ['aprobada'],
        'rechazada': ['rechazada', 'vencida'],
    }

    # Filtrar solicitudes
    solicitudes_list = request.user.solicitudes.select_related('empresa', 'puerto_destino', 'motivo_acceso').order_by('-creada_el')

    if estado_filtro:
        # Obtener los estados internos correspondientes al filtro del solicitante
        estados_internos = MAPEO_FILTRO_SOLICITANTE.get(estado_filtro, [estado_filtro])
        solicitudes_list = solicitudes_list.filter(estado__in=estados_internos)

    # Estadísticas (usando estados visibles para el solicitante)
    stats = {
        'total': request.user.solicitudes.count(),
        'borradores': request.user.solicitudes.filter(estado='borrador').count(),
        'recibidas': request.user.solicitudes.filter(estado__in=['recibido', 'sin_asignar', 'pendiente', 'en_revision', 'documentos_faltantes', 'escalada']).count(),
        'aprobadas': request.user.solicitudes.filter(estado='aprobada').count(),
        'rechazadas': request.user.solicitudes.filter(estado__in=['rechazada', 'vencida']).count(),
    }

    # Paginación
    paginator = Paginator(solicitudes_list, 15)
    page_number = request.GET.get('page')
    solicitudes = paginator.get_page(page_number)

    context = {
        'user': request.user,
        'solicitudes': solicitudes,
        'stats': stats,
        'estado_filtro': estado_filtro,
        'estados_choices': ESTADOS_SOLICITANTE_CHOICES  # Estados simplificados
    }

    return render(request, 'solicitudes/mis_solicitudes.html', context)

@login_required
@role_required('solicitante')
def mis_autorizaciones(request):
    """Vista para mostrar autorizaciones del usuario"""
    # Por ahora mostrar las solicitudes aprobadas como autorizaciones
    autorizaciones_list = request.user.solicitudes.filter(estado='aprobada').select_related('empresa', 'puerto_destino', 'motivo_acceso').order_by('-creada_el')
    
    # Paginación
    paginator = Paginator(autorizaciones_list, 10)
    page_number = request.GET.get('page')
    autorizaciones = paginator.get_page(page_number)
    
    context = {
        'user': request.user,
        'autorizaciones': autorizaciones,
        'total_autorizaciones': autorizaciones_list.count()
    }
    
    return render(request, 'solicitudes/mis_autorizaciones.html', context)


@login_required
@role_required('solicitante')
def estadisticas(request):
    """Vista para mostrar estadísticas completas del usuario"""
    from django.db.models import Avg, Max, Min
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    now = timezone.now()
    current_month = now.month
    current_year = now.year
    last_month = now - timedelta(days=30)
    
    # Solicitudes del usuario
    user_solicitudes = request.user.solicitudes.all()
    solicitudes_mes_actual = user_solicitudes.filter(creada_el__month=current_month, creada_el__year=current_year)
    solicitudes_mes_anterior = user_solicitudes.filter(creada_el__month=last_month.month, creada_el__year=last_month.year)
    
    # Estadísticas básicas
    total_solicitudes = user_solicitudes.count()
    aprobadas = user_solicitudes.filter(estado='aprobada').count()
    pendientes = user_solicitudes.filter(estado__in=['pendiente', 'en_revision', 'documentos_faltantes']).count()
    rechazadas = user_solicitudes.filter(estado='rechazada').count()
    
    # Porcentajes
    tasa_aprobacion = round((aprobadas / total_solicitudes * 100) if total_solicitudes > 0 else 0, 1)
    tasa_rechazo = round((rechazadas / total_solicitudes * 100) if total_solicitudes > 0 else 0, 1)
    
    # Comparación mensual
    solicitudes_este_mes = solicitudes_mes_actual.count()
    solicitudes_mes_pasado = solicitudes_mes_anterior.count()
    cambio_mensual = solicitudes_este_mes - solicitudes_mes_pasado
    
    # Puertos más utilizados
    puertos_frecuentes = user_solicitudes.values('puerto_destino__nombre').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Motivos más frecuentes
    motivos_frecuentes = user_solicitudes.values('motivo_acceso__nombre').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Tiempo promedio de aprobación (simulado - en días)
    tiempo_promedio = 5  # Por ahora estático, se puede calcular con fechas reales
    
    # Próximas autorizaciones por vencer (simulado)
    autorizaciones_por_vencer = user_solicitudes.filter(estado='aprobada').count()
    
    # Vehículos más utilizados
    vehiculos_frecuentes = []
    for solicitud in user_solicitudes.prefetch_related('vehiculos')[:10]:
        for vehiculo in solicitud.vehiculos.all():
            vehiculos_frecuentes.append({
                'placa': vehiculo.placa,
                'tipo': vehiculo.tipo,
            })
    
    # Conteo de vehículos únicos
    vehiculos_unicos = {}
    for v in vehiculos_frecuentes:
        key = f"{v['placa']} ({v['tipo']})"
        vehiculos_unicos[key] = vehiculos_unicos.get(key, 0) + 1
    
    vehiculos_top = sorted(vehiculos_unicos.items(), key=lambda x: x[1], reverse=True)[:5]
    
    context = {
        'user': request.user,
        'stats': {
            'total_solicitudes': total_solicitudes,
            'aprobadas': aprobadas,
            'pendientes': pendientes,
            'rechazadas': rechazadas,
            'tasa_aprobacion': tasa_aprobacion,
            'tasa_rechazo': tasa_rechazo,
            'solicitudes_este_mes': solicitudes_este_mes,
            'solicitudes_mes_pasado': solicitudes_mes_pasado,
            'cambio_mensual': cambio_mensual,
            'tiempo_promedio': tiempo_promedio,
            'autorizaciones_por_vencer': autorizaciones_por_vencer,
        },
        'puertos_frecuentes': puertos_frecuentes,
        'motivos_frecuentes': motivos_frecuentes,
        'vehiculos_top': vehiculos_top,
    }
    
    return render(request, 'solicitudes/estadisticas.html', context)


# ================================================
# VIEWS FOR WIZARD FORM (Experimental)
# ================================================

def limpiar_sesion_wizard(request):
    """Limpia los datos de sesión del wizard y archivos temporales"""
    import os
    from django.conf import settings

    # Obtener datos del paso 4 para limpiar archivos temporales
    paso4 = request.session.get('wizard_paso4', {})
    documentos_subidos = paso4.get('documentos_subidos', [])

    # Eliminar archivos temporales
    for doc_info in documentos_subidos:
        temp_path = doc_info.get('temp_path')
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

    # Limpiar sesión
    for key in list(request.session.keys()):
        if key.startswith('wizard_'):
            del request.session[key]

@login_required
@role_required('solicitante')
def solicitud_wizard_inicio(request):
    """Página de inicio del wizard - solo para pruebas"""
    if request.method == 'POST' and request.POST.get('iniciar_wizard'):
        limpiar_sesion_wizard(request)
        return redirect('solicitudes:wizard_paso1')
    
    context = {
        'titulo': 'Formulario de Solicitud (Wizard - Prueba)',
        'descripcion': 'Esta es una versión experimental del formulario como wizard. El formulario actual no se verá afectado.',
        'porcentaje_progreso': 0,
        'paso_actual': 0,
        'total_pasos': 5
    }
    return render(request, 'solicitudes/wizard/inicio.html', context)

@login_required
@role_required('solicitante')
def solicitud_wizard_paso1(request):
    """Paso 1: Información Básica"""
    if request.method == 'POST':
        # Guardar datos del paso 1 en sesión
        request.session['wizard_paso1'] = {
            'numero_imo': request.POST.get('numero_imo'),
            'naviera': request.POST.get('naviera'),
            'puerto_destino': request.POST.get('puerto_destino'),
            'lugar_destino': request.POST.get('lugar_destino'),
            'motivo_acceso': request.POST.get('motivo_acceso'),
            'fecha_ingreso': request.POST.get('fecha_ingreso'),
            'hora_ingreso': request.POST.get('hora_ingreso'),
            'fecha_salida': request.POST.get('fecha_salida'),
            'hora_salida': request.POST.get('hora_salida'),
            'descripcion': request.POST.get('descripcion'),
            'prioridad': request.POST.get('prioridad', 'normal'),
        }
        return redirect('solicitudes:wizard_paso2')

    # Cargar datos si existen en sesión
    datos_previos = request.session.get('wizard_paso1', {})

    # Cargar opciones para el formulario
    puertos = Puerto.objects.filter(activo=True)
    motivos_acceso = MotivoAcceso.objects.filter(activo=True)

    # Calcular porcentaje de progreso
    porcentaje_progreso = int((1 / 5) * 100) if 5 > 0 else 20

    context = {
        'datos_previos': datos_previos,
        'paso_actual': 1,
        'total_pasos': 5,
        'porcentaje_progreso': porcentaje_progreso,
        'puertos': puertos,
        'motivos_acceso': motivos_acceso,
        'prioridades': Solicitud.PRIORIDAD_CHOICES,
    }
    return render(request, 'solicitudes/wizard/paso1.html', context)

@login_required
@role_required('solicitante')
def solicitud_wizard_paso2(request):
    """Paso 2: Personal"""
    if request.method == 'POST':
        # Procesar personal
        personal_data = []
        i = 0
        while f'personal-nombre-{i}' in request.POST:
            nombre = request.POST.get(f'personal-nombre-{i}')
            apellido = request.POST.get(f'personal-apellido-{i}')
            cedula = request.POST.get(f'personal-cedula-{i}')
            pasaporte = request.POST.get(f'personal-pasaporte-{i}')
            email = request.POST.get(f'personal-email-{i}')
            telefono = request.POST.get(f'personal-telefono-{i}')
            cargo = request.POST.get(f'personal-cargo-{i}')
            licencia_conducir = request.POST.get(f'personal-licencia-{i}')
            rol_operacion = request.POST.get(f'personal-rol-{i}')

            # Solo guardar si hay nombre, apellido y (cédula o pasaporte)
            if nombre and apellido and (cedula or pasaporte):
                personal_data.append({
                    'nombre': nombre,
                    'apellido': apellido,
                    'cedula': cedula or '',
                    'pasaporte': pasaporte or '',
                    'email': email or '',
                    'telefono': telefono or '',
                    'cargo': cargo or '',
                    'licencia_conducir': licencia_conducir or '',
                    'rol_operacion': rol_operacion or '',
                })
            i += 1

        request.session['wizard_paso2'] = {
            'personal': personal_data
        }
        return redirect('solicitudes:wizard_paso3')

    # Cargar datos previos
    datos_previos = request.session.get('wizard_paso2', {'personal': []})

    # Calcular porcentaje de progreso
    porcentaje_progreso = int((2 / 5) * 100) if 5 > 0 else 40

    context = {
        'datos_previos': datos_previos,
        'paso_actual': 2,
        'total_pasos': 5,
        'porcentaje_progreso': porcentaje_progreso,
    }
    return render(request, 'solicitudes/wizard/paso2.html', context)

@login_required
@role_required('solicitante')
def solicitud_wizard_paso3(request):
    """Paso 3: Vehículos"""
    if request.method == 'POST':
        # Procesar vehículos
        vehiculos_data = []
        i = 0
        while f'vehiculo-placa-{i}' in request.POST:
            placa = request.POST.get(f'vehiculo-placa-{i}')
            tipo = request.POST.get(f'vehiculo-tipo-{i}')
            conductor_nombre = request.POST.get(f'vehiculo-conductor-{i}')
            conductor_licencia = request.POST.get(f'vehiculo-licencia-{i}')

            if placa:  # Solo guardar si hay placa
                vehiculos_data.append({
                    'placa': placa,
                    'tipo_vehiculo': tipo,
                    'conductor_nombre': conductor_nombre,
                    'conductor_licencia': conductor_licencia,
                })
            i += 1

        request.session['wizard_paso3'] = {
            'vehiculos': vehiculos_data
        }
        return redirect('solicitudes:wizard_paso4')

    # Cargar datos previos
    datos_previos = request.session.get('wizard_paso3', {'vehiculos': []})

    # Calcular porcentaje de progreso
    porcentaje_progreso = int((3 / 5) * 100) if 5 > 0 else 60

    context = {
        'datos_previos': datos_previos,
        'paso_actual': 3,
        'total_pasos': 5,
        'porcentaje_progreso': porcentaje_progreso,
        'tipos_vehiculo': [
            ('automovil', 'Automóvil'),
            ('camion', 'Camión'),
            ('camioneta', 'Camioneta'),
            ('motocicleta', 'Motocicleta'),
            ('equipo_especializado', 'Equipo Especializado'),
        ]
    }
    return render(request, 'solicitudes/wizard/paso3.html', context)

@login_required
@role_required('solicitante')
def solicitud_wizard_paso4(request):
    """Paso 4: Servicios y Documentos"""
    import os
    import uuid
    from django.conf import settings
    from evaluacion.models import DocumentoRequeridoServicio

    if request.method == 'POST':
        # Procesar servicio seleccionado (solo uno)
        servicio_seleccionado = request.POST.get('servicio_seleccionado')

        # Procesar archivos subidos para documentos requeridos
        documentos_subidos = []

        if servicio_seleccionado:
            # Obtener documentos requeridos del servicio
            docs_requeridos = DocumentoRequeridoServicio.objects.filter(
                servicio_id=servicio_seleccionado,
                activo=True
            )

            # Crear directorio temporal si no existe
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_wizard')
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            # Generar un ID único para esta sesión de wizard
            wizard_session_id = request.session.get('wizard_session_id')
            if not wizard_session_id:
                wizard_session_id = str(uuid.uuid4())
                request.session['wizard_session_id'] = wizard_session_id

            # Procesar cada archivo subido
            for doc in docs_requeridos:
                file_key = f'documento_{doc.id}'
                if file_key in request.FILES:
                    archivo = request.FILES[file_key]

                    # Generar nombre único para el archivo temporal
                    ext = os.path.splitext(archivo.name)[1]
                    temp_filename = f"{wizard_session_id}_{doc.id}{ext}"
                    temp_path = os.path.join(temp_dir, temp_filename)

                    # Guardar archivo temporalmente
                    with open(temp_path, 'wb+') as destination:
                        for chunk in archivo.chunks():
                            destination.write(chunk)

                    documentos_subidos.append({
                        'documento_requerido_id': doc.id,
                        'nombre_original': archivo.name,
                        'tamaño': archivo.size,
                        'temp_path': temp_path,
                        'temp_filename': temp_filename,
                    })

        request.session['wizard_paso4'] = {
            'servicios_seleccionados': [servicio_seleccionado] if servicio_seleccionado else [],
            'documentos_subidos': documentos_subidos,
        }
        return redirect('solicitudes:wizard_paso5')

    # Cargar datos previos
    datos_previos = request.session.get('wizard_paso4', {'servicios_seleccionados': [], 'documentos_subidos': []})

    # Cargar servicios de la licencia asociada a la empresa del usuario
    servicios = []
    tipo_licencia = None

    if request.user.empresa:
        empresa = request.user.empresa
        tipo_licencia = empresa.tipo_licencia

        # Solo obtener servicios del tipo de licencia (no adicionales)
        if tipo_licencia:
            servicios = list(tipo_licencia.servicios_incluidos.filter(activo=True))

    # Calcular porcentaje de progreso
    porcentaje_progreso = int((4 / 5) * 100) if 5 > 0 else 80

    context = {
        'datos_previos': datos_previos,
        'paso_actual': 4,
        'total_pasos': 5,
        'porcentaje_progreso': porcentaje_progreso,
        'servicios': servicios,
        'tipo_licencia': tipo_licencia,
    }
    return render(request, 'solicitudes/wizard/paso4.html', context)

@login_required
@role_required('solicitante')
def solicitud_wizard_paso5(request):
    """Paso 5: Confirmación y Resumen"""
    from evaluacion.models import Servicio, DocumentoRequeridoServicio

    # Obtener todos los datos acumulados
    paso1 = request.session.get('wizard_paso1', {})
    paso2 = request.session.get('wizard_paso2', {})
    paso3 = request.session.get('wizard_paso3', {})
    paso4 = request.session.get('wizard_paso4', {})

    # Cargar información adicional para mostrar en el resumen
    puertos = Puerto.objects.filter(activo=True)
    lugares = LugarPuerto.objects.filter(activo=True)
    motivos_acceso = MotivoAcceso.objects.filter(activo=True)
    servicios = Servicio.objects.filter(activo=True)

    puerto_nombre = ""
    lugar_nombre = ""
    motivo_nombre = ""
    servicios_nombres = []

    if paso1.get('puerto_destino'):
        puerto_obj = puertos.filter(id=paso1['puerto_destino']).first()
        puerto_nombre = puerto_obj.nombre if puerto_obj else ""

    if paso1.get('lugar_destino'):
        lugar_obj = lugares.filter(id=paso1['lugar_destino']).first()
        lugar_nombre = lugar_obj.nombre if lugar_obj else ""

    if paso1.get('motivo_acceso'):
        motivo_obj = motivos_acceso.filter(id=paso1['motivo_acceso']).first()
        motivo_nombre = motivo_obj.nombre if motivo_obj else ""

    if paso4.get('servicios_seleccionados'):
        servicios_queryset = servicios.filter(id__in=paso4['servicios_seleccionados'])
        servicios_nombres = [s.nombre for s in servicios_queryset]

    # Obtener información de documentos subidos
    documentos_info = []
    documentos_subidos = paso4.get('documentos_subidos', [])
    for doc_info in documentos_subidos:
        try:
            doc_requerido = DocumentoRequeridoServicio.objects.get(id=doc_info['documento_requerido_id'])
            documentos_info.append({
                'nombre_requerido': doc_requerido.nombre,
                'nombre_archivo': doc_info['nombre_original'],
                'tamaño_mb': round(doc_info['tamaño'] / (1024 * 1024), 2),
                'obligatorio': doc_requerido.obligatorio
            })
        except DocumentoRequeridoServicio.DoesNotExist:
            pass

    # Obtener el nombre de la prioridad
    prioridad_nombre = ""
    for value, label in Solicitud.PRIORIDAD_CHOICES:
        if paso1.get('prioridad') == value:
            prioridad_nombre = label
            break

    # Calcular porcentaje de progreso
    porcentaje_progreso = int((5 / 5) * 100) if 5 > 0 else 100

    context = {
        'paso_actual': 5,
        'total_pasos': 5,
        'porcentaje_progreso': porcentaje_progreso,
        'documentos_info': documentos_info,
        'datos_totales': {
            'paso1': paso1,
            'paso2': paso2,
            'paso3': paso3,
            'paso4': paso4,
        },
        'puerto_nombre': puerto_nombre,
        'lugar_nombre': lugar_nombre,
        'motivo_nombre': motivo_nombre,
        'servicios_nombres': servicios_nombres,
        'prioridad_nombre': prioridad_nombre,
        'prioridades': Solicitud.PRIORIDAD_CHOICES,
    }
    return render(request, 'solicitudes/wizard/paso5.html', context)

def convertir_hora_12_a_24(hora_12h):
    """Convierte hora en formato 12H (08:00 AM) a formato 24H (08:00)"""
    if not hora_12h:
        return None
    try:
        # Parsear la hora en formato 12H
        hora_obj = datetime.strptime(hora_12h, '%I:%M %p')
        # Retornar en formato 24H
        return hora_obj.strftime('%H:%M')
    except:
        return None

@login_required
@role_required('solicitante')
def solicitud_wizard_finalizar(request):
    """Finalizar y crear/actualizar la solicitud"""
    import os
    import shutil
    from django.conf import settings
    from django.core.files import File

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Obtener todos los datos del wizard
                paso1 = request.session.get('wizard_paso1', {})
                paso2 = request.session.get('wizard_paso2', {})
                paso3 = request.session.get('wizard_paso3', {})
                paso4 = request.session.get('wizard_paso4', {})

                # Verificar si estamos en modo edición
                modo_edicion = request.session.get('wizard_modo_edicion', False)
                solicitud_id = request.session.get('wizard_solicitud_id')

                # Convertir horas de formato 12H a 24H
                hora_ingreso = convertir_hora_12_a_24(paso1.get('hora_ingreso'))
                hora_salida = convertir_hora_12_a_24(paso1.get('hora_salida'))

                # La empresa es la del usuario
                empresa = request.user.empresa or request.user.empresa_set.first()

                if modo_edicion and solicitud_id:
                    # MODO EDICIÓN: Actualizar solicitud existente
                    solicitud = Solicitud.objects.get(id=solicitud_id, solicitante=request.user)

                    # Actualizar campos básicos
                    solicitud.numero_imo = paso1.get('numero_imo') or None
                    solicitud.naviera = paso1.get('naviera') or None
                    solicitud.puerto_destino_id = paso1.get('puerto_destino')
                    solicitud.lugar_destino_id = paso1.get('lugar_destino')
                    solicitud.motivo_acceso_id = paso1.get('motivo_acceso')
                    solicitud.fecha_ingreso = paso1.get('fecha_ingreso')
                    solicitud.hora_ingreso = hora_ingreso
                    solicitud.fecha_salida = paso1.get('fecha_salida')
                    solicitud.hora_salida = hora_salida
                    solicitud.descripcion = paso1.get('descripcion', '')
                    solicitud.prioridad = paso1.get('prioridad', 'normal')
                    solicitud.estado = 'recibido'  # Cambiar estado a recibido al reenviar
                    solicitud.save()
                else:
                    # MODO CREACIÓN: Crear nueva solicitud
                    solicitud = Solicitud.objects.create(
                        solicitante=request.user,
                        empresa=empresa,
                        numero_imo=paso1.get('numero_imo') or None,
                        naviera=paso1.get('naviera') or None,
                        puerto_destino_id=paso1.get('puerto_destino'),
                        lugar_destino_id=paso1.get('lugar_destino'),
                        motivo_acceso_id=paso1.get('motivo_acceso'),
                        fecha_ingreso=paso1.get('fecha_ingreso'),
                        hora_ingreso=hora_ingreso,
                        fecha_salida=paso1.get('fecha_salida'),
                        hora_salida=hora_salida,
                        descripcion=paso1.get('descripcion', ''),
                        prioridad=paso1.get('prioridad', 'normal'),
                        estado='recibido'  # Estado inicial al enviar la solicitud
                    )

                # Asociar servicios si existen
                if paso4.get('servicios_seleccionados'):
                    from evaluacion.models import Servicio
                    servicios = Servicio.objects.filter(id__in=paso4['servicios_seleccionados'])
                    solicitud.servicios_solicitados.set(servicios)

                # Procesar documentos de servicios subidos
                from evaluacion.models import DocumentoRequeridoServicio
                from .models import DocumentoServicioSolicitud

                documentos_subidos = paso4.get('documentos_subidos', [])
                for doc_info in documentos_subidos:
                    temp_path = doc_info.get('temp_path')
                    if temp_path and os.path.exists(temp_path):
                        try:
                            # Obtener el documento requerido
                            doc_requerido = DocumentoRequeridoServicio.objects.get(
                                id=doc_info['documento_requerido_id']
                            )

                            # Crear el registro de documento de servicio
                            with open(temp_path, 'rb') as f:
                                doc_servicio = DocumentoServicioSolicitud(
                                    solicitud=solicitud,
                                    documento_requerido=doc_requerido,
                                    nombre_original=doc_info['nombre_original'],
                                    tamaño=doc_info['tamaño'],
                                )
                                # Guardar el archivo
                                doc_servicio.archivo.save(
                                    doc_info['nombre_original'],
                                    File(f),
                                    save=True
                                )

                            # Eliminar archivo temporal
                            os.remove(temp_path)
                        except Exception as e:
                            # Log error pero continuar
                            print(f"Error procesando documento: {e}")

                # Crear personal y asociarlo
                from empresas.models import Personal
                for pers_data in paso2.get('personal', []):
                    # Construir nombre completo
                    nombre_completo = f"{pers_data.get('nombre', '')} {pers_data.get('apellido', '')}".strip()

                    # Buscar o crear personal con los campos requeridos
                    personal_data = {
                        'nombre': nombre_completo,
                        'cedula': pers_data.get('cedula', '') or None,
                        'pasaporte': pers_data.get('pasaporte', '') or None,
                        'telefono': pers_data.get('telefono', '') or None,
                        'cargo': pers_data.get('cargo', '') or None,
                        'licencia_conducir': pers_data.get('licencia_conducir', '') or None,
                    }

                    # Buscar por cédula o pasaporte
                    personal = None
                    if personal_data['cedula']:
                        personal = Personal.objects.filter(cedula=personal_data['cedula']).first()
                    elif personal_data['pasaporte']:
                        personal = Personal.objects.filter(pasaporte=personal_data['pasaporte']).first()

                    # Si no existe, crear nuevo personal
                    if not personal:
                        personal = Personal.objects.create(**personal_data)

                    # Crear relación solicitud-personal
                    solicitud.personal_asignado.create(
                        personal=personal,
                        rol_operacion=pers_data.get('rol_operacion', '')
                    )

                # Crear vehículos
                from .models import Vehiculo
                for veh_data in paso3.get('vehiculos', []):
                    Vehiculo.objects.create(
                        solicitud=solicitud,
                        placa=veh_data.get('placa', ''),
                        tipo_vehiculo=veh_data.get('tipo_vehiculo', 'camion'),
                        conductor_nombre=veh_data.get('conductor_nombre', ''),
                        conductor_licencia=veh_data.get('conductor_licencia', '')
                    )

                # Enviar notificación por correo (solo si es nueva)
                if not modo_edicion:
                    enviar_notificacion_nueva_solicitud(solicitud)

                # Limpiar sesión del wizard
                limpiar_sesion_wizard(request)

                if modo_edicion:
                    messages.success(request, f"¡Solicitud {solicitud.codigo} actualizada y reenviada exitosamente!")
                else:
                    messages.success(request, "¡Solicitud creada exitosamente!")
                return redirect('solicitudes:detalle_solicitud', solicitud_id=solicitud.id)

        except Exception as e:
            messages.error(request, f"Error al procesar la solicitud: {str(e)}")

    return redirect('solicitudes:solicitud_wizard_inicio')

@login_required
@role_required('solicitante')
def wizard_cargar_lugares_puerto(request):
    """API para cargar lugares del puerto dinámicamente"""
    puerto_id = request.GET.get('puerto_id')
    if puerto_id:
        lugares = LugarPuerto.objects.filter(puerto_id=puerto_id, activo=True).values('id', 'nombre', 'tipo_lugar')
        return JsonResponse({'lugares': list(lugares)})
    return JsonResponse({'lugares': []})

@login_required
@role_required('solicitante')
def wizard_cargar_lugar_detalle(request, lugar_id):
    """API para cargar detalles del lugar del puerto"""
    lugar = get_object_or_404(LugarPuerto, id=lugar_id, activo=True)
    return JsonResponse({
        'id': lugar.id,
        'nombre': lugar.nombre,
        'tipo_lugar': lugar.tipo_lugar,
        'descripcion': lugar.descripcion,
        'capacidad_maxima': lugar.capacidad_maxima,
    })


@login_required
@role_required('solicitante')
def wizard_cargar_documentos_servicio(request, servicio_id):
    """API para cargar los documentos requeridos de un servicio"""
    from evaluacion.models import DocumentoRequeridoServicio

    documentos = DocumentoRequeridoServicio.objects.filter(
        servicio_id=servicio_id,
        activo=True
    ).values('id', 'nombre', 'descripcion', 'obligatorio', 'orden').order_by('orden', 'nombre')

    return JsonResponse({'documentos': list(documentos)})

@login_required
@role_required('solicitante')
def solicitud_wizard_volver_paso(request, paso):
    """Volver a un paso específico del wizard"""
    if request.method == 'POST':
        limpiar_sesion_wizard(request)
        return redirect(f'solicitudes:solicitud_wizard_paso{paso}')
    return redirect('solicitudes:solicitud_wizard_inicio')


@login_required
@role_required('solicitante')
def solicitud_wizard_editar(request, solicitud_id):
    """
    Carga una solicitud existente en el wizard para editarla.
    Útil para solicitudes con estado 'documentos_faltantes' que necesitan completar documentación.
    """
    # Verificar que la solicitud pertenece al usuario y es editable
    solicitud = request.user.solicitudes.filter(
        id=solicitud_id,
        estado__in=['borrador', 'documentos_faltantes']
    ).select_related('puerto_destino', 'lugar_destino', 'motivo_acceso').first()

    if not solicitud:
        messages.error(request, "No tienes permiso para editar esta solicitud o no está en un estado editable.")
        return redirect('solicitudes:mis_solicitudes')

    # Limpiar sesión anterior del wizard
    limpiar_sesion_wizard(request)

    # Cargar datos de la solicitud en la sesión del wizard
    # Paso 1: Información básica
    request.session['wizard_paso1'] = {
        'numero_imo': solicitud.numero_imo or '',
        'naviera': solicitud.naviera or '',
        'puerto_destino': str(solicitud.puerto_destino.id) if solicitud.puerto_destino else '',
        'lugar_destino': str(solicitud.lugar_destino.id) if solicitud.lugar_destino else '',
        'motivo_acceso': str(solicitud.motivo_acceso.id) if solicitud.motivo_acceso else '',
        'fecha_ingreso': solicitud.fecha_ingreso.strftime('%Y-%m-%d') if solicitud.fecha_ingreso else '',
        'hora_ingreso': solicitud.hora_ingreso.strftime('%H:%M') if solicitud.hora_ingreso else '',
        'fecha_salida': solicitud.fecha_salida.strftime('%Y-%m-%d') if solicitud.fecha_salida else '',
        'hora_salida': solicitud.hora_salida.strftime('%H:%M') if solicitud.hora_salida else '',
        'descripcion': solicitud.descripcion or '',
        'prioridad': solicitud.prioridad or 'normal',
    }

    # Paso 2: Personal
    personal_ids = list(solicitud.personal_asignado.values_list('personal_id', flat=True))
    request.session['wizard_paso2'] = {
        'personal': [str(p) for p in personal_ids]
    }

    # Paso 3: Vehículos
    vehiculos = list(solicitud.vehiculos.values('placa', 'tipo_vehiculo', 'conductor_nombre', 'conductor_licencia'))
    request.session['wizard_paso3'] = {
        'vehiculos': vehiculos
    }

    # Paso 4: Servicios y documentos
    servicios_ids = list(solicitud.servicios_solicitados.values_list('id', flat=True))
    # Obtener documentos ya subidos
    documentos_subidos = []
    for doc in solicitud.documentos_servicio.all():
        documentos_subidos.append({
            'documento_requerido_id': doc.documento_requerido_id,
            'nombre': doc.nombre_original,
            'archivo_id': doc.id
        })

    request.session['wizard_paso4'] = {
        'servicios_seleccionados': [str(s) for s in servicios_ids],
        'documentos_subidos': documentos_subidos
    }

    # Guardar ID de solicitud que se está editando
    request.session['wizard_solicitud_id'] = solicitud.id
    request.session['wizard_modo_edicion'] = True

    # Mensaje informativo
    if solicitud.estado == 'documentos_faltantes':
        messages.info(request, f"Editando solicitud {solicitud.codigo}. Complete los documentos faltantes y envíe nuevamente.")
    else:
        messages.info(request, f"Editando solicitud {solicitud.codigo}.")

    # Redirigir al paso 4 si es documentos_faltantes, o paso 1 si es borrador
    if solicitud.estado == 'documentos_faltantes':
        return redirect('solicitudes:wizard_paso4')
    else:
        return redirect('solicitudes:wizard_paso1')


def enviar_notificacion_nueva_solicitud(solicitud):
    """
    Envía un correo electrónico de notificación cuando se crea una nueva solicitud
    Utiliza el nuevo sistema de notificaciones centralizado
    """
    from notificaciones.services import notificar_solicitud_recibida

    try:
        # Enviar notificación usando el nuevo sistema
        success, mensaje, log_id = notificar_solicitud_recibida(solicitud)

        if success:
            print(f"Notificación enviada exitosamente: {mensaje}")
        else:
            print(f"No se pudo enviar notificación: {mensaje}")

        return success

    except Exception as e:
        # Log del error pero no fallar la creación de la solicitud
        print(f"Error al enviar notificación de nueva solicitud: {str(e)}")
        return False


@login_required
@role_required('solicitante')
def listar_vehiculos_ajax(request):
    """Listar todos los vehículos registrados del usuario (para modal de selección)"""
    try:
        from gestion_vehiculos.models import Vehiculo as VehiculoRegistrado

        # Obtener vehículos registrados de la empresa del usuario
        vehiculos_registrados = VehiculoRegistrado.objects.filter(
            activo=True,
            empresa_propietaria=request.user
        ).order_by('placa')

        vehiculos_list = []
        for vehiculo in vehiculos_registrados:
            vehiculos_list.append({
                'placa': vehiculo.placa,
                'tipo_vehiculo': vehiculo.tipo_vehiculo,
                'marca': vehiculo.marca,
                'modelo': vehiculo.modelo,
                'ano': vehiculo.ano,
                'color': vehiculo.color,
                'conductor_nombre': '',  # No hay conductor en el modelo de vehículos registrados
                'conductor_licencia': '',
            })

        return JsonResponse({
            'success': True,
            'vehiculos': vehiculos_list
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
def imprimir_autorizacion(request, solicitud_id):
    """Vista para imprimir la autorización con QR de una solicitud aprobada"""
    # Verificar permisos según el rol
    if request.user.role == 'solicitante':
        # El solicitante solo puede ver sus propias autorizaciones
        solicitud = get_object_or_404(
            Solicitud,
            id=solicitud_id,
            solicitante=request.user,
            estado='aprobada'
        )
    elif request.user.role in ['evaluador', 'supervisor', 'admin_tic', 'direccion']:
        # Los evaluadores y otros roles administrativos pueden ver cualquier autorización
        solicitud = get_object_or_404(
            Solicitud,
            id=solicitud_id,
            estado='aprobada'
        )
    else:
        messages.error(request, "No tiene permisos para ver esta autorización.")
        return redirect('accounts:dashboard_redirect')

    # Verificar que existe la autorización
    try:
        autorizacion = solicitud.autorizacion
    except:
        messages.error(request, "Esta solicitud no tiene una autorización generada aún.")
        if request.user.role == 'solicitante':
            return redirect('solicitudes:mis_solicitudes')
        else:
            return redirect('evaluacion:dashboard')

    # Actualizar el estado de la autorización por si está vencida
    autorizacion.actualizar_estado()

    context = {
        'solicitud': solicitud,
        'autorizacion': autorizacion,
        'fecha_impresion': timezone.now(),
    }

    return render(request, 'solicitudes/imprimir_autorizacion.html', context)
