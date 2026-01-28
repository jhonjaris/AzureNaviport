#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naviport.settings')
django.setup()

from accounts.models import User, Empresa
from solicitudes.models import Solicitud, Puerto, MotivoAcceso, Vehiculo
from datetime import datetime, timedelta

def verificar_y_crear_solicitud():
    """Verifica usuarios existentes y crea solicitud"""
    
    print("=== Usuarios existentes ===")
    usuarios = User.objects.all()
    for user in usuarios:
        print(f"- {user.username} ({user.role}) - Empresa: {user.empresa}")
    
    print("\n=== Empresas existentes ===")
    empresas = Empresa.objects.all()
    for empresa in empresas:
        print(f"- {empresa.nombre}")
    
    # Buscar un solicitante
    solicitantes = User.objects.filter(role='solicitante')
    if solicitantes.exists():
        solicitante = solicitantes.first()
        print(f"\nUsando solicitante: {solicitante.username}")
        
        try:
            # Obtener puerto y motivo
            puerto = Puerto.objects.first()
            motivo = MotivoAcceso.objects.first()
            
            print(f"Puerto: {puerto.nombre if puerto else 'No hay puertos'}")
            print(f"Motivo: {motivo.nombre if motivo else 'No hay motivos'}")
            
            if puerto and motivo:
                # Crear solicitud
                solicitud = Solicitud.objects.create(
                    solicitante=solicitante,
                    empresa=solicitante.empresa,
                    puerto_destino=puerto,
                    motivo_acceso=motivo,
                    fecha_ingreso=datetime.now().date() + timedelta(days=1),
                    hora_ingreso=datetime.now().time(),
                    fecha_salida=datetime.now().date() + timedelta(days=2),
                    hora_salida=datetime.now().time(),
                    descripcion="Solicitud de ejemplo para transportar mercancía general al puerto. Operación de carga y descarga programada con documentación completa.",
                    estado='pendiente'
                )
                
                # Crear vehículo asociado
                Vehiculo.objects.create(
                    solicitud=solicitud,
                    placa='A123456',
                    tipo_vehiculo='camion',
                    conductor_nombre='Juan Pérez Conductor',
                    conductor_licencia='123456789'
                )
                
                print(f"\nSolicitud creada exitosamente: ID {solicitud.id}")
                print(f"Estado: {solicitud.estado}")
                return solicitud.id
            else:
                print("No hay puertos o motivos disponibles")
                return None
                
        except Exception as e:
            print(f"Error creando solicitud: {e}")
            return None
    else:
        print("No hay usuarios solicitantes disponibles")
        return None

if __name__ == "__main__":
    verificar_y_crear_solicitud()