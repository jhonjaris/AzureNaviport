from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from accounts.decorators import role_required
from .models import Incumplimiento, SolicitudSubsanacion, RespuestaSubsanacion, DocumentoSubsanacion
from solicitudes.models import Solicitud, Puerto, LugarPuerto
from control_acceso.models import Autorizacion
from django.forms import modelform_factory, inlineformset_factory


# ========================================
# VISTAS PARA OFICIAL DE ACCESO
# ========================================

@login_required
@role_required('oficial_acceso')
def reportar_incumplimiento(request):
    """Vista para que el oficial de acceso reporte un incumplimiento"""
    if request.method == 'POST':
        try:
            solicitud_id = request.POST.get('solicitud')
            solicitud = get_object_or_404(Solicitud, id=solicitud_id)

            # Obtener autorización si existe
            autorizacion = None
            if hasattr(solicitud, 'autorizacion'):
                autorizacion = solicitud.autorizacion

            # Crear el incumplimiento
            incumplimiento = Incumplimiento.objects.create(
                solicitud=solicitud,
                autorizacion=autorizacion,
                tipo=request.POST.get('tipo'),
                descripcion=request.POST.get('descripcion'),
                fecha_incumplimiento=request.POST.get('fecha_incumplimiento'),
                reportado_por=request.user,
                puerto_id=request.POST.get('puerto'),
                lugar_puerto_id=request.POST.get('lugar_puerto') if request.POST.get('lugar_puerto') else None,
                observaciones=request.POST.get('observaciones', '')
            )

            # Guardar evidencia si se adjuntó
            if request.FILES.get('evidencia'):
                incumplimiento.evidencia = request.FILES['evidencia']
                incumplimiento.save()

            messages.success(request, 'Incumplimiento reportado exitosamente.')
            return redirect('incumplimientos:mis_reportes')

        except Exception as e:
            messages.error(request, f'Error al reportar incumplimiento: {str(e)}')

    # GET request - mostrar formulario
    # Obtener solicitudes aprobadas (con autorización)
    solicitudes = Solicitud.objects.filter(
        estado='aprobada'
    ).select_related('empresa', 'puerto').order_by('-fecha_creacion')[:100]

    puertos = Puerto.objects.filter(activo=True)

    context = {
        'solicitudes': solicitudes,
        'puertos': puertos,
        'tipos_incumplimiento': Incumplimiento.TIPO_CHOICES,
    }
    return render(request, 'incumplimientos/reportar.html', context)


@login_required
@role_required('oficial_acceso')
def lista_incumplimientos_oficial(request):
    """Lista de incumplimientos reportados por este oficial"""
    incumplimientos_list = Incumplimiento.objects.filter(
        reportado_por=request.user
    ).select_related(
        'solicitud__empresa', 'puerto', 'lugar_puerto', 'revisado_por'
    ).order_by('-fecha_incumplimiento')

    # Filtros
    estado = request.GET.get('estado')
    tipo = request.GET.get('tipo')

    if estado:
        incumplimientos_list = incumplimientos_list.filter(estado=estado)
    if tipo:
        incumplimientos_list = incumplimientos_list.filter(tipo=tipo)

    # Estadísticas
    stats = {
        'total': incumplimientos_list.count(),
        'reportados': incumplimientos_list.filter(estado='reportado').count(),
        'en_revision': incumplimientos_list.filter(estado='en_revision').count(),
        'subsanados': incumplimientos_list.filter(estado='subsanado').count(),
    }

    # Paginación
    paginator = Paginator(incumplimientos_list, 15)
    page = request.GET.get('page')
    incumplimientos = paginator.get_page(page)

    context = {
        'incumplimientos': incumplimientos,
        'stats': stats,
        'estados': Incumplimiento.ESTADO_CHOICES,
        'tipos': Incumplimiento.TIPO_CHOICES,
    }
    return render(request, 'incumplimientos/lista_oficial.html', context)


