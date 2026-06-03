# Data: provenance, licensing, and dictionary

## Source (verifiable)

This project uses the **Laptop Price** dataset, a real, publicly available
dataset of 1,303 laptop configurations and their retail prices.

- **Original author:** Muhammet Varli, "Laptop Price" (published on Kaggle).
- **Copy used here:** mirrored on GitHub and retrieved programmatically by
  `src/01_ingest.py` from:
  `https://raw.githubusercontent.com/campusx-official/laptop-price-predictor-regression-project/main/laptop_data.csv`
- **Retrieved:** see the SHA-256 hash printed by the ingest step for the exact
  bytes used (stored copy: `data/raw/laptop_pricing_raw.csv`).
- **Rows:** 1,303  **Columns (raw):** 11  **Missing values:** none.

The dataset is widely used for educational pricing/regression work and is
redistributed here for non-commercial, portfolio purposes with attribution to
the original author. If you reuse it, credit the original source.

## Currency note

Prices in the raw file are in **Indian Rupees (INR)**. The cleaning step adds a
`price_usd` column using a fixed, documented conversion rate of
**83.0 INR = 1 USD** (an approximate 2024-2025 rate, used only to present a
globally readable figure). The native `price_inr` column is retained so no
information is lost.

## Cleaned data dictionary (`data/processed/laptop_pricing_clean.csv`)

| Column             | Type    | Description                                              | Derived from |
|--------------------|---------|----------------------------------------------------------|--------------|
| brand              | string  | Manufacturer (e.g., Dell, HP, Apple)                     | Company |
| form_factor        | string  | Notebook, Ultrabook, Gaming, Workstation, etc.           | TypeName |
| screen_in          | float   | Screen size in inches                                    | Inches |
| ram_gb             | float   | RAM in GB                                                | Ram ("8GB"->8) |
| weight_kg          | float   | Weight in kg                                             | Weight ("1.37kg"->1.37) |
| ssd_gb             | float   | SSD capacity in GB                                       | Memory parse |
| hdd_gb             | float   | HDD capacity in GB                                       | Memory parse |
| storage_total_gb   | float   | Total storage in GB (TB converted at 1TB=1000GB)         | Memory parse |
| has_ssd            | int     | 1 if any SSD present, else 0                             | Memory parse |
| res_w, res_h       | int     | Screen resolution width/height in pixels                 | ScreenResolution |
| ppi                | float   | Pixels per inch = sqrt(w^2+h^2)/screen_in                | derived |
| is_touch           | int     | 1 if touchscreen                                         | ScreenResolution |
| is_ips             | int     | 1 if IPS panel                                           | ScreenResolution |
| is_retina          | int     | 1 if Retina display                                      | ScreenResolution |
| cpu_brand          | string  | Intel / AMD / Other                                      | Cpu |
| cpu_tier           | string  | Core i7/i5/i3, Ryzen, Celeron, etc.                      | Cpu |
| cpu_ghz            | float   | Base clock in GHz                                        | Cpu |
| gpu_brand          | string  | Intel / Nvidia / AMD / Other                             | Gpu |
| os_group           | string  | Windows / macOS / Linux-Other / No OS                    | OpSys |
| price_inr          | float   | Price in Indian Rupees (original)                        | Price |
| price_usd          | float   | Price in USD at 83 INR/USD                               | derived |
