"""Send en testmail til Magnus selv og vis hvad der går galt, uden at afsløre adgangskoden."""
import os
import re
import traceback

from finder import mailer

pw = os.environ.get("GMAIL_APP_PASSWORD", "")
me = os.environ.get("KONTAKT_EMAIL", "")
letters = re.sub(r"\s", "", pw)
print("adgangskode: længde", len(pw), "uden mellemrum", len(letters), "kun bogstaver a-z:", letters.isalpha() and letters.isascii(),
      "linjeskift:", "\n" in pw or "\r" in pw)
print("mail: længde", len(me), "linjeskift/mellemrum:", me != me.strip(), "gmail:", me.strip().lower().endswith("@gmail.com"))
try:
    mailer.send(me.strip(), "Test fra Lejlighed Finder", "Hvis du kan læse denne, virker automatisk ansøgning på mail.")
    print("TESTMAIL SENDT")
except Exception as e:
    traceback.print_exc()
