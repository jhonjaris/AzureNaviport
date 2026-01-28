from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import re


def validate_placa_dominicana(value):
    """Validar formato de placa dominicana (A123456 o AB123456)"""
    pattern = r'^[A-Z]{1,2}\d{6}$'
    if not re.match(pattern, value.upper()):
        raise ValidationError('La placa debe tener formato A123456 o AB123456')


class Vehiculo(models.Model):
    TIPO_VEHICULO_CHOICES = [
        ('automovil', 'Automóvil'),
        ('camion', 'Camión'),
        ('camioneta', 'Camioneta'),
        ('motocicleta', 'Motocicleta'),
        ('autobus', 'Autobús'),
        ('trailer', 'Trailer'),
        ('montacargas', 'Montacargas'),
        ('otro', 'Otro'),
    ]

    placa = models.CharField(
        max_length=8,
        unique=True,
        validators=[validate_placa_dominicana],
        help_text="Formato: A123456 o AB123456"
    )
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    ano = models.PositiveIntegerField(
        help_text="Año del vehículo (ej: 2020)"
    )
    color = models.CharField(max_length=30)
    tipo_vehiculo = models.CharField(
        max_length=20,
        choices=TIPO_VEHICULO_CHOICES
    )

    # Información adicional
    numero_chasis = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Número de chasis (VIN)"
    )
    numero_motor = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    # Notas adicionales
    notas_adicionales = models.TextField(
        blank=True,
        null=True,
        help_text="Notas o comentarios adicionales sobre el vehículo"
    )

    # Campos de auditoría
    empresa_propietaria = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vehiculos_registrados',
        help_text="Empresa propietaria del vehículo"
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)

    # Campos de inhabilitación
    motivo_inhabilitacion = models.TextField(
        blank=True,
        null=True,
        help_text="Motivo por el cual se inhabilitó el vehículo"
    )
    fecha_inhabilitacion = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Fecha en que se inhabilitó el vehículo"
    )
    inhabilitado_por = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vehiculos_inhabilitados',
        help_text="Usuario que inhabilitó el vehículo"
    )

    class Meta:
        db_table = 'gestion_vehiculos_vehiculo'
        verbose_name = 'Vehículo'
        verbose_name_plural = 'Vehículos'
        ordering = ['placa']

    def __str__(self):
        return f"{self.placa} - {self.marca} {self.modelo} ({self.ano})"

    @property
    def descripcion_completa(self):
        return f"{self.marca} {self.modelo} {self.ano} - {self.color} - {self.placa}"

    @property
    def edad_vehiculo(self):
        """Calcula la edad del vehículo"""
        ano_actual = timezone.now().year
        return ano_actual - self.ano

    def get_documento_matricula(self):
        """Obtener documento de matrícula si existe"""
        return self.documentos.filter(tipo_documento='matricula').first()

    def get_documento_seguro(self):
        """Obtener documento de seguro si existe"""
        return self.documentos.filter(tipo_documento='seguro').first()

    def inhabilitar(self, usuario, motivo):
        """Inhabilitar vehículo con registro de auditoría"""
        self.activo = False
        self.motivo_inhabilitacion = motivo
        self.fecha_inhabilitacion = timezone.now()
        self.inhabilitado_por = usuario
        self.save()

    def reactivar(self):
        """Reactivar vehículo y limpiar datos de inhabilitación"""
        self.activo = True
        self.motivo_inhabilitacion = None
        self.fecha_inhabilitacion = None
        self.inhabilitado_por = None
        self.save()

    def clean(self):
        super().clean()
        # Validar año
        ano_actual = timezone.now().year
        if self.ano < 1900 or self.ano > ano_actual + 1:
            raise ValidationError({'ano': f'El año debe estar entre 1900 y {ano_actual + 1}'})

        # Convertir placa a mayúsculas
        if self.placa:
            self.placa = self.placa.upper()


class DocumentoVehiculo(models.Model):
    TIPO_DOCUMENTO_CHOICES = [
        ('matricula', 'Matrícula'),
        ('registro', 'Registro'),
        ('seguro', 'Seguro'),
        ('revision_tecnica', 'Revisión Técnica'),
        ('permiso_circulacion', 'Permiso de Circulación'),
        ('otro', 'Otro Documento'),
    ]

    ESTADO_VALIDACION_CHOICES = [
        ('pendiente', 'Pendiente de Validación'),
        ('validado', 'Validado'),
        ('rechazado', 'Rechazado'),
        ('vencido', 'Vencido'),
    ]

    vehiculo = models.ForeignKey(
        Vehiculo,
        on_delete=models.CASCADE,
        related_name='documentos'
    )
    tipo_documento = models.CharField(
        max_length=20,
        choices=TIPO_DOCUMENTO_CHOICES
    )
    numero_documento = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Número del documento (opcional)"
    )
    archivo = models.FileField(
        upload_to='documentos/vehiculos/%Y/%m/',
        help_text="Archivo del documento (PDF, JPG, PNG máx. 5MB)"
    )
    fecha_vencimiento = models.DateField(
        blank=True,
        null=True,
        help_text="Fecha de vencimiento del documento"
    )
    estado_validacion = models.CharField(
        max_length=20,
        choices=ESTADO_VALIDACION_CHOICES,
        default='pendiente'
    )

    # Campos de auditoría
    fecha_subida = models.DateTimeField(auto_now_add=True)
    subido_por = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='documentos_vehiculos_subidos'
    )
    validado_por = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos_vehiculos_validados'
    )
    fecha_validacion = models.DateTimeField(blank=True, null=True)
    comentarios_validacion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'gestion_vehiculos_documento'
        verbose_name = 'Documento de Vehículo'
        verbose_name_plural = 'Documentos de Vehículos'
        ordering = ['-fecha_subida']
        unique_together = ['vehiculo', 'tipo_documento']

    def __str__(self):
        return f"{self.vehiculo.placa} - {self.get_tipo_documento_display()}"

    @property
    def esta_vencido(self):
        """Verifica si el documento está vencido"""
        if self.fecha_vencimiento:
            return timezone.now().date() > self.fecha_vencimiento
        return False

    @property
    def proxima_vencer(self):
        """Verifica si el documento vence en los próximos 30 días"""
        if self.fecha_vencimiento:
            dias_hasta_vencimiento = (self.fecha_vencimiento - timezone.now().date()).days
            return 0 <= dias_hasta_vencimiento <= 30
        return False

    def clean(self):
        super().clean()
        # Actualizar estado si está vencido
        if self.esta_vencido and self.estado_validacion != 'vencido':
            self.estado_validacion = 'vencido'
