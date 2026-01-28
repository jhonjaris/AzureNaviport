from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied

def role_required(*roles):
    """
    Decorador que requiere que el usuario tenga uno de los roles permitidos.
    
    Args:
        roles: Roles permitidos
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if hasattr(request.user, 'role') and request.user.role in roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, 'No tienes permisos para acceder a esta página.')
            # Importar aquí para evitar circular import
            from .views import redirect_by_role
            return redirect_by_role(request.user.role)
        return _wrapped_view
    return decorator

def solicitante_required(view_func):
    """Decorador que requiere rol de solicitante"""
    return role_required('solicitante')(view_func)

def evaluador_required(view_func):
    """Decorador que requiere rol de evaluador"""
    return role_required('evaluador')(view_func)

def supervisor_required(view_func):
    """Decorador que requiere rol de supervisor"""
    return role_required('supervisor')(view_func)

def oficial_acceso_required(view_func):
    """Decorador que requiere rol de oficial de acceso"""
    return role_required('oficial_acceso')(view_func)

def admin_required(view_func):
    """Decorador que requiere rol de administrador"""
    return role_required('admin_tic')(view_func)

def can_evaluate_required(view_func):
    """Decorador que requiere permisos de evaluación"""
    return role_required('evaluador', 'supervisor', 'admin_tic')(view_func)

def can_supervise_required(view_func):
    """Decorador que requiere permisos de supervisión"""
    return role_required('supervisor', 'admin_tic')(view_func)

def active_user_required(view_func):
    """Decorador que requiere que el usuario esté activo"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.activo:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'Tu cuenta está desactivada. Contacta al administrador.')
            return redirect('accounts:logout')
    return wrapper

def ajax_required(view_func):
    """Decorador que requiere que la petición sea AJAX"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return view_func(request, *args, **kwargs)
        else:
            return HttpResponseForbidden('Esta vista requiere una petición AJAX.')
    return wrapper 