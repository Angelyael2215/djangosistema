import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OrticorpSystem.settings')
django.setup()

from polls.models import Horarios, Trabajador

# Ver horarios existentes
print("Horarios existentes:")
for h in Horarios.objects.all():
    print(f"  {h.id}: {h.nombre_turno} - {h.hora_entrada} a {h.hora_salida}")

# Ver trabajadores con horarios
print("\nTrabajadores con horarios:")
for t in Trabajador.objects.filter(horario__isnull=False):
    print(f"  {t.nombre}: {t.get_horario_display()}")

# Test: Create a horario if none exist
if not Horarios.objects.exists():
    print("\nCreando horarios de prueba...")
    matutino = Horarios.objects.create(
        nombre_turno='MATUTINO',
        hora_entrada='06:00',
        hora_salida='14:00'
    )
    print(f"  Creado: {matutino}")
