# from rest_framework.views import exception_handler
# from rest_framework.response import Response
# from rest_framework import status


# def custom_exception_handler(exc, context):
#     response = exception_handler(exc, context)

#     if response is not None:
#         # Uniformise la structure d'erreur
#         custom_response = {
#             'success': False,
#             'errors': response.data,
#             'status_code': response.status_code,
#         }
#         response.data = custom_response

#     return response

import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger("django")

def custom_exception_handler(exc, context):
    """
    Intercepte TOUTES les erreurs du backend et les convertit en un format JSON unique.
    """
    # 1. Laisse Django Rest Framework gérer ses erreurs natives (400 Bad Request, 401 Unauthorized, 403, etc.)
    response = exception_handler(exc, context)

    # 2. Si DRF a déjà traité l'erreur, on harmonise la structure de sortie
    if response is not None:
        custom_data = {
            "status": "error",
            "message": "Une erreur de validation ou de permission est survenue.",
            "errors": response.data # Contient le détail des champs (ex: {"email": ["Cet email est déjà utilisé."]})
        }
        
        # Si l'erreur est un message de texte brut, on le range proprement
        if isinstance(response.data, dict) and "detail" in response.data:
            custom_data["message"] = response.data["detail"]
            del custom_data["errors"]
            
        response.data = custom_data
        return response

    # 3. CRASH CRITIQUE (Erreur 500) : Si 'response' est None, c'est un crash Python non géré
    # On logue immédiatement le crash complet avec la trace pour le développeur
    view_name = context['view'].__class__.__name__
    logger.error(f"Crash critique détecté dans la vue {view_name}: {str(exc)}", exc_info=True)

    # On renvoie un JSON propre au client, sans JAMAIS divulguer les secrets du code
    return Response(
        {
            "status": "error",
            "message": "Une erreur interne du serveur est survenue. Nos équipes ont été notifiées.",
            "errors": None
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
