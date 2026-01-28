from django import forms
from django.core.exceptions import ValidationError
from .models import EmpresaServicio, Servicio
from datetime import date


class ServicioForm(forms.ModelForm):
    """Formulario para crear/editar servicios"""
    
    class Meta:
        model = Servicio
        fields = ['nombre', 'descripcion', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Transporte de Contenedores'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada del servicio...'
            }),
        }


class EmpresaServicioForm(forms.ModelForm):
    """Formulario para crear/editar empresas de servicio"""
    
    servicios_autorizados = forms.ModelMultipleChoiceField(
        queryset=Servicio.objects.filter(activo=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label='Servicios Autorizados'
    )
    
    class Meta:
        model = EmpresaServicio
        fields = [
            'rnc', 'nombre', 'telefono', 'email', 'direccion',
            'numero_licencia', 'fecha_expiracion_licencia', 
            'servicios_autorizados', 'activa'
        ]
        widgets = {
            'rnc': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'XXX-XXXXX-X',
                'id': 'rncInput'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo de la empresa'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'XXX-XXX-XXXX',
                'id': 'telefonoInput'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'empresa@ejemplo.com'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Dirección completa de la empresa'
            }),
            'numero_licencia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número único de licencia'
            }),
            'fecha_expiracion_licencia': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'fechaExpiracionInput'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configurar fecha mínima para no permitir fechas pasadas
        today = date.today().isoformat()
        if 'fecha_expiracion_licencia' in self.fields:
            self.fields['fecha_expiracion_licencia'].widget.attrs['min'] = today
        
        # Hacer campos obligatorios más claros
        self.fields['rnc'].required = True
        self.fields['nombre'].required = True
        self.fields['numero_licencia'].required = True
        self.fields['fecha_expiracion_licencia'].required = True
    
    def clean_rnc(self):
        """Validar formato RNC"""
        rnc = self.cleaned_data.get('rnc')
        if rnc:
            # Remover espacios y guiones para validación
            rnc_clean = rnc.replace('-', '').replace(' ', '')
            if len(rnc_clean) != 9 or not rnc_clean.isdigit():
                raise ValidationError('El RNC debe tener formato XXX-XXXXX-X (9 dígitos)')
            # Reformatear
            return f"{rnc_clean[:3]}-{rnc_clean[3:8]}-{rnc_clean[8]}"
        return rnc
    
    def clean_telefono(self):
        """Validar formato teléfono"""
        telefono = self.cleaned_data.get('telefono')
        if telefono:
            # Remover espacios y guiones para validación
            tel_clean = telefono.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
            if len(tel_clean) != 10 or not tel_clean.isdigit():
                raise ValidationError('El teléfono debe tener formato XXX-XXX-XXXX (10 dígitos)')
            # Reformatear
            return f"{tel_clean[:3]}-{tel_clean[3:6]}-{tel_clean[6:]}"
        return telefono
    
    def clean_fecha_expiracion_licencia(self):
        """Validar que la fecha de expiración no sea en el pasado"""
        fecha = self.cleaned_data.get('fecha_expiracion_licencia')
        if fecha and fecha < date.today():
            raise ValidationError('La fecha de expiración no puede ser anterior a hoy')
        return fecha
    
    def clean_numero_licencia(self):
        """Validar unicidad del número de licencia"""
        numero_licencia = self.cleaned_data.get('numero_licencia')
        if numero_licencia:
            # Verificar si ya existe otra empresa con este número
            existing = EmpresaServicio.objects.filter(numero_licencia=numero_licencia)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError('Ya existe una empresa con este número de licencia')
        return numero_licencia