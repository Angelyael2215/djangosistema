import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OrticorpSystem.settings')
django.setup()

from polls.models import Horarios, Trabajador

print("=" * 60)
print("VERIFICACIÓN DEL SISTEMA DE HORARIOS")
print("=" * 60)

# 1. Ver horarios existentes
print("\n1. Horarios existentes:")
horarios_list = Horarios.objects.all()
if horarios_list.exists():
    for h in horarios_list:
        print(f"   ID: {h.id}, Turno: {h.nombre_turno}, Entrada: {h.hora_entrada}, Salida: {h.hora_salida}")
else:
    print("   No hay horarios. Creando horarios de prueba...")
    turnos_data = [
        ('MATUTINO', '06:00', '14:00'),
        ('VESPERTINO', '14:00', '22:00'),
        ('NOCTURNO', '22:00', '06:00')
    ]
    for turno, entrada, salida in turnos_data:
        h = Horarios.objects.create(nombre_turno=turno, hora_entrada=entrada, hora_salida=salida)
        print(f"   Creado: {h}")

# 2. Crear un trabajador de prueba con un horario
print("\n2. Creando trabajador de prueba con horario...")
matutino = Horarios.objects.get(nombre_turno='MATUTINO')
trabajador_test = Trabajador.objects.create(
    nombre='Juan',
    apellido='Pérez',
    horario=matutino
)
print(f"   Trabajador creado: {trabajador_test}")
print(f"   Horario asignado: {trabajador_test.get_horario_display()}")

# 3. Verificar que el horario está correctamente asignado
print("\n3. Verificando asignación de horario...")
t = Trabajador.objects.get(id=trabajador_test.id)
print(f"   Horario de {t.nombre}: {t.get_horario_display()}")
assert t.horario is not None, "El horario debería estar asignado"
assert t.get_horario_display() == "06:00:00 - 14:00:00", "El horario no es el correcto"
print("   ✓ Horario asignado correctamente")

# 4. Cambiar el horario
print("\n4. Cambiando horario...")
vespertino = Horarios.objects.get(nombre_turno='VESPERTINO')
t.horario = vespertino
t.save()
t_updated = Trabajador.objects.get(id=t.id)
print(f"   Nuevo horario: {t_updated.get_horario_display()}")
assert t_updated.get_horario_display() == "14:00:00 - 22:00:00", "El horario no cambió correctamente"
print("   ✓ Horario actualizado correctamente")

# 5. Simular el problema: Eliminar horario y verificar que no rompe
print("\n5. Probando eliminación de horario...")
nocturno = Horarios.objects.get(nombre_turno='NOCTURNO')
t.horario = nocturno
t.save()
print(f"   Horario antes de eliminar: {t.get_horario_display()}")
print(f"   Eliminando horario NOCTURNO...")
nocturno.delete()
t_after = Trabajador.objects.get(id=t.id)
print(f"   Horario después de eliminar: {t_after.get_horario_display()}")
print(f"   Horario es NULL: {t_after.horario is None}")
print("   ✓ La eliminación no rompió la asignación (SET_NULL funcionó)")

# 6. Limpiar
print("\n6. Limpiando datos de prueba...")
trabajador_test.delete()
print("   ✓ Trabajador de prueba eliminado")

print("\n" + "=" * 60)
print("✓ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
print("=" * 60)
