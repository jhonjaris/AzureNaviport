"""
Signals para registrar eventos automáticamente en el timeline de solicitudes
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Solicitud, EventoSolicitud


@receiver(post_save, sender=Solicitud)
def registrar_evento_creacion(sender, instance, created, **kwargs):
    """
    Registra un evento cuando se crea una nueva solicitud
    """
    if created:
        EventoSolicitud.objects.create(
            solicitud=instance,
            usuario=instance.solicitante,
            tipo_evento='creacion',
            titulo='Solicitud creada',
            descripcion=f'Se creó la solicitud {instance.codigo} en estado "{instance.get_estado_display()}"',
            metadata={
                'estado_inicial': instance.estado,
                'puerto': instance.puerto_destino.nombre,
                'fecha_ingreso': str(instance.fecha_ingreso),
            },
            es_visible_solicitante=True,
            es_interno=False
        )


@receiver(pre_save, sender=Solicitud)
def detectar_cambios_solicitud(sender, instance, **kwargs):
    """
    Detecta cambios en la solicitud y registra eventos correspondientes.
    Este signal se ejecuta ANTES de guardar, por eso usamos pre_save.
    """
    # Solo procesamos si la solicitud ya existe (no es creación)
    if instance.pk:
        try:
            # Obtener el estado anterior de la solicitud
            solicitud_anterior = Solicitud.objects.get(pk=instance.pk)

            # Detectar cambio de estado
            if solicitud_anterior.estado != instance.estado:
                registrar_cambio_estado(instance, solicitud_anterior.estado, instance.estado)

            # Detectar asignación de evaluador
            if solicitud_anterior.evaluador_asignado != instance.evaluador_asignado:
                registrar_asignacion_evaluador(instance, solicitud_anterior.evaluador_asignado, instance.evaluador_asignado)

            # Detectar cambio de prioridad
            if solicitud_anterior.prioridad != instance.prioridad:
                registrar_cambio_prioridad(instance, solicitud_anterior.prioridad, instance.prioridad)

        except Solicitud.DoesNotExist:
            # La solicitud no existe aún, es una creación (manejado por post_save)
            pass


def registrar_cambio_estado(solicitud, estado_anterior, estado_nuevo):
    """
    Registra un evento de cambio de estado con lógica específica según el estado
    """
    # Mapeo de estados a tipos de evento y títulos
    evento_info = {
        'recibido': {
            'tipo': 'envio',
            'titulo': 'Solicitud enviada',
            'descripcion': 'La solicitud fue enviada para evaluación',
            'visible': True,
            'interno': False
        },
        'en_revision': {
            'tipo': 'inicio_revision',
            'titulo': 'Revisión iniciada',
            'descripcion': 'El evaluador ha iniciado la revisión de la solicitud',
            'visible': True,
            'interno': False
        },
        'documentos_faltantes': {
            'tipo': 'documentos_faltantes',
            'titulo': 'Documentos faltantes',
            'descripcion': 'Se han solicitado documentos adicionales',
            'visible': True,
            'interno': False
        },
        'aprobada': {
            'tipo': 'aprobacion',
            'titulo': 'Solicitud aprobada',
            'descripcion': f'La solicitud ha sido aprobada',
            'visible': True,
            'interno': False
        },
        'rechazada': {
            'tipo': 'rechazo',
            'titulo': 'Solicitud rechazada',
            'descripcion': f'La solicitud ha sido rechazada',
            'visible': True,
            'interno': False
        },
        'escalada': {
            'tipo': 'escalacion',
            'titulo': 'Escalada a supervisor',
            'descripcion': 'La solicitud fue escalada al supervisor para revisión',
            'visible': False,
            'interno': True
        },
    }

    # Obtener información del evento o usar valores por defecto
    info = evento_info.get(estado_nuevo, {
        'tipo': 'cambio_estado',
        'titulo': f'Estado actualizado',
        'descripcion': f'El estado cambió de "{Solicitud.ESTADO_CHOICES[estado_anterior][1]}" a "{Solicitud.ESTADO_CHOICES[estado_nuevo][1]}"',
        'visible': True,
        'interno': False
    })

    EventoSolicitud.objects.create(
        solicitud=solicitud,
        usuario=None,  # Se asignará desde la vista que hizo el cambio
        tipo_evento=info['tipo'],
        titulo=info['titulo'],
        descripcion=info['descripcion'],
        metadata={
            'estado_anterior': estado_anterior,
            'estado_nuevo': estado_nuevo,
            'timestamp': timezone.now().isoformat()
        },
        es_visible_solicitante=info['visible'],
        es_interno=info['interno']
    )


def registrar_asignacion_evaluador(solicitud, evaluador_anterior, evaluador_nuevo):
    """
    Registra un evento de asignación o reasignación de evaluador
    """
    if evaluador_anterior is None:
        # Primera asignación
        tipo_evento = 'asignacion'
        titulo = 'Solicitud asignada'
        descripcion = f'La solicitud fue asignada a {evaluador_nuevo.get_full_name()}'
    else:
        # Reasignación
        tipo_evento = 'reasignacion'
        titulo = 'Solicitud reasignada'
        descripcion = f'La solicitud fue reasignada de {evaluador_anterior.get_full_name()} a {evaluador_nuevo.get_full_name()}'

    EventoSolicitud.objects.create(
        solicitud=solicitud,
        usuario=evaluador_nuevo,
        tipo_evento=tipo_evento,
        titulo=titulo,
        descripcion=descripcion,
        metadata={
            'evaluador_anterior_id': evaluador_anterior.id if evaluador_anterior else None,
            'evaluador_nuevo_id': evaluador_nuevo.id,
            'evaluador_anterior_nombre': evaluador_anterior.get_full_name() if evaluador_anterior else None,
            'evaluador_nuevo_nombre': evaluador_nuevo.get_full_name(),
        },
        es_visible_solicitante=False,
        es_interno=True
    )


def registrar_cambio_prioridad(solicitud, prioridad_anterior, prioridad_nueva):
    """
    Registra un evento de cambio de prioridad
    """
    # Obtener el display name de las prioridades
    prioridades_dict = dict(Solicitud.PRIORIDAD_CHOICES)

    EventoSolicitud.objects.create(
        solicitud=solicitud,
        usuario=None,
        tipo_evento='cambio_prioridad',
        titulo='Prioridad actualizada',
        descripcion=f'La prioridad cambió de "{prioridades_dict[prioridad_anterior]}" a "{prioridades_dict[prioridad_nueva]}"',
        metadata={
            'prioridad_anterior': prioridad_anterior,
            'prioridad_nueva': prioridad_nueva,
        },
        es_visible_solicitante=False,
        es_interno=True
    )


def registrar_evento_manual(solicitud, usuario, tipo_evento, titulo, descripcion, metadata=None, visible=True, interno=False):
    """
    Función helper para registrar eventos manuales desde vistas.

    Uso desde vistas:
    from solicitudes.signals import registrar_evento_manual

    registrar_evento_manual(
        solicitud=solicitud,
        usuario=request.user,
        tipo_evento='comentario',
        titulo='Comentario agregado',
        descripcion='El evaluador agregó un comentario...',
        metadata={'comentario': texto},
        visible=True,
        interno=False
    )
    """
    return EventoSolicitud.objects.create(
        solicitud=solicitud,
        usuario=usuario,
        tipo_evento=tipo_evento,
        titulo=titulo,
        descripcion=descripcion,
        metadata=metadata or {},
        es_visible_solicitante=visible,
        es_interno=interno
    )
