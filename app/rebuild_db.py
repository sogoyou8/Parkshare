from __future__ import annotations

from pathlib import Path

from db_utils import initialize_db

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "DATA"


def main() -> None:
    communes_csv = DATA_DIR / "communes_idf_clean.csv"
    logement_csv = DATA_DIR / "logement_idf_clean.csv"

    missing = [path for path in (communes_csv, logement_csv) if not path.exists()]
    if missing:
        missing_list = ", ".join(str(path) for path in missing)
        raise FileNotFoundError(f"CSV introuvables: {missing_list}")

    db_path = initialize_db(communes_csv, logement_csv, overwrite=True)
    print(f"BDD reconstruite: {db_path}")


if __name__ == "__main__":
    main()
