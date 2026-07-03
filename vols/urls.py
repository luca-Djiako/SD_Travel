from django.urls import path
from . import views

urlpatterns = [
    # ── Client ──
    path('', views.home, name='home'),
    path('vols/', views.liste_vols, name='liste_vols'),
    path('vols/<int:vol_id>/', views.detail_vol, name='detail_vol'),
    path('tarifs/', views.tarifs, name='tarifs'),
    path('contact/', views.contact, name='contact'),

    # ── Admin ──
    path('admin-sd/vols/', views.admin_vols, name='admin_vols'),
    # path('admin-sd/vols/', views.admin_vols, name='admin_creer_compagnie'),
    path('admin-sd/compagnies/creer/', views.admin_creer_compagnie, name='admin_creer_compagnie'),
    path('admin-sd/vols/<int:vol_id>/modifier/', views.admin_modifier_vol, name='admin_modifier_vol'),
    path('admin-sd/vols/<int:vol_id>/supprimer/', views.admin_supprimer_vol, name='admin_supprimer_vol'),
    path('admin-sd/vols/<int:vol_id>/statut/', views.admin_statut_vol, name='admin_statut_vol'),
]