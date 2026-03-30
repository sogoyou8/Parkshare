from __future__ import annotations

import copy
from pathlib import Path

import branca.colormap as cm
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from real_data_utils import (
    aggregate_by_departement,
    color_for_score,
    compute_score,
    get_idf_departments_geojson,
    load_idf_datasets,
)

st.set_page_config(page_title="Parkshare Dashboard", layout="wide")
st.title("Parkshare - Carte interactive (CSV reels)")
st.caption("Pipeline CSV modulaire, scoring parametrable, carte + choropleth + export")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "DATA"
CSV_COMMUNES = DATA_DIR / "communes_idf_clean.csv"
CSV_LOGEMENT = DATA_DIR / "logement_idf_clean.csv"


@st.cache_data(show_spinner=False)
def charger_base_data(csv_communes: str, csv_logement: str) -> pd.DataFrame:
    return load_idf_datasets(csv_communes, csv_logement)


def format_int(value: float | int) -> str:
    return f"{int(value):,}".replace(",", " ")


def format_float(value: float, decimals: int = 1) -> str:
    return f"{value:.{decimals}f}".replace(".", ",")


def geojson_departements_avec_stats(departement_stats: pd.DataFrame) -> dict:
    geojson = copy.deepcopy(get_idf_departments_geojson())

    lookup = {}
    if not departement_stats.empty:
        lookup = departement_stats.set_index("departement_code").to_dict(orient="index")

    for feature in geojson["features"]:
        props = feature["properties"]
        code = props["departement_code"]
        stats = lookup.get(code)

        if stats is None:
            props["score_moyen"] = 0.0
            props["score_moyen_label"] = "0,0"
            props["nb_communes"] = 0
            props["population_totale"] = 0
            props["population_totale_label"] = "0"
            props["logements_total"] = 0
            props["logements_total_label"] = "0"
            props["taux_rp_moyen"] = 0.0
            props["taux_rp_moyen_label"] = "0,0%"
        else:
            score_moyen = float(stats["score_moyen"])
            population_totale = int(stats["population_totale"])
            logements_total = int(stats["logements_total"])
            taux_rp_moyen = float(stats["taux_rp_moyen"])

            props["score_moyen"] = score_moyen
            props["score_moyen_label"] = format_float(score_moyen, 1)
            props["nb_communes"] = int(stats["nb_communes"])
            props["population_totale"] = population_totale
            props["population_totale_label"] = format_int(population_totale)
            props["logements_total"] = logements_total
            props["logements_total_label"] = format_int(logements_total)
            props["taux_rp_moyen"] = taux_rp_moyen
            props["taux_rp_moyen_label"] = f"{format_float(taux_rp_moyen * 100, 1)}%"

    return geojson


if not CSV_COMMUNES.exists() or not CSV_LOGEMENT.exists():
    st.error("Fichiers CSV introuvables dans le dossier DATA.")
    st.stop()

base_data = charger_base_data(str(CSV_COMMUNES), str(CSV_LOGEMENT))
if base_data.empty:
    st.error("Aucune donnee exploitable apres fusion des CSV.")
    st.stop()

st.sidebar.header("Scoring")
w_population = st.sidebar.slider("Poids population", min_value=0.0, max_value=1.0, value=0.45, step=0.01)
w_logements = st.sidebar.slider("Poids logements", min_value=0.0, max_value=1.0, value=0.35, step=0.01)
w_taux_rp = st.sidebar.slider("Poids taux RP", min_value=0.0, max_value=1.0, value=0.20, step=0.01)

scored_data, normalized_weights = compute_score(
    base_data,
    weight_population=w_population,
    weight_logements=w_logements,
    weight_taux_rp=w_taux_rp,
)

st.sidebar.header("Filtres")
departements_disponibles = sorted(scored_data["departement_code"].astype(str).unique().tolist())
deps_selectionnes = st.sidebar.multiselect(
    "Departements",
    options=departements_disponibles,
    default=departements_disponibles,
)

