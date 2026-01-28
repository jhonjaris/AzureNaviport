from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta
import uuid

class Puerto(models.Model):
    """Modelo para los puertos disponibles"""
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre')
    codigo = models.CharField(max_length=10, unique=True, verbose_name='Código')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    ubicacion = models.CharField(max_length=200, blank=True, verbose_name='Ubicación')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    fecha_creacion = models.DateTimeField(default=timezone.now, verbose_name='Fecha de Creación')
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name='Última Modificación')

    class Meta:
        verbose_name = 'Puerto'
        verbose_name_plural = 'Puertos'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def lugares_activos(self):
        """Retorna los lugares activos de este puerto"""
        return self.lugares.filter(activo=True)

class LugarPuerto(models.Model):
    """Modelo para lugares específicos dentro de cada puerto"""
    puerto = models.ForeignKey(Puerto, on_delete=models.CASCADE, related_name='lugares', verbose_name='Puerto')
    nombre = models.CharField(max_length=100, verbose_name='Nombre del Lugar')
    codigo = models.CharField(max_length=20, verbose_name='Código')
    tipo_lugar = models.CharField(max_length=50, choices=[
        ('muelle', 'Muelle'),
        ('oficinas', 'Oficinas'),
        ('parqueo', 'Parqueo'),
        ('almacen', 'Almacén'),
        ('contenedores', 'Zona de Contenedores'),
        ('aduana', 'Aduana'),
        ('servicios', 'Servicios'),
        ('otro', 'Otro')
    ], default='muelle', verbose_name='Tipo de Lugar')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    capacidad_maxima = models.PositiveIntegerField(null=True, blank=True, verbose_name='Capacidad Máxima')
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    fecha_creacion = models.DateTimeField(default=timezone.now, verbose_name='Fecha de Creación')
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name='Última Modificación')

    class Meta:
        verbose_name = 'Lugar del Puerto'
        verbose_name_plural = 'Lugares del Puerto'
        ordering = ['puerto__nombre', 'nombre']
        unique_together = [['puerto', 'codigo']]

    def __str__(self):
        return f"{self.puerto.nombre} - {self.nombre}"

    def get_tipo_display_icon(self):
        """Retorna icono según el tipo de lugar"""
        icons = {
            'muelle': '⚓',
            'oficinas': '🏢',
            'parqueo': '🚗',
            'almacen': '📦',
            'contenedores': '📦',
            'aduana': '🏛️',
            'servicios': '🔧',
            'otro': '📍'
        }
        return icons.get(self.tipo_lugar, '📍')

class MotivoAcceso(models.Model):
    """Modelo para los motivos de acceso disponibles"""
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Motivo')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    requiere_documentos_especiales = models.BooleanField(default=False, verbose_name='Requiere documentos especiales')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    servicios_relacionados = models.ManyToManyField(
        'evaluacion.Servicio',
        related_name='motivos_acceso',
        blank=True,
        verbose_name='Servicios Relacionados',
        help_text='Servicios que pueden usar este motivo de acceso'
    )

    class Meta:
        verbose_name = 'Motivo de Acceso'
        verbose_name_plural = 'Motivos de Acceso'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre

