from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

class ConfiguracionEvaluacion(models.Model):
    """Configuración global para las reglas de validación de empresas"""
    
    # Tipos de expiración a considerar
    TIPO_EXPIRACION_CHOICES = [
        ('vuce', 'Fecha de Expiración VUCE'),
        ('contrato', 'Expiración Contrato'),
        ('ambas', 'Ambas fechas (la más próxima)')
    ]
    
    # Configuración de preaviso
    dias_preaviso_critico = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(365)],
        verbose_name='Días de preaviso crítico',
        help_text='Días antes de expiración para considerar crítico (ej: 30 días)'
    )
    
    dias_preaviso_advertencia = models.PositiveIntegerField(
        default=60,
        validators=[MinValueValidator(1), MaxValueValidator(365)],
        verbose_name='Días de preaviso de advertencia',
        help_text='Días antes de expiración para mostrar advertencia (ej: 60 días)'
    )
    
    dias_preaviso_informativo = models.PositiveIntegerField(
        default=90,
        validators=[MinValueValidator(1), MaxValueValidator(365)],
        verbose_name='Días de preaviso informativo',
        help_text='Días antes de expiración para mostrar información (ej: 90 días)'
    )
    
    # Tipo de expiración a considerar
    tipo_expiracion_principal = models.CharField(
        max_length=10,
        choices=TIPO_EXPIRACION_CHOICES,
        default='vuce',
        verbose_name='Expiración principal a considerar'
    )
    
    # Configuración adicional
    notificar_empresas_vencidas = models.BooleanField(
        default=True,
        verbose_name='Notificar empresas con licencias vencidas'
    )

    # Enlace de instrucciones para renovación
    enlace_instrucciones = models.URLField(
        blank=True,
        null=True,
        verbose_name='Enlace de instrucciones para renovación',
        help_text='URL que aparecerá en los avisos de expiración (ej: https://vuce.gob.do/renovacion)'
    )
    
    # Tiempo de respuesta para evaluaciones
    tiempo_respuesta_horas = models.PositiveIntegerField(
        default=24,
        validators=[MinValueValidator(1), MaxValueValidator(168)],
        verbose_name='Tiempo de respuesta (horas)',
        help_text='Tiempo límite para responder solicitudes en horas (máximo 7 días)'
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado el')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado el')
    
    class Meta:
        verbose_name = 'Configuración de Evaluación'
        verbose_name_plural = 'Configuraciones de Evaluación'
    
    def __str__(self):
        return f'Configuración - Crítico: {self.dias_preaviso_critico}d, Principal: {self.get_tipo_expiracion_principal_display()}'
    
    @classmethod
    def get_configuracion(cls):
        """Obtiene la configuración actual o crea una por defecto"""
        config, created = cls.objects.get_or_create(pk=1)
        return config
    
    def clean(self):
        """Validación personalizada"""
        from django.core.exceptions import ValidationError
        
        # Validar que los días estén en orden lógico
        if self.dias_preaviso_critico >= self.dias_preaviso_advertencia:
            raise ValidationError('Los días de preaviso crítico deben ser menores que los de advertencia')
        
        if self.dias_preaviso_advertencia >= self.dias_preaviso_informativo:
            raise ValidationError('Los días de preaviso de advertencia deben ser menores que los informativos')


class Servicio(models.Model):
    """Servicios que pueden ofrecer las empresas portuarias"""
    
    nombre = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name='Nombre del Servicio',
        help_text='Ej: Carga General, Contenedores, Combustibles, etc.'
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción detallada del servicio'
    )
    codigo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Código',
        help_text='Código único del servicio (ej: CG-001)'
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Si está desactivado, no aparecerá en nuevas asignaciones'
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado el')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado el')
    
    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    def puede_eliminar(self):
        """Verifica si el servicio puede ser eliminado"""
        return not self.empresas_autorizadas.exists() and not self.tipos_licencia.exists()
    
    def empresas_que_lo_usan(self):
        """Retorna las empresas que tienen este servicio autorizado"""
        return self.empresas_autorizadas.all()
    
    def tipos_licencia_que_lo_incluyen(self):
        """Retorna los tipos de licencia que incluyen este servicio"""
        return self.tipos_licencia.all()


