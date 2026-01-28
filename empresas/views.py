from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from accounts.decorators import role_required
from .models import Personal, EmpresaServicio, PersonalEmpresa, Servicio
from .forms import EmpresaServicioForm, ServicioForm
import json


@require_http_methods(["GET"])
def buscar_personal(request):
    """API endpoint para buscar personal por cédula o nombre"""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 3:
        return JsonResponse({
            'success': False,
            'message': 'Debe proporcionar al menos 3 caracteres para la búsqueda'
        })
    
    try:
        personal = Personal.objects.filter(
            Q(cedula__icontains=query) | Q(nombre__icontains=query),
            activo=True
        )[:10]  # Limitar a 10 resultados
        
        resultados = []
        for p in personal:
            resultados.append({
                'id': p.id,
                'nombre': p.nombre,
                'cedula': p.cedula,
                'cargo': p.cargo,
                'licencia_conducir': p.licencia_conducir,
                'telefono': p.telefono,
            })
        
        return JsonResponse({
            'success': True,
            'resultados': resultados
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error en la búsqueda: {str(e)}'
        })


@csrf_exempt
@require_http_methods(["POST"])
def crear_personal(request):
    """API endpoint para crear nuevo personal"""
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        if not data.get('nombre') or not data.get('cedula'):
            return JsonResponse({
                'success': False,
                'message': 'Nombre y cédula son obligatorios'
            })
        
        # Verificar si ya existe
        if Personal.objects.filter(cedula=data['cedula']).exists():
            return JsonResponse({
                'success': False,
                'message': 'Ya existe una persona con esta cédula'
            })
        
        # Crear el personal
        personal = Personal.objects.create(
            nombre=data['nombre'],
            cedula=data['cedula'],
            cargo=data.get('cargo', ''),
            licencia_conducir=data.get('licencia_conducir', ''),
            telefono=data.get('telefono', ''),
        )
        
        return JsonResponse({
            'success': True,
            'personal': {
                'id': personal.id,
                'nombre': personal.nombre,
                'cedula': personal.cedula,
                'cargo': personal.cargo,
                'licencia_conducir': personal.licencia_conducir,
                'telefono': personal.telefono,
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Formato JSON inválido'
        })
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'message': f'Error de validación: {str(e)}'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al crear el personal: {str(e)}'
        })


@require_http_methods(["GET"])
def detalle_personal(request, personal_id):
    """API endpoint para obtener detalles de una persona"""
    try:
        personal = Personal.objects.get(id=personal_id, activo=True)
        
        return JsonResponse({
            'success': True,
            'personal': {
                'id': personal.id,
                'nombre': personal.nombre,
                'cedula': personal.cedula,
                'cargo': personal.cargo,
                'licencia_conducir': personal.licencia_conducir,
                'telefono': personal.telefono,
            }
        })
        
    except Personal.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Personal no encontrado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })


# CRUD de Empresas de Servicio
@login_required
@role_required('evaluador', 'supervisor')
def listar_empresas(request):
    """Vista para listar empresas de servicio"""
    empresas_list = EmpresaServicio.objects.all().order_by('nombre')
    
    # Filtros
    search = request.GET.get('search', '')
    estado = request.GET.get('estado', 'all')
    
    if search:
        empresas_list = empresas_list.filter(
            Q(nombre__icontains=search) | 
            Q(rnc__icontains=search) |
            Q(numero_licencia__icontains=search)
        )
    
    if estado == 'activas':
        empresas_list = empresas_list.filter(activa=True)
    elif estado == 'inactivas':
        empresas_list = empresas_list.filter(activa=False)
    elif estado == 'vencidas':
        from datetime import date
        empresas_list = empresas_list.filter(fecha_expiracion_licencia__lt=date.today())
    
    # Paginación
    paginator = Paginator(empresas_list, 15)
    page_number = request.GET.get('page')
    empresas = paginator.get_page(page_number)
    
    context = {
        'empresas': empresas,
        'search': search,
        'estado': estado,
        'total_empresas': EmpresaServicio.objects.count(),
        'empresas_activas': EmpresaServicio.objects.filter(activa=True).count(),
    }
    
    return render(request, 'empresas/listar_empresas.html', context)


