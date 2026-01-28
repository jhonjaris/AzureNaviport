#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naviport.settings')
django.setup()

from django.contrib import admin
from accounts.models import User, Empresa
from solicitudes.models import Solicitud, Puerto, MotivoAcceso
from control_acceso.models import Autorizacion
from supervisor.models import Escalamiento

def check_admin_registry():
    print("=== VERIFICANDO REGISTRO EN ADMIN ===")
    
    # Obtener todos los modelos registrados
    registered_models = admin.site._registry
    
    print(f"\nTotal de modelos registrados: {len(registered_models)}")
    print("\nModelos registrados:")
    
    for model, admin_class in registered_models.items():
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        admin_class_name = admin_class.__class__.__name__
        print(f"  - {app_label}.{model_name} ({admin_class_name})")
    
    # Verificar modelos específicos
    models_to_check = [
        (User, 'accounts.User'),
        (Empresa, 'accounts.Empresa'),
        (Solicitud, 'solicitudes.Solicitud'),
        (Puerto, 'solicitudes.Puerto'),
        (MotivoAcceso, 'solicitudes.MotivoAcceso'),
        (Autorizacion, 'control_acceso.Autorizacion'),
        (Escalamiento, 'supervisor.Escalamiento'),
    ]
    
    print("\n=== VERIFICACIÓN DE MODELOS ESPECÍFICOS ===")
    for model, model_path in models_to_check:
        is_registered = model in registered_models
        status = "✅ REGISTRADO" if is_registered else "❌ NO REGISTRADO"
        print(f"{model_path}: {status}")
        
        if is_registered:
            admin_class = registered_models[model]
            print(f"    Admin class: {admin_class.__class__.__name__}")

if __name__ == '__main__':
    check_admin_registry()