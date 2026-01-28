from django.core.management.base import BaseCommand
from evaluacion.models import TipoLicencia, Servicio


class Command(BaseCommand):
    help = 'Crea el tipo de licencia predeterminada "Otros servicios a buques"'

    def handle(self, *args, **options):
        # Verificar si ya existe
        tipo_licencia, created = TipoLicencia.objects.get_or_create(
            nombre='Otros servicios a buques',
            defaults={
                'descripcion': 'Licencia para servicios generales no especificados. '
                               'Permite a la empresa realizar servicios diversos a buques '
                               'en instalaciones portuarias.',
                'activo': True
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f'[OK] Tipo de licencia "{tipo_licencia.nombre}" creado exitosamente'
                )
            )

            # Si hay servicios existentes, preguntar si desea asociarlos
            servicios_count = Servicio.objects.filter(activo=True).count()
            if servicios_count > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f'[INFO] Hay {servicios_count} servicios activos en el sistema. '
                        'Puedes asociarlos manualmente desde el admin.'
                    )
                )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'[INFO] El tipo de licencia "{tipo_licencia.nombre}" ya existe'
                )
            )

        # Mostrar información del tipo de licencia
        servicios_asociados = tipo_licencia.servicios_incluidos.count()
        self.stdout.write(f'\nInformación del tipo de licencia:')
        self.stdout.write(f'  - Nombre: {tipo_licencia.nombre}')
        self.stdout.write(f'  - Activo: {"Si" if tipo_licencia.activo else "No"}')
        self.stdout.write(f'  - Servicios asociados: {servicios_asociados}')
        self.stdout.write(f'  - Empresas asignadas: {tipo_licencia.empresas_asignadas.count()}')
