from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from datetime import datetime, timedelta
import uuid
# Imports for QR code generation will be handled at runtime to avoid dependency issues
import json
from django.conf import settings

class Autorizacion(models.Model):
    """Modelo para las autorizaciones de acceso con código QR"""
    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('vencida', 'Vencida'),
        ('revocada', 'Revocada'),
        ('usada', 'Usada'),
    ]
    
    # Información básica
    codigo = models.CharField(
        max_length=30, 
        unique=True, 
        editable=False,
        verbose_name='Código de Autorización'
    )
    uuid = models.UUIDField(
        default=uuid.uuid4, 
        editable=False, 
        unique=True,
        verbose_name='UUID único'
    )
    solicitud = models.OneToOneField(
        'solicitudes.Solicitud', 
        on_delete=models.CASCADE, 
        related_name='autorizacion',
        verbose_name='Solicitud'
    )
    
    # Datos de la autorización
    empresa_nombre = models.CharField(max_length=200, verbose_name='Empresa')
    empresa_rnc = models.CharField(max_length=15, verbose_name='RNC')
    representante_nombre = models.CharField(max_length=200, verbose_name='Representante')
    representante_cedula = models.CharField(max_length=15, verbose_name='Cédula')
    
    # Vigencia
    valida_desde = models.DateTimeField(verbose_name='Válida desde')
    valida_hasta = models.DateTimeField(verbose_name='Válida hasta')
    
    # Detalles del acceso
    puerto_nombre = models.CharField(max_length=100, verbose_name='Puerto')
    motivo_acceso = models.CharField(max_length=200, verbose_name='Motivo')
    vehiculos_autorizados = models.JSONField(
        default=list, 
        blank=True,
        verbose_name='Vehículos Autorizados'
    )
    
    # Estado y control
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default='activa',
        verbose_name='Estado'
    )
    
    # QR Code
    qr_code = models.ImageField(
        upload_to='autorizaciones/qr/%Y/%m/',
        blank=True,
        verbose_name='Código QR'
    )
    
    # Metadatos
    generada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='autorizaciones_generadas',
        verbose_name='Generada por'
    )
    creada_el = models.DateTimeField(auto_now_add=True, verbose_name='Creada el')
    actualizada_el = models.DateTimeField(auto_now=True, verbose_name='Actualizada el')
    revocada_el = models.DateTimeField(null=True, blank=True, verbose_name='Revocada el')
    revocada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='autorizaciones_revocadas',
        verbose_name='Revocada por'
    )
    motivo_revocacion = models.TextField(blank=True, verbose_name='Motivo de Revocación')
    
    class Meta:
        verbose_name = 'Autorización'
        verbose_name_plural = 'Autorizaciones'
        ordering = ['-creada_el']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['uuid']),
            models.Index(fields=['estado', '-creada_el']),
        ]

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self.generar_codigo()
        
        # Copiar datos de la solicitud
        if self.solicitud and not self.empresa_nombre:
            self.empresa_nombre = self.solicitud.empresa.nombre
            self.empresa_rnc = self.solicitud.empresa.rnc
            self.representante_nombre = self.solicitud.solicitante.get_full_name()
            self.representante_cedula = self.solicitud.solicitante.cedula_rnc
            self.puerto_nombre = self.solicitud.puerto_destino.nombre
            self.motivo_acceso = self.solicitud.motivo_acceso.nombre
            
            # Crear fecha de inicio y fin
            fecha_inicio = datetime.combine(
                self.solicitud.fecha_ingreso, 
                self.solicitud.hora_ingreso
            )
            fecha_fin = datetime.combine(
                self.solicitud.fecha_salida, 
                self.solicitud.hora_salida
            )
            self.valida_desde = timezone.make_aware(fecha_inicio)
            self.valida_hasta = timezone.make_aware(fecha_fin)
            
            # Obtener vehículos
            vehiculos = []
            for vehiculo in self.solicitud.vehiculos.all():
                vehiculos.append({
                    'placa': vehiculo.placa,
                    'tipo': vehiculo.tipo_vehiculo,
                    'conductor': vehiculo.conductor_nombre,
                    'licencia': vehiculo.conductor_licencia
                })
            self.vehiculos_autorizados = vehiculos
        
        super().save(*args, **kwargs)
        
        # Generar QR si no existe
        if not self.qr_code:
            self.generar_qr()

    def generar_codigo(self):
        """Genera un código único para la autorización"""
        año = timezone.now().year
        count = Autorizacion.objects.filter(creada_el__year=año).count() + 1
        return f"AUT-{año}-{count:03d}"
    
    def generar_qr(self):
        """Genera el código QR para la autorización"""
        try:
            import qrcode
            from io import BytesIO
            from django.core.files import File

            # Generar URL de verificación pública
            # En producción, cambiar por el dominio real
            base_url = settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://127.0.0.1:8002'
            verificacion_url = f"{base_url}/verificar/{self.uuid}/"

            # El QR solo contiene la URL de verificación
            # Esto es más seguro y hace el QR más pequeño
            qr_data = verificacion_url

            # Crear QR con configuración optimizada para lectura móvil
            qr = qrcode.QRCode(
                version=3,  # Aumentado para mejor lectura
                error_correction=qrcode.constants.ERROR_CORRECT_H,  # Alta corrección de errores
                box_size=12,  # Tamaño más grande para móviles
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)

            # Crear imagen
            qr_image = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            qr_image.save(buffer, format='PNG')

            # Guardar archivo
            filename = f'qr_{self.codigo}.png'
            self.qr_code.save(filename, File(buffer), save=False)
            buffer.close()

            # Guardar sin crear bucle infinito
            Autorizacion.objects.filter(pk=self.pk).update(qr_code=self.qr_code)
        except ImportError:
            # Si no están las dependencias, simplemente no generar QR
            pass
    
    def esta_vigente(self):
        """Verifica si la autorización está vigente"""
        ahora = timezone.now()
        return (
            self.estado == 'activa' and
            self.valida_desde <= ahora <= self.valida_hasta
        )
    
    def dias_restantes(self):
        """Retorna los días restantes de vigencia"""
        if not self.esta_vigente():
            return 0
        return (self.valida_hasta - timezone.now()).days
    
    def actualizar_estado(self):
        """Actualiza el estado basado en la fecha actual"""
        if self.estado == 'activa' and timezone.now() > self.valida_hasta:
            self.estado = 'vencida'
            self.save()
    
    def revocar(self, usuario, motivo=""):
        """Revoca la autorización"""
        self.estado = 'revocada'
        self.revocada_el = timezone.now()
        self.revocada_por = usuario
        self.motivo_revocacion = motivo
        self.save()

    def __str__(self):
        return f"{self.codigo} - {self.empresa_nombre} - {self.get_estado_display()}"

