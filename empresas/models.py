from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import date, timedelta


def get_default_expiration_date():
    """Función para obtener fecha de expiración por defecto (1 año desde hoy)"""
    return date.today() + timedelta(days=365)


class Servicio(models.Model):
    """
    Modelo para los tipos de servicios que puede ofrecer una empresa
    """
    nombre = models.CharField(max_length=100, verbose_name='Nombre del Servicio')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado el')

    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class EmpresaServicio(models.Model):
    """
    Modelo para empresas proveedoras de servicios y personal operativo
    (Diferente de accounts.Empresa que son empresas solicitantes con usuarios del sistema)
    """
    rnc = models.CharField(
        max_length=15,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{3}-\d{5}-\d{1}$',
                message='Formato inválido. Use XXX-XXXXX-X para RNC'
            )
        ],
        verbose_name='RNC'
    )
    nombre = models.CharField(max_length=200, verbose_name='Nombre de la Empresa')
    telefono = models.CharField(
        max_length=15,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\d{3}-\d{3}-\d{4}$',
                message='Formato inválido. Use XXX-XXX-XXXX'
            )
        ],
        verbose_name='Teléfono'
    )
    email = models.EmailField(blank=True, verbose_name='Email')
    direccion = models.TextField(blank=True, verbose_name='Dirección')
    
    # Campos de licencia
    numero_licencia = models.CharField(
        max_length=50,
        unique=True,
        default='TEMP-LICENSE-001',
        verbose_name='Número de Licencia',
        help_text='Número único de licencia de operación'
    )
    fecha_expiracion_licencia = models.DateField(
        default=get_default_expiration_date,
        verbose_name='Fecha de Expiración de Licencia',
        help_text='Fecha hasta la cual la licencia es válida'
    )
    
    # Servicios autorizados
    servicios_autorizados = models.ManyToManyField(
        Servicio,
        blank=True,
        verbose_name='Servicios Autorizados',
        help_text='Servicios que la empresa está autorizada a ofrecer'
    )
    
    activa = models.BooleanField(default=True, verbose_name='Activa')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado el')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado el')

    class Meta:
        verbose_name = 'Empresa de Servicio'
        verbose_name_plural = 'Empresas de Servicios'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def licencia_vigente(self):
        """Verifica si la licencia está vigente"""
        return self.fecha_expiracion_licencia >= date.today()
    
    def dias_para_vencimiento(self):
        """Calcula los días restantes hasta el vencimiento de la licencia"""
        if self.fecha_expiracion_licencia:
            delta = self.fecha_expiracion_licencia - date.today()
            return delta.days
        return None
    
    def get_servicios_names(self):
        """Obtiene los nombres de los servicios autorizados"""
        return ", ".join([servicio.nombre for servicio in self.servicios_autorizados.all()])
    
    def licencia_por_vencer(self, dias=30):
        """Verifica si la licencia vence en los próximos N días"""
        dias_restantes = self.dias_para_vencimiento()
        return dias_restantes is not None and dias_restantes <= dias


class Personal(models.Model):
    """
    Modelo para personal operativo que visita las instalaciones portuarias
    (NO son usuarios del sistema, solo datos para control de acceso)
    """
    nombre = models.CharField(max_length=100, verbose_name='Nombre Completo')
    cedula = models.CharField(
        max_length=13,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\d{3}-\d{7}-\d{1}$',
                message='Formato inválido. Use XXX-XXXXXXX-X para cédula'
            )
        ],
        verbose_name='Cédula',
        help_text='Para dominicanos'
    )
    pasaporte = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Pasaporte',
        help_text='Para extranjeros sin cédula dominicana'
    )
    cargo = models.CharField(
        max_length=100, 
        blank=True,
        help_text='Ej: Conductor, Operador, Técnico, etc.',
        verbose_name='Cargo/Posición'
    )
    licencia_conducir = models.CharField(
        max_length=20,
        blank=True,
        help_text='Número de licencia de conducir si aplica',
        verbose_name='Licencia de Conducir'
    )
    telefono = models.CharField(
        max_length=15,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\d{3}-\d{3}-\d{4}$',
                message='Formato inválido. Use XXX-XXX-XXXX'
            )
        ],
        verbose_name='Teléfono'
    )
    activo = models.BooleanField(default=True, verbose_name='Activo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado el')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado el')

    class Meta:
        verbose_name = 'Personal'
        verbose_name_plural = 'Personal'
        ordering = ['nombre']

    def __str__(self):
        documento = self.cedula or self.pasaporte or "Sin documento"
        return f"{self.nombre} ({documento})"

    def clean(self):
        """Validación: debe tener al menos cédula o pasaporte"""
        from django.core.exceptions import ValidationError
        if not self.cedula and not self.pasaporte:
            raise ValidationError('Debe proporcionar al menos una cédula o un pasaporte.')

    def get_empresas(self):
        """Obtiene las empresas donde trabaja esta persona"""
        return EmpresaServicio.objects.filter(personalempresa__personal=self, personalempresa__activo=True)


class PersonalEmpresa(models.Model):
    """
    Tabla intermedia para la relación many-to-many entre Personal y EmpresaServicio
    Una persona puede trabajar para múltiples empresas
    """
    personal = models.ForeignKey(
        Personal,
        on_delete=models.CASCADE,
        verbose_name='Personal'
    )
    empresa = models.ForeignKey(
        EmpresaServicio,
        on_delete=models.CASCADE,
        verbose_name='Empresa'
    )
    fecha_inicio = models.DateField(
        auto_now_add=True,
        verbose_name='Fecha de Inicio'
    )
    fecha_fin = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Finalización'
    )
    activo = models.BooleanField(default=True, verbose_name='Activo')
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones'
    )

    class Meta:
        verbose_name = 'Personal de Empresa'
        verbose_name_plural = 'Personal de Empresas'
        unique_together = ['personal', 'empresa']
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"{self.personal.nombre} - {self.empresa.nombre}"
