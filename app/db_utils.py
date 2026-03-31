from __future__ import annotations

from pathlib import Path
from typing import Union

import duckdb
import pandas as pd

from real_data_utils import aggregate_by_departement, compute_score, load_idf_datasets

PathLike = Union[str, Path]

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "DATA"
DB_PATH = DATA_DIR / "parkshare.duckdb"
DONNEES_CLEAN_PATH = DATA_DIR / "donnees_clean_idf.csv"
COPRO_EPCI_CLEAN_PATH = DATA_DIR / "copro_epci_clean.csv"
COPRO_EPCI_RAW_PATH = DATA_DIR / "tableau-synthetique-coproff-epci-2024.csv"


def get_db_path() -> Path:
    return DB_PATH


def connect_db(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    if read_only:
        return duckdb.connect(str(DB_PATH), read_only=True)
    return duckdb.connect(str(DB_PATH))


def initialize_db(
    communes_csv: PathLike,
    logement_csv: PathLike,
    overwrite: bool = False,
) -> Path:
    if DB_PATH.exists() and not overwrite:
        return DB_PATH

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    conn = connect_db(read_only=False)
    try:
        conn.execute(
            "CREATE OR REPLACE TABLE src_communes AS SELECT * FROM read_csv_auto(?)",
            [str(communes_csv)],
        )
        conn.execute(
            "CREATE OR REPLACE TABLE src_logement AS SELECT * FROM read_csv_auto(?)",
            [str(logement_csv)],
        )

        merged = load_idf_datasets(communes_csv, logement_csv)
        conn.register("tr_df", merged)
        conn.execute("CREATE OR REPLACE TABLE tr_communes AS SELECT * FROM tr_df")
        conn.unregister("tr_df")

        scored, _ = compute_score(merged)
        conn.register("kpi_communes_df", scored)
        conn.execute("CREATE OR REPLACE TABLE kpi_communes AS SELECT * FROM kpi_communes_df")
        conn.unregister("kpi_communes_df")

        departements = aggregate_by_departement(scored)
        conn.register("kpi_departements_df", departements)
        conn.execute(
            "CREATE OR REPLACE TABLE kpi_departements AS SELECT * FROM kpi_departements_df"
        )
        conn.unregister("kpi_departements_df")

        optional_sources = [
            (DONNEES_CLEAN_PATH, "tr_donnees_clean_idf"),
            (COPRO_EPCI_RAW_PATH, "src_copro_epci_raw"),
            (COPRO_EPCI_CLEAN_PATH, "tr_copro_epci"),
        ]
        for path, table_name in optional_sources:
            if path.exists():
                conn.execute(
                    f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_csv_auto(?)",
                    [str(path)],
                )
    finally:
        conn.close()

    return DB_PATH


def load_transformed_data() -> pd.DataFrame:
    conn = connect_db(read_only=True)
    try:
        return conn.execute("SELECT * FROM tr_communes").df()
    finally:
        conn.close()


def load_kpi_communes() -> pd.DataFrame:
    conn = connect_db(read_only=True)
    try:
        return conn.execute("SELECT * FROM kpi_communes").df()
    finally:
        conn.close()


def load_kpi_departements() -> pd.DataFrame:
    conn = connect_db(read_only=True)
    try:
        return conn.execute("SELECT * FROM kpi_departements").df()
    finally:
        conn.close()
