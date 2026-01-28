from django import forms
from .models import Solicitud, Vehiculo, DocumentoAdjunto, LugarPuerto, MotivoAcceso
from evaluacion.models import Servicio

class SolicitudForm(forms.ModelForm):
    servicios_solicitados = forms.ModelMultipleChoiceField(
        queryset=Servicio.objects.none(),  # Se establecerá dinámicamente
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'servicios-checkboxes'
        }),
        required=False,
        help_text='Selecciona los servicios que necesitas para esta solicitud (solo servicios autorizados para tu empresa)'
    )

    # Campo personalizado para servicios
    servicio_seleccionado = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Servicio a ofrecer *'
    )
    
    class Meta:
        model = Solicitud
        fields = [
            'puerto_destino', 'lugar_destino', 'motivo_acceso', 'fecha_ingreso', 'hora_ingreso',
            'fecha_salida', 'hora_salida', 'servicios_solicitados', 'descripcion'
        ]
        widgets = {
            'puerto_destino': forms.Select(attrs={
                'class': 'form-control',
                'required': True,
                'id': 'id_puerto_destino'
            }),
            'lugar_destino': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_lugar_destino'
            }),
            'motivo_acceso': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'fecha_ingreso': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True
            }),
            'hora_ingreso': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'required': True
            }),
            'fecha_salida': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True
            }),
            'hora_salida': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'required': True
            }),
            'descripcion': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Describa detalladamente las actividades a realizar, equipos a utilizar, personal involucrado, etc.',
                'required': True
            }),
        }
        labels = {
            'puerto_destino': 'Puerto de Destino *',
            'lugar_destino': 'Lugar de Destino',
            'motivo_acceso': 'Motivo del Acceso *',
            'fecha_ingreso': 'Fecha de Ingreso *',
            'hora_ingreso': 'Hora de Ingreso *',
            'fecha_salida': 'Fecha de Salida *',
            'hora_salida': 'Hora de Salida *',
            'descripcion': 'Descripción Detallada *',
        }

    def __init__(self, *args, **kwargs):
        # Extraer el usuario del contexto
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Personalizar las opciones de los campos select
        self.fields['puerto_destino'].empty_label = "Seleccionar puerto"
        self.fields['lugar_destino'].empty_label = "Seleccionar lugar"
        self.fields['lugar_destino'].queryset = self.fields['lugar_destino'].queryset.none()  # Inicialmente vacío
        self.fields['lugar_destino'].required = False  # Hacer el campo realmente opcional
        self.fields['motivo_acceso'].empty_label = "Seleccionar motivo"

        # Configurar el campo de servicio personalizado
        if user and hasattr(user, 'empresa') and user.empresa:
            try:
                # Obtener todos los servicios autorizados para la empresa
                servicios_autorizados = user.empresa.todos_los_servicios()

                if servicios_autorizados:
                    # Configurar choices para el campo servicio_seleccionado
                    choices = [('', 'Seleccionar servicio')]
                    for servicio in servicios_autorizados:
                        choices.append((servicio.id, servicio.nombre))

                    self.fields['servicio_seleccionado'].choices = choices
                    self.fields['servicio_seleccionado'].help_text = f'Servicios autorizados para {user.empresa.nombre} ({servicios_autorizados.count()} disponibles)'
                    self.fields['servicio_seleccionado'].required = True
                else:
                    # Si no hay servicios autorizados, no mostrar opciones
                    self.fields['servicio_seleccionado'].choices = [('', 'Seleccionar servicio')]
                    self.fields['servicio_seleccionado'].help_text = 'Tu empresa no tiene servicios autorizados. Contacta al administrador.'
                    self.fields['servicio_seleccionado'].widget.attrs['disabled'] = True
            except Exception as e:
                print(f"Error configurando servicios: {e}")
                # En caso de error, mantener comportamiento original
                pass
        else:
            # Si no hay empresa, no mostrar opciones
            self.fields['servicio_seleccionado'].choices = [('', 'Seleccionar servicio')]
            self.fields['servicio_seleccionado'].help_text = 'Usuario sin empresa asignada. Contacta al administrador.'
            self.fields['servicio_seleccionado'].widget.attrs['disabled'] = True

        # Ocultar el campo motivo_acceso original
        self.fields['motivo_acceso'].widget = forms.HiddenInput()
        self.fields['motivo_acceso'].required = False
        
        # Configurar servicios según la empresa del usuario
        if user and hasattr(user, 'empresas_representadas'):
            try:
                empresa = user.empresas_representadas.first()
                if empresa:
                    # Obtener todos los servicios autorizados para la empresa
                    servicios_autorizados = empresa.todos_los_servicios()
                    self.fields['servicios_solicitados'].queryset = servicios_autorizados.filter(activo=True).order_by('codigo')
                    
                    if servicios_autorizados.exists():
                        self.fields['servicios_solicitados'].help_text = f'Servicios autorizados para {empresa.nombre} ({servicios_autorizados.count()} disponibles)'
                    else:
                        self.fields['servicios_solicitados'].help_text = 'Tu empresa no tiene servicios autorizados. Contacta al administrador.'
                        self.fields['servicios_solicitados'].widget.attrs['disabled'] = True
                else:
                    self.fields['servicios_solicitados'].help_text = 'No tienes una empresa asignada. Contacta al administrador.'
                    self.fields['servicios_solicitados'].widget.attrs['disabled'] = True
            except Exception:
                self.fields['servicios_solicitados'].help_text = 'Error al cargar servicios autorizados.'
                self.fields['servicios_solicitados'].widget.attrs['disabled'] = True
        else:
            self.fields['servicios_solicitados'].help_text = 'Usuario no válido para solicitar servicios.'
            self.fields['servicios_solicitados'].widget.attrs['disabled'] = True

    def clean(self):
        """Validación personalizada del formulario completo"""
        cleaned_data = super().clean()
        servicio_seleccionado = cleaned_data.get('servicio_seleccionado')

        if servicio_seleccionado:
            try:
                # Convertir el servicio seleccionado en un motivo de acceso
                servicio = Servicio.objects.get(id=servicio_seleccionado)

                # Buscar un motivo de acceso compatible con este servicio
                motivo_compatible = MotivoAcceso.objects.filter(
                    servicios_relacionados=servicio,
                    activo=True
                ).first()

                if motivo_compatible:
                    cleaned_data['motivo_acceso'] = motivo_compatible
                else:
                    # Si no hay motivo específico, crear uno genérico
                    motivo_generico, created = MotivoAcceso.objects.get_or_create(
                        nombre='Servicio Autorizado',
                        defaults={
                            'descripcion': 'Motivo genérico para servicios autorizados',
                            'activo': True
                        }
                    )
                    if created:
                        motivo_generico.servicios_relacionados.add(servicio)
                    cleaned_data['motivo_acceso'] = motivo_generico

            except Servicio.DoesNotExist:
                raise forms.ValidationError('Servicio seleccionado no válido')
            except Exception as e:
                print(f"Error procesando servicio: {e}")
                raise forms.ValidationError('Error al procesar el servicio seleccionado')

        return cleaned_data

