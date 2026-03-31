# 🚗 Projet Parkshare : Analyse du Parc Immobilier et Potentiel de Mobilité en Île-de-France

NB: ce fichier README est la car demander dans le cahier des charge mais mon fichier notebook ( analytics.ipynb) est plus detailer


Ce projet s'appuie sur un script Python (Jupyter Notebook
`analytics.ipynb`) visant à identifier les zones à fort potentiel pour
le déploiement d'une solution de parking partagé (**Parkshare**) en
Île-de-France.

En croisant des données démographiques, des statistiques sur les
logements et des informations sur les copropriétés, ce modèle calcule un
**Score d'Opportunité** pour chaque commune francilienne.

------------------------------------------------------------------------

## 🎯 Pourquoi le focus sur l'Île-de-France ?

Le choix de restreindre l'analyse à la région **Île-de-France**
(départements 75, 77, 78, 91, 92, 93, 94, 95) repose sur des arguments
stratégiques forts :

1.  **Un vivier de données massif** : Avec plus de 1 200 communes et 5
    000 IRIS, l'Île-de-France offre une granularité et une concentration
    de données uniques pour modéliser des comportements urbains
    complexes.
2.  **Le défi de la mobilité et du stationnement** : Des recherches
    approfondies montrent que dans le **Top 5 des départements français
    comptant le plus de véhicules, trois se situent en Île-de-France**.

------------------------------------------------------------------------

## 🗂️ Sources des Données

1.  **Référentiel Communes (2025)** : `communes-france-2025.csv`\
2.  **Base Logement INSEE (2022)** : `base-ic-logement-2022.CSV`\
3.  **Copropriétés par EPCI (2024)** :
    `tableau-synthetique-coproff-epci-2024.csv`

------------------------------------------------------------------------

## ⚙️ Méthodologie et Ingénierie des Données

### Indicateurs Clés

-   **Ratio Collectif** = Résidences Principales / Logements\
-   **Tension Parking** = Population / Logements\
-   **Indice Urbain** = Population × Ratio Collectif

### Score Parkshare

Score = (Population × 0.4) + (Ratio Collectif × 0.3) + (Tension Parking
× 0.3)

------------------------------------------------------------------------

## 📈 Résultats

-   Boulogne-Billancourt en tête\
-   Forte opportunité en petite couronne (92, 93)\
-   Score corrélé à la population

------------------------------------------------------------------------

## 📂 Exports

-   donnees_clean_idf.csv\
-   communes_idf_clean.csv\
-   logement_idf_clean.csv\
-   copro_epci_clean.csv

------------------------------------------------------------------------

## 💻 Prérequis

-   Python 3.x\
-   pandas\
-   matplotlib\
-   seaborn