score_min = st.sidebar.slider("Score minimum", min_value=0, max_value=100, value=55, step=5)
pop_min = st.sidebar.number_input(
    "Population minimale",
    min_value=0,
    max_value=int(scored_data["population"].max()),
    value=10000,
    step=10000,
)
taux_rp_min = st.sidebar.slider(
    "Taux residences principales minimum",
    min_value=0.0,
    max_value=1.0,
    value=0.40,
    step=0.05,
)
max_points = st.sidebar.slider("Max points sur la carte", min_value=100, max_value=2500, value=1200, step=100)

st.sidebar.header("Affichage carte")
fond_carte = st.sidebar.selectbox(
    "Fond de carte",
    options=["CartoDB Positron", "OpenStreetMap", "CartoDB dark_matter"],
    index=0,
)
afficher_choropleth = st.sidebar.checkbox("Afficher choropleth departement", value=True)
hauteur_carte = st.sidebar.slider("Hauteur carte", min_value=500, max_value=900, value=650, step=50)

donnees_filtrees = scored_data[
    (scored_data["score"] >= score_min)
    & (scored_data["population"] >= pop_min)
    & (scored_data["taux_rp"] >= taux_rp_min)
    & (scored_data["departement_code"].isin(deps_selectionnes))
].copy()

donnees_affichage = donnees_filtrees.sort_values("score", ascending=False).head(max_points).copy()

base_choropleth = donnees_filtrees if not donnees_filtrees.empty else scored_data
departement_stats = aggregate_by_departement(base_choropleth)
geojson_stats = geojson_departements_avec_stats(departement_stats)

centre_lat = float(donnees_affichage["latitude"].mean()) if not donnees_affichage.empty else 48.8566
centre_lon = float(donnees_affichage["longitude"].mean()) if not donnees_affichage.empty else 2.3522

carte = folium.Map(location=[centre_lat, centre_lon], zoom_start=9, tiles=fond_carte)

if afficher_choropleth and not departement_stats.empty:
    score_min_dep = float(departement_stats["score_moyen"].min())
    score_max_dep = float(departement_stats["score_moyen"].max())
    if score_min_dep == score_max_dep:
        score_max_dep = score_min_dep + 1.0

    palette = ["#eef7f3", "#cae8de", "#8ccdb7", "#4ea786", "#1f6f5a"]
    color_scale = cm.LinearColormap(colors=palette, vmin=score_min_dep, vmax=score_max_dep)

    # Render fill layer as non-interactive so markers remain easy to click.
    folium.GeoJson(
        geojson_stats,
        name="Choropleth departement",
        style_function=lambda feature: {
            "fillColor": color_scale(float(feature["properties"].get("score_moyen", 0.0))),
            "color": "#64748b",
            "weight": 1.0,
            "fillOpacity": 0.28,
            "interactive": False,
        },
        highlight_function=lambda _: {
            "fillOpacity": 0.28,
            "weight": 1.0,
        },
    ).add_to(carte)

    folium.GeoJson(
        geojson_stats,
        name="Infos departement",
        style_function=lambda _: {
            "fill": False,
            "color": "#334155",
            "weight": 2.0,
            "opacity": 0.95,
        },
        highlight_function=lambda _: {
            "color": "#0f766e",
            "weight": 3.0,
            "opacity": 1.0,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=[
                "departement_name",
                "score_moyen_label",
                "nb_communes",
                "population_totale_label",
                "logements_total_label",
                "taux_rp_moyen_label",
            ],
            aliases=[
                "Departement:",
                "Score moyen:",
                "Nb communes:",
                "Population:",
                "Logements:",
                "Taux RP moyen:",
            ],
            localize=True,
            labels=True,
            sticky=False,
            style=(
                "background-color: rgba(255,255,255,0.97);"
                "border: 1px solid #cbd5e1;"
                "border-radius: 8px;"
                "box-shadow: 0 8px 20px rgba(15,23,42,0.16);"
                "padding: 8px 10px;"
                "font-size: 12px;"
                "color: #0f172a;"
            ),
        ),
    ).add_to(carte)

    legend_html = f"""
    <div style="
        position: fixed;
        right: 22px;
        bottom: 22px;
        z-index: 9999;
        background: rgba(255,255,255,0.96);
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        box-shadow: 0 8px 20px rgba(15,23,42,0.16);
        padding: 10px 12px;
        width: 220px;
        font-family: Arial, sans-serif;
    ">
        <div style="font-size:12px; font-weight:700; color:#0f172a; margin-bottom:6px;">Score moyen departement</div>
        <div style="height:10px; border-radius:6px; background: linear-gradient(90deg, {', '.join(palette)});"></div>
        <div style="display:flex; justify-content:space-between; margin-top:6px; font-size:11px; color:#334155;">
            <span>{format_float(score_min_dep, 1)}</span>
            <span>{format_float(score_max_dep, 1)}</span>
        </div>
    </div>
    """
    carte.get_root().html.add_child(folium.Element(legend_html))