class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = ['placa', 'tipo_vehiculo', 'conductor_nombre', 'conductor_licencia']
        widgets = {
            'placa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ABC-1234',
                'pattern': '[A-Z]{1,3}-[0-9]{4}',
                'title': 'Formato: ABC-1234'
            }),
            'tipo_vehiculo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'conductor_nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo del conductor'
            }),
            'conductor_licencia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de licencia'
            }),
        }
        labels = {
            'placa': 'Placa del Vehículo',
            'tipo_vehiculo': 'Tipo de Vehículo',
            'conductor_nombre': 'Conductor',
            'conductor_licencia': 'Licencia de Conducir',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo_vehiculo'].empty_label = "Seleccionar tipo"

class DocumentoAdjuntoForm(forms.ModelForm):
    class Meta:
        model = DocumentoAdjunto
        fields = ['tipo_documento', 'archivo']
        widgets = {
            'tipo_documento': forms.Select(attrs={
                'class': 'form-control'
            }),
            'archivo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx',
                'multiple': False
            }),
        }
        labels = {
            'tipo_documento': 'Tipo de Documento',
            'archivo': 'Seleccionar Archivo',
        }

# Formset para manejar múltiples vehículos
VehiculoFormSet = forms.inlineformset_factory(
    Solicitud, 
    Vehiculo, 
    form=VehiculoForm,
    extra=1,  # Número de formularios vacíos adicionales
    min_num=1,  # Mínimo un vehículo
    validate_min=True,
    can_delete=True
)

# Formset para manejar múltiples documentos
DocumentoFormSet = forms.inlineformset_factory(
    Solicitud,
    DocumentoAdjunto,
    form=DocumentoAdjuntoForm,
    extra=2,  # Formularios vacíos adicionales
    can_delete=True
) 