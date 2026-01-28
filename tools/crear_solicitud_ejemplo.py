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

def crear_solicitud_ejemplo():
    """Crea una solicitud de ejemplo para poder capturar la pantalla de evaluar"""
    
    try:
        # Obtener usuario solicitante
        solicitante = User.objects.get(username='logistica_caribe')
        empresa = solicitante.empresa
        
        # Obtener puerto y motivo
        puerto = Puerto.objects.first()
        motivo = MotivoAcceso.objects.first()
        
        # Crear solicitud
        solicitud = Solicitud.objects.create(
            solicitante=solicitante,
            empresa=empresa,
            puerto_destino=puerto,
            motivo_acceso=motivo,
            fecha_ingreso=datetime.now().date() + timedelta(days=1),
            hora_ingreso=datetime.now().time(),
            fecha_salida=datetime.now().date() + timedelta(days=2),
            hora_salida=datetime.now().time(),
            descripcion="Solicitud de ejemplo para transportar mercancía general al puerto. Operación de carga y descarga programada.",
            estado='pendiente'
        )
        
        # Crear vehículo asociado
        Vehiculo.objects.create(
            solicitud=solicitud,
            placa='A123456',
            tipo_vehiculo='camion',
            conductor_nombre='Juan Pérez',
            conductor_licencia='123456789'
        )
        
        print(f"Solicitud creada exitosamente: ID {solicitud.id}")
        return solicitud.id
        
    except Exception as e:
        print(f"Error creando solicitud: {e}")
        return None

if __name__ == "__main__":
    solicitud_id = crear_solicitud_ejemplo()