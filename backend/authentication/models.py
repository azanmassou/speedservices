from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # DÉFINITION DES RÔLES UTILISATEURS
    ROLE_CHOICES = [
        ("client", "Client"),
        ("prestataire", "Prestataire de service"),
        ("admin", "Administrateur"),
    ]

    # CONFIGURATION DES CHAMPS PRINCIPAUX
    email = models.EmailField(
        unique=True, 
        error_messages={
            "unique": "Un utilisateur avec cette adresse email existe déjà."
        }
    )
    
    # Rôle applicatif (Client par défaut)
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default="client"
    )
    
    # Informations complémentaires optionnelles
    phone = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)  # Utile pour la validation d'email future

    # CONFIGURATION DE L'AUTHENTIFICATION
    USERNAME_FIELD = "email"      # L'email sert d'identifiant principal
    REQUIRED_FIELDS = ["username"] # Le username reste requis uniquement pour la console (createsuperuser)

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        db_table = "auth_users"    # Force un nom de table propre dans votre base MySQL

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
