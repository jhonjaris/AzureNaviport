#!/usr/bin/env python
"""
Script para crear solicitudes de prueba con datos falsos
para testear las funcionalidades del sistema NaviPort RD
"""
import os
import sys
import django
from datetime import datetime, timedelta, time
import random

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naviport.settings')
django.setup()

from django.contrib.auth import get_user_model
from solicitudes.models import Solicitud, Puerto, MotivoAcceso, SolicitudPersonal
from accounts.models import Empresa
from empresas.models import Personal

User = get_user_model()

# Datos falsos para generar contenido
NOMBRES = [
    "Juan Carlos", "María Elena", "Pedro José", "Ana Lucía", "Carlos Alberto",
    "Sofía Isabel", "Miguel Ángel", "Carmen Rosa", "José Antonio", "Lucía María",
    "Fernando Luis", "Patricia Elena", "Roberto Carlos", "Mónica Isabel", "Diego Alejandro"
]

APELLIDOS = [
    "Pérez García", "Rodríguez López", "González Martínez", "Fernández Ruiz", "López Hernández",
    "Martínez González", "Sánchez Rodríguez", "Jiménez Fernández", "Ruiz Sánchez", "Hernández Jiménez",
    "Moreno Morales", "Muñoz Romero", "Álvarez Torres", "Romero Álvarez", "Torres Muñoz"
]

EMPRESAS_NOMBRES = [
    "Logística Marítima del Caribe",
    "Transportes y Servicios Portuarios SA",
    "Caribbean Shipping Solutions",
    "Dominicana de Carga y Logística",
    "Navieros Profesionales RD",
    "Servicios Portuarios Integrados",
    "Carga Express Internacional",
    "Maritime Solutions Group",
    "Transporte Especializado del Este",
    "Logística Avanzada Santo Domingo"
]

DESCRIPCIONES = [
    "Transporte de contenedores refrigerados con productos perecederos desde Puerto de Haina hacia almacenes centrales de distribución nacional.",
    "Carga y descarga de maquinaria industrial pesada para proyecto de construcción en zona franca de Santiago.",
    "Transporte de materiales de construcción incluyendo cemento, varillas y materiales prefabricados para desarrollo inmobiliario.",
    "Descarga de vehículos nuevos importados desde Asia para distribución en concesionarios autorizados a nivel nacional.",
    "Transporte de combustibles y lubricantes hacia estaciones de servicios en el interior del país bajo estrictas medidas de seguridad.",
    "Carga de productos agrícolas dominicanos (cacao, café, azúcar) destinados a exportación hacia mercados europeos.",
    "Transporte de equipos médicos especializados y suministros hospitalarios para centros de salud públicos y privados.",
    "Descarga de textiles y productos manufacturados para distribución en centros comerciales y tiendas especializadas.",
    "Transporte de insumos químicos para industria farmacéutica nacional bajo protocolos de seguridad industrial.",
    "Carga de productos tecnológicos y electrónicos importados para distribución en el mercado dominicano."
]

def generar_cedula():
    """Genera una cédula dominicana falsa pero válida en formato"""
    return f"{random.randint(100, 999)}-{random.randint(1000000, 9999999)}-{random.randint(0, 9)}"

def generar_placa():
    """Genera una placa dominicana falsa"""
    letra = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    numeros = random.randint(100000, 999999)
    return f"{letra}{numeros}"

def generar_telefono():
    """Genera un teléfono dominicano falso"""
    return f"{random.choice(['809', '829', '849'])}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"

