# Mappa del Progetto (Context Navigation)

> 📝 **Ultimi aggiornamenti:** [`CHANGELOG_SESSION.md`](CHANGELOG_SESSION.md)

## ROOT
- `app.py` -> Entry point principale (Main Navigation).
- `config.py` -> Configurazioni globali.
- `requirements.txt` -> Librerie.

## LOGICA DI BUSINESS (Il cervello)
- `/engine/core.py` -> Logica principale.
- `/engine/scoring.py` -> Algoritmi di calcolo punteggio.
- `/engine/metrics.py` -> Calcolo KPI.
- `/engine/insights.py` -> Generazione testi/analisi.

## DATI & SERVIZI (Il braccio)
- `/services/db.py` -> Wrapper database Postgres.
- `/services/strava_api.py` -> Chiamate dirette a Strava.
- `/services/strava_sync.py` -> Logica di sincronizzazione dati.

- `/services/meteo_svc.py` -> Dati meteo.

## INTERFACCIA UTENTE (Il volto)
- `/views/dashboard.py` -> Pagina principale (grafici, tabelle).
- `/views/landing.py` -> Home page per non loggati.
- `/views/login.py` -> Gestione autenticazione.
- `/components/athlete.py` -> Visualizzazione profilo atleta.
- `/components/kpi.py` -> Widget KPI.
- `/ui/style.css` -> Fogli di stile globali.

## DATABASE SCHEMA
- `/migrations/` -> Storico delle modifiche al DB (controllare sempre l'ultimo `v4_*.sql`).

---

## 📝 AGENT TASK REPORTING
**Regola:** Ogni volta che un agente completa una task, DEVE scrivere un report consultabile in `CHANGELOG_SESSION.md` con:
- Modifiche effettuate
- Bug risolti
- File toccati
- Stato finale
