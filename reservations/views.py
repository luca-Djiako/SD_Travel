# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages
# from django.http import JsonResponse
# from .models import Reservation, Passager, Paiement
# from accounts.decorators import admin_required
# from vols.models import Vol

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
import csv

from .models import Reservation, Passager, Paiement
from accounts.decorators import admin_required
from vols.models import Vol


# ─── ETAPE 1 — FORMULAIRE PASSAGERS ────────────────────────
@login_required(login_url='login')
def creer_reservation(request, vol_id):
    vol = get_object_or_404(Vol, id=vol_id, statut='actif')
    classe = request.GET.get('classe', 'economique')

    # Prix selon la classe choisie
    prix_map = {
        'economique': vol.prix_economique,
        'affaires'  : vol.prix_affaires,
        'premiere'  : vol.prix_premiere,
    }
    prix_unitaire = prix_map.get(classe, vol.prix_economique) or vol.prix_economique

    if request.method == 'POST':
        nombre_passagers = int(request.POST.get('nombre_passagers', 1))
        methode_paiement = request.POST.get('methode_paiement', 'carte')
        prix_total = prix_unitaire * nombre_passagers

        # ── Créer la réservation ──
        reservation = Reservation.objects.create(
            client           = request.user,
            vol              = vol,
            classe           = classe,
            nombre_passagers = nombre_passagers,
            prix_total       = prix_total,
            statut           = 'confirmee'
        )

        # ── Créer les passagers ──
        for i in range(nombre_passagers):
            Passager.objects.create(
                reservation          = reservation,
                nom                  = request.POST.get(f'nom_{i}', ''),
                prenom               = request.POST.get(f'prenom_{i}', ''),
                date_naissance       = request.POST.get(f'date_naissance_{i}') or None,
                nationalite          = request.POST.get(f'nationalite_{i}', ''),
                numero_passeport     = request.POST.get(f'passeport_{i}', ''),
                expiration_passeport = request.POST.get(f'expiration_{i}') or None,
                email                = request.POST.get(f'email_{i}', ''),
                telephone            = request.POST.get(f'telephone_{i}', ''),
            )

        # ── Enregistrer le paiement (mock — Stripe/MoMo plus tard) ──
        Paiement.objects.create(
            reservation    = reservation,
            methode        = methode_paiement,
            montant        = prix_total,
            devise         = 'XAF',
            statut         = 'reussi',
            transaction_id = f"MOCK-{reservation.reference}"
        )

        messages.success(request, f"Réservation {reservation.reference} confirmée !")
        return redirect('confirmation', ref=reservation.reference)

    # ── GET : afficher le formulaire ──
    context = {
        'vol'          : vol,
        'classe'       : classe,
        'prix_unitaire': prix_unitaire,
    }
    return render(request, 'reservations/formulaire.html', context)

# ─── ETAPE 2 — PAIEMENT ─────────────────────────────────────
# @login_required(login_url='login')
# def paiement(request):
#     reservation_id = request.session.get('reservation_id')

#     if not reservation_id:
#         messages.error(request, "Aucune réservation en cours.")
#         return redirect('liste_vols')

#     reservation = get_object_or_404(
#         Reservation,
#         id=reservation_id,
#         client=request.user
#     )

#     if request.method == 'POST':
#         methode = request.POST.get('methode_paiement')

#         # Créer l'entrée paiement
#         paiement = Paiement.objects.create(
#             reservation    = reservation,
#             methode        = methode,
#             montant        = reservation.prix_total,
#             devise         = 'FCFA',
#             statut         = 'en_attente'
#         )

#         # Ici on intégrera Stripe ou CinetPay plus tard
#         # Pour l'instant on simule un paiement réussi
#         paiement.statut = 'reussi'
#         paiement.transaction_id = f"MOCK-{reservation.reference}"
#         paiement.save()

#         # Mettre à jour le statut de la réservation
#         reservation.statut = 'confirmee'
#         reservation.save()

#         # Nettoyer la session
#         del request.session['reservation_id']

#         return redirect('confirmation', ref=reservation.reference)

