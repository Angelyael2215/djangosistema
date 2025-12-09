import os
import sys
import django
from django.contrib.auth import get_user_model

# Ajustar ruta del proyecto
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OrticorpSystem.settings')
django.setup()

from django.test import Client
from polls.models import Trabajador, Auditoria, CustomUser

client = Client()

HR_EMAIL = 'hr_test@example.com'
HR_PASS = 'HrPass123!'

# Crear usuario HR si no existe
User = get_user_model()
user_qs = User.objects.filter(email=HR_EMAIL)
if not user_qs.exists():
    print('Creando usuario HR de prueba...')
    hr = User.objects.create_user(email=HR_EMAIL, password=HR_PASS, role='HR')
else:
    hr = user_qs.first()
    hr.set_password(HR_PASS)
    hr.save()
    print('Usuario HR ya existe; contraseña reseteada para la prueba.')

# Crear trabajador de prueba
trabajador = Trabajador.objects.create(nombre='Test', apellido='Worker', estado='Activo')
print(f'Creado Trabajador id={trabajador.id}')

# Login (especificar HTTP_HOST para evitar DisallowedHost en test client)
resp = client.post('/login/', {'username': HR_EMAIL, 'password': HR_PASS}, HTTP_HOST='127.0.0.1')
print('Login status_code=', resp.status_code)

# Realizar POST a baja/ (incluir HTTP_HOST)
resp2 = client.post('/baja/', {'trabajador_id': trabajador.id, 'motivo': 'Prueba automatizada'}, follow=True, HTTP_HOST='127.0.0.1')
print('POST /baja/ status_code=', resp2.status_code)

# Refrescar trabajador
trabajador.refresh_from_db()
print('Trabajador estado after POST:', trabajador.estado)

# Comprobar auditoria
aud = Auditoria.objects.filter(trabajador=trabajador).order_by('-fecha_cambio').first()
if aud:
    print('Auditoria creada: accion=', aud.accion, 'usuario=', aud.usuario.email, 'motivo=', aud.motivo)
else:
    print('No se creó auditoria')

# Limpieza: opcional (no borrar objects to keep trace)
print('Fin del test.')
