"""
╔══════════════════════════════════════════════════════════════════╗
║  main.py — Page d'accueil, navigation, guide en bulles           ║
║  Run : streamlit run main.py                                     ║
╚══════════════════════════════════════════════════════════════════╝
"""
import streamlit as st

st.set_page_config(
    page_title="Système Anti-Décrochage",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

from app_config import (
    inject_css, render_topbar, section_header, sidebar_kpis,
    load_predictions, compute_kpis, guide_tooltip, guide_banner,
    BG_TOPBAR, BG_PAGE, BG_CARD, BORDER, T_WHITE, T_DARK, T_MID, T_LIGHT,
    C_COBALT, C_CORAL, C_AMBER, C_EMERALD, C_VIOLET,
)

inject_css()

# ── CSS spécifique à la home ──────────────────────────────────────
st.markdown(f"""
<style>
.hero {{
    background: linear-gradient(135deg, #0F172A 0%, #1B4FD8 55%, #0F172A 100%);
    border-radius: 22px; padding: 54px 52px;
    margin-bottom: 32px; position: relative; overflow: hidden;
    box-shadow: 0 12px 48px rgba(27,79,216,0.22);
}}
.hero::before {{
    content:''; position:absolute; top:-80px; right:-40px;
    width:380px; height:380px; border-radius:50%;
    background:radial-gradient(circle, rgba(27,79,216,0.3) 0%, transparent 70%);
}}
.hero::after {{
    content:''; position:absolute; bottom:-100px; left:30%;
    width:420px; height:420px; border-radius:50%;
    background:radial-gradient(circle, rgba(5,150,105,0.18) 0%, transparent 70%);
}}
.hero-content {{ position:relative; z-index:2; }}
.hero-eyebrow {{
    font-size:10px; font-weight:700; letter-spacing:3.5px;
    text-transform:uppercase; color:rgba(248,250,252,0.38);
    font-family:'JetBrains Mono',monospace; margin-bottom:16px;
    display:flex; align-items:center; gap:12px;
}}
.hero-eyebrow::before {{
    content:''; width:32px; height:1px; background:rgba(248,250,252,0.22);
}}
.hero-title {{
    font-size:46px; font-weight:900; color:#F8FAFC;
    line-height:1.06; margin-bottom:16px; letter-spacing:-2px;
}}
.hero-title em {{ color:#34D399; font-style:normal; }}
.hero-desc {{
    font-size:15px; color:rgba(248,250,252,0.55);
    max-width:580px; line-height:1.8; margin-bottom:36px; font-weight:400;
}}
.hero-pills {{ display:flex; gap:10px; flex-wrap:wrap; }}
.hero-pill {{
    padding:7px 16px; border-radius:20px;
    font-size:11px; font-weight:700; letter-spacing:.8px;
    font-family:'JetBrains Mono',monospace;
    display:inline-flex; align-items:center; gap:8px;
}}
.hp-cobalt  {{ background:rgba(27,79,216,0.3);  border:1px solid rgba(27,79,216,0.6);  color:#93C5FD; }}
.hp-emerald {{ background:rgba(5,150,105,0.2);  border:1px solid rgba(5,150,105,0.45); color:#6EE7B7; }}
.hp-emerald::before {{
    content:''; width:6px; height:6px; border-radius:50%;
    background:#6EE7B7; animation:blink 2s infinite;
}}
.hp-coral {{ background:rgba(220,38,38,0.2); border:1px solid rgba(220,38,38,0.45); color:#FCA5A5; }}

/* Nav Cards */
.nav-card {{
    background:{BG_CARD}; border:1px solid {BORDER};
    border-radius:20px; padding:30px 28px 36px;
    box-shadow:0 2px 12px rgba(15,23,42,0.06);
    transition:all .25s ease; position:relative; overflow:hidden; height:100%;
}}
.nav-card:hover {{
    transform:translateY(-6px);
    box-shadow:0 18px 40px rgba(15,23,42,0.12);
}}
.nav-accent {{
    position:absolute; top:0; left:0; right:0;
    height:5px; border-radius:20px 20px 0 0;
}}
.nav-icon {{ font-size:42px; margin-bottom:16px; display:block; }}
.nav-title {{
    font-size:20px; font-weight:800; color:{T_DARK};
    margin-bottom:10px; letter-spacing:-.4px;
}}
.nav-desc {{ font-size:13px; color:{T_MID}; line-height:1.7; margin-bottom:18px; }}
.nav-tags {{ display:flex; flex-wrap:wrap; gap:6px; margin-bottom:12px; }}
.nav-tag {{
    padding:4px 11px; border-radius:8px;
    font-size:10px; font-weight:700; letter-spacing:.5px;
    font-family:'JetBrains Mono',monospace;
}}
.nav-arrow {{
    position:absolute; bottom:26px; right:26px;
    font-size:20px; color:{T_LIGHT}; transition:all .2s;
}}
.nav-card:hover .nav-arrow {{ color:{C_COBALT}; transform:translateX(6px); }}

/* Stat box */
.stat-box {{
    background:{BG_CARD}; border:1px solid {BORDER};
    border-radius:12px; padding:16px 18px;
    text-align:center;
}}
.stat-box-val {{
    font-size:28px; font-weight:800; letter-spacing:-1px;
    font-family:'JetBrains Mono',monospace; margin-bottom:4px;
}}
.stat-box-lbl {{
    font-size:10px; font-weight:700; letter-spacing:1.5px;
    text-transform:uppercase; color:{T_LIGHT};
}}
</style>
""", unsafe_allow_html=True)

# ── Données ───────────────────────────────────────────────────────
df   = load_predictions()
kpis = compute_kpis(df)
sidebar_kpis(kpis, "🎓", "Anti-Décrochage", "SYSTÈME DE MONITORING ML")

# ── Hero ──────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
  <div class="hero-content">
    <div class="hero-eyebrow">Système de Prédiction · ML Dashboard · Version Production</div>
    <div class="hero-title">
      Plateforme de Suivi<br>du <em>Décrochage Scolaire</em>
    </div>
    <div class="hero-desc">
      Détectez les étudiants à risque avant qu'il ne soit trop tard.
      Diagnostics ML personnalisés, analyses SHAP explicatives,
      explorations par filière et tableaux de bord avancés.
    </div>
    <div class="hero-pills">
      <span class="hero-pill hp-cobalt">⚙️ Machine Learning</span>
      <span class="hero-pill hp-emerald">Temps Réel</span>
      <span class="hero-pill hp-coral">🎓 {kpis['total']:,} étudiants</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Guide d'utilisation ───────────────────────────────────────────
guide_banner(
    "Comment utiliser ce tableau de bord ?",
    "Ce système analyse les données académiques pour prédire le risque de décrochage. "
    "Survolez les icônes <b>?</b> dans chaque section pour comprendre comment lire les données.",
    steps=[
        "Consultez les KPI globaux",
        "Explorez la Vue Globale",
        "Analysez les profils individuels",
        "Comparez les filières",
        "Générez les rapports PDF",
    ]
)

st.markdown("<br>", unsafe_allow_html=True)

# ── KPI Snapshot ─────────────────────────────────────────────────
section_header(
    "📡", "Snapshot en Temps Réel",
    guide_title="Indicateurs clés",
    guide_text="Ces 5 chiffres résument l'état actuel de la population. "
               "🔴 Rouge = intervention urgente. 🟠 Orange = surveillance. 🟢 Vert = stable."
)

if kpis["pct_rouge"] >= 20:
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:14px;background:rgba(220,38,38,0.05);
                border:1px solid rgba(220,38,38,0.2);border-radius:12px;padding:14px 20px;
                margin-bottom:16px;">
      <div style="width:10px;height:10px;border-radius:50%;background:{C_CORAL};
                  flex-shrink:0;animation:blink 2s infinite;"></div>
      <div style="font-size:13px;color:{T_DARK};font-weight:500;">
        <b style="color:{C_CORAL};">{kpis['rouge']} étudiants</b> sont en zone rouge
        ({kpis['pct_rouge']}%) — une intervention immédiate est recommandée.
      </div>
    </div>
    """, unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5, gap="small")
snap = [
    (c1, "cobalt",  "👥", "Total Étudiants",  kpis["total"],       "effectif complet",                         100),
    (c2, "coral",   "🔴", "Zone Rouge",        kpis["rouge"],       f"{kpis['pct_rouge']}% · Risque élevé",    kpis["pct_rouge"]),
    (c3, "amber",   "🟠", "Zone Orange",       kpis["orange"],      f"{kpis['pct_orange']}% · Surveillance",   kpis["pct_orange"]),
    (c4, "emerald", "🟢", "Zone Verte",        kpis["vert"],        f"{kpis['pct_vert']}% · Stable",           kpis["pct_vert"]),
    (c5, "violet",  "📉", "Taux Décrochage",   f"{kpis['taux']}%", f"{kpis['dropout']} Dropout prédits",       kpis["taux"]),
]
for col, cls, ico, lbl, val, sub, bar_w in snap:
    with col:
        st.markdown(f"""
        <div class="kpi {cls}">
          <span class="kpi-bg-icon">{ico}</span>
          <div class="kpi-label">{lbl}</div>
          <div class="kpi-val {cls}">{val}</div>
          <div class="kpi-sub">{ico} {sub}</div>
          <div class="kpi-bar-bg">
            <div class="kpi-bar {cls}" style="width:{bar_w}%"></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Navigation Cards ──────────────────────────────────────────────
section_header("🗺️", "Modules du Dashboard")

# ─── 5 colonnes pour les 5 modules ───────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5, gap="large")

with col1:
    st.markdown(f"""
    <div class="nav-card">
      <div class="nav-accent" style="background:linear-gradient(90deg,{C_COBALT},{C_COBALT}77);"></div>
      <span class="nav-icon">📊</span>
      <div class="nav-title">Vue Globale</div>
      <div class="nav-desc">
        Dashboard principal : KPI complets, distribution des scores de risque,
        répartition rouge/orange/vert, matrice de confusion ML,
        Top 10 des étudiants les plus à risque et filtres avancés.
      </div>
      <div class="nav-tags">
        <span class="nav-tag" style="background:rgba(27,79,216,0.09);color:{C_COBALT};">KPI</span>
        <span class="nav-tag" style="background:rgba(27,79,216,0.09);color:{C_COBALT};">Distribution</span>
        <span class="nav-tag" style="background:rgba(27,79,216,0.09);color:{C_COBALT};">Matrice ML</span>
        <span class="nav-tag" style="background:rgba(27,79,216,0.09);color:{C_COBALT};">Top 10</span>
      </div>
      <span class="nav-arrow">→</span>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/01_Vue_Globale.py", label="📊 Ouvrir la Vue Globale", use_container_width=True)

with col2:
    st.markdown(f"""
    <div class="nav-card">
      <div class="nav-accent" style="background:linear-gradient(90deg,{C_AMBER},{C_AMBER}77);"></div>
      <span class="nav-icon">👤</span>
      <div class="nav-title">Vue Individuelle</div>
      <div class="nav-desc">
        Profil complet par étudiant : jauge de risque personnalisée,
        facteurs SHAP explicatifs, historique académique S1/S2,
        recommandations d'intervention et export PDF officiel.
      </div>
      <div class="nav-tags">
        <span class="nav-tag" style="background:rgba(217,119,6,0.09);color:{C_AMBER};">Profil</span>
        <span class="nav-tag" style="background:rgba(217,119,6,0.09);color:{C_AMBER};">SHAP</span>
        <span class="nav-tag" style="background:rgba(217,119,6,0.09);color:{C_AMBER};">Académique</span>
        <span class="nav-tag" style="background:rgba(217,119,6,0.09);color:{C_AMBER};">📄 PDF</span>
      </div>
      <span class="nav-arrow">→</span>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/02_Vue_Individuelle.py", label="👤 Ouvrir la Vue Individuelle", use_container_width=True)

with col3:
    st.markdown(f"""
    <div class="nav-card">
      <div class="nav-accent" style="background:linear-gradient(90deg,{C_CORAL},{C_CORAL}77);"></div>
      <span class="nav-icon">🏫</span>
      <div class="nav-title">Vue par Filière</div>
      <div class="nav-desc">
        Comparaison inter-filières : taux de décrochage par programme,
        score moyen, radar Top 5 filières à risque,
        filtres dynamiques et export CSV des données.
      </div>
      <div class="nav-tags">
        <span class="nav-tag" style="background:rgba(220,38,38,0.09);color:{C_CORAL};">Filières</span>
        <span class="nav-tag" style="background:rgba(220,38,38,0.09);color:{C_CORAL};">Radar</span>
        <span class="nav-tag" style="background:rgba(220,38,38,0.09);color:{C_CORAL};">Tendances</span>
        <span class="nav-tag" style="background:rgba(220,38,38,0.09);color:{C_CORAL};">Export CSV</span>
      </div>
      <span class="nav-arrow">→</span>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/03_Vue_Par_Filiere.py", label="🏫 Ouvrir la Vue par Filière", use_container_width=True)

with col4:
    st.markdown(f"""
    <div class="nav-card">
      <div class="nav-accent" style="background:linear-gradient(90deg,{C_VIOLET},{C_VIOLET}77);"></div>
      <span class="nav-icon">🤖</span>
      <div class="nav-title">Chatbot Conseiller</div>
      <div class="nav-desc">
        Assistant IA pédagogique : expliquez le risque d'un étudiant,
        obtenez des recommandations d'intervention concrètes et
        interrogez les statistiques globales en langage naturel.
      </div>
      <div class="nav-tags">
        <span class="nav-tag" style="background:rgba(109,40,217,0.09);color:{C_VIOLET};">Groq AI</span>
        <span class="nav-tag" style="background:rgba(109,40,217,0.09);color:{C_VIOLET};">SHAP Chat</span>
        <span class="nav-tag" style="background:rgba(109,40,217,0.09);color:{C_VIOLET};">Mémoire</span>
        <span class="nav-tag" style="background:rgba(109,40,217,0.09);color:{C_VIOLET};">Stats</span>
      </div>
      <span class="nav-arrow">→</span>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/04_Chatbot.py", label="🤖 Ouvrir le Chatbot", use_container_width=True)

# ─── NOUVELLE CARTE : Rapports PDF ───────────────────────────────
with col5:
    st.markdown(f"""
    <div class="nav-card">
      <div class="nav-accent" style="background:linear-gradient(90deg,{C_EMERALD},{C_EMERALD}77);"></div>
      <span class="nav-icon">📄</span>
      <div class="nav-title">Rapports PDF</div>
      <div class="nav-desc">
        Génération automatique de fiches individuelles : score,
        niveau d'alerte, top 5 SHAP, graphiques d'évolution académique
        et recommandations. Export en lot ZIP pour toute une zone.
      </div>
      <div class="nav-tags">
        <span class="nav-tag" style="background:rgba(5,150,105,0.09);color:{C_EMERALD};">Fiche PDF</span>
        <span class="nav-tag" style="background:rgba(5,150,105,0.09);color:{C_EMERALD};">Top 5 SHAP</span>
        <span class="nav-tag" style="background:rgba(5,150,105,0.09);color:{C_EMERALD};">Graphiques</span>
        <span class="nav-tag" style="background:rgba(5,150,105,0.09);color:{C_EMERALD};">📦 ZIP Lot</span>
      </div>
      <span class="nav-arrow">→</span>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/05 rapports.py", label="📄 Ouvrir les Rapports PDF", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Légende des zones ─────────────────────────────────────────────
section_header(
    "🎯", "Guide de Lecture des Zones",
    guide_title="Comment interpréter les zones ?",
    guide_text="Le modèle ML calcule un score de 0 à 100. Plus le score est élevé, "
               "plus le risque de décrochage est grand. Les seuils sont calibrés sur les données historiques."
)

z1, z2, z3 = st.columns(3, gap="medium")

with z1:
    st.markdown(f"""
    <div style="background:{BG_CARD};border:1px solid {BORDER};border-left:5px solid {C_CORAL};
                border-radius:12px;padding:20px 22px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
            <span style="font-size:20px;">🔴</span>
            <div>
                <div style="font-size:15px;font-weight:800;color:{C_CORAL};">Zone Rouge</div>
                <div style="font-size:10px;font-family:'JetBrains Mono',monospace;
                            color:{T_LIGHT};letter-spacing:1px;">SCORE ≥ 70%</div>
            </div>
        </div>
        <div style="font-size:12px;color:{T_MID};line-height:1.7;">
            Risque élevé de décrochage. Une <b>intervention immédiate</b> est nécessaire
            dans les 48h. Contacter le conseiller pédagogique et la famille.
        </div>
    </div>
    """, unsafe_allow_html=True)

with z2:
    st.markdown(f"""
    <div style="background:{BG_CARD};border:1px solid {BORDER};border-left:5px solid {C_AMBER};
                border-radius:12px;padding:20px 22px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
            <span style="font-size:20px;">🟠</span>
            <div>
                <div style="font-size:15px;font-weight:800;color:{C_AMBER};">Zone Orange</div>
                <div style="font-size:10px;font-family:'JetBrains Mono',monospace;
                            color:{T_LIGHT};letter-spacing:1px;">SCORE 40–70%</div>
            </div>
        </div>
        <div style="font-size:12px;color:{T_MID};line-height:1.7;">
            Surveillance renforcée requise. Augmenter la <b>fréquence des points de suivi</b>.
            Proposer un tutorat ou un accompagnement ciblé.
        </div>
    </div>
    """, unsafe_allow_html=True)

with z3:
    st.markdown(f"""
    <div style="background:{BG_CARD};border:1px solid {BORDER};border-left:5px solid {C_EMERALD};
                border-radius:12px;padding:20px 22px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
            <span style="font-size:20px;">🟢</span>
            <div>
                <div style="font-size:15px;font-weight:800;color:{C_EMERALD};">Zone Verte</div>
                <div style="font-size:10px;font-family:'JetBrains Mono',monospace;
                            color:{T_LIGHT};letter-spacing:1px;">SCORE &lt; 40%</div>
            </div>
        </div>
        <div style="font-size:12px;color:{T_MID};line-height:1.7;">
            Situation stable. Maintenir le <b>suivi mensuel habituel</b>.
            Encourager la participation aux activités parascolaires.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Structure du projet ───────────────────────────────────────────
section_header("📁", "Architecture du Projet")

with st.expander("Voir la structure des fichiers"):
    st.markdown(f"""
    <div class="glass-card">
    <pre style="font-family:'JetBrains Mono',monospace; font-size:12px; color:{T_MID};
                background:{BG_PAGE}; border:1px solid {BORDER}; border-radius:10px;
                padding:16px; line-height:2.2; overflow-x:auto; margin:0;">
Projet_Decrochage/
├── <b style="color:{C_COBALT};">main.py</b>              ← Accueil · Guide · Navigation
├── <b style="color:{C_COBALT};">app_config.py</b>        ← Palette · CSS · Tooltips · DB
├── students.db          ← Base de données SQLite
│
└── pages/
    ├── <b style="color:{C_COBALT};">01_Vue_Globale.py</b>      ← KPI · Graphiques · Top 10 · Filtres
    ├── <b style="color:{C_AMBER};">02_Vue_Individuelle.py</b>  ← Profil · SHAP · Académique · PDF
    ├── <b style="color:{C_CORAL};">03_Vue_Par_Filiere.py</b>   ← Filières · Radar · Export CSV
    ├── <b style="color:{C_VIOLET};">04_Chatbot.py</b>          ← Assistant IA · SHAP · Recommandations
    └── <b style="color:{C_EMERALD};">05 rapports.py</b>    ← Fiches PDF · SHAP · Graphiques · ZIP
    </pre>
    </div>
    """, unsafe_allow_html=True)
    st.code("streamlit run main.py", language="bash")

# ── Footer ────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"""
<div class="page-footer">
    Système Anti-Décrochage Scolaire &nbsp;·&nbsp;
    {kpis['total']:,} étudiants &nbsp;·&nbsp; Machine Learning &nbsp;·&nbsp; Streamlit
</div>
""", unsafe_allow_html=True)