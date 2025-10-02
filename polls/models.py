
from django.db import models
from django.utils import timezone

class Trabajador(models.Model):
	nombre = models.CharField(max_length=128)
	apellido = models.CharField(max_length=128, blank=True, null=True)
	fecha_ingreso = models.DateTimeField(default=timezone.now)
	estado = models.CharField(max_length=64, default="Activo", blank=True, null=True)

	def __str__(self):
		return f"{self.nombre} {self.apellido or ''}".strip()

class Servicio(models.Model):
	trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE, related_name="servicios")
	nombre_lugar = models.CharField(max_length=128)
	fecha_inicio = models.DateTimeField(default=timezone.now)
	fecha_fin = models.DateTimeField(blank=True, null=True)
	direccion = models.CharField(max_length=128)

	def __str__(self):
		return f"{self.nombre_lugar} ({self.trabajador})"

class Documentos(models.Model):
	trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE, related_name="documentos")
	cuip = models.CharField(max_length=128)
	antecedentes = models.CharField(max_length=128)
	situacion_fiscal = models.CharField(max_length=128)
	curp = models.CharField(max_length=128)
	nss = models.CharField(max_length=128)
	cursos = models.CharField(max_length=128)
	certificado_estudios = models.CharField(max_length=128)

	def __str__(self):
		return f"Documentos de {self.trabajador}"

class Horarios(models.Model):
	trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE, related_name="horarios")
	hora = models.CharField(max_length=128)
	dia = models.CharField(max_length=128)
	mes = models.CharField(max_length=128)
	anio = models.CharField(max_length=128)

	def __str__(self):
		return f"Horario de {self.trabajador}: {self.hora}, {self.dia}/{self.mes}/{self.anio}"