marker_layer = folium.FeatureGroup(name="Communes filtrees")
for _, row in donnees_affichage.iterrows():
    couleur = color_for_score(float(row["score"]))
    folium.CircleMarker(
        location=[float(row["latitude"]), float(row["longitude"])],
        radius=5 + (float(row["score"]) / 20),
        popup=(
            f"<b>{row['commune']}</b><br>"
            f"Code commune: {row['code_commune']}<br>"
            f"Departement: {row['departement_code']}<br>"
            f"Score: {float(row['score']):.2f}/100<br>"
            f"Population: {int(row['population']):,}<br>"
            f"Logements: {int(row['logements_total']):,}<br>"
            f"Residences principales: {int(row['residences_principales']):,}<br>"
            f"Taux RP: {float(row['taux_rp']):.1%}"
        ),
        tooltip=f"{row['commune']} | score {float(row['score']):.1f}",
        color=couleur,
        weight=1.2,
        opacity=0.95,
        fill=True,
        fill_color=couleur,
        fill_opacity=0.82,
    ).add_to(marker_layer)

marker_layer.add_to(carte)
folium.LayerControl(collapsed=False).add_to(carte)
st_folium(carte, width=1400, height=hauteur_carte)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Communes filtrees", len(donnees_filtrees))
col2.metric("Communes affichees", len(donnees_affichage))
col3.metric("Score moyen", f"{donnees_filtrees['score'].mean():.1f}" if not donnees_filtrees.empty else "0.0")
col4.metric(
    "Population totale",
    f"{int(donnees_filtrees['population'].sum()):,}" if not donnees_filtrees.empty else "0",
)

st.subheader("Ponderations normalisees")
weights_df = pd.DataFrame(
    {
        "composante": ["Population", "Logements", "Taux RP"],
        "poids": [
            normalized_weights["population"],
            normalized_weights["logements"],
            normalized_weights["taux_rp"],
        ],
    }
)
weights_df["poids"] = (weights_df["poids"] * 100).round(1).astype(str) + "%"
st.dataframe(weights_df, width="stretch")

st.subheader("Resultats filtres")
export_columns = [
    "code_commune",
    "commune",
    "departement_code",
    "score",
    "population",
    "logements_total",
    "residences_principales",
    "taux_rp",
]
export_df = donnees_filtrees[export_columns].sort_values("score", ascending=False).reset_index(drop=True)

st.download_button(
    label="Telecharger le CSV filtre",
    data=export_df.to_csv(index=False).encode("utf-8"),
    file_name="parkshare_communes_filtrees.csv",
    mime="text/csv",
    disabled=export_df.empty,
)

if export_df.empty:
    st.warning("Aucune commune ne correspond aux filtres. Reduis les seuils.")
else:
    st.dataframe(export_df, width="stretch")

st.subheader("Synthese departement")
st.dataframe(departement_stats, width="stretch")
if not departement_stats.empty:
    st.bar_chart(departement_stats.set_index("departement_code")["score_moyen"])
