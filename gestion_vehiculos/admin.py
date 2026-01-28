from django.contrib import admin
from .models import Vehiculo, DocumentoVehiculo


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = [
        'placa', 'marca', 'modelo', 'ano', 'color', 'tipo_vehiculo',
        'empresa_propietaria_nombre', 'activo_display', 'fecha_registro'
    ]
    list_filter = ['activo', 'tipo_vehiculo', 'marca', 'fecha_registro']
    search_fields = ['placa', 'marca', 'modelo', 'color', 'numero_chasis', 'numero_motor']
    ordering = ['-fecha_registro']
    readonly_fields = [
        'fecha_registro', 'fecha_actualizacion',
        'fecha_inhabilitacion', 'inhabilitado_por'
    ]

    fieldsets = (
        ('Información del Vehículo', {
            'fields': ('placa', 'marca', 'modelo', 'ano', 'color', 'tipo_vehiculo')
        }),
        ('Información Técnica', {
            'fields': ('numero_chasis', 'numero_motor'),
            'classes': ('collapse',)
        }),
        ('Notas', {
            'fields': ('notas_adicionales',),
            'classes': ('collapse',)
        }),
        ('Propietario', {
            'fields': ('empresa_propietaria',)
        }),
        ('Estado', {
            'fields': ('activo', 'motivo_inhabilitacion', 'fecha_inhabilitacion', 'inhabilitado_por')
        }),
        ('Auditoría', {
            'fields': ('fecha_registro', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    def empresa_propietaria_nombre(self, obj):
        if obj.empresa_propietaria and obj.empresa_propietaria.empresa:
            return obj.empresa_propietaria.empresa.nombre
        return '-'
    empresa_propietaria_nombre.short_description = 'Empresa'

    def activo_display(self, obj):
        if obj.activo:
            return '✅ Activo'
        return '❌ Inhabilitado'
    activo_display.short_description = 'Estado'


@admin.register(DocumentoVehiculo)
class DocumentoVehiculoAdmin(admin.ModelAdmin):
    list_display = [
        'vehiculo', 'tipo_documento', 'estado_validacion_display',
        'fecha_vencimiento', 'fecha_subida', 'subido_por'
    ]
    list_filter = ['tipo_documento', 'estado_validacion', 'fecha_subida']
    search_fields = ['vehiculo__placa', 'numero_documento']
    ordering = ['-fecha_subida']
    readonly_fields = ['fecha_subida', 'fecha_validacion']

    fieldsets = (
        ('Documento', {
            'fields': ('vehiculo', 'tipo_documento', 'numero_documento', 'archivo', 'fecha_vencimiento')
        }),
        ('Validación', {
            'fields': ('estado_validacion', 'validado_por', 'fecha_validacion', 'comentarios_validacion')
        }),
        ('Auditoría', {
            'fields': ('subido_por', 'fecha_subida'),
            'classes': ('collapse',)
        }),
    )

    def estado_validacion_display(self, obj):
        estados = {
            'pendiente': '⏳ Pendiente',
            'validado': '✅ Validado',
            'rechazado': '❌ Rechazado',
            'vencido': '⚠️ Vencido',
        }
        return estados.get(obj.estado_validacion, obj.estado_validacion)
    estado_validacion_display.short_description = 'Estado'
