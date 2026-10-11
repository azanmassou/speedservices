import logging
from django.conf import settings
from django.db import transaction
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from utils.emails import register_email
from .serializers import UserSerializer, RegisterSerializer, LoginSerializer

logger = logging.getLogger("authentication")

# --- UTILITAIRES DE FACTORISATION ---

def set_auth_cookie(response, refresh_token, max_age=7*24*60*60):
    """Injecte de manière uniforme le cookie HTTP-Only."""
    response.set_cookie(
        key="refresh_token",
        value=str(refresh_token),
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
        max_age=max_age,
    )

def generate_auth_response(user, message, status_code=status.HTTP_200_OK):
    """Centralise la création des tokens et le formatage JSON de la réponse."""
    refresh = RefreshToken.for_user(user)
    response = Response(
        {
            "message": message,
            "user": UserSerializer(user).data,
            "token": str(refresh.access_token),
        },
        status=status_code,
    )
    set_auth_cookie(response, refresh)
    return response


# --- THROTTLES ---

class RegisterThrottle(AnonRateThrottle): scope = "register"
class LoginThrottle(AnonRateThrottle): scope = "login"


# --- VUES APPLICATIVES ---

class RegisterView(generics.CreateAPIView):
    """API d'inscription sécurisée."""
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [RegisterThrottle]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        try:
            register_email(user.email, user.username)
        except Exception as e:
            logger.warning(f"Inscription OK pour {user.email} mais envoi mail échoué: {e}")

        logger.info(f"Nouvel utilisateur créé: {user.email} (ID: {user.id})")
        return generate_auth_response(user, "Compte créé avec succès", status.HTTP_201_CREATED)


class LoginView(APIView):
    """API de connexion sécurisée."""
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        logger.info(f"Connexion réussie pour : {user.email} (ID: {user.id})")
        return generate_auth_response(user, "Connexion réussie")


class CustomTokenRefreshView(TokenRefreshView):
    """Régénère un access token à partir du cookie HTTP-Only."""
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            return Response(
                {"status": "error", "message": "Session expirée ou introuvable. Veuillez vous reconnecter."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = self.get_serializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except (InvalidToken, TokenError) as e:
            return Response(
                {"status": "error", "message": "Votre session n'est plus valide.", "details": e.args[0]},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response({"status": "success", "token": serializer.validated_data["access"]}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """API de déconnexion. Supprime le cookie contenant le refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        logger.info(f"Déconnexion de l'utilisateur : {request.user.email}")
        response = Response({"status": "success", "message": "Déconnexion réussie. À bientôt !"}, status=status.HTTP_200_OK)
        set_auth_cookie(response, "", max_age=0)  # Expire instantanément le cookie
        return response
