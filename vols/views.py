from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Sum
from django.contrib import messages
from django.http import JsonResponse
from accounts.decorators import admin_required
from .models import Vol, CompagnieAerienne


# ─── PAGE ACCUEIL ───────────────────────────────────────────
def home(request):
    vols_populaires = Vol.objects.filter(
        est_populaire=True,
        statut='actif'
    ).select_related('compagnie')[:6]

    context = {'vols_populaires': vols_populaires}
    return render(request, 'vols/home.html', context)


# ─── LISTE ET RECHERCHE DES VOLS ────────────────────────────
def liste_vols(request):
    vols = Vol.objects.filter(
        statut='actif'
    ).select_related('compagnie').order_by('date_depart')

    depart   = request.GET.get('depart', '').strip()
    arrivee  = request.GET.get('arrivee', '').strip()
    date_dep = request.GET.get('date_depart', '')
    classe   = request.GET.get('classe', '')

    if depart:
        vols = vols.filter(
            Q(ville_depart__icontains=depart) |
            Q(code_depart__icontains=depart)
        )
    if arrivee:
        vols = vols.filter(
            Q(ville_arrivee__icontains=arrivee) |
            Q(code_arrivee__icontains=arrivee)
        )
    if date_dep:
        vols = vols.filter(date_depart__date=date_dep)

    prix_min  = request.GET.get('prix_min')
    prix_max  = request.GET.get('prix_max')
    compagnie = request.GET.get('compagnie')
    escales   = request.GET.get('escales')

    if prix_min:
        vols = vols.filter(prix_economique__gte=prix_min)
    if prix_max:
        vols = vols.filter(prix_economique__lte=prix_max)
    if compagnie:
        vols = vols.filter(compagnie__id=compagnie)
    if escales is not None and escales != '':
        vols = vols.filter(nombre_escales=escales)

    tri = request.GET.get('tri', 'prix')
    if tri == 'prix':
        vols = vols.order_by('prix_economique')
    elif tri == 'duree':
        vols = vols.order_by('date_depart')

    compagnies = CompagnieAerienne.objects.all()

    context = {
        'vols'      : vols,
        'compagnies': compagnies,
        'depart'    : depart,
        'arrivee'   : arrivee,
        'date_dep'  : date_dep,
        'classe'    : classe,
        'tri'       : tri,
    }
    return render(request, 'vols/liste_vols.html', context)


# ─── DETAIL D'UN VOL ────────────────────────────────────────
def detail_vol(request, vol_id):
    vol = get_object_or_404(Vol, id=vol_id, statut='actif')
    vols_similaires = Vol.objects.filter(
        ville_arrivee=vol.ville_arrivee,
        statut='actif'
    ).exclude(id=vol.id)[:3]

    context = {'vol': vol, 'vols_similaires': vols_similaires}
    return render(request, 'vols/detail_vol.html', context)


# ─── PAGE TARIFS ────────────────────────────────────────────
def tarifs(request):
    vols = Vol.objects.filter(
        statut='actif'
    ).select_related('compagnie').order_by('prix_economique')
    return render(request, 'vols/tarifs.html', {'vols': vols})


# ─── CONTACT ────────────────────────────────────────────────
def contact(request):
    if request.method == 'POST':
        messages.success(request, "Message envoyé avec succès !")
        return redirect('contact')
    return render(request, 'vols/contact.html')


