from django.db import connections
from django.db.utils import OperationalError
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class HealthCheckView(APIView):
    """
    Endpoint public de supervision. 
    Vérifie que l'instance Django tourne et que la connexion MySQL est opérationnelle.
    """
    permission_classes = [AllowAny]
    throttle_classes = [] # Aucune limite de requête pour permettre au monitoring de tester H24

    def get(self, request, *args, **kwargs):
        health = {"status": "healthy", "database": "up"}
        
        try:
            # On force Django à exécuter une micro-requête sur la base par défaut
            db_conn = connections['default']
            db_conn.cursor()
        except OperationalError:
            health["status"] = "unhealthy"
            health["database"] = "down"
            return Response(health, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        return Response(health, status=status.HTTP_200_OK)
