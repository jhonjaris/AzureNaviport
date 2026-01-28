from django.urls import path
from .views import (
    # Dashboard
    dashboard,
    # Gestión de personas
    crear_persona, crear_persona_ajax, editar_persona, eliminar_persona,
    detalle_persona, buscar_personas_ajax, listar_personas_ajax,
    # Gestión de documentos
    subir_documento_personal, editar_documento_personal, eliminar_documento_personal,
    validar_documento_personal, descargar_documento_personal,
)

app_name = 'gestion_personal'

urlpatterns = [
    # Dashboard
    path('dashboard/', dashboard, name='dashboard'),

    # Gestión de personas
    path('personas/crear/', crear_persona, name='crear_persona'),
    path('personas/ajax/crear/', crear_persona_ajax, name='crear_persona_ajax'),
    path('personas/<int:persona_id>/', detalle_persona, name='detalle_persona'),
    path('personas/<int:persona_id>/editar/', editar_persona, name='editar_persona'),
    path('personas/<int:persona_id>/eliminar/', eliminar_persona, name='eliminar_persona'),
    path('personas/buscar/', buscar_personas_ajax, name='buscar_personas_ajax'),
    path('personas/ajax/listar/', listar_personas_ajax, name='listar_personas_ajax'),

    # Gestión de documentos personales
    path('personas/<int:persona_id>/documentos/subir/', subir_documento_personal, name='subir_documento_personal'),
    path('documentos/<int:documento_id>/editar/', editar_documento_personal, name='editar_documento_personal'),
    path('documentos/<int:documento_id>/eliminar/', eliminar_documento_personal, name='eliminar_documento_personal'),
    path('documentos/<int:documento_id>/validar/', validar_documento_personal, name='validar_documento_personal'),
    path('documentos/<int:documento_id>/descargar/', descargar_documento_personal, name='descargar_documento_personal'),
]