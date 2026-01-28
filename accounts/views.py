from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import User, NotificacionEmpresa, Empresa
import json
from .decorators import role_required
from .forms import CustomAuthenticationForm
from django import forms
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import re

@csrf_protect
def login_view(request):
    """Vista de login simple con usuario y contraseña"""
    if request.user.is_authenticated:
        return redirect_by_role(request.user.role)
    
    form = CustomAuthenticationForm()
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)
            
            # Autenticar usuario
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # Verificar si está activo
                if not user.activo:
                    messages.error(request, 'Tu cuenta está desactivada. Contacte al administrador.')
                    return render(request, 'login.html', {'form': form})
                
                # Verificar si está bloqueado
                if user.is_locked and user.locked_until and timezone.now() < user.locked_until:
                    tiempo_restante = user.locked_until - timezone.now()
                    minutos = int(tiempo_restante.total_seconds() / 60)
                    messages.error(request, f'Tu cuenta está bloqueada por {minutos} minutos más.')
                    return render(request, 'login.html', {'form': form})
                
                # Login exitoso
                login(request, user)
                
                # Limpiar intentos fallidos y bloqueos
                user.failed_login_attempts = 0
                user.is_locked = False
                user.locked_until = None
                user.last_login_ip = get_client_ip(request)
                user.save()
                
                # Configurar sesión
                if not remember_me:
                    request.session.set_expiry(0)  # Cerrar al cerrar navegador
                
                messages.success(request, f'¡Bienvenido, {user.get_display_name()}!')
                
                # Redirigir según el rol
                return redirect_by_role(user.role)
            else:
                # Usuario o contraseña incorrectos
                try:
                    # Buscar usuario para incrementar intentos fallidos
                    user_obj = User.objects.get(username=username)
                    handle_failed_login(user_obj, request)
                except User.DoesNotExist:
                    pass
                
                messages.error(request, 'Usuario o contraseña incorrectos.')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    
    return render(request, 'login.html', {'form': form})

def handle_failed_login(user, request):
    """Maneja los intentos fallidos de login"""
    user.failed_login_attempts += 1
    
    # Bloquear después de 5 intentos fallidos
    if user.failed_login_attempts >= 5:
        user.is_locked = True
        user.locked_until = timezone.now() + timezone.timedelta(minutes=30)
        messages.warning(request, 'Cuenta bloqueada por 30 minutos debido a múltiples intentos fallidos.')
    
    user.save()

def get_client_ip(request):
    """Obtiene la IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def redirect_by_role(role):
    """Redirige según el rol del usuario"""
    role_redirects = {
        'solicitante': 'solicitudes:dashboard',
        'evaluador': 'evaluacion:dashboard', 
        'supervisor': 'supervisor:dashboard',
        'oficial_acceso': 'control_acceso:dashboard',
        'admin_tic': 'admin:index',
        'direccion': 'reportes:dashboard'
    }
    
    return redirect(role_redirects.get(role, 'dashboard'))

@login_required 
def dashboard_redirect(request):
    """Redirige al dashboard apropiado según el rol del usuario"""
    return redirect_by_role(request.user.role)

@login_required
def logout_view(request):
    """Vista de logout personalizada"""
    user_name = request.user.get_display_name()
    logout(request)
    messages.success(request, f'Sesión cerrada correctamente. ¡Hasta luego, {user_name}!')
    return redirect('accounts:login')

@login_required
def profile_view(request):
    """Vista del perfil del usuario"""
    user = request.user
    context = {
        'user': user,
        'empresa': getattr(user, 'empresas_representadas', None).first() if user.is_solicitante() else None
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def change_password_view(request):
    """Vista para cambiar contraseña"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(current_password):
            messages.error(request, 'La contraseña actual es incorrecta.')
        elif new_password != confirm_password:
            messages.error(request, 'Las contraseñas nuevas no coinciden.')
        elif len(new_password) < 8:
            messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
        else:
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, 'Contraseña cambiada exitosamente.')
            return redirect('accounts:profile')
    
    return render(request, 'accounts/change_password.html')

# API Views para AJAX
@login_required
def check_session_status(request):
    """API endpoint para verificar el estado de la sesión"""
    return JsonResponse({
        'authenticated': True,
        'user': request.user.get_display_name(),
        'role': request.user.get_role_display(),
        'expires_in': request.session.get_expiry_age() if request.session.get_expiry_age() else None
    })

