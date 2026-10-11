import logging
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

# Initialisation du logger dédié
logger = logging.getLogger('authentication')


def register_email(user_email: str, username: str) -> bool:
    """
    Envoie un email de bienvenue stylisé (HTML + Texte brut) à un nouvel utilisateur.
    Garantit une capture stricte des exceptions pour ne pas bloquer le flux principal.
    """
    try:
        subject = "Bienvenue sur Speed Services !"
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Speed Services <noreply@speedservices.bj>')

        # 1. Préparation du contexte pour le template
        context = {
            "username": username,
            "support_url": "https://speedservices.bj"  # Exemple de lien utile
        }

        # 2. Génération du contenu HTML à partir d'un fichier template
        try:
            html_content = render_to_string("emails/welcome_email.html", context)
            # Génération automatique du texte brut à partir du HTML pour éviter la duplication
            text_content = strip_tags(html_content)
        except Exception as template_err:
            # Fallback (secours) en texte brut si le fichier HTML est introuvable ou mal écrit
            logger.warning(f"Template HTML non trouvé ou invalide ({template_err}). Utilisation du texte brut.")
            text_content = f"Bonjour {username},\n\nMerci de votre inscription sur Speed Services !"
            html_content = None

        # 3. Construction de l'email avec la classe native avancée de Django
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[user_email.strip()]
        )

        # Si le HTML a été généré avec succès, on l'attache à l'email
        if html_content:
            msg.attach_alternative(html_content, "text/html")

        # 4. Envoi de l'email
        msg.send(fail_silently=False)
        
        logger.info(f"Mail de bienvenue envoyé avec succès à {user_email}")
        return True
        
    except Exception as e:
        # 'exc_info=True' va enregistrer toute la stack trace de l'erreur dans vos fichiers de logs
        logger.error(f"Échec critique de l'envoi du mail de bienvenue à {user_email}: {e}", exc_info=True)
        return False
