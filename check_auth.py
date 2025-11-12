import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','OrticorpSystem.settings')
django.setup()
from django.contrib.auth import authenticate

u = authenticate(username='admin@example.com', password='admin')
print('AUTH OK' if u else 'AUTH FAIL')
print(repr(u))

u2 = authenticate(username='rh@example.com', password='rh123')
print('HR OK' if u2 else 'HR FAIL', repr(u2))

u3 = authenticate(username='view@example.com', password='view123')
print('VIEW OK' if u3 else 'VIEW FAIL', repr(u3))
