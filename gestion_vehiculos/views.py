from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, FileResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import os
from django.conf import settings
from accounts.decorators import role_required
from .models import Vehiculo, DocumentoVehiculo
from .forms import VehiculoForm, DocumentoVehiculoForm


@login_required
def dashboard(request):
    """Dashboard del módulo de gestión de vehículos"""
    query = request.GET.get('q', '')
    # Filtrar solo los vehículos de la empresa del usuario actual
    vehiculos = Vehiculo.objects.filter(activo=True, empresa_propietaria=request.user)

    if query:
        vehiculos = vehiculos.filter(
            Q(placa__icontains=query) |
            Q(marca__icontains=query) |
            Q(modelo__icontains=query) |
            Q(color__icontains=query)
        )

    vehiculos = vehiculos.order_by('placa').prefetch_related('documentos')
    total_vehiculos = vehiculos.count()
    # Filtrar documentos pendientes solo de los vehículos de esta empresa
    documentos_pendientes = DocumentoVehiculo.objects.filter(
        estado_validacion='pendiente',
        vehiculo__empresa_propietaria=request.user
    ).count()

    context = {
        'total_vehiculos': total_vehiculos,
        'vehiculos_recientes': vehiculos,
        'documentos_pendientes': documentos_pendientes,
        'query': query,
    }
    return render(request, 'gestion_vehiculos/dashboard.html', context)


@login_required
def detalle_vehiculo(request, vehiculo_id):
    """Ver detalle de un vehículo"""
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, activo=True, empresa_propietaria=request.user)
    documentos = vehiculo.documentos.all().order_by('-fecha_subida')

    context = {
        'vehiculo': vehiculo,
        'documentos': documentos,
    }
    return render(request, 'gestion_vehiculos/detalle_vehiculo.html', context)


@login_required
def crear_vehiculo(request):
    """Crear nuevo vehículo - Vista básica"""
    if request.method == 'POST':
        form = VehiculoForm(request.POST)
        if form.is_valid():
            vehiculo = form.save(commit=False)
            vehiculo.empresa_propietaria = request.user
            vehiculo.save()
            messages.success(request, 'Vehículo creado exitosamente.')
            return redirect('gestion_vehiculos:dashboard')
    else:
        form = VehiculoForm()

    context = {'form': form}
    return render(request, 'gestion_vehiculos/crear_vehiculo.html', context)


@login_required
@require_http_methods(["POST"])
def crear_vehiculo_ajax(request):
    """Crear nuevo vehículo vía AJAX"""
    try:
        # Parsear datos JSON
        data = json.loads(request.body)

        # Crear formulario con los datos
        form = VehiculoForm(data)

        if form.is_valid():
            vehiculo = form.save(commit=False)
            vehiculo.empresa_propietaria = request.user
            vehiculo.save()

            return JsonResponse({
                'success': True,
                'message': 'Vehículo agregado exitosamente',
                'vehiculo': {
                    'id': vehiculo.id,
                    'placa': vehiculo.placa,
                    'marca': vehiculo.marca,
                    'modelo': vehiculo.modelo,
                    'ano': vehiculo.ano,
                    'color': vehiculo.color,
                    'tipo_vehiculo': vehiculo.get_tipo_vehiculo_display(),
                    'descripcion_completa': vehiculo.descripcion_completa,
                    'fecha_registro': vehiculo.fecha_registro.strftime('%d/%m/%Y'),
                    'empresa_nombre': vehiculo.empresa_propietaria.empresa.nombre if vehiculo.empresa_propietaria and vehiculo.empresa_propietaria.empresa else 'Sin empresa'
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Error en los datos proporcionados',
                'errors': form.errors
            }, status=400)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error interno: {str(e)}'
        }, status=500)


@login_required
def editar_vehiculo(request, vehiculo_id):
    """Editar vehículo existente"""
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, activo=True, empresa_propietaria=request.user)

    if request.method == 'POST':
        form = VehiculoForm(request.POST, instance=vehiculo)
        if form.is_valid():
            form.save()
            messages.success(request, f'Información del vehículo {vehiculo.placa} actualizada exitosamente.')
            return redirect('gestion_vehiculos:detalle_vehiculo', vehiculo_id=vehiculo.id)
        else:
            # Si hay errores, mostrarlos
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')

    context = {'vehiculo': vehiculo}
    return render(request, 'gestion_vehiculos/editar_vehiculo.html', context)


@login_required
def eliminar_vehiculo(request, vehiculo_id):
    """Eliminar vehículo (marcar como inactivo) con motivo"""
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, activo=True, empresa_propietaria=request.user)

    if request.method == 'POST':
        motivo = request.POST.get('motivo', '').strip()
        if not motivo:
            motivo = 'Eliminado por el usuario'
        vehiculo.inhabilitar(request.user, motivo)
        messages.success(request, f'Vehículo {vehiculo.placa} inhabilitado exitosamente.')
        return redirect('gestion_vehiculos:dashboard')

    context = {'vehiculo': vehiculo}
    return render(request, 'gestion_vehiculos/confirmar_eliminar_vehiculo.html', context)


