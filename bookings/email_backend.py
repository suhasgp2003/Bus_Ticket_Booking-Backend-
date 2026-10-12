"""Deliver GoBus transactional messages through Brevo's HTTPS API."""

import json
from email.utils import parseaddr
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.base import BaseEmailBackend


class BrevoDeliveryError(Exception):
    """A delivery failure safe to log without credentials or message bodies."""


class BrevoEmailBackend(BaseEmailBackend):
    def __init__(self, *, api_key=None, sender_name=None, timeout=None, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key or getattr(settings, "BREVO_API_KEY", "")
        self.sender_name = sender_name or getattr(settings, "BREVO_SENDER_NAME", "GoBus")
        self.timeout = timeout if timeout is not None else 10
        if not self.api_key:
            raise ImproperlyConfigured("Set BREVO_API_KEY to a Brevo API key.")
        if self.timeout <= 0:
            raise ImproperlyConfigured("The Brevo email timeout must be positive.")

    def send_messages(self, email_messages):
        sent = 0
        for message in email_messages or []:
            if not message.recipients():
                continue
            # Validate headers using Django's normal protections.
            message.message()
            if message.attachments or getattr(message, "alternatives", []):
                raise ValueError("The GoBus Brevo backend supports plain text emails only.")
            name, address = parseaddr(str(message.from_email))
            if not address or address.endswith(".local"):
                raise ImproperlyConfigured(
                    "Set DEFAULT_FROM_EMAIL to your verified Brevo sender address."
                )
            payload = {
                "sender": {"email": address, "name": name or self.sender_name},
                "subject": message.subject,
                "textContent": message.body,
            }
            for field in ("to", "cc", "bcc"):
                addresses = getattr(message, field)
                if addresses:
                    payload[field] = [{"email": parseaddr(str(value))[1]} for value in addresses]
            if message.reply_to:
                payload["replyTo"] = {"email": parseaddr(str(message.reply_to[0]))[1]}
            request = Request(
                "https://api.brevo.com/v3/smtp/email",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "api-key": self.api_key,
                    "accept": "application/json",
                    "content-type": "application/json",
                },
                method="POST",
            )
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    if response.status != 201:
                        raise BrevoDeliveryError("Brevo did not accept the email.")
            except HTTPError as exc:
                # Do not log response bodies or headers: they may contain private data.
                raise BrevoDeliveryError(
                    f"Brevo rejected the email (HTTP {exc.code}). Check the API key, "
                    "verified sender, account status, and sending quota."
                ) from None
            except (URLError, OSError):
                raise BrevoDeliveryError("Unable to reach Brevo within the email timeout.") from None
            sent += 1
        return sent
