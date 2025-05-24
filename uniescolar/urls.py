from django.urls import path
from django.contrib import admin
from uniescolar.views import home, register_user, logout_user, add_aula, aula_detail_view
from . import views

urlpatterns=[    
    path('', views.home, name='home'),
    path('register/', views.register_user, name='register'),
    path('logout/', views.logout_user, name='logout'),
    path('add_aula/', views.add_aula, name='add_aula'),
    path('aula/<int:id>/detalhes/', views.aula_detail_view, name='detalhe_aula'),    
    path('aula/<int:aula_id>/editar/', views.update_aula_view, name='update_aula'),
    path('aula/<int:aula_id>/excluir/', views.excluir_aula, name='delete_aula'),
    path('aula/<int:aula_id>/aprovar/', views.aprovar_aula_view, name='aprovar_aula'), 
    path('aula/<int:aula_id>/rejeitar/', views.rejeitar_aula_view, name='rejeitar_aula'), 
]