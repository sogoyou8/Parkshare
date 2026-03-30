from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple, Union

import pandas as pd

PathLike = Union[str, Path]


def minmax_normalize(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.dropna().empty:
        return pd.Series([0.5] * len(series), index=series.index)

    min_val = numeric.min()
    max_val = numeric.max()
    if min_val == max_val:
        return pd.Series([0.5] * len(series), index=series.index)

    return (numeric - min_val) / (max_val - min_val)


def normalize_weights(
    weight_population: float,
    weight_logements: float,
    weight_taux_rp: float,
) -> Dict[str, float]:
    total = weight_population + weight_logements + weight_taux_rp
    if total <= 0:
        return {
            "population": 1 / 3,
            "logements": 1 / 3,
            "taux_rp": 1 / 3,
        }

    return {
        "population": weight_population / total,
        "logements": weight_logements / total,
        "taux_rp": weight_taux_rp / total,
    }


def load_idf_datasets(communes_csv: PathLike, logement_csv: PathLike) -> pd.DataFrame:
    communes = pd.read_csv(communes_csv)
    logement = pd.read_csv(logement_csv)

    required_communes = {
        "code_commune",
        "nom_standard",
        "population",
        "latitude_centre",
        "longitude_centre",
    }
    required_logement = {"code_commune", "p22_log", "p22_rp"}

    missing_communes = sorted(required_communes - set(communes.columns))
    missing_logement = sorted(required_logement - set(logement.columns))
    if missing_communes:
        raise ValueError(f"Colonnes manquantes dans communes: {missing_communes}")
    if missing_logement:
        raise ValueError(f"Colonnes manquantes dans logement: {missing_logement}")

    communes = communes.rename(
        columns={
            "nom_standard": "commune",
            "latitude_centre": "latitude",
            "longitude_centre": "longitude",
        }
    )

    communes["code_commune"] = communes["code_commune"].astype(str).str.zfill(5)
    logement["code_commune"] = logement["code_commune"].astype(str).str.zfill(5)

    communes["population"] = pd.to_numeric(communes["population"], errors="coerce")
    communes["latitude"] = pd.to_numeric(communes["latitude"], errors="coerce")
    communes["longitude"] = pd.to_numeric(communes["longitude"], errors="coerce")

    logement["p22_log"] = pd.to_numeric(logement["p22_log"], errors="coerce").fillna(0)
    logement["p22_rp"] = pd.to_numeric(logement["p22_rp"], errors="coerce").fillna(0)

    logement_agg = (
        logement.groupby("code_commune", as_index=False)
        .agg(
            logements_total=("p22_log", "sum"),
            residences_principales=("p22_rp", "sum"),
        )
        .assign(
            taux_rp=lambda d: d["residences_principales"]
            / d["logements_total"].replace(0, pd.NA)
        )
    )

    merged = communes.merge(logement_agg, on="code_commune", how="left")

    merged["population"] = merged["population"].fillna(0)
    merged["logements_total"] = pd.to_numeric(merged["logements_total"], errors="coerce").fillna(0)
    merged["residences_principales"] = pd.to_numeric(
        merged["residences_principales"], errors="coerce"
    ).fillna(0)
    merged["taux_rp"] = pd.to_numeric(merged["taux_rp"], errors="coerce").fillna(0)

    merged["departement_code"] = merged["code_commune"].astype(str).str[:2]

    merged = merged[
        merged["latitude"].between(41, 52)
        & merged["longitude"].between(-5, 10)
        & merged["commune"].notna()
    ].copy()

    return merged.sort_values("code_commune").reset_index(drop=True)


def compute_score(
    df: pd.DataFrame,
    weight_population: float = 0.45,
    weight_logements: float = 0.35,
    weight_taux_rp: float = 0.20,
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    work = df.copy()
    weights = normalize_weights(weight_population, weight_logements, weight_taux_rp)

    work["population_norm"] = minmax_normalize(work["population"])
    work["logements_norm"] = minmax_normalize(work["logements_total"])
    work["taux_rp_norm"] = minmax_normalize(work["taux_rp"])

    work["score"] = (
        100
        * (
            work["population_norm"] * weights["population"]
            + work["logements_norm"] * weights["logements"]
            + work["taux_rp_norm"] * weights["taux_rp"]
        )
    ).round(2)

    return work, weights


def aggregate_by_departement(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "departement_code",
        "score_moyen",
        "nb_communes",
        "population_totale",
        "logements_total",
        "residences_principales",
        "taux_rp_moyen",
    ]
    if df.empty:
        return pd.DataFrame(columns=columns)

    grouped = (
        df.groupby("departement_code", as_index=False)
        .agg(
            score_moyen=("score", "mean"),
            nb_communes=("code_commune", "nunique"),
            population_totale=("population", "sum"),
            logements_total=("logements_total", "sum"),
            residences_principales=("residences_principales", "sum"),
            taux_rp_moyen=("taux_rp", "mean"),
        )
        .sort_values("score_moyen", ascending=False)
        .reset_index(drop=True)
    )

    grouped["score_moyen"] = grouped["score_moyen"].round(2)
    grouped["taux_rp_moyen"] = grouped["taux_rp_moyen"].round(4)
    grouped["population_totale"] = grouped["population_totale"].round(0)
    grouped["logements_total"] = grouped["logements_total"].round(0)
    grouped["residences_principales"] = grouped["residences_principales"].round(0)

    return grouped[columns]


def color_for_score(score: float) -> str:
    if score >= 80:
        return "darkgreen"
    if score >= 60:
        return "green"
    if score >= 40:
        return "orange"
    return "red"


def _legacy_idf_departments_geojson() -> Dict:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "departement_code": "92",
                    "departement_name": "Hauts-de-Seine",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[2.13, 48.80], [2.34, 48.80], [2.34, 48.93], [2.13, 48.93], [2.13, 48.80]]],
                },
            },
            {
                "type": "Feature",
                "properties": {
                    "departement_code": "93",
                    "departement_name": "Seine-Saint-Denis",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[2.33, 48.83], [2.58, 48.83], [2.58, 49.02], [2.33, 49.02], [2.33, 48.83]]],
                },
            },
            {
                "type": "Feature",
                "properties": {
                    "departement_code": "94",
                    "departement_name": "Val-de-Marne",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[2.33, 48.70], [2.58, 48.70], [2.58, 48.86], [2.33, 48.86], [2.33, 48.70]]],
                },
            },
            {
                "type": "Feature",
                "properties": {
                    "departement_code": "95",
                    "departement_name": "Val-d-Oise",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[1.95, 48.94], [2.47, 48.94], [2.47, 49.20], [1.95, 49.20], [1.95, 48.94]]],
                },
            },
            {
                "type": "Feature",
                "properties": {
                    "departement_code": "78",
                    "departement_name": "Yvelines",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[1.45, 48.62], [2.20, 48.62], [2.20, 49.05], [1.45, 49.05], [1.45, 48.62]]],
                },
            },
            {
                "type": "Feature",
                "properties": {
                    "departement_code": "91",
                    "departement_name": "Essonne",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[2.05, 48.35], [2.62, 48.35], [2.62, 48.72], [2.05, 48.72], [2.05, 48.35]]],
                },
            },
            {
                "type": "Feature",
                "properties": {
                    "departement_code": "77",
                    "departement_name": "Seine-et-Marne",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[2.30, 48.35], [3.42, 48.35], [3.42, 49.15], [2.30, 49.15], [2.30, 48.35]]],
                },
            },
        ],
    }


def _normalize_idf_geojson_schema(geojson: Dict) -> Dict:
    expected_codes = {"75", "77", "78", "91", "92", "93", "94", "95"}
    normalized_features = []

    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        geometry = feature.get("geometry")
        if geometry is None:
            continue

        code_raw = props.get("departement_code", props.get("code", ""))
        code = str(code_raw).strip().zfill(2)
        if code not in expected_codes:
            continue

        name = props.get("departement_name", props.get("nom", code))
        normalized_features.append(
            {
                "type": "Feature",
                "properties": {
                    "departement_code": code,
                    "departement_name": str(name),
                },
                "geometry": geometry,
            }
        )

    return {
        "type": "FeatureCollection",
        "features": normalized_features,
    }


def get_idf_departments_geojson() -> Dict:
    data_dir = Path(__file__).resolve().parents[1] / "DATA"
    geojson_path = data_dir / "idf_departements.geojson"

    if geojson_path.exists():
        try:
            with geojson_path.open("r", encoding="utf-8") as f:
                local_geojson = json.load(f)

            normalized = _normalize_idf_geojson_schema(local_geojson)
            if normalized.get("features"):
                return normalized
        except (json.JSONDecodeError, OSError):
            pass

    return _legacy_idf_departments_geojson()