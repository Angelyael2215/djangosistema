#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OrticorpSystem.settings')
django.setup()

from polls.models import CustomUser

# Crear superusuario
if not CustomUser.objects.filter(email='admin@orticorp.com').exists():
    CustomUser.objects.create_superuser(
        email='admin@orticorp.com',
        password='admin123'
    )
    print("✅ Superusuario creado exitosamente")
    print("Email: admin@orticorp.com")
    print("Contraseña: admin123")
else:
    print("El usuario admin ya existe")
