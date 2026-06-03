"""
run_pipeline.py  -  Orchestrates the full pricing-analytics pipeline end to end.

    python run_pipeline.py

Stages:
  01 ingest          download + store raw data (hashed, idempotent)
  02 clean           parse spec strings -> typed features + quality gates
  03 eda_trends      EDA, pricing-trend tables, business charts
  04 pricing_model   model, driver ranking, segmentation, auto-insights
  05 export_model    export a linear model for the C++ scorer
  (C++)              compile + run the C++ price scorer (if g++ present)
  06 price_scenarios forward time-based value projection (assumption-driven)
  07 insight_writer  executive summary (LLM if ANTHROPIC_API_KEY set, else fallback)

Each stage is also runnable on its own (see src/).
"""
import runpy
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
PY_STEPS = ["01_ingest.py", "02_clean.py", "03_eda_trends.py",
            "04_pricing_model.py", "05_export_model.py"]
LATE_STEPS = ["06_price_scenarios.py", "07_insight_writer.py"]


def run_py(step):
    print(f"\n{'='*60}\nRUNNING {step}\n{'='*60}")
    runpy.run_path(str(SRC / step), run_name="__main__")


def build_and_run_cpp():
    print(f"\n{'='*60}\nBUILDING + RUNNING C++ scorer\n{'='*60}")
    if shutil.which("g++") is None:
        print("[cpp] g++ not found; skipping compile. "
              "Install g++ to build src/score_price.cpp.")
        return
    (ROOT / "bin").mkdir(exist_ok=True)
    subprocess.run(["g++", "-O2", "-std=c++17", "-o", "bin/score_price",
                    "src/score_price.cpp"], cwd=ROOT, check=True)
    print("[cpp] compiled bin/score_price; scoring sample config:")
    subprocess.run(["./bin/score_price"], cwd=ROOT, check=True)


if __name__ == "__main__":
    for s in PY_STEPS:
        run_py(s)
    build_and_run_cpp()
    for s in LATE_STEPS:
        run_py(s)
    print("\nPipeline complete. See reports/ for figures, findings, "
          "executive_summary.md, and metrics; bin/ for the C++ scorer.")
