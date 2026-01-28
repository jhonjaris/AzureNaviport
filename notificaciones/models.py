from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings

# ===========================
# CONFIGURACIÓN DE CORREO
# ===========================

class ConfiguracionEmail(models.Model):
    """Configuración del sistema de email para notificaciones"""

    TIPO_PROVEEDOR_CHOICES = [
        ('gmail', 'Gmail'),
        ('outlook', 'Outlook'),
        ('custom', 'SMTP Personalizado')
    ]

    # Tipo de proveedor
    tipo_proveedor = models.CharField(
        max_length=20,
        choices=TIPO_PROVEEDOR_CHOICES,
        default='custom',
        verbose_name='Tipo de Proveedor',
        help_text='Seleccione su proveedor de correo para autoconfigurar los valores'
    )

    # Nombre identificativo
    nombre = models.CharField(
        max_length=100,
        default='Configuración Principal',
        verbose_name='Nombre de la Configuración',
        help_text='Nombre para identificar esta configuración'
    )

    # Configuración SMTP
    email_backend = models.CharField(
        max_length=100,
        default='django.core.mail.backends.smtp.EmailBackend',
        verbose_name='Backend de Email',
        help_text='Backend de email a utilizar'
    )

    email_host = models.CharField(
        max_length=100,
        default='smtp.gmail.com',
        verbose_name='Servidor SMTP',
        help_text='Dirección del servidor SMTP (ej: smtp.gmail.com)'
    )

    email_port = models.PositiveIntegerField(
        default=587,
        validators=[MinValueValidator(1), MaxValueValidator(65535)],
        verbose_name='Puerto SMTP',
        help_text='Puerto del servidor SMTP (587 para TLS, 465 para SSL, 25 sin cifrado)'
    )

    email_use_tls = models.BooleanField(
        default=True,
        verbose_name='Usar TLS',
        help_text='Usar cifrado TLS (recomendado para puerto 587)'
    )

    email_use_ssl = models.BooleanField(
        default=False,
        verbose_name='Usar SSL',
        help_text='Usar cifrado SSL (para puerto 465)'
    )

    email_host_user = models.EmailField(
        verbose_name='Usuario de Email',
        help_text='Dirección de email para autenticación SMTP'
    )

    email_host_password = models.CharField(
        max_length=200,
        verbose_name='Contraseña de Email',
        help_text='Contraseña o App Password para autenticación SMTP'
    )

    default_from_email = models.EmailField(
        verbose_name='Email Remitente',
        help_text='Dirección de email que aparecerá como remitente'
    )

    # Configuración de recuperación de contraseñas
    password_reset_timeout = models.PositiveIntegerField(
        default=24,
        validators=[MinValueValidator(1), MaxValueValidator(168)],  # Máximo 7 días
        verbose_name='Tiempo de expiración (horas)',
        help_text='Horas de validez para los enlaces de recuperación de contraseña'
    )

    max_reset_attempts = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='Máx. intentos por hora',
        help_text='Máximo número de solicitudes de recuperación por email por hora'
    )

    # Plantillas de email
    reset_email_subject = models.CharField(
        max_length=200,
        default='NaviPort RD - Recuperación de Contraseña',
        verbose_name='Asunto del Email de Recuperación'
    )

    # Estado del sistema
    email_enabled = models.BooleanField(
        default=False,
        verbose_name='Sistema de Email Habilitado',
        help_text='Habilitar el envío de emails (recuperación de contraseñas, notificaciones)'
    )

    test_email_sent = models.BooleanField(
        default=False,
        verbose_name='Email de Prueba Enviado',
        help_text='Indica si se ha enviado exitosamente un email de prueba'
    )

    last_test_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Última Prueba de Email'
    )

    total_emails_sent = models.PositiveIntegerField(
        default=0,
        verbose_name='Total de Emails Enviados',
        help_text='Contador de emails enviados con esta configuración'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado el')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado el')

    class Meta:
        verbose_name = 'Configuración de Email'
        verbose_name_plural = 'Configuraciones de Email'

    def __str__(self):
        return f"{self.nombre} - {self.email_host_user}"

    def clean(self):
        """Validaciones del modelo"""
        super().clean()

        # Validar que no se use TLS y SSL a la vez
        if self.email_use_tls and self.email_use_ssl:
            raise ValidationError('No se puede usar TLS y SSL al mismo tiempo. Escoge uno.')

        # Sugerir puertos según el cifrado
        if self.email_use_ssl and self.email_port != 465:
            raise ValidationError('Para SSL se recomienda usar el puerto 465')
        elif self.email_use_tls and self.email_port != 587:
            raise ValidationError('Para TLS se recomienda usar el puerto 587')

    def save(self, *args, **kwargs):
        """Sobrescribir save para aplicar configuración"""
        super().save(*args, **kwargs)

        # Solo puede haber una configuración activa
        if self.email_enabled:
            ConfiguracionEmail.objects.exclude(pk=self.pk).update(email_enabled=False)

    @property
    def estado_visual(self):
        """Retorna el estado visual para mostrar en la UI"""
        if self.email_enabled:
            return 'activa'
        return 'inactiva'

    @property
    def icono_proveedor(self):
        """Retorna el icono correspondiente al proveedor"""
        iconos = {
            'gmail': '📧',
            'outlook': '📮',
            'custom': '⚙️'
        }
        return iconos.get(self.tipo_proveedor, '📧')

    @property
    def color_estado(self):
        """Retorna el color del estado"""
        if self.email_enabled:
            return 'success'
        return 'secondary'

    def incrementar_contador_emails(self):
        """Incrementa el contador de emails enviados"""
        self.total_emails_sent += 1
        self.save(update_fields=['total_emails_sent'])

    @classmethod
    def get_configuracion_activa(cls):
        """Obtiene la configuración de email activa o la única existente"""
        # Primero buscar una configuración habilitada
        config = cls.objects.filter(email_enabled=True).first()
        if config:
            return config

        # Si no hay habilitada, usar la primera que exista
        config = cls.objects.first()
        if config:
            return config

        # Si no existe ninguna, crear una por defecto
        config = cls.objects.create(
            email_host_user='admin@naviport.rd',
            default_from_email='NaviPort RD <admin@naviport.rd>',
            email_enabled=False
        )
        return config

    def aplicar_configuracion(self):
        """Aplica esta configuración al sistema Django"""
        # Solo aplicar si está habilitada
        if self.email_enabled:
            settings.EMAIL_BACKEND = self.email_backend
            settings.EMAIL_HOST = self.email_host
            settings.EMAIL_PORT = self.email_port
            settings.EMAIL_USE_TLS = self.email_use_tls
            settings.EMAIL_USE_SSL = self.email_use_ssl
            settings.EMAIL_HOST_USER = self.email_host_user
            settings.EMAIL_HOST_PASSWORD = self.email_host_password
            settings.DEFAULT_FROM_EMAIL = self.default_from_email

    def enviar_email_prueba(self, email_destino):
        """Envía un email de prueba para validar configuración"""
        from django.core.mail import send_mail
        from django.utils import timezone

        try:
            # Aplicar configuración
            self.aplicar_configuracion()

            # Enviar email
            send_mail(
                subject='Prueba de Configuración - NaviPort RD',
                message='Este es un email de prueba del sistema NaviPort RD.',
                from_email=self.default_from_email,
                recipient_list=[email_destino],
                fail_silently=False,
            )

            # Actualizar estado
            self.test_email_sent = True
            self.last_test_date = timezone.now()
            self.save(update_fields=['test_email_sent', 'last_test_date'])

            return True, 'Email de prueba enviado exitosamente'
        except Exception as e:
            return False, f'Error al enviar email: {str(e)}'


