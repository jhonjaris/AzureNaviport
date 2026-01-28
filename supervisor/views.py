from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import Http404
from django.views.decorators.http import require_POST
from .models import Escalamiento, AlertaSistema
from control_acceso.models import Discrepancia
from accounts.decorators import role_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from solicitudes.models import Solicitud
from datetime import datetime, timedelta

# Create your views here.

@login_required
@role_required('supervisor', 'admin_tic')
def dashboard(request):
    # Escalamientos pendientes
    escalamientos_list = Escalamiento.objects.filter(
        estado__in=['pendiente', 'en_revision']
    ).select_related('solicitud', 'escalado_por').order_by('-creado_el')
    
    # Discrepancias pendientes
    discrepancias_list = Discrepancia.objects.filter(
        estado__in=['reportada', 'en_revision']
    ).select_related('registro_acceso', 'reportada_por').order_by('-creada_el')
    
    # Alertas del sistema
    alertas_list = AlertaSistema.objects.filter(
        activa=True, leida=False
    ).order_by('-creada_el')
    
    # Estadísticas del mes actual
    today = datetime.now().date()
    first_day_month = today.replace(day=1)
    
    # Estadísticas generales del sistema
    stats = {
        'escalamientos_pendientes': escalamientos_list.count(),
        'discrepancias_pendientes': discrepancias_list.count(),
        'alertas_activas': alertas_list.count(),
        'casos_criticos': escalamientos_list.filter(prioridad='critica').count(),
        
        # Estadísticas del mes
        'solicitudes_procesadas': Solicitud.objects.filter(
            fecha_evaluacion__date__gte=first_day_month,
            estado__in=['aprobada', 'rechazada']
        ).count(),
        
        'solicitudes_aprobadas': Solicitud.objects.filter(
            fecha_evaluacion__date__gte=first_day_month,
            estado='aprobada'
        ).count(),
        
        'escalamientos_resueltos': Escalamiento.objects.filter(
            fecha_resolucion__date__gte=first_day_month,
            estado='resuelto'
        ).count(),
    }
    
    # Calcular porcentaje de aprobación
    if stats['solicitudes_procesadas'] > 0:
        stats['porcentaje_aprobacion'] = round((stats['solicitudes_aprobadas'] / stats['solicitudes_procesadas']) * 100)
    else:
        stats['porcentaje_aprobacion'] = 0
    
    # Alertas simuladas para mostrar en el dashboard
    alertas_dashboard = []
    if stats['casos_criticos'] > 0:
        alertas_dashboard.append({
            'tipo': 'Crítico',
            'mensaje': f'{stats["casos_criticos"]} caso{"s" if stats["casos_criticos"] > 1 else ""} crítico{"s" if stats["casos_criticos"] > 1 else ""} pendiente{"s" if stats["casos_criticos"] > 1 else ""}',
            'color': '#e74c3c',
            'bg': '#f8d7da'
        })
    
    if stats['discrepancias_pendientes'] > 5:
        alertas_dashboard.append({
            'tipo': 'Advertencia',
            'mensaje': f'{stats["discrepancias_pendientes"]} discrepancias acumuladas',
            'color': '#856404',
            'bg': '#fff3cd'
        })
    
    # Paginación
    paginator_esc = Paginator(escalamientos_list, 10)
    page_esc = request.GET.get('esc_page')
    escalamientos = paginator_esc.get_page(page_esc)
    
    paginator_disc = Paginator(discrepancias_list, 10)
    page_disc = request.GET.get('disc_page')
    discrepancias = paginator_disc.get_page(page_disc)
    
    context = {
        'user': request.user,
        'escalamientos': escalamientos,
        'discrepancias': discrepancias,
        'stats': stats,
        'alertas': alertas_dashboard,
        'alertas_sistema': alertas_list[:5]  # Solo mostrar las primeras 5
    }
    
    return render(request, 'supervisor/dashboard.html', context)

@login_required
@role_required('supervisor', 'admin_tic')
def detalle_escalamiento(request, codigo):
    try:
        escalamiento = Escalamiento.objects.select_related(
            'solicitud', 'escalado_por', 'asignado_a'
        ).get(codigo=codigo)
    except Escalamiento.DoesNotExist:
        raise Http404('Escalamiento no encontrado')
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        comentarios = request.POST.get('comentarios', '')
        
        if accion in ['aprobar', 'rechazar', 'solicitar_documentos', 'reasignar']:
            escalamiento.resolver(request.user, accion, comentarios)
            messages.success(request, f"¡Escalamiento {escalamiento.codigo} resuelto exitosamente!")
            return redirect('supervisor:dashboard')
        else:
            messages.error(request, "Acción no válida.")
    
    return render(request, 'supervisor/detalle_escalamiento.html', {
        'escalamiento': escalamiento,
        'solicitud': escalamiento.solicitud
    })

@login_required
@require_POST
@role_required('supervisor', 'admin_tic')
def resolver_escalamiento(request, codigo):
    # Aquí se resolvería el escalamiento en la base de datos
    # Por ahora solo simula la acción y redirige
    messages.success(request, "¡Escalamiento resuelto exitosamente!")
    return redirect('supervisor:dashboard')

@login_required
@role_required('supervisor', 'admin_tic')
def detalle_discrepancia(request, codigo):
    try:
        discrepancia = Discrepancia.objects.select_related(
            'registro_acceso', 'registro_acceso__autorizacion', 'reportada_por'
        ).get(codigo=codigo)
    except Discrepancia.DoesNotExist:
        raise Http404('Discrepancia no encontrada')
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        resolucion = request.POST.get('resolucion', '')
        
        if accion == 'resolver':
            discrepancia.resolver(request.user, resolucion)
            messages.success(request, f"¡Discrepancia {discrepancia.codigo} resuelta exitosamente!")
            return redirect('supervisor:dashboard')
        elif accion == 'asignar':
            discrepancia.estado = 'en_revision'
            discrepancia.asignada_a = request.user
            discrepancia.save()
            messages.success(request, f"¡Discrepancia {discrepancia.codigo} asignada!")
            return redirect('supervisor:dashboard')
        else:
            messages.error(request, "Acción no válida.")
    
    return render(request, 'supervisor/detalle_discrepancia.html', {
        'discrepancia': discrepancia
    })

@require_POST
@login_required
@role_required('supervisor', 'admin_tic')
def gestionar_discrepancia(request, autorizacion):
    # Aquí se gestionaría la discrepancia en la base de datos
    # Por ahora solo simula la acción y redirige
    messages.success(request, "¡Discrepancia gestionada exitosamente!")
    return redirect('supervisor:dashboard')