class RegistroAcceso(models.Model):
    """Modelo para registrar los accesos físicos al puerto"""
    TIPO_ACCESO_CHOICES = [
        ('ingreso', 'Ingreso'),
        ('salida', 'Salida'),
    ]
    
    ESTADO_CHOICES = [
        ('autorizado', 'Autorizado'),
        ('denegado', 'Denegado'),
        ('pendiente', 'Pendiente Verificación'),
    ]
    
    # Información básica
    autorizacion = models.ForeignKey(
        Autorizacion,
        on_delete=models.CASCADE,
        related_name='registros_acceso',
        verbose_name='Autorización'
    )
    tipo_acceso = models.CharField(
        max_length=10,
        choices=TIPO_ACCESO_CHOICES,
        verbose_name='Tipo de Acceso'
    )
    
    # Detalles del acceso
    vehiculo_placa = models.CharField(max_length=15, verbose_name='Placa del Vehículo')
    conductor_nombre = models.CharField(max_length=200, verbose_name='Conductor')
    
    # Control y verificación
    oficial_acceso = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='registros_procesados',
        verbose_name='Oficial de Acceso'
    )
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name='Estado'
    )
    
    # Verificaciones realizadas
    documento_verificado = models.BooleanField(default=False, verbose_name='Documento Verificado')
    vehiculo_verificado = models.BooleanField(default=False, verbose_name='Vehículo Verificado')
    conductor_verificado = models.BooleanField(default=False, verbose_name='Conductor Verificado')
    
    # Observaciones
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    motivo_denegacion = models.TextField(blank=True, verbose_name='Motivo de Denegación')
    
    # Metadatos
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Fecha y Hora')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='Dirección IP')
    
    class Meta:
        verbose_name = 'Registro de Acceso'
        verbose_name_plural = 'Registros de Acceso'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['autorizacion', 'tipo_acceso']),
            models.Index(fields=['-timestamp']),
            models.Index(fields=['oficial_acceso', '-timestamp']),
        ]
    
    def autorizar(self, observaciones=""):
        """Autoriza el acceso"""
        self.estado = 'autorizado'
        self.observaciones = observaciones
        self.save()
    
    def denegar(self, motivo):
        """Deniega el acceso"""
        self.estado = 'denegado'
        self.motivo_denegacion = motivo
        self.save()

    def __str__(self):
        return f"{self.get_tipo_acceso_display()} - {self.vehiculo_placa} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"