def validate_cedula_rnc(request):
    """API endpoint para validar formato de cédula/RNC"""
    cedula_rnc = request.GET.get('cedula_rnc', '')
    
    # Validar formato
    import re
    cedula_pattern = r'^\d{3}-\d{7}-\d{1}$'
    rnc_pattern = r'^\d{3}-\d{5}-\d{1}$'
    
    is_valid = bool(re.match(cedula_pattern, cedula_rnc) or re.match(rnc_pattern, cedula_rnc))
    doc_type = 'cédula' if re.match(cedula_pattern, cedula_rnc) else 'RNC' if re.match(rnc_pattern, cedula_rnc) else 'desconocido'
    
    return JsonResponse({
        'valid': is_valid,
        'type': doc_type,
        'message': 'Formato válido' if is_valid else 'Formato inválido. Use 000-0000000-0 para cédula o 130-12345-7 para RNC'
    })

@login_required
def cerrar_notificacion(request):
    """API endpoint para cerrar una notificación"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        data = json.loads(request.body)
        notificacion_id = data.get('notificacion_id')
        
        if not notificacion_id:
            return JsonResponse({'success': False, 'error': 'ID de notificación requerido'})
        
        # Verificar que la notificación pertenece al usuario
        notificacion = NotificacionEmpresa.objects.filter(
            id=notificacion_id,
            usuario=request.user
        ).first()
        
        if not notificacion:
            return JsonResponse({'success': False, 'error': 'Notificación no encontrada'})
        
        # Cerrar la notificación
        notificacion.cerrar()
        
        return JsonResponse({'success': True, 'message': 'Notificación cerrada'})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# === GESTIÓN DE USUARIOS ===

class UsuarioForm(forms.ModelForm):
    """Formulario para crear/editar usuarios"""
    
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Contraseña',
        required=True
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Confirmar Contraseña',
        required=True
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'cedula_rnc', 
                 'telefono', 'role', 'empresa', 'es_admin_empresa', 'puede_crear_usuarios', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'cedula_rnc': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'XXX-XXXXXXX-X'
            }),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'empresa': forms.Select(attrs={'class': 'form-control'}),
            'es_admin_empresa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'puede_crear_usuarios': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        user_role = kwargs.pop('user_role', None)
        empresa_filter = kwargs.pop('empresa_filter', None)
        super().__init__(*args, **kwargs)
        
        # Si es admin de empresa, solo puede crear solicitantes
        if user_role == 'solicitante':
            self.fields['role'].choices = [('solicitante', 'Solicitante')]
            self.fields['empresa'].widget = forms.HiddenInput()
            if empresa_filter:
                self.fields['empresa'].queryset = Empresa.objects.filter(id=empresa_filter.id)
        else:
            # Evaluadores pueden crear cualquier tipo de usuario
            self.fields['empresa'].queryset = Empresa.objects.filter(activa=True).order_by('nombre')
            self.fields['empresa'].empty_label = "--- Seleccionar Empresa ---"
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        
        if not username:
            raise ValidationError("El nombre de usuario es requerido.")
        
        # Verificar que no exista otro usuario con este username
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Ya existe un usuario con este nombre de usuario.")
        
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        if not email:
            raise ValidationError("El correo electrónico es requerido.")
        
        # Validar formato de email
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("Ingrese una dirección de correo electrónico válida.")
        
        # Verificar que no exista otro usuario con este email
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Ya existe un usuario con este correo electrónico.")
        
        return email.lower()

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Solo establecer contraseña si se proporcionó una nueva
        if self.cleaned_data.get("password1"):
            user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

@login_required
def gestionar_usuarios(request):
    """Vista principal para gestionar usuarios según el rol"""
    if not request.user.puede_gestionar_usuarios():
        messages.error(request, 'No tienes permisos para gestionar usuarios.')
        return redirect('accounts:profile')
    
    # Obtener parámetros de filtro
    busqueda = request.GET.get('q', '')
    empresa_filtro = request.GET.get('empresa', '')
    rol_filtro = request.GET.get('rol', '')
    estado_filtro = request.GET.get('estado', '')
    
    # Construir queryset base según el rol del usuario
    if request.user.role in ['evaluador', 'supervisor', 'admin_tic']:
        # Evaluadores pueden ver usuarios de todas las empresas
        usuarios_queryset = User.objects.all().select_related('empresa').order_by('-created_at')
    else:
        # Admins de empresa solo ven usuarios de su empresa
        if not request.user.empresa:
            messages.error(request, 'No tienes una empresa asignada.')
            return redirect('accounts:profile')
        usuarios_queryset = User.objects.filter(empresa=request.user.empresa).select_related('empresa').order_by('-created_at')
    
    # Aplicar filtros de búsqueda
    if busqueda:
        usuarios_queryset = usuarios_queryset.filter(
            Q(username__icontains=busqueda) |
            Q(first_name__icontains=busqueda) |
            Q(last_name__icontains=busqueda) |
            Q(email__icontains=busqueda) |
            Q(cedula_rnc__icontains=busqueda) |
            Q(empresa__nombre__icontains=busqueda)
        )
    
    # Filtro por empresa (solo para evaluadores)
    if empresa_filtro and request.user.role in ['evaluador', 'supervisor', 'admin_tic']:
        usuarios_queryset = usuarios_queryset.filter(empresa__id=empresa_filtro)
    
    # Filtro por rol
    if rol_filtro:
        usuarios_queryset = usuarios_queryset.filter(role=rol_filtro)
    
    # Filtro por estado
    if estado_filtro == 'activo':
        usuarios_queryset = usuarios_queryset.filter(is_active=True)
    elif estado_filtro == 'inactivo':
        usuarios_queryset = usuarios_queryset.filter(is_active=False)
    elif estado_filtro == 'admin_empresa':
        usuarios_queryset = usuarios_queryset.filter(es_admin_empresa=True)
    
    # Paginación
    paginator = Paginator(usuarios_queryset, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    stats = {
        'total': usuarios_queryset.count(),
        'activos': usuarios_queryset.filter(is_active=True).count(),
        'inactivos': usuarios_queryset.filter(is_active=False).count(),
        'admin_empresa': usuarios_queryset.filter(es_admin_empresa=True).count(),
    }
    
    # Lista de empresas para el filtro (solo para evaluadores)
    empresas_filtro = []
    if request.user.role in ['evaluador', 'supervisor', 'admin_tic']:
        empresas_filtro = Empresa.objects.filter(activa=True).order_by('nombre')
    
    context = {
        'usuarios': page_obj,
        'busqueda': busqueda,
        'empresa_filtro': empresa_filtro,
        'rol_filtro': rol_filtro,
        'estado_filtro': estado_filtro,
        'stats': stats,
        'empresas_filtro': empresas_filtro,
        'is_paginated': page_obj.has_other_pages(),
        'puede_crear': request.user.puede_crear_usuarios_empresa() or request.user.role in ['evaluador', 'supervisor', 'admin_tic']
    }
    
    return render(request, 'accounts/gestionar_usuarios.html', context)

@login_required
def crear_usuario(request):
    """Vista para crear nuevo usuario"""
    if not (request.user.puede_crear_usuarios_empresa() or request.user.role in ['evaluador', 'supervisor', 'admin_tic']):
        messages.error(request, 'No tienes permisos para crear usuarios.')
        return redirect('accounts:gestionar_usuarios')
    
    if request.method == 'POST':
        form = UsuarioForm(request.POST, user_role=request.user.role, empresa_filter=request.user.empresa)
        if form.is_valid():
            user = form.save(commit=False)
            
            # Si es admin de empresa, auto-asignar su empresa
            if request.user.role == 'solicitante' and request.user.es_admin_empresa:
                user.empresa = request.user.empresa
                user.role = 'solicitante'
            
            user.save()
            messages.success(request, f'Usuario "{user.username}" creado exitosamente.')
            return redirect('accounts:gestionar_usuarios')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = UsuarioForm(user_role=request.user.role, empresa_filter=request.user.empresa)
        # Pre-seleccionar empresa si es admin de empresa
        if request.user.role == 'solicitante' and request.user.empresa:
            form.initial['empresa'] = request.user.empresa
    
    context = {
        'form': form,
        'titulo': 'Crear Usuario'
    }
    return render(request, 'accounts/crear_usuario.html', context)

@login_required
def editar_usuario(request, usuario_id):
    """Vista para editar usuario existente"""
    usuario = get_object_or_404(User, id=usuario_id)
    
    # Verificar permisos
    if request.user.role in ['evaluador', 'supervisor', 'admin_tic']:
        # Evaluadores pueden editar cualquier usuario
        pass
    elif request.user.es_admin_empresa and request.user.empresa == usuario.empresa:
        # Admin de empresa puede editar usuarios de su empresa
        pass
    else:
        messages.error(request, 'No tienes permisos para editar este usuario.')
        return redirect('accounts:gestionar_usuarios')
    
    if request.method == 'POST':
        # Para edición, no requerimos contraseña
        form_data = request.POST.copy()
        form = UsuarioForm(form_data, instance=usuario, user_role=request.user.role, empresa_filter=request.user.empresa)
        
        # Remover validación de contraseña si no se proporcionó
        if not form_data.get('password1'):
            form.fields['password1'].required = False
            form.fields['password2'].required = False
        
        if form.is_valid():
            user = form.save(commit=False)
            
            # Solo actualizar contraseña si se proporcionó
            if form.cleaned_data.get('password1'):
                user.set_password(form.cleaned_data["password1"])
            
            user.save()
            messages.success(request, f'Usuario "{user.username}" actualizado exitosamente.')
            return redirect('accounts:gestionar_usuarios')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = UsuarioForm(instance=usuario, user_role=request.user.role, empresa_filter=request.user.empresa)
        # Para edición, hacer contraseñas opcionales
        form.fields['password1'].required = False
        form.fields['password2'].required = False
        form.fields['password1'].help_text = "Dejar en blanco para mantener contraseña actual"
    
    context = {
        'form': form,
        'usuario': usuario,
        'titulo': f'Editar Usuario: {usuario.username}',
        'editando': True
    }
    return render(request, 'accounts/crear_usuario.html', context)

@login_required
def eliminar_usuario(request, usuario_id):
    """Vista para eliminar usuario"""
    usuario = get_object_or_404(User, id=usuario_id)
    
    # Verificar permisos
    if request.user.role in ['evaluador', 'supervisor', 'admin_tic']:
        # Evaluadores pueden eliminar cualquier usuario
        pass
    elif request.user.es_admin_empresa and request.user.empresa == usuario.empresa:
        # Admin de empresa puede eliminar usuarios de su empresa
        pass
    else:
        messages.error(request, 'No tienes permisos para eliminar este usuario.')
        return redirect('accounts:gestionar_usuarios')
    
    # No permitir auto-eliminación
    if usuario == request.user:
        messages.error(request, 'No puedes eliminar tu propio usuario.')
        return redirect('accounts:gestionar_usuarios')
    
    if request.method == 'POST':
        username = usuario.username
        usuario.delete()
        messages.success(request, f'Usuario "{username}" eliminado exitosamente.')
        return redirect('accounts:gestionar_usuarios')
    
    # Verificar si el usuario tiene solicitudes asociadas
    solicitudes_count = getattr(usuario, 'solicitudes', None)
    if solicitudes_count:
        solicitudes_count = solicitudes_count.count()
    else:
        solicitudes_count = 0
    
    context = {
        'usuario': usuario,
        'solicitudes_count': solicitudes_count
    }
    return render(request, 'accounts/eliminar_usuario.html', context)

@login_required
def toggle_admin_empresa(request, usuario_id):
    """Vista AJAX para activar/desactivar admin de empresa"""
    try:
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'Método no permitido'})
        
        if request.user.role not in ['evaluador', 'supervisor', 'admin_tic']:
            return JsonResponse({'success': False, 'error': 'Sin permisos suficientes'})
        
        usuario = get_object_or_404(User, id=usuario_id)
        
        # Guardar estado anterior para el mensaje
        estado_anterior = usuario.es_admin_empresa
        
        # Toggle admin status
        usuario.es_admin_empresa = not usuario.es_admin_empresa
        
        # Si se convierte en admin, también darle permisos de crear usuarios
        if usuario.es_admin_empresa:
            usuario.puede_crear_usuarios = True
        
        usuario.save()
        
        return JsonResponse({
            'success': True,
            'es_admin_empresa': usuario.es_admin_empresa,
            'puede_crear_usuarios': usuario.puede_crear_usuarios,
            'message': f'Usuario "{usuario.username}" {"promovido a" if usuario.es_admin_empresa else "removido como"} admin de empresa'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f'Error interno: {str(e)}'
        })


@login_required
def toggle_usuario_activo(request, usuario_id):
    """Vista AJAX para activar/desactivar usuario"""
    try:
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'Método no permitido'})

        # Verificar permisos
        if request.user.role not in ['evaluador', 'supervisor', 'admin_tic']:
            # Admin de empresa puede inhabilitar usuarios de su empresa
            if not (request.user.es_admin_empresa and request.user.empresa):
                return JsonResponse({'success': False, 'error': 'Sin permisos suficientes'})

        usuario = get_object_or_404(User, id=usuario_id)

        # Verificar que admin de empresa solo modifique usuarios de su empresa
        if request.user.role == 'solicitante':
            if usuario.empresa != request.user.empresa:
                return JsonResponse({'success': False, 'error': 'No puedes modificar usuarios de otra empresa'})

        # No permitir desactivar a sí mismo
        if usuario == request.user:
            return JsonResponse({'success': False, 'error': 'No puedes desactivarte a ti mismo'})

        # Toggle estado activo
        usuario.activo = not usuario.activo
        usuario.is_active = usuario.activo  # Sincronizar con is_active de Django
        usuario.save()

        return JsonResponse({
            'success': True,
            'activo': usuario.activo,
            'message': f'Usuario "{usuario.username}" {"activado" if usuario.activo else "desactivado"} exitosamente'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno: {str(e)}'
        })


@login_required
def historial_usuario(request, usuario_id):
    """Vista para ver el historial de actividad de un usuario"""
    usuario = get_object_or_404(User, id=usuario_id)

    # Verificar permisos
    puede_ver = False
    if request.user.role in ['evaluador', 'supervisor', 'admin_tic']:
        puede_ver = True
    elif request.user.es_admin_empresa and request.user.empresa == usuario.empresa:
        puede_ver = True
    elif request.user == usuario:
        puede_ver = True

    if not puede_ver:
        messages.error(request, 'No tienes permisos para ver el historial de este usuario.')
        return redirect('accounts:gestionar_usuarios')

    # Recopilar actividad del usuario
    actividades = []

    # 1. Solicitudes creadas
    from solicitudes.models import Solicitud
    solicitudes = Solicitud.objects.filter(solicitante=usuario).order_by('-creada_el')[:10]
    for sol in solicitudes:
        actividades.append({
            'tipo': 'solicitud_creada',
            'icono': 'fas fa-file-alt',
            'color': 'primary',
            'titulo': f'Solicitud creada: {sol.codigo}',
            'descripcion': f'Estado: {sol.get_estado_display()}',
            'fecha': sol.creada_el,
            'url': None  # Agregar URL si existe vista de detalle
        })

    # 2. Solicitudes asignadas (si es evaluador)
    if usuario.role in ['evaluador', 'supervisor']:
        solicitudes_asignadas = Solicitud.objects.filter(evaluador_asignado=usuario).order_by('-fecha_evaluacion')[:10]
        for sol in solicitudes_asignadas:
            if sol.fecha_evaluacion:
                actividades.append({
                    'tipo': 'solicitud_evaluada',
                    'icono': 'fas fa-check-circle',
                    'color': 'success',
                    'titulo': f'Solicitud evaluada: {sol.codigo}',
                    'descripcion': f'Estado: {sol.get_estado_display()}',
                    'fecha': sol.fecha_evaluacion,
                    'url': None
                })

    # 3. Incumplimientos reportados (si es oficial de acceso)
    if usuario.role == 'oficial_acceso':
        from incumplimientos.models import Incumplimiento
        incumplimientos = Incumplimiento.objects.filter(reportado_por=usuario).order_by('-fecha_reporte')[:10]
        for inc in incumplimientos:
            actividades.append({
                'tipo': 'incumplimiento',
                'icono': 'fas fa-exclamation-triangle',
                'color': 'warning',
                'titulo': f'Incumplimiento reportado',
                'descripcion': f'{inc.get_tipo_display()} - {inc.puerto.nombre}',
                'fecha': inc.fecha_reporte,
                'url': None
            })

    # 4. Aprobaciones excepcionales (si es supervisor/dirección)
    if usuario.role in ['supervisor', 'direccion']:
        from accounts.models import AprobacionExcepcional
        aprobaciones = AprobacionExcepcional.objects.filter(
            Q(aprobada_por=usuario) | Q(revocada_por=usuario)
        ).order_by('-fecha_aprobacion')[:10]
        for aprob in aprobaciones:
            if aprob.aprobada_por == usuario:
                actividades.append({
                    'tipo': 'aprobacion_excepcional',
                    'icono': 'fas fa-star',
                    'color': 'success',
                    'titulo': f'Aprobó permiso excepcional',
                    'descripcion': f'Empresa: {aprob.empresa.nombre}',
                    'fecha': aprob.fecha_aprobacion,
                    'url': None
                })
            if aprob.revocada_por == usuario and aprob.fecha_revocacion:
                actividades.append({
                    'tipo': 'revocacion_excepcional',
                    'icono': 'fas fa-ban',
                    'color': 'warning',
                    'titulo': f'Revocó permiso excepcional',
                    'descripcion': f'Empresa: {aprob.empresa.nombre}',
                    'fecha': aprob.fecha_revocacion,
                    'url': None
                })

    # 5. Cambios de estado del usuario
    cambios_estado = []
    if not usuario.activo:
        cambios_estado.append({
            'tipo': 'usuario_desactivado',
            'icono': 'fas fa-user-times',
            'color': 'danger',
            'titulo': 'Usuario desactivado',
            'descripcion': 'El usuario fue desactivado',
            'fecha': usuario.updated_at,
            'url': None
        })

    # Combinar y ordenar todas las actividades
    todas_actividades = actividades + cambios_estado
    todas_actividades.sort(key=lambda x: x['fecha'], reverse=True)

    # Paginación
    paginator = Paginator(todas_actividades, 20)
    page = request.GET.get('page')
    actividades_page = paginator.get_page(page)

    # Estadísticas
    stats = {
        'solicitudes_creadas': Solicitud.objects.filter(solicitante=usuario).count(),
        'solicitudes_evaluadas': Solicitud.objects.filter(evaluador_asignado=usuario).count() if usuario.role in ['evaluador', 'supervisor'] else 0,
        'dias_desde_registro': (timezone.now() - usuario.created_at).days,
        'ultimo_login': usuario.last_login,
    }

    context = {
        'usuario': usuario,
        'actividades': actividades_page,
        'stats': stats,
    }

    return render(request, 'accounts/historial_usuario.html', context)


# Password Reset Views
def password_reset_request(request):
    """Vista para solicitar restablecimiento de contraseña"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'Por favor, ingresa tu correo electrónico.')
            return render(request, 'accounts/password_reset_form.html')
        
        # Validar formato de email
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Por favor, ingresa una dirección de correo electrónico válida.')
            return render(request, 'accounts/password_reset_form.html')
        
        # Intentar enviar email solo si el usuario existe y está activo
        try:
            user = User.objects.get(email__iexact=email)
            
            # Solo proceder si el usuario está activo
            if user.activo:
                # Importar la configuración de email y enviar
                from evaluacion.models import ConfiguracionEmail
                from django.core.mail import send_mail
                
                config = ConfiguracionEmail.get_configuracion_activa()
                
                if config and config.email_enabled:
                    try:
                        # Aplicar configuración de email
                        config.aplicar_configuracion()
                        
                        # Generar token de recuperación
                        token = default_token_generator.make_token(user)
                        uid = urlsafe_base64_encode(force_bytes(user.pk))
                        
                        # Crear el enlace de recuperación
                        reset_url = request.build_absolute_uri(
                            f'/accounts/password-reset/confirm/{uid}/{token}/'
                        )
                        
                        # Renderizar el email
                        email_subject = 'NaviPort RD - Restablecimiento de Contraseña'
                        email_body = render_to_string('accounts/password_reset_email.html', {
                            'user': user,
                            'reset_url': reset_url,
                            'site_name': 'NaviPort RD'
                        })
                        
                        # Enviar email usando Django mail
                        send_mail(
                            subject=email_subject,
                            message=email_body,
                            from_email=config.default_from_email,
                            recipient_list=[user.email],
                            html_message=email_body,
                            fail_silently=True
                        )
                        
                        # Incrementar contador de emails enviados
                        config.incrementar_contador_emails()
                        
                    except Exception:
                        # Silenciosamente fallar el envío de email
                        pass
                        
        except User.DoesNotExist:
            # Usuario no existe, pero no revelamos esta información
            pass
        
        # Siempre mostrar el mismo mensaje sin importar si el email existe o no
        messages.success(request, 'Si el correo está registrado en el sistema, recibirás un enlace de recuperación.')
        return redirect('accounts:password_reset_done')
    
    return render(request, 'accounts/password_reset_form.html')

