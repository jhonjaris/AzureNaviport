from django.db import models
from django.utils import timezone
from django.conf import settings
from datetime import timedelta

class Escalamiento(models.Model):
    """Modelo para casos escalados al supervisor"""
    TIPO_ESCALAMIENTO_CHOICES = [
        ('vip_gubernamental', 'VIP Gubernamental'),
        ('caso_complejo', 'Caso Complejo'),
        ('documentacion_especial', 'Documentación Especial'),
        ('solicitud_vencida', 'Solicitud Vencida'),
        ('discrepancia_grave', 'Discrepancia Grave'),
        ('revision_manual', 'Revisión Manual Requerida'),
        ('otros', 'Otros'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('critica', 'Crítica'),
        ('alta', 'Alta'),
        ('media', 'Media'),
        ('baja', 'Baja'),
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_revision', 'En Revisión'),
        ('resuelto', 'Resuelto'),
        ('reasignado', 'Reasignado'),
        ('cerrado', 'Cerrado'),
    ]
    
    # Información básica
    codigo = models.CharField(
        max_length=20, 
        unique=True, 
        editable=False,
        verbose_name='Código de Escalamiento'
    )
    solicitud = models.ForeignKey(
        'solicitudes.Solicitud', 
        on_delete=models.CASCADE, 
        related_name='escalamientos',
        verbose_name='Solicitud'
    )
    
    # Tipo y prioridad
    tipo_escalamiento = models.CharField(
        max_length=25,
        choices=TIPO_ESCALAMIENTO_CHOICES,
        verbose_name='Tipo de Escalamiento'
    )
    prioridad = models.CharField(
        max_length=10, 
        choices=PRIORIDAD_CHOICES,
        default='media',
        verbose_name='Prioridad'
    )
    
    # Asignación
    escalado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='escalamientos_creados',
        verbose_name='Escalado por'
    )
    asignado_a = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='escalamientos_asignados',
        verbose_name='Asignado a'
    )
    
    # Descripción y resolución
    motivo = models.TextField(verbose_name='Motivo del Escalamiento')
    descripcion_detallada = models.TextField(verbose_name='Descripción Detallada')
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name='Estado'
    )
    
    # Resolución
    resuelto_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='escalamientos_resueltos',
        verbose_name='Resuelto por'
    )
    resolucion = models.TextField(blank=True, verbose_name='Resolución')
    decision_tomada = models.CharField(
        max_length=50,
        choices=[
            ('aprobar', 'Aprobar Solicitud'),
            ('rechazar', 'Rechazar Solicitud'),
            ('solicitar_documentos', 'Solicitar Documentos Adicionales'),
            ('reasignar', 'Reasignar a Otro Evaluador'),
            ('otros', 'Otros'),
        ],
        blank=True,
        verbose_name='Decisión Tomada'
    )
    
    # Tiempos
    tiempo_limite = models.DateTimeField(null=True, blank=True, verbose_name='Tiempo Límite')
    fecha_resolucion = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Resolución')
    
    # Metadatos
    creado_el = models.DateTimeField(auto_now_add=True, verbose_name='Creado el')
    actualizado_el = models.DateTimeField(auto_now=True, verbose_name='Actualizado el')
    
    class Meta:
        verbose_name = 'Escalamiento'
        verbose_name_plural = 'Escalamientos'
        ordering = ['-creado_el']
        indexes = [
            models.Index(fields=['estado', '-creado_el']),
            models.Index(fields=['asignado_a', 'estado']),
            models.Index(fields=['prioridad', '-creado_el']),
        ]

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self.generar_codigo()
        
        # Calcular tiempo límite basado en prioridad
        if not self.tiempo_limite and self.estado == 'pendiente':
            self.calcular_tiempo_limite()
            
        super().save(*args, **kwargs)

    def generar_codigo(self):
        """Genera un código único para el escalamiento"""
        año = timezone.now().year
        count = Escalamiento.objects.filter(creado_el__year=año).count() + 1
        return f"ESC-{año}-{count:03d}"
    
    def calcular_tiempo_limite(self):
        """Calcula el tiempo límite basado en la prioridad"""
        if self.prioridad == 'critica':
            horas = 1
        elif self.prioridad == 'alta':
            horas = 4
        elif self.prioridad == 'media':
            horas = 12
        else:  # baja
            horas = 24
            
        self.tiempo_limite = timezone.now() + timedelta(hours=horas)
    
    def tiempo_restante(self):
        """Retorna el tiempo restante para resolución"""
        if not self.tiempo_limite or self.estado in ['resuelto', 'cerrado']:
            return None
        
        ahora = timezone.now()
        if ahora > self.tiempo_limite:
            return timedelta(0)  # Ya venció
        return self.tiempo_limite - ahora
    
    def esta_vencido(self):
        """Verifica si el escalamiento está vencido"""
        if not self.tiempo_limite or self.estado in ['resuelto', 'cerrado']:
            return False
        return timezone.now() > self.tiempo_limite
    
    def requiere_atencion_urgente(self):
        """Verifica si requiere atención urgente"""
        if self.esta_vencido():
            return True
        tiempo_restante = self.tiempo_restante()
        if tiempo_restante and tiempo_restante.total_seconds() < 3600:  # Menos de 1 hora
            return True
        return self.prioridad == 'critica'
    
    def resolver(self, usuario, decision, resolucion):
        """Resuelve el escalamiento"""
        self.estado = 'resuelto'
        self.resuelto_por = usuario
        self.decision_tomada = decision
        self.resolucion = resolucion
        self.fecha_resolucion = timezone.now()
        self.save()
        
        # Actualizar solicitud según la decisión
        if decision == 'aprobar':
            self.solicitud.estado = 'aprobada'
            self.solicitud.evaluador_asignado = usuario
            self.solicitud.fecha_evaluacion = timezone.now()
            self.solicitud.comentarios_evaluacion = f"Aprobada por escalamiento: {resolucion}"
        elif decision == 'rechazar':
            self.solicitud.estado = 'rechazada'
            self.solicitud.evaluador_asignado = usuario
            self.solicitud.fecha_evaluacion = timezone.now()
            self.solicitud.motivo_rechazo = resolucion
        elif decision == 'solicitar_documentos':
            self.solicitud.estado = 'documentos_faltantes'
            self.solicitud.comentarios_evaluacion = f"Documentos faltantes: {resolucion}"
        
        self.solicitud.save()

    def __str__(self):
        return f"{self.codigo} - {self.get_tipo_escalamiento_display()} - {self.get_prioridad_display()}"

