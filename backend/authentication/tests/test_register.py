import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

User = get_user_model()


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class RegisterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('register')
        
        # Désactivation du Throttling pour les suites de tests complexes
        from ..api.views import RegisterView
        RegisterView.throttle_classes = []
        
        # Nettoyage systématique de la boîte d'envoi fictive
        mail.outbox.clear()

    def _payload(self, **overrides):
        """Générateur de payloads d'inscription uniques."""
        uid = uuid.uuid4().hex[:6]
        base = {
            "username": f"user_{uid}",
            "email": f"user_{uid}@test.bj",
            "password": "Happylouis66@",
            "password_confirm": "Happylouis66@",
        }
        base.update(overrides)
        return base

    def test_1_register_success(self):
        """Vérifie la création de compte, l'access token JSON et la pose du cookie."""
        res = self.client.post(self.url, self._payload(), format='json')
        self.assertEqual(res.status_code, 201, res.data)
        
        self.assertIn('token', res.data)
        self.assertIn('user', res.data)
        self.assertNotIn('tokens', res.data)

        # Test de présence et configuration du cookie sécurisé
        self.assertIn('refresh_token', res.cookies)
        self.assertTrue(res.cookies['refresh_token']['httponly'])

    def test_2_mail_sent(self):
        """Vérifie qu'un email de bienvenue est envoyé."""
        payload = self._payload()
        res = self.client.post(self.url, payload, format='json')
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(len(mail.outbox), 1)

    def test_3_mail_failure_ok(self):
        """Vérifie la tolérance aux pannes du serveur d'envoi d'emails."""
        with patch('authentication.api.views.register_email', side_effect=Exception("SMTP down")):
            res = self.client.post(self.url, self._payload(), format='json')
            self.assertEqual(res.status_code, 201, res.data)

    def test_4_duplicate_email(self):
        """Vérifie le blocage en cas de conflit d'adresses email."""
        p = self._payload()
        self.client.post(self.url, p, format='json')
        
        p2 = self._payload(email=p['email'])
        res = self.client.post(self.url, p2, format='json')
        self.assertEqual(res.status_code, 400)

    def test_5_password_mismatch(self):
        """Vérifie le rejet si les mots de passe ne concordent pas."""
        res = self.client.post(self.url, self._payload(password_confirm="XXXxxx111@"), format='json')
        self.assertEqual(res.status_code, 400)

    def test_6_missing_fields(self):
        """Vérifie la détection des structures JSON incomplètes."""
        res = self.client.post(self.url, {}, format='json')
        self.assertEqual(res.status_code, 400)
