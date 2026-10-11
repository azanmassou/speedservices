import re
from django.core.exceptions import ValidationError


class ComplexPasswordValidator:
    def validate(self, password, user=None):
        if not re.search(r"[A-Z]", password):
            raise ValidationError(
                "Le mot de passe doit contenir au moins une majuscule.",
                code="password_no_upper",
            )
        if not re.search(r"[a-z]", password):
            raise ValidationError(
                "Le mot de passe doit contenir au moins une minuscule.",
                code="password_no_lower",
            )
        if not re.search(r"\d", password):
            raise ValidationError(
                "Le mot de passe doit contenir au moins un chiffre.",
                code="password_no_digit",
            )
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_+-]', password):
            raise ValidationError(
                "Le mot de passe doit contenir au moins un caractère spécial.",
                code="password_no_special",
            )

    def get_help_text(self):
        return "Votre mot de passe doit contenir au moins une majuscule, une minuscule, un chiffre et un caractère spécial."
