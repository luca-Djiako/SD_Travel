# accounts/decorators.py
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def admin_required(view_func):
    """
    Décorateur qui vérifie les droits admin.
    Si non autorisé, on redirige vers 'home' pour ne pas exposer le dashboard client.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # 1. Vérification : est-ce un admin ?
        if request.user.is_authenticated and request.user.is_admin_site:
            return view_func(request, *args, **kwargs)
        
        # 2. Si ce n'est pas un admin, on refuse l'accès
        messages.error(request, "Accès non autorisé : zone réservée aux administrateurs.")
        
        # Redirection vers la page d'accueil (ou une vue spécifique)
        return redirect('home') 
    return wrapper