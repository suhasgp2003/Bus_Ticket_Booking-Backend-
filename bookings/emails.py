import logging

from django.core.mail import EmailMessage


logger = logging.getLogger(__name__)


def _send_email(*, recipient, subject, body):
    """Send a transactional email without interrupting a completed request."""
    if not recipient:
        return

    try:
        EmailMessage(subject=subject, body=body, to=[recipient]).send(
            fail_silently=True
        )
    except Exception:
        logger.exception("Unable to send email notification to %s", recipient)


def send_account_created_email(user):
    _send_email(
        recipient=user.email,
        subject="Your Bus Ticket Booking account is ready",
        body=(
            f"Hi {user.username},\n\n"
            "Your account has been created successfully. You can now sign in "
            "and book bus tickets.\n\n"
            "Thank you,\nBus Ticket Booking"
        ),
    )


def send_booking_confirmation_email(user, bookings):
    booking_details = "\n".join(
        (
            f"- {booking.bus.bus_name} ({booking.bus.bus_number}): "
            f"{booking.bus.origin} to {booking.bus.destination}, "
            f"seat {booking.seat.seat_number}, price {booking.bus.price}"
        )
        for booking in bookings
    )
    _send_email(
        recipient=user.email,
        subject="Your bus booking is confirmed",
        body=(
            f"Hi {user.username},\n\n"
            "Your booking has been confirmed.\n\n"
            f"Booking details:\n{booking_details}\n\n"
            "Thank you,\nBus Ticket Booking"
        ),
    )


def send_booking_cancellation_email(user, bookings):
    booking_details = "\n".join(
        (
            f"- {booking.bus.bus_name} ({booking.bus.bus_number}): "
            f"{booking.bus.origin} to {booking.bus.destination}, "
            f"seat {booking.seat.seat_number}"
        )
        for booking in bookings
    )
    _send_email(
        recipient=user.email,
        subject="Your bus booking has been cancelled",
        body=(
            f"Hi {user.username},\n\n"
            "Your booking cancellation was successful.\n\n"
            f"Cancelled booking details:\n{booking_details}\n\n"
            "Thank you,\nBus Ticket Booking"
        ),
    )