class Solicitud(models.Model):
    """Modelo principal para las solicitudes de acceso portuario"""
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('recibido', 'Recibida'),
        ('sin_asignar', 'Sin Asignar'),
        ('pendiente', 'Pendiente de Revisión'),
        ('en_revision', 'En Revisión'),
        ('documentos_faltantes', 'Documentos Faltantes'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('vencida', 'Vencida'),
        ('escalada', 'Escalada a Supervisor'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('normal', 'Normal'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
        ('vip', 'VIP Gubernamental'),
    ]
    
    # Información básica
    codigo = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name='Código de Solicitud'
    )
    numero_imo = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Número IMO',
        help_text='Número de identificación IMO de la embarcación (7 dígitos)'
    )
    naviera = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Naviera',
        help_text='Nombre de la empresa naviera propietaria de la embarcación'
    )
    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='solicitudes',
        verbose_name='Solicitante'
    )
    empresa = models.ForeignKey(
        'accounts.Empresa', 
        on_delete=models.CASCADE, 
        related_name='solicitudes',
        verbose_name='Empresa'
    )
    
    # Detalles del acceso
    puerto_destino = models.ForeignKey(
        Puerto,
        on_delete=models.CASCADE,
        verbose_name='Puerto de Destino'
    )
    lugar_destino = models.ForeignKey(
        LugarPuerto,
        on_delete=models.CASCADE,
        verbose_name='Lugar de Destino',
        help_text='Lugar específico dentro del puerto',
        null=True,
        blank=True
    )
    motivo_acceso = models.ForeignKey(
        MotivoAcceso,
        on_delete=models.CASCADE,
        verbose_name='Motivo del Acceso'
    )
    fecha_ingreso = models.DateField(verbose_name='Fecha de Ingreso')
    hora_ingreso = models.TimeField(verbose_name='Hora de Ingreso')
    fecha_salida = models.DateField(verbose_name='Fecha de Salida')
    hora_salida = models.TimeField(verbose_name='Hora de Salida')
    descripcion = models.TextField(verbose_name='Descripción Detallada')
    
    # Servicios solicitados
    servicios_solicitados = models.ManyToManyField(
        'evaluacion.Servicio',
        related_name='solicitudes',
        blank=True,
        verbose_name='Servicios Solicitados',
        help_text='Servicios específicos que la empresa requiere para esta solicitud'
    )
    
    # Estado y seguimiento
    estado = models.CharField(
        max_length=25, 
        choices=ESTADO_CHOICES, 
        default='borrador',
        verbose_name='Estado'
    )
    prioridad = models.CharField(
        max_length=15,
        choices=PRIORIDAD_CHOICES,
        default='normal',
        verbose_name='Prioridad'
    )
    
    # Campos de evaluación
    evaluador_asignado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitudes_asignadas',
        verbose_name='Evaluador Asignado'
    )
    fecha_evaluacion = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Evaluación')
    comentarios_evaluacion = models.TextField(blank=True, verbose_name='Comentarios de Evaluación')
    motivo_rechazo = models.TextField(blank=True, verbose_name='Motivo de Rechazo')
    
    # Tiempos límite
    vence_el = models.DateTimeField(null=True, blank=True, verbose_name='Vence el')
    tiempo_limite_horas = models.PositiveIntegerField(default=24, verbose_name='Tiempo límite (horas)')
    
    # Metadatos
    creada_el = models.DateTimeField(auto_now_add=True, verbose_name='Creada el')
    actualizada_el = models.DateTimeField(auto_now=True, verbose_name='Actualizada el')
    enviada_el = models.DateTimeField(null=True, blank=True, verbose_name='Enviada el')
    
    class Meta:
        verbose_name = 'Solicitud'
        verbose_name_plural = 'Solicitudes'
        ordering = ['-creada_el']
        indexes = [
            models.Index(fields=['estado', '-creada_el']),
            models.Index(fields=['evaluador_asignado', 'estado']),
            models.Index(fields=['vence_el']),
        ]

    def clean(self):
        """Validaciones de reglas de negocio"""
        from django.core.exceptions import ValidationError

        # Validar que no haya múltiples solicitudes activas para el mismo buque (número IMO)
        if self.numero_imo:
            estados_activos = ['recibido', 'sin_asignar', 'pendiente', 'en_revision', 'documentos_faltantes', 'aprobada']

            # Buscar solicitudes activas con el mismo número IMO
            query = Solicitud.objects.filter(
                numero_imo=self.numero_imo,
                estado__in=estados_activos
            )

            # Excluir la solicitud actual si ya existe (edición)
            if self.pk:
                query = query.exclude(pk=self.pk)

            if query.exists():
                solicitud_existente = query.first()
                raise ValidationError({
                    'numero_imo': f'Ya existe una solicitud activa ({solicitud_existente.codigo}) '
                                  f'para el buque con IMO {self.numero_imo}. '
                                  f'Estado: {solicitud_existente.get_estado_display()}'
                })

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self.generar_codigo()
        if self.estado == 'pendiente' and not self.enviada_el:
            self.enviada_el = timezone.now()
            self.calcular_vencimiento()
        super().save(*args, **kwargs)

    def generar_codigo(self):
        """Genera un código único para la solicitud"""
        from django.core.exceptions import ValidationError
        año = timezone.now().year
        base_codigo = f"SOL-{año}-"
        
        # Obtener el último número usado para este año
        ultima_solicitud = Solicitud.objects.filter(
            codigo__startswith=base_codigo
        ).order_by('-codigo').first()
        
        if ultima_solicitud:
            # Extraer el número de la última solicitud y sumar 1
            try:
                ultimo_numero = int(ultima_solicitud.codigo.split('-')[-1])
                nuevo_numero = ultimo_numero + 1
            except (ValueError, IndexError):
                # Si hay algún error al parsear, usar el conteo como fallback
                count = Solicitud.objects.filter(creada_el__year=año).count() + 1
                nuevo_numero = count
        else:
            # Primera solicitud del año
            nuevo_numero = 1
        
        # Buscar si ya existe este código y encontrar uno disponible
        while True:
            codigo_propuesto = f"{base_codigo}{nuevo_numero:03d}"
            if not Solicitud.objects.filter(codigo=codigo_propuesto).exists():
                return codigo_propuesto
            nuevo_numero += 1
    
    def calcular_vencimiento(self):
        """Calcula cuándo vence la solicitud basado en la prioridad"""
        if self.prioridad == 'vip':
            self.tiempo_limite_horas = 1
        elif self.prioridad == 'critica':
            self.tiempo_limite_horas = 2
        elif self.prioridad == 'alta':
            self.tiempo_limite_horas = 8
        else:  # normal (por defecto)
            self.tiempo_limite_horas = 24

        if self.enviada_el:
            self.vence_el = self.enviada_el + timedelta(hours=self.tiempo_limite_horas)
    
    def tiempo_restante(self):
        """Retorna el tiempo restante para el vencimiento"""
        if not self.vence_el:
            return None
        ahora = timezone.now()
        if ahora > self.vence_el:
            return timedelta(0)  # Ya venció
        return self.vence_el - ahora
    
    def tiempo_restante_formateado(self):
        """Retorna el tiempo restante formateado para mostrar"""
        tiempo = self.tiempo_restante()
        if not tiempo:
            return {'texto': 'N/A', 'color': '#95a5a6'}
        
        if self.esta_vencida():
            return {'texto': '⏰ Vencida', 'color': '#e74c3c'}
        
        total_seconds = int(tiempo.total_seconds())
        
        if tiempo.days > 0:
            return {'texto': f'{tiempo.days}d', 'color': '#27ae60'}
        elif total_seconds >= 3600:  # Más de 1 hora
            horas = total_seconds // 3600
            return {'texto': f'{horas}h', 'color': '#f39c12'}
        else:  # Menos de 1 hora
            minutos = total_seconds // 60
            return {'texto': f'{minutos}m', 'color': '#e74c3c'}
    
    def esta_vencida(self):
        """Verifica si la solicitud está vencida"""
        if not self.vence_el:
            return False
        return timezone.now() > self.vence_el
    
    def dias_transcurridos(self):
        """Retorna los días transcurridos desde la creación"""
        return (timezone.now() - self.creada_el).days
    
    def puede_ser_editada(self):
        """Verifica si la solicitud puede ser editada"""
        return self.estado in ['borrador', 'recibido', 'documentos_faltantes']
    
    def requiere_atencion_urgente(self):
        """Verifica si requiere atención urgente"""
        if self.esta_vencida():
            return True
        tiempo_restante = self.tiempo_restante()
        if tiempo_restante and tiempo_restante.total_seconds() < 3600:  # Menos de 1 hora
            return True
        return self.prioridad in ['critica', 'vip']
    
    @property
    def estado_con_color(self):
        """Retorna el estado de la solicitud con información de color"""
        estado_map = {
            'borrador': {'color': 'gray', 'bg_color': '#95a5a6', 'texto': 'Borrador', 'icono': '📝'},
            'recibido': {'color': 'yellow', 'bg_color': '#f1c40f', 'texto': 'Recibida', 'icono': '📨', 'text_color': '#000000'},
            'sin_asignar': {'color': 'secondary', 'bg_color': '#6c757d', 'texto': 'Sin Asignar', 'icono': '📋'},
            'pendiente': {'color': 'orange', 'bg_color': '#f39c12', 'texto': 'Pendiente', 'icono': '⏳'},
            'en_revision': {'color': 'blue', 'bg_color': '#3498db', 'texto': 'En Revisión', 'icono': '👀'},
            'documentos_faltantes': {'color': 'info', 'bg_color': '#17a2b8', 'texto': 'Docs. Faltantes', 'icono': '📄', 'text_color': '#ffffff'},
            'aprobada': {'color': 'green', 'bg_color': '#27ae60', 'texto': 'Aprobada', 'icono': '✅'},
            'rechazada': {'color': 'red', 'bg_color': '#e74c3c', 'texto': 'Rechazada', 'icono': '❌'},
            'vencida': {'color': 'dark-red', 'bg_color': '#c0392b', 'texto': 'Vencida', 'icono': '⏰'},
            'escalada': {'color': 'purple', 'bg_color': '#9b59b6', 'texto': 'Escalada', 'icono': '🚨'},
        }
        
        estado_info = estado_map.get(self.estado, {
            'color': 'secondary', 
            'bg_color': '#6c757d', 
            'texto': self.get_estado_display(), 
            'icono': 'ℹ️'
        })
        
        # Modificar color si está vencida independientemente del estado
        # (excepto para documentos_faltantes que mantiene su color azul para diferenciarlo de rechazada)
        if self.esta_vencida() and self.estado not in ['aprobada', 'rechazada', 'documentos_faltantes']:
            estado_info.update({
                'color': 'danger',
                'bg_color': '#dc3545',
                'texto': f"{estado_info['texto']} (Vencida)",
                'icono': '⚠️'
            })
        
        return estado_info

    # ===== MAPEO DE ESTADOS POR ROL =====

    # Estados simplificados para el solicitante
    ESTADOS_SOLICITANTE = {
        'borrador': 'borrador',
        'recibido': 'recibida',
        'sin_asignar': 'recibida',
        'pendiente': 'recibida',
        'en_revision': 'recibida',
        'documentos_faltantes': 'documentos_faltantes',
        'escalada': 'recibida',
        'aprobada': 'aprobada',
        'rechazada': 'rechazada',
        'vencida': 'rechazada',
    }

    # Configuración visual de estados para solicitante
    ESTADOS_SOLICITANTE_CONFIG = {
        'borrador': {'color': 'gray', 'bg_color': '#95a5a6', 'texto': 'Borrador', 'icono': '📝', 'text_color': 'white'},
        'recibida': {'color': 'yellow', 'bg_color': '#f1c40f', 'texto': 'Recibida', 'icono': '📨', 'text_color': '#000000'},
        'documentos_faltantes': {'color': 'orange', 'bg_color': '#e67e22', 'texto': 'Docs. Pendientes', 'icono': '📄', 'text_color': 'white'},
        'aprobada': {'color': 'green', 'bg_color': '#27ae60', 'texto': 'Aprobada', 'icono': '✅', 'text_color': 'white'},
        'rechazada': {'color': 'red', 'bg_color': '#e74c3c', 'texto': 'Rechazada', 'icono': '❌', 'text_color': 'white'},
    }

    def get_estado_para_rol(self, rol):
        """Retorna el estado visible según el rol del usuario"""
        if rol == 'solicitante':
            return self.ESTADOS_SOLICITANTE.get(self.estado, self.estado)
        else:
            # Evaluadores, supervisores, admin_tic, etc. ven el estado real
            return self.estado

    def get_estado_display_para_rol(self, rol):
        """Retorna el texto del estado según el rol"""
        if rol == 'solicitante':
            estado_mapeado = self.ESTADOS_SOLICITANTE.get(self.estado, self.estado)
            config = self.ESTADOS_SOLICITANTE_CONFIG.get(estado_mapeado)
            if config:
                return config['texto']
        return self.get_estado_display()

    def get_estado_con_color_para_rol(self, rol):
        """Retorna el estado con información de color según el rol"""
        if rol == 'solicitante':
            estado_mapeado = self.ESTADOS_SOLICITANTE.get(self.estado, self.estado)
            config = self.ESTADOS_SOLICITANTE_CONFIG.get(estado_mapeado)
            if config:
                return config.copy()
        # Para otros roles, usar el método normal
        return self.estado_con_color

    def __str__(self):
        return f"{self.codigo} - {self.empresa.nombre} - {self.estado.title()}"