@login_required
def detalle_incumplimiento(request, pk):
    """Vista de detalle de un incumplimiento (accesible para varios roles)"""
    incumplimiento = get_object_or_404(
        Incumplimiento.objects.select_related(
            'solicitud__empresa', 'autorizacion', 'puerto', 'lugar_puerto',
            'reportado_por', 'revisado_por'
        ),
        pk=pk
    )

    # Verificar permisos según rol
    user = request.user
    puede_ver = False

    if user.role == 'oficial_acceso' and incumplimiento.reportado_por == user:
        puede_ver = True
    elif user.role in ['supervisor', 'direccion', 'admin_tic']:
        puede_ver = True
    elif user.role == 'solicitante' and incumplimiento.solicitud.empresa == user.empresa:
        puede_ver = True

    if not puede_ver:
        messages.error(request, 'No tiene permisos para ver este incumplimiento.')
        return redirect('home')

    # Obtener solicitud de subsanación si existe
    subsanacion = None
    if hasattr(incumplimiento, 'solicitud_subsanacion'):
        subsanacion = incumplimiento.solicitud_subsanacion
        # Obtener respuesta si existe
        if hasattr(subsanacion, 'respuesta'):
            subsanacion.respuesta_empresa = subsanacion.respuesta

    context = {
        'incumplimiento': incumplimiento,
        'subsanacion': subsanacion,
    }
    return render(request, 'incumplimientos/detalle.html', context)


# ========================================
# VISTAS PARA SUPERVISOR
# ========================================

@login_required
@role_required(['supervisor', 'direccion'])
def lista_incumplimientos_pendientes(request):
    """Lista de incumplimientos pendientes de revisión (para supervisores)"""
    incumplimientos_list = Incumplimiento.objects.filter(
        estado__in=['reportado', 'en_revision']
    ).select_related(
        'solicitud__empresa', 'puerto', 'reportado_por'
    ).order_by('-fecha_incumplimiento')

    # Filtros
    tipo = request.GET.get('tipo')
    puerto_id = request.GET.get('puerto')

    if tipo:
        incumplimientos_list = incumplimientos_list.filter(tipo=tipo)
    if puerto_id:
        incumplimientos_list = incumplimientos_list.filter(puerto_id=puerto_id)

    # Estadísticas
    stats = {
        'total_pendientes': incumplimientos_list.count(),
        'reportados': incumplimientos_list.filter(estado='reportado').count(),
        'en_revision': incumplimientos_list.filter(estado='en_revision').count(),
    }

    # Paginación
    paginator = Paginator(incumplimientos_list, 15)
    page = request.GET.get('page')
    incumplimientos = paginator.get_page(page)

    puertos = Puerto.objects.filter(activo=True)

    context = {
        'incumplimientos': incumplimientos,
        'stats': stats,
        'tipos': Incumplimiento.TIPO_CHOICES,
        'puertos': puertos,
    }
    return render(request, 'incumplimientos/lista_pendientes.html', context)


@login_required
@role_required(['supervisor', 'direccion'])
def solicitar_subsanacion(request, pk):
    """Vista para que el supervisor solicite subsanación de un incumplimiento"""
    incumplimiento = get_object_or_404(Incumplimiento, pk=pk)

    if not incumplimiento.puede_solicitar_subsanacion():
        messages.error(request, 'Este incumplimiento no puede tener una solicitud de subsanación.')
        return redirect('incumplimientos:pendientes')

    if hasattr(incumplimiento, 'solicitud_subsanacion'):
        messages.warning(request, 'Ya existe una solicitud de subsanación para este incumplimiento.')
        return redirect('incumplimientos:detalle', pk=pk)

    if request.method == 'POST':
        try:
            plazo_dias = int(request.POST.get('plazo_dias', 5))
            fecha_limite = timezone.now() + timedelta(days=plazo_dias)

            # Crear solicitud de subsanación
            subsanacion = SolicitudSubsanacion.objects.create(
                incumplimiento=incumplimiento,
                informacion_requerida=request.POST.get('informacion_requerida'),
                plazo_dias=plazo_dias,
                fecha_limite=fecha_limite,
                solicitado_por=request.user
            )

            # Actualizar estado del incumplimiento
            incumplimiento.estado = 'pendiente_subsanacion'
            incumplimiento.revisado_por = request.user
            incumplimiento.fecha_revision = timezone.now()
            incumplimiento.save()

            messages.success(request, 'Solicitud de subsanación enviada exitosamente.')
            return redirect('incumplimientos:detalle', pk=pk)

        except Exception as e:
            messages.error(request, f'Error al crear solicitud de subsanación: {str(e)}')

    context = {
        'incumplimiento': incumplimiento,
    }
    return render(request, 'incumplimientos/solicitar_subsanacion.html', context)


