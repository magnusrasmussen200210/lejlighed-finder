"""Send ansøgninger på mail fra Magnus' Gmail (kræver et app-password)."""
import os
import re
import smtplib
from email.message import EmailMessage

GENERIC = re.compile(r"^(info|mail|kontakt|post|udlejning|bolig|boligudlejning|taurus|dacas|cej|support|kundeservice|admin)@", re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


def configured() -> bool:
    return bool(os.environ.get("GMAIL_APP_PASSWORD") and os.environ.get("KONTAKT_EMAIL"))


def pick_recipient(text: str, own_domain_hint: str = "") -> str | None:
    """Vælg udlejerens kontaktperson fra annoncen; generelle adresser bruges kun hvis der ikke er andre."""
    me = (os.environ.get("KONTAKT_EMAIL") or "").strip().lower()
    found = []
    for e in EMAIL.findall(text):
        e = e.rstrip(".").lower()
        if e != me and e not in found and not e.endswith((".png", ".jpg", ".webp")):
            found.append(e)
    specific = [e for e in found if not GENERIC.match(e)]
    return (specific or found or [None])[0]


def send(to: str, subject: str, body: str):
    sender = os.environ["KONTAKT_EMAIL"].strip()
    msg = EmailMessage()
    msg["From"] = f"Magnus og Ida <{sender}>"
    msg["To"] = to
    msg["Bcc"] = sender  # så ansøgningen også ligger i Magnus' indbakke
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as s:
        s.login(sender, re.sub(r"\s", "", os.environ["GMAIL_APP_PASSWORD"]))
        s.send_message(msg)
