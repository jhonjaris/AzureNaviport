from django.urls import path
from .views import (
    login_view, dashboard_redirect, logout_view, profile_view, change_password_view,
    check_session_status, validate_cedula_rnc, cerrar_notificacion,
    gestionar_usuarios, crear_usuario, editar_usuario, eliminar_usuario, toggle_admin_empresa,
    toggle_usuario_activo, historial_usuario,
    password_reset_request, password_reset_done, password_reset_confirm, password_reset_complete,
    notificar_admin, notificar_admin_ajax, ayuda_view
)

app_name = 'accounts'

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_redirect, name='dashboard'),
    path('profile/', profile_view, name='profile'),
    path('change-password/', change_password_view, name='change_password'),
    path('ayuda/', ayuda_view, name='ayuda'),

    # Gestión de usuarios
    path('usuarios/', gestionar_usuarios, name='gestionar_usuarios'),
    path('usuarios/crear/', crear_usuario, name='crear_usuario'),
    path('usuarios/<int:usuario_id>/editar/', editar_usuario, name='editar_usuario'),
    path('usuarios/<int:usuario_id>/eliminar/', eliminar_usuario, name='eliminar_usuario'),
    path('usuarios/<int:usuario_id>/historial/', historial_usuario, name='historial_usuario'),
    path('usuarios/<int:usuario_id>/notificar-admin/', notificar_admin, name='notificar_admin'),
    path('notificar-admin/', notificar_admin_ajax, name='notificar_admin_ajax'),
    
    # Password reset
    path('password-reset/', password_reset_request, name='password_reset'),
    path('password-reset/done/', password_reset_done, name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', password_reset_confirm, name='password_reset_confirm'),
    path('password-reset/complete/', password_reset_complete, name='password_reset_complete'),
    
    # API endpoints
    path('api/session-status/', check_session_status, name='session_status'),
    path('api/validate-cedula-rnc/', validate_cedula_rnc, name='validate_cedula_rnc'),
    path('api/cerrar-notificacion/', cerrar_notificacion, name='cerrar_notificacion'),
    path('api/toggle-admin-empresa/<int:usuario_id>/', toggle_admin_empresa, name='toggle_admin_empresa'),
    path('api/toggle-usuario-activo/<int:usuario_id>/', toggle_usuario_activo, name='toggle_usuario_activo'),
] 