# ─── ADMIN : LISTE + AJOUT DES VOLS ────────────────────────
@admin_required
def admin_vols(request):
    if request.method == 'POST':
        try:
            # ── Gestion compagnie ──
            compagnie_id = request.POST.get('compagnie')

            if compagnie_id == 'nouvelle':
                nom_compagnie  = request.POST.get('nouvelle_compagnie_nom', '').strip()
                code_compagnie = request.POST.get('nouvelle_compagnie_code', '').strip().upper()

                if not nom_compagnie or not code_compagnie:
                    messages.error(request, "Nom et code IATA de la compagnie requis.")
                    return redirect('admin_vols')

                compagnie, created = CompagnieAerienne.objects.get_or_create(
                    code_iata=code_compagnie,
                    defaults={'nom': nom_compagnie}
                )
                compagnie_id = compagnie.id

            Vol.objects.create(
                numero_vol        = request.POST.get('numero_vol', '').strip(),
                compagnie_id      = compagnie_id,
                ville_depart      = request.POST.get('ville_depart', '').strip(),
                code_depart       = request.POST.get('code_depart', '').strip().upper(),
                ville_arrivee     = request.POST.get('ville_arrivee', '').strip(),
                code_arrivee      = request.POST.get('code_arrivee', '').strip().upper(),
                date_depart       = request.POST.get('date_depart'),
                date_arrivee      = request.POST.get('date_arrivee'),
                nombre_escales    = request.POST.get('nombre_escales', 0),
                prix_economique   = request.POST.get('prix_economique'),
                prix_affaires     = request.POST.get('prix_affaires') or None,
                prix_premiere     = request.POST.get('prix_premiere') or None,
                places_economique = request.POST.get('places_economique', 0),
                places_affaires   = request.POST.get('places_affaires') or 0,
                places_premiere   = request.POST.get('places_premiere') or 0,
                statut            = request.POST.get('statut', 'actif'),
                est_populaire     = request.POST.get('est_populaire') == 'on',
            )
            messages.success(request, "Vol ajouté avec succès.")
        except Exception as e:
            messages.error(request, f"Erreur lors de l'ajout : {e}")
        return redirect('admin_vols')

    # ... reste inchangé

    vols       = Vol.objects.select_related('compagnie').order_by('-date_creation')
    compagnies = CompagnieAerienne.objects.all()

    # Stats réelles pour le header
    stats = {
        'vols_actifs'   : Vol.objects.filter(statut='actif').count(),
        'vols_complets' : Vol.objects.filter(statut='complet').count(),
        'vols_annules'  : Vol.objects.filter(statut='annule').count(),
        'total_places'  : Vol.objects.filter(statut='actif').aggregate(
                            t=Sum('places_economique'))['t'] or 0,
    }

    context = {
        'vols'      : vols,
        'compagnies': compagnies,
        'stats'     : stats,
        'total_vols': vols.count(),
    }
    return render(request, 'admin_sd/vols.html', context)


# ─── ADMIN : MODIFIER UN VOL ────────────────────────────────
@admin_required
def admin_modifier_vol(request, vol_id):
    vol = get_object_or_404(Vol, id=vol_id)
    if request.method == 'POST':
        try:
            vol.numero_vol        = request.POST.get('numero_vol', '').strip()
            vol.compagnie_id      = request.POST.get('compagnie')
            vol.ville_depart      = request.POST.get('ville_depart', '').strip()
            vol.code_depart       = request.POST.get('code_depart', '').strip().upper()
            vol.ville_arrivee     = request.POST.get('ville_arrivee', '').strip()
            vol.code_arrivee      = request.POST.get('code_arrivee', '').strip().upper()
            vol.date_depart       = request.POST.get('date_depart')
            vol.date_arrivee      = request.POST.get('date_arrivee')
            vol.nombre_escales    = request.POST.get('nombre_escales', 0)
            vol.prix_economique   = request.POST.get('prix_economique')
            vol.prix_affaires     = request.POST.get('prix_affaires') or None
            vol.prix_premiere     = request.POST.get('prix_premiere') or None
            vol.places_economique = request.POST.get('places_economique', 0)
            vol.places_affaires   = request.POST.get('places_affaires') or 0
            vol.places_premiere   = request.POST.get('places_premiere') or 0
            vol.statut            = request.POST.get('statut', 'actif')
            vol.est_populaire     = request.POST.get('est_populaire') == 'on'
            vol.save()
            messages.success(request, "Vol modifié avec succès.")
        except Exception as e:
            messages.error(request, f"Erreur : {e}")
    return redirect('admin_vols')

# ─── ADMIN : SUPPRIMER UN VOL ───────────────────────────────
@admin_required
def admin_supprimer_vol(request, vol_id):
    vol = get_object_or_404(Vol, id=vol_id)
    vol.delete()
    messages.success(request, "Vol supprimé.")
    return redirect('admin_vols')


# ─── ADMIN : CHANGER STATUT D'UN VOL ───────────────────────
@admin_required
def admin_statut_vol(request, vol_id):
    vol = get_object_or_404(Vol, id=vol_id)
    nouveau_statut = request.POST.get('statut')
    if nouveau_statut in dict(Vol.STATUT_CHOICES):
        vol.statut = nouveau_statut
        vol.save()
        messages.success(request, f"Statut mis à jour : {vol.get_statut_display()}")
    return redirect('admin_vols')

@admin_required
def admin_creer_compagnie(request):
    if request.method == 'POST':
        nom  = request.POST.get('nom', '').strip()
        code = request.POST.get('code_iata', '').strip().upper()

        if not nom or not code:
            return JsonResponse({'error': 'Nom et code IATA requis.'}, status=400)

        if len(code) > 3:
            return JsonResponse({'error': 'Le code IATA ne doit pas dépasser 3 caractères.'}, status=400)

        if CompagnieAerienne.objects.filter(code_iata=code).exists():
            return JsonResponse({'error': f'Code IATA {code} déjà utilisé.'}, status=400)

        compagnie = CompagnieAerienne.objects.create(nom=nom, code_iata=code)
        return JsonResponse({'id': compagnie.id, 'nom': compagnie.nom, 'code_iata': compagnie.code_iata})

    return JsonResponse({'error': 'Méthode non autorisée.'}, status=405)