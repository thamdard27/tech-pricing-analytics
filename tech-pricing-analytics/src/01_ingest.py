"""
01_ingest.py  -  Data ingestion layer.

Downloads the source technology-pricing dataset from its public origin and
stores an immutable copy in data/raw/. Re-running is idempotent: the raw file
is never modified in place, satisfying a simple raw-immutability data-management
standard (see docs/data_governance.md).

Data source (cited): Laptop Price dataset, originally published on Kaggle by
Muhammet Varli ("Laptop Price"), mirrored at the GitHub URL below.
See data/README.md for full provenance and licensing.
"""
from pathlib import Path
import hashlib
import urllib.request

SOURCE_URL = (
    "https://raw.githubusercontent.com/campusx-official/"
    "laptop-price-predictor-regression-project/main/laptop_data.csv"
)
RAW_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "laptop_pricing_raw.csv"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ingest() -> Path:
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    if RAW_PATH.exists():
        print(f"[ingest] raw copy already present: {RAW_PATH}")
    else:
        print(f"[ingest] downloading from source ...")
        req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=30).read()
        RAW_PATH.write_bytes(data)
        print(f"[ingest] wrote {len(data):,} bytes -> {RAW_PATH}")
    print(f"[ingest] sha256: {sha256(RAW_PATH)}")
    return RAW_PATH


if __name__ == "__main__":
    ingest()
