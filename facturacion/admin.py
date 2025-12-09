from django.contrib import admin
from .models import Cliente, Factura, FacturaItem

class FacturaItemInline(admin.TabularInline):
    model = FacturaItem
    extra = 1

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rfc', 'email')

@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ('folio', 'cliente', 'fecha', 'total', 'estado')
    inlines = [FacturaItemInline]
    readonly_fields = ('folio','uuid','created_at','updated_at')

@admin.register(FacturaItem)
class FacturaItemAdmin(admin.ModelAdmin):
    list_display = ('factura','descripcion','cantidad','precio_unitario','importe')
