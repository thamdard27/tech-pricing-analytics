"""
05_export_model.py  -  Train a transparent, fully interpretable linear pricing
model and export its coefficients in a plain text format that a standalone C++
program (src/score_price.cpp) can read and use to score new laptops.

Why a second, simpler model here?
  The gradient-boosted model in 04 is accurate but a "black box" to a C++
  re-implementation. For a fast, dependency-free production scorer we train a
  LINEAR model on log(price) using natural-unit numeric features, so its
  coefficients can be applied with nothing more than multiply-add-exp. This is a
  common real pattern: train/experiment in Python, deploy a tiny fast scorer in
  C++ that any service can call.

Outputs:
  models/price_model_coeffs.txt   intercept + one coefficient per feature
  models/sample_config.txt        a sample laptop + Python's predicted price,
                                  used to verify the C++ scorer agrees.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

BASE = Path(__file__).resolve().parents[1]
CLEAN = BASE / "data" / "processed" / "laptop_pricing_clean.csv"
MODELS = BASE / "models"

# natural-unit numeric features (no scaling, so coefs are directly usable in C++)
FEATURES = ["ram_gb", "ssd_gb", "ppi", "cpu_ghz", "weight_kg", "screen_in", "has_ssd"]


def main():
    MODELS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(CLEAN).dropna(subset=["cpu_ghz"])
    X = df[FEATURES].values
    y = np.log(df["price_usd"].values)  # model log price

    lr = LinearRegression().fit(X, y)

    # export coefficients: "intercept <value>" then "<feature> <coef>" per line
    lines = [f"intercept {lr.intercept_:.10f}"]
    for f, c in zip(FEATURES, lr.coef_):
        lines.append(f"{f} {c:.10f}")
    (MODELS / "price_model_coeffs.txt").write_text("\n".join(lines) + "\n")

    # a sample config to verify the C++ scorer matches Python exactly
    sample = {"ram_gb": 16, "ssd_gb": 512, "ppi": 157.0, "cpu_ghz": 2.8,
              "weight_kg": 1.6, "screen_in": 15.6, "has_ssd": 1}
    xs = np.array([[sample[f] for f in FEATURES]])
    py_pred = float(np.exp(lr.predict(xs))[0])

    cfg_lines = [f"{f} {sample[f]}" for f in FEATURES] + [f"python_predicted_usd {py_pred:.4f}"]
    (MODELS / "sample_config.txt").write_text("\n".join(cfg_lines) + "\n")

    print(f"[export] wrote coefficients for {len(FEATURES)} features -> models/price_model_coeffs.txt")
    print(f"[export] Python predicted price for sample config: ${py_pred:,.2f}")
    print("[export] (the C++ scorer should reproduce this number)")


if __name__ == "__main__":
    main()