# ===========================
# EVENTOS DEL SISTEMA
# ===========================

class EventoSistema(models.Model):
    """Eventos del sistema que pueden generar notificaciones"""

    # Códigos de eventos predefinidos
    CODIGO_EVENTO_CHOICES = [
        # Solicitudes
        ('solicitud_recibida', 'Solicitud Recibida'),
        ('solicitud_aprobada', 'Solicitud Aprobada'),
        ('solicitud_rechazada', 'Solicitud Rechazada'),
        ('solicitud_requerimientos', 'Solicitud con Requerimientos'),
        ('solicitud_vencida', 'Solicitud Vencida'),

        # Asignaciones
        ('asignacion_evaluador', 'Asignación a Evaluador'),
        ('asignacion_supervisor', 'Asignación a Supervisor'),

        # Autorizaciones
        ('autorizacion_generada', 'Autorización Generada'),
        ('autorizacion_vencida', 'Autorización Vencida'),
        ('extension_solicitada', 'Extensión de Validez Solicitada'),
        ('extension_aprobada', 'Extensión de Validez Aprobada'),
        ('extension_rechazada', 'Extensión de Validez Rechazada'),

        # Incumplimientos
        ('incumplimiento_reportado', 'Incumplimiento Reportado'),
        ('subsanacion_solicitada', 'Subsanación Solicitada'),
        ('subsanacion_respondida', 'Subsanación Respondida'),

        # Excepcionales
        ('solicitud_excepcional_aprobada', 'Solicitud Excepcional Aprobada'),

        # Sistema
        ('licencia_por_vencer', 'Licencia por Vencer'),
        ('licencia_vencida', 'Licencia Vencida'),
        ('contrato_por_vencer', 'Contrato por Vencer'),
        ('contrato_vencido', 'Contrato Vencido'),

        # Personalizado
        ('personalizado', 'Evento Personalizado'),
    ]

    codigo = models.CharField(
        max_length=50,
        choices=CODIGO_EVENTO_CHOICES,
        unique=True,
        verbose_name='Código del Evento',
        help_text='Código único que identifica este evento'
    )

    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre del Evento',
        help_text='Nombre descriptivo del evento'
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción detallada del evento'
    )

    # Plantilla de email
    asunto_email = models.CharField(
        max_length=200,
        verbose_name='Asunto del Email',
        help_text='Puede usar variables: {solicitud_codigo}, {empresa_nombre}, {usuario_nombre}'
    )

    template_html = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Template HTML',
        help_text='Nombre del archivo template (ej: emails/solicitud_recibida.html)'
    )

    mensaje_texto_plano = models.TextField(
        blank=True,
        verbose_name='Mensaje en Texto Plano',
        help_text='Versión en texto plano del mensaje. Puede usar variables.'
    )

    # Estado
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Si está desactivado, no se enviarán notificaciones para este evento'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado el')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado el')

    class Meta:
        verbose_name = 'Evento del Sistema'
        verbose_name_plural = 'Eventos del Sistema'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

    def get_destinatarios(self):
        """Obtiene todos los destinatarios configurados para este evento"""
        return self.destinatarios.filter(activo=True)


