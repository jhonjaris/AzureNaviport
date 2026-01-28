from django.urls import path
from .views import (
    dashboard,
    verificar_qr,
    autorizar_ingreso,
    denegar_acceso,
    reportar_discrepancia,
    listar_autorizaciones,
    solicitar_extension,
    listar_extensiones_pendientes,
    aprobar_extension,
    rechazar_extension,
    historial_extensiones
)

app_name = 'control_acceso'

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
    path('autorizaciones/', listar_autorizaciones, name='listar_autorizaciones'),
    path('verificar-qr/', verificar_qr, name='verificar_qr'),
    path('autorizar/<str:codigo>/', autorizar_ingreso, name='autorizar_ingreso'),
    path('denegar/<str:codigo>/', denegar_acceso, name='denegar_acceso'),
    path('discrepancia/<str:codigo>/', reportar_discrepancia, name='reportar_discrepancia'),

    # Extensiones de validez
    path('extensiones/', listar_extensiones_pendientes, name='listar_extensiones_pendientes'),
    path('extensiones/<int:autorizacion_id>/solicitar/', solicitar_extension, name='solicitar_extension'),
    path('extensiones/<int:extension_id>/aprobar/', aprobar_extension, name='aprobar_extension'),
    path('extensiones/<int:extension_id>/rechazar/', rechazar_extension, name='rechazar_extension'),
    path('extensiones/<int:autorizacion_id>/historial/', historial_extensiones, name='historial_extensiones'),
] 