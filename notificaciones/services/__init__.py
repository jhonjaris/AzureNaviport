"""
Servicios de la app notificaciones
"""
from .email_service import (
    EmailService,
    notificar_solicitud_recibida,
    notificar_solicitud_aprobada,
    notificar_solicitud_rechazada,
    notificar_asignacion_evaluador,
)

__all__ = [
    'EmailService',
    'notificar_solicitud_recibida',
    'notificar_solicitud_aprobada',
    'notificar_solicitud_rechazada',
    'notificar_asignacion_evaluador',
]