# ===========================
# DESTINATARIOS POR EVENTO
# ===========================

class DestinatarioEvento(models.Model):
    """Define quién recibe notificaciones para cada evento"""

    # Roles del sistema
    ROL_CHOICES = [
        ('evaluador', 'Evaluadores'),
        ('supervisor', 'Supervisores'),
        ('direccion', 'Dirección Logística'),
        ('admin_tic', 'Administradores TIC'),
        ('oficial_acceso', 'Oficiales de Acceso'),
        ('empresa', 'Empresa (solicitante)'),
        ('evaluador_asignado', 'Evaluador Asignado (específico)'),
        ('supervisor_asignado', 'Supervisor Asignado (específico)'),
    ]

    evento = models.ForeignKey(
        EventoSistema,
        on_delete=models.CASCADE,
        related_name='destinatarios',
        verbose_name='Evento'
    )

    # Puede ser por rol O por email específico
    tipo_destinatario = models.CharField(
        max_length=20,
        choices=[('rol', 'Por Rol'), ('email', 'Email Específico')],
        default='rol',
        verbose_name='Tipo de Destinatario'
    )

    rol = models.CharField(
        max_length=30,
        choices=ROL_CHOICES,
        blank=True,
        null=True,
        verbose_name='Rol',
        help_text='Rol que recibirá la notificación'
    )

    email_especifico = models.EmailField(
        blank=True,
        null=True,
        verbose_name='Email Específico',
        help_text='Email individual que recibirá la notificación'
    )

    activo = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado el')

    class Meta:
        verbose_name = 'Destinatario de Evento'
        verbose_name_plural = 'Destinatarios de Eventos'
        ordering = ['evento', 'tipo_destinatario', 'rol']

    def __str__(self):
        if self.tipo_destinatario == 'rol':
            return f"{self.evento.nombre} → {self.get_rol_display()}"
        else:
            return f"{self.evento.nombre} → {self.email_especifico}"

    def clean(self):
        """Validar que tenga rol O email, no ambos"""
        super().clean()

        if self.tipo_destinatario == 'rol' and not self.rol:
            raise ValidationError('Debe seleccionar un rol')

        if self.tipo_destinatario == 'email' and not self.email_especifico:
            raise ValidationError('Debe ingresar un email específico')

        if self.tipo_destinatario == 'rol' and self.email_especifico:
            raise ValidationError('No puede tener rol y email al mismo tiempo')

        if self.tipo_destinatario == 'email' and self.rol:
            raise ValidationError('No puede tener email y rol al mismo tiempo')


