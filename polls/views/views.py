from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from ..models import Trabajador, Servicio, Documentos, Horarios
from ..models import CustomUser
from django.core.exceptions import PermissionDenied

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
    context = {
        'trabajadores': trabajadores,
        'can_edit': is_hr_or_admin(request.user)
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
    if request.method == 'POST':
        trabajador_id = request.POST.get('trabajador_id')
        try:
            trabajador = Trabajador.objects.get(id=trabajador_id)
            trabajador.estado = 'Inactivo'
            trabajador.save()
            messages.success(request, f'El trabajador {trabajador.nombre} ha sido dado de baja.')
        except Trabajador.DoesNotExist:
            messages.error(request, 'Trabajador no encontrado.')
            
    trabajadores = Trabajador.objects.filter(estado='Activo')
    return render(request, 'polls/BajaElementos.html', {'trabajadores': trabajadores})

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