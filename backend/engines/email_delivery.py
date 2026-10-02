"""Verification via an explicitly selected HTTPS provider; no SMTP or automatic fallback."""
import base64
import json
import os
import re
from email.message import EmailMessage
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from fastapi import HTTPException


TEST_SENDER = "onboarding@resend.dev"
# Consumer mailbox domains cannot be verified as a domain owned by this service.
MAILBOX_DOMAINS = {"gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com",
    "yahoo.com", "ymail.com", "icloud.com", "aol.com", "proton.me", "protonmail.com"}


def valid_address(value):
    return bool(re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+", value))


def provider():
    # Preserve the existing Resend configuration until the owner explicitly selects Gmail.
    return os.environ.get("EMAIL_PROVIDER", "resend").strip().lower()


def configured(recipient=None):
    sender = os.environ.get("MAIL_FROM", "").strip().lower()
    if not valid_address(sender):
        return False
    domain = sender.rsplit("@", 1)[1]
    if provider() == "gmail":
        return bool(domain != "resend.dev" and all(os.environ.get(key, "").strip()
            for key in ("GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET", "GMAIL_REFRESH_TOKEN")))
    if provider() != "resend" or not os.environ.get("RESEND_API_KEY", "").strip():
        return False
    if domain == "resend.dev":
        owner = os.environ.get("RESEND_TEST_RECIPIENT", "").strip().lower()
        return bool(sender == TEST_SENDER and valid_address(owner) and
            (recipient is None or recipient.strip().lower() == owner))
    # Local configuration presence is not proof of domain verification or inbox delivery.
    return domain not in MAILBOX_DOMAINS


def send_verification(recipient, link, event_key):
    if not configured(recipient):
        raise HTTPException(503, "Email delivery is unavailable for this account. Please contact your college administrator.")
    try:
        body = {"from": "JobJugaad <" + os.environ["MAIL_FROM"].strip() + ">", "to": [recipient],
            "subject": "Verify your JobJugaad email",
            "text": "Verify your email to continue your college account request:\n\n" + link +
                "\n\nThis link expires in one hour. If you did not request this, ignore this email. "
                "Inbox verification does not confirm college affiliation."}
        if provider() == "gmail":
            return send_gmail(recipient, body["text"])
        request = Request("https://api.resend.com/emails", data=json.dumps(body).encode("utf-8"),
            headers={"Authorization": "Bearer " + os.environ["RESEND_API_KEY"].strip(),
                "Content-Type": "application/json", "Idempotency-Key": event_key,
                "User-Agent": "JobJugaad/0.11.2"}, method="POST")
        with urlopen(request, timeout=15) as response:
            sent = json.load(response)
        if not isinstance(sent, dict) or not isinstance(sent.get("id"), str) or not sent["id"].strip():
            raise ValueError("Missing message ID")
    except (HTTPError, URLError, OSError, ValueError, TypeError):
        # Do not expose credentials/provider payloads. A timeout can be ambiguous: no automatic retry.
        # Resend deduplicates the same challenge event key for 24 hours; each resend creates a new key.
        raise HTTPException(503, "Verification email could not be delivered. Please retry after one minute or contact your administrator.") from None


def send_gmail(recipient, text):
    # Owner authorizes gmail.send only. Students do not connect Google or grant mailbox access.
    credentials = urlencode({"client_id": os.environ["GMAIL_CLIENT_ID"].strip(),
        "client_secret": os.environ["GMAIL_CLIENT_SECRET"].strip(),
        "refresh_token": os.environ["GMAIL_REFRESH_TOKEN"].strip(), "grant_type": "refresh_token"}).encode()
    request = Request("https://oauth2.googleapis.com/token", data=credentials,
        headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    with urlopen(request, timeout=15) as response:
        granted = json.load(response)
    if not isinstance(granted, dict) or not isinstance(granted.get("access_token"), str) or not granted["access_token"].strip():
        raise ValueError("Missing access token")
    message = EmailMessage()
    message["From"] = "JobJugaad <" + os.environ["MAIL_FROM"].strip() + ">"
    message["To"] = recipient
    message["Subject"] = "Verify your JobJugaad email"
    message.set_content(text)
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
    request = Request("https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        data=json.dumps({"raw": raw}).encode("utf-8"), headers={"Authorization": "Bearer " + granted["access_token"],
            "Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=15) as response:
        sent = json.load(response)
    if not isinstance(sent, dict) or not isinstance(sent.get("id"), str) or not sent["id"].strip():
        raise ValueError("Missing message ID")
    # Gmail has no Resend-style idempotency key. An ambiguous send timeout is never automatically retried.
