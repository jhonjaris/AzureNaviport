from django import forms
from .models import Vehiculo, DocumentoVehiculo


class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = ['placa', 'marca', 'modelo', 'ano', 'color', 'tipo_vehiculo', 'numero_chasis', 'numero_motor', 'notas_adicionales']
        widgets = {
            'placa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'A123456 o AB123456',
                'style': 'text-transform: uppercase;'
            }),
            'marca': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Toyota, Ford, Honda, etc.'
            }),
            'modelo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Corolla, F-150, Civic, etc.'
            }),
            'ano': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '2020',
                'min': '1900',
                'max': '2030'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Blanco, Negro, Rojo, etc.'
            }),
            'tipo_vehiculo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'numero_chasis': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número VIN (opcional)'
            }),
            'numero_motor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de motor (opcional)'
            }),
            'notas_adicionales': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas o comentarios adicionales sobre el vehículo (opcional)'
            }),
        }

    def clean_placa(self):
        placa = self.cleaned_data.get('placa')
        if placa:
            # Convertir a mayúsculas
            placa = placa.upper()

            # Verificar si ya existe (excluyendo la instancia actual en caso de edición)
            queryset = Vehiculo.objects.filter(placa=placa, activo=True)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise forms.ValidationError('Ya existe un vehículo con esta placa.')

        return placa

    def clean_ano(self):
        ano = self.cleaned_data.get('ano')
        if ano:
            import datetime
            current_year = datetime.datetime.now().year
            if ano < 1900 or ano > current_year + 1:
                raise forms.ValidationError(f'El año debe estar entre 1900 y {current_year + 1}')
        return ano


class DocumentoVehiculoForm(forms.ModelForm):
    class Meta:
        model = DocumentoVehiculo
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
        vehiculo = getattr(self, 'vehiculo', None)

        # Verificar si ya existe un documento de este tipo para este vehículo
        if vehiculo and tipo_documento:
            existing = DocumentoVehiculo.objects.filter(
                vehiculo=vehiculo,
                tipo_documento=tipo_documento
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise forms.ValidationError(f'Ya existe un documento de tipo "{self.get_tipo_documento_display(tipo_documento)}" para este vehículo.')

        return cleaned_data

    def get_tipo_documento_display(self, value):
        choices_dict = dict(DocumentoVehiculo.TIPO_DOCUMENTO_CHOICES)
        return choices_dict.get(value, value)