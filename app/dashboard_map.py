from __future__ import annotations

import copy
from pathlib import Path

import branca.colormap as cm
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from db_utils import initialize_db, load_kpi_communes
from real_data_utils import (
    aggregate_by_departement,
    color_for_score,
    get_idf_departments_geojson,
    normalize_weights,
)

st.set_page_config(page_title="Parkshare Dashboard", layout="wide", initial_sidebar_state="collapsed")


def apply_dashboard_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

        :root {
            --ps-bg: #f3ede4;
            --ps-bg-soft: #faf4ec;
            --ps-card: #fffcf6;
            --ps-line: #d9cfc2;
            --ps-ink: #1f2b37;
            --ps-muted: #5b6b73;
            --ps-brand: #0b6b5b;
            --ps-brand-soft: #d6ece5;
            --ps-warm: #c76b3a;
            --ps-night: #11151c;
        }

        .stApp {
            background:
                radial-gradient(circle at 10% -10%, rgba(210,236,228,0.7) 0%, transparent 35%),
                radial-gradient(circle at 110% 0%, rgba(251,219,193,0.65) 0%, transparent 38%),
                radial-gradient(circle at 35% 35%, rgba(255,255,255,0.75) 0%, transparent 35%),
                linear-gradient(180deg, var(--ps-bg) 0%, var(--ps-bg-soft) 100%);
            color: var(--ps-ink);
        }

        html, body, [class*="css"] {
            font-family: 'Space Grotesk', sans-serif;
        }

        body {
            overflow: hidden;
        }

        header[data-testid="stHeader"] {
            height: 0;
            visibility: hidden;
        }

        #MainMenu, footer, div[data-testid="stToolbar"], div[data-testid="stDecoration"] {
            visibility: hidden;
        }

        section[data-testid="stSidebar"] {
            display: none;
        }

        .topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 14px;
            margin-bottom: 4px;
            border-radius: 14px;
            background: rgba(17, 21, 28, 0.92);
            color: #fef7ed;
            box-shadow: 0 12px 26px rgba(17, 21, 28, 0.25);
        }

        .topbar-brand {
            font-size: 0.84rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            font-weight: 700;
        }

        .topbar-tag {
            font-size: 0.72rem;
            font-weight: 600;
            padding: 6px 10px;
            border-radius: 999px;
            color: #ffe5c7;
            background: rgba(199, 107, 58, 0.2);
            border: 1px solid rgba(199, 107, 58, 0.45);
        }

        .hero-shell {
            border: 1px solid var(--ps-line);
            border-radius: 20px;
            background:
                linear-gradient(120deg, rgba(214,236,229,0.85) 0%, rgba(255,251,242,0.98) 45%, rgba(251,219,193,0.5) 100%);
            box-shadow: 0 16px 32px rgba(33, 47, 61, 0.12);
            padding: 12px 18px;
            margin-bottom: 6px;
        }

        .hero-kicker {
            display: inline-block;
            font-size: 0.7rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--ps-brand);
            background: var(--ps-brand-soft);
            padding: 5px 10px;
            border-radius: 999px;
            margin-bottom: 8px;
        }

        .hero-title {
            margin: 0;
            font-family: 'Fraunces', 'Space Grotesk', sans-serif;
            font-size: 1.5rem;
            line-height: 1.15;
            color: var(--ps-ink);
            font-weight: 700;
        }

        .hero-subtitle {
            margin-top: 6px;
            margin-bottom: 0;
            color: var(--ps-muted);
            font-size: 0.85rem;
            line-height: 1.35;
        }

        .panel-card {
            border: 1px solid var(--ps-line);
            border-radius: 16px;
            background: rgba(255, 252, 246, 0.96);
            box-shadow: 0 12px 26px rgba(33, 47, 61, 0.09);
            padding: 12px 14px;
            margin-bottom: 10px;
        }

        .panel-title {
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--ps-ink);
            margin-bottom: 4px;
        }

        .panel-subtitle {
            color: var(--ps-muted);
            font-size: 0.82rem;
            margin-bottom: 8px;
        }

        .panel-list {
            margin: 6px 0 0 16px;
            color: var(--ps-muted);
            font-size: 0.82rem;
        }

        .filter-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(11, 107, 91, 0.1);
            color: #0b6b5b;
            border: 1px solid rgba(11, 107, 91, 0.22);
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 600;
            margin-right: 6px;
            margin-bottom: 6px;
        }

        label[data-testid="stWidgetLabel"] {
            font-weight: 700;
            font-size: 0.86rem;
            color: var(--ps-ink);
        }

        div[data-testid="stCaptionContainer"] {
            color: var(--ps-muted);
        }

        .side-scroll-marker,
        .tables-scroll-marker {
            display: none;
        }

        div[data-testid="stVerticalBlock"]:has(.side-scroll-marker) {
            border: 1px solid var(--ps-line);
            border-radius: 16px;
            background: rgba(255, 252, 246, 0.96);
            box-shadow: 0 12px 26px rgba(33, 47, 61, 0.09);
            padding: 12px 14px;
            max-height: 520px;
            overflow-y: auto;
        }

        div[data-testid="stVerticalBlock"]:has(.tables-scroll-marker) {
            border: 1px solid var(--ps-line);
            border-radius: 16px;
            background: rgba(255, 252, 246, 0.96);
            box-shadow: 0 12px 26px rgba(33, 47, 61, 0.09);
            padding: 12px 14px;
            max-height: 540px;
            overflow-y: auto;
        }

        .kpi-card {
            border: 1px solid var(--ps-line);
            border-radius: 14px;
            background: var(--ps-card);
            box-shadow: 0 10px 22px rgba(33, 47, 61, 0.08);
            padding: 10px 12px;
            min-height: 72px;
        }

        .kpi-label {
            margin: 0;
            color: var(--ps-muted);
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .kpi-value {
            margin-top: 6px;
            margin-bottom: 2px;
            color: var(--ps-ink);
            font-size: 1.15rem;
            font-weight: 700;
            line-height: 1.1;
        }

        .kpi-note {
            margin: 0;
            color: #7d8b93;
            font-size: 0.74rem;
            font-weight: 500;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 6px;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 10px;
            border: 1px solid var(--ps-line);
            background: rgba(255, 255, 255, 0.78);
            color: var(--ps-ink);
            font-weight: 600;
            padding: 6px 12px;
        }

        .stTabs [aria-selected="true"] {
            background: var(--ps-brand-soft) !important;
            border-color: #8ab9ae !important;
            color: #11453d !important;
        }

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div {
            background: #f6efe6 !important;
            border-radius: 12px !important;
            border: 1px solid rgba(31, 43, 55, 0.12) !important;
        }

        div[data-testid="stNumberInput"] input {
            background: #f6efe6 !important;
            border-radius: 12px !important;
            border: 1px solid rgba(31, 43, 55, 0.12) !important;
        }

        div[data-baseweb="slider"] > div > div {
            color: var(--ps-brand);
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--ps-line);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 8px 20px rgba(33, 47, 61, 0.07);
        }

        div[data-testid="stVegaLiteChart"] > div {
            border-radius: 14px;
            border: 1px solid rgba(31, 43, 55, 0.15);
            box-shadow: 0 10px 20px rgba(17, 21, 28, 0.12);
            padding: 6px;
            background: #11151c;
        }

        .stDownloadButton button {
            background: linear-gradient(135deg, #0f6a5a 0%, #17836f 100%);
            color: #ffffff;
            border: 0;
            border-radius: 10px;
            font-weight: 700;
            padding: 0.55rem 0.95rem;
        }

        .stDownloadButton button:hover {
            background: linear-gradient(135deg, #0e5f50 0%, #136f5f 100%);
            color: #ffffff;
        }

        .block-container {
            padding-top: 0.4rem;
            padding-bottom: 0.4rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(label: str, value: str, note: str) -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <p class="kpi-label">{label}</p>
            <p class="kpi-value">{value}</p>
            <p class="kpi-note">{note}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_info_card(title: str, items: list[str]) -> None:
    items_html = "".join(f"<li>{item}</li>" for item in items)
    st.markdown(
        f"""
        <div class="panel-card">
            <div class="panel-title">{title}</div>
            <ul class="panel-list">{items_html}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


apply_dashboard_theme()
st.markdown(
    """
    <div class="topbar">
        <div class="topbar-brand">Parkshare Intelligence</div>
        <div class="topbar-tag">IDF • 2024</div>
    </div>
    <div class="hero-shell">
        <div class="hero-kicker">Etude de marche data</div>
        <h1 class="hero-title">Carte interactive des opportunites de stationnement partage en Ile-de-France</h1>
        <p class="hero-subtitle">
            Explore les communes prioritaires et analyse les dynamiques departementales
            avec un score pre-calcule et une vue simplifiee.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "DATA"
CSV_COMMUNES = DATA_DIR / "communes_idf_clean.csv"
CSV_LOGEMENT = DATA_DIR / "logement_idf_clean.csv"
DEFAULT_WEIGHT_POPULATION = 0.45
DEFAULT_WEIGHT_LOGEMENTS = 0.35
DEFAULT_WEIGHT_TAUX_RP = 0.20


@st.cache_data(show_spinner=False)
def charger_base_data(csv_communes: str, csv_logement: str) -> pd.DataFrame:
    initialize_db(csv_communes, csv_logement, overwrite=False)
    return load_kpi_communes()


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

normalized_weights = normalize_weights(
    DEFAULT_WEIGHT_POPULATION,
    DEFAULT_WEIGHT_LOGEMENTS,
    DEFAULT_WEIGHT_TAUX_RP,
)
scored_data = base_data.copy()
tab_overview, tab_tables = st.tabs(["Vue principale", "Tableaux & analyses"])

with tab_overview:
    col_map, col_side = st.columns([3.2, 1.6], gap="large")
    with col_side:
        side_container = st.container()

    with side_container:
        st.markdown('<div class="side-scroll-marker"></div>', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Filtres & affichage</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="panel-subtitle">Ajuste les seuils, puis explore la carte.</div>',
            unsafe_allow_html=True,
        )
        chips_html = " ".join(
            [
                f"<span class='filter-chip'>Population {format_float(normalized_weights['population'] * 100, 1)}%</span>",
                f"<span class='filter-chip'>Logements {format_float(normalized_weights['logements'] * 100, 1)}%</span>",
                f"<span class='filter-chip'>Taux RP {format_float(normalized_weights['taux_rp'] * 100, 1)}%</span>",
            ]
        )
        st.markdown(chips_html, unsafe_allow_html=True)

        departements_disponibles = sorted(scored_data["departement_code"].astype(str).unique().tolist())
        deps_selectionnes = st.multiselect(
            "Departements",
            options=departements_disponibles,
            default=departements_disponibles,
        )

        col_a, col_b = st.columns(2)
        with col_a:
            score_min = st.slider("Score minimum", min_value=0, max_value=100, value=55, step=5)
            taux_rp_min = st.slider(
                "Taux RP minimum",
                min_value=0.0,
                max_value=1.0,
                value=0.40,
                step=0.05,
            )
        with col_b:
            pop_min = st.number_input(
                "Population minimale",
                min_value=0,
                max_value=int(scored_data["population"].max()),
                value=10000,
                step=10000,
            )
            max_points = st.slider("Max points carte", min_value=200, max_value=2000, value=900, step=100)

        with st.expander("Options carte", expanded=False):
            fond_carte = st.selectbox(
                "Fond de carte",
                options=["CartoDB Positron", "OpenStreetMap", "CartoDB dark_matter"],
                index=0,
            )
            afficher_choropleth = st.checkbox("Afficher choropleth departement", value=True)

        hauteur_carte = 400

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

        palette = ["#eff6f2", "#cfe7db", "#9ad0bb", "#5ab08d", "#1f6f5a"]
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
                "fillOpacity": 0.3,
                "weight": 1.2,
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
                sticky=True,
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
            width: 210px;
            font-family: Space Grotesk, sans-serif;
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
        popup_html = (
            "<div style='font-family:Space Grotesk, Arial, sans-serif; min-width: 230px;'>"
            f"<div style='font-weight:700; font-size:14px; color:#0f172a; margin-bottom:6px;'>{row['commune']}</div>"
            "<div style='font-size:12px; color:#334155; line-height:1.45;'>"
            f"Code commune: <b>{row['code_commune']}</b><br>"
            f"Departement: <b>{row['departement_code']}</b><br>"
            f"Score: <b>{format_float(float(row['score']), 1)}/100</b><br>"
            f"Population: <b>{format_int(row['population'])}</b><br>"
            f"Logements: <b>{format_int(row['logements_total'])}</b><br>"
            f"Residences principales: <b>{format_int(row['residences_principales'])}</b><br>"
            f"Taux RP: <b>{format_float(float(row['taux_rp']) * 100, 1)}%</b>"
            "</div>"
            "</div>"
        )
        folium.CircleMarker(
            location=[float(row["latitude"]), float(row["longitude"])],
            radius=6 + (float(row["score"]) / 22),
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=f"{row['commune']} | score {format_float(float(row['score']), 1)}",
            color=couleur,
            weight=1.2,
            opacity=0.95,
            fill=True,
            fill_color=couleur,
            fill_opacity=0.82,
        ).add_to(marker_layer)

    marker_layer.add_to(carte)
    folium.LayerControl(collapsed=True).add_to(carte)

    with col_map:
        map_state = st_folium(
            carte,
            height=hauteur_carte,
            use_container_width=True,
            returned_objects=["last_object_hovered_tooltip", "last_object_clicked_tooltip"],
        )

    selected_tooltip = None
    if map_state:
        selected_tooltip = map_state.get("last_object_hovered_tooltip") or map_state.get(
            "last_object_clicked_tooltip"
        )

    score_moyen_affichage = (
        format_float(float(donnees_filtrees["score"].mean()), 1) if not donnees_filtrees.empty else "0,0"
    )
    population_totale_affichage = (
        format_int(float(donnees_filtrees["population"].sum())) if not donnees_filtrees.empty else "0"
    )

    with side_container:
        render_info_card(
            "Filtres actifs",
            [
                f"Departements: {len(deps_selectionnes)}",
                f"Score minimum: {score_min}/100",
                f"Population min: {format_int(pop_min)}",
                f"Taux RP min: {format_float(taux_rp_min * 100, 0)}%",
            ],
        )
        if selected_tooltip:
            st.markdown(
                f"""
                <div class="panel-card">
                    <div class="panel-title">Departement survole</div>
                    {selected_tooltip}
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            render_info_card(
                "Departement survole",
                ["Survole ou clique sur un departement pour afficher ses indicateurs."],
            )

        st.markdown('<div class="panel-title">Synthese rapide</div>', unsafe_allow_html=True)
        kpi_col1, kpi_col2 = st.columns(2)
        with kpi_col1:
            render_kpi_card("Communes filtrees", str(len(donnees_filtrees)), "apres seuils")
            render_kpi_card("Score moyen", score_moyen_affichage, "moyenne locale")
        with kpi_col2:
            render_kpi_card("Communes affichees", str(len(donnees_affichage)), "limite carte")
            render_kpi_card("Population", population_totale_affichage, "total perimetre")
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

display_df = export_df.copy()
if not display_df.empty:
    display_df["score"] = display_df["score"].map(lambda x: format_float(float(x), 2))
    display_df["population"] = display_df["population"].map(format_int)
    display_df["logements_total"] = display_df["logements_total"].map(format_int)
    display_df["residences_principales"] = display_df["residences_principales"].map(format_int)
    display_df["taux_rp"] = display_df["taux_rp"].map(lambda x: f"{format_float(float(x) * 100, 1)}%")

with tab_tables:
    with st.container():
        st.markdown('<div class="tables-scroll-marker"></div>', unsafe_allow_html=True)
        tab_communes, tab_departements, tab_ponderations, tab_export = st.tabs(
            ["Communes", "Departements", "Ponderations", "Export"]
        )

        with tab_communes:
            st.caption("Classement des communes selon les filtres actifs.")
            if display_df.empty:
                st.warning("Aucune commune ne correspond aux filtres. Reduis les seuils.")
            else:
                st.dataframe(display_df, height=280, use_container_width=True)

        with tab_departements:
            st.caption("Synthese departementale pour lecture macro du territoire.")
            col_table, col_chart = st.columns([1.2, 1], gap="large")
            with col_table:
                st.dataframe(departement_stats, height=280, use_container_width=True)
            with col_chart:
                if not departement_stats.empty:
                    st.bar_chart(departement_stats.set_index("departement_code")["score_moyen"], height=280)

        with tab_ponderations:
            st.caption("Ponderations fixes appliquees au calcul de score.")
            weights_display = weights_df.copy()
            weights_display["poids_percent"] = (weights_display["poids"] * 100).round(1)
            col_table, col_chart = st.columns([1, 1], gap="large")
            with col_table:
                st.dataframe(
                    weights_display[["composante", "poids_percent"]].rename(
                        columns={"poids_percent": "poids (%)"}
                    ),
                    height=240,
                    use_container_width=True,
                )
            with col_chart:
                st.bar_chart(weights_display.set_index("composante")["poids_percent"], height=240)

        with tab_export:
            st.caption("Exporte le jeu filtre pour partage, reporting ou pipeline data.")
            col_action, col_preview = st.columns([1, 2], gap="large")
            with col_action:
                st.download_button(
                    label="Telecharger le CSV filtre",
                    data=export_df.to_csv(index=False).encode("utf-8"),
                    file_name="parkshare_communes_filtrees.csv",
                    mime="text/csv",
                    disabled=export_df.empty,
                )
            with col_preview:
                if not display_df.empty:
                    st.dataframe(display_df.head(20), height=220, use_container_width=True)
