from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import re


def validate_cedula_dominicana(value):
    """Validar formato de cédula dominicana (XXX-XXXXXXX-X)"""
    pattern = r'^\d{3}-\d{7}-\d{1}$'
    if not re.match(pattern, value):
        raise ValidationError('La cédula debe tener el formato XXX-XXXXXXX-X')


# Función de extracción de fecha eliminada por decisión del usuario


class Persona(models.Model):
    cedula = models.CharField(
        max_length=13,
        unique=False,
        blank=True,
        null=True,
        validators=[validate_cedula_dominicana],
        help_text="Formato: XXX-XXXXXXX-X (para dominicanos)"
    )
    pasaporte = models.CharField(
        max_length=20,
        unique=False,
        blank=True,
        null=True,
        help_text="Número de pasaporte (para extranjeros sin cédula)"
    )
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    cargo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Cargo/Posición',
        help_text='Ej: Conductor, Operador, Técnico, etc.'
    )
    licencia_conducir = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Licencia de Conducir',
        help_text='Número de licencia de conducir si aplica'
    )

    # Campos de auditoría
    empresa = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='personas_registradas',
        help_text="Empresa que registró esta persona"
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'gestion_personal_persona'
        verbose_name = 'Persona'
        verbose_name_plural = 'Personas'
        ordering = ['apellido', 'nombre']
        unique_together = ['cedula', 'empresa']

    def __str__(self):
        documento = self.cedula or self.pasaporte or "Sin documento"
        return f"{self.nombre} {self.apellido} - {documento}"

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def get_documento_cedula(self):
        """Obtener documento de cédula si existe"""
        return self.documentos.filter(tipo_documento='cedula').first()

    def get_documento_licencia(self):
        """Obtener documento de licencia si existe"""
        return self.documentos.filter(tipo_documento='licencia_conducir').first()

    def tiene_documentos_minimos(self):
        """
        Verifica si la persona tiene los documentos mínimos requeridos:
        - Al menos 1 documento de identidad (cédula o pasaporte)
        - Al menos 1 documento adicional (licencia, pasaporte u otro)
        Retorna tupla (bool, str) con resultado y mensaje
        """
        documentos = self.documentos.all()
        count = documentos.count()

        if count < 2:
            return False, f'Se requieren al menos 2 documentos. Actualmente tiene {count}.'

        # Verificar que tenga al menos un documento de identidad
        tiene_identidad = documentos.filter(
            tipo_documento__in=['cedula', 'pasaporte']
        ).exists()

        if not tiene_identidad:
            return False, 'Debe tener al menos un documento de identidad (cédula o pasaporte).'

        return True, 'Documentos mínimos completos'

    def documentos_faltantes(self):
        """Retorna lista de tipos de documentos faltantes para cumplir el mínimo"""
        documentos_actuales = list(self.documentos.values_list('tipo_documento', flat=True))
        faltantes = []

        # Si no tiene documento de identidad
        if not any(doc in documentos_actuales for doc in ['cedula', 'pasaporte']):
            faltantes.append('Documento de identidad (cédula o pasaporte)')

        # Si tiene menos de 2 documentos en total
        if len(documentos_actuales) < 2:
            faltantes.append(f'Al menos {2 - len(documentos_actuales)} documento(s) adicional(es)')

        return faltantes

# Propiedades de fecha de nacimiento y edad eliminadas

    def clean(self):
        super().clean()
        # Validar que tenga al menos cédula o pasaporte
        if not self.cedula and not self.pasaporte:
            raise ValidationError('Debe proporcionar al menos una cédula o un pasaporte.')
        # No validar extracción de fecha de nacimiento


class DocumentoPersonal(models.Model):
    TIPO_DOCUMENTO_CHOICES = [
        ('cedula', 'Cédula de Identidad'),
        ('licencia_conducir', 'Licencia de Conducir'),
        ('pasaporte', 'Pasaporte'),
        ('otro', 'Otro Documento'),
    ]

    ESTADO_VALIDACION_CHOICES = [
        ('pendiente', 'Pendiente de Validación'),
        ('validado', 'Validado'),
        ('rechazado', 'Rechazado'),
        ('vencido', 'Vencido'),
    ]

    persona = models.ForeignKey(
        Persona,
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
        upload_to='documentos/personal/%Y/%m/',
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
        related_name='documentos_personales_subidos'
    )
    validado_por = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos_personales_validados'
    )
    fecha_validacion = models.DateTimeField(blank=True, null=True)
    comentarios_validacion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'gestion_personal_documento'
        verbose_name = 'Documento Personal'
        verbose_name_plural = 'Documentos Personales'
        ordering = ['-fecha_subida']
        unique_together = ['persona', 'tipo_documento']

    def __str__(self):
        return f"{self.persona.nombre_completo} - {self.get_tipo_documento_display()}"

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
