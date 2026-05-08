from django.contrib import admin
from .models import SalarioBase, PeriodoNomina, ReciboPago, Percepcion, Deduccion

@admin.register(SalarioBase)
class SalarioBaseAdmin(admin.ModelAdmin):
    list_display = ('trabajador', 'salario_diario', 'salario_mensual', 'activo')
    list_filter = ('activo',)

@admin.register(PeriodoNomina)
class PeriodoNominaAdmin(admin.ModelAdmin):
    list_display = ('tipo_periodo', 'fecha_inicio', 'fecha_fin', 'cerrado')
    list_filter = ('tipo_periodo', 'cerrado')

@admin.register(ReciboPago)
class ReciboPagoAdmin(admin.ModelAdmin):
    list_display = ('trabajador', 'periodo', 'salario_base', 'neto_pagar', 'fecha_emision')
    list_filter = ('periodo', 'fecha_emision')

@admin.register(Percepcion)
class PercepcionAdmin(admin.ModelAdmin):
    list_display = ('recibo', 'tipo', 'descripcion', 'monto')

@admin.register(Deduccion)
class DeduccionAdmin(admin.ModelAdmin):
    list_display = ('recibo', 'tipo', 'descripcion', 'monto')
