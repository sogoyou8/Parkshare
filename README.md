# Parkshare

Application de visualisation territoriale pour le challenge 48h.

## Lancement rapide

1. Installer les dependances

python -m pip install -r requirements.txt

2. Lancer l'application

python -m streamlit run app/dashboard_map.py

3. Ouvrir l'URL affichee dans le terminal (en general http://localhost:8501)

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

## Ce que fait l'app

- Construit et charge une base DuckDB depuis les CSV de DATA.
- Calcule un score communal avec ponderations ajustables.
- Affiche une carte interactive des communes.
- Affiche un choropleth par departement avec vrais contours IDF.
- Permet l'export CSV des resultats filtres.