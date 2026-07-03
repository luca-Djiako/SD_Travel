from django.urls import path
from . import views

urlpatterns = [
    path(
        'reserver/<int:vol_id>/',
        views.creer_reservation,
        name='creer_reservation'
    ),
  
    path(
        'confirmation/<str:ref>/',
        views.confirmation,
        name='confirmation'
    ),
    path(
        'mes-reservations/<str:ref>/',
        views.detail_reservation,
        name='detail_reservation'
    ),
     # ── Admin ──
    path('admin-sd/reservations/', views.admin_reservations, name='admin_reservations'),
    path('admin-sd/reservations/<str:ref>/statut/', views.admin_changer_statut, name='admin_changer_statut'),
]