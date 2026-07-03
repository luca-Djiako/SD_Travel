from django.db import models

class CompagnieAerienne(models.Model):
    """
    Référentiel des compagnies aériennes.
    L'admin ajoute les compagnies une fois, 
    les réutilise sur tous les vols.
    """
    nom = models.CharField(max_length=100)
    code_iata = models.CharField(max_length=3, unique=True)  # ex: AF, TK, EK
    logo = models.ImageField(upload_to='compagnies/', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Compagnie Aérienne'
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom} ({self.code_iata})"


class Vol(models.Model):
    """
    Un vol publié par l'admin SD Travel.
    L'admin entre ses propres prix (marge incluse).
    """
    
    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('complet', 'Complet'),
        ('annule', 'Annulé'),
        ('termine', 'Terminé'),
    ]
    
    ESCALE_CHOICES = [
        (0, 'Direct'),
        (1, '1 escale'),
        (2, '2 escales'),
    ]
    
    # Informations du vol
    numero_vol = models.CharField(max_length=10)  # ex: AF-547
    compagnie = models.ForeignKey(
        CompagnieAerienne, 
        on_delete=models.PROTECT,
        related_name='vols'
    )
    
    # Itinéraire
    ville_depart = models.CharField(max_length=100)
    code_depart = models.CharField(max_length=3)   # ex: DLA (Douala)
    ville_arrivee = models.CharField(max_length=100)
    code_arrivee = models.CharField(max_length=3)  # ex: CDG (Paris)
    
    # Dates et horaires
    date_depart = models.DateTimeField()
    date_arrivee = models.DateTimeField()
    
    # Caractéristiques
    nombre_escales = models.IntegerField(choices=ESCALE_CHOICES, default=0)
    
    # Prix par classe (définis par l'admin SD Travel)
    prix_economique = models.DecimalField(max_digits=10, decimal_places=2)
    prix_affaires = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    prix_premiere  = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    # Disponibilité
    places_economique = models.IntegerField(default=0)
    places_affaires = models.IntegerField(default=0)
    places_premiere = models.IntegerField(default=0)
    
    # Statut
    statut = models.CharField(
        max_length=10, 
        choices=STATUT_CHOICES, 
        default='actif'
    )
    est_populaire = models.BooleanField(default=False)  # mis en avant sur accueil
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Vol'
        ordering = ['date_depart']
    
    def __str__(self):
        return f"{self.numero_vol} — {self.ville_depart} → {self.ville_arrivee}"
    
    @property
    def duree_vol(self):
        """Calcule la durée du vol automatiquement"""
        delta = self.date_arrivee - self.date_depart
        heures = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        return f"{heures}h{minutes:02d}"
    
    @property
    def est_disponible(self):
        return self.statut == 'actif' and self.places_economique > 0