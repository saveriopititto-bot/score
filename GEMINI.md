# PROGETTO: Score (Streamlit App)

## 1. TECH STACK (Immutable)
# L'Agente DEVE rispettare rigorosamente questo stack.
- **Language:** Python 3.12+
- **Frontend/UI:** Streamlit (No React/Next.js)
- **Database:** PostgreSQL (gestito via `services/db.py`)
- **Integration:** Strava API

- **Dependency Mgmt:** `requirements.txt`

## 2. ARCHITETTURA & CONVENZIONI
Il progetto segue una struttura modulare per Streamlit. NON mettere logica di business nelle Views.

### A. Core Layers
1. **Views (`/views`, `/pages`):** Solo visualizzazione. Usano `st.write`, `st.plotly_chart`. Chiamano i Controller o l'Engine.
2. **Components (`/components`):** Pezzi di UI riutilizzabili (es. `athlete.py`, `kpi.py`).
3. **Engine (`/engine`):** La "Black Box" matematica. Calcolo punteggi (`scoring.py`), metriche (`metrics.py`). Qui NON deve esserci codice Streamlit (`st.*`).
4. **Services (`/services`):** Interazione con l'esterno (DB, API Strava, Meteo).
5. **Controllers (`/controllers`):** Colla tra UI e Logic (es. gestione del sync).

### B. Regole di Coding (Directive)
1. **Database:** Non scrivere query SQL raw nei file `.py` sparsi. Usa sempre i metodi in `services/db.py`.
2. **Migrations:** Le modifiche al DB si fanno SOLO tramite file SQL in `/migrations`, mai on-the-fly.
3. **State Management:** Usa `st.session_state` per mantenere i dati tra i re-run di Streamlit.
4. **Typing:** Usa Type Hints (`def func(a: int) -> str:`) ovunque.
5. **UI Styling:** Tutto il CSS custom deve stare in `ui/style.css` o `ui/style.py`. Non usare `st.markdown("<style>...")` inline nelle pagine.

## 3. WORKFLOW OPERATIVO (DOE)
Se devi aggiungere una feature:
1. **Orchestration:** Controlla prima `PROJECT_MAP.md` per capire quali file toccare.
2. **Impact Analysis:** Se tocchi `/engine/scoring.py`, verifica chi lo importa (es. `dashboard.py`).
3. **Execution:** Scrivi il codice rispettando la separazione (Logica in Engine, UI in Views).
4. **Task Completion:** Al termine di ogni task, scrivi un report consultabile in `CHANGELOG_SESSION.md` con dettagli, fix applicati, e stato finale.

## 4. CODE MAINTENANCE & STYLE RULES

### A. Import Organization
1. **Multi-line Imports:** Quando importi >3 elementi da un modulo, usa formato multi-line:
   ```python
   from ui.visuals import (
       render_history_table,
       quality_circle,
       trend_circle
   )
   ```
2. **Raggruppamento:** Ordina imports: standard library → dipendenze → moduli locali
3. **No Wildcard:** Evita `from module import *`

### B. CSS Organization (style.css)
1. **Navigazione:** Usa [`CSS_GUIDE.md`](ui/CSS_GUIDE.md) per trovare sezioni
2. **Variabili First:** Nuovi colori vanno in `:root` come CSS variables
3. **Sezioni Logiche:** Raggruppa regole correlate insieme
4. **Commenti Intestazione:** Ogni sezione principale ha header con emoji
5. **No Inline Styles:** CSS va in `style.css`, non in `st.markdown("<style>")`

### C. Component Design Patterns
1. **Circle Rendering:** Usa `data-score-tier` per hover dinamici
2. **Responsive:** Sempre testare <768px (mobile) e >1024px (desktop)
3. **Popover vs Expander:** Popover per dettagli compatti, Expander per grandi contenuti
4. **Flex Container:** Usa `.details-row` per layout orizzontale scorrevole

### D. Code Quality
1. **Docstrings:** Funzioni pubbliche devono avere docstring con Args/Returns
2. **Commented Code:** Rimuovere codice commentato o spostare in file separato
3. **Magic Numbers:** Estrarre in `Config` class se riutilizzati
4. **Type Hints:** Obbligatori per parametri e return types

### E. Testing & Verification
1. **Dopo CSS Changes:** Verifica hover effects, responsive, colori tier
2. **Dopo Python Changes:** Test import errors con `python -m compileall`
3. **Funzionalità:** Test manuale delle feature modificate
4. **Cross-browser:** Verifica su Chrome/Firefox/Safari quando possibile

## 5. REFERENCE DOCUMENTATION
- **CSS Navigation:** `ui/CSS_GUIDE.md`
- **Cleanup Todo:** `CLEANUP_RECOMMENDATIONS.md`
- **Project Structure:** `PROJECT_MAP.md`
- **Session Changelog:** `CHANGELOG_SESSION.md` - Fix e update recenti

## 6. COMMON PATTERNS

### Tier-Based Styling
```python
# Python: Determine tier
tier = get_score_tier(score, "score")

# Python: Pass to render function
render_stat_card(value, label, color, tier=tier)

# CSS: Apply tier-specific styles
.stat-circle[data-score-tier="epic"]:hover {
    box-shadow: 0 20px 50px var(--tier-epic-glow);
}
```

### Responsive Layout
```css
/* Desktop first, mobile override */
.component { width: 500px; }

@media (max-width: 768px) {
    .component { width: 100%; }
}
```