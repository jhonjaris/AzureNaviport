#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naviport.settings')
django.setup()

from django.contrib.auth import get_user_model

def check_superuser():
    User = get_user_model()
    
    print("=== VERIFICANDO SUPERUSUARIO ===")
    
    # Buscar superusuarios
    superusers = User.objects.filter(is_superuser=True)
    print(f"Superusuarios encontrados: {superusers.count()}")
    
    for user in superusers:
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Is staff: {user.is_staff}")
        print(f"Is active: {user.is_active}")
        print(f"Password admin123 valid: {user.check_password('admin123')}")
        print(f"Password password123 valid: {user.check_password('password123')}")
        print("---")
    
    # Si no hay superusuario, crear uno
    if superusers.count() == 0:
        print("No hay superusuarios. Creando uno...")
        User.objects.create_superuser(
            username='admin',
            email='admin@naviport.com',
            password='admin123',
            role='admin_tic',
            cedula_rnc='001-0000000-1',
            first_name='Admin',
            last_name='Sistema'
        )
        print("Superusuario creado: admin / admin123")

if __name__ == '__main__':
    check_superuser()