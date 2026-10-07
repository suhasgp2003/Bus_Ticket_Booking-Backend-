from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from .emails import (
    send_account_created_email,
    send_booking_cancellation_email,
    send_booking_confirmation_email,
)


class EmailNotificationTests(SimpleTestCase):
    @patch("bookings.emails.EmailMessage")
    def test_account_creation_email(self, email_message):
        user = SimpleNamespace(username="sam", email="sam@example.com")

        send_account_created_email(user)

        email_message.assert_called_once()
        kwargs = email_message.call_args.kwargs
        self.assertEqual(kwargs["to"], ["sam@example.com"])
        self.assertIn("account has been created successfully", kwargs["body"])
        email_message.return_value.send.assert_called_once_with(fail_silently=True)

    @patch("bookings.emails.EmailMessage")
    def test_booking_confirmation_email_contains_ticket_details(self, email_message):
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
        email_message.return_value.send.assert_called_once_with(fail_silently=True)

    @patch("bookings.emails.EmailMessage")
    def test_cancellation_email_contains_cancelled_seat(self, email_message):
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
        email_message.return_value.send.assert_called_once_with(fail_silently=True)

# Create your tests here.
