from django import forms
from .models import Trabajador, Documentos, Horarios

class TrabajadorRegistroForm(forms.ModelForm):
    class Meta:
        model = Trabajador
        fields = ['nombre', 'apellido', 'estado', 'horario']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del trabajador',
                'required': True
            }),
            'apellido': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido del trabajador',
                'required': True
            }),
            'estado': forms.Select(attrs={
                'class': 'form-control'
            }),
            'horario': forms.Select(attrs={
                'class': 'form-control'
            })
        }

class DocumentosForm(forms.ModelForm):
    class Meta:
        model = Documentos
        fields = ['cuip', 'antecedentes', 'situacion_fiscal', 'curp', 'nss', 'cursos', 'certificado_estudios']
        widgets = {
            'cuip': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
            }),
            'antecedentes': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
            }),
            'situacion_fiscal': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
            }),
            'curp': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
            }),
            'nss': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
            }),
            'cursos': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
            }),
            'certificado_estudios': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
            })
        }

class HorariosForm(forms.ModelForm):
    class Meta:
        model = Horarios
        fields = ['nombre_turno', 'hora_entrada', 'hora_salida']
        widgets = {
            'nombre_turno': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'hora_entrada': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'required': True
            }),
            'hora_salida': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'required': True
            })
        }
    
    def clean(self):
        cleaned_data = super().clean()
        nombre_turno = cleaned_data.get('nombre_turno')
        hora_entrada = cleaned_data.get('hora_entrada')
        hora_salida = cleaned_data.get('hora_salida')
        
        if not nombre_turno:
            raise forms.ValidationError('El turno es requerido.')
        if not hora_entrada:
            raise forms.ValidationError('La hora de entrada es requerida.')
        if not hora_salida:
            raise forms.ValidationError('La hora de salida es requerida.')
        
        return cleaned_data
