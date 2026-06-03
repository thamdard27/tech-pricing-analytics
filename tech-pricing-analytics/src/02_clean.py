"""
02_clean.py  -  Cleaning and feature engineering layer.

Transforms the raw, human-readable specification strings (e.g. "8GB",
"256GB SSD + 1TB HDD", "IPS Panel Full HD 1920x1080") into clean, typed,
analysis-ready features, and writes a curated table to data/processed/.

Every transformation is documented so a reviewer can trace each engineered
column back to its raw source (data lineage). Quality checks run at the end and
fail loudly if an expectation is violated.
"""
from pathlib import Path
import re
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
RAW_PATH = BASE / "data" / "raw" / "laptop_pricing_raw.csv"
OUT_PATH = BASE / "data" / "processed" / "laptop_pricing_clean.csv"


def _ram_to_gb(s: str) -> float:
    return float(re.sub(r"[^0-9.]", "", s))


def _weight_to_kg(s: str) -> float:
    m = re.sub(r"[^0-9.]", "", str(s))
    return float(m) if m else np.nan


def _parse_memory(s: str):
    """Return (ssd_gb, hdd_gb, flash_gb, hybrid_gb, total_gb)."""
    s = s.replace("Storage", "").strip()
    ssd = hdd = flash = hybrid = 0.0
    for part in s.split("+"):
        part = part.strip()
        if not part:
            continue
        num = re.findall(r"[\d.]+", part)
        if not num:
            continue
        size = float(num[0])
        if "TB" in part:
            size *= 1000  # 1 TB = 1000 GB (decimal, marketing convention)
        if "SSD" in part:
            ssd += size
        elif "HDD" in part:
            hdd += size
        elif "Flash" in part:
            flash += size
        elif "Hybrid" in part:
            hybrid += size
        else:
            ssd += size  # default unknown to ssd
    total = ssd + hdd + flash + hybrid
    return ssd, hdd, flash, hybrid, total


def _parse_resolution(s: str):
    """Return (width_px, height_px, is_touch, is_ips, is_retina)."""
    is_touch = int("Touchscreen" in s)
    is_ips = int("IPS" in s)
    is_retina = int("Retina" in s)
    m = re.search(r"(\d{3,4})x(\d{3,4})", s)
    w, h = (int(m.group(1)), int(m.group(2))) if m else (np.nan, np.nan)
    return w, h, is_touch, is_ips, is_retina


def _cpu_brand(s: str) -> str:
    if s.startswith("Intel"):
        return "Intel"
    if s.startswith("AMD"):
        return "AMD"
    return "Other"


def _cpu_tier(s: str) -> str:
    for tier in ["Core i7", "Core i5", "Core i3", "Ryzen", "Celeron", "Pentium", "Xeon", "Atom"]:
        if tier in s:
            return tier
    return "Other"


def _cpu_ghz(s: str) -> float:
    m = re.search(r"([\d.]+)GHz", s)
    return float(m.group(1)) if m else np.nan


def _gpu_brand(s: str) -> str:
    for b in ["Intel", "Nvidia", "AMD"]:
        if b in s:
            return b
    return "Other"


def _os_group(s: str) -> str:
    if "Windows" in s:
        return "Windows"
    if "mac" in s or "Mac" in s:
        return "macOS"
    if s in ("No OS", "No Os"):
        return "No OS"
    return "Linux/Other"


def clean() -> pd.DataFrame:
    df = pd.read_csv(RAW_PATH, index_col=0).reset_index(drop=True)
    n0 = len(df)

    df["ram_gb"] = df["Ram"].map(_ram_to_gb)
    df["weight_kg"] = df["Weight"].map(_weight_to_kg)

    mem = df["Memory"].map(_parse_memory)
    df["ssd_gb"] = [m[0] for m in mem]
    df["hdd_gb"] = [m[1] for m in mem]
    df["storage_total_gb"] = [m[4] for m in mem]
    df["has_ssd"] = (df["ssd_gb"] > 0).astype(int)

    res = df["ScreenResolution"].map(_parse_resolution)
    df["res_w"] = [r[0] for r in res]
    df["res_h"] = [r[1] for r in res]
    df["is_touch"] = [r[2] for r in res]
    df["is_ips"] = [r[3] for r in res]
    df["is_retina"] = [r[4] for r in res]
    # pixels-per-inch: a clean proxy for display quality
    df["ppi"] = np.sqrt(df["res_w"] ** 2 + df["res_h"] ** 2) / df["Inches"]

    df["cpu_brand"] = df["Cpu"].map(_cpu_brand)
    df["cpu_tier"] = df["Cpu"].map(_cpu_tier)
    df["cpu_ghz"] = df["Cpu"].map(_cpu_ghz)
    df["gpu_brand"] = df["Gpu"].map(_gpu_brand)
    df["os_group"] = df["OpSys"].map(_os_group)

    # Convert price from INR to USD for a globally readable figure (cited rate).
    # Rate documented in data/README.md; stored alongside native INR.
    INR_PER_USD = 83.0
    df["price_inr"] = df["Price"]
    df["price_usd"] = (df["Price"] / INR_PER_USD).round(2)

    keep = [
        "Company", "TypeName", "Inches", "ram_gb", "weight_kg",
        "ssd_gb", "hdd_gb", "storage_total_gb", "has_ssd",
        "res_w", "res_h", "ppi", "is_touch", "is_ips", "is_retina",
        "cpu_brand", "cpu_tier", "cpu_ghz", "gpu_brand", "os_group",
        "price_inr", "price_usd",
    ]
    clean_df = df[keep].rename(columns={"Company": "brand", "TypeName": "form_factor", "Inches": "screen_in"})

    # ---- data-quality gates (fail loudly) ----
    assert len(clean_df) == n0, "row count changed during cleaning"
    assert clean_df["price_usd"].gt(0).all(), "non-positive prices found"
    assert clean_df["ram_gb"].between(1, 128).all(), "implausible RAM values"
    assert clean_df["ppi"].notna().all(), "missing PPI after parse"
    assert clean_df.isna().sum().sum() <= clean_df["cpu_ghz"].isna().sum(), "unexpected nulls"

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    clean_df.to_csv(OUT_PATH, index=False)
    print(f"[clean] {n0} rows in -> {len(clean_df)} rows out | {clean_df.shape[1]} cols")
    print(f"[clean] wrote {OUT_PATH}")
    return clean_df


if __name__ == "__main__":
    clean()
