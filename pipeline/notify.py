"""
Email notification for AI Governance Tracker.

Sends a plain text email digest when new entries are detected.
Uses Gmail SMTP with an app password.

Required environment variables:
    GMAIL_USER — sender Gmail address
    GMAIL_APP_PASSWORD — Gmail app password (requires 2FA enabled)
    NOTIFY_EMAIL — recipient email address
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
TRACKER_URL = "https://sovereign-t-code.github.io/ai-governance-tracker"


def send_notification(new_entries):
    """
    Send an email listing newly detected legislation entries.

    Does nothing if credentials aren't configured or if the send fails
    (logs a warning but never crashes the pipeline).

    Args:
        new_entries: List of entry dicts that are new since the last run
    """
    gmail_user = os.environ.get("GMAIL_USER")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient = os.environ.get("NOTIFY_EMAIL")

    if not all([gmail_user, gmail_password, recipient]):
        logger.warning(
            "Email notification skipped — missing one or more env vars: "
            "GMAIL_USER, GMAIL_APP_PASSWORD, NOTIFY_EMAIL"
        )
        return

    # Only notify for legislation, never for news articles
    legislation_entries = [e for e in new_entries if e.get("type") != "news"]
    if not legislation_entries:
        return

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    count = len(legislation_entries)
    subject = f"AI Governance Tracker — {count} new legislation item{'s' if count != 1 else ''} detected ({today})"

    # Build plain text body
    lines = [
        f"AI Governance Tracker found {count} new legislation item{'s' if count != 1 else ''} on {today}.\n",
        "=" * 60,
        "",
    ]

    for entry in legislation_entries:
        description = entry.get("summary") or entry.get("title", "No title")
        lines.append(f"[{entry.get('status', 'Unknown')}] {entry.get('title', 'No title')}")
        lines.append(f"  Jurisdiction: {entry.get('jurisdiction', 'Unknown')}")
        lines.append(f"  Domains:      {', '.join(entry.get('domains', []))}")
        lines.append(f"  Summary:      {description}")
        lines.append("")

    lines.append("=" * 60)
    lines.append(f"View the full tracker: {TRACKER_URL}")
    lines.append("This is an automated message from AI Governance Tracker.")

    body = "\n".join(lines)

    # Build email
    msg = MIMEMultipart()
    msg["From"] = gmail_user
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, recipient, msg.as_string())

        logger.info(f"Notification email sent to {recipient} ({count} new entries)")

    except Exception as e:
        logger.warning(f"Failed to send notification email: {e}")
