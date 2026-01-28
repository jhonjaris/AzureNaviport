from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.validators import FileExtensionValidator

class Incumplimiento(models.Model):
    """
    Modelo para registrar incumplimientos de proveedores de servicio.
    Reportados por oficiales de seguridad cuando se detectan irregularidades.
    """
    TIPO_CHOICES = [
        ('documentacion_invalida', 'Documentación Inválida o Vencida'),
        ('personal_no_autorizado', 'Personal No Autorizado'),
        ('vehiculo_no_autorizado', 'Vehículo No Autorizado'),
        ('horario_incumplido', 'Incumplimiento de Horario Autorizado'),
        ('zona_no_autorizada', 'Acceso a Zona No Autorizada'),
        ('seguridad', 'Incumplimiento de Normas de Seguridad'),
        ('otro', 'Otro Incumplimiento'),
    ]

    ESTADO_CHOICES = [
        ('reportado', 'Reportado'),
        ('en_revision', 'En Revisión'),
        ('pendiente_subsanacion', 'Pendiente de Subsanación'),
        ('subsanado', 'Subsanado'),
        ('desestimado', 'Desestimado'),
    ]

    # Relaciones
    solicitud = models.ForeignKey(
        'solicitudes.Solicitud',
        on_delete=models.CASCADE,
        related_name='incumplimientos',
        verbose_name='Solicitud Relacionada',
        help_text='Solicitud asociada al incumplimiento'
    )

    autorizacion = models.ForeignKey(
        'control_acceso.Autorizacion',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='incumplimientos',
        verbose_name='Autorización Relacionada',
        help_text='Autorización asociada si ya fue aprobada'
    )

    # Información del incumplimiento
    tipo = models.CharField(
        max_length=30,
        choices=TIPO_CHOICES,
        verbose_name='Tipo de Incumplimiento'
    )

    descripcion = models.TextField(
        verbose_name='Descripción del Incumplimiento',
        help_text='Detalle completo de la situación observada'
    )

    estado = models.CharField(
        max_length=25,
        choices=ESTADO_CHOICES,
        default='reportado',
        verbose_name='Estado'
    )

    # Usuarios involucrados
    reportado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='incumplimientos_reportados',
        verbose_name='Reportado Por',
        help_text='Oficial de acceso que detectó el incumplimiento'
    )

    revisado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incumplimientos_revisados',
        verbose_name='Revisado Por',
        help_text='Supervisor que revisó el incumplimiento'
    )

    # Ubicación del incumplimiento
    puerto = models.ForeignKey(
        'solicitudes.Puerto',
        on_delete=models.PROTECT,
        related_name='incumplimientos',
        verbose_name='Puerto'
    )

    lugar_puerto = models.ForeignKey(
        'solicitudes.LugarPuerto',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='incumplimientos',
        verbose_name='Lugar Específico'
    )

    # Archivo de evidencia (foto, documento escaneado, etc.)
    evidencia = models.FileField(
        upload_to='incumplimientos/evidencias/%Y/%m/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'])],
        verbose_name='Evidencia',
        help_text='Archivo con evidencia del incumplimiento (PDF, imagen o documento)'
    )

    # Observaciones adicionales
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones',
        help_text='Notas adicionales sobre el incumplimiento'
    )

    # Timestamps
    fecha_incumplimiento = models.DateTimeField(
        verbose_name='Fecha del Incumplimiento',
        help_text='Fecha y hora en que ocurrió el incumplimiento'
    )

    fecha_reporte = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Reporte',
        editable=False
    )

    fecha_revision = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Revisión'
    )

    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Modificación'
    )

    class Meta:
        verbose_name = 'Incumplimiento'
        verbose_name_plural = 'Incumplimientos'
        ordering = ['-fecha_incumplimiento', '-fecha_reporte']
        indexes = [
            models.Index(fields=['solicitud', 'estado']),
            models.Index(fields=['reportado_por', 'fecha_reporte']),
            models.Index(fields=['estado']),
        ]

    def __str__(self):
        return f"Incumplimiento #{self.pk} - {self.get_tipo_display()} - {self.solicitud.empresa.nombre}"

    def puede_solicitar_subsanacion(self):
        """Verifica si se puede solicitar subsanación"""
        return self.estado in ['reportado', 'en_revision']

    def empresa(self):
        """Retorna la empresa asociada al incumplimiento"""
        return self.solicitud.empresa


