
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, BaseUserManager

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
