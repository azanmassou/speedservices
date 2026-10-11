import re
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

User = get_user_model()

# --- VALIDATEURS INDÉPENDANTS (FACTORISATION) ---

def clean_and_check_password_format(password, exception_to_raise):
    """Vérifie d'un seul coup si le mot de passe possède 1 majuscule, 1 minuscule et 1 chiffre."""
    # Cette regex unique vérifie les 3 conditions en une seule passe CPU (Lookahead assertions)
    if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$', password):
        raise exception_to_raise

def validate_username_rules(value):
    """Applique les contraintes de format sur le nom d'utilisateur."""
    value = value.strip()
    if not (3 <= len(value) <= 30):
        raise serializers.ValidationError("Le nom d'utilisateur doit contenir entre 3 et 30 caractères.")
    if not re.match(r"^[a-zA-Z0-9_]+$", value):
        raise serializers.ValidationError("Le nom d'utilisateur ne peut contenir que des lettres, chiffres et underscores.")
    if User.objects.filter(username__iexact=value).exists():
        raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
    return value


# --- SERIALIZERS ---

class UserSerializer(serializers.ModelSerializer):
    """Serializer dédié à l'affichage sécurisé du profil utilisateur en JSON."""
    role = serializers.CharField(source="get_role_display", default="client")

    class Meta:
        model = User
        fields = ["id", "username", "email", "role"]
        read_only_fields = ["id", "email"]


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer dédié à la validation et à la création de compte utilisateur."""
    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})
    password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ["username", "email", "password", "password_confirm"]

    def validate_username(self, value):
        return validate_username_rules(value)

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    def validate(self, attrs):
        # 1. Correspondance des mots de passe
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Les mots de passe ne correspondent pas."})

        # 2. Validations natives Django (mots de passe communs, etc.)
        try:
            validate_password(attrs["password"])
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        # 3. Sécurité : Recherche d'identifiants dans le mot de passe
        pwd_lower = attrs["password"].lower()
        if attrs.get("username", "").lower() in pwd_lower:
            raise serializers.ValidationError({"password": "Le mot de passe ne doit pas contenir le nom d'utilisateur."})
        
        email_prefix = attrs.get("email", "").split("@")[0].lower()
        if email_prefix and email_prefix in pwd_lower:
            raise serializers.ValidationError({"password": "Le mot de passe ne doit pas contenir votre adresse email."})

        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """Serializer de connexion optimisé pour rejeter instantanément les requêtes malveillantes."""
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        email = attrs.get("email", "").lower().strip()
        password = attrs.get("password", "")

        if not email or not password:
            raise serializers.ValidationError("L'email et le mot de passe sont obligatoires.")

        # --- OPTIMISATION CPU : Filtre de format instantané ---
        generic_error = serializers.ValidationError("Adresse email ou mot de passe incorrect.")
        clean_and_check_password_format(password, exception_to_raise=generic_error)

        # --- VÉRIFICATION BASE DE DONNÉES (MySQL) ---
        user = authenticate(username=email, password=password)
        if not user:
            raise generic_error
        if not user.is_active:
            raise serializers.ValidationError("Ce compte utilisateur a été désactivé.")

        attrs["user"] = user
        return attrs