@login_required
@role_required(['supervisor', 'direccion'])
def lista_subsanaciones(request):
    """Lista de todas las solicitudes de subsanación"""
    subsanaciones_list = SolicitudSubsanacion.objects.select_related(
        'incumplimiento__solicitud__empresa',
        'incumplimiento__puerto',
        'solicitado_por'
    ).order_by('-fecha_solicitud')

    # Filtros
    estado = request.GET.get('estado')
    if estado:
        subsanaciones_list = subsanaciones_list.filter(estado=estado)

    # Estadísticas
    stats = {
        'total': subsanaciones_list.count(),
        'pendientes': subsanaciones_list.filter(estado='pendiente').count(),
        'respondidas': subsanaciones_list.filter(estado='respondida').count(),
        'aprobadas': subsanaciones_list.filter(estado='aprobada').count(),
        'vencidas': subsanaciones_list.filter(estado='vencida').count(),
    }

    # Paginación
    paginator = Paginator(subsanaciones_list, 15)
    page = request.GET.get('page')
    subsanaciones = paginator.get_page(page)

    context = {
        'subsanaciones': subsanaciones,
        'stats': stats,
        'estados': SolicitudSubsanacion.ESTADO_CHOICES,
    }
    return render(request, 'incumplimientos/lista_subsanaciones.html', context)


@login_required
@role_required(['supervisor', 'direccion'])
def revisar_respuesta_subsanacion(request, pk):
    """Vista para que el supervisor revise y apruebe/rechace una respuesta de subsanación"""
    subsanacion = get_object_or_404(
        SolicitudSubsanacion.objects.select_related(
            'incumplimiento__solicitud__empresa',
            'incumplimiento__puerto',
            'respuesta'
        ),
        pk=pk
    )

    if not hasattr(subsanacion, 'respuesta'):
        messages.error(request, 'Esta subsanación aún no ha sido respondida por la empresa.')
        return redirect('incumplimientos:lista_subsanaciones')

    respuesta = subsanacion.respuesta

    if request.method == 'POST':
        accion = request.POST.get('accion')

        try:
            if accion == 'aprobar':
                respuesta.estado = 'aprobada'
                respuesta.revisado_por = request.user
                respuesta.fecha_revision = timezone.now()
                respuesta.comentarios_revision = request.POST.get('comentarios', '')
                respuesta.save()

                # Actualizar estados
                subsanacion.estado = 'aprobada'
                subsanacion.save()

                subsanacion.incumplimiento.estado = 'subsanado'
                subsanacion.incumplimiento.save()

                messages.success(request, 'Subsanación aprobada exitosamente.')

            elif accion == 'rechazar':
                respuesta.estado = 'rechazada'
                respuesta.revisado_por = request.user
                respuesta.fecha_revision = timezone.now()
                respuesta.comentarios_revision = request.POST.get('comentarios', '')
                respuesta.save()

                subsanacion.estado = 'rechazada'
                subsanacion.save()

                messages.warning(request, 'Subsanación rechazada. La empresa deberá enviar una nueva respuesta.')

            return redirect('incumplimientos:lista_subsanaciones')

        except Exception as e:
            messages.error(request, f'Error al procesar la revisión: {str(e)}')

    context = {
        'subsanacion': subsanacion,
        'respuesta': respuesta,
        'documentos': respuesta.documentos.all(),
    }
    return render(request, 'incumplimientos/revisar_subsanacion.html', context)


