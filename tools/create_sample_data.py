#!/usr/bin/env python
import os
import sys
import django

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naviport.settings')
django.setup()

from solicitudes.models import Puerto, MotivoAcceso
from accounts.models import User, Empresa

def create_sample_data():
    # Crear puertos
    puertos = [
        {'nombre': 'Puerto Haina Oriental', 'codigo': 'HAI-OR', 'ubicacion': 'Haina, San Cristóbal'},
        {'nombre': 'Puerto Caucedo', 'codigo': 'CAU', 'ubicacion': 'Boca Chica, Santo Domingo'},
        {'nombre': 'Puerto Multimodal', 'codigo': 'MULTI', 'ubicacion': 'Santo Domingo Este'},
        {'nombre': 'Puerto Boca Chica', 'codigo': 'BOC-CH', 'ubicacion': 'Boca Chica, Santo Domingo'},
        {'nombre': 'Puerto Haina Norte', 'codigo': 'HAI-NO', 'ubicacion': 'Haina, San Cristóbal'},
    ]
    
    for puerto_data in puertos:
        puerto, created = Puerto.objects.get_or_create(
            nombre=puerto_data['nombre'],
            defaults={
                'codigo': puerto_data['codigo'],
                'ubicacion': puerto_data.get('ubicacion', ''),
                'activo': True
            }
        )
        if created:
            print(f'Puerto creado: {puerto.nombre}')
        else:
            print(f'Puerto ya existe: {puerto.nombre}')
    
    # Crear motivos de acceso
    motivos = [
        {'nombre': 'Carga y Descarga', 'descripcion': 'Operaciones de carga y descarga de mercancías', 'requiere_documentos_especiales': False},
        {'nombre': 'Inspección de Mercancía', 'descripcion': 'Inspección física de contenedores y mercancías', 'requiere_documentos_especiales': True},
        {'nombre': 'Mantenimiento Preventivo', 'descripcion': 'Trabajos de mantenimiento de equipos e instalaciones', 'requiere_documentos_especiales': True},
        {'nombre': 'Visita Técnica', 'descripcion': 'Visitas técnicas y de supervisión', 'requiere_documentos_especiales': False},
        {'nombre': 'Supervisión de Obra', 'descripcion': 'Supervisión de trabajos de construcción y obra civil', 'requiere_documentos_especiales': True},
        {'nombre': 'Transporte de Personal', 'descripcion': 'Transporte de trabajadores y personal autorizado', 'requiere_documentos_especiales': False},
    ]
    
    for motivo_data in motivos:
        motivo, created = MotivoAcceso.objects.get_or_create(
            nombre=motivo_data['nombre'],
            defaults={
                'descripcion': motivo_data['descripcion'],
                'requiere_documentos_especiales': motivo_data['requiere_documentos_especiales'],
                'activo': True
            }
        )
        if created:
            print(f'Motivo creado: {motivo.nombre}')
        else:
            print(f'Motivo ya existe: {motivo.nombre}')
    
    # Crear empresas
    empresas_data = [
        {
            'nombre': 'Logística del Caribe SRL',
            'rnc': '131-12345-7',
            'telefono': '809-555-0001',
            'email': 'logistica@caribe.com',
        },
        {
            'nombre': 'Navieros Unidos SA',
            'rnc': '101-98765-4',
            'telefono': '809-555-0002',
            'email': 'admin@navierosunidos.com',
        },
        {
            'nombre': 'Transportes Express',
            'rnc': '201-55555-1',
            'telefono': '809-555-0003',
            'email': 'info@transportesexpress.com',
        },
        {
            'nombre': 'Carga Rápida Dominicana',
            'rnc': '301-77777-8',
            'telefono': '809-555-0004',
            'email': 'info@cargarapida.com',
        },
        {
            'nombre': 'Maritima del Este',
            'rnc': '401-88888-5',
            'telefono': '809-555-0005',
            'email': 'contacto@maritimaeste.com',
        }
    ]
    
    # Crear usuarios y empresas
    usuarios_data = [
        # Solicitantes (empresas)
        {
            'username': 'mgonzalez',
            'password': 'demo123',
            'first_name': 'María',
            'last_name': 'González',
            'email': 'maria.gonzalez@caribe.com',
            'cedula_rnc': '001-1234567-8',
            'telefono': '809-555-0001',
            'role': 'solicitante',
            'empresa_rnc': '131-12345-7'
        },
        {
            'username': 'jrodriguez',
            'password': 'demo123',
            'first_name': 'José',
            'last_name': 'Rodríguez',
            'email': 'jose.rodriguez@navierosunidos.com',
            'cedula_rnc': '001-2345678-9',
            'telefono': '809-555-0002',
            'role': 'solicitante',
            'empresa_rnc': '101-98765-4'
        },
        {
            'username': 'lmartinez',
            'password': 'demo123',
            'first_name': 'Luis',
            'last_name': 'Martínez',
            'email': 'luis.martinez@transportesexpress.com',
            'cedula_rnc': '001-3456789-0',
            'telefono': '809-555-0003',
            'role': 'solicitante',
            'empresa_rnc': '201-55555-1'
        },
        # Evaluadores
        {
            'username': 'asanchez',
            'password': 'eval123',
            'first_name': 'Ana',
            'last_name': 'Sánchez',
            'email': 'ana.sanchez@portuaria.gob.do',
            'cedula_rnc': '001-4567890-1',
            'telefono': '809-555-1001',
            'role': 'evaluador',
        },
        {
            'username': 'cmartinez',
            'password': 'eval123',
            'first_name': 'Carlos',
            'last_name': 'Martínez',
            'email': 'carlos.martinez@portuaria.gob.do',
            'cedula_rnc': '001-5678901-2',
            'telefono': '809-555-1002',
            'role': 'evaluador',
        },
        {
            'username': 'alopez',
            'password': 'eval123',
            'first_name': 'Ana',
            'last_name': 'López',
            'email': 'ana.lopez@portuaria.gob.do',
            'cedula_rnc': '001-6789012-3',
            'telefono': '809-555-1003',
            'role': 'evaluador',
        },
        # Oficiales de Acceso
        {
            'username': 'jperez',
            'password': 'acceso123',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': 'juan.perez@portuaria.gob.do',
            'cedula_rnc': '001-7890123-4',
            'telefono': '809-555-2001',
            'role': 'oficial_acceso',
        },
        {
            'username': 'pgarcia',
            'password': 'acceso123',
            'first_name': 'Pedro',
            'last_name': 'García',
            'email': 'pedro.garcia@portuaria.gob.do',
            'cedula_rnc': '001-8901234-5',
            'telefono': '809-555-2002',
            'role': 'oficial_acceso',
        },
        {
            'username': 'lruiz',
            'password': 'acceso123',
            'first_name': 'Luis',
            'last_name': 'Ruiz',
            'email': 'luis.ruiz@portuaria.gob.do',
            'cedula_rnc': '001-9012345-6',
            'telefono': '809-555-2003',
            'role': 'oficial_acceso',
        },
        # Supervisores
        {
            'username': 'rsilva',
            'password': 'super123',
            'first_name': 'Roberto',
            'last_name': 'Silva',
            'email': 'roberto.silva@portuaria.gob.do',
            'cedula_rnc': '001-0123456-7',
            'telefono': '809-555-3001',
            'role': 'supervisor',
        },
        {
            'username': 'cruiz',
            'password': 'super123',
            'first_name': 'Carmen',
            'last_name': 'Ruiz',
            'email': 'carmen.ruiz@portuaria.gob.do',
            'cedula_rnc': '001-1234561-8',
            'telefono': '809-555-3002',
            'role': 'supervisor',
        },
        # Admin TIC
        {
            'username': 'jtech',
            'password': 'tech123',
            'first_name': 'José',
            'last_name': 'Tech',
            'email': 'jose.tech@portuaria.gob.do',
            'cedula_rnc': '001-2345672-9',
            'telefono': '809-555-4001',
            'role': 'admin_tic',
        }
    ]
    
    # Separar usuarios por tipo
    usuarios_no_solicitantes = [u for u in usuarios_data if u['role'] != 'solicitante']
    usuarios_solicitantes = [u for u in usuarios_data if u['role'] == 'solicitante']
    
    # Crear primero usuarios no solicitantes
    print("\n--- Creando Usuarios No Solicitantes ---")
    for user_data in usuarios_no_solicitantes:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'password': user_data['password'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'email': user_data['email'],
                'cedula_rnc': user_data['cedula_rnc'],
                'telefono': user_data['telefono'],
                'role': user_data['role'],
                'empresa': None,
                'is_active': True
            }
        )
        
        if created:
            user.set_password(user_data['password'])
            user.save()
            print(f'Usuario creado: {user.username} ({user.get_role_display()})')
        else:
            print(f'Usuario ya existe: {user.username}')
    
    # Crear usuarios solicitantes
    print("\n--- Creando Usuarios Solicitantes ---")
    usuarios_solicitantes_creados = {}
    for user_data in usuarios_solicitantes:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'password': user_data['password'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'email': user_data['email'],
                'cedula_rnc': user_data['cedula_rnc'],
                'telefono': user_data['telefono'],
                'role': user_data['role'],
                'empresa': None,  # Se asignará después
                'is_active': True
            }
        )
        
        if created:
            user.set_password(user_data['password'])
            user.save()
            print(f'Usuario creado: {user.username} ({user.get_role_display()})')
        else:
            print(f'Usuario ya existe: {user.username}')
            
        usuarios_solicitantes_creados[user_data['empresa_rnc']] = user
    
    # Crear empresas con representantes legales
    print("\n--- Creando Empresas ---")
    empresas_creadas = {}
    for empresa_data in empresas_data:
        # Obtener el usuario solicitante correspondiente
        representante = usuarios_solicitantes_creados.get(empresa_data['rnc'])
        print(f"Empresa: {empresa_data['nombre']} - RNC: {empresa_data['rnc']} - Representante: {representante}")
        
        if not representante:
            print(f"AVISO: No se encontro representante para {empresa_data['nombre']}")
            continue
        
        empresa, created = Empresa.objects.get_or_create(
            rnc=empresa_data['rnc'],
            defaults={
                'nombre': empresa_data['nombre'],
                'telefono': empresa_data['telefono'],
                'email': empresa_data['email'],
                'representante_legal': representante
            }
        )
        empresas_creadas[empresa_data['rnc']] = empresa
        if created:
            print(f'Empresa creada: {empresa.nombre}')
        else:
            print(f'Empresa ya existe: {empresa.nombre}')
    
    # Actualizar usuarios solicitantes con sus empresas
    print("\n--- Actualizando Relación Usuario-Empresa ---")
    for user_data in usuarios_solicitantes:
        user = usuarios_solicitantes_creados.get(user_data['empresa_rnc'])
        empresa = empresas_creadas.get(user_data['empresa_rnc'])
        
        if user and empresa and not user.empresa:
            user.empresa = empresa
            user.save()
            print(f'Usuario {user.username} asignado a {empresa.nombre}')
    
    print("\n--- Resumen ---")
    print(f"Puertos: {Puerto.objects.count()}")
    print(f"Motivos de acceso: {MotivoAcceso.objects.count()}")
    print(f"Empresas: {Empresa.objects.count()}")
    print(f"Usuarios: {User.objects.count()}")
    print("\nDatos de ejemplo creados exitosamente!")

if __name__ == '__main__':
    create_sample_data()