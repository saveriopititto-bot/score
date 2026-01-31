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
    mu = mu0 - k_mu * (age - 30)
    sigma = sigma0 + k_sigma * max(0, age - 30)
    return mu, sigma

# ============================================================
# 4. PERCENTILE REALE
# ============================================================

def percentile(distance, sex, age, T_act):
    if (distance, sex) not in BASE_PARAMS:
        return 0.5 # Default fallback
        
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
    if p > 0.95: return 1.00
    if p > 0.85: return 1.05
    if p > 0.70: return 1.12
    if p > 0.50: return 1.20
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
    
    def calculate_decoupling(self, power_stream: List[int], hr_stream: List[int]) -> float:
        """
        Calcola il disaccoppiamento aerobico (Pw:Hr).
        Ritorna un valore decimale (es. 0.035 per 3.5%).
        """
        if not power_stream or not hr_stream or len(power_stream) != len(hr_stream):
            return 0.0

        length = len(power_stream)
        half_point = length // 2

        # Prima metà
        p1 = np.mean(power_stream[:half_point])
        h1 = np.mean(hr_stream[:half_point])
        
        # Seconda metà
        p2 = np.mean(power_stream[half_point:])
        h2 = np.mean(hr_stream[half_point:])

        if h1 == 0 or h2 == 0 or p1 == 0: 
            return 0.0

        ratio1 = p1 / h1
        ratio2 = p2 / h2

        decoupling = (ratio1 - ratio2) / ratio1
        return float(decoupling)

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
        # CORREZIONE 1: p0 fissato a 0.70 per il riferimento
        p0 = 0.70
        Tref = T_ref(dist_label, age, sex, p0, surface, temp_c)

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

        # ---- stabilità
        # CORREZIONE 3: D positivo
        D = max(0.0, D)
        stability = np.exp(-alpha * np.sqrt(D / max(T_hours, 1e-6)))

        # ---- SCORE finale
        SCORE = W_eff * (WCF * P_eff / HRR_eff) * stability

        return SCORE, p, Tref, WCF

    def compute_score(self, m: RunMetrics, decoupling_decimal: float) -> Tuple[float, Dict[str, Any], float, float]:
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

            # --- POST PROCESSING ---
            # Percentuale (p è decimale 0-1) -> 0-100
            wr_pct = p * 100

            # Costruzione Dettagli per la UI
            # CORREZIONE 5: Formattazione Ore
            t_ref_int = int(t_ref)
            h = int(t_ref_int // 3600)
            m = int((t_ref_int % 3600) // 60)
            s = int(t_ref_int % 60)
            t_ref_fmt = f"{h}:{m:02d}:{s:02d}" if h > 0 else f"{m}:{s:02d}"

            details = {
                "Potenza": round(w_kg * 10, 1),           # Proxy visivo
                "Volume": round(t_hours * 10, 1),         # Proxy visivo
                "Intensità": round(m.avg_hr / m.hr_max * 100, 0),
                "Target": t_ref_fmt,
                "Malus Efficienza": f"-{round(abs(decoupling_decimal * 100), 1)}%" if decoupling_decimal > 0.05 else "OK"
            }

            return final_score, details, wcf, wr_pct
            
        except Exception as e:
            logger.error(f"Error computing score: {e}")
            return 0.0, {}, 1.0, 0.0

    def get_rank(self, score: float) -> Tuple[str, str]:
        if score >= 100: return "ELITE 🏆", "text-purple-600"
        
        # Use config thresholds if available, otherwise defaults
        thresholds = getattr(Config, 'RANK_THRESHOLDS', {})
        
        # NOTE: logic in original code was hardcoded. adapting to potentially use config or keep simplicity
        # For now keeping it simple but cleaner
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

