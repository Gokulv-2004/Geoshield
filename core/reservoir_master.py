# core/reservoir_master.py
import os
import pandas as pd
from functools import lru_cache

MASTER_CSV = os.path.join(os.path.dirname(__file__), "data", "dam_master.csv")

def _norm(s: str) -> str:
    return str(s).strip().lower()

@lru_cache(maxsize=1)
def load_master() -> pd.DataFrame:
    cols = [
        "reservoir_name","alias","wris_project_name","state","district",
        "lat","lon","capacity_tmc","catchment_km2","design_spill_cumecs","curve_number"
    ]
    if not os.path.exists(MASTER_CSV):
        # empty but with schema keeps app alive
        return pd.DataFrame(columns=cols)
    df = pd.read_csv(MASTER_CSV)
    df.columns = [c.strip().lower() for c in df.columns]
    for col in ["reservoir_name","alias","wris_project_name","state","district"]:
        if col in df.columns:
            df[col] = df[col].astype(str).map(_norm)
    return df

def list_reservoirs() -> list[str]:
    df = load_master()
    if df.empty or "reservoir_name" not in df.columns:
        return ["Almatti","Tungabhadra"]
    vals = sorted(set(df["reservoir_name"].dropna().astype(str).tolist()))
    return vals if vals else ["Almatti","Tungabhadra"]

def _find_row(df: pd.DataFrame, key: str):
    for col in ["reservoir_name","alias","wris_project_name"]:
        if col in df.columns:
            hit = df.loc[df[col] == key]
            if not hit.empty:
                return hit.iloc[0]
    for col in ["reservoir_name","alias","wris_project_name"]:
        if col in df.columns:
            hit = df[df[col].str.contains(key, na=False)]
            if not hit.empty:
                return hit.iloc[0]
    return None

def find_row(station: str) -> dict | None:
    df = load_master()
    if df.empty: return None
    key = _norm(station)
    r = _find_row(df, key)
    return r.to_dict() if r is not None else None

def _num(row, k, default=None, t=float):
    try:
        v = row.get(k, None) if row else None
        return t(v) if v not in (None,"") else default
    except Exception:
        return default

def get_latlon(station: str):
    row = find_row(station)
    lat = _num(row, "lat")
    lon = _num(row, "lon")
    return (lat, lon) if (lat is not None and lon is not None) else None

def get_capacity_tmc(station: str):
    return _num(find_row(station), "capacity_tmc")

def get_catchment_km2(station: str):
    return _num(find_row(station), "catchment_km2")

def get_design_spill_cumecs(station: str):
    return _num(find_row(station), "design_spill_cumecs")

def get_curve_number(station: str):
    cn = _num(find_row(station), "curve_number", default=78, t=float)
    if cn is None: return 78
    return int(max(30, min(98, cn)))
