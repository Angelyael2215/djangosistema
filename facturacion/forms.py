from django import forms
from .models import Factura, FacturaItem, Cliente
from django.forms import inlineformset_factory

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre','rfc','direccion','email']

class FacturaForm(forms.ModelForm):
    class Meta:
        model = Factura
        fields = ['cliente','fecha','moneda','forma_pago','metodo_pago','notas','estado']
        widgets = {
            'fecha': forms.DateInput(attrs={'type':'date'})
        }

class FacturaItemForm(forms.ModelForm):
    class Meta:
        model = FacturaItem
        fields = ('descripcion','cantidad','precio_unitario')
        widgets = {
            'cantidad': forms.NumberInput(attrs={'step':'0.01','min':'0','style':'width:100%;padding:6px;border:1px solid #ddd;border-radius:4px;'}),
            'precio_unitario': forms.NumberInput(attrs={'step':'0.01','min':'0','style':'width:100%;padding:6px;border:1px solid #ddd;border-radius:4px;'}),
            'descripcion': forms.TextInput(attrs={'style':'width:100%;padding:6px;border:1px solid #ddd;border-radius:4px;'})
        }

FacturaItemFormSet = inlineformset_factory(Factura, FacturaItem, form=FacturaItemForm, fields=('descripcion','cantidad','precio_unitario'), extra=1, can_delete=True)
