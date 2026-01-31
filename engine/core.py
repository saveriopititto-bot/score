import numpy as np
import logging
from typing import Dict, Any, Tuple, List, Optional
from config import Config
from scipy.stats import norm

# Setup Logger
logger = logging.getLogger("sCore.Engine")

# ============================================================
# 1. MODELLI BASE (μ0, σ0) PER DISTANZA E SESSO
# ============================================================

# ============================================================
# 1. RECORD MONDIALI (secondi)
# ============================================================

WR = {
    "5k": 12*60 + 35,
    "10k": 26*60 + 11,
    "hm": 57*60 + 31,
    "m": 2*3600 + 35
}

# ============================================================
# 2. CURVE PERCENTILI (parametri base)
# ============================================================

BASE_PARAMS = {
    ("5k", "M"): (6.68, 0.35),
    ("5k", "F"): (6.79, 0.38),
    ("10k", "M"): (7.39, 0.33),
    ("10k", "F"): (7.51, 0.36),
    ("hm", "M"): (8.16, 0.32),
    ("hm", "F"): (8.27, 0.35),
    ("m", "M"): (8.91, 0.30),
    ("m", "F"): (9.00, 0.33),
}

# ============================================================
# 3. PARAMETRI AGE-DEPENDENTI μ(a), σ(a)
# ============================================================

def age_params(mu0, sigma0, age, sex):
    k_mu = 0.006 if sex == "M" else 0.007
    k_sigma = 0.001
    mu = mu0 + k_mu * (age - 30)
    sigma = sigma0 + k_sigma * max(0, age - 30)
    return mu, sigma

# ============================================================
# 4. PERCENTILE REALE
# ============================================================

def percentile(distance, sex, age, T_act):
    if (distance, sex) not in BASE_PARAMS:
        return 0.5 # Default fallback
    
    # Safety Check for invalid time
    if T_act <= 10: # Min 10 seconds to avoid log(0) issues
        return 0.99 

    mu0, sigma0 = BASE_PARAMS[(distance, sex)]
    mu, sigma = age_params(mu0, sigma0, age, sex)
    z = (np.log(T_act) - mu) / sigma
    return norm.cdf(z)

# ============================================================
# 5. FATTORI DI CORREZIONE T_ref
# ============================================================

def F_age(age):
    return 1 + 0.15 * ((age - 30) / 30) ** 2

def F_sex(sex):
    return 1.0 if sex == "M" else 1.10

def F_level(p):
    """
    p is the percentile (0.0=Fastest, 1.0=Slowest)
    Elite athletes (p near 0) have factor 1.0
    Rookies (p near 1) have factor > 1.0
    """
    if p < 0.05: return 1.00
    if p < 0.15: return 1.05
    if p < 0.30: return 1.12
    if p < 0.50: return 1.20
    return 1.35

def F_surface(surface):
    return {
        "road": 1.00,
        "gravel": 1.03,
        "trail": 1.06,
        "trail_tech": 1.08
    }.get(surface, 1.00)

def F_env(temp_c):
    return 1 + max(0, temp_c - 15) * 0.01

# ============================================================
# 6. TEMPO DI RIFERIMENTO DINAMICO
# ============================================================

def T_ref(distance, age, sex, p, surface, temp_c):
    # Fallback to 10k WR if unknown
    wr_sec = WR.get(distance, 26*60 + 11) 
    
    return (
        wr_sec
        * F_age(age)
        * F_sex(sex)
        * F_level(p)
        * F_surface(surface)
        * F_env(temp_c)
    )

class RunMetrics:
    def __init__(self, avg_power: float, avg_hr: float, distance: float, moving_time: int, 
                 elevation_gain: float, weight: float, hr_max: int, hr_rest: int, 
                 temp_c: float, humidity: float, age: int = 30, sex: str = "M"):
        self.avg_power = avg_power
        self.avg_hr = avg_hr
        self.distance_meters = distance
        self.moving_time = moving_time
        self.elevation_gain = elevation_gain
        self.weight = weight if weight > 0 else 70.0 # Evita div by zero
        self.hr_max = hr_max
        self.hr_rest = hr_rest
        self.temperature = temp_c
        self.humidity = humidity
        self.age = age
        self.sex = sex

