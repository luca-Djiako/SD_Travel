# Django imports
from django.contrib import messages
# from django.contrib.auth.models import AbstractUser,UserManager
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render, redirect
from django.utils import timezone
import json
from django.db.models import Q, Count
from django.db.models.functions import TruncDate, TruncMonth
from datetime import timedelta
from django.shortcuts import get_object_or_404
# Local imports
from .decorators import admin_required 
from .models import Utilisateur
from reservations.models import Paiement, Reservation
from vols.models import Vol


# ─── INSCRIPTION ────────────────────────────────────────────
def register(request):
    if request.method == 'POST':
        prenom    = request.POST.get('prenom')
        nom       = request.POST.get('nom')
        email     = request.POST.get('email')
        telephone = request.POST.get('telephone')
        password  = request.POST.get('password')
        password2 = request.POST.get('password2')

        # Vérifications
        if password != password2:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return redirect('/accounts/login/?tab=register')

        if Utilisateur.objects.filter(email=email).exists():
            messages.error(request, "Cet email est déjà utilisé.")
            return redirect('/accounts/login/?tab=register')

        # Création de l'utilisateur
        user = Utilisateur.objects.create_user(
            username  = email,  # on utilise email comme username
            email     = email,
            password  = password,
            first_name = prenom,
            last_name  = nom,
            telephone  = telephone,
            role       = 'client'
        )

        messages.success(request, "Compte créé avec succès. Connectez-vous.")
        return redirect('dashboard')

    return redirect('/accounts/login/?tab=register')

# ─── CONNEXION ──────────────────────────────────────────────
# ─── CONNEXION ──────────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        # AVANT : if request.user.role == 'admin':
        # APRÈS :
        if request.user.role == 'admin' or request.user.is_superuser:
            return redirect('admin_dashboard')
        return redirect('dashboard')

    if request.method == 'POST':
        email    = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Bienvenue {user.first_name} !")

            # AVANT : if user.role == 'admin':
            # APRÈS :
            if user.role == 'admin' or user.is_superuser:
                return redirect('admin_dashboard')
        else:
            messages.error(request, "Email ou mot de passe incorrect.")
            return redirect('login')

    return render(request, 'accounts/login.html')


# ─── DÉCONNEXION ────────────────────────────────────────────
def logout_view(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté.")
    return redirect('login')


# ─── DASHBOARD CLIENT ───────────────────────────────────────
@login_required(login_url='login')
def dashboard(request):
    # Récupère les réservations du client connecté
    reservations = Reservation.objects.filter(
        client=request.user
    ).select_related('vol', 'vol__compagnie').order_by('-date_reservation')

    # Stats rapides
    total_reservations = reservations.count()
    confirmees         = reservations.filter(statut='confirmee').count()
    en_attente         = reservations.filter(statut='en_attente').count()

    context = {
        'reservations'      : reservations,
        'total_reservations': total_reservations,
        'confirmees'        : confirmees,
        'en_attente'        : en_attente,
    }

    return render(request, 'accounts/dashboard.html', context)


# ─── PROFIL CLIENT ──────────────────────────────────────────
@login_required(login_url='login')
def profil(request):
    if request.method == 'POST':
        user           = request.user
        user.first_name = request.POST.get('prenom')
        user.last_name  = request.POST.get('nom')
        user.telephone  = request.POST.get('telephone')

        if request.FILES.get('photo_profil'):
            user.photo_profil = request.FILES['photo_profil']

        user.save()
        messages.success(request, "Profil mis à jour avec succès.")
        return redirect('profil')

    return render(request, 'accounts/profil.html')


admin_required
def admin_utilisateurs(request):
    utilisateurs = Utilisateur.objects.filter(
        role='client'
    ).order_by('-date_creation')
 
    q = request.GET.get('q', '').strip()
    if q:
        utilisateurs = utilisateurs.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q) |
            Q(telephone__icontains=q)
        )
 
    context = {'utilisateurs': utilisateurs, 'q': q}
    return render(request, 'admin_sd/utilisateurs.html', context)
 
 
# ─── REMPLACE admin_supprimer_utilisateur (exige POST désormais) ──
@admin_required
def admin_supprimer_utilisateur(request, user_id):
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
 
    if request.method != 'POST':
        messages.error(request, "Méthode non autorisée.")
        return redirect('admin_utilisateurs')
 
    if utilisateur.is_superuser or utilisateur.role == 'admin':
        messages.error(request, "Vous ne pouvez pas supprimer un administrateur.")
    else:
        nom = utilisateur.first_name
        utilisateur.delete()
        messages.success(request, f"L'utilisateur {nom} a été supprimé.")
 
    return redirect('admin_utilisateurs')
 
