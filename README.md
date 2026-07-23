# 🏃‍♂️ SCORE 7.0 Lab Thooth_and_nails

Web app avanzata per l'analisi delle performance di corsa, basata sull'algoritmo **SCORE 4.1** e integrata con **Strava**, **Open-Meteo** e **Google Gemini AI**.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://scorerun.streamlit.app/)

> 📝 **Session Updates:** Vedi [`CHANGELOG_SESSION.md`](CHANGELOG_SESSION.md) per gli ultimi fix e miglioramenti

## 🚀 Funzionalità

- **Analisi OAuth Strava**: Importazione sicura delle attività.
- **SCORE 4.1 Engine**: Algoritmo proprietario che valuta l'efficienza bio-meccanica normalizzata per pendenza, peso e meteo.
- **Riegel Benchmark**: Confronto dinamico della prestazione rispetto al Record del Mondo sulla specifica distanza.
- **AI Coach (Gemini)**: Analisi qualitativa automatica basata su Zone di Potenza e Disaccoppiamento aerobico.
- **Deep Dive**: Grafici interattivi (Altair) per distribuzione zone, scatter plot HR/Power e deriva cardiaca.

## 🛠 Tech Stack

- **Frontend/Backend**: Python, Streamlit
- **Data Science**: Pandas, NumPy
- **Visualization**: Altair
- **External Services**:
  - Strava API v3 (Auth & Data Streams)
  - Open-Meteo API (Historical Weather)
  - Google Gemini 1.5 Flash (Generative AI Analysis)

## 📂 Struttura Modulare

Il progetto segue un'architettura pulita:
- `engine/`: Logica matematica pura (RunMetrics, ScoreEngine).
- `services/`: Gestione API esterne e caching.
- `ui/`: Componenti di visualizzazione e grafici.
- `app.py`: Controller principale dell'applicazione.

## 🤖 Agent Task Reporting
**Regola operativa:** Ogni task completata da un agente viene documentata in [`CHANGELOG_SESSION.md`](CHANGELOG_SESSION.md) con report dettagliato consultabile.



<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/drive/1P1aoVHVlak3hd7OO1Bl1_lrLjGhctTGE

## Run Locally

**Prerequisites:**  Node.js


1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. Run the app:
   `npm run dev`

