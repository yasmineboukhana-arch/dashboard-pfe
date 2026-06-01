"""
╔══════════════════════════════════════════════════════════════════╗
║  pages/03_Vue_Par_Filiere.py                                     ║
║  Comparaison inter-filières · Filtres · Export CSV               ║
║  Palette cobalt/blanc · Guide en bulles · Sans chatbot           ║
╚══════════════════════════════════════════════════════════════════╝
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import sqlite3

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from app_config import (
    inject_css, render_topbar, section_header, sidebar_kpis,
    load_predictions, compute_kpis, guide_banner, guide_tooltip,
    BG_CARD, BG_PAGE, BG_SIDEBAR, BORDER, T_DARK, T_MID, T_LIGHT, T_WHITE,
    C_COBALT, C_CORAL, C_AMBER, C_EMERALD, C_VIOLET, C_CYAN,
    AXIS_STYLE, base_layout, DB_PATH, alert_color, hex_rgba,
)

# ─────────────────────────────────────────────────────────────────
COURSE_MAP = {
    "171":  "Animation & Multimédia",
    "8014": "Service Social (soir)",
    "9003": "Agronomie",
    "9070": "Design Communication",
    "9085": "Infirmerie Vétérinaire",
    "9119": "Ingénierie Informatique",
    "9130": "Équinculture",
    "9147": "Management",
    "9238": "Service Social",
    "9254": "Tourisme",
    "9500": "Soins Infirmiers",
    "9556": "Hygiène Orale",
    "9670": "Marketing & Pub",
    "9773": "Journalisme & Comm.",
    "9853": "Éducation de Base",
    "9991": "Management (soir)",
}

# ─────────────────────────────────────────────────────────────────
inject_css()

# ─────────────────────────────────────────────────────────────────
# DONNÉES
# ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def load_filiere_data(path: str = DB_PATH) -> pd.DataFrame:
    try:
        con = sqlite3.connect(path)
        df  = pd.read_sql_query("SELECT * FROM predictions", con)
        con.close()
    except Exception as e:
        st.error(f"❌ Base de données introuvable : {e}")
        st.stop()

    def extract_filiere(shap_json: str) -> str:
        try:
            d       = json.loads(shap_json)
            courses = {k: v for k, v in d.items() if k.startswith("Course_")}
            if not courses:
                return "Inconnue"
            best = max(courses, key=lambda k: abs(courses[k]))
            code = best.split("_")[1]
            return COURSE_MAP.get(code, f"Filière {code}")
        except Exception:
            return "Inconnue"

    df["filiere"]   = df["shap_values"].apply(extract_filiere)
    df["score_pct"] = (df["risk_score"] * 100).round(1)
    return df


@st.cache_data(ttl=60, show_spinner=False)
def compute_filiere_stats(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("filiere")
    stats = pd.DataFrame({
        "filiere":      g["student_id"].count().index,
        "nb":           g["student_id"].count().values,
        "risk_moyen":   g["risk_score"].mean().values,
        "grade_s1_moy": g["grade_s1"].mean().values if "grade_s1" in df.columns else 0,
        "grade_s2_moy": g["grade_s2"].mean().values if "grade_s2" in df.columns else 0,
        "nb_rouge":     g["alert_level"].apply(lambda x: (x == "rouge").sum()).values,
        "nb_orange":    g["alert_level"].apply(lambda x: (x == "orange").sum()).values,
        "nb_vert":      g["alert_level"].apply(lambda x: (x == "vert").sum()).values,
        "nb_dropout":   g["true_label"].apply(lambda x: (x == "Dropout").sum()).values,
        "nb_graduate":  g["true_label"].apply(lambda x: (x == "Graduate").sum()).values,
        "nb_enrolled":  g["true_label"].apply(lambda x: (x == "Enrolled").sum()).values,
    }).reset_index(drop=True)

    stats["taux_rouge"]   = (stats["nb_rouge"]   / stats["nb"] * 100).round(1)
    stats["taux_orange"]  = (stats["nb_orange"]  / stats["nb"] * 100).round(1)
    stats["taux_vert"]    = (stats["nb_vert"]    / stats["nb"] * 100).round(1)
    stats["taux_dropout"] = (stats["nb_dropout"] / stats["nb"] * 100).round(1)
    stats["risk_pct"]     = (stats["risk_moyen"] * 100).round(1)
    return stats.sort_values("risk_pct", ascending=False).reset_index(drop=True)


def risk_color(pct: float) -> str:
    if pct >= 60: return C_CORAL
    if pct >= 35: return C_AMBER
    return C_EMERALD


def dominant_alert(row) -> str:
    if row["taux_rouge"] >= 30:  return "rouge"
    if row["taux_orange"] >= 30: return "orange"
    return "vert"


# ─────────────────────────────────────────────────────────────────
# GRAPHIQUES
# ─────────────────────────────────────────────────────────────────

def plot_bar_risque(stats: pd.DataFrame) -> go.Figure:
    df_plot = stats.sort_values("risk_pct")
    colors  = [risk_color(v) for v in df_plot["risk_pct"]]
    hover   = [
        f"<b>{r['filiere']}</b><br>"
        f"Score moyen : {r['risk_pct']:.1f}%<br>"
        f"Étudiants : {r['nb']}<br>"
        f"🔴 {r['taux_rouge']:.1f}%  🟠 {r['taux_orange']:.1f}%  🟢 {r['taux_vert']:.1f}%<br>"
        f"Dropout réel : {r['taux_dropout']:.1f}%<extra></extra>"
        for _, r in df_plot.iterrows()
    ]
    fig = go.Figure(go.Bar(
        x=df_plot["risk_pct"], y=df_plot["filiere"], orientation="h",
        marker=dict(color=colors, opacity=0.85, line=dict(width=0)),
        text=[f"  {v:.1f}%" for v in df_plot["risk_pct"]],
        textposition="outside",
        textfont=dict(size=11, color=T_MID, family="JetBrains Mono, monospace"),
        hovertemplate=hover,
    ))
    fig.add_vline(x=35, line_color=C_AMBER, line_dash="dash", line_width=1.2,
                  annotation_text="Seuil orange (35%)",
                  annotation_font=dict(color=C_AMBER, size=9), annotation_position="top")
    fig.add_vline(x=60, line_color=C_CORAL, line_dash="dash", line_width=1.2,
                  annotation_text="Seuil rouge (60%)",
                  annotation_font=dict(color=C_CORAL, size=9), annotation_position="top")
    max_val = max(df_plot["risk_pct"].max() + 14, 75)
    fig.update_layout(**base_layout(
        title="<b>Score de Risque Moyen par Filière</b>",
        title_font=dict(size=13, color=T_DARK),
        xaxis=dict(**AXIS_STYLE, title="Score de risque moyen (%)", range=[0, max_val]),
        yaxis=dict(linecolor=BORDER, tickfont=dict(color=T_MID, size=11), automargin=True),
        showlegend=False,
        height=max(380, len(df_plot) * 38 + 80),
        margin=dict(l=10, r=70, t=50, b=40),
    ))
    return fig


def plot_stacked_alertes(stats: pd.DataFrame) -> go.Figure:
    df_plot = stats.sort_values("taux_rouge", ascending=True)
    fig = go.Figure()
    for level, color, label in [
        ("taux_vert",   C_EMERALD, "🟢 Vert"),
        ("taux_orange", C_AMBER,   "🟠 Orange"),
        ("taux_rouge",  C_CORAL,   "🔴 Rouge"),
    ]:
        fig.add_trace(go.Bar(
            name=label, x=df_plot[level], y=df_plot["filiere"], orientation="h",
            marker=dict(color=color, opacity=0.82, line=dict(width=0)),
            hovertemplate=f"<b>%{{y}}</b><br>{label} : %{{x:.1f}}%<extra></extra>",
        ))
    fig.update_layout(**base_layout(
        title="<b>Répartition des Alertes par Filière (%)</b>",
        title_font=dict(size=13, color=T_DARK),
        xaxis=dict(**AXIS_STYLE, title="Part des étudiants (%)", range=[0, 105]),
        yaxis=dict(linecolor=BORDER, tickfont=dict(color=T_MID, size=11), automargin=True),
        barmode="stack",
        legend=dict(font=dict(color=T_MID), bgcolor="rgba(0,0,0,0)",
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=max(380, len(df_plot) * 38 + 80),
        margin=dict(l=10, r=20, t=50, b=40),
    ))
    return fig


def plot_scatter(stats: pd.DataFrame) -> go.Figure:
    colors = [risk_color(v) for v in stats["risk_pct"]]
    hover  = [
        f"<b>{r['filiere']}</b><br>"
        f"Risque ML : {r['risk_pct']:.1f}%<br>"
        f"Dropout réel : {r['taux_dropout']:.1f}%<br>"
        f"Effectif : {r['nb']}<extra></extra>"
        for _, r in stats.iterrows()
    ]
    fig = go.Figure(go.Scatter(
        x=stats["risk_pct"], y=stats["taux_dropout"],
        mode="markers+text",
        text=stats["filiere"],
        textposition="top center",
        textfont=dict(size=9, color=T_MID),
        marker=dict(
            size=[max(12, n // 5) for n in stats["nb"]],
            color=colors, opacity=0.80,
            line=dict(width=1.5, color=BG_CARD),
        ),
        hovertemplate=hover,
    ))
    max_val = max(stats["risk_pct"].max(), stats["taux_dropout"].max()) + 12
    fig.add_shape(type="line", x0=0, y0=0, x1=max_val, y1=max_val,
                  line=dict(color=BORDER, width=1.5, dash="dot"))
    fig.update_layout(**base_layout(
        title="<b>Risque Prédit vs Dropout Réel</b>",
        title_font=dict(size=13, color=T_DARK),
        xaxis=dict(**AXIS_STYLE, title="Score de risque ML (%)", range=[0, max_val]),
        yaxis=dict(**AXIS_STYLE, title="Taux dropout réel (%)",  range=[0, max_val]),
        showlegend=False, height=420, margin=dict(l=10, r=20, t=50, b=40),
    ))
    return fig


def plot_notes_filieres(stats: pd.DataFrame) -> go.Figure:
    if "grade_s1_moy" not in stats.columns:
        return None
    df_plot = stats.sort_values("grade_s1_moy", ascending=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Note moy. S1", x=df_plot["grade_s1_moy"].round(2), y=df_plot["filiere"],
        orientation="h", marker=dict(color=C_COBALT, opacity=0.82, line=dict(width=0)),
        hovertemplate="<b>%{y}</b><br>S1 : %{x:.2f}/20<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Note moy. S2", x=df_plot["grade_s2_moy"].round(2), y=df_plot["filiere"],
        orientation="h", marker=dict(color=C_VIOLET, opacity=0.82, line=dict(width=0)),
        hovertemplate="<b>%{y}</b><br>S2 : %{x:.2f}/20<extra></extra>",
    ))
    fig.add_vline(x=10, line_color=C_AMBER, line_dash="dash", line_width=1.2,
                  annotation_text="Moyenne 10/20",
                  annotation_font=dict(color=C_AMBER, size=9))
    fig.update_layout(**base_layout(
        title="<b>Notes Moyennes S1/S2 par Filière</b>",
        title_font=dict(size=13, color=T_DARK),
        xaxis=dict(**AXIS_STYLE, title="Note moyenne (/20)", range=[0, 22]),
        yaxis=dict(linecolor=BORDER, tickfont=dict(color=T_MID, size=11), automargin=True),
        barmode="group", bargap=0.22, bargroupgap=0.06,
        legend=dict(font=dict(color=T_MID), bgcolor="rgba(0,0,0,0)",
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=max(380, len(df_plot) * 38 + 80),
        margin=dict(l=10, r=20, t=50, b=40),
    ))
    return fig


def plot_radar_top5(stats: pd.DataFrame) -> go.Figure:
    top5 = stats.head(5)
    cats = ["Risque moy.", "% Rouge", "% Dropout", "% Orange", "% Vert"]
    fig  = go.Figure()
    palette = [C_CORAL, C_AMBER, C_COBALT, C_VIOLET, C_CYAN]
    for i, (_, row) in enumerate(top5.iterrows()):
        vals = [
            row["risk_pct"], row["taux_rouge"],
            row["taux_dropout"], row["taux_orange"], row["taux_vert"],
        ]
        cats_c = cats + [cats[0]]
        vals_c = vals + [vals[0]]
        c = palette[i % len(palette)]
        fig.add_trace(go.Scatterpolar(
            r=vals_c, theta=cats_c, fill="toself",
            name=row["filiere"][:22],
            line=dict(color=c, width=2),
            fillcolor=hex_rgba(c, 0.08),
            hovertemplate=f"<b>{row['filiere']}</b><br>%{{theta}}: %{{r:.1f}}%<extra></extra>",
        ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        polar=dict(
            bgcolor=BG_CARD,
            radialaxis=dict(visible=True, gridcolor=BORDER, linecolor=BORDER,
                            tickfont=dict(color=T_LIGHT, size=9), range=[0, 100]),
            angularaxis=dict(linecolor=BORDER, gridcolor=BORDER,
                             tickfont=dict(color=T_MID, size=10)),
        ),
        title="<b>Radar — Top 5 Filières à Risque</b>",
        title_font=dict(size=13, color=T_DARK),
        legend=dict(font=dict(color=T_MID, size=10), bgcolor="rgba(0,0,0,0)",
                    orientation="v", x=1.02, y=0.5),
        font=dict(family="Outfit, sans-serif", color=T_MID),
        margin=dict(l=20, r=140, t=50, b=20),
        height=400,
    )
    return fig


# ─────────────────────────────────────────────────────────────────
# KPI FILIÈRES
# ─────────────────────────────────────────────────────────────────

def render_kpis_filieres(df_filt: pd.DataFrame, stats_filt: pd.DataFrame) -> None:
    nb_total     = len(df_filt)
    nb_filieres  = len(stats_filt)
    taux_rouge   = (df_filt["alert_level"] == "rouge").mean() * 100
    taux_dropout = (df_filt["true_label"]  == "Dropout").mean() * 100
    top_fil      = stats_filt.iloc[0]["filiere"]  if len(stats_filt) > 0 else "—"
    top_fil_r    = stats_filt.iloc[0]["risk_pct"] if len(stats_filt) > 0 else 0

    c1, c2, c3, c4, c5 = st.columns(5, gap="small")
    data = [
        (c1, "cobalt",  "🎓", f"{nb_total:,}",        "Étudiants filtrés"),
        (c2, "cobalt",  "📚", f"{nb_filieres}",        "Filières affichées"),
        (c3, "coral",   "🔴", f"{taux_rouge:.1f}%",    "En alerte rouge"),
        (c4, "amber",   "📉", f"{taux_dropout:.1f}%",  "Taux dropout réel"),
        (c5, "coral",   "⚠️", f"{top_fil_r:.1f}%",     f"Risque max · {top_fil[:16]}"),
    ]
    for col, cls, ico, val, lbl in data:
        with col:
            st.markdown(f"""
            <div class="kpi {cls}">
              <span class="kpi-bg-icon">{ico}</span>
              <div class="kpi-label">{lbl}</div>
              <div class="kpi-val {cls}" style="font-size:32px;">{val}</div>
              <div class="kpi-sub">{ico}</div>
            </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# TABLEAU FILIÈRES