# ─── DASHBOARD ADMIN (remplace la fonction existante du même nom) ──
@admin_required
def admin_dashboard(request):
    periode = request.GET.get('periode', '30j')     # 7j | 30j | 12m | all
    q       = request.GET.get('q', '').strip()
    tri     = request.GET.get('tri', 'recent')       # recent | ancien | montant
 
    maintenant = timezone.now()
    if periode == '7j':
        depuis = maintenant - timedelta(days=7)
    elif periode == '12m':
        depuis = maintenant - timedelta(days=365)
    elif periode == 'all':
        depuis = None
    else:
        periode = '30j'
        depuis = maintenant - timedelta(days=30)
 
    reservations_qs = Reservation.objects.all()
    paiements_qs    = Paiement.objects.filter(statut='reussi')
    clients_qs      = Utilisateur.objects.filter(role='client')
 
    if depuis:
        reservations_qs = reservations_qs.filter(date_reservation__gte=depuis)
        paiements_qs    = paiements_qs.filter(date_paiement__gte=depuis)
        clients_qs      = clients_qs.filter(date_creation__gte=depuis)
 
    # ── KPIs (agrégés en base) ──
    total_reservations = reservations_qs.count()
    revenus_mois        = paiements_qs.aggregate(total=Sum('montant'))['total'] or 0
    vols_actifs          = Vol.objects.filter(statut='actif').count()
    nouveaux_users       = clients_qs.count()
 
    # ── Courbe d'évolution (réservations + revenus) ──
    if periode in ('12m', 'all'):
        evolution = (
            reservations_qs.annotate(groupe=TruncMonth('date_reservation'))
            .values('groupe').annotate(total=Count('id'), revenu=Sum('prix_total'))
            .order_by('groupe')
        )
        fmt = '%b %Y'
    else:
        evolution = (
            reservations_qs.annotate(groupe=TruncDate('date_reservation'))
            .values('groupe').annotate(total=Count('id'), revenu=Sum('prix_total'))
            .order_by('groupe')
        )
        fmt = '%d %b'
 
    chart_labels       = [e['groupe'].strftime(fmt) for e in evolution if e['groupe']]
    chart_reservations = [e['total'] for e in evolution]
    chart_revenus      = [float(e['revenu'] or 0) for e in evolution]
 
    # ── Répartition par statut (donut) ──
    repartition = reservations_qs.values('statut').annotate(total=Count('id'))
    statut_display = dict(Reservation.STATUT_CHOICES)
    statut_labels = [statut_display.get(r['statut'], r['statut']) for r in repartition]
    statut_data   = [r['total'] for r in repartition]
 
    # ── Top 5 destinations ──
    top_destinations = (
        reservations_qs.values('vol__ville_arrivee')
        .annotate(total=Count('id')).order_by('-total')[:5]
    )
 
    # ── Dernières réservations : recherche + tri ──
    dernieres_reservations = reservations_qs.select_related('client', 'vol')
    if q:
        dernieres_reservations = dernieres_reservations.filter(
            Q(client__first_name__icontains=q) |
            Q(client__last_name__icontains=q) |
            Q(reference__icontains=q) |
            Q(vol__numero_vol__icontains=q)
        )
    if tri == 'ancien':
        dernieres_reservations = dernieres_reservations.order_by('date_reservation')
    elif tri == 'montant':
        dernieres_reservations = dernieres_reservations.order_by('-prix_total')
    else:
        tri = 'recent'
        dernieres_reservations = dernieres_reservations.order_by('-date_reservation')
 
    dernieres_reservations = dernieres_reservations[:10]
 
    context = {
        'total_reservations'    : total_reservations,
        'revenus_mois'          : revenus_mois,
        'vols_actifs'           : vols_actifs,
        'nouveaux_users'        : nouveaux_users,
        'dernieres_reservations': dernieres_reservations,
        'periode'               : periode,
        'periodes'              : [('7j', '7 jours'), ('30j', '30 jours'), ('12m', '12 mois'), ('all', 'Tout')],
        'q'                     : q,
        'tri'                   : tri,
        'chart_labels'          : json.dumps(chart_labels),
        'chart_reservations'    : json.dumps(chart_reservations),
        'chart_revenus'         : json.dumps(chart_revenus),
        'statut_labels'         : json.dumps(statut_labels),
        'statut_data'           : json.dumps(statut_data),
        'top_destinations'      : top_destinations,
    }
    return render(request, 'admin_sd/dashboard.html', context)

