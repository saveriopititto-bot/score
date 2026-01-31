
class RunMetrics:
    def __init__(self, avg_power, avg_hr, weight):
        self.avg_power = avg_power
        self.avg_hr = avg_hr
        self.weight = weight

def compute_score(m):
    try:
        # 1. Power
        print("Accessing avg_power...")
        w_kg = m.avg_power / m.weight
        
        # 2. HR
        print("Accessing avg_hr...")
        hr = m.avg_hr
        
        print("Success")
    except Exception as e:
        print(f"Caught error: {e}")

print("--- Test 1: Valid Object ---")
r = RunMetrics(100, 150, 70)
compute_score(r)

print("\n--- Test 2: Integer passed as m ---")
compute_score(123)
