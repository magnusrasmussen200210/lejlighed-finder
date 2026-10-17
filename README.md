# Lejlighed Finder

Tjekker udlejernes egne hjemmesider hvert 10. minut (GitHub Actions) for nye lejligheder i Aarhus, der passer til Ida og Magnus, og sender dem på Telegram med en færdig ansøgning.

## Kriterier
- Maks 10.000 kr/md inkl. aconto
- Område: 1) Trøjborg, 2) Frederiksbjerg, 3) Aarhus C (8000)
- Mindst 2 værelser og 45 m²
- Helst ubegrænset lejemål; tidsbegrænset under 12 mdr frasorteres
- Opvaskemaskine og vaskemaskine markeres i beskeden

Kriterierne står øverst i `finder/main.py` og områderne i `finder/areas.py`. Udlejerne står i `finder/sites.py`.

## Secrets (Settings → Secrets and variables → Actions)
| Navn | Indhold |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token fra @BotFather |
| `TELEGRAM_CHAT_ID` | Valgfri. Findes automatisk ud fra den seneste besked til botten |
| `ANSOEGNING` | Master-ansøgningen med `{adresse}`, `{omraade_saetning}`, `{bolig_saetning}`, `{telefon}`, `{email}` |
| `KONTAKT_TELEFON`, `KONTAKT_EMAIL` | Indsættes i ansøgningen |

Personlige oplysninger ligger kun i secrets, fordi repoet er offentligt.

## Kør manuelt
Actions → "Tjek lejligheder" → Run workflow (sæt "dry run" for kun at se loggen).
