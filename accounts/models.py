from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone

class User(AbstractUser):
    """Modelo de usuario personalizado para NaviPort RD"""
    ROLE_CHOICES = [
        ('solicitante', 'Solicitante'),
        ('evaluador', 'Evaluador Portuario'),
        ('supervisor', 'Supervisor'),
        ('admin_tic', 'Administrador TIC'),
        ('oficial_acceso', 'Oficial de Acceso Físico'),
        ('direccion', 'Dirección Logística'),
    ]
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='solicitante',
        verbose_name='Rol'
    )
    cedula_rnc = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^(\d{3}-\d{7}-\d{1}|\d{3}-\d{5}-\d{1})$',
                message='Formato inválido. Use XXX-XXXXXXX-X para cédula o XXX-XXXXX-X para RNC'
            )
        ],
        verbose_name='Cédula/RNC'
    )
    telefono = models.CharField(
        max_length=15,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Número de teléfono inválido'
            )
        ],
        verbose_name='Teléfono'
    )
    empresa = models.ForeignKey(
        'Empresa',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios',
        verbose_name='Empresa'
    )
    es_admin_empresa = models.BooleanField(default=False, verbose_name='Admin de Empresa')
    puede_crear_usuarios = models.BooleanField(default=False, verbose_name='Puede Crear Usuarios')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado el')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado el')
    failed_login_attempts = models.PositiveIntegerField(default=0, verbose_name='Intentos fallidos')
    is_locked = models.BooleanField(default=False, verbose_name='Bloqueado')
    locked_until = models.DateTimeField(null=True, blank=True, verbose_name='Bloqueado hasta')
    last_login_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='Última IP')

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    def get_display_name(self):
        return self.get_full_name() or self.username

    def get_role_display_with_admin(self):
        """Retorna el rol con sufijo (Administrador) si es admin de empresa"""
        role_display = self.get_role_display()
        if self.es_admin_empresa and self.role == 'solicitante':
            return f"{role_display} (Administrador)"
        return role_display

    def is_solicitante(self):
        return self.role == 'solicitante'
    def is_evaluador(self):
        return self.role == 'evaluador'
    def is_supervisor(self):
        return self.role == 'supervisor'
    def is_oficial_acceso(self):
        return self.role == 'oficial_acceso'
    def is_admin_tic(self):
        return self.role == 'admin_tic'
    def is_direccion(self):
        return self.role == 'direccion'
    def puede_evaluar(self):
        return self.role in ['evaluador', 'supervisor', 'admin_tic']
    def puede_supervisar(self):
        return self.role in ['supervisor', 'admin_tic']
    
    def puede_gestionar_usuarios(self):
        """Determina si el usuario puede gestionar usuarios de empresas"""
        return self.role in ['evaluador', 'supervisor', 'admin_tic'] or (self.is_solicitante() and self.es_admin_empresa)
    
    def puede_crear_usuarios_empresa(self):
        """Determina si puede crear usuarios para su empresa"""
        return self.puede_crear_usuarios and self.es_admin_empresa and self.empresa

