from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),  # admin Django natif

    # Nos apps
    # path('vols/', include('vols.urls')),
    # APRÈS
    path('', include('vols.urls')),
    path('accounts/', include('accounts.urls')),
    path('reservations/', include('reservations.urls')),
    # path('dashboard/', include('admin_panel.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)