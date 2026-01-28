from django.contrib import admin
from .models import Incumplimiento, SolicitudSubsanacion, RespuestaSubsanacion, DocumentoSubsanacion


@admin.register(Incumplimiento)
class IncumplimientoAdmin(admin.ModelAdmin):
    list_display = ('id', 'tipo', 'solicitud', 'estado', 'reportado_por', 'puerto', 'fecha_incumplimiento', 'fecha_reporte')
    list_filter = ('estado', 'tipo', 'puerto', 'fecha_reporte')
    search_fields = ('descripcion', 'solicitud__empresa__nombre', 'reportado_por__username')
    readonly_fields = ('fecha_reporte', 'fecha_modificacion')
    date_hierarchy = 'fecha_incumplimiento'

    fieldsets = (
        ('Información del Incumplimiento', {
            'fields': ('tipo', 'descripcion', 'estado', 'evidencia', 'observaciones')
        }),
        ('Relaciones', {
            'fields': ('solicitud', 'autorizacion')
        }),
        ('Ubicación', {
            'fields': ('puerto', 'lugar_puerto')
        }),
        ('Usuarios', {
            'fields': ('reportado_por', 'revisado_por')
        }),
        ('Fechas', {
            'fields': ('fecha_incumplimiento', 'fecha_reporte', 'fecha_revision', 'fecha_modificacion')
        }),
    )


@admin.register(SolicitudSubsanacion)
class SolicitudSubsanacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'incumplimiento', 'estado', 'solicitado_por', 'plazo_dias', 'fecha_limite', 'dias_restantes_display')
    list_filter = ('estado', 'fecha_solicitud')
    search_fields = ('incumplimiento__descripcion', 'informacion_requerida')
    readonly_fields = ('fecha_solicitud', 'fecha_modificacion')
    date_hierarchy = 'fecha_solicitud'

    fieldsets = (
        ('Incumplimiento', {
            'fields': ('incumplimiento',)
        }),
        ('Requerimientos', {
            'fields': ('informacion_requerida', 'plazo_dias', 'fecha_limite', 'estado')
        }),
        ('Usuarios', {
            'fields': ('solicitado_por',)
        }),
        ('Fechas', {
            'fields': ('fecha_solicitud', 'fecha_modificacion')
        }),
    )

    def dias_restantes_display(self, obj):
        dias = obj.dias_restantes()
        if dias == 0 and obj.estado == 'pendiente':
            return '⚠️ Vencido'
        return f"{dias} días"
    dias_restantes_display.short_description = 'Días Restantes'


@admin.register(RespuestaSubsanacion)
class RespuestaSubsanacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'solicitud_subsanacion', 'estado', 'respondido_por', 'revisado_por', 'fecha_respuesta')
    list_filter = ('estado', 'fecha_respuesta')
    search_fields = ('explicacion', 'medidas_preventivas')
    readonly_fields = ('fecha_respuesta', 'fecha_modificacion')
    date_hierarchy = 'fecha_respuesta'

    fieldsets = (
        ('Solicitud', {
            'fields': ('solicitud_subsanacion',)
        }),
        ('Respuesta de la Empresa', {
            'fields': ('explicacion', 'medidas_preventivas', 'estado')
        }),
        ('Revisión', {
            'fields': ('revisado_por', 'comentarios_revision', 'fecha_revision')
        }),
        ('Usuarios y Fechas', {
            'fields': ('respondido_por', 'fecha_respuesta', 'fecha_modificacion')
        }),
    )


class DocumentoSubsanacionInline(admin.TabularInline):
    model = DocumentoSubsanacion
    extra = 1
    fields = ('tipo_documento', 'nombre', 'descripcion', 'archivo', 'fecha_subida')
    readonly_fields = ('fecha_subida',)


@admin.register(DocumentoSubsanacion)
class DocumentoSubsanacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'tipo_documento', 'respuesta', 'fecha_subida')
    list_filter = ('tipo_documento', 'fecha_subida')
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('fecha_subida',)
    date_hierarchy = 'fecha_subida'
