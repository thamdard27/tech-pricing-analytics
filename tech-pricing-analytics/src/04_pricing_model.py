"""
04_pricing_model.py  -  Predictive pricing model, price-driver ranking,
market segmentation, and automated plain-language insight generation.

Outputs:
  * model performance (R2, MAE, RMSE) on a held-out test set
  * ranked price drivers (permutation importance) -> figure + table
  * interpretable log-linear elasticities (how each spec moves price, in %)
  * three-tier market segmentation with profile of each tier
  * auto-generated business insights (reports/findings_auto.md)

The "insight generator" is a transparent, rule-based natural-language layer that
turns the model's real numeric outputs into readable sentences for business
users. It does not invent numbers; every sentence is templated from a computed
value. (An optional LLM rewriting step is described in the README.)
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.inspection import permutation_importance
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.cluster import KMeans

BASE = Path(__file__).resolve().parents[1]
CLEAN = BASE / "data" / "processed" / "laptop_pricing_clean.csv"
FIG = BASE / "reports" / "figures"
FINDINGS = BASE / "reports" / "findings_auto.md"
RANDOM_STATE = 42

NUMERIC = ["screen_in", "ram_gb", "weight_kg", "storage_total_gb", "ssd_gb",
           "ppi", "cpu_ghz", "is_touch", "is_ips", "has_ssd"]
CATEG = ["brand", "form_factor", "cpu_brand", "cpu_tier", "gpu_brand", "os_group"]


def build_model():
    pre = ColumnTransformer([
        ("num", StandardScaler(), NUMERIC),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEG),
    ])
    model = Pipeline([
        ("pre", pre),
        ("gbr", GradientBoostingRegressor(random_state=RANDOM_STATE, n_estimators=400, max_depth=3, learning_rate=0.05)),
    ])
    return model


def main():
    df = pd.read_csv(CLEAN).dropna(subset=["cpu_ghz"])  # drop few rows missing GHz
    X = df[NUMERIC + CATEG]
    y = np.log1p(df["price_usd"])  # model log price for multiplicative behavior

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=RANDOM_STATE)
    model = build_model().fit(Xtr, ytr)

    pred_log = model.predict(Xte)
    pred = np.expm1(pred_log)
    true = np.expm1(yte)
    r2 = r2_score(true, pred)
    mae = mean_absolute_error(true, pred)
    rmse = mean_squared_error(true, pred) ** 0.5
    mape = float(np.mean(np.abs((true - pred) / true)) * 100)
    print(f"[model] GradientBoosting  R2={r2:.3f}  MAE=${mae:,.0f}  RMSE=${rmse:,.0f}  MAPE={mape:.1f}%")

    # ---- driver ranking via permutation importance (real) ----
    perm = permutation_importance(model, Xte, yte, n_repeats=15, random_state=RANDOM_STATE)
    importances = pd.Series(perm.importances_mean, index=NUMERIC + CATEG).sort_values(ascending=False)
    print("\n[model] top price drivers (permutation importance):")
    print(importances.head(8).round(4).to_string())

    plt.figure(figsize=(8, 6))
    importances.head(10)[::-1].plot.barh(color="#1f4e79")
    plt.title("Top price drivers (permutation importance)")
    plt.xlabel("Mean increase in error when shuffled")
    plt.tight_layout(); plt.savefig(FIG / "06_price_drivers.png", dpi=120); plt.close()

    # ---- interpretable elasticities via log-linear regression on key numerics ----
    lin_feats = ["ram_gb", "ssd_gb", "ppi", "cpu_ghz", "weight_kg"]
    lin = Pipeline([("sc", StandardScaler()), ("lr", LinearRegression())]).fit(df[lin_feats], np.log(df["price_usd"]))
    # convert standardized coefs back to "per natural unit" approx % effect
    coefs = lin.named_steps["lr"].coef_
    sds = df[lin_feats].std().values
    pct_per_unit = (np.exp(coefs / sds) - 1) * 100
    elasticity = pd.Series(pct_per_unit, index=lin_feats).sort_values(ascending=False)
    print("\n[model] approx % change in price per +1 natural unit (log-linear):")
    print(elasticity.round(2).to_string())

    # ---- segmentation: 3 market tiers ----
    seg_feats = ["price_usd", "ram_gb", "ppi", "cpu_ghz", "storage_total_gb"]
    km = KMeans(n_clusters=3, n_init=10, random_state=RANDOM_STATE).fit(StandardScaler().fit_transform(df[seg_feats]))
    df["segment"] = km.labels_
    seg_profile = df.groupby("segment").agg(
        n=("price_usd", "size"),
        median_price=("price_usd", "median"),
        avg_ram=("ram_gb", "mean"),
        avg_ppi=("ppi", "mean"),
        ssd_share=("has_ssd", "mean"),
    ).round(1).sort_values("median_price")
    # name tiers by price order
    names = ["Budget", "Mainstream", "Premium"]
    seg_profile["tier"] = names
    print("\n[model] market segments (sorted by price):")
    print(seg_profile.to_string())

    # ---- automated, rule-based business insights (real numbers only) ----
    top3 = list(importances.head(3).index)
    ssd_med = df.groupby("has_ssd")["price_usd"].median()
    lines = []
    lines.append("# Auto-generated pricing insights\n")
    lines.append(f"- The pricing model explains **{r2*100:.0f}%** of price variation on unseen laptops "
                 f"(R2={r2:.2f}), with a typical error of about **{mape:.0f}%** (MAE ${mae:,.0f}).")
    lines.append(f"- The three strongest price drivers are **{top3[0]}, {top3[1]}, and {top3[2]}**.")
    lines.append(f"- Each additional GB of RAM is associated with roughly **{elasticity['ram_gb']:.1f}%** higher price, "
                 f"holding the other measured specs constant.")
    lines.append(f"- Laptops with an SSD carry a median price of **${ssd_med[1]:,.0f}** versus "
                 f"**${ssd_med[0]:,.0f}** without one, a **{100*(ssd_med[1]/ssd_med[0]-1):.0f}%** premium.")
    lines.append(f"- The market splits into three clear tiers: Budget (median ${seg_profile['median_price'].iloc[0]:,.0f}), "
                 f"Mainstream (${seg_profile['median_price'].iloc[1]:,.0f}), and "
                 f"Premium (${seg_profile['median_price'].iloc[2]:,.0f}).")
    lines.append("\n*All figures above are computed directly from the model and the cleaned dataset; "
                 "no values are hand-entered.*")
    FINDINGS.write_text("\n".join(lines))
    print(f"\n[model] auto-insights written to {FINDINGS}")

    # persist metrics for the README/report
    (BASE / "reports" / "metrics.txt").write_text(
        f"R2={r2:.3f}\nMAE_usd={mae:.1f}\nRMSE_usd={rmse:.1f}\nMAPE_pct={mape:.2f}\n"
        f"top_drivers={top3}\n"
    )


if __name__ == "__main__":
    main()