@login_required
@role_required('evaluador', 'supervisor')
def registrar_empresa(request):
    """Vista para registrar nueva empresa"""
    if request.method == 'POST':
        form = EmpresaServicioForm(request.POST)
        if form.is_valid():
            empresa = form.save()
            messages.success(request, f'¡Empresa "{empresa.nombre}" registrada exitosamente!')
            return redirect('empresas:listar_empresas')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = EmpresaServicioForm()
    
    context = {
        'form': form,
        'servicios': Servicio.objects.filter(activo=True),
        'title': 'Registrar Nueva Empresa'
    }
    
    return render(request, 'empresas/registrar_empresa.html', context)


@login_required
@role_required('evaluador', 'supervisor')
def editar_empresa(request, empresa_id):
    """Vista para editar empresa existente"""
    empresa = get_object_or_404(EmpresaServicio, id=empresa_id)
    
    if request.method == 'POST':
        form = EmpresaServicioForm(request.POST, instance=empresa)
        if form.is_valid():
            form.save()
            messages.success(request, f'¡Empresa "{empresa.nombre}" actualizada exitosamente!')
            return redirect('empresas:listar_empresas')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = EmpresaServicioForm(instance=empresa)
    
    context = {
        'form': form,
        'empresa': empresa,
        'servicios': Servicio.objects.filter(activo=True),
        'title': f'Editar Empresa: {empresa.nombre}'
    }
    
    return render(request, 'empresas/registrar_empresa.html', context)


@login_required
@role_required('evaluador', 'supervisor')
def detalle_empresa(request, empresa_id):
    """Vista para ver detalles de empresa"""
    empresa = get_object_or_404(EmpresaServicio, id=empresa_id)
    
    context = {
        'empresa': empresa,
    }
    
    return render(request, 'empresas/detalle_empresa.html', context)


# CRUD de Servicios
@login_required
@role_required('evaluador', 'supervisor')
def listar_servicios(request):
    """Vista para listar servicios"""
    servicios_list = Servicio.objects.all().order_by('nombre')
    
    search = request.GET.get('search', '')
    if search:
        servicios_list = servicios_list.filter(nombre__icontains=search)
    
    paginator = Paginator(servicios_list, 20)
    page_number = request.GET.get('page')
    servicios = paginator.get_page(page_number)
    
    context = {
        'servicios': servicios,
        'search': search,
    }
    
    return render(request, 'empresas/listar_servicios.html', context)


@login_required
@role_required('evaluador', 'supervisor')
def crear_servicio(request):
    """Vista para crear nuevo servicio"""
    if request.method == 'POST':
        form = ServicioForm(request.POST)
        if form.is_valid():
            servicio = form.save()
            messages.success(request, f'¡Servicio "{servicio.nombre}" creado exitosamente!')
            return redirect('empresas:listar_servicios')
    else:
        form = ServicioForm()
    
    return render(request, 'empresas/crear_servicio.html', {'form': form})


@login_required
@role_required('evaluador', 'supervisor')
def editar_servicio(request, servicio_id):
    """Vista para editar servicio existente"""
    servicio = get_object_or_404(Servicio, id=servicio_id)
    
    if request.method == 'POST':
        form = ServicioForm(request.POST, instance=servicio)
        if form.is_valid():
            form.save()
            messages.success(request, f'¡Servicio "{servicio.nombre}" actualizado exitosamente!')
            return redirect('empresas:listar_servicios')
    else:
        form = ServicioForm(instance=servicio)
    
    return render(request, 'empresas/crear_servicio.html', {'form': form, 'servicio': servicio})