#     context = {'reservation': reservation}
#     return render(request, 'reservations/paiement.html', context)


# ─── ETAPE 3 — CONFIRMATION ─────────────────────────────────
@login_required(login_url='login')
def confirmation(request, ref):
    reservation = get_object_or_404(
        Reservation,
        reference=ref,
        client=request.user
    )

    context = {'reservation': reservation}
    return render(request, 'reservations/confirmation.html', context)


# ─── DETAIL RESERVATION CLIENT ──────────────────────────────
@login_required(login_url='login')
def detail_reservation(request, ref):
    reservation = get_object_or_404(
        Reservation,
        reference=ref,
        client=request.user
    )

    context = {'reservation': reservation}
    return render(request, 'reservations/detail.html', context)

 
# ─── GESTION DES RESERVATIONS ───────────────────────────────
@admin_required
def admin_reservations(request):
    reservations = Reservation.objects.select_related(
        'client', 'vol', 'vol__compagnie'
    ).prefetch_related('passagers', 'paiement').order_by('-date_reservation')
 
    # ── Filtre par statut ──
    statut = request.GET.get('statut', 'all')
    if statut and statut != 'all':
        reservations = reservations.filter(statut=statut)
 
    # ── Recherche (client, référence, n° de vol) ──
    q = request.GET.get('q', '').strip()
    if q:
        reservations = reservations.filter(
            Q(client__first_name__icontains=q) |
            Q(client__last_name__icontains=q) |
            Q(client__email__icontains=q) |
            Q(reference__icontains=q) |
            Q(vol__numero_vol__icontains=q)
        )
 
    # ── Export CSV (respecte les filtres actifs, avant pagination) ──
    if request.GET.get('export') == 'csv':
        return export_reservations_csv(reservations)
 
    # ── Revenus du mois en cours (réservations réellement payées) ──
    maintenant = timezone.now()
    revenus_mensuels = Reservation.objects.filter(
        statut__in=['confirmee', 'billet_emis'],
        date_reservation__year=maintenant.year,
        date_reservation__month=maintenant.month
    ).aggregate(total=Sum('prix_total'))['total'] or 0
 
    # ── Pagination (10 par page) ──
    paginator = Paginator(reservations, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))
 
    context = {
        'reservations'    : page_obj,
        'page_obj'        : page_obj,
        'statut_filtre'   : statut,
        'q'               : q,
        'revenus_mensuels': revenus_mensuels,
        'total'           : paginator.count,
    }
    return render(request, 'admin_sd/reservations.html', context)
 
 
def export_reservations_csv(reservations):
    """Génère un CSV des réservations, en respectant les filtres actifs."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reservations_sdtravel.csv"'
    response.write('\ufeff')  # BOM — pour que Excel affiche correctement les accents
 
    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'Référence', 'Client', 'Email', 'N° Vol', 'Itinéraire',
        'Classe', 'Passagers', 'Date réservation', 'Montant (FCFA)', 'Statut'
    ])
 
    for r in reservations:
        writer.writerow([
            r.reference,
            r.client.get_full_name(),
            r.client.email,
            r.vol.numero_vol,
            f"{r.vol.ville_depart} → {r.vol.ville_arrivee}",
            r.get_classe_display(),
            r.nombre_passagers,
            r.date_reservation.strftime('%d/%m/%Y %H:%M'),
            r.prix_total,
            r.get_statut_display(),
        ])
 
    return response
 
 
# ─── CHANGER STATUT RESERVATION ─────────────────────────────
@admin_required
def admin_changer_statut(request, ref):
    reservation = get_object_or_404(Reservation, reference=ref)
 
    if request.method == 'POST':
        nouveau_statut = request.POST.get('statut')
        if nouveau_statut in dict(Reservation.STATUT_CHOICES):
            reservation.statut = nouveau_statut
            if request.POST.get('notes'):
                reservation.notes_admin = request.POST.get('notes')
            reservation.save()
            messages.success(request, f"Statut mis à jour : {reservation.get_statut_display()}")
        else:
            messages.error(request, "Statut invalide.")
 
    return redirect('admin_reservations')