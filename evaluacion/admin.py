from django.contrib import admin
from .models import ConfiguracionEvaluacion, Servicio, TipoLicencia, DocumentoRequeridoServicio


class DocumentoRequeridoInline(admin.TabularInline):
    """Inline para agregar documentos requeridos desde el formulario de Servicio"""
    model = DocumentoRequeridoServicio
    extra = 1
    max_num = 5
    fields = ['nombre', 'descripcion', 'obligatorio', 'orden', 'activo']
    ordering = ['orden', 'nombre']


@admin.register(ConfiguracionEvaluacion)
class ConfiguracionEvaluacionAdmin(admin.ModelAdmin):
    list_display = ['dias_preaviso_critico', 'dias_preaviso_advertencia', 'dias_preaviso_informativo', 'tipo_expiracion_principal', 'updated_at']
    fields = [
        'dias_preaviso_critico', 'dias_preaviso_advertencia', 'dias_preaviso_informativo',
        'tipo_expiracion_principal', 'enlace_instrucciones', 'notificar_empresas_vencidas'
    ]
    
    def has_add_permission(self, request):
        # Solo permitir una configuración
        return not ConfiguracionEvaluacion.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # No permitir eliminar la configuración
        return False


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'cantidad_documentos_requeridos', 'activo', 'created_at']
    list_filter = ['activo', 'created_at']
    search_fields = ['codigo', 'nombre', 'descripcion']
    ordering = ['codigo', 'nombre']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [DocumentoRequeridoInline]

    def cantidad_documentos_requeridos(self, obj):
        return obj.documentos_requeridos.filter(activo=True).count()
    cantidad_documentos_requeridos.short_description = 'Docs. Requeridos'

    def get_readonly_fields(self, request, obj=None):
        # Si el servicio está en uso, hacer el código de solo lectura
        if obj and not obj.puede_eliminar():
            return self.readonly_fields + ['codigo']
        return self.readonly_fields

    def has_delete_permission(self, request, obj=None):
        # Solo permitir eliminar si no está en uso
        if obj:
            return obj.puede_eliminar()
        return True


@admin.register(DocumentoRequeridoServicio)
class DocumentoRequeridoServicioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'servicio', 'obligatorio', 'orden', 'activo']
    list_filter = ['servicio', 'obligatorio', 'activo']
    search_fields = ['nombre', 'descripcion', 'servicio__nombre']
    ordering = ['servicio', 'orden', 'nombre']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TipoLicencia)
class TipoLicenciaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'cantidad_servicios', 'activo', 'created_at']
    list_filter = ['activo', 'created_at']
    search_fields = ['nombre', 'descripcion']
    filter_horizontal = ['servicios_incluidos']
    ordering = ['nombre']
    readonly_fields = ['created_at', 'updated_at']
    
    def cantidad_servicios(self, obj):
        return obj.servicios_incluidos.count()
    cantidad_servicios.short_description = 'Servicios'
    
    def has_delete_permission(self, request, obj=None):
        # Solo permitir eliminar si no está en uso
        if obj:
            return obj.puede_eliminar()
        return True
