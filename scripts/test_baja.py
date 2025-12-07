import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OrticorpSystem.settings')
# Ensure project root is in sys.path so imports like `OrticorpSystem` work
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import django
django.setup()
from django.test import Client
from polls.models import Trabajador, Auditoria

# Ensure there's at least one activo trabajador
trabajador = Trabajador.objects.filter(estado='Activo').first()
if not trabajador:
    trabajador = Trabajador.objects.create(nombre='Test', apellido='User', estado='Activo')

client = Client()
# login as HR user
logged_in = client.login(username='rh@example.com', password='rh123')
print('Logged in as HR?', logged_in)
# perform POST to baja (set HTTP_HOST to avoid DisallowedHost from test client)
resp = client.post('/baja/', {'trabajador_id': trabajador.id, 'motivo': 'Prueba automática'}, HTTP_HOST='127.0.0.1:8000')
print('POST /baja/ status code:', resp.status_code)
# refresh from db
trabajador.refresh_from_db()
print('Trabajador estado after POST:', trabajador.estado)
# check auditoria record
aud = Auditoria.objects.filter(trabajador=trabajador).first()
print('Auditoria created?', bool(aud), 'accion:', getattr(aud, 'accion', None))
