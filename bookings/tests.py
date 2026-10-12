import json
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from django.contrib.auth.models import User
from django.core import mail
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from .email_backend import BrevoDeliveryError
from .models import Booking, Bus

from .emails import (
    send_account_created_email,
    send_booking_cancellation_email,
    send_booking_confirmation_email,
)


class EmailNotificationTests(SimpleTestCase):
    @patch("bookings.emails.EmailMessage")
    def test_account_creation_email(self, email_message):
        email_message.return_value.send.return_value = 1
        user = SimpleNamespace(username="sam", email="sam@example.com")

        send_account_created_email(user)

        email_message.assert_called_once()
        kwargs = email_message.call_args.kwargs
        self.assertEqual(kwargs["to"], ["sam@example.com"])
        self.assertIn("account has been created successfully", kwargs["body"])
        email_message.return_value.send.assert_called_once_with()

    @patch("bookings.emails.EmailMessage")
    def test_booking_confirmation_email_contains_ticket_details(self, email_message):
        email_message.return_value.send.return_value = 1
        user = SimpleNamespace(username="sam", email="sam@example.com")
        booking = SimpleNamespace(
            bus=SimpleNamespace(
                bus_name="City Express",
                bus_number="CE-101",
                origin="Bengaluru",
                destination="Mysuru",
                price="250.00",
            ),
            seat=SimpleNamespace(seat_number="A1"),
        )

        send_booking_confirmation_email(user, [booking])

        body = email_message.call_args.kwargs["body"]
        self.assertIn("City Express", body)
        self.assertIn("A1", body)
        email_message.return_value.send.assert_called_once_with()

    @patch("bookings.emails.EmailMessage")
    def test_cancellation_email_contains_cancelled_seat(self, email_message):
        email_message.return_value.send.return_value = 1
        user = SimpleNamespace(username="sam", email="sam@example.com")
        booking = SimpleNamespace(
            bus=SimpleNamespace(
                bus_name="City Express",
                bus_number="CE-101",
                origin="Bengaluru",
                destination="Mysuru",
            ),
            seat=SimpleNamespace(seat_number="A1"),
        )

        send_booking_cancellation_email(user, [booking])

        self.assertIn("A1", email_message.call_args.kwargs["body"])
        email_message.return_value.send.assert_called_once_with()

    @patch("bookings.emails.EmailMessage")
    def test_email_delivery_error_does_not_interrupt_the_request(self, email_message):
        email_message.return_value.send.side_effect = RuntimeError("SMTP unavailable")
        user = SimpleNamespace(username="sam", email="sam@example.com")

        with self.assertLogs("bookings.emails", level="ERROR"):
            send_account_created_email(user)

        email_message.return_value.send.assert_called_once_with()

    @patch("bookings.emails.EmailMessage")
    def test_missing_recipient_skips_email(self, email_message):
        send_account_created_email(SimpleNamespace(username="sam", email=""))
        email_message.assert_not_called()

    @patch("bookings.emails.EmailMessage")
    def test_zero_sent_is_logged(self, email_message):
        email_message.return_value.send.return_value = 0
        with self.assertLogs("bookings.emails", level="ERROR"):
            send_account_created_email(SimpleNamespace(username="sam", email="sam@example.com"))


BREVO_MAILERS = {
    "default": {
        "BACKEND": "bookings.email_backend.BrevoEmailBackend",
        "OPTIONS": {"api_key": "test-api-key", "sender_name": "GoBus", "timeout": 5},
    },
}


@override_settings(MAILERS=BREVO_MAILERS, DEFAULT_FROM_EMAIL="sender@example.com")
class BrevoBackendTests(SimpleTestCase):
    @patch("bookings.email_backend.urlopen")
    def test_api_request_and_success_count(self, urlopen):
        urlopen.return_value.__enter__.return_value.status = 201
        message = mail.EmailMessage("Welcome", "Hi Sam", to=["sam@example.com"])
        self.assertEqual(message.send(), 1)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.brevo.com/v3/smtp/email")
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.get_header("Api-key"), "test-api-key")
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 5)
        self.assertEqual(json.loads(request.data), {
            "sender": {"email": "sender@example.com", "name": "GoBus"},
            "to": [{"email": "sam@example.com"}],
            "subject": "Welcome", "textContent": "Hi Sam",
        })

    @patch("bookings.email_backend.urlopen")
    def test_empty_messages_do_not_make_requests(self, urlopen):
        self.assertEqual(mail.mailers.default.send_messages([]), 0)
        self.assertEqual(mail.mailers.default.send_messages([mail.EmailMessage()]), 0)
        urlopen.assert_not_called()

    @override_settings(BREVO_API_KEY="", MAILERS={"default": {
        "BACKEND": "bookings.email_backend.BrevoEmailBackend",
    }})
    def test_missing_api_key_is_actionable(self):
        with self.assertRaisesMessage(ImproperlyConfigured, "BREVO_API_KEY"):
            mail.EmailMessage("Welcome", "Hi", to=["sam@example.com"]).send()

    @override_settings(DEFAULT_FROM_EMAIL="noreply@busticketbooking.local")
    @patch("bookings.email_backend.urlopen")
    def test_placeholder_sender_is_rejected(self, urlopen):
        with self.assertRaisesMessage(ImproperlyConfigured, "verified Brevo sender"):
            mail.EmailMessage("Welcome", "Hi", to=["sam@example.com"]).send()
        urlopen.assert_not_called()

    @patch("bookings.email_backend.urlopen")
    def test_http_failures_are_sanitized(self, urlopen):
        urlopen.side_effect = HTTPError("https://api.brevo.com", 401, "private response", {}, None)
        with self.assertRaisesMessage(BrevoDeliveryError, "HTTP 401") as error:
            mail.EmailMessage("Welcome", "Hi", to=["sam@example.com"]).send()
        self.assertNotIn("private response", str(error.exception))
        self.assertNotIn("test-api-key", str(error.exception))

    @patch("bookings.email_backend.urlopen")
    def test_network_failure_is_reported(self, urlopen):
        urlopen.side_effect = URLError("network down")
        with self.assertRaisesMessage(BrevoDeliveryError, "Unable to reach Brevo"):
            mail.EmailMessage("Welcome", "Hi", to=["sam@example.com"]).send()

    @patch("bookings.email_backend.urlopen")
    def test_header_injection_is_rejected_before_network(self, urlopen):
        with self.assertRaises(ValueError):
            mail.EmailMessage("Welcome\nBcc: other@example.com", "Hi", to=["sam@example.com"]).send()
        urlopen.assert_not_called()


