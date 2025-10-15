from django.urls import path
from .views import views

urlpatterns = [
    path('', views.login_view, name='index'),           # http://127.0.0.1:8000/
    path('inicio/', views.inicio_view, name='inicio'),  # http://127.0.0.1:8000/inicio/
    path('login/', views.login_view, name='login'),     # http://127.0.0.1:8000/login/
    path('registro/', views.register_view, name='registro'),  # http://127.0.0.1:8000/registro/
    path('baja/', views.baja_view, name='baja'),  # http://127.0.0.1:8000/baja/
]