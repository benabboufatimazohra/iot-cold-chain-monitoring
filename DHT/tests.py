from django.core import mail
from django.test import TestCase, override_settings

from .models import Incident

POST_URL = "/api/post/"


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    ALERT_EMAIL_RECIPIENTS=["operator@example.com"],
)
class IncidentAndAlertTests(TestCase):
    def post(self, temp, hum=50):
        response = self.client.post(
            POST_URL, {"temp": temp, "hum": hum}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)

    def test_reading_in_range_creates_no_incident_and_no_email(self):
        self.post(5)
        self.assertEqual(Incident.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_high_temperature_opens_incident_and_sends_one_email(self):
        self.post(9.5)
        self.post(11)
        incident = Incident.objects.get()
        self.assertTrue(incident.is_open)
        self.assertEqual(incident.counter, 2)
        self.assertEqual(incident.max_temp, 11)
        self.assertEqual(len(mail.outbox), 1)  # one email per incident, not per reading
        self.assertIn("haute", mail.outbox[0].subject)

    def test_low_temperature_email_says_low(self):
        self.post(1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("basse", mail.outbox[0].subject)

    def test_back_in_range_closes_incident(self):
        self.post(12)
        self.post(6)
        incident = Incident.objects.get()
        self.assertFalse(incident.is_open)
        self.assertIsNotNone(incident.end_at)

    def test_new_excursion_after_closing_sends_new_email(self):
        self.post(12)
        self.post(6)
        self.post(0)
        self.assertEqual(Incident.objects.count(), 2)
        self.assertEqual(len(mail.outbox), 2)

    @override_settings(ALERT_EMAIL_RECIPIENTS=[])
    def test_no_recipients_configured_sends_nothing(self):
        self.post(12)
        self.assertEqual(Incident.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 0)