class Discrepancia(models.Model):
    """Modelo para registrar discrepancias en el control de acceso"""
    TIPO_DISCREPANCIA_CHOICES = [
        ('vehiculo_diferente', 'Vehículo Diferente'),
        ('conductor_diferente', 'Conductor Diferente'),
        ('documento_vencido', 'Documento Vencido'),
        ('documento_ilegible', 'Documento Ilegible'),
        ('autorizacion_vencida', 'Autorización Vencida'),
        ('datos_incorrectos', 'Datos Incorrectos'),
        ('otros', 'Otros'),
    ]
    
    ESTADO_CHOICES = [
        ('reportada', 'Reportada'),
        ('en_revision', 'En Revisión'),
        ('resuelta', 'Resuelta'),
        ('cerrada', 'Cerrada'),
    ]
    
    # Información básica
    codigo = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name='Código de Discrepancia'
    )
    registro_acceso = models.ForeignKey(
        RegistroAcceso,
        on_delete=models.CASCADE,
        related_name='discrepancias',
        verbose_name='Registro de Acceso'
    )
    
    # Tipo y descripción
    tipo_discrepancia = models.CharField(
        max_length=25,
        choices=TIPO_DISCREPANCIA_CHOICES,
        verbose_name='Tipo de Discrepancia'
    )
    descripcion = models.TextField(verbose_name='Descripción')
    
    # Control
    reportada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='discrepancias_reportadas',
        verbose_name='Reportada por'
    )
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default='reportada',
        verbose_name='Estado'
    )
    
    # Resolución
    asignada_a = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='discrepancias_asignadas',
        verbose_name='Asignada a'
    )
    resuelta_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='discrepancias_resueltas',
        verbose_name='Resuelta por'
    )
    resolucion = models.TextField(blank=True, verbose_name='Resolución')
    fecha_resolucion = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Resolución')
    
    # Metadatos
    creada_el = models.DateTimeField(auto_now_add=True, verbose_name='Creada el')
    actualizada_el = models.DateTimeField(auto_now=True, verbose_name='Actualizada el')
    
    class Meta:
        verbose_name = 'Discrepancia'
        verbose_name_plural = 'Discrepancias'
        ordering = ['-creada_el']
    
    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self.generar_codigo()
        super().save(*args, **kwargs)
    
    def generar_codigo(self):
        """Genera un código único para la discrepancia"""
        año = timezone.now().year
        count = Discrepancia.objects.filter(creada_el__year=año).count() + 1
        return f"DISC-{año}-{count:03d}"
    
    def resolver(self, usuario, resolucion):
        """Resuelve la discrepancia"""
        self.estado = 'resuelta'
        self.resuelta_por = usuario
        self.resolucion = resolucion
        self.fecha_resolucion = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.codigo} - {self.get_tipo_discrepancia_display()}"


