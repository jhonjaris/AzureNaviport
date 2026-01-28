#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naviport.settings')
django.setup()

from django.contrib import admin
from django.contrib.auth import get_user_model
from accounts.models import Empresa
from solicitudes.models import Solicitud, Puerto

def debug_admin():
    print("=== DEBUG ADMIN NAVIPORT RD ===")
    
    User = get_user_model()
    
    # Verificar modelos
    print("\n1. MODELOS REGISTRADOS:")
    for model, admin_class in admin.site._registry.items():
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        print(f"   {app_label}.{model_name} -> {admin_class.__class__.__name__}")
    
    # Contar registros
    print("\n2. CONTEO DE REGISTROS:")
    print(f"   Usuarios: {User.objects.count()}")
    print(f"   Empresas: {Empresa.objects.count()}")
    print(f"   Solicitudes: {Solicitud.objects.count()}")
    print(f"   Puertos: {Puerto.objects.count()}")
    
    # Usuarios por rol
    print("\n3. USUARIOS POR ROL:")
    roles = User.objects.values_list('role', flat=True).distinct()
    for role in roles:
        count = User.objects.filter(role=role).count()
        print(f"   {role}: {count}")
    
    print("\n4. SUPERUSUARIOS:")
    superusers = User.objects.filter(is_superuser=True)
    for user in superusers:
        print(f"   {user.username} ({user.email}) - Staff: {user.is_staff}")

if __name__ == '__main__':
    debug_admin()