def password_reset_done(request):
    """Vista mostrada después de solicitar el restablecimiento"""
    return render(request, 'accounts/password_reset_done.html')

def password_reset_confirm(request, uidb64, token):
    """Vista para confirmar y cambiar la contraseña"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            
            if not password1 or not password2:
                messages.error(request, 'Ambos campos de contraseña son requeridos.')
                return render(request, 'accounts/password_reset_confirm.html', {
                    'validlink': True,
                    'uidb64': uidb64,
                    'token': token
                })
            
            if password1 != password2:
                messages.error(request, 'Las contraseñas no coinciden.')
                return render(request, 'accounts/password_reset_confirm.html', {
                    'validlink': True,
                    'uidb64': uidb64,
                    'token': token
                })
            
            if len(password1) < 8:
                messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
                return render(request, 'accounts/password_reset_confirm.html', {
                    'validlink': True,
                    'uidb64': uidb64,
                    'token': token
                })
            
            # Cambiar la contraseña
            user.set_password(password1)
            user.failed_login_attempts = 0  # Resetear intentos fallidos
            user.is_locked = False  # Desbloquear cuenta si estaba bloqueada
            user.locked_until = None
            user.save()
            
            messages.success(request, 'Tu contraseña ha sido cambiada exitosamente.')
            return redirect('accounts:password_reset_complete')
        
        return render(request, 'accounts/password_reset_confirm.html', {
            'validlink': True,
            'uidb64': uidb64,
            'token': token
        })
    else:
        return render(request, 'accounts/password_reset_confirm.html', {
            'validlink': False
        })

def password_reset_complete(request):
    """Vista mostrada después de cambiar exitosamente la contraseña"""
    return render(request, 'accounts/password_reset_complete.html')

@login_required
@role_required('evaluador', 'supervisor', 'admin_tic')
def notificar_admin(request, usuario_id):
    """Vista para notificar al administrador de empresa por correo"""
    print("=" * 50)
    print("FUNCIÓN NOTIFICAR_ADMIN LLAMADA")
    print("=" * 50)
    print(f"DEBUG: notificar_admin vista llamada con usuario_id={usuario_id}")
    print(f"DEBUG: Método de request: {request.method}")
    print(f"DEBUG: Usuario logueado: {request.user.username if request.user.is_authenticated else 'Anónimo'}")

    # Respuesta inmediata para AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        print("DEBUG: Detectada solicitud AJAX - enviando respuesta de prueba")
        return JsonResponse({
            'success': True,
            'message': 'FUNCIÓN EJECUTADA CORRECTAMENTE - ESTO ES UNA PRUEBA'
        })
    try:
        print(f"DEBUG: Buscando usuario con ID {usuario_id}")
        usuario = get_object_or_404(User, pk=usuario_id)
        print(f"DEBUG: Usuario encontrado: {usuario.username}")

        # Verificar que el usuario sea admin de empresa
        print(f"DEBUG: es_admin_empresa = {usuario.es_admin_empresa}")
        if not usuario.es_admin_empresa:
            print("DEBUG: Usuario NO es admin de empresa - SALIENDO")
            messages.error(request, 'Este usuario no es administrador de empresa.')
            return redirect('accounts:gestionar_usuarios')

        # Verificar que tenga email
        print(f"DEBUG: email = {usuario.email}")
        if not usuario.email:
            print("DEBUG: Usuario NO tiene email - SALIENDO")
            messages.error(request, 'El usuario no tiene email configurado.')
            return redirect('accounts:gestionar_usuarios')

        # Verificar que tenga empresa
        print(f"DEBUG: empresa = {usuario.empresa}")
        if not usuario.empresa:
            print("DEBUG: Usuario NO tiene empresa - SALIENDO")
            messages.error(request, 'El usuario no tiene empresa asignada.')
            return redirect('accounts:gestionar_usuarios')

        print("DEBUG: Todas las validaciones pasadas - preparando correo")

        # Preparar datos del correo
        empresa_nombre = usuario.empresa.nombre
        usuario_nombre = usuario.get_display_name()
        evaluador_nombre = request.user.get_display_name()
        fecha_actual = timezone.now().strftime('%d/%m/%Y')

        # Asunto del correo
        asunto = f"Acceso Administrativo a NaviPort RD - {empresa_nombre}"

        # Cuerpo del correo
        mensaje = f"""Estimado/a {usuario_nombre},