@login_required
@require_http_methods(["POST"])
def toggle_vehiculo_activo(request, vehiculo_id):
    """Toggle activo/inactivo de vehículo vía AJAX"""
    try:
        vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, empresa_propietaria=request.user)
        data = json.loads(request.body) if request.body else {}

        if vehiculo.activo:
            # Inhabilitar
            motivo = data.get('motivo', 'Inhabilitado por el usuario')
            vehiculo.inhabilitar(request.user, motivo)
            return JsonResponse({
                'success': True,
                'message': f'Vehículo {vehiculo.placa} inhabilitado exitosamente.',
                'activo': False,
                'fecha_inhabilitacion': vehiculo.fecha_inhabilitacion.strftime('%d/%m/%Y %H:%M') if vehiculo.fecha_inhabilitacion else None
            })
        else:
            # Reactivar
            vehiculo.reactivar()
            return JsonResponse({
                'success': True,
                'message': f'Vehículo {vehiculo.placa} reactivado exitosamente.',
                'activo': True
            })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
def vehiculos_inhabilitados(request):
    """Listar vehículos inhabilitados de la empresa"""
    query = request.GET.get('q', '')
    vehiculos = Vehiculo.objects.filter(activo=False, empresa_propietaria=request.user)

    if query:
        vehiculos = vehiculos.filter(
            Q(placa__icontains=query) |
            Q(marca__icontains=query) |
            Q(modelo__icontains=query) |
            Q(color__icontains=query) |
            Q(motivo_inhabilitacion__icontains=query)
        )

    vehiculos = vehiculos.order_by('-fecha_inhabilitacion')
    total_inhabilitados = vehiculos.count()

    context = {
        'vehiculos': vehiculos,
        'total_inhabilitados': total_inhabilitados,
        'query': query,
    }
    return render(request, 'gestion_vehiculos/vehiculos_inhabilitados.html', context)


@login_required
def reactivar_vehiculo(request, vehiculo_id):
    """Reactivar un vehículo inhabilitado"""
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, activo=False, empresa_propietaria=request.user)

    if request.method == 'POST':
        vehiculo.reactivar()
        messages.success(request, f'Vehículo {vehiculo.placa} reactivado exitosamente.')
        return redirect('gestion_vehiculos:dashboard')

    context = {'vehiculo': vehiculo}
    return render(request, 'gestion_vehiculos/confirmar_reactivar_vehiculo.html', context)


@login_required
def buscar_vehiculos_ajax(request):
    """Búsqueda AJAX de vehículos para autocompletar"""
    query = request.GET.get('q', '')
    vehiculos = []

    if len(query) >= 2:
        vehiculos_queryset = Vehiculo.objects.filter(
            Q(placa__icontains=query) |
            Q(marca__icontains=query) |
            Q(modelo__icontains=query) |
            Q(color__icontains=query),
            activo=True,
            empresa_propietaria=request.user
        ).order_by('placa')[:10]

        vehiculos = [{
            'id': vehiculo.id,
            'placa': vehiculo.placa,
            'descripcion_completa': vehiculo.descripcion_completa,
            'marca': vehiculo.marca,
            'modelo': vehiculo.modelo,
            'ano': vehiculo.ano,
            'color': vehiculo.color,
        } for vehiculo in vehiculos_queryset]

    return JsonResponse({'vehiculos': vehiculos})


# === GESTIÓN DE DOCUMENTOS ===

@login_required
def subir_documento_vehiculo(request, vehiculo_id):
    """Subir documento para un vehículo"""
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, activo=True, empresa_propietaria=request.user)
    tipo_documento = request.GET.get('tipo', 'matricula')

    if request.method == 'POST':
        form = DocumentoVehiculoForm(request.POST, request.FILES)
        form.vehiculo = vehiculo  # Pasar vehículo para validación
        if form.is_valid():
            documento = form.save(commit=False)
            documento.vehiculo = vehiculo
            documento.subido_por = request.user
            documento.save()
            messages.success(request, f'{documento.get_tipo_documento_display()} subido exitosamente.')
            return redirect('gestion_vehiculos:detalle_vehiculo', vehiculo_id=vehiculo.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        # Pre-seleccionar el tipo de documento del parámetro GET
        initial_data = {'tipo_documento': tipo_documento}
        form = DocumentoVehiculoForm(initial=initial_data)
        form.vehiculo = vehiculo  # Pasar vehículo para validación

    context = {
        'vehiculo': vehiculo,
        'form': form,
        'tipo_documento': tipo_documento
    }
    return render(request, 'gestion_vehiculos/subir_documento.html', context)


@login_required
def editar_documento_vehiculo(request, documento_id):
    """Editar documento de vehículo"""
    documento = get_object_or_404(DocumentoVehiculo, id=documento_id)

    # Verificar que el usuario tenga acceso a este documento (mismo propietario del vehículo)
    if documento.vehiculo.empresa_propietaria != request.user:
        messages.error(request, 'No tienes permisos para editar este documento.')
        return redirect('gestion_vehiculos:dashboard')

    if request.method == 'POST':
        try:
            # Actualizar campos de texto si se proporcionan
            numero_documento = request.POST.get('numero_documento', '').strip()
            if numero_documento:
                documento.numero_documento = numero_documento

            fecha_vencimiento = request.POST.get('fecha_vencimiento')
            if fecha_vencimiento:
                documento.fecha_vencimiento = fecha_vencimiento
            elif fecha_vencimiento == '':  # Si se envía vacío, limpiar la fecha
                documento.fecha_vencimiento = None

            # Manejar archivo nuevo si se subió uno
            nuevo_archivo = request.FILES.get('nuevo_archivo')
            if nuevo_archivo:
                # Validar tamaño (5MB)
                if nuevo_archivo.size > 5 * 1024 * 1024:
                    messages.error(request, 'El archivo es demasiado grande. Máximo 5MB permitido.')
                    return render(request, 'gestion_vehiculos/editar_documento.html', {'documento': documento})

                # Validar extensión
                import os
                file_extension = os.path.splitext(nuevo_archivo.name)[1].lower()
                allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
                if file_extension not in allowed_extensions:
                    messages.error(request, 'Formato de archivo no permitido. Use PDF, JPG o PNG.')
                    return render(request, 'gestion_vehiculos/editar_documento.html', {'documento': documento})

                # Eliminar archivo anterior si existe
                if documento.archivo:
                    old_file_path = documento.archivo.path
                    if os.path.exists(old_file_path):
                        try:
                            os.remove(old_file_path)
                        except OSError:
                            pass  # No detener el proceso si no se puede eliminar el archivo anterior

                # Asignar nuevo archivo
                documento.archivo = nuevo_archivo

                # Resetear estado de validación cuando se cambia el archivo
                documento.estado_validacion = 'pendiente'
                documento.validado_por = None
                documento.fecha_validacion = None
                documento.comentarios_validacion = None

            documento.save()
            messages.success(request, f'{documento.get_tipo_documento_display()} actualizado exitosamente.')
            return redirect('gestion_vehiculos:detalle_vehiculo', vehiculo_id=documento.vehiculo.id)

        except Exception as e:
            messages.error(request, f'Error al actualizar el documento: {str(e)}')
            return render(request, 'gestion_vehiculos/editar_documento.html', {'documento': documento})

    context = {'documento': documento}
    return render(request, 'gestion_vehiculos/editar_documento.html', context)


@login_required
def eliminar_documento_vehiculo(request, documento_id):
    """Eliminar documento de vehículo"""
    documento = get_object_or_404(DocumentoVehiculo, id=documento_id)
    vehiculo_id = documento.vehiculo.id

    if request.method == 'POST':
        documento.delete()
        messages.success(request, 'Documento eliminado exitosamente.')
        return redirect('gestion_vehiculos:detalle_vehiculo', vehiculo_id=vehiculo_id)

    context = {'documento': documento}
    return render(request, 'gestion_vehiculos/confirmar_eliminar_documento.html', context)


@login_required
@role_required('evaluador', 'supervisor', 'admin_tic')
def validar_documento_vehiculo(request, documento_id):
    """Validar documento de vehículo - Solo evaluadores"""
    documento = get_object_or_404(DocumentoVehiculo, id=documento_id)

    if request.method == 'POST':
        # TODO: Implementar validación de documento
        messages.success(request, 'Estado de documento actualizado.')
        return redirect('gestion_vehiculos:detalle_vehiculo', vehiculo_id=documento.vehiculo.id)

    context = {'documento': documento}
    return render(request, 'gestion_vehiculos/validar_documento.html', context)


@login_required
def descargar_documento_vehiculo(request, documento_id):
    """Descargar archivo de documento de vehículo"""
    documento = get_object_or_404(DocumentoVehiculo, id=documento_id)

    if not documento.archivo:
        messages.error(request, 'No hay archivo asociado a este documento.')
        return redirect('gestion_vehiculos:detalle_vehiculo', vehiculo_id=documento.vehiculo.id)

    # Obtener la ruta completa del archivo
    file_path = documento.archivo.path

    if not os.path.exists(file_path):
        messages.error(request, 'El archivo no existe en el servidor.')
        return redirect('gestion_vehiculos:detalle_vehiculo', vehiculo_id=documento.vehiculo.id)

    try:
        # Determinar el tipo de contenido
        file_extension = os.path.splitext(file_path)[1].lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
        }
        content_type = content_types.get(file_extension, 'application/octet-stream')

        # Crear nombre de archivo descriptivo
        safe_filename = f"{documento.vehiculo.placa}_{documento.get_tipo_documento_display()}{file_extension}"

        response = FileResponse(
            open(file_path, 'rb'),
            content_type=content_type,
            as_attachment=False  # Para vista previa en navegador
        )
        response['Content-Disposition'] = f'inline; filename="{safe_filename}"'
        return response

    except Exception as e:
        messages.error(request, f'Error al abrir el archivo: {str(e)}')
        return redirect('gestion_vehiculos:detalle_vehiculo', vehiculo_id=documento.vehiculo.id)