class AlertaSistema(models.Model):
    """Modelo para alertas del sistema dirigidas al supervisor"""
    TIPO_ALERTA_CHOICES = [
        ('solicitud_vip_venciendo', 'Solicitud VIP por Vencer'),
        ('evaluadores_sobrecargados', 'Evaluadores Sobrecargados'),
        ('discrepancias_acumuladas', 'Discrepancias Acumuladas'),
        ('sistema_actualizado', 'Sistema Actualizado'),
        ('error_sistema', 'Error del Sistema'),
        ('rendimiento_bajo', 'Rendimiento Bajo'),
        ('otros', 'Otros'),
    ]
    
    NIVEL_CHOICES = [
        ('info', 'Información'),
        ('advertencia', 'Advertencia'),
        ('critico', 'Crítico'),
    ]
    
    # Información básica
    titulo = models.CharField(max_length=200, verbose_name='Título')
    mensaje = models.TextField(verbose_name='Mensaje')
    tipo_alerta = models.CharField(
        max_length=30,
        choices=TIPO_ALERTA_CHOICES,
        verbose_name='Tipo de Alerta'
    )
    nivel = models.CharField(
        max_length=15,
        choices=NIVEL_CHOICES,
        default='info',
        verbose_name='Nivel'
    )
    
    # Control
    activa = models.BooleanField(default=True, verbose_name='Activa')
    leida = models.BooleanField(default=False, verbose_name='Leída')
    dirigida_a = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alertas_recibidas',
        verbose_name='Dirigida a'
    )
    
    # Datos adicionales
    datos_adicionales = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Datos Adicionales'
    )
    
    # Metadatos
    creada_el = models.DateTimeField(auto_now_add=True, verbose_name='Creada el')
    leida_el = models.DateTimeField(null=True, blank=True, verbose_name='Leída el')
    
    class Meta:
        verbose_name = 'Alerta del Sistema'
        verbose_name_plural = 'Alertas del Sistema'
        ordering = ['-creada_el']
        indexes = [
            models.Index(fields=['dirigida_a', 'activa', '-creada_el']),
            models.Index(fields=['nivel', 'activa']),
        ]
    
    def marcar_como_leida(self, usuario=None):
        """Marca la alerta como leída"""
        self.leida = True
        self.leida_el = timezone.now()
        self.save()
    
    @classmethod
    def crear_alerta_vip_venciendo(cls, solicitud):
        """Crea una alerta para solicitudes VIP que están por vencer"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        supervisores = User.objects.filter(role='supervisor', activo=True)
        for supervisor in supervisores:
            cls.objects.create(
                titulo="Solicitud VIP vence en 15 min",
                mensaje=f"La solicitud {solicitud.codigo} de {solicitud.empresa.nombre} vence en 15 minutos.",
                tipo_alerta='solicitud_vip_venciendo',
                nivel='critico',
                dirigida_a=supervisor,
                datos_adicionales={
                    'solicitud_id': solicitud.id,
                    'codigo': solicitud.codigo,
                    'empresa': solicitud.empresa.nombre
                }
            )
    
    @classmethod
    def crear_alerta_evaluadores_sobrecarga(cls, count_sobrecargados):
        """Crea una alerta por evaluadores sobrecargados"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        supervisores = User.objects.filter(role='supervisor', activo=True)
        for supervisor in supervisores:
            cls.objects.create(
                titulo=f"{count_sobrecargados} evaluadores sobrecargados",
                mensaje=f"Hay {count_sobrecargados} evaluadores con carga de trabajo excesiva.",
                tipo_alerta='evaluadores_sobrecargados',
                nivel='advertencia',
                dirigida_a=supervisor,
                datos_adicionales={
                    'count': count_sobrecargados
                }
            )

    def __str__(self):
        return f"{self.titulo} - {self.get_nivel_display()}"