# ===========================
# LOG DE NOTIFICACIONES
# ===========================

class LogNotificacion(models.Model):
    """Log auditable de todas las notificaciones enviadas"""

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('enviado', 'Enviado'),
        ('error', 'Error'),
    ]

    evento = models.ForeignKey(
        EventoSistema,
        on_delete=models.PROTECT,
        related_name='logs',
        verbose_name='Evento'
    )

    destinatarios = models.TextField(
        verbose_name='Destinatarios',
        help_text='Lista de emails separados por comas'
    )

    asunto = models.CharField(
        max_length=255,
        verbose_name='Asunto'
    )

    mensaje_html = models.TextField(
        blank=True,
        verbose_name='Mensaje HTML'
    )

    mensaje_texto = models.TextField(
        blank=True,
        verbose_name='Mensaje en Texto'
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name='Estado'
    )

    exitoso = models.BooleanField(
        default=False,
        verbose_name='Envío Exitoso'
    )

    mensaje_error = models.TextField(
        blank=True,
        null=True,
        verbose_name='Mensaje de Error'
    )

    # Metadata adicional en JSON
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Metadata',
        help_text='Información adicional (solicitud_id, empresa_id, etc.)'
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )

    fecha_envio = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Envío'
    )

    class Meta:
        verbose_name = 'Log de Notificación'
        verbose_name_plural = 'Logs de Notificaciones'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.evento.nombre} - {self.get_estado_display()} ({self.fecha_creacion})"

    def marcar_como_enviado(self):
        """Marca el log como enviado exitosamente"""
        self.estado = 'enviado'
        self.exitoso = True
        self.fecha_envio = timezone.now()
        self.save(update_fields=['estado', 'exitoso', 'fecha_envio'])

    def marcar_como_error(self, mensaje_error):
        """Marca el log como error"""
        self.estado = 'error'
        self.exitoso = False
        self.mensaje_error = mensaje_error
        self.fecha_envio = timezone.now()
        self.save(update_fields=['estado', 'exitoso', 'mensaje_error', 'fecha_envio'])