Le informamos que ha sido designado/a como administrador/a de su empresa {empresa_nombre} en el sistema NaviPort RD.

Como administrador empresarial, usted tiene los siguientes privilegios:
• Crear y gestionar usuarios de su organización
• Administrar las solicitudes de acceso portuario de su empresa
• Supervisar las autorizaciones activas

Para acceder al sistema, visite:
🔗 www.naviportrd.com

Su nombre de usuario es: {usuario.username}

⚠️ IMPORTANTE: Debe cambiar su contraseña por seguridad utilizando el enlace "Olvidé mi contraseña" en la página de inicio de sesión.

Atentamente,
Equipo NaviPort RD
Sistema de Gestión Portuaria

---
Este mensaje fue enviado por: {evaluador_nombre}
Fecha: {fecha_actual}

---
⚠️ IMPORTANTE: Este es un correo automático de notificación.
No responda a este mensaje.

Para soporte técnico o consultas, contacte a:
📧 soporte@naviportrd.com
"""

        # Enviar correo
        try:
            print(f"DEBUG: Intentando enviar correo a {usuario.email}")

            # Preparar lista de copias (CC)
            cc_list = []
            if request.user.email:
                cc_list = [request.user.email]

            # Crear y enviar el correo con copia
            email = EmailMessage(
                subject=asunto,
                body=mensaje,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[usuario.email],
                cc=cc_list
            )
            email.send(fail_silently=False)

            print(f"DEBUG: Correo enviado exitosamente")

            # Si es una solicitud AJAX, devolver JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Notificación enviada exitosamente a {usuario.email}'
                })

            messages.success(request, f'Notificación enviada exitosamente a {usuario.email}')

        except Exception as e:
            print(f"DEBUG: Error al enviar correo: {str(e)}")

            # Si es una solicitud AJAX, devolver JSON con error
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': f'Error al enviar la notificación: {str(e)}'
                }, status=500)

            messages.error(request, f'Error al enviar la notificación: {str(e)}')

    except Exception as e:
        messages.error(request, f'Error al procesar la solicitud: {str(e)}')

    return redirect('accounts:gestionar_usuarios')

def notificar_admin_ajax(request):
    """Envía notificación al administrador de empresa (AJAX)"""
    print("*" * 50)
    print("NOTIFICAR_ADMIN_AJAX LLAMADA")
    print("*" * 50)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    usuario_id = request.POST.get('usuario_id')
    if not usuario_id:
        return JsonResponse({'success': False, 'error': 'ID de usuario requerido'})

    try:
        usuario = get_object_or_404(User, pk=usuario_id)
        print(f"Usuario encontrado: {usuario.username}")

        # Verificar que el usuario sea admin de empresa
        if not usuario.es_admin_empresa:
            return JsonResponse({'success': False, 'error': 'Este usuario no es administrador de empresa'})

        # Verificar que tenga email
        if not usuario.email:
            return JsonResponse({'success': False, 'error': 'El usuario no tiene email configurado'})

        # Verificar que tenga empresa
        if not usuario.empresa:
            return JsonResponse({'success': False, 'error': 'El usuario no tiene empresa asignada'})

        # Preparar datos del correo
        empresa_nombre = usuario.empresa.nombre
        usuario_nombre = usuario.get_display_name()
        evaluador_nombre = request.user.get_display_name() if request.user.is_authenticated else "Sistema"
        fecha_actual = timezone.now().strftime('%d/%m/%Y')

        # Asunto del correo
        asunto = f"Acceso Administrativo a NaviPort RD - {empresa_nombre}"

        # Cuerpo del correo
        mensaje = f"""Estimado/a {usuario_nombre},

