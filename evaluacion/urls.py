from django.urls import path
from .views import (
    dashboard, evaluar_solicitud, gestionar_empresas, crear_empresa,
    editar_empresa, renovar_licencia, eliminar_empresa, buscar_empresas_ajax,
    configuracion, configuracion_email, crear_configuracion_email, editar_configuracion_email,
    activar_configuracion_email, eliminar_configuracion_email, enviar_email_prueba,
    obtener_servicios_tipo_licencia, gestion_licencias_servicios,
    asignar_evaluador, mis_solicitudes, nuevas_solicitudes,
    # Servicios
    gestionar_servicios, crear_servicio, editar_servicio, eliminar_servicio,
    # Tipos de Licencia
    gestionar_tipos_licencia, crear_tipo_licencia, editar_tipo_licencia,
    eliminar_tipo_licencia, ver_tipo_licencia,
    # Dashboard y Reportes (Fase 2.3)
    dashboard_rendimiento, distribucion_evaluadores, historial_evaluaciones_empresa,
    exportar_empresas_csv, exportar_empresas_xlsx, exportar_empresas_pdf
)
from .views_puertos import (
    gestion_puertos, crear_puerto, editar_puerto, eliminar_puerto,
    detalle_puerto, crear_lugar, editar_lugar, eliminar_lugar, get_lugares_puerto
)

app_name = 'evaluacion'

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
    path('mis-solicitudes/', mis_solicitudes, name='mis_solicitudes'),
    path('nuevas-solicitudes/', nuevas_solicitudes, name='nuevas_solicitudes'),
    path('evaluar/<int:solicitud_id>/', evaluar_solicitud, name='evaluar_solicitud'),
    path('asignar/<int:solicitud_id>/', asignar_evaluador, name='asignar_evaluador'),
    
    # Gestión de empresas
    path('empresas/', gestionar_empresas, name='gestionar_empresas'),
    path('empresas/crear/', crear_empresa, name='crear_empresa'),
    path('empresas/<int:empresa_id>/editar/', editar_empresa, name='editar_empresa'),
    path('empresas/<int:empresa_id>/renovar/', renovar_licencia, name='renovar_licencia'),
    path('empresas/<int:empresa_id>/eliminar/', eliminar_empresa, name='eliminar_empresa'),
    path('empresas/buscar/', buscar_empresas_ajax, name='buscar_empresas_ajax'),
    path('empresas/<int:empresa_id>/historial-evaluaciones/', historial_evaluaciones_empresa, name='historial_evaluaciones_empresa'),
    path('tipos-licencia/<int:tipo_licencia_id>/servicios/', obtener_servicios_tipo_licencia, name='obtener_servicios_tipo_licencia'),

    # Dashboard y Reportes (Fase 2.3)
    path('dashboard/rendimiento/', dashboard_rendimiento, name='dashboard_rendimiento'),
    path('dashboard/distribucion-evaluadores/', distribucion_evaluadores, name='distribucion_evaluadores'),
    path('empresas/exportar/csv/', exportar_empresas_csv, name='exportar_empresas_csv'),
    path('empresas/exportar/xlsx/', exportar_empresas_xlsx, name='exportar_empresas_xlsx'),
    path('empresas/exportar/pdf/', exportar_empresas_pdf, name='exportar_empresas_pdf'),

    # Configuración
    path('configuracion/', configuracion, name='configuracion'),
    path('configuracion/email/', configuracion_email, name='configuracion_email'),
    path('configuracion/email/crear/', crear_configuracion_email, name='crear_configuracion_email'),
    path('configuracion/email/<int:pk>/editar/', editar_configuracion_email, name='editar_configuracion_email'),
    path('configuracion/email/<int:pk>/activar/', activar_configuracion_email, name='activar_configuracion_email'),
    path('configuracion/email/<int:pk>/eliminar/', eliminar_configuracion_email, name='eliminar_configuracion_email'),
    path('configuracion/email/probar/', enviar_email_prueba, name='enviar_email_prueba'),
    
    # Gestión de Licencias y Servicios
    path('licencias-servicios/', gestion_licencias_servicios, name='gestion_licencias_servicios'),
    
    # Gestión de Servicios
    path('servicios/', gestionar_servicios, name='gestionar_servicios'),
    path('servicios/crear/', crear_servicio, name='crear_servicio'),
    path('servicios/<int:servicio_id>/editar/', editar_servicio, name='editar_servicio'),
    path('servicios/<int:servicio_id>/eliminar/', eliminar_servicio, name='eliminar_servicio'),
    
    # Gestión de Tipos de Licencia
    path('tipos-licencia/', gestionar_tipos_licencia, name='gestionar_tipos_licencia'),
    path('tipos-licencia/crear/', crear_tipo_licencia, name='crear_tipo_licencia'),
    path('tipos-licencia/<int:tipo_licencia_id>/', ver_tipo_licencia, name='ver_tipo_licencia'),
    path('tipos-licencia/<int:tipo_licencia_id>/editar/', editar_tipo_licencia, name='editar_tipo_licencia'),
    path('tipos-licencia/<int:tipo_licencia_id>/eliminar/', eliminar_tipo_licencia, name='eliminar_tipo_licencia'),

    # Gestión de Puertos y Lugares
    path('puertos/', gestion_puertos, name='gestion_puertos'),
    path('puertos/crear/', crear_puerto, name='crear_puerto'),
    path('puertos/<int:puerto_id>/editar/', editar_puerto, name='editar_puerto'),
    path('puertos/<int:puerto_id>/eliminar/', eliminar_puerto, name='eliminar_puerto'),
    path('puertos/<int:puerto_id>/', detalle_puerto, name='detalle_puerto'),
    path('puertos/<int:puerto_id>/lugares/crear/', crear_lugar, name='crear_lugar'),
    path('lugares/<int:lugar_id>/editar/', editar_lugar, name='editar_lugar'),
    path('lugares/<int:lugar_id>/eliminar/', eliminar_lugar, name='eliminar_lugar'),

    # API endpoints para puertos
    path('api/puertos/<int:puerto_id>/lugares/', get_lugares_puerto, name='get_lugares_puerto'),
] 