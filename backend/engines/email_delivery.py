"""Transactional verification via Resend HTTPS; the default sender is owner-test-only."""
import json
import os
import re
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from fastapi import HTTPException


TEST_SENDER = "onboarding@resend.dev"
# Consumer mailbox domains cannot be verified as a domain owned by this service.
MAILBOX_DOMAINS = {"gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com",
    "yahoo.com", "ymail.com", "icloud.com", "aol.com", "proton.me", "protonmail.com"}


def valid_address(value):
    return bool(re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+", value))


def configured(recipient=None):
    sender = os.environ.get("MAIL_FROM", "").strip().lower()
    if not os.environ.get("RESEND_API_KEY", "").strip() or not valid_address(sender):
        return False
    domain = sender.rsplit("@", 1)[1]
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
        request = Request("https://api.resend.com/emails", data=json.dumps(body).encode("utf-8"),
            headers={"Authorization": "Bearer " + os.environ["RESEND_API_KEY"].strip(),
                "Content-Type": "application/json", "Idempotency-Key": event_key,
                "User-Agent": "JobJugaad/0.11.1"}, method="POST")
        with urlopen(request, timeout=15) as response:
            sent = json.load(response)
        if not isinstance(sent, dict) or not isinstance(sent.get("id"), str) or not sent["id"].strip():
            raise ValueError("Missing message ID")
    except (HTTPError, URLError, OSError, ValueError, TypeError):
        # Do not expose credentials/provider payloads. A timeout can be ambiguous: no automatic retry.
        # Resend deduplicates the same challenge event key for 24 hours; each resend creates a new key.
        raise HTTPException(503, "Verification email could not be delivered. Please retry after one minute or contact your administrator.") from None
