import numpy as np
import logging
from typing import Dict, Any, Tuple, List, Optional
from config import Config

# Setup Logger
logger = logging.getLogger("sCore.Engine")

def clip(x: float, low: float, high: float) -> float:
    return max(low, min(x, high))

class RunMetrics:
    def __init__(self, avg_power: float, avg_hr: float, distance: float, moving_time: int, 
                 elevation_gain: float, weight: float, hr_max: int, hr_rest: int, 
                 temp_c: float, humidity: float):
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

    def compute_score_4_1_math(self, W_avg: float, ascent: float, distance: float, HR_avg: float, 
                               HR_rest: int, HR_max: int, T_act: float, T_ref: float, D: float, 
                               T_hours: float, temp_c: float, humidity: float, 
                               alpha: float = Config.SCORE_ALPHA, 
                               beta: float = Config.SCORE_BETA, 
                               gamma: float = Config.SCORE_GAMMA, 
                               W_ref: float = Config.SCORE_W_REF) -> Tuple[float, float, float]:
        """
        SCORE 4.1 – Implementazione matematica pura fornita
        """
        # 1. Potenza corretta dislivello
        G = ascent / max(distance, 1)
        W_adj = W_avg * (1 + G)
        W_eff = np.log(1 + W_adj / W_ref)

        # 2. HRR robusta
        HRR = (HR_avg - HR_rest) / max(HR_max - HR_rest, 1)
        HRR_clip = clip(HRR, 0.30, 0.95)
        HRR_eff = np.log(1 + beta * HRR_clip)

        # 3. Weather Correction Factor (WCF)
        WCF = (
            1
            + max(0, 0.012 * (temp_c - 20))
            + max(0, 0.005 * (humidity - 60))
        )

        # 4. Performance relativa
        P = T_ref / max(T_act, 1)
        P_clip = clip(P, 0.6, 1.2)
        P_eff = np.log(1 + gamma * P_clip)

        # 5. Stabilità cardiovascolare
        # Nota: D qui deve essere percentuale (es. 5.0) per far funzionare bene sqrt(D) con alpha 0.8
        stability = np.exp(-alpha * np.sqrt(abs(D) / max(T_hours, 1e-6)))

        # 6. SCORE finale
        raw_score = (
            W_eff
            * (WCF * P_eff / HRR_eff)
            * stability
        )
        
        return raw_score, WCF, P

    def compute_score(self, m: RunMetrics, decoupling_decimal: float) -> Tuple[float, Dict[str, Any], float, float]:
        """
        Wrapper che collega l'app alla matematica 4.1
        """
        try:
            # Preparazione Dati per l'algoritmo
            
            # 1. Watt per Kg
            w_kg = m.avg_power / m.weight

            # 2. Tempo di Riferimento (T_ref)
            t_ref_seconds = m.distance_meters / Config.ELITE_SPEED_M_S

            # 3. Decoupling in formato percentuale (es. 3.5 invece di 0.035) per la formula
            d_percent = decoupling_decimal * 100 
            
            # 4. Durata in ore
            t_hours = m.moving_time / 3600.0

            # --- ESECUZIONE ALGORITMO 4.1 ---
            raw_score, wcf, p_ratio = self.compute_score_4_1_math(
                W_avg=w_kg,
                ascent=m.elevation_gain,
                distance=m.distance_meters,
                HR_avg=m.avg_hr,
                HR_rest=m.hr_rest,
                HR_max=m.hr_max,
                T_act=m.moving_time,
                T_ref=t_ref_seconds,
                D=d_percent,
                T_hours=t_hours,
                temp_c=m.temperature,
                humidity=m.humidity
            )

            # --- POST PROCESSING ---
            
            final_score = raw_score * Config.SCALING_FACTOR
            
            # Percentuale rispetto al Record del Mondo (usiamo P della formula)
            wr_pct = p_ratio * 100

            # Costruzione Dettagli per la UI
            details = {
                "Potenza": round(w_kg * 10, 1),           # Proxy visivo
                "Volume": round(t_hours * 10, 1),         # Proxy visivo
                "Intensità": round(m.avg_hr / m.hr_max * 100, 0),
                "Malus Efficienza": f"-{round(abs(d_percent), 1)}%" if d_percent > 5 else "OK"
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

