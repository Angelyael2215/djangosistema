from django.shortcuts import render

def login_view(request):
    return render(request, 'polls/login.html')

def inicio_view(request):
    return render(request, 'polls/inicio.html')
def register_view(request):
    return render(request, 'polls/registro.html')