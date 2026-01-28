#!/usr/bin/env python
import os
import sys
import django

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naviport.settings')
django.setup()

from accounts.models import User
from django.contrib.auth import authenticate

def test_login():
    print("=== TEST DE LOGIN NAVIPORT RD ===\n")
    
    # Listar algunos usuarios para probar
    print("Usuarios disponibles para probar:")
    usuarios_prueba = [
        ('logistica_caribe', 'demo123', 'Solicitante'),
        ('maria.gonzalez.eval', 'eval123', 'Evaluador'),
        ('juan.rodriguez', 'acceso123', 'Oficial de Acceso'),
        ('roberto.silva', 'super123', 'Supervisor'),
        ('admin', 'admin123', 'Admin'),
    ]
    
    for username, password, role in usuarios_prueba:
        print(f"  - {username} / {password} ({role})")
    
    print("\n" + "="*50)
    
    # Probar autenticación de cada usuario
    for username, password, role_desc in usuarios_prueba:
        print(f"\nProbando login: {username}")
        
        try:
            # Verificar que el usuario existe
            user = User.objects.get(username=username)
            print(f"  [OK] Usuario encontrado: {user.get_display_name()}")
            print(f"  [OK] Rol: {user.get_role_display()}")
            print(f"  [OK] Activo: {'Si' if user.activo else 'No'}")
            print(f"  [OK] Email: {user.email}")
            if user.empresa:
                print(f"  [OK] Empresa: {user.empresa.nombre}")
            
            # Probar autenticación
            auth_user = authenticate(username=username, password=password)
            if auth_user:
                print(f"  [OK] Autenticacion: EXITOSA")
            else:
                print(f"  [ERROR] Autenticacion: FALLIDA")
                
        except User.DoesNotExist:
            print(f"  [ERROR] Usuario NO ENCONTRADO")
        except Exception as e:
            print(f"  [ERROR] Error: {str(e)}")
    
    print("\n" + "="*50)
    print("TEST COMPLETADO")
    print("\nPara probar el login web:")
    print("1. Ejecuta: python manage.py runserver")
    print("2. Visita: http://127.0.0.1:8000/login/")
    print("3. Usa cualquiera de las credenciales de arriba")

if __name__ == '__main__':
    test_login()