class Empresa(models.Model):
    """Modelo para empresas registradas en el sistema"""
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
    nombre = models.CharField(max_length=200, verbose_name='Nombre')
    telefono = models.CharField(
        max_length=15,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Número de teléfono inválido'
            )
        ],
        verbose_name='Teléfono'
    )
    email = models.EmailField(verbose_name='Email')
    representante_legal = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='empresas_representadas',
        verbose_name='Representante Legal'
    )
    activa = models.BooleanField(default=True, verbose_name='Activa')
    verificada = models.BooleanField(default=False, verbose_name='Verificada')
    certificado_rnc = models.FileField(
        upload_to='empresas/certificados/',
        blank=True,
        verbose_name='Certificado RNC'
    )
    numero_licencia = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Número de Licencia'
    )
    fecha_expedicion_licencia = models.DateField(
        blank=True,
        null=True,
        verbose_name='Fecha de Expedición'
    )
    fecha_expiracion_licencia = models.DateField(
        blank=True,
        null=True,
        verbose_name='Fecha de Expiración'
    )
    fecha_expiracion_contrato = models.DateField(
        blank=True,
        null=True,
        verbose_name='Expiración Contrato'
    )
    
    # Servicios y tipo de licencia
    tipo_licencia = models.ForeignKey(
        'evaluacion.TipoLicencia',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='empresas_asignadas',
        verbose_name='Tipo de Licencia',
        help_text='Tipo de licencia que determina los servicios base autorizados'
    )
    servicios_autorizados = models.ManyToManyField(
        'evaluacion.Servicio',
        related_name='empresas_autorizadas',
        blank=True,
        verbose_name='Servicios Autorizados',
        help_text='Servicios específicos que la empresa está autorizada a ofrecer'
    )

    # Permisos excepcionales
    puede_solicitud_excepcional = models.BooleanField(
        default=False,
        verbose_name='Permite Solicitud Excepcional',
        help_text='Si está habilitado, la empresa puede realizar solicitudes excepcionales aprobadas por supervisión'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Registrada el')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizada el')

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nombre} ({self.rnc})"
    
    @property
    def licencia_vigente(self):
        """Verifica si la licencia está vigente"""
        if not self.fecha_expiracion_licencia:
            return None
        return self.fecha_expiracion_licencia >= timezone.now().date()
    
    @property
    def dias_para_vencimiento(self):
        """Calcula días hasta vencimiento de licencia"""
        if not self.fecha_expiracion_licencia:
            return None
        delta = self.fecha_expiracion_licencia - timezone.now().date()
        return delta.days
    
    @property
    def dias_vencimiento_absoluto(self):
        """Calcula días de vencimiento en valor absoluto"""
        if not self.fecha_expiracion_licencia:
            return None
        delta = self.fecha_expiracion_licencia - timezone.now().date()
        return abs(delta.days)
    
    @property
    def estado_licencia(self):
        """Retorna el estado de la licencia con código de color"""
        if not self.numero_licencia or not self.fecha_expiracion_licencia:
            return {'status': 'sin_licencia', 'color': 'gray', 'texto': 'Sin Licencia'}
        
        dias_restantes = self.dias_para_vencimiento
        if dias_restantes < 0:
            return {'status': 'vencida', 'color': 'red', 'texto': 'Vencida'}
        elif dias_restantes <= 7:
            return {'status': 'critica', 'color': 'red', 'texto': f'Vence en {dias_restantes} día{"s" if dias_restantes != 1 else ""}'}
        elif dias_restantes <= 30:
            return {'status': 'proxima', 'color': 'orange', 'texto': f'Vence en {dias_restantes} días'}
        else:
            return {'status': 'vigente', 'color': 'green', 'texto': 'Vigente'}
    
    def servicios_por_tipo_licencia(self):
        """Retorna los servicios que vienen del tipo de licencia"""
        if self.tipo_licencia:
            return self.tipo_licencia.servicios_incluidos.all()
        return []
    
    def servicios_adicionales(self):
        """Retorna servicios autorizados que NO vienen del tipo de licencia"""
        servicios_tipo = set(self.servicios_por_tipo_licencia())
        servicios_autorizados = set(self.servicios_autorizados.all())
        return list(servicios_autorizados - servicios_tipo)
    
    def todos_los_servicios(self):
        """Retorna TODOS los servicios autorizados (tipo + adicionales)"""
        servicios_tipo = set(self.servicios_por_tipo_licencia())
        servicios_autorizados = set(self.servicios_autorizados.all())
        return list(servicios_tipo | servicios_autorizados)
    
    def cantidad_servicios(self):
        """Retorna la cantidad total de servicios autorizados"""
        return len(self.todos_los_servicios())
    
    def aplicar_servicios_tipo_licencia(self):
        """Aplica automáticamente los servicios del tipo de licencia seleccionado"""
        if self.tipo_licencia:
            servicios_tipo = self.tipo_licencia.servicios_incluidos.all()
            for servicio in servicios_tipo:
                self.servicios_autorizados.add(servicio)


