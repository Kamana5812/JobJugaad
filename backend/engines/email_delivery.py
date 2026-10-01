"""Transactional verification via Gmail HTTPS API; no SMTP ports or inbox-reading scope."""
import base64
import json
import os
import re
from email.message import EmailMessage
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from fastapi import HTTPException


def configured():
    sender = os.environ.get("MAIL_FROM", "").strip()
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", sender) and all(
        os.environ.get(key, "").strip() for key in
        ("GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET", "GMAIL_REFRESH_TOKEN")))


def send_verification(recipient, link, event_key):
    if not configured():
        raise HTTPException(503, "Email delivery is not configured. Please contact your college administrator.")
    # Only gmail.send is needed. Refresh tokens and provider responses never enter logs or API responses.
    try:
        credentials = urlencode({"client_id": os.environ["GMAIL_CLIENT_ID"],
            "client_secret": os.environ["GMAIL_CLIENT_SECRET"],
            "refresh_token": os.environ["GMAIL_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
        request = Request("https://oauth2.googleapis.com/token", data=credentials,
            headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
        with urlopen(request, timeout=15) as response:
            access = json.load(response).get("access_token")
        if not isinstance(access, str) or not access:
            raise ValueError("Missing access token")
        message = EmailMessage()
        message["From"] = "JobJugaad <" + os.environ["MAIL_FROM"].strip() + ">"
        message["To"] = recipient
        message["Subject"] = "Verify your JobJugaad email"
        message.set_content("Verify your email to continue your college account request:\n\n" + link +
            "\n\nThis link expires in one hour. If you did not request this, ignore this email. "
            "Inbox verification does not confirm college affiliation.")
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
        request = Request("https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            data=json.dumps({"raw": raw}).encode(), headers={"Authorization": "Bearer " + access,
            "Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=15) as response:
            sent = json.load(response)
        if not isinstance(sent.get("id"), str) or not sent["id"]:
            raise ValueError("Missing message ID")
    except (HTTPError, URLError, OSError, ValueError, TypeError):
        # A send timeout can be ambiguous: do not automatically retry and generate duplicate mail.
        raise HTTPException(503, "Verification email could not be delivered. Please retry after one minute or contact your administrator.") from None
