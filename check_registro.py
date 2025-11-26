import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','OrticorpSystem.settings')
import django
django.setup()
from django.test import Client
c=Client()
r=c.get('/registro/')
print('STATUS', r.status_code)
print('LENGTH', len(r.content))
print(r.content.decode('utf-8')[:400])
