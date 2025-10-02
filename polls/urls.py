from django.urls import path
from .views import views

urlpatterns = [
    path('', views.login_view, name='index'),
]