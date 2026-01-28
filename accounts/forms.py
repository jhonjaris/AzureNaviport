from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from .models import User, Empresa
import re

class CustomAuthenticationForm(AuthenticationForm):
    """Formulario de login simple con usuario y contraseña"""
    username = forms.CharField(
        label='Usuario',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su nombre de usuario',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••••'
        })
    )
    remember_me = forms.BooleanField(
        required=False, 
        label='Recordarme',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = ['username', 'password', 'remember_me']

class UserRegistrationForm(forms.ModelForm):
    """Formulario para registro interno de usuarios con todos los datos"""
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirmar Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'cedula_rnc', 'telefono', 'role', 'empresa'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'cedula_rnc': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '000-0000000-0 para cédula o 000-00000-0 para RNC'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '809-555-0000'
            }),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'empresa': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        
        if not username:
            raise ValidationError("El nombre de usuario es requerido.")
        
        # Para nuevos usuarios (no tiene pk), validar que sea un email válido
        if not self.instance.pk:
            try:
                validate_email(username)
            except ValidationError:
                raise ValidationError(
                    "Para nuevos usuarios, el nombre de usuario debe ser una dirección de correo electrónico válida. "
                    "Ejemplo: usuario@ejemplo.com"
                )
            
            # Verificar que el formato sea correcto con regex adicional
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, username):
                raise ValidationError(
                    "El formato del correo electrónico no es válido. "
                    "Debe tener la forma: nombre@dominio.com"
                )
        
        # Verificar que no exista otro usuario con este username
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Ya existe un usuario con este nombre de usuario/correo.")
        
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
        
        # Para nuevos usuarios, el email debe coincidir con el username
        username = self.cleaned_data.get('username')
        if not self.instance.pk and username and email.lower() != username.lower():
            raise ValidationError(
                "Para nuevos usuarios, el correo electrónico debe ser igual al nombre de usuario."
            )
        
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
        user.set_password(self.cleaned_data["password1"])
        
        # Para nuevos usuarios, asegurar que email y username sean iguales
        if not user.pk:
            user.email = self.cleaned_data["username"].lower()
        
        if commit:
            user.save()
        return user 