class NotificacionEmpresa(models.Model):
    """Modelo para manejar notificaciones de empresas"""
    
    TIPO_CHOICES = [
        ('critico', 'Crítico'),
        ('advertencia', 'Advertencia'), 
        ('informativo', 'Informativo'),
        ('vencido', 'Vencido')
    ]
    
    CATEGORIA_CHOICES = [
        ('vuce', 'Expiración VUCE'),
        ('contrato', 'Expiración Contrato'),
        ('general', 'General')
    ]
    
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='notificaciones',
        verbose_name='Empresa'
    )
    
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notificaciones_recibidas',
        verbose_name='Usuario'
    )
    
    tipo = models.CharField(
        max_length=15,
        choices=TIPO_CHOICES,
        verbose_name='Tipo de Notificación'
    )
    
    categoria = models.CharField(
        max_length=15,
        choices=CATEGORIA_CHOICES,
        default='general',
        verbose_name='Categoría'
    )
    
    titulo = models.CharField(
        max_length=200,
        verbose_name='Título'
    )
    
    mensaje = models.TextField(
        verbose_name='Mensaje'
    )
    
    enlace_accion = models.URLField(
        blank=True,
        null=True,
        verbose_name='Enlace de Acción'
    )
    
    texto_enlace = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Texto del Enlace'
    )
    
    fecha_expiracion = models.DateField(
        blank=True,
        null=True,
        verbose_name='Fecha de Expiración Relacionada'
    )
    
    mostrar_desde = models.DateTimeField(
        default=timezone.now,
        verbose_name='Mostrar Desde'
    )
    
    mostrar_hasta = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Mostrar Hasta'
    )
    
    activa = models.BooleanField(
        default=True,
        verbose_name='Activa'
    )
    
    cerrada_por_usuario = models.BooleanField(
        default=False,
        verbose_name='Cerrada por Usuario'
    )
    
    fecha_cerrada = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de Cierre'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creada el')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizada el')
    
    class Meta:
        verbose_name = 'Notificación de Empresa'
        verbose_name_plural = 'Notificaciones de Empresas'
        ordering = ['-created_at', 'tipo']
        indexes = [
            models.Index(fields=['usuario', 'activa', 'cerrada_por_usuario']),
            models.Index(fields=['empresa', 'tipo']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_display()}: {self.titulo} - {self.empresa.nombre}"
    
    @property 
    def color_css(self):
        """Retorna la clase CSS según el tipo"""
        colores = {
            'critico': 'danger',
            'advertencia': 'warning', 
            'informativo': 'info',
            'vencido': 'dark'
        }
        return colores.get(self.tipo, 'secondary')
    
    @property
    def icono(self):
        """Retorna el ícono según el tipo"""
        iconos = {
            'critico': '🔴',
            'advertencia': '🟠',
            'informativo': '🟡', 
            'vencido': '⚫'
        }
        return iconos.get(self.tipo, 'ℹ️')
    
    @property
    def debe_mostrarse(self):
        """Verifica si la notificación debe mostrarse"""
        if not self.activa or self.cerrada_por_usuario:
            return False
            
        ahora = timezone.now()
        
        # Verificar rango de fechas
        if self.mostrar_hasta and ahora > self.mostrar_hasta:
            return False
            
        if self.mostrar_desde and ahora < self.mostrar_desde:
            return False
            
        return True
    
    def cerrar(self):
        """Marca la notificación como cerrada por el usuario"""
        self.cerrada_por_usuario = True
        self.fecha_cerrada = timezone.now()
        self.save(update_fields=['cerrada_por_usuario', 'fecha_cerrada'])
    
    @classmethod
    def crear_notificacion_expiracion(cls, empresa, usuario, config):
        """
        Crea notificaciones automáticas basadas en la configuración de expiración
        """
        from evaluacion.models import ConfiguracionEvaluacion
        
        # Determinar qué fecha usar según configuración
        fecha_vuce = empresa.fecha_expiracion_licencia
        fecha_contrato = empresa.fecha_expiracion_contrato
        
        notificaciones_creadas = []
        
        def procesar_fecha(fecha, categoria, nombre_categoria):
            if not fecha:
                return
                
            dias_restantes = (fecha - timezone.now().date()).days
            
            # Determinar tipo de notificación
            if dias_restantes < 0:
                tipo = 'vencido'
                titulo = f"{nombre_categoria} Vencida"
                mensaje = f"Su {nombre_categoria.lower()} venció hace {abs(dias_restantes)} días. Debe renovar urgentemente."
            elif dias_restantes <= config.dias_preaviso_critico:
                tipo = 'critico'
                titulo = f"{nombre_categoria} por Vencer - URGENTE"
                mensaje = f"Su {nombre_categoria.lower()} expira en {dias_restantes} días. Debe renovar inmediatamente."
            elif dias_restantes <= config.dias_preaviso_advertencia:
                tipo = 'advertencia'
                titulo = f"{nombre_categoria} por Vencer"
                mensaje = f"Su {nombre_categoria.lower()} expira en {dias_restantes} días. Considere renovar pronto."
            elif dias_restantes <= config.dias_preaviso_informativo:
                tipo = 'informativo'
                titulo = f"Recordatorio: {nombre_categoria}"
                mensaje = f"Su {nombre_categoria.lower()} expira en {dias_restantes} días. Planifique su renovación."
            else:
                return  # No crear notificación si está muy lejos
            
            # Agregar enlace si está configurado
            enlace_accion = config.enlace_instrucciones if config.enlace_instrucciones else None
            texto_enlace = "Ver instrucciones" if enlace_accion else None
            
            if enlace_accion:
                mensaje += f" Para más información, consulte las instrucciones."
            
            # Verificar si ya existe una notificación similar
            existe = cls.objects.filter(
                empresa=empresa,
                usuario=usuario,
                categoria=categoria,
                tipo=tipo,
                activa=True,
                cerrada_por_usuario=False
            ).exists()
            
            if not existe:
                notificacion = cls.objects.create(
                    empresa=empresa,
                    usuario=usuario,
                    tipo=tipo,
                    categoria=categoria,
                    titulo=titulo,
                    mensaje=mensaje,
                    enlace_accion=enlace_accion,
                    texto_enlace=texto_enlace,
                    fecha_expiracion=fecha
                )
                notificaciones_creadas.append(notificacion)
        
        # Procesar según configuración
        if config.tipo_expiracion_principal == 'vuce' and fecha_vuce:
            procesar_fecha(fecha_vuce, 'vuce', 'Licencia VUCE')
        elif config.tipo_expiracion_principal == 'contrato' and fecha_contrato:
            procesar_fecha(fecha_contrato, 'contrato', 'Contrato')
        elif config.tipo_expiracion_principal == 'ambas':
            if fecha_vuce:
                procesar_fecha(fecha_vuce, 'vuce', 'Licencia VUCE')
            if fecha_contrato:
                procesar_fecha(fecha_contrato, 'contrato', 'Contrato')
        
        return notificaciones_creadas


class AprobacionExcepcional(models.Model):
    """
    Modelo para registrar aprobaciones de solicitudes excepcionales
    Audita cuándo, quién y por qué se habilita una empresa para solicitudes excepcionales
    """

    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('revocada', 'Revocada'),
        ('vencida', 'Vencida'),
    ]

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='aprobaciones_excepcionales',
        verbose_name='Empresa'
    )

    motivo = models.TextField(
        verbose_name='Motivo de la Aprobación',
        help_text='Justificación detallada de por qué se aprueba la solicitud excepcional'
    )

    aprobada_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='aprobaciones_excepcionales_otorgadas',
        verbose_name='Aprobada por'
    )

    fecha_aprobacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Aprobación'
    )

    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default='activa',
        verbose_name='Estado'
    )

    # Fechas de vigencia (opcional)
    fecha_inicio = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Inicio',
        help_text='Fecha desde la cual es válida la aprobación'
    )

    fecha_vencimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Vencimiento',
        help_text='Fecha hasta la cual es válida la aprobación (dejar vacío para indefinido)'
    )

    # Revocación
    revocada_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='aprobaciones_excepcionales_revocadas',
        verbose_name='Revocada por'
    )

    fecha_revocacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Revocación'
    )

    motivo_revocacion = models.TextField(
        blank=True,
        verbose_name='Motivo de Revocación',
        help_text='Razón por la cual se revocó la aprobación'
    )

    # Metadatos
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones Adicionales'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creada el')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizada el')

    class Meta:
        verbose_name = 'Aprobación Excepcional'
        verbose_name_plural = 'Aprobaciones Excepcionales'
        ordering = ['-fecha_aprobacion']
        indexes = [
            models.Index(fields=['empresa', 'estado']),
            models.Index(fields=['aprobada_por', '-fecha_aprobacion']),
        ]

    def __str__(self):
        return f"{self.empresa.nombre} - {self.get_estado_display()} ({self.fecha_aprobacion.strftime('%d/%m/%Y')})"

    @property
    def esta_activa(self):
        """Verifica si la aprobación está activa y vigente"""
        if self.estado != 'activa':
            return False

        # Si tiene fecha de vencimiento, verificar que no haya pasado
        if self.fecha_vencimiento:
            from django.utils import timezone
            return self.fecha_vencimiento >= timezone.now().date()

        return True

    @property
    def dias_para_vencer(self):
        """Calcula días hasta el vencimiento"""
        if not self.fecha_vencimiento:
            return None

        from django.utils import timezone
        delta = self.fecha_vencimiento - timezone.now().date()
        return delta.days

    def revocar(self, usuario, motivo):
        """Revoca la aprobación excepcional"""
        from django.utils import timezone

        self.estado = 'revocada'
        self.revocada_por = usuario
        self.fecha_revocacion = timezone.now()
        self.motivo_revocacion = motivo
        self.save()

        # Actualizar el campo de la empresa
        self.empresa.puede_solicitud_excepcional = False
        self.empresa.save(update_fields=['puede_solicitud_excepcional'])

    def activar_empresa(self):
        """Activa el permiso de solicitud excepcional en la empresa"""
        if self.esta_activa:
            self.empresa.puede_solicitud_excepcional = True
            self.empresa.save(update_fields=['puede_solicitud_excepcional'])

    def save(self, *args, **kwargs):
        """Sobrescribir save para activar empresa automáticamente"""
        super().save(*args, **kwargs)

        # Si es una aprobación nueva y está activa, activar empresa
        if self.estado == 'activa' and self.esta_activa:
            self.activar_empresa()
