from django.urls import path
from .views import views

urlpatterns = [
    path('', views.login_view, name='index'),
    path('inicio/', views.inicio_view, name='inicio'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.registrar_trabajador, name='registro'),
    path('baja/', views.baja_view, name='baja'),
    path('logout/', views.logout_view, name='logout'),
    path('trabajador/agregar/', views.agregar_trabajador, name='agregar_trabajador'),
    path('trabajador/editar/<int:trabajador_id>/', views.editar_trabajador, name='editar_trabajador'),
    path('trabajador/registrar/', views.registrar_trabajador, name='registrar_trabajador'),
    path('trabajador/<int:trabajador_id>/documentos/', views.agregar_documentos, name='agregar_documentos'),
    path('trabajador/<int:trabajador_id>/reactivar/', views.reactivar_trabajador, name='reactivar_trabajador'),
    path('auditoria/', views.historial_auditoria, name='historial_auditoria'),
    # Horarios URLs
    path('horarios/', views.horarios_list, name='horarios_list'),
    path('horarios/agregar/', views.horarios_agregar, name='horarios_agregar'),
    path('horarios/editar/<int:horario_id>/', views.horarios_editar, name='horarios_editar'),
    path('horarios/eliminar/<int:horario_id>/', views.horarios_eliminar, name='horarios_eliminar'),
]
