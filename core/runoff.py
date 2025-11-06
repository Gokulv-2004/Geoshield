# core/runoff.py
# SCS Curve Number → quick runoff + peak inflow estimate
def scs_runoff_mm(P_mm: float, CN: float) -> float:
    if P_mm <= 0 or CN <= 0: return 0.0
    S = (25400.0 / CN) - 254.0  # mm
    Ia = 0.2 * S
    if P_mm <= Ia: return 0.0
    Q = ((P_mm - Ia) ** 2) / (P_mm - Ia + S)
    return max(0.0, Q)

def runoff_volume_m3(runoff_mm: float, area_km2: float) -> float:
    if runoff_mm <= 0 or area_km2 <= 0: return 0.0
    area_m2 = area_km2 * 1_000_000.0
    depth_m = runoff_mm / 1000.0
    return area_m2 * depth_m

def estimate_peak_inflow_cumecs(volume_m3: float, storm_hours: float = 6.0) -> float:
    if volume_m3 <= 0 or storm_hours <= 0: return 0.0
    return volume_m3 / (storm_hours * 3600.0)
