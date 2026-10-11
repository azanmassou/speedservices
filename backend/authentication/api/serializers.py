import re
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer dédié à la validation et à la création de compte utilisateur."""
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True, 
        style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = ["username", "email", "password", "password_confirm"]
    
    def validate_username(self, value):
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError(
                "Le nom d'utilisateur doit contenir au moins 3 caractères."
            )
        if len(value) > 30:
            raise serializers.ValidationError(
                "Le nom d'utilisateur ne doit pas dépasser 30 caractères."
            )
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError(
                "Le nom d'utilisateur ne peut contenir que des lettres, chiffres et underscores."
            )
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "Ce nom d'utilisateur est déjà pris."
            )
        return value

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "Cet email est déjà utilisé."
            )
        return value

    def validate(self, attrs):
        # 1. Vérification de la correspondance des mots de passe
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password_confirm": "Les mots de passe ne correspondent pas."
            })
        
        # 2. Utilisation des validateurs de sécurité natifs de Django (Mots de passe communs, etc.)
        try:
            validate_password(attrs['password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        
        # 3. Sécurité : le password ne doit pas contenir le username ou l'email
        password_lower = attrs['password'].lower()
        
        if attrs.get('username') and attrs['username'].lower() in password_lower:
            raise serializers.ValidationError({
                "password": "Le mot de passe ne doit pas contenir le nom d'utilisateur."
            })
            
        if attrs.get('email'):
            email_prefix = attrs['email'].split('@')[0].lower()
            if email_prefix in password_lower:
                raise serializers.ValidationError({
                    "password": "Le mot de passe ne doit pas contenir votre adresse email."
                })
        
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        return User.objects.create_user(**validated_data)
    

class UserSerializer(serializers.ModelSerializer):
    """Serializer dédié à l'affichage sécurisé du profil utilisateur en JSON."""
    role = serializers.CharField(source='get_role_display', default='client')
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']
        read_only_fields = ["id", "email"]