def crear_solicitudes_prueba():
    print(">> Iniciando creacion de solicitudes de prueba...")
    
    # Verificar que existen usuarios, puertos y motivos
    try:
        # Obtener usuarios solicitantes existentes
        solicitantes = User.objects.filter(role='solicitante')
        if not solicitantes.exists():
            print(">> ERROR: No hay usuarios solicitantes. Ejecute primero create_sample_data.py")
            return
        
        # Obtener puertos y motivos
        puertos = Puerto.objects.filter(activo=True)
        motivos = MotivoAcceso.objects.filter(activo=True)
        
        if not puertos.exists() or not motivos.exists():
            print(">> ERROR: No hay puertos o motivos disponibles. Ejecute primero create_sample_data.py")
            return
        
        print(f">> Encontrados {solicitantes.count()} solicitantes, {puertos.count()} puertos, {motivos.count()} motivos")
        
        # Crear solicitudes en diferentes estados
        estados_solicitudes = [
            ('borrador', 8),      # 8 borradores
            ('pendiente', 5),     # 5 pendientes
            ('en_revision', 3),   # 3 en revisión
            ('aprobada', 6),      # 6 aprobadas
            ('rechazada', 2),     # 2 rechazadas
            ('documentos_faltantes', 3),  # 3 con documentos faltantes
        ]
        
        total_creadas = 0
        
        for estado, cantidad in estados_solicitudes:
            print(f"\n>> Creando {cantidad} solicitudes en estado '{estado}'...")
            
            for i in range(cantidad):
                try:
                    # Seleccionar solicitante aleatorio
                    solicitante = random.choice(solicitantes)
                    
                    # Fechas aleatorias (próximas 2 semanas)
                    fecha_base = datetime.now().date() + timedelta(days=random.randint(1, 14))
                    fecha_ingreso = fecha_base
                    fecha_salida = fecha_base + timedelta(days=random.randint(1, 3))
                    
                    # Horas aleatorias
                    hora_ingreso = time(random.randint(6, 14), random.choice([0, 30]))
                    hora_salida = time(random.randint(15, 20), random.choice([0, 30]))
                    
                    # Crear la solicitud
                    solicitud = Solicitud.objects.create(
                        solicitante=solicitante,
                        empresa=solicitante.empresa,
                        puerto_destino=random.choice(puertos),
                        motivo_acceso=random.choice(motivos),
                        fecha_ingreso=fecha_ingreso,
                        hora_ingreso=hora_ingreso,
                        fecha_salida=fecha_salida,
                        hora_salida=hora_salida,
                        descripcion=random.choice(DESCRIPCIONES),
                        estado=estado,
                        prioridad=random.choice(['normal', 'normal', 'normal', 'alta', 'baja'])  # Más normales
                    )
                    
                    # Si no es borrador, agregar fecha de envío
                    if estado != 'borrador':
                        solicitud.enviada_el = datetime.now() - timedelta(days=random.randint(0, 7))
                        solicitud.save()
                    
                    # Agregar personal aleatorio a la solicitud
                    num_personal = random.randint(1, 3)
                    personal_disponible = Personal.objects.all()
                    
                    if personal_disponible.exists():
                        personal_seleccionado = random.sample(
                            list(personal_disponible), 
                            min(num_personal, personal_disponible.count())
                        )
                        
                        roles_operacion = ['Conductor Principal', 'Conductor Auxiliar', 'Operador de Carga', 'Supervisor de Operaciones']
                        
                        for persona in personal_seleccionado:
                            SolicitudPersonal.objects.create(
                                solicitud=solicitud,
                                personal=persona,
                                rol_operacion=random.choice(roles_operacion)
                            )
                    
                    total_creadas += 1
                    print(f"  >> Solicitud #{solicitud.id} creada - {solicitante.get_display_name()} - {solicitud.puerto_destino}")
                    
                except Exception as e:
                    print(f"  >> ERROR creando solicitud: {e}")
                    continue
        
        print(f"\n>> Proceso completado! Se crearon {total_creadas} solicitudes de prueba")
        
        # Mostrar resumen por estado
        print("\n>> Resumen por estado:")
        for estado_cod, estado_nombre in Solicitud.ESTADO_CHOICES:
            count = Solicitud.objects.filter(estado=estado_cod).count()
            if count > 0:
                print(f"  {estado_nombre}: {count} solicitudes")
        
        # Mostrar resumen por solicitante
        print("\n>> Resumen por solicitante:")
        for solicitante in solicitantes:
            count = solicitante.solicitudes.count()
            if count > 0:
                print(f"  {solicitante.get_display_name()}: {count} solicitudes")
        
    except Exception as e:
        print(f">> ERROR general: {e}")
        sys.exit(1)

if __name__ == '__main__':
    crear_solicitudes_prueba()