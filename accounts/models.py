from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class UtilisateurManager(UserManager):
    """
    Manager custom : force role='admin' automatiquement
    quand on crée un superuser via `createsuperuser`.
    """
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        return super().create_superuser(username, email, password, **extra_fields)


class Utilisateur(AbstractUser):
    """
    On étend AbstractUser pour ajouter nos champs custom.
    Le champ username est remplacé par email comme identifiant principal.
    """

    ROLE_CHOICES = [
        ('client', 'Client'),
        ('admin', 'Administrateur'),
    ]

    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20, blank=True)
    photo_profil = models.ImageField(
        upload_to='profils/',
        blank=True,
        null=True
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='client'
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    objects = UtilisateurManager()

    # On utilise email comme identifiant de connexion
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def is_admin_site(self):
        return self.is_superuser or self.role == 'admin'