"""
Configuración de producción para PythonAnywhere
"""
import os
from .settings import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Hosts permitidos - actualizar con tu dominio de PythonAnywhere
ALLOWED_HOSTS = [
    'tuusuario.pythonanywhere.com',  # Cambiar 'tuusuario' por tu nombre de usuario
    'www.tuusuario.pythonanywhere.com',  # Cambiar 'tuusuario' por tu nombre de usuario
]

# Base de datos para producción (SQLite está bien para proyectos pequeños)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/home/tuusuario/NaviPortRD/db.sqlite3',  # Cambiar 'tuusuario'
    }
}

# Configuración de archivos estáticos para producción
STATIC_URL = '/static/'
STATIC_ROOT = '/home/tuusuario/NaviPortRD/staticfiles'  # Cambiar 'tuusuario'
STATICFILES_DIRS = [
    '/home/tuusuario/NaviPortRD/static',  # Cambiar 'tuusuario'
]

# Configuración de archivos media
MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/tuusuario/NaviPortRD/media'  # Cambiar 'tuusuario'

# Whitenoise para servir archivos estáticos
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Configuración de seguridad adicional
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Configuración de sesiones
SESSION_COOKIE_SECURE = False  # True si usas HTTPS
CSRF_COOKIE_SECURE = False     # True si usas HTTPS

# Configuración de logging para producción
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/home/tuusuario/NaviPortRD/django.log',  # Cambiar 'tuusuario'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}