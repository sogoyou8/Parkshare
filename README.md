# Parkshare

Application de visualisation territoriale pour le challenge 48h.

## Prerequis

- Python 3.10+
- Fichiers DATA disponibles (voir section Donnees requises)

## Lancement rapide

1. Installer les dependances

```
python -m pip install -r requirements.txt
```

2. Lancer l'application

```
python -m streamlit run app/dashboard_map.py
```

3. Ouvrir l'URL affichee dans le terminal (en general http://localhost:8501)

## Fonctionnalites principales

- Construit et charge une base DuckDB depuis les CSV de DATA.
- Calcule un score communal base sur population, logements et taux RP.
- Filtres par departements, score, population, taux RP et limite de points.
- Carte interactive + choropleth departement avec infos au survol.
- Synthese rapide KPI et tableaux d'analyse.
- Export CSV des resultats filtres.

## Donnees requises

- DATA/communes_idf_clean.csv
- DATA/logement_idf_clean.csv
- DATA/idf_departements.geojson

## Structure minimale

- DATA
  - communes_idf_clean.csv
  - logement_idf_clean.csv
  - idf_departements.geojson
  - analytics.ipynb
- app
  - dashboard_map.py
  - db_utils.py
  - real_data_utils.py
  - rebuild_db.py
- INFRA