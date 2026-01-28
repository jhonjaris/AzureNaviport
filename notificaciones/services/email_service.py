"""
Servicio centralizado de envío de emails para el sistema NaviPortRD
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from accounts.models import User
from ..models import ConfiguracionEmail, EventoSistema, LogNotificacion, DestinatarioEvento


class EmailService:
    """Servicio para enviar emails con logging y gestión de destinatarios"""

    @staticmethod
    def obtener_emails_por_rol(rol):
        """Obtiene lista de emails de usuarios con un rol específico"""
        usuarios = User.objects.filter(role=rol, activo=True, email__isnull=False).exclude(email='')
        return list(usuarios.values_list('email', flat=True))

    @staticmethod
    def resolver_destinatarios(evento):
        """Resuelve todos los destinatarios configurados para un evento"""
        destinatarios = evento.get_destinatarios()
        emails = []

        for dest in destinatarios:
            if dest.tipo_destinatario == 'email':
                emails.append(dest.email_especifico)
            elif dest.tipo_destinatario == 'rol':
                emails.extend(EmailService.obtener_emails_por_rol(dest.rol))

        # Eliminar duplicados
        return list(set(emails))

    @staticmethod
    def aplicar_configuracion():
        """Aplica la configuración de email activa al sistema"""
        config = ConfiguracionEmail.get_configuracion_activa()
        if config and config.email_enabled:
            config.aplicar_configuracion()
            return True
        return False

    @staticmethod
    def enviar_notificacion(
        codigo_evento,
        contexto=None,
        destinatarios_adicionales=None,
        forzar_destinatarios=False
    ):
        """
        Envía una notificación basada en un evento del sistema

        Args:
            codigo_evento: Código del evento (ej: 'solicitud_recibida')
            contexto: Diccionario con variables para el template
            destinatarios_adicionales: Lista de emails adicionales
            forzar_destinatarios: Si True, solo usa destinatarios_adicionales

        Returns:
            Tuple (success: bool, mensaje: str, log_id: int)
        """
        # Obtener evento
        try:
            evento = EventoSistema.objects.get(codigo=codigo_evento, activo=True)
        except EventoSistema.DoesNotExist:
            return False, f"Evento '{codigo_evento}' no encontrado o inactivo", None

        # Resolver destinatarios
        if forzar_destinatarios and destinatarios_adicionales:
            emails_destinatarios = destinatarios_adicionales
        else:
            emails_destinatarios = EmailService.resolver_destinatarios(evento)
            if destinatarios_adicionales:
                emails_destinatarios.extend(destinatarios_adicionales)
                emails_destinatarios = list(set(emails_destinatarios))

        if not emails_destinatarios:
            return False, "No hay destinatarios configurados para este evento", None

        # Preparar contexto
        if contexto is None:
            contexto = {}

        # Generar asunto y mensaje
        asunto = evento.asunto_email.format(**contexto)
        mensaje_texto = evento.mensaje_texto_plano.format(**contexto) if evento.mensaje_texto_plano else ''

        # Generar HTML si hay template
        mensaje_html = ''
        if evento.template_html:
            try:
                mensaje_html = render_to_string(evento.template_html, contexto)
            except Exception as e:
                mensaje_html = f'<p>{mensaje_texto}</p>'

        # Crear log
        log = LogNotificacion.objects.create(
            evento=evento,
            destinatarios=', '.join(emails_destinatarios),
            asunto=asunto,
            mensaje_html=mensaje_html,
            mensaje_texto=mensaje_texto,
            metadata=contexto,
            estado='pendiente'
        )

        # Aplicar configuración
        if not EmailService.aplicar_configuracion():
            log.marcar_como_error('Configuración de email no disponible o deshabilitada')
            return False, 'Sistema de email no configurado', log.id

        # Enviar email
        try:
            if mensaje_html:
                # Email con HTML
                email = EmailMultiAlternatives(
                    subject=asunto,
                    body=mensaje_texto,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=emails_destinatarios
                )
                email.attach_alternative(mensaje_html, "text/html")
                email.send(fail_silently=False)
            else:
                # Email solo texto
                send_mail(
                    subject=asunto,
                    message=mensaje_texto,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=emails_destinatarios,
                    fail_silently=False
                )

            # Marcar como enviado
            log.marcar_como_enviado()

            # Incrementar contador
            config = ConfiguracionEmail.get_configuracion_activa()
            if config:
                config.incrementar_contador_emails()

            return True, f'Email enviado a {len(emails_destinatarios)} destinatario(s)', log.id

        except Exception as e:
            # Marcar como error
            log.marcar_como_error(str(e))
            return False, f'Error al enviar email: {str(e)}', log.id

    @staticmethod
    def enviar_simple(asunto, mensaje, destinatarios):
        """
        Envía un email simple sin usar el sistema de eventos

        Args:
            asunto: Asunto del email
            mensaje: Mensaje en texto plano
            destinatarios: Lista de emails

        Returns:
            Tuple (success: bool, mensaje: str)
        """
        if not EmailService.aplicar_configuracion():
            return False, 'Sistema de email no configurado'

        try:
            send_mail(
                subject=asunto,
                message=mensaje,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=destinatarios,
                fail_silently=False
            )

            # Incrementar contador
            config = ConfiguracionEmail.get_configuracion_activa()
            if config:
                config.incrementar_contador_emails()

            return True, f'Email enviado a {len(destinatarios)} destinatario(s)'

        except Exception as e:
            return False, f'Error al enviar email: {str(e)}'


# Atajos para eventos comunes
def notificar_solicitud_recibida(solicitud):
    """Notifica que se recibió una nueva solicitud"""
    contexto = {
        'solicitud_codigo': solicitud.codigo,
        'empresa_nombre': solicitud.empresa.nombre,
        'fecha': timezone.now().strftime('%d/%m/%Y %H:%M'),
    }
    return EmailService.enviar_notificacion('solicitud_recibida', contexto)


def notificar_solicitud_aprobada(solicitud):
    """Notifica que una solicitud fue aprobada"""
    contexto = {
        'solicitud_codigo': solicitud.codigo,
        'empresa_nombre': solicitud.empresa.nombre,
        'fecha_aprobacion': timezone.now().strftime('%d/%m/%Y %H:%M'),
    }
    # Notificar a la empresa específica
    email_empresa = solicitud.solicitante.email
    return EmailService.enviar_notificacion(
        'solicitud_aprobada',
        contexto,
        destinatarios_adicionales=[email_empresa] if email_empresa else None
    )


def notificar_solicitud_rechazada(solicitud, motivo=''):
    """Notifica que una solicitud fue rechazada"""
    contexto = {
        'solicitud_codigo': solicitud.codigo,
        'empresa_nombre': solicitud.empresa.nombre,
        'motivo': motivo,
    }
    email_empresa = solicitud.solicitante.email
    return EmailService.enviar_notificacion(
        'solicitud_rechazada',
        contexto,
        destinatarios_adicionales=[email_empresa] if email_empresa else None
    )


def notificar_asignacion_evaluador(solicitud, evaluador):
    """Notifica a un evaluador que se le asignó una solicitud"""
    contexto = {
        'solicitud_codigo': solicitud.codigo,
        'empresa_nombre': solicitud.empresa.nombre,
        'evaluador_nombre': evaluador.get_full_name(),
    }
    email_evaluador = evaluador.email
    return EmailService.enviar_notificacion(
        'asignacion_evaluador',
        contexto,
        destinatarios_adicionales=[email_evaluador] if email_evaluador else None
    )
