from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from accounts.decorators import role_required
from solicitudes.models import Puerto, LugarPuerto


@role_required('evaluador', 'supervisor', 'admin_tic')
def gestion_puertos(request):
    """Vista principal para gestión de puertos y lugares"""
    # Búsqueda
    search_query = request.GET.get('search', '')
    puertos = Puerto.objects.all()

    if search_query:
        puertos = puertos.filter(
            Q(nombre__icontains=search_query) |
            Q(codigo__icontains=search_query) |
            Q(ubicacion__icontains=search_query)
        )

    # Paginación
    paginator = Paginator(puertos, 10)
    page_number = request.GET.get('page')
    puertos_page = paginator.get_page(page_number)

    # Estadísticas
    stats = {
        'total_puertos': Puerto.objects.count(),
        'puertos_activos': Puerto.objects.filter(activo=True).count(),
        'total_lugares': LugarPuerto.objects.count(),
        'lugares_activos': LugarPuerto.objects.filter(activo=True).count(),
    }

    context = {
        'puertos': puertos_page,
        'search_query': search_query,
        'stats': stats,
        'titulo': 'Catálogo de Instalaciones Portuarias'
    }

    return render(request, 'evaluacion/gestion_puertos.html', context)


@role_required('evaluador', 'supervisor', 'admin_tic')
def crear_puerto(request):
    """Vista para crear un nuevo puerto"""
    if request.method == 'POST':
        try:
            # Validar datos requeridos
            nombre = request.POST.get('nombre', '').strip()
            codigo = request.POST.get('codigo', '').strip().upper()
            ubicacion = request.POST.get('ubicacion', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()

            if not nombre or not codigo:
                messages.error(request, 'El nombre y código del puerto son obligatorios.')
                return redirect('evaluacion:gestion_puertos')

            # Verificar que no exista
            if Puerto.objects.filter(Q(nombre=nombre) | Q(codigo=codigo)).exists():
                messages.error(request, 'Ya existe un puerto con ese nombre o código.')
                return redirect('evaluacion:gestion_puertos')

            # Crear puerto
            puerto = Puerto.objects.create(
                nombre=nombre,
                codigo=codigo,
                ubicacion=ubicacion,
                descripcion=descripcion,
                activo=True
            )

            messages.success(request, f'Puerto "{puerto.nombre}" creado exitosamente.')
            return redirect('evaluacion:gestion_puertos')

        except Exception as e:
            messages.error(request, f'Error al crear el puerto: {str(e)}')
            return redirect('evaluacion:gestion_puertos')

    return render(request, 'evaluacion/crear_puerto.html', {
        'titulo': 'Crear Nuevo Puerto'
    })


@role_required('evaluador', 'supervisor', 'admin_tic')
def editar_puerto(request, puerto_id):
    """Vista para editar un puerto existente"""
    puerto = get_object_or_404(Puerto, pk=puerto_id)

    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre = request.POST.get('nombre', '').strip()
            codigo = request.POST.get('codigo', '').strip().upper()
            ubicacion = request.POST.get('ubicacion', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            activo = request.POST.get('activo') == 'on'

            if not nombre or not codigo:
                messages.error(request, 'El nombre y código del puerto son obligatorios.')
                return render(request, 'evaluacion/editar_puerto.html', {
                    'puerto': puerto,
                    'titulo': 'Editar Puerto'
                })

            # Verificar duplicados (excluyendo el puerto actual)
            if Puerto.objects.filter(Q(nombre=nombre) | Q(codigo=codigo)).exclude(pk=puerto.pk).exists():
                messages.error(request, 'Ya existe otro puerto con ese nombre o código.')
                return render(request, 'evaluacion/editar_puerto.html', {
                    'puerto': puerto,
                    'titulo': 'Editar Puerto'
                })

            # Actualizar puerto
            puerto.nombre = nombre
            puerto.codigo = codigo
            puerto.ubicacion = ubicacion
            puerto.descripcion = descripcion
            puerto.activo = activo
            puerto.save()

            messages.success(request, f'Puerto "{puerto.nombre}" actualizado exitosamente.')
            return redirect('evaluacion:gestion_puertos')

        except Exception as e:
            messages.error(request, f'Error al actualizar el puerto: {str(e)}')

    context = {
        'puerto': puerto,
        'titulo': 'Editar Puerto'
    }

    return render(request, 'evaluacion/editar_puerto.html', context)


@role_required('evaluador', 'supervisor', 'admin_tic')
def eliminar_puerto(request, puerto_id):
    """Vista para eliminar un puerto"""
    puerto = get_object_or_404(Puerto, pk=puerto_id)

    if request.method == 'POST':
        try:
            # Verificar si tiene lugares asociados
            if puerto.lugares.exists():
                messages.error(request, f'No se puede eliminar el puerto "{puerto.nombre}" porque tiene lugares asociados.')
                return redirect('evaluacion:gestion_puertos')

            nombre_puerto = puerto.nombre
            puerto.delete()
            messages.success(request, f'Puerto "{nombre_puerto}" eliminado exitosamente.')

        except Exception as e:
            messages.error(request, f'Error al eliminar el puerto: {str(e)}')

    return redirect('evaluacion:gestion_puertos')


@role_required('evaluador', 'supervisor', 'admin_tic')
def detalle_puerto(request, puerto_id):
    """Vista para ver detalles de un puerto y sus lugares"""
    puerto = get_object_or_404(Puerto, pk=puerto_id)

    # Búsqueda en lugares
    search_query = request.GET.get('search', '')
    lugares = puerto.lugares.all()

    if search_query:
        lugares = lugares.filter(
            Q(nombre__icontains=search_query) |
            Q(codigo__icontains=search_query) |
            Q(tipo_lugar__icontains=search_query)
        )

    # Paginación
    paginator = Paginator(lugares, 10)
    page_number = request.GET.get('page')
    lugares_page = paginator.get_page(page_number)

    # Estadísticas del puerto
    puerto_stats = {
        'total_lugares': puerto.lugares.count(),
        'lugares_activos': puerto.lugares.filter(activo=True).count(),
        'lugares_inactivos': puerto.lugares.filter(activo=False).count(),
        'tipos_lugar': puerto.lugares.values('tipo_lugar').annotate(count=Count('id'))
    }

    context = {
        'puerto': puerto,
        'lugares': lugares_page,
        'search_query': search_query,
        'puerto_stats': puerto_stats,
        'titulo': f'Puerto: {puerto.nombre}'
    }

    return render(request, 'evaluacion/detalle_puerto.html', context)


@role_required('evaluador', 'supervisor', 'admin_tic')
def crear_lugar(request, puerto_id):
    """Vista para crear un nuevo lugar en un puerto"""
    puerto = get_object_or_404(Puerto, pk=puerto_id)

    if request.method == 'POST':
        try:
            # Validar datos requeridos
            nombre = request.POST.get('nombre', '').strip()
            codigo = request.POST.get('codigo', '').strip().upper()
            tipo_lugar = request.POST.get('tipo_lugar', '')
            descripcion = request.POST.get('descripcion', '').strip()
            capacidad_maxima = request.POST.get('capacidad_maxima')
            observaciones = request.POST.get('observaciones', '').strip()

            if not nombre or not codigo or not tipo_lugar:
                messages.error(request, 'El nombre, código y tipo de lugar son obligatorios.')
                return redirect('evaluacion:detalle_puerto', puerto_id=puerto.pk)

            # Verificar que no exista en el mismo puerto
            if puerto.lugares.filter(Q(nombre=nombre) | Q(codigo=codigo)).exists():
                messages.error(request, 'Ya existe un lugar con ese nombre o código en este puerto.')
                return redirect('evaluacion:detalle_puerto', puerto_id=puerto.pk)

            # Procesar capacidad máxima
            capacidad = None
            if capacidad_maxima and capacidad_maxima.strip():
                try:
                    capacidad = int(capacidad_maxima)
                    if capacidad <= 0:
                        capacidad = None
                except ValueError:
                    capacidad = None

            # Crear lugar
            lugar = LugarPuerto.objects.create(
                puerto=puerto,
                nombre=nombre,
                codigo=codigo,
                tipo_lugar=tipo_lugar,
                descripcion=descripcion,
                capacidad_maxima=capacidad,
                observaciones=observaciones,
                activo=True
            )

            messages.success(request, f'Lugar "{lugar.nombre}" creado exitosamente en {puerto.nombre}.')
            return redirect('evaluacion:detalle_puerto', puerto_id=puerto.pk)

        except Exception as e:
            messages.error(request, f'Error al crear el lugar: {str(e)}')
            return redirect('evaluacion:detalle_puerto', puerto_id=puerto.pk)

    # Obtener opciones de tipo de lugar
    tipos_lugar = LugarPuerto._meta.get_field('tipo_lugar').choices

    context = {
        'puerto': puerto,
        'tipos_lugar': tipos_lugar,
        'titulo': f'Crear Lugar en {puerto.nombre}'
    }

    return render(request, 'evaluacion/crear_lugar.html', context)


@role_required('evaluador', 'supervisor', 'admin_tic')
def editar_lugar(request, lugar_id):
    """Vista para editar un lugar existente"""
    lugar = get_object_or_404(LugarPuerto, pk=lugar_id)
    puerto = lugar.puerto

    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre = request.POST.get('nombre', '').strip()
            codigo = request.POST.get('codigo', '').strip().upper()
            tipo_lugar = request.POST.get('tipo_lugar', '')
            descripcion = request.POST.get('descripcion', '').strip()
            capacidad_maxima = request.POST.get('capacidad_maxima')
            observaciones = request.POST.get('observaciones', '').strip()
            activo = request.POST.get('activo') == 'on'

            if not nombre or not codigo or not tipo_lugar:
                messages.error(request, 'El nombre, código y tipo de lugar son obligatorios.')
                return render(request, 'evaluacion/editar_lugar.html', {
                    'lugar': lugar,
                    'puerto': puerto,
                    'tipos_lugar': LugarPuerto._meta.get_field('tipo_lugar').choices,
                    'titulo': f'Editar Lugar en {puerto.nombre}'
                })

            # Verificar duplicados (excluyendo el lugar actual)
            if puerto.lugares.filter(Q(nombre=nombre) | Q(codigo=codigo)).exclude(pk=lugar.pk).exists():
                messages.error(request, 'Ya existe otro lugar con ese nombre o código en este puerto.')
                return render(request, 'evaluacion/editar_lugar.html', {
                    'lugar': lugar,
                    'puerto': puerto,
                    'tipos_lugar': LugarPuerto._meta.get_field('tipo_lugar').choices,
                    'titulo': f'Editar Lugar en {puerto.nombre}'
                })

            # Procesar capacidad máxima
            capacidad = None
            if capacidad_maxima and capacidad_maxima.strip():
                try:
                    capacidad = int(capacidad_maxima)
                    if capacidad <= 0:
                        capacidad = None
                except ValueError:
                    capacidad = None

            # Actualizar lugar
            lugar.nombre = nombre
            lugar.codigo = codigo
            lugar.tipo_lugar = tipo_lugar
            lugar.descripcion = descripcion
            lugar.capacidad_maxima = capacidad
            lugar.observaciones = observaciones
            lugar.activo = activo
            lugar.save()

            messages.success(request, f'Lugar "{lugar.nombre}" actualizado exitosamente.')
            return redirect('evaluacion:detalle_puerto', puerto_id=puerto.pk)

        except Exception as e:
            messages.error(request, f'Error al actualizar el lugar: {str(e)}')

    context = {
        'lugar': lugar,
        'puerto': puerto,
        'tipos_lugar': LugarPuerto._meta.get_field('tipo_lugar').choices,
        'titulo': f'Editar Lugar en {puerto.nombre}'
    }

    return render(request, 'evaluacion/editar_lugar.html', context)


@role_required('evaluador', 'supervisor', 'admin_tic')
def eliminar_lugar(request, lugar_id):
    """Vista para eliminar un lugar"""
    lugar = get_object_or_404(LugarPuerto, pk=lugar_id)
    puerto = lugar.puerto

    if request.method == 'POST':
        try:
            nombre_lugar = lugar.nombre
            lugar.delete()
            messages.success(request, f'Lugar "{nombre_lugar}" eliminado exitosamente.')

        except Exception as e:
            messages.error(request, f'Error al eliminar el lugar: {str(e)}')

    return redirect('evaluacion:detalle_puerto', puerto_id=puerto.pk)


@login_required
def get_lugares_puerto(request, puerto_id):
    """API endpoint para obtener lugares de un puerto específico"""
    try:
        puerto = get_object_or_404(Puerto, pk=puerto_id)
        lugares = puerto.lugares_activos().values('id', 'nombre', 'codigo', 'tipo_lugar')

        lugares_data = [
            {
                'id': lugar['id'],
                'nombre': lugar['nombre'],
                'codigo': lugar['codigo'],
                'tipo_lugar': lugar['tipo_lugar'],
                'display_name': f"{lugar['nombre']} ({lugar['codigo']})"
            }
            for lugar in lugares
        ]

        return JsonResponse({
            'success': True,
            'lugares': lugares_data
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })