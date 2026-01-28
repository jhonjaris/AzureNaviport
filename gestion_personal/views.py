from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from accounts.decorators import role_required
from .models import Persona, DocumentoPersonal
from .forms import PersonaForm, DocumentoPersonalForm


@login_required
def dashboard(request):
    """Dashboard del módulo de gestión de personal"""
    query = request.GET.get('q', '')
    # Filtrar solo las personas de la empresa del usuario actual
    personas = Persona.objects.filter(activo=True, empresa=request.user)

    if query:
        personas = personas.filter(
            Q(nombre__icontains=query) |
            Q(apellido__icontains=query) |
            Q(cedula__icontains=query)
        )

    personas = personas.order_by('apellido', 'nombre').prefetch_related('documentos')
    total_personas = personas.count()
    # Filtrar documentos pendientes solo de las personas de esta empresa
    documentos_pendientes = DocumentoPersonal.objects.filter(
        estado_validacion='pendiente',
        persona__empresa=request.user
    ).count()

    context = {
        'total_personas': total_personas,
        'personas_recientes': personas,  # Cambiado para mostrar todas las personas (filtradas)
        'documentos_pendientes': documentos_pendientes,
        'query': query,
    }
    return render(request, 'gestion_personal/dashboard.html', context)



@login_required
def detalle_persona(request, persona_id):
    """Ver detalle de una persona"""
    persona = get_object_or_404(Persona, id=persona_id, activo=True, empresa=request.user)
    documentos = persona.documentos.all().order_by('-fecha_subida')

    context = {
        'persona': persona,
        'documentos': documentos,
    }
    return render(request, 'gestion_personal/detalle_persona.html', context)


@login_required
def crear_persona(request):
    """Crear nueva persona - Vista básica"""
    if request.method == 'POST':
        form = PersonaForm(request.POST, empresa=request.user)
        if form.is_valid():
            persona = form.save(commit=False)
            persona.empresa = request.user
            persona.save()
            messages.success(request, 'Persona creada exitosamente.')
            return redirect('gestion_personal:dashboard')
    else:
        form = PersonaForm(empresa=request.user)

    context = {'form': form}
    return render(request, 'gestion_personal/crear_persona.html', context)


@login_required
@require_http_methods(["POST"])
def crear_persona_ajax(request):
    """Crear nueva persona vía AJAX"""
    try:
        # Parsear datos JSON
        data = json.loads(request.body)

        # Crear formulario con los datos Y la empresa
        form = PersonaForm(data, empresa=request.user)

        if form.is_valid():
            persona = form.save(commit=False)
            persona.empresa = request.user
            persona.save()

            return JsonResponse({
                'success': True,
                'message': 'Personal agregado exitosamente',
                'persona': {
                    'id': persona.id,
                    'nombre': persona.nombre,
                    'apellido': persona.apellido,
                    'cedula': persona.cedula or '',
                    'pasaporte': persona.pasaporte or '',
                    'telefono': persona.telefono or '',
                    'email': persona.email or '',
                    'cargo': persona.cargo or '',
                    'licencia_conducir': persona.licencia_conducir or '',
                    'nombre_completo': persona.nombre_completo,
                    'fecha_registro': persona.fecha_registro.strftime('%d/%m/%Y'),
                    'empresa_nombre': persona.empresa.empresa.nombre if persona.empresa and persona.empresa.empresa else 'Sin empresa'
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
def editar_persona(request, persona_id):
    """Editar persona existente"""
    persona = get_object_or_404(Persona, id=persona_id, activo=True, empresa=request.user)

    if request.method == 'POST':
        form = PersonaForm(request.POST, instance=persona, empresa=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Información de {persona.nombre_completo} actualizada exitosamente.')
            return redirect('gestion_personal:detalle_persona', persona_id=persona.id)
        else:
            # Si hay errores, mostrarlos
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')

    context = {'persona': persona}
    return render(request, 'gestion_personal/editar_persona.html', context)


@login_required
def eliminar_persona(request, persona_id):
    """Eliminar persona (marcar como inactiva)"""
    persona = get_object_or_404(Persona, id=persona_id, activo=True, empresa=request.user)

    if request.method == 'POST':
        persona.activo = False
        persona.save()
        messages.success(request, f'Persona {persona.nombre_completo} eliminada exitosamente.')
        return redirect('gestion_personal:dashboard')

    context = {'persona': persona}
    return render(request, 'gestion_personal/confirmar_eliminar_persona.html', context)


@login_required
def buscar_personas_ajax(request):
    """Búsqueda AJAX de personas para autocompletar"""
    query = request.GET.get('q', '')
    personas = []

    if len(query) >= 2:
        personas_queryset = Persona.objects.filter(
            Q(nombre__icontains=query) |
            Q(apellido__icontains=query) |
            Q(cedula__icontains=query),
            activo=True,
            empresa=request.user
        ).order_by('apellido', 'nombre')[:10]

        personas = [{
            'id': persona.id,
            'nombre_completo': persona.nombre_completo,
            'cedula': persona.cedula,
            'email': persona.email or '',
            'telefono': persona.telefono or '',
        } for persona in personas_queryset]

    return JsonResponse({'personas': personas})


@login_required
def listar_personas_ajax(request):
    """Listar todas las personas registradas del usuario (para modal de selección)"""
    try:
        personas_queryset = Persona.objects.filter(
            activo=True,
            empresa=request.user
        ).order_by('apellido', 'nombre')

        personas = [{
            'id': persona.id,
            'nombre': persona.nombre,
            'apellido': persona.apellido,
            'nombre_completo': persona.nombre_completo,
            'cedula': persona.cedula or '',
            'pasaporte': persona.pasaporte or '',
            'email': persona.email or '',
            'telefono': persona.telefono or '',
            'cargo': persona.cargo or '',
            'licencia_conducir': persona.licencia_conducir or '',
        } for persona in personas_queryset]

        return JsonResponse({
            'success': True,
            'personas': personas
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


# === GESTIÓN DE DOCUMENTOS ===

@login_required
def subir_documento_personal(request, persona_id):
    """Subir documento para una persona"""
    persona = get_object_or_404(Persona, id=persona_id, activo=True, empresa=request.user)
    tipo_documento = request.GET.get('tipo', 'cedula')

    if request.method == 'POST':
        form = DocumentoPersonalForm(request.POST, request.FILES)
        form.persona = persona  # Pasar persona para validación
        if form.is_valid():
            documento = form.save(commit=False)
            documento.persona = persona
            documento.subido_por = request.user
            documento.save()
            messages.success(request, f'{documento.get_tipo_documento_display()} subido exitosamente.')
            return redirect('gestion_personal:detalle_persona', persona_id=persona.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        # Pre-seleccionar el tipo de documento del parámetro GET
        initial_data = {'tipo_documento': tipo_documento}
        form = DocumentoPersonalForm(initial=initial_data)
        form.persona = persona  # Pasar persona para validación

    context = {
        'persona': persona,
        'form': form,
        'tipo_documento': tipo_documento
    }
    return render(request, 'gestion_personal/subir_documento.html', context)


@login_required
def editar_documento_personal(request, documento_id):
    """Editar documento personal - Vista básica"""
    documento = get_object_or_404(DocumentoPersonal, id=documento_id)

    if request.method == 'POST':
        # TODO: Implementar edición de documento
        messages.success(request, 'Documento actualizado exitosamente.')
        return redirect('gestion_personal:detalle_persona', persona_id=documento.persona.id)

    context = {'documento': documento}
    return render(request, 'gestion_personal/editar_documento.html', context)


@login_required
def eliminar_documento_personal(request, documento_id):
    """Eliminar documento personal"""
    documento = get_object_or_404(DocumentoPersonal, id=documento_id)
    persona_id = documento.persona.id

    if request.method == 'POST':
        documento.delete()
        messages.success(request, 'Documento eliminado exitosamente.')
        return redirect('gestion_personal:detalle_persona', persona_id=persona_id)

    context = {'documento': documento}
    return render(request, 'gestion_personal/confirmar_eliminar_documento.html', context)


@login_required
@role_required('evaluador', 'supervisor', 'admin_tic')
def validar_documento_personal(request, documento_id):
    """Validar documento personal - Solo evaluadores"""
    documento = get_object_or_404(DocumentoPersonal, id=documento_id)

    if request.method == 'POST':
        # TODO: Implementar validación de documento
        messages.success(request, 'Estado de documento actualizado.')
        return redirect('gestion_personal:detalle_persona', persona_id=documento.persona.id)

    context = {'documento': documento}
    return render(request, 'gestion_personal/validar_documento.html', context)


@login_required
def descargar_documento_personal(request, documento_id):
    """Descargar archivo de documento personal"""
    import os
    from django.http import FileResponse
    from django.conf import settings

    documento = get_object_or_404(DocumentoPersonal, id=documento_id)

    if not documento.archivo:
        messages.error(request, 'No hay archivo asociado a este documento.')
        return redirect('gestion_personal:detalle_persona', persona_id=documento.persona.id)

    # Obtener la ruta completa del archivo
    file_path = documento.archivo.path

    if not os.path.exists(file_path):
        messages.error(request, 'El archivo no existe en el servidor.')
        return redirect('gestion_personal:detalle_persona', persona_id=documento.persona.id)

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
        safe_filename = f"{documento.persona.nombre}_{documento.persona.apellido}_{documento.get_tipo_documento_display()}{file_extension}"

        response = FileResponse(
            open(file_path, 'rb'),
            content_type=content_type,
            as_attachment=False  # Para vista previa en navegador
        )
        response['Content-Disposition'] = f'inline; filename="{safe_filename}"'
        return response

    except Exception as e:
        messages.error(request, f'Error al abrir el archivo: {str(e)}')
        return redirect('gestion_personal:detalle_persona', persona_id=documento.persona.id)