Le informamos que ha sido designado/a como administrador/a de su empresa {empresa_nombre} en el sistema NaviPort RD.

Como administrador empresarial, usted tiene los siguientes privilegios:
• Crear y gestionar usuarios de su organización
• Administrar las solicitudes de acceso portuario de su empresa
• Supervisar las autorizaciones activas

Para acceder al sistema, visite:
🔗 www.naviportrd.com

Su nombre de usuario es: {usuario.username}

⚠️ IMPORTANTE: Debe cambiar su contraseña por seguridad utilizando el enlace "Olvidé mi contraseña" en la página de inicio de sesión.

Atentamente,
Equipo NaviPort RD
Sistema de Gestión Portuaria

---
Este mensaje fue enviado por: {evaluador_nombre}
Fecha: {fecha_actual}

---
⚠️ IMPORTANTE: Este es un correo automático de notificación.
No responda a este mensaje.

Para soporte técnico o consultas, contacte a:
📧 soporte@naviportrd.com
"""

        # Aplicar configuración de email activa (igual que en Comprobar Configuración)
        from evaluacion.models import ConfiguracionEmail
        try:
            config_email = ConfiguracionEmail.objects.filter(email_enabled=True).first()
            if config_email:
                config_email.aplicar_configuracion()
                print(f"Configuración de email aplicada: {config_email.nombre}")
            else:
                print("No hay configuración de email activa, usando configuración por defecto")
        except Exception as e:
            print(f"Error aplicando configuración de email: {e}")

        # Enviar correo
        print(f"Intentando enviar correo a {usuario.email}")

        # Preparar lista de copias (CC)
        cc_list = []
        if request.user.is_authenticated and request.user.email:
            cc_list = [request.user.email]

        # Crear y enviar el correo con copia
        email = EmailMessage(
            subject=asunto,
            body=mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[usuario.email],
            cc=cc_list
        )
        email.send(fail_silently=False)

        print(f"Correo enviado exitosamente")

        return JsonResponse({
            'success': True,
            'message': f'Notificación enviada exitosamente a {usuario.email}'
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def ayuda_view(request):
    """Vista del manual de ayuda contextual por rol"""
    context = {
        'user_role': request.user.role,
        'role_display': request.user.get_role_display(),
    }
    return render(request, 'ayuda.html', context)
