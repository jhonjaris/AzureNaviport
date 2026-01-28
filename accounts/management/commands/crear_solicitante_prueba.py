from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from accounts.models import User, Empresa, NotificacionEmpresa
from evaluacion.models import ConfiguracionEvaluacion

class Command(BaseCommand):
    help = 'Crea un solicitante de prueba con empresa y fechas de expiración para testing de notificaciones'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='test_solicitante', help='Username del solicitante')
        parser.add_argument('--dias-vuce', type=int, default=25, help='Días hasta expiración VUCE')
        parser.add_argument('--dias-contrato', type=int, default=45, help='Días hasta expiración contrato')

    def handle(self, *args, **options):
        username = options['username']
        dias_vuce = options['dias_vuce']
        dias_contrato = options['dias_contrato']
        
        # Crear usuario solicitante
        import random
        cedula_random = f'001-{random.randint(1000000, 9999999)}-{random.randint(1, 9)}'
        
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': 'Usuario',
                'last_name': 'Prueba',
                'email': f'{username}@test.com',
                'cedula_rnc': cedula_random,
                'role': 'solicitante',
                'activo': True
            }
        )
        
        if created:
            user.set_password('test123')
            user.save()
            self.stdout.write(f'[OK] Usuario creado: {username}/test123')
        else:
            self.stdout.write(f'[INFO] Usuario ya existe: {username}')
        
        # Crear empresa
        fecha_vuce = timezone.now().date() + timedelta(days=dias_vuce)
        fecha_contrato = timezone.now().date() + timedelta(days=dias_contrato)
        rnc_random = f'101-{random.randint(10000, 99999)}-{random.randint(1, 9)}'
        
        empresa, created = Empresa.objects.get_or_create(
            rnc=rnc_random,
            defaults={
                'nombre': f'Empresa de Prueba {username}',
                'email': f'empresa_{username}@test.com',
                'telefono': '809-123-4567',
                'representante_legal': user,
                'numero_licencia': f'LIC-{username}-2024',
                'fecha_expedicion_licencia': timezone.now().date() - timedelta(days=365),
                'fecha_expiracion_licencia': fecha_vuce,
                'fecha_expiracion_contrato': fecha_contrato,
                'activa': True,
                'verificada': True
            }
        )
        
        if created:
            self.stdout.write(f'[OK] Empresa creada: {empresa.nombre}')
        else:
            # Actualizar fechas si ya existe
            empresa.fecha_expiracion_licencia = fecha_vuce
            empresa.fecha_expiracion_contrato = fecha_contrato
            empresa.representante_legal = user
            empresa.save()
            self.stdout.write(f'[UPDATE] Empresa actualizada: {empresa.nombre}')
        
        # Asegurar configuración existe
        config = ConfiguracionEvaluacion.get_configuracion()
        self.stdout.write(f'[CONFIG] Critico={config.dias_preaviso_critico}d, Advertencia={config.dias_preaviso_advertencia}d, Informativo={config.dias_preaviso_informativo}d')
        
        # Limpiar notificaciones anteriores para testing
        NotificacionEmpresa.objects.filter(usuario=user).delete()
        
        # Generar notificaciones
        notificaciones = NotificacionEmpresa.crear_notificacion_expiracion(empresa, user, config)
        
        self.stdout.write(f'[NOTIF] Notificaciones generadas: {len(notificaciones)}')
        for notif in notificaciones:
            self.stdout.write(f'   - {notif.get_tipo_display()}: {notif.titulo}')
        
        self.stdout.write('\n[INFO] Informacion de prueba:')
        self.stdout.write(f'   Usuario: {username}/test123')
        self.stdout.write(f'   Empresa: {empresa.nombre}')
        self.stdout.write(f'   VUCE expira: {fecha_vuce} ({dias_vuce} dias)')
        self.stdout.write(f'   Contrato expira: {fecha_contrato} ({dias_contrato} dias)')
        self.stdout.write(f'   URL: http://127.0.0.1:8002/solicitudes/dashboard/')
        
        self.stdout.write('\n[SUCCESS] Solicitante de prueba listo para testing!')