class Vehiculo(models.Model):
    """Modelo para los vehículos asociados a una solicitud"""
    solicitud = models.ForeignKey(
        Solicitud,
        on_delete=models.CASCADE,
        related_name='vehiculos',
        verbose_name='Solicitud'
    )
    placa = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]{1,3}-\d{4}$',
                message='Formato inválido. Use ABC-1234'
            )
        ],
        verbose_name='Placa'
    )
    tipo_vehiculo = models.CharField(
        max_length=50,
        choices=[
            ('automovil', 'Automóvil'),
            ('camion', 'Camión'),
            ('camioneta', 'Camioneta'),
            ('motocicleta', 'Motocicleta'),
            ('equipo_especializado', 'Equipo Especializado'),
        ],
        verbose_name='Tipo de Vehículo'
    )
    conductor_nombre = models.CharField(max_length=200, verbose_name='Nombre del Conductor')
    conductor_licencia = models.CharField(max_length=20, blank=True, verbose_name='Licencia de Conducir')
    
    class Meta:
        verbose_name = 'Vehículo'
        verbose_name_plural = 'Vehículos'
        unique_together = ['solicitud', 'placa']
    
    def __str__(self):
        return f"{self.placa} - {self.conductor_nombre}"

class DocumentoAdjunto(models.Model):
    """Modelo para los documentos adjuntos a una solicitud"""
    TIPO_DOCUMENTO_CHOICES = [
        ('cedula_representante', 'Cédula del Representante'),
        ('rnc_empresa', 'RNC de la Empresa'),
        ('registro_vehiculo', 'Registro de Vehículo'),
        ('licencia_conducir', 'Licencia de Conducir'),
        ('otros', 'Otros Documentos'),
    ]
    
    solicitud = models.ForeignKey(
        Solicitud,
        on_delete=models.CASCADE,
        related_name='documentos',
        verbose_name='Solicitud'
    )
    tipo_documento = models.CharField(
        max_length=25,
        choices=TIPO_DOCUMENTO_CHOICES,
        verbose_name='Tipo de Documento'
    )
    archivo = models.FileField(
        upload_to='solicitudes/documentos/%Y/%m/',
        verbose_name='Archivo'
    )
    nombre_original = models.CharField(max_length=255, verbose_name='Nombre Original')
    tamaño = models.PositiveIntegerField(verbose_name='Tamaño (bytes)')
    subido_el = models.DateTimeField(auto_now_add=True, verbose_name='Subido el')
    verificado = models.BooleanField(default=False, verbose_name='Verificado')
    
    class Meta:
        verbose_name = 'Documento Adjunto'
        verbose_name_plural = 'Documentos Adjuntos'
        ordering = ['-subido_el']
    
    def __str__(self):
        return f"{self.get_tipo_documento_display()} - {self.nombre_original}"


