from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('mon-compte/', views.dashboard, name='dashboard'),
    path('mon-compte/profil/', views.profil, name='profil'),
    
    path('admin-sd/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-sd/utilisateurs/', views.admin_utilisateurs, name='admin_utilisateurs'),
    path('admin-sd/utilisateur/supprimer/<int:user_id>/', views.admin_supprimer_utilisateur, name='admin_supprimer_utilisateur'),

]