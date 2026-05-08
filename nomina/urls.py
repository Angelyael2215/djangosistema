from django.urls import path
from . import views

app_name = 'nomina'

urlpatterns = [
    path('periodos/', views.periodo_list, name='periodo_list'),
    path('periodos/crear/', views.periodo_create, name='periodo_create'),
    path('periodos/<int:pk>/', views.periodo_detail, name='periodo_detail'),
    path('recibos/<int:pk>/', views.recibo_detail, name='recibo_detail'),
    path('periodos/<int:periodo_id>/trabajador/<int:trabajador_id>/crear/', views.crear_recibo, name='crear_recibo'),
    path('salarios/', views.salario_list, name='salario_list'),
    path('salarios/crear/', views.salario_create, name='salario_create'),
    path('salarios/crear/<int:trabajador_id>/', views.salario_create, name='salario_create_trabajador'),
    path('salarios/editar/<int:pk>/', views.salario_edit, name='salario_edit'),
    path('recibos/<int:pk>/pdf/', views.descargar_recibo_pdf, name='recibo_pdf'),
]