from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


def send_email(to: str, subject: str, body: str) -> None:
    sender = os.getenv("ASSISTANT_EMAIL")
    password = os.getenv("ASSISTANT_EMAIL_PASSWORD")
    smtp_host = os.getenv("ASSISTANT_SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("ASSISTANT_SMTP_PORT", "587"))

    if not sender or not password:
        raise RuntimeError(
            "Email credentials are missing. Set ASSISTANT_EMAIL and "
            "ASSISTANT_EMAIL_PASSWORD."
        )

    message = EmailMessage()
    message["From"] = sender
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        server.starttls()
        server.login(sender, password)
        server.send_message(message)
