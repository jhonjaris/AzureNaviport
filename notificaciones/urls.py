from django.urls import path
from . import views

app_name = 'notificaciones'

urlpatterns = [
    # Configuración de Correo
    path('configuracion/', views.configuracion_correo, name='configuracion_correo'),
    path('configuracion/editar/', views.editar_configuracion_correo, name='editar_configuracion_correo'),
    path('configuracion/enviar-prueba/', views.enviar_email_prueba, name='enviar_email_prueba'),

    # Gestión de Eventos
    path('eventos/', views.gestionar_eventos, name='gestionar_eventos'),
    path('eventos/<int:evento_id>/editar/', views.editar_evento, name='editar_evento'),
    path('eventos/<int:evento_id>/destinatarios/', views.gestionar_destinatarios, name='gestionar_destinatarios'),

    # Logs de Notificaciones
    path('logs/', views.ver_logs_notificaciones, name='ver_logs'),
    path('logs/<int:log_id>/', views.detalle_log, name='detalle_log'),
]
