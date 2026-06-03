"""
06_price_scenarios.py  -  Forward (time-based) pricing scenarios.

IMPORTANT HONESTY NOTE
----------------------
The source dataset is a CROSS-SECTIONAL snapshot: it has no dates, so it cannot
show how prices actually moved over time. This module does NOT pretend it does.
Instead it builds a transparent *scenario / what-if projection*: given a laptop's
modeled current price, it projects future value under an EXPLICIT, stated
depreciation assumption. This is a standard, legitimate pricing-analytics
technique (forward pricing under assumptions), and it is clearly labelled as
assumption-driven, not observed history.

What it does:
  * picks one representative laptop from each market tier (Budget/Mainstream/
    Premium) using the cleaned data,
  * projects each one's value over 0-4 years at a documented annual
    depreciation rate, plus a sensitivity band (low/base/high rates),
  * writes a chart (reports/figures/07_price_scenarios.png) and a table.

Run:  python src/06_price_scenarios.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parents[1]
CLEAN = BASE / "data" / "processed" / "laptop_pricing_clean.csv"
FIG = BASE / "reports" / "figures"

# --- documented assumptions (the inputs a pricing analyst would set & defend) ---
BASE_DEPRECIATION = 0.20   # 20% value lost per year (base case)
LOW_DEPRECIATION = 0.12    # gentle case
HIGH_DEPRECIATION = 0.28   # aggressive case
YEARS = np.arange(0, 5)     # 0..4 years


def representative_configs(df: pd.DataFrame) -> pd.DataFrame:
    """Pick a typical laptop in each price tier by nearest-to-median price."""
    df = df.copy()
    q = df["price_usd"].quantile([0.33, 0.66]).values
    df["tier"] = np.where(df["price_usd"] <= q[0], "Budget",
                  np.where(df["price_usd"] <= q[1], "Mainstream", "Premium"))
    reps = []
    for tier, g in df.groupby("tier"):
        med = g["price_usd"].median()
        row = g.iloc[(g["price_usd"] - med).abs().argsort().iloc[0]]
        reps.append({"tier": tier, "brand": row["brand"],
                     "form_factor": row["form_factor"],
                     "price_usd": float(row["price_usd"])})
    order = {"Budget": 0, "Mainstream": 1, "Premium": 2}
    return pd.DataFrame(reps).sort_values("tier", key=lambda s: s.map(order)).reset_index(drop=True)


def project(start_price: float, rate: float, years=YEARS) -> np.ndarray:
    """Geometric depreciation: value(t) = start * (1 - rate)^t."""
    return start_price * (1 - rate) ** years


def main():
    df = pd.read_csv(CLEAN)
    reps = representative_configs(df)

    # build the base-case projection table
    rows = []
    for _, r in reps.iterrows():
        vals = project(r["price_usd"], BASE_DEPRECIATION)
        for t, v in zip(YEARS, vals):
            rows.append({"tier": r["tier"], "year": int(t), "value_usd": round(float(v), 2)})
    table = pd.DataFrame(rows)

    print("=== Forward value projection (base case: "
          f"{int(BASE_DEPRECIATION*100)}%/yr depreciation) ===")
    print(table.pivot(index="tier", columns="year", values="value_usd")
              .reindex(["Budget", "Mainstream", "Premium"]).round(0).to_string())
    print("\n(Assumption-driven scenario, not observed historical prices.)")

    # chart: base-case lines per tier, with a sensitivity band on the Premium tier
    plt.figure(figsize=(9, 5.5))
    colors = {"Budget": "#9dc3e6", "Mainstream": "#2e75b6", "Premium": "#1f4e79"}
    for _, r in reps.iterrows():
        plt.plot(YEARS, project(r["price_usd"], BASE_DEPRECIATION),
                 marker="o", color=colors[r["tier"]],
                 label=f"{r['tier']} (start ${r['price_usd']:,.0f})")
    # sensitivity band on Premium
    prem = reps[reps["tier"] == "Premium"]["price_usd"].iloc[0]
    plt.fill_between(YEARS, project(prem, HIGH_DEPRECIATION),
                     project(prem, LOW_DEPRECIATION), color="#1f4e79", alpha=0.12,
                     label=f"Premium sensitivity ({int(LOW_DEPRECIATION*100)}-{int(HIGH_DEPRECIATION*100)}%/yr)")
    plt.title("Forward value scenario by tier (assumption-driven, not observed)")
    plt.xlabel("Years from purchase"); plt.ylabel("Projected value (USD)")
    plt.xticks(YEARS); plt.legend(fontsize=8)
    plt.tight_layout(); plt.savefig(FIG / "07_price_scenarios.png", dpi=120); plt.close()
    print(f"\n[scenarios] chart written to {FIG / '07_price_scenarios.png'}")


if __name__ == "__main__":
    main()