class ScoreEngine:
    def __init__(self):
        self.version = Config.ENGINE_VERSION
    
    def calculate_decoupling(
        self,
        power_stream: List[float],
        hr_stream: List[float],
        window_sec: int = 300 # Unused in 4.2 but kept for signature comp
    ) -> float:
        """
        Drift Fisiologico (Engine 4.2).
        Basato su Costo Cardiaco (HR/Power) tra prima e seconda metà.
        """
        power = np.array(power_stream)
        hr = np.array(hr_stream)

        # Minimo 120 datapoint (2 min) per validità
        if len(power) < 120 or len(hr) < 120:
             return 0.0

        n = len(power)
        split = int(n * 0.5)

        # Divisione in due metà
        p1, h1 = np.mean(power[:split]), np.mean(hr[:split])
        p2, h2 = np.mean(power[split:]), np.mean(hr[split:])

        # Protezione divisione per zero
        if p1 <= 0 or p2 <= 0 or h1 <= 0 or h2 <= 0:
            return 0.0

        # Calcolo Costo Cardiaco (battiti per watt)
        cost1 = h1 / p1
        cost2 = h2 / p2

        # Calcolo Drift % (sempre >= 0)
        drift = (cost2 - cost1) / cost1
        return float(max(0.0, drift))

    def calculate_zones(self, watts_stream: List[int], ftp: int) -> Dict[str, float]:
        """Calcola distribuzione zone per i grafici"""
        if not watts_stream or not ftp: return {}
        zones = [0]*7
        # Coggan Zones
        limits = [0.55, 0.75, 0.90, 1.05, 1.20, 1.50] 
        for w in watts_stream:
            if w < ftp * limits[0]: zones[0]+=1
            elif w < ftp * limits[1]: zones[1]+=1
            elif w < ftp * limits[2]: zones[2]+=1
            elif w < ftp * limits[3]: zones[3]+=1
            elif w < ftp * limits[4]: zones[4]+=1
            elif w < ftp * limits[5]: zones[5]+=1
            else: zones[6]+=1
        total = len(watts_stream)
        return {f"Z{i+1}": round(c/total*100, 1) for i, c in enumerate(zones)}

    def compute_score_4_1_math(self, W_avg: float, ascent: float, distance_m: float, HR_avg: float, 
                               HR_rest: int, HR_max: int, T_act_sec: float, D: float, 
                               T_hours: float, temp_c: float, humidity: float,
                               dist_label: str, sex: str, age: int,
                               surface: str = "road",
                               alpha: float = Config.SCORE_ALPHA, 
                               beta: float = 3.0, 
                               gamma: float = 2.0) -> Tuple[float, float, float]:
        """
        SCORE 4.1 INTEGRATO (CON LIVELLO PERCENTILE E T_REF DINAMICO)
        """
        # ---- percentile reale
        p = percentile(dist_label, sex, age, T_act_sec)

        # ---- tempo di riferimento dinamico
        # Follow the spec: Tref depends on the athlete's level (percentile p)
        Tref = T_ref(dist_label, age, sex, p, surface, temp_c)

        # ---- performance
        P = Tref / max(T_act_sec, 1)
        
        P_eff = np.log(1 + gamma * np.clip(P, 0.6, 1.2))

        # ---- potenza efficace
        # CORREZIONE 2: W_ref da Config
        W_ref = getattr(Config, "W_REF", 6.0)
        G = ascent / max(distance_m, 1)
        W_eff = np.log(1 + (W_avg * (1 + G)) / W_ref)

        # ---- HRR robusta
        # CORREZIONE 4: Denominatore min 10
        den = max(HR_max - HR_rest, 10)
        HRR = (HR_avg - HR_rest) / den
        HRR = np.clip(HRR, 0.30, 0.95)
        HRR_eff = np.log(1 + beta * HRR)

        # ---- weather correction
        WCF = (
            1
            + max(0, 0.012 * (temp_c - 20))
            + max(0, 0.005 * (humidity - 60))
        )

        # ---- stabilità (Drift 4.2 Logic)
        # D here is already the Cost Index drift (max 0).
        # We apply penalty if drift is high.
        stability = np.exp(-alpha * D)

        # ---- SCORE RAW calculation
        # Raw value - no arbitrary scaling
        raw_score = W_eff * (WCF * P_eff / HRR_eff) * stability
        
        # ---- SCORE 4.2 FINAL LOGISTIC NORMALIZATION
        # Maps raw score to 0-100 curve
        # RAW expected roughly 0.5 - 2.0 range for normal activities
        # Tuning factor K=2.5 provides good spread
        K = 2.5
        score_logistic = 100 * (1 - np.exp(-K * raw_score))
        
        SCORE = np.clip(score_logistic, 0.0, 100.0)

        return SCORE, p, Tref, WCF

    def compute_score(self, m: RunMetrics, decoupling_decimal: float) -> Tuple[float, Dict[str, Any], float, float, Dict[str, Any]]:
        """
        Wrapper che collega l'app alla matematica 4.1
        """
        try:
            # Infer Distance Label
            d = m.distance_meters
            dist_label = "10k" # Default fallback
            if d < 8000: dist_label = "5k"
            elif d < 16000: dist_label = "10k"
            elif d < 30000: dist_label = "hm"
            else: dist_label = "m"

            # Preparazione Dati per l'algoritmo
            
            # 1. Watt per Kg
            w_kg = m.avg_power / m.weight

            # 2. Durata in ore
            t_hours = m.moving_time / 3600.0

            # 3. Decoupling Decimal (passiamo il valore puro, es. 0.05)
            # Nota: la UI potrebbe volerlo in % per display

            # --- ESECUZIONE ALGORITMO 4.1 ---
            final_score, p, t_ref, wcf = self.compute_score_4_1_math(
                W_avg=w_kg,
                ascent=m.elevation_gain,
                distance_m=m.distance_meters,
                HR_avg=m.avg_hr,
                HR_rest=m.hr_rest,
                HR_max=m.hr_max,
                T_act_sec=m.moving_time,
                D=decoupling_decimal,
                T_hours=t_hours,
                temp_c=m.temperature,
                humidity=m.humidity,
                dist_label=dist_label,
                sex=m.sex,
                age=m.age,
                surface="road" 
            )

            # --- GAMING LAYER ---
            quality = self.run_quality(final_score)

            # --- POST PROCESSING ---
            # Percentuale (p è probabilità di essere PIÙ VELOCI dell'utente)
            # Scala: 0.0 (Elite) -> 1.0 (Lento)
            # Vogliamo visualizzarlo come "Better than X%": 
            # Se p=0.99 (99% sono più veloci), il rank è 1%.
            # Se p=0.01 (1% sono più veloci), il rank è 99%.
            wr_pct = (1 - p) * 100

            # Costruzione Dettagli per la UI
            # CORREZIONE 5: Formattazione Ore
            t_ref_int = int(t_ref)
            h = int(t_ref_int // 3600)
            mins = int((t_ref_int % 3600) // 60)
            s = int(t_ref_int % 60)
            t_ref_fmt = f"{h}:{mins:02d}:{s:02d}" if h > 0 else f"{mins}:{s:02d}"

            details = {
                "Potenza": round(w_kg * 10, 1),           # Proxy visivo
                "Volume": round(t_hours * 10, 1),         # Proxy visivo
                "Intensità": round(m.avg_hr / m.hr_max * 100, 0),
                "Target": t_ref_fmt,
                "Malus Efficienza": f"-{round(abs(decoupling_decimal * 100), 1)}%" if decoupling_decimal > 0.05 else "OK"
            }

            return final_score, details, wcf, wr_pct, quality
            
        except Exception as e:
            logger.error(f"Error computing score: {e}")
            return 0.0, {}, 1.0, 0.0, {}

    def get_rank(self, score: float) -> Tuple[str, str]:
        # Use config thresholds if available
        # The thresholds in Config (e.g., 0.35) seem to be for a different scale (decimal).
        # We mapped the score to 0-100, so we should use intuitive thresholds or adapt.
        # Let's keep the 0-100 logic but make it robust.
        if score >= 100: return "ELITE 🏆", "text-purple-600"
        if score >= 85: return "PRO 🥇", "text-blue-600"
        if score >= 70: return "ADVANCED 🥈", "text-green-600"
        if score >= 50: return "INTERMEDIATE 🥉", "text-yellow-600"
        return "ROOKIE 🎗️", "text-gray-600"

    def age_adjusted_percentile(self, score: float, age: int) -> int:
        # Semplice logica di percentile basata sull'età
        base = 50
        if age > 30: base += (age - 30) * 0.5
        pct = min(99, (score / 100) * base + 30)
        return int(pct)

    # ============================================================
    # GAMING LAYER – QUALITÀ DELLA CORSA
    # ============================================================

    def run_quality(self, score: float) -> Dict[str, str]:
        """
        Valuta la qualità della singola corsa (gaming feedback)
        score: SCORE 4.1 già scalato 0–100
        """
        if score >= 95:
            return {"label": "LEGENDARY 🔥", "color": "purple"}
        if score >= 90:
            return {"label": "EPIC 🏆", "color": "blue"}
        if score >= 80:
            return {"label": "GREAT 💎", "color": "green"}
        if score >= 70:
            return {"label": "SOLID 👍", "color": "teal"}
        if score >= 60:
            return {"label": "OK ⚖️", "color": "yellow"}
        if score >= 40:
            return {"label": "WEAK 💤", "color": "gray"}
        return {"label": "WASTED ⚠️", "color": "red"}

    # ============================================================
    # ACHIEVEMENT SYSTEM
    # ============================================================

    def achievements(self, scores_last_runs: List[float]) -> List[str]:
        """
        Ritorna una lista di achievement sbloccati
        scores_last_runs: lista score 4.1 (0–100) ordinati dal più vecchio al più recente
        """
        ach = []
        if not scores_last_runs:
            return ach

        last = scores_last_runs[-1]

        # --- Qualità singola corsa ---
        if last >= 95:
            ach.append("🔥 Legendary Run")
        elif last >= 90:
            ach.append("🏆 Epic Run")
        elif last >= 80:
            ach.append("💎 Great Run")

        # --- Costanza (ultime 5) ---
        if len(scores_last_runs) >= 5:
            avg5 = np.mean(scores_last_runs[-5:])
            if avg5 >= 80:
                ach.append("📈 Consistency Beast (5 runs)")

        # --- Costanza (ultime 10) ---
        if len(scores_last_runs) >= 10:
            avg10 = np.mean(scores_last_runs[-10:])
            if avg10 >= 75:
                ach.append("🧱 Iron Engine (10 runs)")

        # --- Miglioramento ---
        if len(scores_last_runs) >= 3:
            if scores_last_runs[-1] > scores_last_runs[-2] > scores_last_runs[-3]:
                ach.append("🚀 On Fire (3 improving runs)")

        # --- Ritorno dopo crisi ---
        if len(scores_last_runs) >= 4:
            if scores_last_runs[-4] < 50 and last >= 70:
                ach.append("💪 Comeback")

        return ach

    # ============================================================
    # QUALITY TREND
    # ============================================================

    def quality_trend(self, scores: List[float], window: int = 5) -> Dict[str, float]:
        """
        Calcola trend qualità con rolling average
        """
        if len(scores) < window:
            return {"trend": 0.0, "direction": "flat", "delta": 0.0}

        recent = np.mean(scores[-window:])
        previous = np.mean(scores[-2*window:-window]) if len(scores) >= 2*window else recent

        delta = recent - previous

        if delta > 3:
            direction = "up"
        elif delta < -3:
            direction = "down"
        else:
            direction = "flat"

        return {
            "recent_avg": round(recent, 1),
            "previous_avg": round(previous, 1),
            "delta": round(delta, 1),
            "direction": direction
        }

    # ============================================================
    # LAST 10 RUNS COMPARISON
    # ============================================================

    def compare_last_10(self, scores: List[float]) -> Dict[str, Any]:
        """
        Confronta l'ultima corsa con le precedenti 10
        """
        if len(scores) < 2:
            return {}

        last = scores[-1]
        last10 = scores[-10:] if len(scores) >= 10 else scores[:-1]

        avg10 = np.mean(last10)
        best10 = max(last10)
        worst10 = min(last10)

        return {
            "vs_avg": round(last - avg10, 1),
            "vs_best": round(last - best10, 1),
            "vs_worst": round(last - worst10, 1),
            "rank": sum(last >= s for s in last10) + 1,
            "total": len(last10) + 1
        }

    # ============================================================
    # FULL GAMING FEEDBACK
    # ============================================================

    def gaming_feedback(self, scores_history: List[float]) -> Dict[str, Any]:
        """
        Restituisce feedback completo per la UI
        """
        if not scores_history:
            return {}

        quality = self.run_quality(scores_history[-1])
        achievements = self.achievements(scores_history)
        trend = self.quality_trend(scores_history)
        compare = self.compare_last_10(scores_history)

        return {
            "quality": quality,
            "achievements": achievements,
            "trend": trend,
            "comparison": compare
        }
    
    # ============================================================
    # 4. REPLAY SYSTEM (SCORING V4.2)
    # ============================================================
    
    def replay_score(self, run: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ricalcola lo score di una corsa esistente usando l'engine corrente (4.2).
        Non sovrascrive, ritorna il risultato per confronto o salvataggio separato.
        """
        try:
            # Estrazione streams raw (se disponibili nel dizionario)
            watts = run.get('raw_watts', [])
            hr = run.get('raw_hr', [])
            
            # 1. Ricalcolo Drift 4.2
            dec = self.calculate_decoupling(watts, hr)
            
            # 2. Parametri base
            # Se run['duration_sec'] non c'è, usa len(watts)
            if 'duration_sec' in run:
                dur_sec = run['duration_sec']
            else:
                 dur_sec = len(watts) if watts else 3600

            t_hours = dur_sec / 3600.0
            
            weight = run.get('weight', Config.DEFAULT_WEIGHT)
            w_kg = (run.get('avg_power', 0)) / weight if weight > 0 else 0
            
            dist_label = run.get('dist_label', "10k") # Dovresti idealmente inferirlo dalla distanza
            if 'distance_km' in run:
                d = run['distance_km'] * 1000
                if d < 8000: dist_label = "5k"
                elif d < 16000: dist_label = "10k"
                elif d < 30000: dist_label = "hm"
                else: dist_label = "m"

            # 3. Calcolo Math
            score, p, tref, wcf = self.compute_score_4_1_math(
                W_avg=w_kg,
                ascent=run.get('elevation', 0),
                distance_m=run.get('distance_km', 10) * 1000,
                HR_avg=run.get('avg_hr', 0),
                HR_rest=run.get('hr_rest', Config.DEFAULT_HR_REST),
                HR_max=run.get('hr_max', Config.DEFAULT_HR_MAX),
                T_act_sec=dur_sec,
                D=dec,
                T_hours=t_hours,
                temp_c=run.get('temp', 20),
                humidity=run.get('humidity', 50),
                dist_label=dist_label,
                sex=run.get('sex', 'M'),
                age=run.get('age', Config.DEFAULT_AGE)
            )
            
            return {
                "score_version": self.version,
                "score": score,
                "decoupling": dec,
                "wcf": wcf,
                "percentile": p,
                "tref_sec": tref
            }

        except Exception as e:
            logger.error(f"Replay Error: {e}")
            return {}

