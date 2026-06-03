# Findings: what drives technology product pricing

*All figures below are produced by the code in this repository from the real
dataset described in `data/README.md`. Re-running `python run_pipeline.py`
regenerates them. Numbers were last refreshed from a clean run of the pipeline.*

## Headline results

- A gradient-boosted pricing model explains **about 77% of price variation**
  (R² = 0.77) on a held-out 20% test set, with a **typical error near 15-16%**
  (MAE ≈ $116, RMSE ≈ $221 on a median price of ~$627).
- The **strongest price drivers**, ranked by permutation importance, are
  **RAM, CPU clock speed, and CPU tier**, followed by SSD capacity and display
  sharpness (PPI).
- **Storage type is a large, clean pricing lever:** laptops with an SSD have a
  **median price of $810 vs $360** without one, a **~125% premium**.
- The market separates cleanly into **three tiers**: Budget (median ~$320),
  Mainstream (~$617), and Premium (~$1,268), differing most in RAM, display
  sharpness, and SSD adoption.

## Segment profiles

| Tier        | Count | Median price | Avg RAM | Avg PPI | SSD share |
|-------------|------:|-------------:|--------:|--------:|----------:|
| Budget      |   381 |        ~$320 |    ~5.7 |   ~135  |      ~40% |
| Mainstream  |   674 |        ~$617 |    ~7.0 |   ~140  |      ~70% |
| Premium     |   248 |       ~$1,268|   ~16.3 |   ~182  |     ~100% |

## How a business user could act on this

- **Configuration pricing:** because RAM, CPU, and SSD dominate price, these
  are the levers to model first when setting or benchmarking a product's price.
- **Positioning:** the SSD premium and the sharp tier boundaries show where a
  product sits relative to the market and where a spec change would move it
  across a tier line.
- **Anomaly detection:** the model's per-unit prediction can flag listings
  priced far from what their specs predict (candidates for repricing or review).

## Honesty notes / limitations

- This is a **cross-sectional** dataset (a snapshot), so it shows pricing
  *structure*, not pricing *trends over time*; a time-stamped feed would be
  needed for temporal trend analysis.
- Prices were converted INR→USD at a fixed documented rate for readability.
- Brand effects partly capture unobserved quality/brand-premium factors, not
  just hardware.

These limitations are stated deliberately: knowing what a model *cannot* say is
part of using it responsibly.
