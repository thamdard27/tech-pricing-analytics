"""
03_eda_trends.py  -  Exploratory analysis, pricing-trend detection, and
business-facing visualizations.

Produces the charts in reports/figures/ and prints the trend tables that feed
the written findings (reports/findings.md). All figures are generated from the
cleaned table only.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

BASE = Path(__file__).resolve().parents[1]
CLEAN = BASE / "data" / "processed" / "laptop_pricing_clean.csv"
FIG = BASE / "reports" / "figures"
sns.set_theme(style="whitegrid")


def main():
    df = pd.read_csv(CLEAN)
    FIG.mkdir(parents=True, exist_ok=True)

    # 1. Price distribution
    plt.figure(figsize=(8, 5))
    sns.histplot(df["price_usd"], bins=40, kde=True, color="#1f4e79")
    plt.title("Distribution of laptop price (USD)")
    plt.xlabel("Price (USD)"); plt.ylabel("Count")
    plt.tight_layout(); plt.savefig(FIG / "01_price_distribution.png", dpi=120); plt.close()

    # 2. Median price by brand
    by_brand = df.groupby("brand")["price_usd"].agg(["median", "count"]).query("count >= 10").sort_values("median")
    plt.figure(figsize=(9, 6))
    sns.barplot(x=by_brand["median"], y=by_brand.index, color="#1f4e79")
    plt.title("Median price by brand (brands with >=10 models)")
    plt.xlabel("Median price (USD)"); plt.ylabel("")
    plt.tight_layout(); plt.savefig(FIG / "02_price_by_brand.png", dpi=120); plt.close()

    # 3. Price by form factor
    order = df.groupby("form_factor")["price_usd"].median().sort_values().index
    plt.figure(figsize=(9, 5))
    sns.boxplot(data=df, x="form_factor", y="price_usd", order=order, color="#9dc3e6")
    plt.title("Price by form factor")
    plt.xlabel(""); plt.ylabel("Price (USD)"); plt.xticks(rotation=20)
    plt.tight_layout(); plt.savefig(FIG / "03_price_by_form_factor.png", dpi=120); plt.close()

    # 4. RAM vs price (premium driver)
    plt.figure(figsize=(8, 5))
    sns.boxplot(data=df[df["ram_gb"].isin([4, 8, 16, 32])], x="ram_gb", y="price_usd", color="#9dc3e6")
    plt.title("Price by RAM (GB)")
    plt.xlabel("RAM (GB)"); plt.ylabel("Price (USD)")
    plt.tight_layout(); plt.savefig(FIG / "04_price_by_ram.png", dpi=120); plt.close()

    # 5. Correlation heatmap (numeric drivers)
    num = ["price_usd", "ram_gb", "ppi", "cpu_ghz", "storage_total_gb", "ssd_gb", "weight_kg", "screen_in"]
    plt.figure(figsize=(8, 6))
    sns.heatmap(df[num].corr(), annot=True, fmt=".2f", cmap="Blues")
    plt.title("Correlation of numeric specs with price")
    plt.tight_layout(); plt.savefig(FIG / "05_correlation.png", dpi=120); plt.close()

    # ---- trend tables (printed; consumed by findings.md) ----
    print("\n=== Median price by brand (>=10 models) ===")
    print(by_brand.sort_values("median", ascending=False).round(0).to_string())

    print("\n=== Median price by form factor ===")
    print(df.groupby("form_factor")["price_usd"].median().sort_values(ascending=False).round(0).to_string())

    print("\n=== SSD premium ===")
    ssd_prem = df.groupby("has_ssd")["price_usd"].median()
    print(ssd_prem.round(0).to_string())
    print(f"SSD median uplift: {ssd_prem[1] - ssd_prem[0]:.0f} USD "
          f"({100*(ssd_prem[1]/ssd_prem[0]-1):.0f}%)")

    print("\n=== Correlation with price (sorted) ===")
    corr = df[num].corr()["price_usd"].drop("price_usd").sort_values(ascending=False)
    print(corr.round(3).to_string())

    print(f"\n[eda] figures written to {FIG}")


if __name__ == "__main__":
    main()
