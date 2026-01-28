from django.contrib import admin
from .models import EmpresaServicio, Personal, PersonalEmpresa, Servicio


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion', 'activo', 'created_at']
    list_filter = ['activo', 'created_at']
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']


@admin.register(EmpresaServicio)
class EmpresaServicioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'rnc', 'numero_licencia', 'fecha_expiracion_licencia', 'licencia_vigente', 'activa', 'created_at']
    list_filter = ['activa', 'created_at', 'fecha_expiracion_licencia']
    search_fields = ['nombre', 'rnc', 'email', 'numero_licencia']
    ordering = ['nombre']
    filter_horizontal = ['servicios_autorizados']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('rnc', 'nombre')
        }),
        ('Contacto', {
            'fields': ('email', 'telefono', 'direccion')
        }),
        ('Licencia', {
            'fields': ('numero_licencia', 'fecha_expiracion_licencia')
        }),
        ('Servicios Autorizados', {
            'fields': ('servicios_autorizados',)
        }),
        ('Estado', {
            'fields': ('activa',)
        }),
    )
    
    def licencia_vigente(self, obj):
        return obj.licencia_vigente()
    licencia_vigente.boolean = True
    licencia_vigente.short_description = 'Licencia Vigente'


@admin.register(Personal)
class PersonalAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'cedula', 'cargo', 'licencia_conducir', 'telefono', 'activo', 'created_at']
    list_filter = ['activo', 'cargo', 'created_at']
    search_fields = ['nombre', 'cedula', 'cargo']
    ordering = ['nombre']
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombre', 'cedula')
        }),
        ('Información Laboral', {
            'fields': ('cargo', 'licencia_conducir')
        }),
        ('Contacto', {
            'fields': ('telefono',)
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )


@admin.register(PersonalEmpresa)
class PersonalEmpresaAdmin(admin.ModelAdmin):
    list_display = ['personal', 'empresa', 'fecha_inicio', 'fecha_fin', 'activo']
    list_filter = ['activo', 'fecha_inicio', 'empresa']
    search_fields = ['personal__nombre', 'personal__cedula', 'empresa__nombre']
    ordering = ['-fecha_inicio']
    
    fieldsets = (
        ('Relación', {
            'fields': ('personal', 'empresa')
        }),
        ('Fechas', {
            'fields': ('fecha_inicio', 'fecha_fin')
        }),
        ('Estado', {
            'fields': ('activo', 'observaciones')
        }),
    )