class SolicitudPersonal(models.Model):
    """
    Modelo para el personal asociado a una solicitud de acceso
    Permite agregar múltiples personas a una solicitud (similar a vehículos)
    """
    solicitud = models.ForeignKey(
        Solicitud,
        on_delete=models.CASCADE,
        related_name='personal_asignado',
        verbose_name='Solicitud'
    )
    personal = models.ForeignKey(
        'empresas.Personal',
        on_delete=models.CASCADE,
        verbose_name='Personal'
    )
    rol_operacion = models.CharField(
        max_length=100,
        blank=True,
        help_text='Rol específico en esta operación (ej: Conductor Principal, Operador de Grúa, etc.)',
        verbose_name='Rol en la Operación'
    )
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado el')

    class Meta:
        verbose_name = 'Personal de Solicitud'
        verbose_name_plural = 'Personal de Solicitudes'
        unique_together = ['solicitud', 'personal']
        ordering = ['created_at']

    def __str__(self):
        return f"{self.personal.nombre} - {self.solicitud.codigo}"


class DocumentoPersonal(models.Model):
    """Documentos específicos del personal"""
    TIPOS_DOCUMENTO = [
        ('cedula', 'Cédula de Identidad'),
        ('licencia_conducir', 'Licencia de Conducir'),
        ('certificado_medico', 'Certificado Médico'),
        ('certificado_antecedentes', 'Certificado de Antecedentes'),
        ('foto', 'Fotografía'),
    ]

    personal = models.ForeignKey('empresas.Personal', on_delete=models.CASCADE, related_name='documentos')
    tipo_documento = models.CharField(max_length=25, choices=TIPOS_DOCUMENTO, verbose_name='Tipo de Documento')
    archivo = models.FileField(upload_to='documentos/personal/', verbose_name='Archivo')
    numero_documento = models.CharField(max_length=50, blank=True, verbose_name='Número de Documento')
    fecha_emision = models.DateField(null=True, blank=True, verbose_name='Fecha de Emisión')
    fecha_vencimiento = models.DateField(null=True, blank=True, verbose_name='Fecha de Vencimiento')
    verificado = models.BooleanField(default=False, verbose_name='Verificado')
    verificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos_personales_verificados',
        verbose_name='Verificado por'
    )
    fecha_verificacion = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Verificación')
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    subido_el = models.DateTimeField(auto_now_add=True, verbose_name='Subido el')

    class Meta:
        verbose_name = 'Documento Personal'
        verbose_name_plural = 'Documentos Personales'
        unique_together = ['personal', 'tipo_documento']

    def __str__(self):
        return f"{self.personal.nombre} - {self.get_tipo_documento_display()}"

    @property
    def esta_vigente(self):
        """Verifica si el documento está vigente"""
        if self.fecha_vencimiento:
            from django.utils import timezone
            return self.fecha_vencimiento >= timezone.now().date()
        return True