class DocumentoRequeridoServicio(models.Model):
    """Documentos requeridos para realizar un servicio específico"""

    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.CASCADE,
        related_name='documentos_requeridos',
        verbose_name='Servicio'
    )
    nombre = models.CharField(
        max_length=150,
        verbose_name='Nombre del Documento',
        help_text='Ej: Certificado de Fumigación, Factura Comercial, etc.'
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción/Instrucciones',
        help_text='Instrucciones adicionales sobre el documento requerido'
    )
    obligatorio = models.BooleanField(
        default=True,
        verbose_name='Obligatorio',
        help_text='Si está marcado, el solicitante debe adjuntar este documento'
    )
    orden = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de aparición en el formulario'
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )

    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado el')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado el')

    class Meta:
        verbose_name = 'Documento Requerido'
        verbose_name_plural = 'Documentos Requeridos'
        ordering = ['servicio', 'orden', 'nombre']
        # Máximo 5 documentos por servicio se valida en clean()

    def __str__(self):
        obligatorio_txt = "✓" if self.obligatorio else "○"
        return f"{obligatorio_txt} {self.nombre} ({self.servicio.nombre})"

    def clean(self):
        """Validación: máximo 5 documentos por servicio"""
        if self.pk is None:  # Solo para nuevos registros
            count = DocumentoRequeridoServicio.objects.filter(
                servicio=self.servicio,
                activo=True
            ).count()
            if count >= 5:
                raise ValidationError(
                    f'El servicio "{self.servicio.nombre}" ya tiene 5 documentos requeridos. '
                    'Elimine o desactive uno antes de agregar otro.'
                )


class TipoLicencia(models.Model):
    """Tipos de licencia con servicios predefinidos"""
    
    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nombre del Tipo de Licencia',
        help_text='Ej: Licencia Portuaria General, Licencia de Combustibles, etc.'
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción del tipo de licencia y sus alcances'
    )
    servicios_incluidos = models.ManyToManyField(
        Servicio,
        related_name='tipos_licencia',
        blank=True,
        verbose_name='Servicios Incluidos',
        help_text='Servicios que se autorizan automáticamente con este tipo de licencia'
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Si está desactivado, no aparecerá en nuevas asignaciones'
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado el')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado el')
    
    class Meta:
        verbose_name = 'Tipo de Licencia'
        verbose_name_plural = 'Tipos de Licencia'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre
    
    def cantidad_servicios(self):
        """Retorna la cantidad de servicios incluidos"""
        return self.servicios_incluidos.count()
    
    def puede_eliminar(self):
        """Verifica si el tipo de licencia puede ser eliminado"""
        return not self.empresas_asignadas.exists()
    
    def empresas_que_lo_usan(self):
        """Retorna las empresas que tienen este tipo de licencia"""
        return self.empresas_asignadas.all()


class ConfiguracionEmail(models.Model):
    """Configuración del sistema de email para notificaciones y recuperación de contraseñas"""
    
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

    # Correos para notificaciones de nuevas solicitudes
    correos_notificaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name='Correos de Notificación',
        help_text='Lista de correos separados por comas que recibirán notificaciones de nuevas solicitudes (ej: admin@mail.com, supervisor@mail.com)'
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
        verbose_name_plural = 'Configuración de Email'
    
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

    def get_correos_notificaciones_lista(self):
        """Retorna una lista de correos de notificación parseados"""
        if not self.correos_notificaciones:
            return []

        # Parsear correos separados por comas, limpiar espacios
        correos = [email.strip() for email in self.correos_notificaciones.split(',')]
        # Filtrar correos vacíos
        correos = [email for email in correos if email]
        return correos

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
        from django.conf import settings
        
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
            # Aplicar configuración temporal
            self.aplicar_configuracion()
            
            # Enviar email de prueba
            asunto = 'NaviPort RD - Email de Prueba'
            mensaje = f'''
¡Felicitaciones!

La configuración de email de NaviPort RD está funcionando correctamente.

Este email de prueba fue enviado el {timezone.now().strftime('%d/%m/%Y a las %H:%M')}.

Configuración utilizada:
- Servidor: {self.email_host}:{self.email_port}
- Usuario: {self.email_host_user}
- Cifrado: {"TLS" if self.email_use_tls else "SSL" if self.email_use_ssl else "Sin cifrado"}

Si recibiste este email, el sistema está listo para enviar notificaciones y emails de recuperación de contraseña.

---
Sistema NaviPort RD
            '''
            
            send_mail(
                asunto,
                mensaje,
                self.default_from_email,
                [email_destino],
                fail_silently=False,
            )
            
            # Actualizar flags de éxito y contador
            self.test_email_sent = True
            self.last_test_date = timezone.now()
            self.total_emails_sent += 1
            self.save(update_fields=['test_email_sent', 'last_test_date', 'total_emails_sent'])
            
            return True, "Email de prueba enviado exitosamente"
            
        except Exception as e:
            error_msg = str(e)
            
            # Mejorar mensajes de error comunes
            if "Username and Password not accepted" in error_msg:
                if "gmail" in self.email_host.lower():
                    error_msg = "Credenciales no aceptadas por Gmail. Para Gmail necesitas usar una 'App Password' en lugar de tu contraseña normal. Ve a: Cuenta de Google > Seguridad > Contraseñas de aplicaciones."
                else:
                    error_msg = "Usuario y contraseña no aceptados por el servidor SMTP. Verifica que las credenciales sean correctas."
            elif "Connection refused" in error_msg:
                error_msg = f"No se pudo conectar al servidor {self.email_host}:{self.email_port}. Verifica el host y puerto."
            elif "timed out" in error_msg:
                error_msg = "Conexión agotó tiempo de espera. Verifica la conexión a internet y la configuración del servidor."
            
            return False, error_msg
