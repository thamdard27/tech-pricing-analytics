#!/usr/bin/env Rscript
# validate_findings.R
# -------------------------------------------------------------------
# Independent cross-validation of the Python pricing findings, in R.
# Confirms (a) the direction and significance of the main price drivers
# via a log-linear model, and (b) that form factor explains a significant
# share of price variation via one-way ANOVA.
#
# Run from the project root:
#   Rscript analysis/validate_findings.R
# Requires base R only (no extra packages).
# -------------------------------------------------------------------

df <- read.csv("data/processed/laptop_pricing_clean.csv", stringsAsFactors = TRUE)

cat("Rows:", nrow(df), " Cols:", ncol(df), "\n\n")

# --- Log-linear regression: do the same drivers matter, with the same sign? ---
df$log_price <- log(df$price_usd)
fit <- lm(log_price ~ ram_gb + ssd_gb + ppi + cpu_ghz + weight_kg +
            form_factor + brand, data = df)

cat("=== Log-linear regression (selected coefficients) ===\n")
co <- summary(fit)$coefficients
keep <- c("ram_gb", "ssd_gb", "ppi", "cpu_ghz", "weight_kg")
print(round(co[keep, c("Estimate", "Pr(>|t|)")], 5))
cat("\nAdjusted R-squared:", round(summary(fit)$adj.r.squared, 3), "\n\n")

# --- ANOVA: is price significantly different across form factors? ---
cat("=== One-way ANOVA: price ~ form_factor ===\n")
print(summary(aov(price_usd ~ form_factor, data = df)))

# --- Median price by tier-defining spec (sanity check vs Python) ---
cat("\n=== Median USD price by RAM bucket ===\n")
df$ram_bucket <- cut(df$ram_gb, c(0, 4, 8, 16, 128),
                     labels = c("<=4GB", "8GB", "16GB", ">16GB"))
print(tapply(df$price_usd, df$ram_bucket, median))