class DocumentoVehiculo(models.Model):
    """Documentos específicos de vehículos"""
    TIPOS_DOCUMENTO = [
        ('registro', 'Registro de Vehículo'),
        ('seguro', 'Seguro Vehicular'),
        ('inspeccion_tecnica', 'Inspección Técnica'),
        ('permiso_circulacion', 'Permiso de Circulación'),
        ('certificado_gases', 'Certificado de Emisión de Gases'),
    ]

    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='documentos')
    tipo_documento = models.CharField(max_length=25, choices=TIPOS_DOCUMENTO, verbose_name='Tipo de Documento')
    archivo = models.FileField(upload_to='documentos/vehiculos/', verbose_name='Archivo')
    numero_documento = models.CharField(max_length=50, blank=True, verbose_name='Número de Documento')
    fecha_emision = models.DateField(null=True, blank=True, verbose_name='Fecha de Emisión')
    fecha_vencimiento = models.DateField(null=True, blank=True, verbose_name='Fecha de Vencimiento')
    verificado = models.BooleanField(default=False, verbose_name='Verificado')
    verificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos_vehiculos_verificados',
        verbose_name='Verificado por'
    )
    fecha_verificacion = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Verificación')
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    subido_el = models.DateTimeField(auto_now_add=True, verbose_name='Subido el')

    class Meta:
        verbose_name = 'Documento Vehículo'
        verbose_name_plural = 'Documentos Vehículos'
        unique_together = ['vehiculo', 'tipo_documento']

    def __str__(self):
        return f"{self.vehiculo.placa} - {self.get_tipo_documento_display()}"

    @property
    def esta_vigente(self):
        """Verifica si el documento está vigente"""
        if self.fecha_vencimiento:
            from django.utils import timezone
            return self.fecha_vencimiento >= timezone.now().date()
        return True


