# job-scout

Ein selbst gehostetes Tool, das Junior-Developer-Stellenangebote aus mehreren
Quellen sammelt, nach Umkreis und Stichwort filtert und in einem einfachen
Dashboard anzeigt — inklusive Status-Tracking (neu / interessant / beworben /
abgelehnt) pro Angebot. Beworben wird weiterhin direkt bei der Quelle; dieses
Tool ersetzt keine Bewerbungsplattform, sondern bündelt nur die Übersicht.

## Datenquellen

- [Arbeitnow](https://www.arbeitnow.com/api/job-board-api) — kostenlos, kein API-Key nötig
- [Adzuna](https://developer.adzuna.com/) — kostenloser API-Key nötig (Registrierung), aggregiert u. a. Indeed-Daten

Weitere Quellen (z. B. direktes Scraping von Indeed/Instaffo) sind bewusst
nicht enthalten, da beide in ihren Nutzungsbedingungen automatisiertes
Scraping untersagen. `app/sources/` ist so aufgebaut, dass eine weitere
Quelle nur eine neue Klasse mit einer `fetch()`-Methode braucht (siehe
`app/sources/base.py`).

## Funktionsweise

- Ein Scheduler holt beim Start und danach alle `FETCH_INTERVAL_MINUTES`
  automatisch neue Jobs (Standard: 60 Min).
- Jobs ohne Koordinaten (Arbeitnow) werden per [Nominatim](https://nominatim.org/)
  (OpenStreetMap) geokodiert und die Distanz zu `HOME_LOCATION` berechnet;
  Adzuna liefert Koordinaten direkt mit.
- Angebote werden angezeigt, wenn sie innerhalb von `RADIUS_KM` liegen
  **oder** als Remote markiert sind (siehe `INCLUDE_REMOTE`).
- Bereits gesehene Jobs (`source` + `external_id`) werden nicht erneut
  eingefügt.

## Setup (lokal)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

`.env` anpassen (mindestens `HOME_LOCATION`, `RADIUS_KM`; für Adzuna-Ergebnisse
zusätzlich `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` von https://developer.adzuna.com/ eintragen).

```bash
uvicorn app.main:app --reload
```

Dashboard: http://localhost:8000

## Setup (Docker)

```bash
copy .env.example .env
docker compose up -d --build
```

Die SQLite-Datenbank liegt persistent in `./data/jobs.db`.

## Hinweise

- Ohne Adzuna-Keys laufen nur Arbeitnow-Ergebnisse (die Quelle liefert keine
  Fehler, sondern einfach keine Adzuna-Treffer).
- Nominatim erlaubt maximal 1 Anfrage/Sekunde — bei sehr vielen neuen,
  unterschiedlichen Arbeitnow-Standorten kann ein manuelles "Jetzt
  aktualisieren" dadurch etwas dauern.
- Adzunas `distance`-Parameter ist nicht ganz eindeutig dokumentiert
  (Meilen vs. km). Falls der Umkreis spürbar falsch wirkt, `RADIUS_KM`
  anpassen oder in der [Adzuna-API-Doku](https://developer.adzuna.com/docs/search) nachsehen.

## Tech-Stack

Python · FastAPI · SQLModel (SQLite) · APScheduler · HTMX · Jinja2
