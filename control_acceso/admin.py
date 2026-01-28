from django.contrib import admin
from .models import Autorizacion, RegistroAcceso, Discrepancia, SolicitudExtension

@admin.register(Autorizacion)
class AutorizacionAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'empresa_nombre', 'representante_nombre', 'puerto_nombre', 'estado', 'valida_desde', 'valida_hasta']
    list_filter = ['estado', 'puerto_nombre', 'valida_desde', 'valida_hasta']
    search_fields = ['codigo', 'empresa_nombre', 'empresa_rnc', 'representante_nombre', 'representante_cedula']
    ordering = ['-creada_el']
    date_hierarchy = 'valida_desde'
    
    fieldsets = (
        ('Información de la Autorización', {
            'fields': ('codigo', 'solicitud', 'estado')
        }),
        ('Empresa', {
            'fields': ('empresa_nombre', 'empresa_rnc')
        }),
        ('Representante', {
            'fields': ('representante_nombre', 'representante_cedula')
        }),
        ('Acceso', {
            'fields': ('valida_desde', 'valida_hasta', 'puerto_nombre', 'motivo_acceso')
        }),
        ('Metadatos', {
            'fields': ('generada_por', 'creada_el', 'actualizada_el', 'qr_code'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['codigo', 'qr_code', 'creada_el', 'actualizada_el']

@admin.register(RegistroAcceso)
class RegistroAccesoAdmin(admin.ModelAdmin):
    list_display = ['autorizacion', 'tipo_acceso']
    list_filter = ['tipo_acceso']
    search_fields = ['autorizacion__codigo']
    ordering = ['-id']

@admin.register(Discrepancia)
class DiscrepanciaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'tipo_discrepancia', 'estado']
    list_filter = ['tipo_discrepancia', 'estado']
    search_fields = ['codigo', 'descripcion']
    ordering = ['-id']


@admin.register(SolicitudExtension)
class SolicitudExtensionAdmin(admin.ModelAdmin):
    list_display = [
        'codigo',
        'autorizacion',
        'solicitada_por',
        'dias_extension_display',
        'estado',
        'procesada_por',
        'creada_el'
    ]
    list_filter = ['estado', 'creada_el', 'fecha_procesamiento']
    search_fields = [
        'codigo',
        'autorizacion__codigo',
        'autorizacion__empresa_nombre',
        'solicitada_por__username',
        'motivo'
    ]
    ordering = ['-creada_el']
    date_hierarchy = 'creada_el'

    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'autorizacion', 'estado')
        }),
        ('Solicitud de Extensión', {
            'fields': (
                'fecha_vencimiento_actual',
                'fecha_vencimiento_solicitada',
                'motivo',
                'solicitada_por'
            )
        }),
        ('Procesamiento', {
            'fields': (
                'procesada_por',
                'fecha_procesamiento',
                'observaciones_respuesta',
                'motivo_rechazo'
            )
        }),
        ('Metadatos', {
            'fields': ('creada_el', 'actualizada_el'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['codigo', 'creada_el', 'actualizada_el']

    def dias_extension_display(self, obj):
        """Muestra los días de extensión solicitados"""
        dias = obj.dias_extension_solicitados
        if dias > 0:
            return f"+{dias} días"
        return f"{dias} días"
    dias_extension_display.short_description = 'Extensión Solicitada'

    def get_queryset(self, request):
        """Optimiza el queryset con select_related"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'autorizacion',
            'solicitada_por',
            'procesada_por'
        )
