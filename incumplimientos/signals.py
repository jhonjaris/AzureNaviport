from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Incumplimiento, SolicitudSubsanacion, RespuestaSubsanacion
from notificaciones.services.email_service import EmailService


@receiver(post_save, sender=Incumplimiento)
def notificar_incumplimiento_reportado(sender, instance, created, **kwargs):
    """Notifica cuando se reporta un incumplimiento nuevo"""
    if created:
        # Notificar a la empresa
        if instance.solicitud.empresa:
            empresa_emails = [user.email for user in instance.solicitud.empresa.usuarios.filter(es_admin_empresa=True) if user.email]
            
            if empresa_emails:
                contexto = {
                    'empresa': instance.solicitud.empresa.nombre,
                    'tipo': instance.get_tipo_display(),
                    'descripcion': instance.descripcion,
                    'fecha': instance.fecha_incumplimiento,
                    'puerto': instance.puerto.nombre,
                    'solicitud_id': instance.solicitud.id,
                }
                
                EmailService.enviar_notificacion(
                    codigo_evento='incumplimiento_reportado',
                    contexto=contexto,
                    destinatarios_adicionales=empresa_emails,
                    forzar_destinatarios=True
                )


@receiver(post_save, sender=SolicitudSubsanacion)
def notificar_subsanacion_solicitada(sender, instance, created, **kwargs):
    """Notifica cuando se solicita una subsanación"""
    if created:
        # Notificar a la empresa
        empresa = instance.incumplimiento.solicitud.empresa
        if empresa:
            empresa_emails = [user.email for user in empresa.usuarios.filter(es_admin_empresa=True) if user.email]
            
            if empresa_emails:
                contexto = {
                    'empresa': empresa.nombre,
                    'tipo_incumplimiento': instance.incumplimiento.get_tipo_display(),
                    'informacion_requerida': instance.informacion_requerida,
                    'plazo_dias': instance.plazo_dias,
                    'fecha_limite': instance.fecha_limite,
                }
                
                EmailService.enviar_notificacion(
                    codigo_evento='subsanacion_solicitada',
                    contexto=contexto,
                    destinatarios_adicionales=empresa_emails,
                    forzar_destinatarios=True
                )


@receiver(post_save, sender=RespuestaSubsanacion)
def notificar_subsanacion_respondida(sender, instance, created, **kwargs):
    """Notifica cuando la empresa responde una subsanación"""
    if created:
        # Notificar al supervisor que solicitó la subsanación
        supervisor = instance.solicitud_subsanacion.solicitado_por
        
        if supervisor and supervisor.email:
            contexto = {
                'empresa': instance.solicitud_subsanacion.incumplimiento.solicitud.empresa.nombre,
                'tipo_incumplimiento': instance.solicitud_subsanacion.incumplimiento.get_tipo_display(),
                'explicacion': instance.explicacion,
                'respondido_por': instance.respondido_por.get_full_name(),
            }
            
            EmailService.enviar_notificacion(
                codigo_evento='subsanacion_respondida',
                contexto=contexto,
                destinatarios_adicionales=[supervisor.email],
                forzar_destinatarios=True
            )
    
    # Notificar cuando se aprueba o rechaza
    elif not created:
        if instance.estado in ['aprobada', 'rechazada']:
            # Notificar a la empresa
            empresa = instance.solicitud_subsanacion.incumplimiento.solicitud.empresa
            if empresa:
                empresa_emails = [user.email for user in empresa.usuarios.filter(es_admin_empresa=True) if user.email]
                
                if empresa_emails:
                    contexto = {
                        'empresa': empresa.nombre,
                        'estado': instance.get_estado_display(),
                        'comentarios': instance.comentarios_revision,
                        'revisado_por': instance.revisado_por.get_full_name() if instance.revisado_por else 'N/A',
                    }
                    
                    EmailService.enviar_notificacion(
                        codigo_evento='subsanacion_revisada',
                        contexto=contexto,
                        destinatarios_adicionales=empresa_emails,
                        forzar_destinatarios=True
                    )
