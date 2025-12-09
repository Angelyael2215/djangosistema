from django.db import models
from django.urls import reverse
from django.utils import timezone
import uuid

class Cliente(models.Model):
    nombre = models.CharField(max_length=200)
    rfc = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} ({self.rfc or 'RFC N/A'})"

class Factura(models.Model):
    FOLIO_PREFIX = 'FAC'

    folio = models.CharField(max_length=64, unique=True, editable=False)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='facturas')
    fecha = models.DateField(default=timezone.now)
    moneda = models.CharField(max_length=8, default='MXN')
    forma_pago = models.CharField(max_length=64, blank=True, null=True)
    metodo_pago = models.CharField(max_length=64, blank=True, null=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    impuestos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=(('BORRADOR', 'Borrador'), ('EMITIDA', 'Emitida'), ('PAGADA', 'Pagada')), default='BORRADOR')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    notas = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha', '-id']

    def save(self, *args, **kwargs):
        if not self.folio:
            # Simple folio generation: prefix + year + id placeholder; user should run migrations then save again to get id
            # We'll set a unique folio based on UUID to avoid collisions on first save
            self.folio = f"{self.FOLIO_PREFIX}-{str(self.uuid)[:8]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.folio} - {self.cliente}"

    def get_absolute_url(self):
        return reverse('facturacion:factura_detail', args=[self.id])

class FacturaItem(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='items')
    descripcion = models.CharField(max_length=255)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    importe = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.importe = (self.cantidad or 0) * (self.precio_unitario or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.descripcion} x{self.cantidad} = {self.importe}"
