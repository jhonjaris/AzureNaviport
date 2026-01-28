from django.urls import path
from .views import (
    # Dashboard
    dashboard,
    # Gestión de vehículos
    crear_vehiculo, crear_vehiculo_ajax, editar_vehiculo, eliminar_vehiculo,
    detalle_vehiculo, buscar_vehiculos_ajax,
    # Inhabilitación y reactivación
    toggle_vehiculo_activo, vehiculos_inhabilitados, reactivar_vehiculo,
    # Gestión de documentos
    subir_documento_vehiculo, editar_documento_vehiculo, eliminar_documento_vehiculo,
    validar_documento_vehiculo, descargar_documento_vehiculo,
)

app_name = 'gestion_vehiculos'

urlpatterns = [
    # Dashboard
    path('dashboard/', dashboard, name='dashboard'),

    # Gestión de vehículos
    path('vehiculos/crear/', crear_vehiculo, name='crear_vehiculo'),
    path('vehiculos/ajax/crear/', crear_vehiculo_ajax, name='crear_vehiculo_ajax'),
    path('vehiculos/<int:vehiculo_id>/', detalle_vehiculo, name='detalle_vehiculo'),
    path('vehiculos/<int:vehiculo_id>/editar/', editar_vehiculo, name='editar_vehiculo'),
    path('vehiculos/<int:vehiculo_id>/eliminar/', eliminar_vehiculo, name='eliminar_vehiculo'),
    path('vehiculos/buscar/', buscar_vehiculos_ajax, name='buscar_vehiculos_ajax'),

    # Inhabilitación y reactivación de vehículos
    path('vehiculos/<int:vehiculo_id>/toggle/', toggle_vehiculo_activo, name='toggle_vehiculo_activo'),
    path('vehiculos/inhabilitados/', vehiculos_inhabilitados, name='vehiculos_inhabilitados'),
    path('vehiculos/<int:vehiculo_id>/reactivar/', reactivar_vehiculo, name='reactivar_vehiculo'),

    # Gestión de documentos de vehículos
    path('vehiculos/<int:vehiculo_id>/documentos/subir/', subir_documento_vehiculo, name='subir_documento_vehiculo'),
    path('documentos/<int:documento_id>/editar/', editar_documento_vehiculo, name='editar_documento_vehiculo'),
    path('documentos/<int:documento_id>/eliminar/', eliminar_documento_vehiculo, name='eliminar_documento_vehiculo'),
    path('documentos/<int:documento_id>/validar/', validar_documento_vehiculo, name='validar_documento_vehiculo'),
    path('documentos/<int:documento_id>/descargar/', descargar_documento_vehiculo, name='descargar_documento_vehiculo'),
]