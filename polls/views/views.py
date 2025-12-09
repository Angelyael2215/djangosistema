from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from ..models import Trabajador, Servicio, Documentos, Horarios, Auditoria
from ..models import CustomUser
from ..forms import TrabajadorRegistroForm, DocumentosForm
from django.core.exceptions import PermissionDenied
from django.conf import settings
import os
from datetime import datetime
from django.db.models import Q

def is_admin(user):
    return user.role == 'ADMIN'

def is_hr_or_admin(user):
    return user.role in ['HR', 'ADMIN']

def login_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        # ModelBackend expects the credential named according to USERNAME_FIELD.
        # The login form uses 'username' (which we keep as the POST name),
        # and our CustomUser sets USERNAME_FIELD='email', so pass it as
        # the username argument to authenticate.
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f'Bienvenido, {user.get_username()}')
                return redirect('inicio')
            else:
                messages.error(request, 'Cuenta inactiva.')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'polls/login.html')

@login_required
def inicio_view(request):
    trabajadores = Trabajador.objects.all()

    # Filters
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '').strip()
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()

    if q:
        trabajadores = trabajadores.filter(
            Q(nombre__icontains=q) | Q(apellido__icontains=q) | Q(apellido_materno__icontains=q) | Q(curp_text__icontains=q)
        )
    if estado:
        trabajadores = trabajadores.filter(estado__iexact=estado)
    if from_date:
        try:
            d1 = datetime.strptime(from_date, '%Y-%m-%d').date()
            trabajadores = trabajadores.filter(fecha_ingreso__date__gte=d1)
        except ValueError:
            pass
    if to_date:
        try:
            d2 = datetime.strptime(to_date, '%Y-%m-%d').date()
            trabajadores = trabajadores.filter(fecha_ingreso__date__lte=d2)
        except ValueError:
            pass

    context = {
        'trabajadores': trabajadores,
        'can_edit': is_hr_or_admin(request.user),
        'filters': {
            'q': q,
            'estado': estado,
            'from_date': from_date,
            'to_date': to_date,
        }
    }
    return render(request, 'polls/inicio.html', context)

@user_passes_test(is_admin)
def register_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'El correo ya está registrado.')
            return render(request, 'polls/registro.html')
        
        user = CustomUser.objects.create_user(
            email=email,
            password=password,
            role=role
        )
        messages.success(request, 'Usuario registrado exitosamente.')
        return redirect('inicio')
        
    return render(request, 'polls/registro.html')

@user_passes_test(is_hr_or_admin)
def baja_view(request):
    """Vista para dar de baja a trabajadores"""
    if request.method == 'POST':
        trabajador_id = request.POST.get('trabajador_id')
        motivo = request.POST.get('motivo', '')
        
        try:
            trabajador = Trabajador.objects.get(id=trabajador_id)
            estado_anterior = trabajador.estado
            
            # Cambiar estado a Inactivo
            trabajador.estado = 'Inactivo'
            trabajador.save()
            
            # Registrar auditoría
            Auditoria.objects.create(
                trabajador=trabajador,
                usuario=request.user,
                accion='BAJA',
                estado_anterior=estado_anterior,
                estado_nuevo='Inactivo',
                motivo=motivo
            )
            
            messages.success(request, f'El trabajador {trabajador.nombre} {trabajador.apellido} ha sido dado de baja exitosamente.')
            return redirect('baja')
        except Trabajador.DoesNotExist:
            messages.error(request, 'Trabajador no encontrado.')
            
    # GET -> mostrar formulario de baja
    trabajadores = Trabajador.objects.filter(estado='Activo')
    context = {
        'trabajadores': trabajadores
    }
    return render(request, 'polls/BajaElementos.html', context)

@user_passes_test(is_hr_or_admin)
def reactivar_trabajador(request, trabajador_id):
    """Vista para reactivar un trabajador"""
    try:
        trabajador = Trabajador.objects.get(id=trabajador_id)
        estado_anterior = trabajador.estado
        
        trabajador.estado = 'Activo'
        trabajador.save()
        
        # Registrar auditoría
        Auditoria.objects.create(
            trabajador=trabajador,
            usuario=request.user,
            accion='REACTIVACION',
            estado_anterior=estado_anterior,
            estado_nuevo='Activo',
            motivo='Reactivación de trabajador'
        )
        
        messages.success(request, f'El trabajador {trabajador.nombre} ha sido reactivado exitosamente.')
    except Trabajador.DoesNotExist:
        messages.error(request, 'Trabajador no encontrado.')
    
    return redirect('baja')

@user_passes_test(is_admin)
def historial_auditoria(request):
    """Vista para ver el historial de auditoría"""
    auditorias = Auditoria.objects.all()
    
    # Filtros opcionales
    trabajador_id = request.GET.get('trabajador_id')
    accion = request.GET.get('accion')
    fecha_desde = request.GET.get('from_date')
    fecha_hasta = request.GET.get('to_date')
    
    if trabajador_id:
        auditorias = auditorias.filter(trabajador_id=trabajador_id)
    if accion:
        auditorias = auditorias.filter(accion=accion)
    # Filtrar por fecha (si se proporcionan)
    # Esperamos formato ISO date: YYYY-MM-DD
    if fecha_desde:
        try:
            d = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            auditorias = auditorias.filter(fecha_cambio__date__gte=d)
        except ValueError:
            pass
    if fecha_hasta:
        try:
            d2 = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            auditorias = auditorias.filter(fecha_cambio__date__lte=d2)
        except ValueError:
            pass
    
    trabajadores = Trabajador.objects.all()
    acciones = Auditoria.objects.values_list('accion', flat=True).distinct()
    
    context = {
        'auditorias': auditorias,
        'trabajadores': trabajadores,
        'acciones': acciones
    }
    return render(request, 'polls/historial_auditoria.html', context)

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión.')
    return redirect('login')

