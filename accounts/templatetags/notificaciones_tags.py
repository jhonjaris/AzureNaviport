from django import template
from django.utils import timezone
from django.db import models
from accounts.models import NotificacionEmpresa
from evaluacion.models import ConfiguracionEvaluacion

register = template.Library()

@register.simple_tag(takes_context=True)
def get_notificaciones(context):
    """Template tag para obtener las notificaciones del usuario"""
    request = context.get('request')
    if not request:
        return []

    user = request.user
    notificaciones_activas = []

    if user.is_authenticated and user.is_solicitante():
        # Obtener empresa del usuario
        try:
            empresa = user.empresas_representadas.first()
        except Exception:
            empresa = None

        if empresa:
            # Generar notificaciones automáticas si es necesario
            try:
                config = ConfiguracionEvaluacion.get_configuracion()
                NotificacionEmpresa.crear_notificacion_expiracion(empresa, user, config)
            except Exception:
                # Log error pero no interrumpir la renderización
                pass

            # Obtener notificaciones activas
            notificaciones_activas = list(NotificacionEmpresa.objects.filter(
                usuario=user,
                activa=True,
                cerrada_por_usuario=False,
                mostrar_desde__lte=timezone.now()
            ).filter(
                models.Q(mostrar_hasta__isnull=True) |
                models.Q(mostrar_hasta__gte=timezone.now())
            ).order_by('tipo', '-created_at')[:5])  # Máximo 5 notificaciones

    return notificaciones_activas


@register.inclusion_tag('accounts/notificaciones_bar.html')
def mostrar_notificaciones_lista(notificaciones, user):
    """Template tag para mostrar la barra de notificaciones (sin takes_context)"""
    return {
        'notificaciones': notificaciones,
        'user': user
    }

@register.simple_tag
def contar_notificaciones(user):
    """Cuenta las notificaciones activas del usuario"""
    if not user.is_authenticated or not user.is_solicitante():
        return 0
    
    return NotificacionEmpresa.objects.filter(
        usuario=user,
        activa=True,
        cerrada_por_usuario=False,
        mostrar_desde__lte=timezone.now()
    ).filter(
        models.Q(mostrar_hasta__isnull=True) | 
        models.Q(mostrar_hasta__gte=timezone.now())
    ).count()

@register.filter
def notificacion_color_bootstrap(tipo):
    """Convierte el tipo de notificación a clase Bootstrap"""
    colores = {
        'critico': 'alert-danger',
        'advertencia': 'alert-warning',
        'informativo': 'alert-info',
        'vencido': 'alert-dark'
    }
    return colores.get(tipo, 'alert-secondary')

@register.filter
def notificacion_icono(tipo):
    """Retorna el ícono según el tipo de notificación"""
    iconos = {
        'critico': '🔴',
        'advertencia': '🟠',
        'informativo': '🟡',
        'vencido': '⚫'
    }
    return iconos.get(tipo, 'ℹ️')