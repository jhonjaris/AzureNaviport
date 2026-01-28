from django.contrib import admin
from .models import ConfiguracionEmail, EventoSistema, DestinatarioEvento, LogNotificacion


@admin.register(ConfiguracionEmail)
class ConfiguracionEmailAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'email_host_user', 'tipo_proveedor', 'email_enabled', 'test_email_sent', 'total_emails_sent']
    list_filter = ['email_enabled', 'tipo_proveedor', 'test_email_sent']
    search_fields = ['nombre', 'email_host_user', 'default_from_email']
    readonly_fields = ['created_at', 'updated_at', 'last_test_date', 'total_emails_sent']

    fieldsets = (
        ('Información General', {
            'fields': ('nombre', 'tipo_proveedor')
        }),
        ('Configuración SMTP', {
            'fields': (
                'email_backend',
                'email_host',
                'email_port',
                'email_use_tls',
                'email_use_ssl',
                'email_host_user',
                'email_host_password',
                'default_from_email',
            )
        }),
        ('Recuperación de Contraseñas', {
            'fields': (
                'password_reset_timeout',
                'max_reset_attempts',
                'reset_email_subject',
            ),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': (
                'email_enabled',
                'test_email_sent',
                'last_test_date',
                'total_emails_sent',
            )
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class DestinatarioEventoInline(admin.TabularInline):
    model = DestinatarioEvento
    extra = 1
    fields = ['tipo_destinatario', 'rol', 'email_especifico', 'activo']


@admin.register(EventoSistema)
class EventoSistemaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo', 'activo', 'count_destinatarios', 'updated_at']
    list_filter = ['activo', 'codigo']
    search_fields = ['nombre', 'codigo', 'descripcion']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [DestinatarioEventoInline]

    fieldsets = (
        ('Información del Evento', {
            'fields': ('codigo', 'nombre', 'descripcion', 'activo')
        }),
        ('Plantilla de Email', {
            'fields': (
                'asunto_email',
                'template_html',
                'mensaje_texto_plano',
            )
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def count_destinatarios(self, obj):
        return obj.destinatarios.count()
    count_destinatarios.short_description = 'Destinatarios'


@admin.register(DestinatarioEvento)
class DestinatarioEventoAdmin(admin.ModelAdmin):
    list_display = ['evento', 'tipo_destinatario', 'rol', 'email_especifico', 'activo', 'created_at']
    list_filter = ['activo', 'tipo_destinatario', 'rol', 'evento']
    search_fields = ['evento__nombre', 'email_especifico']
    readonly_fields = ['created_at']

    fieldsets = (
        ('Evento', {
            'fields': ('evento', 'activo')
        }),
        ('Destinatario', {
            'fields': (
                'tipo_destinatario',
                'rol',
                'email_especifico',
            ),
            'description': 'Seleccione si el destinatario será por rol o email específico. Solo uno debe estar lleno.'
        }),
        ('Auditoría', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(LogNotificacion)
class LogNotificacionAdmin(admin.ModelAdmin):
    list_display = ['evento', 'asunto', 'estado', 'exitoso', 'fecha_creacion', 'fecha_envio']
    list_filter = ['estado', 'exitoso', 'evento', 'fecha_creacion']
    search_fields = ['asunto', 'destinatarios', 'mensaje_error']
    readonly_fields = ['evento', 'destinatarios', 'asunto', 'mensaje_html', 'mensaje_texto',
                       'estado', 'exitoso', 'mensaje_error', 'metadata', 'fecha_creacion', 'fecha_envio']

    fieldsets = (
        ('Información del Envío', {
            'fields': ('evento', 'estado', 'exitoso', 'destinatarios', 'asunto')
        }),
        ('Contenido del Mensaje', {
            'fields': ('mensaje_html', 'mensaje_texto'),
            'classes': ('collapse',)
        }),
        ('Resultado', {
            'fields': ('mensaje_error', 'metadata')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_envio')
        }),
    )

    def has_add_permission(self, request):
        # No permitir crear logs manualmente
        return False

    def has_change_permission(self, request, obj=None):
        # No permitir editar logs (solo lectura)
        return False