# Vistas adicionales para gestión de trabajadores
@user_passes_test(is_hr_or_admin)
def agregar_trabajador(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        
        trabajador = Trabajador.objects.create(
            nombre=nombre,
            apellido=apellido
        )
        messages.success(request, f'Trabajador {trabajador.nombre} agregado exitosamente.')
        return redirect('inicio')
    
    return render(request, 'polls/agregar_trabajador.html')

@user_passes_test(is_hr_or_admin)
def editar_trabajador(request, trabajador_id):
    try:
        trabajador = Trabajador.objects.get(id=trabajador_id)
    except Trabajador.DoesNotExist:
        messages.error(request, 'Trabajador no encontrado.')
        return redirect('inicio')
    
    if request.method == 'POST':
        trabajador.nombre = request.POST.get('nombre', trabajador.nombre)
        trabajador.apellido = request.POST.get('apellido', trabajador.apellido)
        trabajador.save()
        messages.success(request, f'Trabajador {trabajador.nombre} actualizado exitosamente.')
        return redirect('inicio')
    
    return render(request, 'polls/editar_trabajador.html', {'trabajador': trabajador})

@user_passes_test(is_hr_or_admin)
def registrar_trabajador(request):
    """Vista para registrar un nuevo trabajador con documentos"""
    if request.method == 'POST':
        # Crear trabajador a partir de los campos principales (y campos adicionales)
        nombre = request.POST.get('nombre')
        apellido_paterno = request.POST.get('apellido_paterno')
        apellido_materno = request.POST.get('apellido_materno')
        estado = request.POST.get('estado', 'Activo')
        rfc = request.POST.get('rfc')
        no_exterior = request.POST.get('no_exterior')
        curp_text = request.POST.get('curp_text')
        codigo_postal = request.POST.get('codigo_postal')
        cuip_text = request.POST.get('cuip_text')
        entidad_federativa = request.POST.get('entidad_federativa')
        nss_text = request.POST.get('nss_text')
        calle = request.POST.get('calle')
        horario = request.POST.get('horario')
        calle_servicio = request.POST.get('calle_servicio')
        no_exterior_servicio = request.POST.get('no_exterior_servicio')
        entidad_servicio = request.POST.get('entidad_servicio')
        estado_servicio = request.POST.get('estado_servicio')

        if not nombre:
            messages.error(request, 'El nombre es obligatorio.')
            return render(request, 'polls/registro.html')

        trabajador = Trabajador.objects.create(
            nombre=nombre,
            apellido=apellido_paterno,
            apellido_materno=apellido_materno,
            estado=estado,
            rfc=rfc,
            no_exterior=no_exterior,
            curp_text=curp_text,
            codigo_postal=codigo_postal,
            cuip_text=cuip_text,
            entidad_federativa=entidad_federativa,
            nss_text=nss_text,
            calle=calle,
            horario=horario,
            calle_servicio=calle_servicio,
            no_exterior_servicio=no_exterior_servicio,
            entidad_servicio=entidad_servicio,
            estado_servicio=estado_servicio,
        )

        # Asegurar que la carpeta exista antes de guardar archivos
        carpeta = os.path.join(settings.MEDIA_ROOT, 'documentos', str(trabajador.id))
        os.makedirs(carpeta, exist_ok=True)

        # Crear registro de Documentos y asignar archivos si existen
        documentos = Documentos(trabajador=trabajador)
        file_fields = ['cuip', 'antecedentes', 'situacion_fiscal', 'curp', 'nss', 'cursos', 'certificado_estudios']
        for f in file_fields:
            uploaded = request.FILES.get(f)
            if uploaded:
                setattr(documentos, f, uploaded)

        documentos.save()

        messages.success(request, f'Trabajador {trabajador.nombre} registrado y archivos guardados.')
        return redirect('inicio')

    # GET -> mostrar plantilla con diseño existente
    return render(request, 'polls/registro.html')

@user_passes_test(is_hr_or_admin)
def agregar_documentos(request, trabajador_id):
    """Vista para agregar documentos a un trabajador"""
    try:
        trabajador = Trabajador.objects.get(id=trabajador_id)
    except Trabajador.DoesNotExist:
        messages.error(request, 'Trabajador no encontrado.')
        return redirect('inicio')
    
    # Obtener o crear registro de documentos
    documentos, created = Documentos.objects.get_or_create(trabajador=trabajador)
    
    if request.method == 'POST':
        form = DocumentosForm(request.POST, request.FILES, instance=documentos)
        if form.is_valid():
            form.save()
            messages.success(request, f'Documentos del trabajador {trabajador.nombre} guardados exitosamente.')
            return redirect('inicio')
        else:
            messages.error(request, 'Error al guardar los documentos.')
    else:
        form = DocumentosForm(instance=documentos)
    
    context = {
        'form': form,
        'trabajador': trabajador,
        'documentos': documentos
    }
    return render(request, 'polls/agregar_documentos.html', context)