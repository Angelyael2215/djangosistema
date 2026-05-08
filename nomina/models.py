from decimal import Decimal, InvalidOperation

from django.db import models
from django.utils import timezone
from django.urls import reverse
from polls.models import Trabajador

class SalarioBase(models.Model):
    trabajador = models.OneToOneField(Trabajador, on_delete=models.CASCADE, related_name='salario_base')
    salario_diario = models.DecimalField(max_digits=10, decimal_places=2, help_text="Salario diario del trabajador")
    salario_mensual = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Salario mensual (calculado)")
    activo = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        try:
            salario = Decimal(self.salario_diario)
        except (InvalidOperation, TypeError, ValueError):
            salario = Decimal('0.00')
        self.salario_mensual = salario * Decimal('30')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Salario de {self.trabajador}: ${self.salario_diario}/día"

class PeriodoNomina(models.Model):
    PERIODO_CHOICES = (
        ('SEMANAL', 'Semanal'),
        ('QUINCENAL', 'Quincenal'),
        ('MENSUAL', 'Mensual'),
    )

    tipo_periodo = models.CharField(max_length=20, choices=PERIODO_CHOICES, default='QUINCENAL')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    descripcion = models.CharField(max_length=100, blank=True, null=True)
    cerrado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_tipo_periodo_display()} - {self.fecha_inicio} a {self.fecha_fin}"

    class Meta:
        ordering = ['-fecha_inicio']

class ReciboPago(models.Model):
    trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE, related_name='recibos')
    periodo = models.ForeignKey(PeriodoNomina, on_delete=models.CASCADE, related_name='recibos')
    fecha_emision = models.DateField(default=timezone.now)

    # Información del servicio / puesto
    puesto = models.CharField(max_length=128, blank=True, null=True)
    lugar_servicio = models.CharField(max_length=128, blank=True, null=True)
    horario_turno = models.CharField(max_length=64, blank=True, null=True)
    horas_por_turno = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Datos de asistencia
    dias_trabajados = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Días efectivamente trabajados")
    horas_extras = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Horas extras trabajadas")
    retardos = models.IntegerField(default=0, help_text="Número de retardos")

    # Cálculos automáticos
    salario_base = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_percepciones = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_deducciones = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    neto_pagar = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    notas = models.TextField(blank=True, null=True)

    def get_salario_record(self):
        try:
            return self.trabajador.salario_base
        except SalarioBase.DoesNotExist:
            return None

    def _to_decimal(self, value):
        try:
            return Decimal(value)
        except (InvalidOperation, TypeError, ValueError):
            return Decimal('0.00')

    def salario_por_dias(self):
        salario = self.get_salario_record()
        if salario:
            return salario.salario_diario * self._to_decimal(self.dias_trabajados)
        return Decimal('0.00')

    def horas_extras_monto(self):
        salario = self.get_salario_record()
        horas_extras = self._to_decimal(self.horas_extras)
        if salario and horas_extras > 0:
            return salario.salario_diario / Decimal('8') * Decimal('1.5') * horas_extras
        return Decimal('0.00')

    def retardos_monto(self):
        salario = self.get_salario_record()
        retardos = self._to_decimal(self.retardos)
        if salario and retardos > 0:
            return salario.salario_diario / Decimal('8') * retardos
        return Decimal('0.00')

    def total_percepciones_automaticas(self):
        return self.salario_por_dias() + self.horas_extras_monto()

    def total_impuestos(self):
        base = self.total_percepciones_automaticas() + sum(self._to_decimal(p.monto) for p in self.percepciones.all())
        return {
            'isr': base * Decimal('0.10'),
            'imss': base * Decimal('0.075'),
            'pension': base * Decimal('0.01125'),
        }

    def calcular_percepciones(self):
        total = self.total_percepciones_automaticas()
        for percepcion in self.percepciones.all():
            total += self._to_decimal(percepcion.monto)
        return total

    def calcular_deducciones(self):
        total = self.retardos_monto()
        impuestos = self.total_impuestos()
        total += impuestos['isr'] + impuestos['imss'] + impuestos['pension']
        for deduccion in self.deducciones.all():
            total += self._to_decimal(deduccion.monto)
        return total

    def save(self, *args, **kwargs):
        salario = self.get_salario_record()
        if salario:
            self.salario_base = salario.salario_diario

        if self.pk is None:
            # Save first to obtain a primary key before accessing related percepciones/deducciones.
            self.total_percepciones = Decimal('0.00')
            self.total_deducciones = Decimal('0.00')
            self.neto_pagar = Decimal('0.00')
            super().save(*args, **kwargs)
            return

        self.total_percepciones = self.calcular_percepciones()
        self.total_deducciones = self.calcular_deducciones()
        self.neto_pagar = self.total_percepciones - self.total_deducciones
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Recibo de {self.trabajador} - {self.periodo}"

    def get_absolute_url(self):
        return reverse('nomina:recibo_detail', args=[self.id])

    class Meta:
        unique_together = ('trabajador', 'periodo')

class Percepcion(models.Model):
    TIPO_CHOICES = (
        ('BONO', 'Bono'),
        ('HORAS_EXTRA', 'Horas Extra'),
        ('VACACIONES', 'Vacaciones'),
        ('OTROS', 'Otros'),
    )

    recibo = models.ForeignKey(ReciboPago, on_delete=models.CASCADE, related_name='percepciones')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='BONO')
    descripcion = models.CharField(max_length=100)
    monto = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.monto}"

class Deduccion(models.Model):
    TIPO_CHOICES = (
        ('PRESTAMO', 'Préstamo'),
        ('FALTAS', 'Faltas'),
        ('OTROS', 'Otros'),
    )

    recibo = models.ForeignKey(ReciboPago, on_delete=models.CASCADE, related_name='deducciones')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='PRESTAMO')
    descripcion = models.CharField(max_length=100)
    monto = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.monto}"
