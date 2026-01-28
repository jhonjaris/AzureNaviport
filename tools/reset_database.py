#!/usr/bin/env python
import os
import sys
import subprocess

def run_command(command, description):
    print(f"\n>>> {description}")
    print(f"Ejecutando: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False

def reset_database():
    print("=== RESET DE BASE DE DATOS NAVIPORT RD ===")
    
    # Cambiar al directorio del proyecto
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    print(f"Directorio: {project_dir}")
    
    # 1. Intentar eliminar la base de datos
    db_file = "db.sqlite3"
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
            print(f"✓ Base de datos {db_file} eliminada")
        except Exception as e:
            print(f"⚠ No se pudo eliminar {db_file}: {e}")
            print("Por favor, cierra cualquier proceso que use la base de datos y ejecuta este script nuevamente")
            return False
    
    # 2. Eliminar migraciones existentes (excepto __init__.py)
    print("\n>>> Limpiando migraciones existentes...")
    for app in ['accounts', 'solicitudes', 'control_acceso', 'supervisor']:
        migrations_dir = os.path.join(app, 'migrations')
        if os.path.exists(migrations_dir):
            for file in os.listdir(migrations_dir):
                if file.endswith('.py') and file != '__init__.py':
                    file_path = os.path.join(migrations_dir, file)
                    try:
                        os.remove(file_path)
                        print(f"  ✓ Eliminado: {file_path}")
                    except Exception as e:
                        print(f"  ⚠ Error eliminando {file_path}: {e}")
    
    # 3. Crear nuevas migraciones
    commands = [
        ("python manage.py makemigrations accounts", "Crear migraciones para accounts"),
        ("python manage.py makemigrations solicitudes", "Crear migraciones para solicitudes"),
        ("python manage.py makemigrations control_acceso", "Crear migraciones para control_acceso"),
        ("python manage.py makemigrations supervisor", "Crear migraciones para supervisor"),
        ("python manage.py migrate", "Aplicar todas las migraciones"),
        ("python manage.py createsuperuser --noinput --username admin --email admin@test.com", "Crear superusuario"),
        ("python create_sample_data.py", "Cargar datos de prueba"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            if "createsuperuser" in command:
                print("⚠ Superusuario ya existe o hubo un error. Continuando...")
                continue
            else:
                print(f"❌ Error en: {description}")
                return False
    
    # 4. Establecer contraseña del admin
    print("\n>>> Configurando contraseña del admin...")
    admin_password_cmd = '''python manage.py shell -c "
from accounts.models import User
try:
    admin = User.objects.get(username='admin')
    admin.set_password('admin123')
    admin.role = 'admin_tic'
    admin.activo = True
    admin.save()
    print('✓ Admin configurado: admin/admin123')
except Exception as e:
    print(f'Error configurando admin: {e}')
"'''
    
    run_command(admin_password_cmd, "Configurar admin")
    
    print("\n" + "="*50)
    print("✓ RESET COMPLETADO")
    print("\nCredenciales disponibles:")
    print("  • admin / admin123 (Admin)")
    print("  • logistica_caribe / demo123 (Empresa)")
    print("  • maria.gonzalez.eval / eval123 (Evaluador)")
    print("  • juan.rodriguez / acceso123 (Oficial)")
    print("  • roberto.silva / super123 (Supervisor)")
    print("\nPara iniciar el servidor:")
    print("  python manage.py runserver")
    print("\nURL de login:")
    print("  http://127.0.0.1:8000/login/")

if __name__ == '__main__':
    reset_database()