# ─────────────────────────────────────────────────────────────────

def render_filiere_table(stats: pd.DataFrame) -> None:
    st.markdown(f"""
    <div style="background:{BG_CARD};border:1px solid {BORDER};
                border-radius:14px;overflow:hidden;box-shadow:0 1px 3px rgba(15,23,42,0.05);">
      <div style="display:grid;grid-template-columns:2fr 0.7fr 0.8fr 1fr 1fr 1fr 0.9fr;
                  background:{BG_SIDEBAR};padding:10px 18px;
                  font-size:9px;font-weight:700;letter-spacing:1.8px;text-transform:uppercase;
                  color:rgba(248,250,252,.5);font-family:'JetBrains Mono',monospace;">
        <span>Filière</span><span>Étudiants</span><span>Risque moy.</span>
        <span>Barre</span><span>🔴 Rouge</span><span>Dropout réel</span>
        <span>Alerte dom.</span>
      </div>
    """, unsafe_allow_html=True)

    for _, row in stats.iterrows():
        c     = risk_color(row["risk_pct"])
        dom   = dominant_alert(row)
        d_col = alert_color(dom)
        d_emo = {"rouge": "🔴", "orange": "🟠", "vert": "🟢"}[dom]
        bar_w = min(row["risk_pct"], 100)

        st.markdown(f"""
        <div style="display:grid;grid-template-columns:2fr 0.7fr 0.8fr 1fr 1fr 1fr 0.9fr;
                    padding:12px 18px;border-bottom:1px solid {BORDER};
                    align-items:center;transition:background .15s;">
          <div>
            <div style="font-size:13px;font-weight:700;color:{T_DARK};">{row['filiere']}</div>
            <div style="font-size:10px;color:{T_LIGHT};font-family:'JetBrains Mono',monospace;margin-top:2px;">
              {int(row['nb_rouge'])}R · {int(row['nb_orange'])}O · {int(row['nb_vert'])}V
            </div>
          </div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:700;color:{T_DARK};">
            {int(row['nb'])}
          </div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:700;color:{c};">
            {row['risk_pct']:.1f}%
          </div>
          <div>
            <div style="width:100%;height:6px;background:{BORDER};border-radius:4px;overflow:hidden;">
              <div style="width:{bar_w}%;height:6px;background:{c};border-radius:4px;"></div>
            </div>
          </div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:12px;
                      font-weight:700;color:{C_CORAL};">
            {row['taux_rouge']:.1f}%
          </div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:12px;
                      font-weight:700;color:{T_DARK};">
            {row['taux_dropout']:.1f}%
          </div>
          <div>
            <span style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;
                         border-radius:20px;font-size:9px;font-weight:700;letter-spacing:.8px;
                         font-family:'JetBrains Mono',monospace;
                         background:{hex_rgba(d_col,0.1)};
                         border:1px solid {hex_rgba(d_col,0.3)};color:{d_col};">
              {d_emo} {dom.capitalize()}
            </span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# PAGE PRINCIPALE
# ─────────────────────────────────────────────────────────────────

df_all  = load_filiere_data(DB_PATH)
kpis    = compute_kpis(df_all)
sidebar_kpis(kpis, "🏫", "Vue par Filière", "COMPARAISON DES RISQUES")
render_topbar("🏫", "Vue par Filière — Comparaison des Risques",
              "Score · Alertes · Dropout · Notes · Filtres Dynamiques · Export",
              len(df_all))

all_filieres = sorted(df_all["filiere"].unique().tolist())
all_alertes  = ["rouge", "orange", "vert"]

# ══════════════════════════════════════════════════════════════════
# FILTRES
# ══════════════════════════════════════════════════════════════════
section_header(
    "🎛️", "Filtres Dynamiques",
    guide_title="Utiliser les filtres",
    guide_text="Sélectionnez une ou plusieurs filières pour les comparer. "
               "Ajoutez un filtre d'alerte pour ne voir que les filières critiques. "
               "Le seuil de risque masque les filières en dessous du niveau choisi."
)

guide_banner(
    "Astuce — Comparaison ciblée",
    "Pour identifier rapidement les filières à fort risque : "
    "gardez toutes les filières sélectionnées, mettez le seuil de risque à 40% "
    "et filtrez par alerte rouge. Vous verrez les filières prioritaires.",
    steps=["Choisir les filières", "Définir le seuil de risque", "Filtrer par alerte"]
)

st.markdown("<br style='margin:6px 0'>", unsafe_allow_html=True)

col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1.8, 1.2, 0.5], gap="medium")

with col_f1:
    filieres_sel = st.multiselect(
        "Filières", options=all_filieres, default=all_filieres,
        placeholder="Toutes les filières…", label_visibility="collapsed",
    )
with col_f2:
    alertes_sel = st.multiselect(
        "Niveaux d'alerte", options=all_alertes, default=all_alertes,
        format_func=lambda x: {"rouge": "🔴 Rouge", "orange": "🟠 Orange", "vert": "🟢 Vert"}[x],
        placeholder="Tous les niveaux…", label_visibility="collapsed",
    )
with col_f3:
    seuil_risque = st.slider(
        "Seuil risque min (%)", min_value=0, max_value=100, value=0, step=5,
        label_visibility="collapsed",
    )
with col_f4:
    if st.button("↺", use_container_width=True, help="Réinitialiser les filtres"):
        st.rerun()

# ── Appliquer les filtres ─────────────────────────────────────────
if not filieres_sel: filieres_sel = all_filieres
if not alertes_sel:  alertes_sel  = all_alertes

df_filt    = df_all[df_all["filiere"].isin(filieres_sel) & df_all["alert_level"].isin(alertes_sel)]
stats_full = compute_filiere_stats(df_filt)
stats_filt = stats_full[
    (stats_full["filiere"].isin(filieres_sel)) &
    (stats_full["risk_pct"] >= seuil_risque)
].reset_index(drop=True)

st.markdown("<br>", unsafe_allow_html=True)

if df_filt.empty or stats_filt.empty:
    st.markdown(f"""
    <div style="text-align:center;padding:60px 20px;background:{BG_CARD};
                border:1px solid {BORDER};border-radius:16px;">
      <div style="font-size:52px;margin-bottom:16px;">🔎</div>
      <div style="font-size:18px;font-weight:800;color:{T_DARK};margin-bottom:8px;">
          Aucun résultat
      </div>
      <div style="font-size:13px;color:{T_LIGHT};">
          La combinaison de filtres ne retourne aucune donnée. Réinitialisez ↺
      </div>
    </div>""", unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════════════════
# KPI SYNTHÈSE
# ══════════════════════════════════════════════════════════════════
section_header(
    "📊", "Synthèse de la Sélection",
    guide_title="Indicateurs filtrés",
    guide_text="Ces KPI reflètent uniquement les données correspondant à vos filtres actifs. "
               "Ils changent dynamiquement quand vous modifiez les filtres."
)
render_kpis_filieres(df_filt, stats_filt)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# GRAPHIQUE PRINCIPAL
# ══════════════════════════════════════════════════════════════════
section_header(
    "📈", "Classement des Filières par Risque",
    guide_title="Lire le classement",
    guide_text="Les filières sont triées du risque le plus faible (bas) au plus élevé (haut). "
               "Couleur de la barre : verte < 35%, orange 35-60%, rouge > 60%. "
               "Les lignes en pointillés marquent les seuils d'alerte."
)

st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.plotly_chart(plot_bar_risque(stats_filt), use_container_width=True,
                config={"displayModeBar": False})
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# LIGNE 2 : ALERTES EMPILÉES + SCATTER
# ══════════════════════════════════════════════════════════════════
section_header(
    "🔍", "Analyse Détaillée",
    guide_title="Scatter risque vs dropout",
    guide_text="La diagonale pointillée = référence parfaite (risque prédit = dropout réel). "
               "Points AU-DESSUS → le modèle sous-estime le vrai danger de cette filière. "
               "La taille des bulles = effectif de la filière."
)

col_stacked, col_scatter = st.columns([1.4, 1], gap="medium")

with col_stacked:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.plotly_chart(plot_stacked_alertes(stats_filt), use_container_width=True,
                    config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

with col_scatter:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.plotly_chart(plot_scatter(stats_filt), use_container_width=True,
                    config={"displayModeBar": False})
    st.markdown(f"""
    <div style="font-size:10px;color:{T_LIGHT};font-family:'JetBrains Mono',monospace;
                margin-top:8px;line-height:1.8;">
        Taille des bulles = effectif.<br>
        Ligne pointillée = référence parfaite.<br>
        Points au-dessus → dropout sous-estimé ⚠️
    </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# LIGNE 3 : NOTES + RADAR
# ══════════════════════════════════════════════════════════════════
notes_fig = plot_notes_filieres(stats_filt)
radar_fig = plot_radar_top5(stats_filt) if len(stats_filt) >= 3 else None

if notes_fig or radar_fig:
    section_header(
        "🎓", "Performance Académique",
        guide_title="Notes et radar Top 5",
        guide_text="Le graphique des notes compare les moyennes S1/S2 par filière. "
                   "La ligne orange = seuil de 10/20. "
                   "Le radar compare simultanément 5 indicateurs pour les 5 filières les plus risquées."
    )
    if notes_fig and radar_fig:
        cn, cr = st.columns([1.4, 1], gap="medium")
        with cn:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.plotly_chart(notes_fig, use_container_width=True,
                            config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)
        with cr:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.plotly_chart(radar_fig, use_container_width=True,
                            config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)
    elif notes_fig:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.plotly_chart(notes_fig, use_container_width=True,
                        config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# TABLEAU RÉCAPITULATIF
# ══════════════════════════════════════════════════════════════════
section_header(
    "📋", "Tableau Récapitulatif des Filières",
    guide_title="Lire le tableau",
    guide_text="Chaque ligne = une filière. "
               "La barre de risque donne une lecture visuelle rapide. "
               "L'alerte dominante est calculée : rouge si >30% d'étudiants en rouge, "
               "sinon orange si >30% en orange, sinon vert."
)
render_filiere_table(stats_filt)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# EXPORT CSV
# ══════════════════════════════════════════════════════════════════
section_header(
    "⬇️", "Export des Données",
    guide_title="Exporter les données",
    guide_text="Deux exports disponibles : les statistiques agrégées par filière "
               "(utile pour un rapport) et les données individuelles filtrées "
               "(utile pour un traitement externe en Excel ou Python)."
)

with st.expander("Exporter les données filtrées"):
    col_e1, col_e2 = st.columns(2, gap="medium")
    with col_e1:
        st.markdown(f"<p style='font-size:12px;color:{T_MID};margin-bottom:8px;'>"
                    f"📊 Stats agrégées ({len(stats_filt)} filières)</p>",
                    unsafe_allow_html=True)
        st.download_button(
            "⬇️ stats_filieres.csv",
            data=stats_filt.to_csv(index=False).encode("utf-8"),
            file_name="stats_filieres.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_e2:
        st.markdown(f"<p style='font-size:12px;color:{T_MID};margin-bottom:8px;'>"
                    f"👤 Données individuelles ({len(df_filt)} étudiants)</p>",
                    unsafe_allow_html=True)
        cols_exp = [c for c in df_filt.columns if c != "shap_values"]
        st.download_button(
            "⬇️ etudiants_filtres.csv",
            data=df_filt[cols_exp].to_csv(index=False).encode("utf-8"),
            file_name="etudiants_filtres.csv",
            mime="text/csv",
            use_container_width=True,
        )

# ── Footer ────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    f"<div class='page-footer'>VUE PAR FILIÈRE &nbsp;·&nbsp; {len(df_filt):,} étudiants "
    f"&nbsp;·&nbsp; {len(stats_filt)} filières affichées</div>",
    unsafe_allow_html=True,
)