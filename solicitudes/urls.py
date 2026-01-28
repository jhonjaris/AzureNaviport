from django.urls import path
from .views import (
    dashboard, nueva_solicitud, detalle_solicitud, editar_solicitud, borrar_solicitud,
    mis_borradores, mis_solicitudes, mis_autorizaciones, estadisticas,
    imprimir_autorizacion,
    # Wizard views
    solicitud_wizard_inicio, solicitud_wizard_paso1, solicitud_wizard_paso2,
    solicitud_wizard_paso3, solicitud_wizard_paso4, solicitud_wizard_paso5,
    solicitud_wizard_finalizar, wizard_cargar_lugares_puerto,
    wizard_cargar_lugar_detalle, wizard_cargar_documentos_servicio,
    solicitud_wizard_volver_paso, solicitud_wizard_editar, listar_vehiculos_ajax
)

app_name = 'solicitudes'

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
    path('nueva/', nueva_solicitud, name='nueva_solicitud'),
    path('detalle/<int:solicitud_id>/', detalle_solicitud, name='detalle_solicitud'),
    path('editar/<int:solicitud_id>/', editar_solicitud, name='editar_solicitud'),
    path('borrar/<int:solicitud_id>/', borrar_solicitud, name='borrar_solicitud'),
    path('borradores/', mis_borradores, name='mis_borradores'),
    path('mis-solicitudes/', mis_solicitudes, name='mis_solicitudes'),
    path('mis-autorizaciones/', mis_autorizaciones, name='mis_autorizaciones'),
    path('estadisticas/', estadisticas, name='estadisticas'),
    path('imprimir/<int:solicitud_id>/', imprimir_autorizacion, name='imprimir_autorizacion'),
    
    # Wizard URLs
    path('wizard/', solicitud_wizard_inicio, name='solicitud_wizard_inicio'),
    path('wizard/paso1/', solicitud_wizard_paso1, name='wizard_paso1'),
    path('wizard/paso2/', solicitud_wizard_paso2, name='wizard_paso2'),
    path('wizard/paso3/', solicitud_wizard_paso3, name='wizard_paso3'),
    path('wizard/paso4/', solicitud_wizard_paso4, name='wizard_paso4'),
    path('wizard/paso5/', solicitud_wizard_paso5, name='wizard_paso5'),
    path('wizard/finalizar/', solicitud_wizard_finalizar, name='wizard_finalizar'),
    path('wizard/api/lugares-puerto/', wizard_cargar_lugares_puerto, name='wizard_cargar_lugares_puerto'),
    path('wizard/api/lugar-detalle/<int:lugar_id>/', wizard_cargar_lugar_detalle, name='wizard_cargar_lugar_detalle'),
    path('wizard/api/documentos-servicio/<int:servicio_id>/', wizard_cargar_documentos_servicio, name='wizard_cargar_documentos_servicio'),
    path('wizard/volver-paso/<int:paso>/', solicitud_wizard_volver_paso, name='wizard_volver_paso'),
    path('wizard/editar/<int:solicitud_id>/', solicitud_wizard_editar, name='wizard_editar'),
    path('wizard/api/listar-vehiculos/', listar_vehiculos_ajax, name='listar_vehiculos_ajax'),
] 