class DocumentoServicioSolicitud(models.Model):
    """
    Documentos que el solicitante adjunta para cumplir con los requisitos
    de los servicios seleccionados en su solicitud
    """

    solicitud = models.ForeignKey(
        Solicitud,
        on_delete=models.CASCADE,
        related_name='documentos_servicios',
        verbose_name='Solicitud'
    )
    documento_requerido = models.ForeignKey(
        'evaluacion.DocumentoRequeridoServicio',
        on_delete=models.CASCADE,
        related_name='documentos_subidos',
        verbose_name='Documento Requerido'
    )
    archivo = models.FileField(
        upload_to='solicitudes/documentos_servicios/%Y/%m/',
        verbose_name='Archivo'
    )
    nombre_original = models.CharField(
        max_length=255,
        verbose_name='Nombre Original del Archivo'
    )
    tamaño = models.PositiveIntegerField(
        verbose_name='Tamaño (bytes)'
    )
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones del Solicitante'
    )

    # Verificación por evaluador
    verificado = models.BooleanField(
        default=False,
        verbose_name='Verificado'
    )
    verificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos_servicios_verificados',
        verbose_name='Verificado por'
    )
    fecha_verificacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Verificación'
    )
    comentario_verificacion = models.TextField(
        blank=True,
        verbose_name='Comentario de Verificación'
    )

    # Metadatos
    subido_el = models.DateTimeField(auto_now_add=True, verbose_name='Subido el')
    actualizado_el = models.DateTimeField(auto_now=True, verbose_name='Actualizado el')

    class Meta:
        verbose_name = 'Documento de Servicio'
        verbose_name_plural = 'Documentos de Servicios'
        ordering = ['solicitud', 'documento_requerido__orden']
        unique_together = ['solicitud', 'documento_requerido']

    def __str__(self):
        return f"{self.solicitud.codigo} - {self.documento_requerido.nombre}"

    @property
    def servicio(self):
        """Retorna el servicio asociado al documento requerido"""
        return self.documento_requerido.servicio

    @property
    def es_obligatorio(self):
        """Indica si este documento es obligatorio"""
        return self.documento_requerido.obligatorio


