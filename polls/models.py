
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, BaseUserManager
import os

def documentos_path(instance, filename):
	"""Genera la ruta para almacenar documentos por ID de trabajador"""
	return os.path.join('documentos', str(instance.trabajador.id), filename)

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El correo electrónico es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    ROLES = (
        ('ADMIN', 'Administrador'),
        ('HR', 'Recursos Humanos'),
        ('VIEW', 'Vista'),
    )
    
    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLES, default='VIEW')
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = CustomUserManager()
    
    def __str__(self):
        return self.email

class Horarios(models.Model):
	TURNOS = (
		('MATUTINO', 'Matutino'),
		('VESPERTINO', 'Vespertino'),
		('NOCTURNO', 'Nocturno'),
	)
	
	nombre_turno = models.CharField(max_length=20, choices=TURNOS, blank=True, null=True)
	hora_entrada = models.TimeField(blank=True, null=True)
	hora_salida = models.TimeField(blank=True, null=True)

	def __str__(self):
		return f"{self.get_nombre_turno_display()} ({self.hora_entrada} - {self.hora_salida})"
	
	class Meta:
		unique_together = ('nombre_turno',)
		ordering = ['nombre_turno']

class Trabajador(models.Model):
	nombre = models.CharField(max_length=128)
	# mantenemos `apellido` como apellido paterno para compatibilidad
	apellido = models.CharField(max_length=128, blank=True, null=True)
	apellido_materno = models.CharField(max_length=128, blank=True, null=True)
	rfc = models.CharField(max_length=64, blank=True, null=True)
	no_exterior = models.CharField(max_length=64, blank=True, null=True)
	curp_text = models.CharField(max_length=128, blank=True, null=True)
	codigo_postal = models.CharField(max_length=16, blank=True, null=True)
	cuip_text = models.CharField(max_length=128, blank=True, null=True)
	entidad_federativa = models.CharField(max_length=128, blank=True, null=True)
	nss_text = models.CharField(max_length=128, blank=True, null=True)
	calle = models.CharField(max_length=256, blank=True, null=True)
	horario = models.ForeignKey(Horarios, on_delete=models.SET_NULL, blank=True, null=True, related_name="trabajadores")
	calle_servicio = models.CharField(max_length=256, blank=True, null=True)
	no_exterior_servicio = models.CharField(max_length=64, blank=True, null=True)
	entidad_servicio = models.CharField(max_length=128, blank=True, null=True)
	estado_servicio = models.CharField(max_length=64, blank=True, null=True)
	fecha_ingreso = models.DateTimeField(default=timezone.now)
	estado = models.CharField(max_length=64, default="Activo", blank=True, null=True)

	def __str__(self):
		return f"{self.nombre} {self.apellido or ''}".strip()
	
	def get_horario_display(self):
		"""Retorna el horario con horas de entrada y salida"""
		if self.horario:
			return f"{self.horario.hora_entrada} - {self.horario.hora_salida}"
		return "-"

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
	cuip = models.FileField(upload_to=documentos_path, blank=True, null=True)
	antecedentes = models.FileField(upload_to=documentos_path, blank=True, null=True)
	situacion_fiscal = models.FileField(upload_to=documentos_path, blank=True, null=True)
	curp = models.FileField(upload_to=documentos_path, blank=True, null=True)
	nss = models.FileField(upload_to=documentos_path, blank=True, null=True)
	cursos = models.FileField(upload_to=documentos_path, blank=True, null=True)
	certificado_estudios = models.FileField(upload_to=documentos_path, blank=True, null=True)

	def __str__(self):
		return f"Documentos de {self.trabajador}"

class 	Auditoria(models.Model):
	"""Registra cambios de estado en trabajadores"""
	trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE, related_name="auditorias")
	usuario = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
	accion = models.CharField(max_length=64)  # 'BAJA', 'ALTA', 'REACTIVACION', etc.
	estado_anterior = models.CharField(max_length=64, blank=True, null=True)
	estado_nuevo = models.CharField(max_length=64, blank=True, null=True)
	motivo = models.TextField(blank=True, null=True)
	fecha_cambio = models.DateTimeField(default=timezone.now)
	
	def __str__(self):
		return f"Auditoría: {self.accion} - {self.trabajador} por {self.usuario} el {self.fecha_cambio}"
	
	class Meta:
		ordering = ['-fecha_cambio']
		verbose_name_plural = 'Auditorías'
