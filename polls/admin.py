from django.contrib import admin
from .models import Trabajador, Servicio, Documentos, Horarios

admin.site.register(Trabajador)
admin.site.register(Servicio)
admin.site.register(Documentos)
admin.site.register(Horarios)
