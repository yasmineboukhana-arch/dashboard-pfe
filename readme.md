<div align="center">

# 🎓 Système Intelligent de Prédiction et de Suivi du Décrochage Scolaire

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Cloud-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![XGBoost](https://img.shields.io/badge/XGBoost-ML_Model-006400?style=for-the-badge)](https://xgboost.readthedocs.io/)
[![SHAP](https://img.shields.io/badge/SHAP-Explicabilité-orange?style=for-the-badge)](https://shap.readthedocs.io/)
[![Gemini](https://img.shields.io/badge/Gemini_API-Chatbot-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

**Projet de Fin d'Études (PFE) — Data Science**

*Un tableau de bord intelligent combinant Machine Learning, explicabilité SHAP et assistance pédagogique par IA pour détecter et prévenir le décrochage scolaire.*

</div>

---

## 📋 Table des matières

- [Aperçu du projet](#-aperçu-du-projet)
- [Fonctionnalités principales](#-fonctionnalités-principales)
- [Architecture technique](#-architecture-technique)
- [Structure du dépôt](#-structure-du-dépôt)
- [Installation et exécution locale](#-installation-et-exécution-locale)
- [Déploiement sur Streamlit Cloud](#-déploiement-sur-streamlit-cloud)
- [Les 3 pages du dashboard](#-les-3-pages-du-dashboard)
- [Explicabilité avec SHAP](#-explicabilité-avec-shap)
- [Chatbot pédagogique Gemini](#-chatbot-pédagogique-gemini)
- [Génération de rapports PDF](#-génération-de-rapports-pdf)
- [Auteure](#-auteure)

---

## 🔭 Aperçu du projet

Le décrochage scolaire est un enjeu majeur dans l'enseignement supérieur. Ce projet propose une solution complète et intelligente permettant aux établissements d'identifier **en temps réel** les étudiants à risque, de comprendre les facteurs déterminants et d'engager des actions préventives personnalisées.

L'application s'appuie sur des modèles de Machine Learning supervisé entraînés sur des données académiques, enrichis par une couche d'explicabilité (SHAP), et présentés au travers d'un dashboard interactif Streamlit accessible en ligne.

---

## ✨ Fonctionnalités principales

| Fonctionnalité | Description |
|---|---|
| 🤖 **Prédiction ML** | Modèles XGBoost & Random Forest avec rééchantillonnage SMOTE pour classes déséquilibrées |
| 🔍 **Explicabilité SHAP** | Visualisation des facteurs de risque au niveau global et individuel |
| 📊 **Dashboard 3 vues** | Vue globale, Vue par étudiant (ID), Vue par filière |
| 🚨 **Alertes colorées** | Système de feux tricolores (🟢 Faible / 🟡 Modéré / 🔴 Élevé) |
| 💬 **Chatbot Gemini** | Assistant pédagogique IA basé sur l'API Google Gemini |
| 📄 **Rapports PDF** | Fiches de suivi individuelles générées automatiquement avec ReportLab |

---

## 🏗️ Architecture technique

```
Données brutes (CSV)
        │
        ▼
┌───────────────────┐
│  Prétraitement    │  ←  Nettoyage, encodage, normalisation
│  & Feature Eng.  │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐        ┌─────────────┐
│  Modèles ML       │        │    SMOTE    │
│  XGBoost / RF     │ ←───── │ (équilibrage│
│                   │        │  des classes│
└────────┬──────────┘        └─────────────┘
         │
         ▼
┌───────────────────┐        ┌─────────────────┐
│  SHAP Values      │        │  Google Gemini  │
│  (Explicabilité)  │        │  API (Chatbot)  │
└────────┬──────────┘        └────────┬────────┘
         │                            │
         ▼                            ▼
┌────────────────────────────────────────────┐
│          Dashboard Streamlit               │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │  Vue     │ │  Vue     │ │  Vue par  │  │
│  │ Globale  │ │  Ind.    │ │  Filière  │  │
│  └──────────┘ └──────────┘ └───────────┘  │
└────────────────────┬───────────────────────┘
                     │
                     ▼
             ┌───────────────┐
             │  Rapport PDF  │
             │  (ReportLab)  │
             └───────────────┘
```

---

## 📁 Structure du dépôt

```
dashboard-pfe/
│
├── main.py                    # Point d'entrée principal de l'application
├── requirements.txt           # Dépendances Python
├── README.md                  # Documentation du projet
│
├── data/
│   ├── raw/                   # Données brutes (non versionnées)
│   └── processed/             # Données prétraitées
│
├── models/
│   ├── xgboost_model.pkl      # Modèle XGBoost sauvegardé
│   ├── rf_model.pkl           # Modèle Random Forest sauvegardé
│   └── scaler.pkl             # StandardScaler sauvegardé
│
├── pages/
│   ├── vue_globale.py         # Page 1 — Vue d'ensemble & statistiques
│   ├── vue_individuelle.py    # Page 2 — Profil étudiant par ID
│   └── vue_filiere.py         # Page 3 — Analyse par filière
│
├── utils/
│   ├── preprocessing.py       # Fonctions de prétraitement
│   ├── prediction.py          # Logique de prédiction
│   ├── shap_utils.py          # Calcul et visualisation SHAP
│   ├── pdf_generator.py       # Génération de rapports PDF
│   └── chatbot.py             # Intégration API Google Gemini
│
├── assets/
│   └── logo.png               # Ressources visuelles
│
└── .streamlit/
    └── secrets.toml           # Clés API (non versionnées — voir .gitignore)
```

---

## 🚀 Installation et exécution locale

### Prérequis

- Python 3.10 ou supérieur
- Une clé API Google Gemini (obtenue sur [Google AI Studio](https://aistudio.google.com/))

### Étapes

```bash
# 1. Cloner le dépôt
git clone https://github.com/yasmineboukhana-arch/dashboard-pfe.git
cd dashboard-pfe

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate        # Linux / macOS
# .\venv\Scripts\activate       # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les secrets (clé Gemini)
mkdir -p .streamlit
echo '[api_keys]
GEMINI_API_KEY = "votre_cle_api_ici"' > .streamlit/secrets.toml

# 5. Lancer l'application
streamlit run main.py
```

L'application sera accessible à l'adresse : **http://localhost:8501**

---

## ☁️ Déploiement sur Streamlit Cloud

L'application est déployée et accessible publiquement via **Streamlit Cloud** à partir de ce dépôt :

- **Dépôt** : `yasmineboukhana-arch/dashboard-pfe`
- **Branche** : `main`
- **Fichier principal** : `main.py`

> 🔐 La clé API Google Gemini est configurée via les **Secrets** de Streamlit Cloud (Settings → Secrets) et n'est **jamais** exposée dans le code source.

---

## 📊 Les 3 pages du dashboard

### 🌐 Page 1 — Vue Globale
- Distribution des niveaux de risque dans l'établissement
- Indicateurs clés (KPIs) : taux de décrochage prédit, répartition par niveau
- Graphiques de tendance et histogrammes
- Tableau récapitulatif exportable

### 👤 Page 2 — Vue Individuelle (par ID étudiant)
- Recherche d'un étudiant par son identifiant
- Score de risque personnalisé avec badge coloré (🟢 / 🟡 / 🔴)
- Facteurs SHAP les plus influents pour cet étudiant
- Accès au chatbot Gemini pour des conseils personnalisés
- Génération de la fiche de suivi PDF individuelle

### 🏫 Page 3 — Vue par Filière
- Comparaison des niveaux de risque entre filières
- Classement des filières les plus à risque
- Analyse des variables discriminantes par filière
- Graphiques interactifs (Plotly)

---

## 🔍 Explicabilité avec SHAP

L'intégration de **SHAP (SHapley Additive exPlanations)** permet de dépasser la simple prédiction pour offrir une explication transparente et auditable de chaque décision du modèle.

- **Beeswarm plot** : vue globale des variables les plus impactantes
- **Waterfall plot** : décomposition du score de risque individuel
- **Force plot** : visualisation interactive contribution par contribution

> *"Pourquoi cet étudiant est-il classé à risque élevé ?"* — SHAP répond à cette question avec précision.

---

## 💬 Chatbot pédagogique Gemini

Un assistant conversationnel alimenté par **Google Gemini** est intégré directement dans la vue individuelle. Il permet à un conseiller pédagogique de :

- Obtenir une **analyse contextuelle** du profil de l'étudiant
- Recevoir des **recommandations d'accompagnement** adaptées
- Formuler des **plans d'action** concrets (tutorat, soutien psychologique, etc.)

Le chatbot reçoit automatiquement le profil de l'étudiant (score de risque, facteurs SHAP) comme contexte afin de générer des réponses pertinentes et personnalisées.

---

## 📄 Génération de rapports PDF

Chaque étudiant peut faire l'objet d'une **fiche de suivi individuelle** générée en un clic, incluant :

- Informations académiques de l'étudiant
- Score de risque et niveau d'alerte
- Top 5 des facteurs de risque identifiés par SHAP
- Recommandations pédagogiques générées par Gemini
- Date de génération et signature de l'encadrant

La génération est assurée par la bibliothèque **ReportLab**, garantissant des PDFs propres et formatés.

---

## 👩‍💻 Auteure

**Yasmine Boukhana**
Étudiante en Data Science — Projet de Fin d'Études

[![GitHub](https://img.shields.io/badge/GitHub-yasmineboukhana--arch-181717?style=flat-square&logo=github)](https://github.com/yasmineboukhana-arch)

---

<div align="center">
  <i>Projet réalisé dans le cadre du Projet de Fin d'Études (PFE) en Data Science.</i>
</div>
