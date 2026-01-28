from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from accounts.decorators import can_evaluate_required
from .models import ConfiguracionEmail, EventoSistema, DestinatarioEvento, LogNotificacion


# ===========================
# CONFIGURACIÓN DE CORREO
# ===========================

@can_evaluate_required
def configuracion_correo(request):
    """Vista principal de configuración de correo"""
    config = ConfiguracionEmail.get_configuracion_activa()

    context = {
        'config': config,
        'tiene_configuracion': config is not None,
    }
    return render(request, 'notificaciones/configuracion_correo.html', context)


@can_evaluate_required
@require_http_methods(["GET", "POST"])
def editar_configuracion_correo(request):
    """Editar o crear configuración de correo"""
    config = ConfiguracionEmail.get_configuracion_activa()

    if request.method == 'POST':
        try:
            # Si no existe configuración, crear una nueva
            if not config:
                config = ConfiguracionEmail()

            # Actualizar campos
            config.nombre = request.POST.get('nombre', 'Configuración Principal')
            config.tipo_proveedor = request.POST.get('tipo_proveedor', 'custom')
            config.email_host = request.POST.get('email_host')
            config.email_port = int(request.POST.get('email_port', 587))
            config.email_use_tls = request.POST.get('email_use_tls') == 'on'
            config.email_use_ssl = request.POST.get('email_use_ssl') == 'on'
            config.email_host_user = request.POST.get('email_host_user')
            config.email_host_password = request.POST.get('email_host_password')
            config.default_from_email = request.POST.get('default_from_email')
            config.email_enabled = request.POST.get('email_enabled') == 'on'

            # Autoconfigurar según proveedor
            if config.tipo_proveedor == 'gmail':
                config.email_host = 'smtp.gmail.com'
                config.email_port = 587
                config.email_use_tls = True
                config.email_use_ssl = False
            elif config.tipo_proveedor == 'outlook':
                config.email_host = 'smtp-mail.outlook.com'
                config.email_port = 587
                config.email_use_tls = True
                config.email_use_ssl = False

            config.save()

            messages.success(request, 'Configuración de correo guardada exitosamente')
            return redirect('notificaciones:configuracion_correo')

        except Exception as e:
            messages.error(request, f'Error al guardar configuración: {str(e)}')

    context = {
        'config': config,
        'tiene_configuracion': config is not None,
    }
    return render(request, 'notificaciones/editar_configuracion_correo.html', context)


@can_evaluate_required
@require_http_methods(["POST"])
def enviar_email_prueba(request):
    """Enviar email de prueba"""
    config = ConfiguracionEmail.get_configuracion_activa()

    if not config:
        return JsonResponse({
            'success': False,
            'message': 'No hay configuración de correo'
        })

    email_destino = request.POST.get('email_destino')

    if not email_destino:
        return JsonResponse({
            'success': False,
            'message': 'Debe proporcionar un email de destino'
        })

    # Enviar email de prueba
    success, message = config.enviar_email_prueba(email_destino)

    return JsonResponse({
        'success': success,
        'message': message
    })


# ===========================
# GESTIÓN DE EVENTOS
# ===========================

@can_evaluate_required
def gestionar_eventos(request):
    """Vista principal para gestionar eventos del sistema"""
    eventos = EventoSistema.objects.all().order_by('nombre')

    # Contar destinatarios por evento
    for evento in eventos:
        evento.total_destinatarios = evento.destinatarios.filter(activo=True).count()

    context = {
        'eventos': eventos,
        'total_eventos': eventos.count(),
        'eventos_activos': eventos.filter(activo=True).count(),
    }
    return render(request, 'notificaciones/gestionar_eventos.html', context)


@can_evaluate_required
@require_http_methods(["GET", "POST"])
def editar_evento(request, evento_id):
    """Editar un evento del sistema"""
    evento = get_object_or_404(EventoSistema, pk=evento_id)

    if request.method == 'POST':
        try:
            evento.nombre = request.POST.get('nombre')
            evento.descripcion = request.POST.get('descripcion', '')
            evento.asunto_email = request.POST.get('asunto_email')
            evento.template_html = request.POST.get('template_html', '')
            evento.mensaje_texto_plano = request.POST.get('mensaje_texto_plano', '')
            evento.activo = request.POST.get('activo') == 'on'

            evento.save()

            messages.success(request, f'Evento "{evento.nombre}" actualizado exitosamente')
            return redirect('notificaciones:gestionar_eventos')

        except Exception as e:
            messages.error(request, f'Error al actualizar evento: {str(e)}')

    # Obtener destinatarios actuales
    destinatarios = evento.destinatarios.all()

    context = {
        'evento': evento,
        'destinatarios': destinatarios,
    }
    return render(request, 'notificaciones/editar_evento.html', context)


@can_evaluate_required
@require_http_methods(["GET", "POST"])
def gestionar_destinatarios(request, evento_id):
    """Gestionar destinatarios de un evento"""
    evento = get_object_or_404(EventoSistema, pk=evento_id)
    destinatarios = evento.destinatarios.all().order_by('tipo_destinatario', 'rol')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'agregar':
            try:
                tipo = request.POST.get('tipo_destinatario')

                destinatario = DestinatarioEvento(
                    evento=evento,
                    tipo_destinatario=tipo,
                )

                if tipo == 'rol':
                    destinatario.rol = request.POST.get('rol')
                else:
                    destinatario.email_especifico = request.POST.get('email_especifico')

                destinatario.save()
                messages.success(request, 'Destinatario agregado exitosamente')

            except Exception as e:
                messages.error(request, f'Error al agregar destinatario: {str(e)}')

        elif action == 'eliminar':
            destinatario_id = request.POST.get('destinatario_id')
            DestinatarioEvento.objects.filter(pk=destinatario_id).delete()
            messages.success(request, 'Destinatario eliminado')

        return redirect('notificaciones:gestionar_destinatarios', evento_id=evento_id)

    context = {
        'evento': evento,
        'destinatarios': destinatarios,
        'roles_choices': DestinatarioEvento.ROL_CHOICES,
    }
    return render(request, 'notificaciones/gestionar_destinatarios.html', context)


# ===========================
# LOGS DE NOTIFICACIONES
# ===========================

@can_evaluate_required
def ver_logs_notificaciones(request):
    """Ver logs de notificaciones enviadas"""
    logs = LogNotificacion.objects.all().order_by('-fecha_creacion')[:100]

    # Filtros
    evento_id = request.GET.get('evento')
    estado = request.GET.get('estado')

    if evento_id:
        logs = logs.filter(evento_id=evento_id)

    if estado:
        logs = logs.filter(estado=estado)

    # Estadísticas
    total_logs = LogNotificacion.objects.count()
    total_enviados = LogNotificacion.objects.filter(exitoso=True).count()
    total_errores = LogNotificacion.objects.filter(exitoso=False, estado='error').count()

    context = {
        'logs': logs,
        'total_logs': total_logs,
        'total_enviados': total_enviados,
        'total_errores': total_errores,
        'eventos': EventoSistema.objects.all(),
    }
    return render(request, 'notificaciones/ver_logs.html', context)


@can_evaluate_required
def detalle_log(request, log_id):
    """Ver detalle de un log de notificación"""
    log = get_object_or_404(LogNotificacion, pk=log_id)

    context = {
        'log': log,
    }
    return render(request, 'notificaciones/detalle_log.html', context)
