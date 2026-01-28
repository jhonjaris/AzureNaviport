"""
URL configuration for naviport project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from control_acceso.views import verificar_autorizacion_publica

def home_redirect(request):
    """Redirige a la página apropiada según el estado de autenticación"""
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    
    try:
        # Obtener el usuario usando solo campos seguros
        from accounts.models import User
        user = User.objects.select_related('empresa').get(id=request.user.id)
        
        # Redirigir según el rol
        role_redirects = {
            'solicitante': 'solicitudes:dashboard',
            'evaluador': 'evaluacion:dashboard', 
            'supervisor': 'supervisor:dashboard',
            'oficial_acceso': 'control_acceso:dashboard',
            'admin_tic': 'admin:index',
            'direccion': 'reportes:dashboard'
        }
        
        redirect_url = role_redirects.get(user.role, 'accounts:login')
        return redirect(redirect_url)
        
    except Exception as e:
        # Si hay cualquier error, ir al login
        from django.contrib import messages
        messages.error(request, 'Error al acceder al sistema. Por favor, inicie sesión nuevamente.')
        return redirect('accounts:login')

def debug_admin(request):
    """Debug del admin de Django"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    html = """
    <html>
    <head><title>Debug Admin NaviPort</title></head>
    <body>
        <h1>Debug Admin NaviPort RD</h1>
        <h2>Modelos Registrados en Admin:</h2>
        <ul>
    """
    
    for model, admin_class in admin.site._registry.items():
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        html += f"<li><strong>{app_label}.{model_name}</strong> ({admin_class.__class__.__name__})</li>"
    
    html += f"""
        </ul>
        <h2>Estadísticas:</h2>
        <ul>
            <li>Total usuarios: {User.objects.count()}</li>
            <li>Superusuarios: {User.objects.filter(is_superuser=True).count()}</li>
        </ul>
        <h2>Enlaces:</h2>
        <ul>
            <li><a href="/admin/" target="_blank">Ir al Admin de Django</a></li>
            <li><a href="/" target="_blank">Ir al Dashboard</a></li>
        </ul>
        <h2>Credenciales Admin:</h2>
        <p><strong>Usuario:</strong> admin<br>
        <strong>Contraseña:</strong> admin123</p>
    </body>
    </html>
    """
    
    return HttpResponse(html)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('debug-admin/', debug_admin, name='debug_admin'),
    # Ruta pública de verificación (debe ir antes de las rutas con login)
    path('verificar/<uuid:uuid>/', verificar_autorizacion_publica, name='verificar_autorizacion_publica'),
    path('accounts/', include('accounts.urls')),
    path('solicitudes/', include('solicitudes.urls')),
    path('evaluacion/', include('evaluacion.urls')),
    path('supervisor/', include('supervisor.urls')),
    path('control_acceso/', include('control_acceso.urls')),
    path('reportes/', include('reportes.urls')),
    path('empresas/', include('empresas.urls')),
    path('gestion_personal/', include('gestion_personal.urls')),
    path('gestion_vehiculos/', include('gestion_vehiculos.urls')),
    path('notificaciones/', include('notificaciones.urls')),
    path('incumplimientos/', include('incumplimientos.urls')),
    path('login/', lambda request: redirect('accounts:login'), name='login'),
    path('dashboard/', home_redirect, name='dashboard'),
    path('', home_redirect, name='home'),
]

# Servir archivos multimedia en modo desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