class SolicitudSubsanacion(models.Model):
    """
    Modelo para solicitudes de subsanación emitidas por supervisores.
    Indica qué debe hacer la empresa para resolver el incumplimiento.
    """
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de Respuesta'),
        ('respondida', 'Respondida por Empresa'),
        ('aprobada', 'Subsanación Aprobada'),
        ('rechazada', 'Subsanación Rechazada'),
        ('vencida', 'Plazo Vencido'),
    ]

    # Relación con incumplimiento
    incumplimiento = models.OneToOneField(
        Incumplimiento,
        on_delete=models.CASCADE,
        related_name='solicitud_subsanacion',
        verbose_name='Incumplimiento'
    )

    # Información requerida
    informacion_requerida = models.TextField(
        verbose_name='Información/Documentación Requerida',
        help_text='Detalle específico de qué debe presentar la empresa para subsanar'
    )

    plazo_dias = models.PositiveIntegerField(
        default=5,
        verbose_name='Plazo en Días Hábiles',
        help_text='Cantidad de días hábiles para responder'
    )

    fecha_limite = models.DateTimeField(
        verbose_name='Fecha Límite',
        help_text='Fecha y hora límite para responder (calculada automáticamente)'
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name='Estado'
    )

    # Usuario que solicita la subsanación
    solicitado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='subsanaciones_solicitadas',
        verbose_name='Solicitado Por',
        help_text='Supervisor que solicita la subsanación'
    )

    # Timestamps
    fecha_solicitud = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Solicitud',
        editable=False
    )

    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Modificación'
    )

    class Meta:
        verbose_name = 'Solicitud de Subsanación'
        verbose_name_plural = 'Solicitudes de Subsanación'
        ordering = ['-fecha_solicitud']

    def __str__(self):
        return f"Subsanación - {self.incumplimiento} - {self.get_estado_display()}"

    def esta_vencida(self):
        """Verifica si la solicitud está vencida"""
        return timezone.now() > self.fecha_limite and self.estado == 'pendiente'

    def dias_restantes(self):
        """Calcula días restantes para responder"""
        if self.estado != 'pendiente':
            return 0
        delta = self.fecha_limite - timezone.now()
        return max(0, delta.days)


class RespuestaSubsanacion(models.Model):
    """
    Modelo para respuestas de subsanación enviadas por las empresas.
    Incluye documentación y explicación de las medidas correctivas.
    """
    ESTADO_CHOICES = [
        ('enviada', 'Enviada - Pendiente de Revisión'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada - Requiere Corrección'),
    ]

    # Relación con solicitud de subsanación
    solicitud_subsanacion = models.OneToOneField(
        SolicitudSubsanacion,
        on_delete=models.CASCADE,
        related_name='respuesta',
        verbose_name='Solicitud de Subsanación'
    )

    # Respuesta de la empresa
    explicacion = models.TextField(
        verbose_name='Explicación',
        help_text='Explicación de las medidas correctivas implementadas'
    )

    medidas_preventivas = models.TextField(
        blank=True,
        verbose_name='Medidas Preventivas',
        help_text='Medidas implementadas para prevenir futuros incumplimientos'
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='enviada',
        verbose_name='Estado'
    )

    # Usuario que responde
    respondido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='subsanaciones_respondidas',
        verbose_name='Respondido Por',
        help_text='Usuario de la empresa que envía la respuesta'
    )

    # Usuario que revisa
    revisado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subsanaciones_revisadas',
        verbose_name='Revisado Por',
        help_text='Supervisor que revisa la respuesta'
    )

    # Comentarios del revisor
    comentarios_revision = models.TextField(
        blank=True,
        verbose_name='Comentarios de Revisión',
        help_text='Comentarios del supervisor sobre la respuesta'
    )

    # Timestamps
    fecha_respuesta = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Respuesta',
        editable=False
    )

    fecha_revision = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Revisión'
    )

    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Modificación'
    )

    class Meta:
        verbose_name = 'Respuesta de Subsanación'
        verbose_name_plural = 'Respuestas de Subsanación'
        ordering = ['-fecha_respuesta']

    def __str__(self):
        return f"Respuesta - {self.solicitud_subsanacion.incumplimiento} - {self.get_estado_display()}"


class DocumentoSubsanacion(models.Model):
    """
    Modelo para los documentos adjuntos a una respuesta de subsanación.
    Permite múltiples archivos por respuesta.
    """
    TIPO_DOCUMENTO_CHOICES = [
        ('certificado', 'Certificado'),
        ('licencia', 'Licencia'),
        ('foto', 'Fotografía'),
        ('informe', 'Informe'),
        ('acta', 'Acta'),
        ('otro', 'Otro Documento'),
    ]

    # Relación con respuesta
    respuesta = models.ForeignKey(
        RespuestaSubsanacion,
        on_delete=models.CASCADE,
        related_name='documentos',
        verbose_name='Respuesta de Subsanación'
    )

    # Información del documento
    tipo_documento = models.CharField(
        max_length=20,
        choices=TIPO_DOCUMENTO_CHOICES,
        verbose_name='Tipo de Documento'
    )

    nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre del Documento'
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción opcional del documento'
    )

    archivo = models.FileField(
        upload_to='incumplimientos/subsanaciones/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'])],
        verbose_name='Archivo',
        help_text='Documento de soporte (PDF, imagen o documento Word)'
    )

    # Timestamps
    fecha_subida = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Subida',
        editable=False
    )

    class Meta:
        verbose_name = 'Documento de Subsanación'
        verbose_name_plural = 'Documentos de Subsanación'
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"{self.nombre} - {self.get_tipo_documento_display()}"
