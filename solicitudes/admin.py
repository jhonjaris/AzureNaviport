from django.contrib import admin
from .models import Solicitud, Vehiculo, DocumentoAdjunto, Puerto, MotivoAcceso, SolicitudPersonal, DocumentoServicioSolicitud, EventoSolicitud

@admin.register(Puerto)
class PuertoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre']
    ordering = ['nombre']

@admin.register(MotivoAcceso)
class MotivoAccesoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre']
    ordering = ['nombre']

class VehiculoInline(admin.TabularInline):
    model = Vehiculo
    extra = 1

class DocumentoAdjuntoInline(admin.TabularInline):
    model = DocumentoAdjunto
    extra = 1
    readonly_fields = ['nombre_original', 'tamaño']


class DocumentoServicioInline(admin.TabularInline):
    model = DocumentoServicioSolicitud
    extra = 0
    readonly_fields = ['nombre_original', 'tamaño', 'subido_el']
    fields = ['documento_requerido', 'archivo', 'nombre_original', 'verificado', 'subido_el']


@admin.register(DocumentoServicioSolicitud)
class DocumentoServicioSolicitudAdmin(admin.ModelAdmin):
    list_display = ['solicitud', 'documento_requerido', 'verificado', 'subido_el']
    list_filter = ['verificado', 'documento_requerido__servicio', 'subido_el']
    search_fields = ['solicitud__codigo', 'documento_requerido__nombre']
    readonly_fields = ['nombre_original', 'tamaño', 'subido_el', 'actualizado_el']


@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = ['id', 'solicitante', 'empresa', 'puerto_destino', 'servicios_count', 'estado', 'fecha_ingreso', 'creada_el']
    list_filter = ['estado', 'puerto_destino', 'motivo_acceso', 'prioridad', 'creada_el']
    search_fields = ['solicitante__username', 'empresa__nombre', 'empresa__rnc', 'descripcion']
    ordering = ['-creada_el']
    date_hierarchy = 'creada_el'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('solicitante', 'empresa', 'puerto_destino', 'motivo_acceso', 'estado')
        }),
        ('Fechas y Horarios', {
            'fields': ('fecha_ingreso', 'hora_ingreso', 'fecha_salida', 'hora_salida', 'vence_el')
        }),
        ('Descripción y Servicios', {
            'fields': ('descripcion', 'servicios_solicitados')
        }),
        ('Evaluación', {
            'fields': ('evaluador_asignado', 'fecha_evaluacion', 'comentarios_evaluacion', 'motivo_rechazo', 'prioridad')
        }),
        ('Metadatos', {
            'fields': ('creada_el', 'actualizada_el'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['creada_el', 'actualizada_el']
    inlines = [VehiculoInline, DocumentoAdjuntoInline]
    
    def servicios_count(self, obj):
        count = obj.servicios_solicitados.count()
        if count == 0:
            return "Sin servicios"
        return f"{count} servicio{'s' if count != 1 else ''}"
    servicios_count.short_description = "Servicios"

@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ['placa', 'tipo_vehiculo', 'conductor_nombre', 'solicitud']
    list_filter = ['tipo_vehiculo']
    search_fields = ['placa', 'conductor_nombre', 'conductor_licencia']
    ordering = ['placa']

@admin.register(DocumentoAdjunto)
class DocumentoAdjuntoAdmin(admin.ModelAdmin):
    list_display = ['nombre_original', 'tipo_documento', 'solicitud', 'tamaño_mb']
    list_filter = ['tipo_documento']
    search_fields = ['nombre_original', 'solicitud__id']
    ordering = ['-id']
    
    def tamaño_mb(self, obj):
        if obj.tamaño:
            return f"{obj.tamaño / (1024*1024):.2f} MB"
        return "N/A"
    tamaño_mb.short_description = "Tamaño"


@admin.register(SolicitudPersonal)
class SolicitudPersonalAdmin(admin.ModelAdmin):
    list_display = ['personal', 'solicitud', 'rol_operacion', 'created_at']
    list_filter = ['rol_operacion', 'created_at']
    search_fields = ['personal__nombre', 'personal__cedula', 'solicitud__codigo']
    ordering = ['-created_at']

    fieldsets = (
        ('Información Básica', {
            'fields': ('solicitud', 'personal')
        }),
        ('Detalles de la Operación', {
            'fields': ('rol_operacion', 'observaciones')
        }),
    )


@admin.register(EventoSolicitud)
class EventoSolicitudAdmin(admin.ModelAdmin):
    list_display = ['icono_tipo', 'solicitud', 'tipo_evento', 'titulo', 'usuario_display', 'creado_el', 'visibilidad_display']
    list_filter = ['tipo_evento', 'es_visible_solicitante', 'es_interno', 'creado_el']
    search_fields = ['solicitud__codigo', 'titulo', 'descripcion', 'usuario__username', 'usuario__first_name', 'usuario__last_name']
    ordering = ['-creado_el']
    date_hierarchy = 'creado_el'
    readonly_fields = ['creado_el']

    fieldsets = (
        ('Evento', {
            'fields': ('solicitud', 'tipo_evento', 'titulo', 'descripcion')
        }),
        ('Responsable', {
            'fields': ('usuario',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Visibilidad', {
            'fields': ('es_visible_solicitante', 'es_interno')
        }),
        ('Timestamps', {
            'fields': ('creado_el',),
            'classes': ('collapse',)
        }),
    )

    def icono_tipo(self, obj):
        return f"{obj.get_icono()} {obj.get_tipo_evento_display()}"
    icono_tipo.short_description = "Tipo"

    def usuario_display(self, obj):
        return obj.get_usuario_nombre()
    usuario_display.short_description = "Usuario"

    def visibilidad_display(self, obj):
        if obj.es_interno:
            return "🔒 Interno"
        elif obj.es_visible_solicitante:
            return "👁️ Público"
        else:
            return "👁️‍🗨️ Staff"
    visibilidad_display.short_description = "Visibilidad"
