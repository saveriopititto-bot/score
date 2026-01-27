import numpy as np
from dataclasses import dataclass
from typing import Tuple, List, Dict

@dataclass
class RunMetrics:
    avg_power: float
    avg_hr: float
    distance_meters: float
    duration_seconds: int
    ascent_meters: float
    weight_kg: float
    hr_max: int
    hr_rest: int
    temp_c: float
    humidity: float

class ScoreEngine:
    W_REF_SPEC = 6.0        
    ALPHA = 0.8             
    WR_BASE_DIST = 42195.0
    WR_BASE_TIME = 7235.0   
    RIEGEL_EXP = 1.06

    @staticmethod
    def get_world_record_time(distance_meters: float) -> float:
        if distance_meters <= 0: return 1.0
        return ScoreEngine.WR_BASE_TIME * (distance_meters / ScoreEngine.WR_BASE_DIST) ** ScoreEngine.RIEGEL_EXP

    @staticmethod
    def calculate_decoupling(power_stream: list, hr_stream: list) -> float:
        if not power_stream or not hr_stream or len(power_stream) != len(hr_stream): return 0.0
        half = len(power_stream) // 2
        if half < 60: return 0.0
        p1, h1 = np.mean(power_stream[:half]), np.mean(hr_stream[:half])
        p2, h2 = np.mean(power_stream[half:]), np.mean(hr_stream[half:])
        if h1 == 0 or h2 == 0: return 0.0
        return (p1/h1 - p2/h2) / (p1/h1)

    @staticmethod
    def calculate_zones(watts_stream: list, ftp: int) -> List[Dict]:
        if not watts_stream or ftp <= 0: return []
        zones_def = [
            {"name": "Z1 Recupero", "limit": 0.55 * ftp, "color": "#bdc3c7"},
            {"name": "Z2 Fondo Lento", "limit": 0.75 * ftp, "color": "#3498db"},
            {"name": "Z3 Tempo", "limit": 0.90 * ftp, "color": "#2ecc71"},
            {"name": "Z4 Soglia", "limit": 1.05 * ftp, "color": "#f1c40f"},
            {"name": "Z5 VO2Max", "limit": 1.20 * ftp, "color": "#e67e22"},
            {"name": "Z6 Anaerobico", "limit": 9999, "color": "#e74c3c"}
        ]
        counts = [0] * len(zones_def)
        total = len(watts_stream)
        for w in watts_stream:
            for i, z in enumerate(zones_def):
                if w <= z["limit"]:
                    counts[i] += 1
                    break
        result = []
        for i, z in enumerate(zones_def):
            pct = (counts[i] / total) * 100
            if pct > 0.1:
                result.append({"Zone": z["name"], "Percent": pct, "Color": z["color"], "Minutes": round(counts[i]/60, 1)})
        return result

    def compute_score(self, metrics: RunMetrics, decoupling: float) -> Tuple[float, float, float]:
        grade = metrics.ascent_meters / metrics.distance_meters if metrics.distance_meters > 0 else 0
        w_adj = metrics.avg_power * (1 + grade)
        w_spec = w_adj / metrics.weight_kg
        term_eff = (w_spec / self.W_REF_SPEC)
        hrr_pct = max(0.05, (metrics.avg_hr - metrics.hr_rest) / (metrics.hr_max - metrics.hr_rest))
        term_hrr = 1 / hrr_pct
        term_wcf = 1.0 + max(0, 0.012 * (metrics.temp_c - 20)) + max(0, 0.005 * (metrics.humidity - 60))
        t_wr = self.get_world_record_time(metrics.distance_meters)
        term_p = t_wr / max(1, metrics.duration_seconds)
        t_hours = metrics.duration_seconds / 3600.0
        term_stab = np.exp(-self.ALPHA * abs(decoupling) / np.sqrt(max(0.1, t_hours)))
        
        score = (term_eff * term_hrr * term_wcf) * term_p * term_stab
        return score, term_wcf, term_p * 100

    @staticmethod
    def get_rank(score: float) -> Tuple[str, str]:
        if score >= 4.0: return "🏆 Classe Mondiale", "success"
        if score >= 3.0: return "🥇 Livello Nazionale", "success"
        if score >= 2.0: return "🥈 Livello Regionale", "warning"
        if score >= 1.0: return "🥉 Runner Avanzato", "info"
        return "👟 Amatore / Recupero", "secondary"
