"""
Vistas para gestión de Solicitudes Excepcionales
Permite a supervisores y dirección habilitar empresas para solicitudes excepcionales
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Prefetch
from django.utils import timezone
from django.core.paginator import Paginator
from accounts.models import Empresa, AprobacionExcepcional
from accounts.decorators import role_required


@login_required
@role_required('supervisor', 'direccion')
def lista_empresas_excepcionales(request):
    """Lista todas las empresas con información sobre permisos excepcionales"""

    # Filtros
    busqueda = request.GET.get('q', '')
    estado_permiso = request.GET.get('estado', '')  # 'con_permiso', 'sin_permiso', 'todas'

    # Query base con anotaciones
    empresas = Empresa.objects.select_related('representante_legal').annotate(
        total_aprobaciones=Count('aprobaciones_excepcionales'),
        aprobaciones_activas=Count('aprobaciones_excepcionales', filter=Q(aprobaciones_excepcionales__estado='activa'))
    )

    # Aplicar búsqueda
    if busqueda:
        empresas = empresas.filter(
            Q(nombre__icontains=busqueda) |
            Q(rnc__icontains=busqueda) |
            Q(email__icontains=busqueda)
        )

    # Filtro por estado de permiso
    if estado_permiso == 'con_permiso':
        empresas = empresas.filter(puede_solicitud_excepcional=True)
    elif estado_permiso == 'sin_permiso':
        empresas = empresas.filter(puede_solicitud_excepcional=False)

    # Ordenamiento
    empresas = empresas.order_by('-puede_solicitud_excepcional', 'nombre')

    # Paginación
    paginator = Paginator(empresas, 20)
    page = request.GET.get('page')
    empresas_page = paginator.get_page(page)

    context = {
        'empresas': empresas_page,
        'busqueda': busqueda,
        'estado_permiso': estado_permiso,
        'total_empresas': empresas.count(),
        'total_con_permiso': empresas.filter(puede_solicitud_excepcional=True).count(),
    }

    return render(request, 'supervisor/excepcionales/lista_empresas.html', context)


@login_required
@role_required('supervisor', 'direccion')
def aprobar_excepcional(request, empresa_id):
    """Aprueba una solicitud excepcional para una empresa"""

    empresa = get_object_or_404(Empresa, id=empresa_id)

    if request.method == 'POST':
        motivo = request.POST.get('motivo', '').strip()
        observaciones = request.POST.get('observaciones', '').strip()
        fecha_vencimiento = request.POST.get('fecha_vencimiento', None)

        # Validar motivo
        if not motivo or len(motivo) < 10:
            messages.error(request, 'El motivo debe tener al menos 10 caracteres.')
            return redirect('supervisor:aprobar_excepcional', empresa_id=empresa_id)

        # Crear la aprobación
        aprobacion = AprobacionExcepcional.objects.create(
            empresa=empresa,
            motivo=motivo,
            observaciones=observaciones,
            aprobada_por=request.user,
            estado='activa',
            fecha_vencimiento=fecha_vencimiento if fecha_vencimiento else None
        )

        # La activación de la empresa se hace automáticamente en el save() del modelo
        messages.success(
            request,
            f'Permiso excepcional aprobado para {empresa.nombre}. '
            f'La empresa ahora puede realizar solicitudes excepcionales.'
        )

        # Enviar notificación por email
        from notificaciones.services.email_service import EmailService

        # Obtener emails de admins de la empresa
        empresa_emails = [
            user.email for user in empresa.usuarios.filter(es_admin_empresa=True)
            if user.email
        ]

        if empresa_emails:
            contexto = {
                'empresa': empresa.nombre,
                'motivo': motivo,
                'aprobada_por': request.user.get_full_name(),
                'fecha_aprobacion': timezone.now().strftime('%d/%m/%Y %H:%M'),
                'fecha_vencimiento': fecha_vencimiento if fecha_vencimiento else 'Indefinido',
            }

            EmailService.enviar_notificacion(
                codigo_evento='permiso_excepcional_aprobado',
                contexto=contexto,
                destinatarios_adicionales=empresa_emails,
                forzar_destinatarios=True
            )

        return redirect('supervisor:lista_empresas_excepcionales')

    # GET - Mostrar formulario
    # Verificar si ya tiene permisos activos
    aprobacion_activa = empresa.aprobaciones_excepcionales.filter(estado='activa').first()

    context = {
        'empresa': empresa,
        'aprobacion_activa': aprobacion_activa,
    }

    return render(request, 'supervisor/excepcionales/aprobar.html', context)


@login_required
@role_required('supervisor', 'direccion')
def revocar_excepcional(request, empresa_id):
    """Revoca el permiso excepcional de una empresa"""

    empresa = get_object_or_404(Empresa, id=empresa_id)

    # Buscar aprobación activa
    aprobacion_activa = empresa.aprobaciones_excepcionales.filter(estado='activa').first()

    if not aprobacion_activa:
        messages.warning(request, f'{empresa.nombre} no tiene permisos excepcionales activos.')
        return redirect('supervisor:lista_empresas_excepcionales')

    if request.method == 'POST':
        motivo_revocacion = request.POST.get('motivo_revocacion', '').strip()

        if not motivo_revocacion or len(motivo_revocacion) < 10:
            messages.error(request, 'El motivo de revocación debe tener al menos 10 caracteres.')
            return redirect('supervisor:revocar_excepcional', empresa_id=empresa_id)

        # Revocar usando el método del modelo
        aprobacion_activa.revocar(
            usuario=request.user,
            motivo=motivo_revocacion
        )

        messages.success(
            request,
            f'Permiso excepcional revocado para {empresa.nombre}.'
        )

        # Enviar notificación por email
        from notificaciones.services.email_service import EmailService

        empresa_emails = [
            user.email for user in empresa.usuarios.filter(es_admin_empresa=True)
            if user.email
        ]

        if empresa_emails:
            contexto = {
                'empresa': empresa.nombre,
                'motivo_revocacion': motivo_revocacion,
                'revocada_por': request.user.get_full_name(),
                'fecha_revocacion': timezone.now().strftime('%d/%m/%Y %H:%M'),
            }

            EmailService.enviar_notificacion(
                codigo_evento='permiso_excepcional_revocado',
                contexto=contexto,
                destinatarios_adicionales=empresa_emails,
                forzar_destinatarios=True
            )

        return redirect('supervisor:lista_empresas_excepcionales')

    # GET - Mostrar formulario de confirmación
    context = {
        'empresa': empresa,
        'aprobacion': aprobacion_activa,
    }

    return render(request, 'supervisor/excepcionales/revocar.html', context)


@login_required
@role_required('supervisor', 'direccion')
def historial_excepcionales(request, empresa_id):
    """Muestra el historial completo de aprobaciones excepcionales de una empresa"""

    empresa = get_object_or_404(Empresa, id=empresa_id)

    # Obtener todas las aprobaciones (activas y revocadas)
    aprobaciones = empresa.aprobaciones_excepcionales.select_related(
        'aprobada_por',
        'revocada_por'
    ).order_by('-fecha_aprobacion')

    context = {
        'empresa': empresa,
        'aprobaciones': aprobaciones,
    }

    return render(request, 'supervisor/excepcionales/historial.html', context)


@login_required
@role_required('supervisor', 'direccion')
def dashboard_excepcionales(request):
    """Dashboard con estadísticas de solicitudes excepcionales"""

    # Estadísticas generales
    total_empresas = Empresa.objects.count()
    empresas_con_permiso = Empresa.objects.filter(puede_solicitud_excepcional=True).count()

    total_aprobaciones = AprobacionExcepcional.objects.count()
    aprobaciones_activas = AprobacionExcepcional.objects.filter(estado='activa').count()
    aprobaciones_revocadas = AprobacionExcepcional.objects.filter(estado='revocada').count()

    # Aprobaciones recientes
    aprobaciones_recientes = AprobacionExcepcional.objects.select_related(
        'empresa',
        'aprobada_por'
    ).order_by('-fecha_aprobacion')[:10]

    # Aprobaciones próximas a vencer (30 días)
    from datetime import timedelta
    fecha_limite = timezone.now().date() + timedelta(days=30)

    aprobaciones_por_vencer = AprobacionExcepcional.objects.filter(
        estado='activa',
        fecha_vencimiento__isnull=False,
        fecha_vencimiento__lte=fecha_limite
    ).select_related('empresa').order_by('fecha_vencimiento')

    context = {
        'total_empresas': total_empresas,
        'empresas_con_permiso': empresas_con_permiso,
        'porcentaje_con_permiso': round((empresas_con_permiso / total_empresas * 100), 1) if total_empresas > 0 else 0,
        'total_aprobaciones': total_aprobaciones,
        'aprobaciones_activas': aprobaciones_activas,
        'aprobaciones_revocadas': aprobaciones_revocadas,
        'aprobaciones_recientes': aprobaciones_recientes,
        'aprobaciones_por_vencer': aprobaciones_por_vencer,
    }

    return render(request, 'supervisor/excepcionales/dashboard.html', context)
