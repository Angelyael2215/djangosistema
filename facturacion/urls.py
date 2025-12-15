from django.urls import path
from . import views

app_name = 'facturacion'

urlpatterns = [
    path('clientes/', views.cliente_list, name='cliente_list'),
    path('clientes/crear/', views.cliente_create, name='cliente_create'),
    path('clientes/<int:pk>/editar/', views.cliente_edit, name='cliente_edit'),
    path('', views.factura_list, name='factura_list'),
    path('crear/', views.factura_create, name='factura_create'),
    path('<int:factura_id>/', views.factura_detail, name='factura_detail'),
    path('<int:factura_id>/pdf/', views.factura_pdf, name='factura_pdf'),
    path('reportes/mes/', views.reportes_mes, name='reportes_mes'),
    path('reportes/export_csv/', views.export_facturas_csv, name='export_facturas_csv'),
    path('reportes/export_xls/', views.export_facturas_xls, name='export_facturas_xls'),
]