class SolicitudExtension(models.Model):
    """Modelo para solicitar extensión de validez de una autorización"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]

    # Información básica
    codigo = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name='Código de Extensión'
    )
    autorizacion = models.ForeignKey(
        Autorizacion,
        on_delete=models.CASCADE,
        related_name='solicitudes_extension',
        verbose_name='Autorización'
    )

    # Datos de la solicitud
    fecha_vencimiento_actual = models.DateTimeField(
        verbose_name='Fecha de Vencimiento Actual',
        help_text='Fecha actual de vencimiento de la autorización'
    )
    fecha_vencimiento_solicitada = models.DateTimeField(
        verbose_name='Nueva Fecha de Vencimiento Solicitada',
        help_text='Nueva fecha hasta la cual se solicita extender la autorización'
    )
    motivo = models.TextField(
        verbose_name='Motivo de la Extensión',
        help_text='Justificación detallada del por qué se necesita la extensión'
    )

    # Control
    solicitada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='extensiones_solicitadas',
        verbose_name='Solicitada por'
    )
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name='Estado'
    )

    # Respuesta (aprobación/rechazo)
    procesada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='extensiones_procesadas',
        verbose_name='Procesada por'
    )
    fecha_procesamiento = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Procesamiento'
    )
    observaciones_respuesta = models.TextField(
        blank=True,
        verbose_name='Observaciones de la Respuesta',
        help_text='Comentarios del supervisor/dirección al aprobar o rechazar'
    )
    motivo_rechazo = models.TextField(
        blank=True,
        verbose_name='Motivo del Rechazo',
        help_text='Razón por la cual se rechaza la extensión'
    )

    # Metadatos
    creada_el = models.DateTimeField(auto_now_add=True, verbose_name='Creada el')
    actualizada_el = models.DateTimeField(auto_now=True, verbose_name='Actualizada el')

    class Meta:
        verbose_name = 'Solicitud de Extensión'
        verbose_name_plural = 'Solicitudes de Extensión'
        ordering = ['-creada_el']
        indexes = [
            models.Index(fields=['estado', '-creada_el']),
            models.Index(fields=['autorizacion']),
            models.Index(fields=['solicitada_por']),
        ]

    def save(self, *args, **kwargs):
        # Generar código si no existe
        if not self.codigo:
            self.codigo = self.generar_codigo()

        # Guardar fecha de vencimiento actual si no está establecida
        if not self.fecha_vencimiento_actual and self.autorizacion:
            self.fecha_vencimiento_actual = self.autorizacion.valida_hasta

        super().save(*args, **kwargs)

    def generar_codigo(self):
        """Genera un código único para la solicitud de extensión"""
        año = timezone.now().year
        count = SolicitudExtension.objects.filter(creada_el__year=año).count() + 1
        return f"EXT-{año}-{count:04d}"

    @property
    def dias_extension_solicitados(self):
        """Calcula la cantidad de días de extensión solicitados"""
        if self.fecha_vencimiento_solicitada and self.fecha_vencimiento_actual:
            delta = self.fecha_vencimiento_solicitada - self.fecha_vencimiento_actual
            return delta.days
        return 0

    @property
    def esta_pendiente(self):
        """Verifica si la solicitud está pendiente"""
        return self.estado == 'pendiente'

    @property
    def fue_aprobada(self):
        """Verifica si la solicitud fue aprobada"""
        return self.estado == 'aprobada'

    @property
    def fue_rechazada(self):
        """Verifica si la solicitud fue rechazada"""
        return self.estado == 'rechazada'

    def aprobar(self, usuario, observaciones=""):
        """Aprueba la solicitud de extensión y actualiza la autorización"""
        from django.utils import timezone

        self.estado = 'aprobada'
        self.procesada_por = usuario
        self.fecha_procesamiento = timezone.now()
        self.observaciones_respuesta = observaciones
        self.save()

        # Actualizar fecha de vencimiento de la autorización
        self.autorizacion.valida_hasta = self.fecha_vencimiento_solicitada
        self.autorizacion.save(update_fields=['valida_hasta'])

    def rechazar(self, usuario, motivo_rechazo):
        """Rechaza la solicitud de extensión"""
        from django.utils import timezone

        self.estado = 'rechazada'
        self.procesada_por = usuario
        self.fecha_procesamiento = timezone.now()
        self.motivo_rechazo = motivo_rechazo
        self.save()

    def __str__(self):
        return f"{self.codigo} - {self.autorizacion.codigo} - {self.get_estado_display()}"
