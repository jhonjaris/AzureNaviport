from django import forms
from .models import Persona, DocumentoPersonal


class PersonaForm(forms.ModelForm):
    class Meta:
        model = Persona
        fields = ['nombre', 'apellido', 'cedula', 'pasaporte', 'email', 'telefono', 'cargo', 'licencia_conducir']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre'
            }),
            'apellido': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido'
            }),
            'cedula': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'XXX-XXXXXXX-X',
                'pattern': r'\d{3}-\d{7}-\d{1}'
            }),
            'pasaporte': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de pasaporte'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'ejemplo@correo.com'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '809-123-4567'
            }),
            'cargo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Conductor, Operador, Técnico'
            }),
            'licencia_conducir': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de licencia'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        if cedula:
            # Verificar si ya existe EN LA MISMA EMPRESA (excluyendo la instancia actual en caso de edición)
            queryset = Persona.objects.filter(cedula=cedula, activo=True)

            # Solo validar dentro de la empresa si se proporcionó
            if self.empresa:
                queryset = queryset.filter(empresa=self.empresa)

            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise forms.ValidationError('Ya existe una persona con esta cédula en su empresa.')

        return cedula

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if telefono:
            # Limpiar cualquier formato existente
            telefono_limpio = ''.join(filter(str.isdigit, telefono))

            # Verificar que tenga 10 dígitos (para RD)
            if len(telefono_limpio) == 10:
                # Formatear como (XXX) XXX-XXXX
                telefono = f"({telefono_limpio[:3]}) {telefono_limpio[3:6]}-{telefono_limpio[6:]}"
            elif len(telefono_limpio) != 0:  # Si no está vacío pero tampoco tiene 10 dígitos
                raise forms.ValidationError('El teléfono debe tener 10 dígitos (formato: (809) 123-4567)')

        return telefono

    def clean(self):
        cleaned_data = super().clean()
        cedula = cleaned_data.get('cedula')
        pasaporte = cleaned_data.get('pasaporte')

        # Validar que al menos tenga cédula o pasaporte
        if not cedula and not pasaporte:
            raise forms.ValidationError('Debe proporcionar al menos una cédula o un pasaporte.')

        return cleaned_data


class DocumentoPersonalForm(forms.ModelForm):
    class Meta:
        model = DocumentoPersonal
        fields = ['tipo_documento', 'numero_documento', 'archivo', 'fecha_vencimiento']
        widgets = {
            'tipo_documento': forms.Select(attrs={
                'class': 'form-control'
            }),
            'numero_documento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número del documento (opcional)'
            }),
            'archivo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'fecha_vencimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if archivo:
            # Verificar tamaño (5MB máximo)
            if archivo.size > 5 * 1024 * 1024:
                raise forms.ValidationError('El archivo es demasiado grande. Máximo 5MB permitido.')

            # Verificar extensión
            import os
            file_extension = os.path.splitext(archivo.name)[1].lower()
            allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
            if file_extension not in allowed_extensions:
                raise forms.ValidationError('Formato de archivo no permitido. Use PDF, JPG o PNG.')

        return archivo

    def clean(self):
        cleaned_data = super().clean()
        tipo_documento = cleaned_data.get('tipo_documento')
        persona = getattr(self, 'persona', None)

        # Verificar si ya existe un documento de este tipo para esta persona
        if persona and tipo_documento:
            existing = DocumentoPersonal.objects.filter(
                persona=persona,
                tipo_documento=tipo_documento
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise forms.ValidationError(f'Ya existe un documento de tipo "{self.get_tipo_documento_display(tipo_documento)}" para esta persona.')

        return cleaned_data

    def get_tipo_documento_display(self, value):
        choices_dict = dict(DocumentoPersonal.TIPO_DOCUMENTO_CHOICES)
        return choices_dict.get(value, value)