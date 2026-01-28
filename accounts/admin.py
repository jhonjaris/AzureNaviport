from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import Empresa, NotificacionEmpresa, AprobacionExcepcional

User = get_user_model()

# Desregistrar el admin de User por defecto si existe
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'empresa', 'cedula_rnc', 'activo']
    list_filter = ['role', 'activo', 'is_staff', 'is_superuser', 'empresa']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'cedula_rnc']
    ordering = ['role', 'username']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Información Adicional', {
            'fields': ('role', 'cedula_rnc', 'telefono', 'empresa', 'activo')
        }),
        ('Seguridad', {
            'fields': ('failed_login_attempts', 'is_locked', 'locked_until', 'last_login_ip')
        }),
    )
    
    readonly_fields = ['last_login_ip', 'created_at', 'updated_at']

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'rnc', 'email', 'telefono', 'representante_legal', 'activa']
    list_filter = ['activa']
    search_fields = ['nombre', 'rnc', 'email']
    ordering = ['nombre']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'rnc', 'representante_legal')
        }),
        ('Contacto', {
            'fields': ('email', 'telefono', 'direccion')
        }),
        ('Estado', {
            'fields': ('activa',)
        }),
    )

# Registrar el modelo User con el admin personalizado
admin.site.register(User, CustomUserAdmin)

@admin.register(NotificacionEmpresa)
class NotificacionEmpresaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'empresa', 'usuario', 'tipo', 'categoria', 'activa', 'cerrada_por_usuario', 'created_at']
    list_filter = ['tipo', 'categoria', 'activa', 'cerrada_por_usuario', 'created_at']
    search_fields = ['titulo', 'mensaje', 'empresa__nombre', 'usuario__first_name', 'usuario__last_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Información Básica', {
            'fields': ('empresa', 'usuario', 'tipo', 'categoria')
        }),
        ('Contenido', {
            'fields': ('titulo', 'mensaje', 'enlace_accion', 'texto_enlace')
        }),
        ('Fechas', {
            'fields': ('fecha_expiracion', 'mostrar_desde', 'mostrar_hasta')
        }),
        ('Estado', {
            'fields': ('activa', 'cerrada_por_usuario', 'fecha_cerrada')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AprobacionExcepcional)
class AprobacionExcepcionalAdmin(admin.ModelAdmin):
    list_display = ['empresa', 'estado', 'aprobada_por', 'fecha_aprobacion', 'fecha_vencimiento', 'esta_activa_display']
    list_filter = ['estado', 'fecha_aprobacion', 'aprobada_por']
    search_fields = ['empresa__nombre', 'empresa__rnc', 'motivo', 'aprobada_por__username']
    readonly_fields = ['fecha_aprobacion', 'created_at', 'updated_at', 'esta_activa_display']
    ordering = ['-fecha_aprobacion']

    fieldsets = (
        ('Información Básica', {
            'fields': ('empresa', 'motivo', 'observaciones')
        }),
        ('Aprobación', {
            'fields': ('aprobada_por', 'fecha_aprobacion', 'estado')
        }),
        ('Vigencia', {
            'fields': ('fecha_inicio', 'fecha_vencimiento')
        }),
        ('Revocación', {
            'fields': ('revocada_por', 'fecha_revocacion', 'motivo_revocacion'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('esta_activa_display', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def esta_activa_display(self, obj):
        """Muestra si la aprobación está activa"""
        return "✅ Sí" if obj.esta_activa else "❌ No"
    esta_activa_display.short_description = 'Está Activa'
