from django import template

register = template.Library()

@register.filter
def split(value, delimiter):
    """Divide una cadena por el delimitador especificado"""
    return value.split(delimiter)

@register.filter
def get_item(list_obj, index):
    """Obtiene un item de una lista por índice"""
    try:
        return list_obj[int(index)]
    except (IndexError, ValueError, TypeError):
        return ''


# ===== FILTROS PARA ESTADOS POR ROL =====

@register.filter
def estado_para_rol(solicitud, user):
    """Retorna el estado visible según el rol del usuario"""
    if hasattr(solicitud, 'get_estado_para_rol') and hasattr(user, 'role'):
        return solicitud.get_estado_para_rol(user.role)
    return solicitud.estado if hasattr(solicitud, 'estado') else ''


@register.filter
def estado_display_para_rol(solicitud, user):
    """Retorna el texto del estado según el rol del usuario"""
    if hasattr(solicitud, 'get_estado_display_para_rol') and hasattr(user, 'role'):
        return solicitud.get_estado_display_para_rol(user.role)
    return solicitud.get_estado_display() if hasattr(solicitud, 'get_estado_display') else ''


@register.simple_tag
def estado_con_color_para_rol(solicitud, user):
    """Retorna el diccionario de estado con color según el rol"""
    if hasattr(solicitud, 'get_estado_con_color_para_rol') and hasattr(user, 'role'):
        return solicitud.get_estado_con_color_para_rol(user.role)
    return solicitud.estado_con_color if hasattr(solicitud, 'estado_con_color') else {}