class EventoSolicitud(models.Model):
    """
    Modelo para registrar todos los eventos que ocurren en el ciclo de vida de una solicitud.
    Permite trazabilidad completa con timeline visual.
    """

    TIPO_EVENTO_CHOICES = [
        # Eventos del ciclo de vida
        ('creacion', 'Solicitud Creada'),
        ('envio', 'Solicitud Enviada'),
        ('asignacion', 'Asignada a Evaluador'),
        ('inicio_revision', 'Revisión Iniciada'),
        ('documentos_faltantes', 'Documentos Faltantes'),
        ('documentos_completados', 'Documentos Completados'),
        ('aprobacion', 'Solicitud Aprobada'),
        ('rechazo', 'Solicitud Rechazada'),
        ('escalacion', 'Escalada a Supervisor'),

        # Cambios de estado
        ('cambio_estado', 'Cambio de Estado'),
        ('cambio_prioridad', 'Cambio de Prioridad'),
        ('reasignacion', 'Reasignada a Otro Evaluador'),

        # Comentarios y notas
        ('comentario', 'Comentario Agregado'),
        ('nota_interna', 'Nota Interna'),

        # Documentos
        ('documento_subido', 'Documento Subido'),
        ('documento_verificado', 'Documento Verificado'),
        ('documento_rechazado', 'Documento Rechazado'),

        # Otros
        ('vencimiento_proximo', 'Vencimiento Próximo'),
        ('vencida', 'Solicitud Vencida'),
        ('actualizacion', 'Información Actualizada'),
    ]

    # Relaciones
    solicitud = models.ForeignKey(
        Solicitud,
        on_delete=models.CASCADE,
        related_name='eventos',
        verbose_name='Solicitud'
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eventos_solicitudes',
        verbose_name='Usuario Responsable',
        help_text='Usuario que generó este evento (puede ser null para eventos automáticos)'
    )

    # Información del evento
    tipo_evento = models.CharField(
        max_length=30,
        choices=TIPO_EVENTO_CHOICES,
        verbose_name='Tipo de Evento'
    )

    titulo = models.CharField(
        max_length=200,
        verbose_name='Título del Evento',
        help_text='Descripción breve del evento'
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción Detallada',
        help_text='Información adicional sobre el evento'
    )

    # Datos adicionales (JSON para flexibilidad)
    metadata = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Metadata',
        help_text='Datos adicionales del evento en formato JSON (estado anterior, estado nuevo, etc.)'
    )

    # Visibilidad
    es_visible_solicitante = models.BooleanField(
        default=True,
        verbose_name='Visible para Solicitante',
        help_text='Si el solicitante puede ver este evento en su timeline'
    )

    es_interno = models.BooleanField(
        default=False,
        verbose_name='Evento Interno',
        help_text='Solo visible para personal de evaluación'
    )

    # Timestamps
    creado_el = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Creado el'
    )

    class Meta:
        verbose_name = 'Evento de Solicitud'
        verbose_name_plural = 'Eventos de Solicitudes'
        ordering = ['-creado_el']
        indexes = [
            models.Index(fields=['solicitud', '-creado_el']),
            models.Index(fields=['tipo_evento', '-creado_el']),
            models.Index(fields=['usuario', '-creado_el']),
        ]

    def __str__(self):
        return f"{self.solicitud.codigo} - {self.get_tipo_evento_display()} ({self.creado_el.strftime('%d/%m/%Y %H:%M')})"

    def get_icono(self):
        """Retorna el icono apropiado según el tipo de evento"""
        iconos = {
            'creacion': '📝',
            'envio': '📤',
            'asignacion': '👤',
            'inicio_revision': '🔍',
            'documentos_faltantes': '📄',
            'documentos_completados': '✅',
            'aprobacion': '✅',
            'rechazo': '❌',
            'escalacion': '⬆️',
            'cambio_estado': '🔄',
            'cambio_prioridad': '⚡',
            'reasignacion': '🔀',
            'comentario': '💬',
            'nota_interna': '📝',
            'documento_subido': '📎',
            'documento_verificado': '✔️',
            'documento_rechazado': '🚫',
            'vencimiento_proximo': '⚠️',
            'vencida': '⏰',
            'actualizacion': '🔄',
        }
        return iconos.get(self.tipo_evento, '📌')

    def get_color(self):
        """Retorna el color apropiado según el tipo de evento"""
        colores = {
            'creacion': '#3498db',
            'envio': '#3498db',
            'asignacion': '#9b59b6',
            'inicio_revision': '#f39c12',
            'documentos_faltantes': '#e67e22',
            'documentos_completados': '#27ae60',
            'aprobacion': '#27ae60',
            'rechazo': '#e74c3c',
            'escalacion': '#e74c3c',
            'cambio_estado': '#95a5a6',
            'cambio_prioridad': '#f39c12',
            'reasignacion': '#9b59b6',
            'comentario': '#3498db',
            'nota_interna': '#95a5a6',
            'documento_subido': '#3498db',
            'documento_verificado': '#27ae60',
            'documento_rechazado': '#e74c3c',
            'vencimiento_proximo': '#f39c12',
            'vencida': '#e74c3c',
            'actualizacion': '#95a5a6',
        }
        return colores.get(self.tipo_evento, '#95a5a6')

    def get_usuario_nombre(self):
        """Retorna el nombre del usuario o 'Sistema' si es automático"""
        if self.usuario:
            return self.usuario.get_full_name()
        return 'Sistema Automático'
