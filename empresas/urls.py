from django.urls import path
from . import views

app_name = 'empresas'

urlpatterns = [
    # API endpoints para búsqueda de personal
    path('api/buscar-personal/', views.buscar_personal, name='buscar_personal'),
    path('api/crear-personal/', views.crear_personal, name='crear_personal'),
    path('api/personal/<int:personal_id>/', views.detalle_personal, name='detalle_personal'),
    
    # CRUD de Empresas de Servicio
    path('', views.listar_empresas, name='listar_empresas'),
    path('registrar/', views.registrar_empresa, name='registrar_empresa'),
    path('<int:empresa_id>/', views.detalle_empresa, name='detalle_empresa'),
    path('<int:empresa_id>/editar/', views.editar_empresa, name='editar_empresa'),
    
    # CRUD de Servicios
    path('servicios/', views.listar_servicios, name='listar_servicios'),
    path('servicios/crear/', views.crear_servicio, name='crear_servicio'),
    path('servicios/<int:servicio_id>/editar/', views.editar_servicio, name='editar_servicio'),
]