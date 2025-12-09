import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','OrticorpSystem.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
users = [
    ('admin@example.com','admin','ADMIN',True),
    ('rh@example.com','rh123','HR',False),
    ('view@example.com','view123','VIEW',False),
]
for email,pwd,role,is_staff in users:
    u = User.objects.filter(email=email).first()
    if not u:
        u = User.objects.create_user(email=email, password=pwd, role=role)
        if is_staff:
            u.is_staff = True
            u.is_superuser = True
        u.save()
        print('Created', email)
    else:
        u.set_password(pwd)
        u.role = role
        if is_staff:
            u.is_staff = True
            u.is_superuser = True
        u.is_active = True
        u.save()
        print('Updated', email)
print('Done')
