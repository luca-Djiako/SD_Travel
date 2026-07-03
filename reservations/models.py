from django.db import models
from accounts.models import Utilisateur
from vols.models import Vol

class Reservation(models.Model):
    """
    Une réservation créée par un client.
    Liée à un vol et un utilisateur.
    """
    
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('confirmee', 'Confirmée'),
        ('billet_emis', 'Billet émis'),
        ('annulee', 'Annulée'),
    ]
    
    CLASSE_CHOICES = [
        ('economique', 'Économique'),
        ('affaires', 'Affaires'),
        ('premiere', 'Première Classe'),
    ]
    
    # Relations
    client = models.ForeignKey(
        Utilisateur, 
        on_delete=models.PROTECT,
        related_name='reservations'
    )
    vol = models.ForeignKey(
        Vol, 
        on_delete=models.PROTECT,
        related_name='reservations'
    )
    
    # Détails réservation
    reference = models.CharField(max_length=10, unique=True)  # ex: SDT-00123
    classe = models.CharField(
        max_length=12, 
        choices=CLASSE_CHOICES, 
        default='economique'
    )
    nombre_passagers = models.IntegerField(default=1)
    prix_total = models.DecimalField(max_digits=10, decimal_places=2)
    
    statut = models.CharField(
        max_length=15, 
        choices=STATUT_CHOICES, 
        default='en_attente'
    )
    
    # Notes admin
    notes_admin = models.TextField(blank=True)
    
    date_reservation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Réservation'
        ordering = ['-date_reservation']
    
    def __str__(self):
        return f"{self.reference} — {self.client} → {self.vol}"
    
    def save(self, *args, **kwargs):
        """Génère automatiquement la référence si elle n'existe pas"""
        if not self.reference:
            import random, string
            code = ''.join(random.choices(string.digits, k=5))
            self.reference = f"SDT-{code}"
        super().save(*args, **kwargs)


class Passager(models.Model):
    """
    Informations de chaque passager sur une réservation.
    Si 3 passagers → 3 entrées Passager liées à 1 Reservation.
    """
    
    GENRE_CHOICES = [
        ('M', 'Monsieur'),
        ('F', 'Madame'),
    ]
    
    reservation = models.ForeignKey(
        Reservation, 
        on_delete=models.CASCADE,
        related_name='passagers'
    )
    
    genre = models.CharField(max_length=1, choices=GENRE_CHOICES)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    nationalite = models.CharField(max_length=50)
    numero_passeport = models.CharField(max_length=20)
    expiration_passeport = models.DateField()
    email = models.EmailField()
    telephone = models.CharField(max_length=20)
    
    class Meta:
        verbose_name = 'Passager'
    
    def __str__(self):
        return f"{self.genre}. {self.prenom} {self.nom}"


class Paiement(models.Model):
    """
    Enregistre le paiement associé à une réservation.
    """
    
    METHODE_CHOICES = [
        ('carte', 'Carte bancaire'),
        ('orange_money', 'Orange Money'),
        ('wave', 'Wave'),
        ('mtn_momo', 'MTN MoMo'),
    ]
    
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('reussi', 'Réussi'),
        ('echoue', 'Échoué'),
        ('rembourse', 'Remboursé'),
    ]
    
    reservation = models.OneToOneField(
        Reservation, 
        on_delete=models.PROTECT,
        related_name='paiement'
    )
    
    methode = models.CharField(max_length=15, choices=METHODE_CHOICES)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    devise = models.CharField(max_length=3, default='EUR')  # EUR, XAF, USD
    
    # Référence retournée par le système de paiement (Stripe, CinetPay...)
    transaction_id = models.CharField(max_length=100, blank=True)
    
    statut = models.CharField(
        max_length=12, 
        choices=STATUT_CHOICES, 
        default='en_attente'
    )
    
    date_paiement = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Paiement'
    
    def __str__(self):
        return f"Paiement {self.reservation.reference} — {self.statut}"