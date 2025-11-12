from django.urls import path
from .views import views

urlpatterns = [
    path('', views.login_view, name='index'),
    path('inicio/', views.inicio_view, name='inicio'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.register_view, name='registro'),
    path('baja/', views.baja_view, name='baja'),
    path('logout/', views.logout_view, name='logout'),
    path('trabajador/agregar/', views.agregar_trabajador, name='agregar_trabajador'),
    path('trabajador/editar/<int:trabajador_id>/', views.editar_trabajador, name='editar_trabajador'),
]