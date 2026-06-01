"""
╔══════════════════════════════════════════════════════════════════╗
║  pages/01_Vue_Globale.py  — KPI · Distribution · Top 10         ║
║  Version avancée avec guide en bulles                            ║
╚══════════════════════════════════════════════════════════════════╝
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from app_config import (
    inject_css, render_topbar, section_header, sidebar_kpis,
    load_predictions, compute_kpis, top3_shap, guide_banner, guide_tooltip,
    badge_alert, badge_pred, rank_badge, score_color, hex_rgba,
    BG_CARD, BG_PAGE, BG_SIDEBAR, BORDER, T_DARK, T_MID, T_LIGHT, T_WHITE,
    C_COBALT, C_CORAL, C_AMBER, C_EMERALD, C_VIOLET,
    AXIS_STYLE, base_layout, DB_PATH,
)

# ─────────────────────────────────────────────────────────────────
inject_css()
df   = load_predictions(DB_PATH)
kpis = compute_kpis(df)
sidebar_kpis(kpis, "📊", "Vue Globale", "KPI · DISTRIBUTION · TOP 10")
render_topbar("📊", "Monitoring Décrochage — Vue Globale",
              "KPI · Distribution des Scores · Matrice ML · Top 10 · Filtres", kpis["total"])

# ═════════════════════════════════════════════════════════════════
# SECTION A — KPI CARDS
# ═════════════════════════════════════════════════════════════════
section_header(
    "📌", "Indicateurs Clés de Performance",
    guide_title="Comment lire les KPI ?",
    guide_text="Chaque carte affiche un indicateur clé. La barre colorée en bas "
               "représente le pourcentage par rapport au total. Survolez les barres "
               "pour voir les détails."
)

c1, c2, c3, c4, c5 = st.columns(5, gap="small")
kpi_data = [
    (c1, "cobalt",  "👥", "Total Étudiants",  kpis["total"],       "effectif complet",                        100),
    (c2, "coral",   "🔴", "Zone Rouge",        kpis["rouge"],       f"{kpis['pct_rouge']}% · Risque élevé",   kpis["pct_rouge"]),
    (c3, "amber",   "🟠", "Zone Orange",       kpis["orange"],      f"{kpis['pct_orange']}% · Surveillance",  kpis["pct_orange"]),
    (c4, "emerald", "🟢", "Zone Verte",        kpis["vert"],        f"{kpis['pct_vert']}% · Stable",          kpis["pct_vert"]),
    (c5, "violet",  "📉", "Taux Décrochage",   f"{kpis['taux']}%", f"{kpis['dropout']} Dropout prédits",      kpis["taux"]),
]
for col, cls, ico, lbl, val, sub, bar_w in kpi_data:
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
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════
# SECTION B — BARRE D'ALERTES
# ═════════════════════════════════════════════════════════════════
section_header(
    "🎚️", "Répartition Proportionnelle des Alertes",
    guide_title="Barre proportionnelle",
    guide_text="La largeur de chaque segment est proportionnelle au nombre d'étudiants. "
               "Rouge à gauche = plus urgents. Les chiffres exactes sont sous la barre."
)

data_bar = [
    ("rouge",  kpis["rouge"],  C_CORAL,   kpis["pct_rouge"]),
    ("orange", kpis["orange"], C_AMBER,   kpis["pct_orange"]),
    ("vert",   kpis["vert"],   C_EMERALD, kpis["pct_vert"]),
]
segs  = "".join(
    f'<div class="alert-seg" style="flex:{p};background:{c};" title="{k}: {n} ({p}%)"></div>'
    for k, n, c, p in data_bar
)
pills = "".join(
    f'<span class="stat-pill">'
    f'<span class="stat-dot" style="background:{c};"></span>'
    f'{k.capitalize()} : <b style="color:{c};margin-left:3px">{n}</b>'
    f'<span style="color:{T_LIGHT};margin-left:4px">({p}%)</span>'
    f'</span>'
    for k, n, c, p in data_bar
)
st.markdown(
    f'<div class="alert-bar-wrap">'
    f'<div class="alert-bar">{segs}</div>'
    f'<div class="stat-pills">{pills}</div>'
    f'</div>',
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════
# SECTION C — HISTOGRAMME + DONUT
# ═════════════════════════════════════════════════════════════════
section_header(
    "📈", "Distribution des Scores de Risque",
    guide_title="Lire la distribution",
    guide_text="L'histogramme montre combien d'étudiants ont un score dans chaque tranche. "
               "Un pic à droite (>70%) signale beaucoup d'étudiants en danger. "
               "Le donut montre la répartition globale des 3 zones."
)


def plot_histogram(df: pd.DataFrame) -> go.Figure:
    fig = px.histogram(
        df, x="score_pct", nbins=32,
        labels={"score_pct": "Score de risque (%)", "count": "Étudiants"},
        title="<b>Distribution des Scores de Risque</b>",
    )
    fig.update_traces(
        marker=dict(color=C_COBALT, line=dict(color="white", width=.5), opacity=.80),
        hovertemplate="Score %{x:.0f}% — %{y} étudiants<extra></extra>",
    )
    fig.add_vrect(x0=0,  x1=40,  fillcolor=hex_rgba(C_EMERALD, 0.06), line_width=0)
    fig.add_vrect(x0=40, x1=70,  fillcolor=hex_rgba(C_AMBER,   0.06), line_width=0)
    fig.add_vrect(x0=70, x1=100, fillcolor=hex_rgba(C_CORAL,   0.06), line_width=0)
    for x, c, lbl in [(40, C_AMBER, "Seuil Orange"), (70, C_CORAL, "Seuil Critique")]:
        fig.add_vline(x=x, line_dash="dash", line_color=c, line_width=1.8,
                      annotation_text=lbl, annotation_position="top",
                      annotation_font=dict(color=c, size=10))
    fig.update_layout(**base_layout(
        title_font=dict(size=13, color=T_DARK),
        xaxis=dict(**AXIS_STYLE, range=[0, 100], title="Score de risque (%)"),
        yaxis=dict(**AXIS_STYLE, title="Nombre d'étudiants"),
        showlegend=False,
    ))
    return fig


def plot_donut(kpis: dict) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=["Rouge", "Orange", "Vert"],
        values=[kpis["rouge"], kpis["orange"], kpis["vert"]],
        marker=dict(colors=[C_CORAL, C_AMBER, C_EMERALD], line=dict(color="white", width=3)),
        hole=.62, textinfo="none", sort=False,
        hovertemplate="<b>%{label}</b><br>%{value} étudiants<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=BG_CARD,
        font=dict(family="Outfit, sans-serif", color=T_MID, size=12),
        margin=dict(l=10, r=10, t=44, b=30),
        title="<b>Répartition des Zones d'Alerte</b>",
        title_font=dict(size=13, color=T_DARK),
        legend=dict(font=dict(color=T_MID, size=12), bgcolor="rgba(0,0,0,0)",
                    orientation="h", yanchor="bottom", y=-0.18, xanchor="center", x=0.5),
        annotations=[dict(
            text=f"<b>{kpis['total']}</b><br><span style='font-size:11px;color:{T_LIGHT}'>étudiants</span>",
            x=0.5, y=0.5, showarrow=False, font=dict(color=T_DARK, size=18),
        )],
    )
    return fig


g1, g2 = st.columns([3, 2], gap="medium")
with g1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.plotly_chart(plot_histogram(df), use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

with g2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.plotly_chart(plot_donut(kpis), use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════
# SECTION D — ANALYSE MODÈLE
# ═════════════════════════════════════════════════════════════════
section_header(
    "🧮", "Analyse & Évaluation du Modèle ML",
    guide_title="Lire la matrice de confusion",
    guide_text="La diagonale (↘) = prédictions correctes. "
               "Hors diagonale = erreurs du modèle. "
               "Une case 'Dropout réel → prédit Graduate' foncée est critique : "
               "le modèle rate des décrocheurs réels."
)


def plot_pred_bar(df: pd.DataFrame) -> go.Figure:
    grp = df.groupby(["pred_label", "alert_level"]).size().reset_index(name="n")
    fig = px.bar(
        grp, x="pred_label", y="n", color="alert_level",
        color_discrete_map={"rouge": C_CORAL, "orange": C_AMBER, "vert": C_EMERALD},
        barmode="group",
        labels={"pred_label": "Prédiction", "n": "Étudiants", "alert_level": "Alerte"},
        title="<b>Prédictions × Niveau d'Alerte</b>",
        category_orders={
            "pred_label":  ["Graduate", "Enrolled", "Dropout"],
            "alert_level": ["vert", "orange", "rouge"],
        },
    )
    fig.update_layout(**base_layout(
        title_font=dict(size=13, color=T_DARK),
        xaxis=dict(**AXIS_STYLE),
        yaxis=dict(**AXIS_STYLE, title="Étudiants"),
        legend=dict(font=dict(color=T_MID), bgcolor="rgba(0,0,0,0)", title_text="",
                    orientation="h", yanchor="top", y=1.12, xanchor="right", x=1),
        bargap=.28, bargroupgap=.1,
    ))
    fig.update_traces(marker_line_width=0, opacity=.88)
    return fig


def plot_confusion(df: pd.DataFrame) -> go.Figure:
    labels = ["Graduate", "Enrolled", "Dropout"]
    matrix = [
        [int(((df["true_label"] == tl) & (df["pred_label"] == pl)).sum()) for pl in labels]
        for tl in labels
    ]
    fig = go.Figure(go.Heatmap(
        z=matrix, x=labels, y=labels,
        colorscale=[[0, BG_PAGE], [0.5, hex_rgba(C_COBALT, 0.45)], [1, C_COBALT]],
        text=[[str(v) for v in row] for row in matrix],
        texttemplate="%{text}", textfont=dict(size=14, color=T_DARK),
        hovertemplate="Réel: %{y}<br>Prédit: %{x}<br>%{z} étudiants<extra></extra>",
        showscale=False,
    ))
    fig.update_layout(**base_layout(
        title="<b>Matrice de Confusion</b>", title_font=dict(size=13, color=T_DARK),
        xaxis=dict(title="Prédit par le modèle", linecolor=BORDER, tickfont=dict(color=T_MID)),
        yaxis=dict(title="Réalité terrain",       linecolor=BORDER, tickfont=dict(color=T_MID)),
    ))
    return fig


def render_summary(df: pd.DataFrame, kpis: dict) -> None:
    items = [
        ("Score moyen global",   f"{kpis['score_moy']}%"),
        ("Moy. zone rouge",      f"{df[df['alert_level']=='rouge']['score_pct'].mean():.1f}%"),
        ("Moy. zone orange",     f"{df[df['alert_level']=='orange']['score_pct'].mean():.1f}%"),
        ("Moy. zone verte",      f"{df[df['alert_level']=='vert']['score_pct'].mean():.1f}%"),
        ("Précision du modèle",  f"{kpis['accuracy']}%"),
        ("Graduate prédits",     f"{kpis['graduate']}"),
        ("Enrolled prédits",     f"{kpis['enrolled']}"),
        ("Dropout prédits",      f"{kpis['dropout']}"),
    ]
    rows = "".join(
        f'<div class="summary-row">'
        f'<span class="summary-key">{k}</span>'
        f'<span class="summary-val">{v}</span>'
        f'</div>'
        for k, v in items
    )
    st.markdown(f'<div class="glass-card">{rows}</div>', unsafe_allow_html=True)


g3, g4, g5 = st.columns([2, 2, 1], gap="medium")
with g3:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.plotly_chart(plot_pred_bar(df), use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

with g4:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.plotly_chart(plot_confusion(df), use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

with g5:
    render_summary(df, kpis)

st.markdown("<br>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════
# SECTION E — TOP 10
# ═════════════════════════════════════════════════════════════════
section_header(
    "🚨", "Top 10 — Étudiants les Plus à Risque",
    guide_title="Lire le Top 10",
    guide_text="Classement par score décroissant. "
               "SHAP rouge = facteur qui aggrave le risque. "
               "SHAP vert = facteur protecteur. "
               "✅ Correcte = le modèle a bien prédit la situation réelle."
)


def render_top10(df_src: pd.DataFrame, n: int = 10) -> None:
    top = df_src.nlargest(n, "risk_score").reset_index(drop=True)
    rows = ""
    for i, row in top.iterrows():
        rank     = i + 1
        pct      = row["score_pct"]
        col      = score_color(pct)
        shap_lst = top3_shap(row.get("shap_values", "{}"))
        shap_html = " ".join(
            f'<span class="shap-{"pos" if v > 0 else "neg"}">{feat} {v:+.3f}</span>'
            for feat, v in shap_lst
        ) if shap_lst else f'<span style="color:{T_LIGHT};font-size:11px;">—</span>'
        correct = str(row.get("pred_label", "")) == str(row.get("true_label", ""))
        rows += f"""
        <tr>
            <td>{rank_badge(rank)}</td>
            <td><span class="stu-id">ETU-{int(row['student_id']):04d}</span></td>
            <td>
              <div class="score-bar-wrap">
                <div class="score-bar-bg">
                  <div class="score-bar-fill" style="width:{pct}%;background:{col};"></div>
                </div>
                <span class="score-txt">{pct:.1f}%</span>
              </div>
            </td>
            <td>{badge_alert(row['alert_level'])}</td>
            <td>{badge_pred(row['pred_label'])}</td>
            <td>{badge_pred(row['true_label'])}</td>
            <td style="font-size:12px;">{"✅" if correct else "❌"}</td>
            <td>{shap_html}</td>
        </tr>"""
    st.markdown(f"""
    <div class="top10-wrap">
    <table class="top10-table">
        <thead><tr>
          <th>Rang</th><th>ID Étudiant</th>
          <th style="min-width:160px">Score</th>
          <th>Alerte</th><th>Prédiction</th><th>Réalité</th>
          <th>Préd.</th><th>Top 3 SHAP</th>
        </tr></thead>
        <tbody>{rows}</tbody>
    </table>
    </div>""", unsafe_allow_html=True)


render_top10(df)

st.markdown("<br>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════
# SECTION F — FILTRES AVANCÉS
# ═════════════════════════════════════════════════════════════════
section_header(
    "🔍", "Exploration Avancée",
    guide_title="Filtres interactifs",
    guide_text="Combinez les filtres pour cibler une sous-population précise. "
               "Exemple : Score ≥ 60% + Zone Rouge + Prédit Dropout = "
               "les cas les plus urgents à traiter."
)

guide_banner(
    "Astuce — Exploration ciblée",
    "Utilisez les filtres ci-dessous pour identifier des sous-groupes spécifiques. "
    "Le tableau se met à jour automatiquement.",
    steps=["Choisir un seuil", "Sélectionner les alertes", "Filtrer par prédiction"]
)

st.markdown("<br style='margin:6px 0'>", unsafe_allow_html=True)

col_f1, col_f2, col_f3, col_f4 = st.columns([1.5, 1, 1, 0.5], gap="medium")
with col_f1:
    seuil = st.slider("Score minimum (%)", 0, 100, 70, 5)
with col_f2:
    alertes_sel = st.multiselect(
        "Niveau d'alerte",
        options=["rouge", "orange", "vert"],
        default=["rouge", "orange"],
        format_func=lambda x: {"rouge": "🔴 Rouge", "orange": "🟠 Orange", "vert": "🟢 Vert"}[x],
        label_visibility="collapsed",
    )
with col_f3:
    pred_sel = st.multiselect(
        "Prédiction ML",
        options=["Dropout", "Enrolled", "Graduate"],
        default=["Dropout"],
        label_visibility="collapsed",
    )
with col_f4:
    show_n = st.selectbox("Afficher", [10, 20, 50], label_visibility="collapsed")

df_filt = df.copy()
if alertes_sel:
    df_filt = df_filt[df_filt["alert_level"].isin(alertes_sel)]
if pred_sel:
    df_filt = df_filt[df_filt["pred_label"].isin(pred_sel)]
df_filt = df_filt[df_filt["score_pct"] >= seuil]

st.markdown(f"""
<div style="background:{BG_CARD};border:1px solid {C_COBALT}22;border-radius:12px;
            padding:12px 18px;margin:12px 0;font-size:13px;color:{T_MID};
            display:flex;align-items:center;gap:12px;">
    <span style="font-size:18px;">🔍</span>
    <div>
        <b style="color:{C_COBALT};">{len(df_filt)} étudiants</b> correspondent à vos filtres
        <span style="color:{T_LIGHT};font-size:11px;margin-left:8px;">
            sur {kpis['total']} au total ({round(len(df_filt)/kpis['total']*100,1)}%)
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

if not df_filt.empty:
    render_top10(df_filt, n=show_n)
else:
    st.markdown(f"""
    <div style="text-align:center;padding:40px;background:{BG_CARD};
                border:1px solid {BORDER};border-radius:14px;">
        <div style="font-size:32px;margin-bottom:12px;">🔎</div>
        <div style="font-size:14px;color:{T_LIGHT};">
            Aucun étudiant ne correspond à ces filtres. Élargissez vos critères.
        </div>
    </div>""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    f"<div class='page-footer'>VUE GLOBALE &nbsp;·&nbsp; {kpis['total']:,} ÉTUDIANTS "
    f"&nbsp;·&nbsp; PRÉCISION MODÈLE {kpis['accuracy']}%</div>",
    unsafe_allow_html=True,
)