# ========================================
# VISTAS PARA EMPRESA/SOLICITANTE
# ========================================

@login_required
@role_required('solicitante')
def lista_incumplimientos_empresa(request):
    """Lista de incumplimientos de la empresa del usuario"""
    if not request.user.empresa:
        messages.error(request, 'No tiene una empresa asociada.')
        return redirect('home')

    incumplimientos_list = Incumplimiento.objects.filter(
        solicitud__empresa=request.user.empresa
    ).select_related(
        'solicitud', 'puerto', 'reportado_por'
    ).order_by('-fecha_incumplimiento')

    # Filtros
    estado = request.GET.get('estado')
    if estado:
        incumplimientos_list = incumplimientos_list.filter(estado=estado)

    # Estadísticas
    stats = {
        'total': incumplimientos_list.count(),
        'pendiente_subsanacion': incumplimientos_list.filter(estado='pendiente_subsanacion').count(),
        'subsanados': incumplimientos_list.filter(estado='subsanado').count(),
    }

    # Paginación
    paginator = Paginator(incumplimientos_list, 15)
    page = request.GET.get('page')
    incumplimientos = paginator.get_page(page)

    context = {
        'incumplimientos': incumplimientos,
        'stats': stats,
        'estados': Incumplimiento.ESTADO_CHOICES,
    }
    return render(request, 'incumplimientos/lista_empresa.html', context)


@login_required
@role_required('solicitante')
def responder_subsanacion(request, pk):
    """Vista para que la empresa responda una solicitud de subsanación"""
    subsanacion = get_object_or_404(
        SolicitudSubsanacion.objects.select_related(
            'incumplimiento__solicitud__empresa',
            'incumplimiento__puerto'
        ),
        pk=pk
    )

    # Verificar que pertenece a la empresa del usuario
    if subsanacion.incumplimiento.solicitud.empresa != request.user.empresa:
        messages.error(request, 'No tiene permisos para responder esta subsanación.')
        return redirect('incumplimientos:mis_incumplimientos')

    # Verificar que no haya sido respondida
    if hasattr(subsanacion, 'respuesta'):
        messages.warning(request, 'Esta subsanación ya ha sido respondida.')
        return redirect('incumplimientos:detalle', pk=subsanacion.incumplimiento.pk)

    if request.method == 'POST':
        try:
            # Crear respuesta
            respuesta = RespuestaSubsanacion.objects.create(
                solicitud_subsanacion=subsanacion,
                explicacion=request.POST.get('explicacion'),
                medidas_preventivas=request.POST.get('medidas_preventivas', ''),
                respondido_por=request.user
            )

            # Guardar documentos adjuntos
            documentos_tipos = request.POST.getlist('tipo_documento[]')
            documentos_nombres = request.POST.getlist('nombre_documento[]')
            documentos_archivos = request.FILES.getlist('archivo[]')

            for i, archivo in enumerate(documentos_archivos):
                if i < len(documentos_tipos) and i < len(documentos_nombres):
                    DocumentoSubsanacion.objects.create(
                        respuesta=respuesta,
                        tipo_documento=documentos_tipos[i],
                        nombre=documentos_nombres[i],
                        archivo=archivo
                    )

            # Actualizar estado de subsanación
            subsanacion.estado = 'respondida'
            subsanacion.save()

            messages.success(request, 'Respuesta enviada exitosamente. Será revisada por un supervisor.')
            return redirect('incumplimientos:detalle', pk=subsanacion.incumplimiento.pk)

        except Exception as e:
            messages.error(request, f'Error al enviar respuesta: {str(e)}')

    context = {
        'subsanacion': subsanacion,
        'tipos_documento': DocumentoSubsanacion.TIPO_DOCUMENTO_CHOICES,
    }
    return render(request, 'incumplimientos/responder_subsanacion.html', context)
