#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naviport.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model

def debug_sessions():
    print("=== DEBUGGING SESSIONS ===")
    
    User = get_user_model()
    
    # Mostrar todos los usuarios
    print("\n=== USUARIOS REGISTRADOS ===")
    users = User.objects.all()
    for user in users:
        print(f"ID: {user.id}, Username: {user.username}, Nombre: {user.get_display_name()}, Role: {user.role}")
    
    # Mostrar sesiones activas
    print("\n=== SESIONES ACTIVAS ===")
    sessions = Session.objects.all()
    print(f"Total de sesiones: {sessions.count()}")
    
    for session in sessions:
        print(f"\nSession Key: {session.session_key}")
        print(f"Expires: {session.expire_date}")
        
        try:
            session_data = session.get_decoded()
            print(f"Session Data: {session_data}")
            
            if '_auth_user_id' in session_data:
                user_id = session_data['_auth_user_id']
                try:
                    user = User.objects.get(id=user_id)
                    print(f"Usuario autenticado: {user.username} ({user.get_display_name()}) - Role: {user.role}")
                except User.DoesNotExist:
                    print(f"ERROR: Usuario con ID {user_id} no existe en la base de datos")
            else:
                print("No hay usuario autenticado en esta sesión")
                
        except Exception as e:
            print(f"Error decodificando sesión: {e}")

if __name__ == '__main__':
    debug_sessions()