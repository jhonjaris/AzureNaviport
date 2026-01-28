from django.urls import path
from .views import dashboard, detalle_escalamiento, resolver_escalamiento, detalle_discrepancia, gestionar_discrepancia
from .views_excepcionales import (
    lista_empresas_excepcionales,
    aprobar_excepcional,
    revocar_excepcional,
    historial_excepcionales,
    dashboard_excepcionales
)

app_name = 'supervisor'

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
    path('escalamiento/<str:codigo>/', detalle_escalamiento, name='detalle_escalamiento'),
    path('escalamiento/<str:codigo>/resolver/', resolver_escalamiento, name='resolver_escalamiento'),
    path('discrepancia/<str:codigo>/', detalle_discrepancia, name='detalle_discrepancia'),
    path('discrepancia/<str:codigo>/gestionar/', gestionar_discrepancia, name='gestionar_discrepancia'),

    # Solicitudes Excepcionales
    path('excepcionales/', lista_empresas_excepcionales, name='lista_empresas_excepcionales'),
    path('excepcionales/dashboard/', dashboard_excepcionales, name='dashboard_excepcionales'),
    path('excepcionales/<int:empresa_id>/aprobar/', aprobar_excepcional, name='aprobar_excepcional'),
    path('excepcionales/<int:empresa_id>/revocar/', revocar_excepcional, name='revocar_excepcional'),
    path('excepcionales/<int:empresa_id>/historial/', historial_excepcionales, name='historial_excepcionales'),
] 