"""
Script para verificar autorizaciones en la base de datos
"""
import os
import sys
import django

# Configurar la codificación UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naviport.settings')
django.setup()

from control_acceso.models import Autorizacion
from solicitudes.models import Solicitud

print("\n" + "="*80)
print("VERIFICACION DE AUTORIZACIONES")
print("="*80)

# Verificar autorizaciones existentes
autorizaciones = Autorizacion.objects.all()
print(f"\nTotal de autorizaciones: {autorizaciones.count()}")

if autorizaciones.exists():
    print("\nAutorizaciones encontradas:")
    print("-" * 80)
    for aut in autorizaciones:
        print(f"  - Codigo: {aut.codigo}")
        print(f"    Empresa: {aut.empresa_nombre}")
        print(f"    Estado: {aut.get_estado_display()}")
        print(f"    Valida desde: {aut.valida_desde}")
        print(f"    Valida hasta: {aut.valida_hasta}")
        print(f"    Creada: {aut.creada_el}")
        print("-" * 80)
else:
    print("\nNo hay autorizaciones en la base de datos")

# Verificar solicitudes aprobadas
print("\n" + "="*80)
print("VERIFICACION DE SOLICITUDES APROBADAS")
print("="*80)

solicitudes_aprobadas = Solicitud.objects.filter(estado='aprobada')
print(f"\nTotal de solicitudes aprobadas: {solicitudes_aprobadas.count()}")

if solicitudes_aprobadas.exists():
    print("\nSolicitudes aprobadas encontradas:")
    print("-" * 80)
    for sol in solicitudes_aprobadas:
        tiene_autorizacion = hasattr(sol, 'autorizacion') and sol.autorizacion is not None
        print(f"  - Solicitud ID: {sol.id}")
        print(f"    Codigo: {sol.codigo if sol.codigo else 'N/A'}")
        print(f"    Empresa: {sol.empresa.nombre}")
        print(f"    Puerto: {sol.puerto_destino.nombre}")
        print(f"    Estado: {sol.get_estado_display()}")
        print(f"    Tiene autorizacion: {'SI' if tiene_autorizacion else 'NO'}")
        if tiene_autorizacion:
            print(f"    Codigo autorizacion: {sol.autorizacion.codigo}")
        print("-" * 80)
else:
    print("\nNo hay solicitudes aprobadas")

# Verificar todas las solicitudes por estado
print("\n" + "="*80)
print("RESUMEN DE SOLICITUDES POR ESTADO")
print("="*80)
from django.db.models import Count

resumen = Solicitud.objects.values('estado').annotate(total=Count('id')).order_by('-total')
for item in resumen:
    print(f"  - {item['estado']}: {item['total']}")

print("\n" + "="*80)
