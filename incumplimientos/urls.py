from django.urls import path
from . import views

app_name = 'incumplimientos'

urlpatterns = [
    # Rutas para Oficial de Acceso (reportar incumplimientos)
    path('reportar/', views.reportar_incumplimiento, name='reportar'),
    path('mis-reportes/', views.lista_incumplimientos_oficial, name='mis_reportes'),
    path('detalle/<int:pk>/', views.detalle_incumplimiento, name='detalle'),

    # Rutas para Supervisor (gestionar subsanaciones)
    path('pendientes/', views.lista_incumplimientos_pendientes, name='pendientes'),
    path('<int:pk>/solicitar-subsanacion/', views.solicitar_subsanacion, name='solicitar_subsanacion'),
    path('subsanaciones/', views.lista_subsanaciones, name='lista_subsanaciones'),
    path('subsanacion/<int:pk>/revisar/', views.revisar_respuesta_subsanacion, name='revisar_subsanacion'),

    # Rutas para Empresa (responder subsanaciones)
    path('mis-incumplimientos/', views.lista_incumplimientos_empresa, name='mis_incumplimientos'),
    path('subsanacion/<int:pk>/responder/', views.responder_subsanacion, name='responder_subsanacion'),
]