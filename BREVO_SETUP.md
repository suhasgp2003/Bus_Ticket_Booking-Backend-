# GoBus emails on Render with Brevo

GoBus sends a registration welcome email, one confirmation email per successful
booking request (including all selected seats), and one cancellation email per
successful cancellation request. Each message is sent after its database
transaction commits.

## Deploy the code and configure delivery

1. Publish these backend changes to the branch connected to your Render service.
2. In Brevo, create an API key and register/verify the sender address you will use.
   An SMTP key does not authenticate HTTPS API requests.
3. In Render, open the backend service and go to **Environment**. Keep your
   existing `SECRET_KEY` and `DB_*` variables, then add:

   ```env
   EMAIL_BACKEND=bookings.email_backend.BrevoEmailBackend
   BREVO_API_KEY=your-brevo-api-key
   DEFAULT_FROM_EMAIL=your-verified-sender@example.com
   BREVO_SENDER_NAME=GoBus
   EMAIL_TIMEOUT=10
   ```

   Enter the real key directly in Render. Keep it out of Git and chat. The sender
   address must match a verified sender in your Brevo account. `.env.example`
   contains placeholders for local configuration; Render does not automatically
   read that example file.
4. Save the variables and redeploy the backend. This implementation uses Django
   6.1's `MAILERS` setting, matching the pinned version in `requirements.txt`.

This backend uses `POST https://api.brevo.com/v3/smtp/email` over HTTPS. Although
the endpoint contains `smtp`, it does not make an SMTP connection. Standard SMTP
ports 25, 465, and 587 are blocked on Render's free web services.

## Verify the three email flows

Use your own email address in GoBus:

1. Register with a new username and your email address. Expect the welcome email.
2. Sign in and book an available seat. Expect the confirmation with the bus,
   route, seat, and price. Multiple seats produce one email.
3. Cancel that booking. Expect the cancellation email and the seat to become
   available again.

The backend routes are `POST /api/register/`, `POST /api/booking/`, and
`DELETE /api/booking/cancel/`. Booking and cancellation require the user's token
and a JSON body such as `{"seats": [1, 2]}` containing actual seat IDs.

Check Brevo's transactional email logs and your inbox/spam folder. An API
acceptance response does not guarantee inbox delivery. Accounts without an
email address are skipped; include `email` in the registration request.

## Troubleshooting

- Emails appear only in Render logs: check that `EMAIL_BACKEND` is set to the
  Brevo class above and that the new code was deployed.
- HTTP 401/403: check the API key, account access, and Brevo security settings.
- Other HTTP rejections: check the verified sender, recipient, account status,
  and sending quota in Brevo's dashboard.
- Network failure: inspect Render logs and Brevo's status. Requests have a
  configurable network timeout.

Email failures are logged without API keys or message bodies. They do not undo
successful registration, booking, or cancellation. Delivery is synchronous;
there is no automatic retry queue in this implementation.

## Run automated tests without sending real email

```bash
python manage.py test bookings --settings=TransportNetwork.test_settings
```

The tests use an isolated SQLite database and mocked Brevo requests. They cover
all three endpoint flows, sending after commit, rollback and rejected requests,
API authentication failures, and preserving completed actions during an outage.
Live delivery still needs verification with your configured Brevo account.

## References

- [Brevo transactional email API](https://developers.brevo.com/docs/send-a-transactional-email)
- [Render free service limits](https://render.com/docs/free#other-limitations)
- [Django 6.1 email configuration](https://docs.djangoproject.com/en/6.1/topics/email/)
