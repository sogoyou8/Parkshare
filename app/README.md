# Parkshare - App (Dev)

## Objectif

- Stocker les donnees Data dans une base DuckDB.
- Exposer un dashboard Streamlit connecte a la base.
- Documenter le schema (sources, transformations, KPIs).

## Lancement rapide

1. Installer les dependances

python -m pip install -r requirements.txt

2. (Optionnel) Rebuild complet de la base

python app/rebuild_db.py

3. Lancer le dashboard

python -m streamlit run app/dashboard_map.py

## Base de donnees (DuckDB)

- Fichier genere: DATA/parkshare.duckdb
- Tables:
  - src_communes (brut)
  - src_logement (brut)
  - tr_communes (transforme)
  - kpi_communes (KPIs par commune)
  - kpi_departements (KPIs par departement)
- Tables optionnelles (si fichiers presentes dans DATA):
  - tr_donnees_clean_idf
  - src_copro_epci_raw
  - tr_copro_epci

  ## Schema (diagramme ASCII)

  src_communes      src_logement
    \              /
     \            /
      tr_communes
        |
      kpi_communes
        |
     kpi_departements

## Schema (description textuelle)

### src_communes

- code_commune: text
- nom_standard: text
- population: integer
- latitude_centre: double
- longitude_centre: double

### src_logement

- code_commune: text
- p22_log: integer
- p22_rp: integer

### tr_communes

- code_commune: text
- commune: text
- population: integer
- latitude: double
- longitude: double
- logements_total: integer
- residences_principales: integer
- taux_rp: double
- departement_code: text

### kpi_communes

- code_commune: text
- commune: text
- departement_code: text
- population: integer
- logements_total: integer
- residences_principales: integer
- taux_rp: double
- latitude: double
- longitude: double
- population_norm: double
- logements_norm: double
- taux_rp_norm: double
- score: double

### kpi_departements

- departement_code: text
- score_moyen: double
- nb_communes: integer
- population_totale: integer
- logements_total: integer
- residences_principales: integer
- taux_rp_moyen: double

### tr_donnees_clean_idf

- code_commune: text
- nom_standard: text
- population: integer
- latitude_centre: double
- longitude_centre: double
- p22_log: double
- p22_rp: double
- logements: double
- residences: double
- ratio_collectif: double
- densite: double
- tension_parking: double
- score: double
- pression_urbaine: double
- logement_par_habitant: double
- indice_urbain: double
- departement: text

### src_copro_epci_raw

- nom_reg: text
- code_reg: text
- nom_dep: text
- code_dep: text
- code_epci: text
- nom_epci: text
- nb_copros: integer
- nb_logements: integer
- copros_5_moins: integer
- copros_6_10: integer
- copros_11_20: integer
- copros_21_50: integer
- copros_51_200: integer
- copros_200_plus: integer
- copros_avant_49: integer
- copros_49_74: integer
- copros_75_2000: integer
- copros_2000_plus: integer
- copros_annee_na: integer
- taux_immat: double

### tr_copro_epci

- nom_epci: text
- nb_coproprietes: integer
- niveau: text

## Relations (logiques)

- code_commune relie src_communes, src_logement, tr_communes et kpi_communes.
- departement_code est derive de code_commune (2 premiers caracteres) et alimente kpi_departements.

## Notes d'exploitation

- Le dashboard charge kpi_communes (score pre-calcule avec ponderations 0.45 / 0.35 / 0.20).
- Pour changer les ponderations, modifier compute_score dans app/real_data_utils.py puis relancer app/rebuild_db.py.
- Les tables kpi_* sont regenerees lors d'un rebuild complet.
- La vue principale affiche carte + KPIs sans scroll, les tableaux sont dans l'onglet "Tableaux & analyses".
- Les tables optionnelles sont chargees automatiquement si les CSV sont presents dans DATA.