@override_settings(MAILERS=BREVO_MAILERS, DEFAULT_FROM_EMAIL="sender@example.com")
class TransactionalEmailFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user("sam", "sam@example.com", "test-password")
        self.bus = Bus.objects.create(
            bus_name="City Express", bus_number="CE-101", origin="Bengaluru",
            destination="Mysuru", features="AC", start_time="09:00", reach_time="12:00",
            no_of_seats=2, price="250.00",
        )
        self.seats = list(self.bus.seats.order_by("id"))

    @patch("bookings.email_backend.urlopen")
    def test_registration_booking_and_cancellation_send_after_commit(self, urlopen):
        urlopen.return_value.__enter__.return_value.status = 201
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            response = self.client.post(reverse("register"), {
                "username": "alex", "email": "alex@example.com", "password": "test-password",
            }, format="json")
            urlopen.assert_not_called()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(callbacks), 1)
        self.assertIn("account has been created", json.loads(urlopen.call_args.args[0].data)["textContent"])

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")
        seat_ids = [seat.id for seat in self.seats]
        urlopen.reset_mock()
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse("bookings"), {"seats": seat_ids}, format="json")
            urlopen.assert_not_called()
        self.assertEqual(response.status_code, 201)
        urlopen.assert_called_once()
        payload = json.loads(urlopen.call_args.args[0].data)
        self.assertEqual(payload["to"], [{"email": "alex@example.com"}])
        for seat in self.seats:
            self.assertIn(seat.seat_number, payload["textContent"])

        urlopen.reset_mock()
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.delete(reverse("booking-cancel"), {"seats": seat_ids}, format="json")
            urlopen.assert_not_called()
        self.assertEqual(response.status_code, 200)
        urlopen.assert_called_once()
        self.assertIn("cancellation was successful", json.loads(urlopen.call_args.args[0].data)["textContent"])
        self.assertFalse(Booking.objects.exists())
        self.assertFalse(self.bus.seats.filter(is_booked=True).exists())

    @patch("bookings.email_backend.urlopen")
    def test_failed_actions_do_not_send_emails(self, urlopen):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse("register"), {
                "username": "sam", "email": "sam@example.com", "password": "test-password",
            }, format="json")
        self.assertEqual(response.status_code, 400)
        self.client.force_authenticate(self.user)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse("bookings"), {"seats": [999999]}, format="json")
        self.assertEqual(response.status_code, 404)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.delete(reverse("booking-cancel"), {"seats": [self.seats[0].id]}, format="json")
        self.assertEqual(response.status_code, 400)
        urlopen.assert_not_called()

    @patch("bookings.email_backend.urlopen")
    def test_rolled_back_registration_does_not_send(self, urlopen):
        with self.captureOnCommitCallbacks(execute=True):
            with self.assertRaises(RuntimeError):
                with transaction.atomic():
                    self.client.post(reverse("register"), {
                        "username": "alex", "email": "alex@example.com", "password": "test-password",
                    }, format="json")
                    raise RuntimeError("Rollback")
        self.assertFalse(User.objects.filter(username="alex").exists())
        urlopen.assert_not_called()

    @patch("bookings.email_backend.urlopen")
    def test_brevo_failure_preserves_completed_actions(self, urlopen):
        urlopen.side_effect = HTTPError("https://api.brevo.com", 401, "Unauthorized", {}, None)
        with self.assertLogs("bookings.emails", level="ERROR"):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(reverse("register"), {
                    "username": "alex", "email": "alex@example.com", "password": "test-password",
                }, format="json")
        self.assertEqual(response.status_code, 201)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")
        with self.assertLogs("bookings.emails", level="ERROR"):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(reverse("bookings"), {"seats": [self.seats[0].id]}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Booking.objects.count(), 1)
        with self.assertLogs("bookings.emails", level="ERROR"):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.delete(reverse("booking-cancel"), {"seats": [self.seats[0].id]}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Booking.objects.exists())
