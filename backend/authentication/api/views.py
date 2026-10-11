import logging
from django.conf import settings
from django.db import transaction
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

from utils.emails import register_email
from .serializers import RegisterSerializer, UserSerializer

logger = logging.getLogger("authentication")


class RegisterThrottle(AnonRateThrottle):
    scope = "register"


class RegisterView(generics.CreateAPIView):
    """API d'inscription qui isole le token refresh dans un Cookie HTTP-Only."""
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [RegisterThrottle]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Envoi de l'email sécurisé sans bloquer l'écriture en BDD si panne SMTP
        try:
            register_email(user.email, user.username)
        except Exception as e:
            logger.warning(
                f"Inscription OK pour {user.email} mais envoi mail échoué: {e}"
            )

        logger.info(f"Nouvel utilisateur créé: {user.email} (ID: {user.id})")

        # Génération des paires de jetons JWT
        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user).data

        # Construction de la réponse (Seul l'access token sort en JSON brut)
        response = Response(
            {
                "message": "Compte créé avec succès",
                "user": user_data,
                "token": str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED,
        )

        # Injection hermétique du refresh token dans les cookies du navigateur
        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,                     # Protection XSS
            secure=not settings.DEBUG,         # Exige HTTPS hors mode local
            samesite="Lax",                    # Protection CSRF
            max_age=7 * 24 * 60 * 60,          # Valide 7 jours
        )

        return response
