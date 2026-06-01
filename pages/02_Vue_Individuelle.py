"""
╔══════════════════════════════════════════════════════════════════╗
║  pages/02_Vue_Individuelle.py                                    ║
║  Profil étudiant · Jauge · SHAP · Radar UC · Notes · PDF        ║
║  Style cobalt/blanc · Tooltips guide en bulles                   ║
╚══════════════════════════════════════════════════════════════════╝
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import sqlite3

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app_config import (
    inject_css, render_topbar, section_header, sidebar_kpis,
    load_predictions, compute_kpis, guide_banner, guide_tooltip,
    badge_alert, badge_pred, alert_color, score_color, hex_rgba,
    BG_CARD, BG_PAGE, BG_SIDEBAR, BORDER, T_DARK, T_MID, T_LIGHT, T_WHITE,
    C_COBALT, C_CORAL, C_AMBER, C_EMERALD, C_VIOLET, C_CYAN,
    AXIS_STYLE, base_layout, DB_PATH,
)

# ─────────────────────────────────────────────────────────────────
inject_css()
df   = load_predictions(DB_PATH)
kpis = compute_kpis(df)
sidebar_kpis(kpis, "👤", "Vue Individuelle", "PROFIL ÉTUDIANT")
render_topbar("👤", "Vue Individuelle — Profil Étudiant",
              "Score · SHAP · Radar UC · Notes · Données académiques · Export PDF",
              len(df))

# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────
def alert_emoji(level: str) -> str:
    return {"rouge": "🔴", "orange": "🟠", "vert": "🟢"}.get(level, "⚪")

def pred_cls(label: str) -> str:
    return {"Dropout": "dropout", "Enrolled": "enrolled",
            "Graduate": "graduate"}.get(label, "blue")

def risk_label(pct: float) -> str:
    if pct >= 70: return "Risque Élevé"
    if pct >= 40: return "Surveillance"
    return "Stable"

def safe_val(student, col):
    try:
        v = student.get(col) if hasattr(student, "get") else student[col]
        return float(v) if v is not None else None
    except Exception:
        return None

def parse_shap(shap_json: str) -> pd.DataFrame:
    try:
        d    = json.loads(shap_json)
        rows = [{"feature": k.split("(")[0].strip(), "value": v} for k, v in d.items()]
        df_s = pd.DataFrame(rows)
        df_s = df_s.reindex(df_s["value"].abs().sort_values(ascending=False).index)
        return df_s.head(12)
    except Exception:
        return pd.DataFrame(columns=["feature", "value"])

def get_recommendations(level: str, shap_df: pd.DataFrame) -> list:
    recs = []
    if level == "rouge":
        recs += [
            ("rouge",  "🚨", "Convocation urgente",
             "Planifier un entretien individuel avec le conseiller pédagogique dans les 48h."),
            ("rouge",  "📞", "Contact famille",
             "Informer les responsables légaux et activer le dispositif d'accompagnement."),
            ("rouge",  "📋", "Plan de remédiation",
             "Définir des objectifs hebdomadaires mesurables avec suivi rapproché."),
        ]
    elif level == "orange":
        recs += [
            ("orange", "👁️", "Suivi renforcé",
             "Augmenter la fréquence des points de suivi à une fois par semaine."),
            ("orange", "📚", "Tutorat pair",
             "Proposer un binôme avec un étudiant performant de la même filière."),
        ]
    else:
        recs += [
            ("vert", "✅", "Situation stable",
             "Maintenir le suivi mensuel. Encourager les activités parascolaires."),
        ]
    if not shap_df.empty:
        top_risk = shap_df[shap_df["value"] > 0].head(2)
        for _, row in top_risk.iterrows():
            feat = row["feature"].lower()
            if any(x in feat for x in ["approv", "grade", "note", "curricular"]):
                recs.append(("cobalt", "📖", "Soutien académique",
                             f"Les résultats ({row['feature']}) sont un facteur de risque clé."))
                break
            if any(x in feat for x in ["debt", "tuition", "financ"]):
                recs.append(("cobalt", "💰", "Aide financière",
                             f"Difficultés financières détectées ({row['feature']}). "
                             "Orienter vers le service des bourses."))
                break
    return recs[:5]

# ─────────────────────────────────────────────────────────────────
# GRAPHIQUES
# ─────────────────────────────────────────────────────────────────

def plot_gauge(score_pct: float, alert_level: str) -> go.Figure:
    color = alert_color(alert_level)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score_pct,
        number=dict(suffix="%", font=dict(size=44, color=color, family="Outfit, sans-serif")),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=1, tickcolor=T_LIGHT,
                      tickfont=dict(color=T_LIGHT, size=10), dtick=20),
            bar=dict(color=color, thickness=0.28),
            bgcolor=BG_PAGE, borderwidth=0,
            steps=[
                dict(range=[0,  40],  color="rgba(5,150,105,0.10)"),
                dict(range=[40, 70],  color="rgba(217,119,6,0.10)"),
                dict(range=[70, 100], color="rgba(220,38,38,0.10)"),
            ],
            threshold=dict(line=dict(color=color, width=3), thickness=0.8, value=score_pct),
        ),
        domain=dict(x=[0, 1], y=[0, 1]),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, sans-serif", color=T_MID),
        margin=dict(l=20, r=20, t=20, b=20),
        height=220,
    )
    return fig


def plot_shap(shap_df: pd.DataFrame) -> go.Figure:
    if shap_df.empty:
        return go.Figure()
    df = shap_df.copy()
    df["abs"] = df["value"].abs()
    df = df.sort_values("abs")
    colors = [C_CORAL if v > 0 else C_EMERALD for v in df["value"]]
    hover  = [
        f"<b>{r['feature']}</b><br>"
        f"Impact : {'↑ Augmente' if r['value'] > 0 else '↓ Réduit'} le risque<br>"
        f"Valeur SHAP : {r['value']:+.4f}<extra></extra>"
        for _, r in df.iterrows()
    ]
    fig = go.Figure(go.Bar(
        x=df["value"], y=df["feature"], orientation="h",
        marker=dict(color=colors, opacity=0.82, line=dict(width=0)),
        hovertemplate=hover,
    ))
    fig.add_vline(x=0, line_color=BORDER, line_width=1.5)
    fig.update_layout(**base_layout(
        title="<b>Facteurs de Risque SHAP</b>",
        title_font=dict(size=13, color=T_DARK),
        xaxis=dict(**AXIS_STYLE, title="Valeur SHAP (impact sur le score)",
                   zeroline=True, zerolinewidth=2),
        yaxis=dict(linecolor=BORDER, tickfont=dict(color=T_MID, size=11), automargin=True),
        showlegend=False, height=420, margin=dict(l=10, r=20, t=44, b=30),
    ))
    return fig


def plot_notes(student) -> go.Figure:
    """Graphique barres groupées notes S1/S2 (ancien code)."""
    g1 = safe_val(student, "grade_s1")
    g2 = safe_val(student, "grade_s2")
    if g1 is None and g2 is None:
        return None
    fig = go.Figure()
    if g1 is not None:
        fig.add_trace(go.Bar(
            name="Semestre 1", x=["Note (/20)"], y=[g1],
            marker=dict(color=C_COBALT, opacity=0.85, line=dict(width=0)),
            text=[f"{g1:.2f}"], textposition="outside",
            hovertemplate="S1 : %{y:.2f}/20<extra></extra>",
        ))
    if g2 is not None:
        fig.add_trace(go.Bar(
            name="Semestre 2", x=["Note (/20)"], y=[g2],
            marker=dict(color=C_VIOLET, opacity=0.85, line=dict(width=0)),
            text=[f"{g2:.2f}"], textposition="outside",
            hovertemplate="S2 : %{y:.2f}/20<extra></extra>",
        ))
    fig.add_hline(y=10, line_color=C_AMBER, line_dash="dash", line_width=1.5,
                  annotation_text="Moyenne 10/20",
                  annotation_font=dict(color=C_AMBER, size=10),
                  annotation_position="top right")
    fig.update_layout(**base_layout(
        title="<b>Notes par Semestre</b>", title_font=dict(size=13, color=T_DARK),
        xaxis=dict(**AXIS_STYLE),
        yaxis=dict(**AXIS_STYLE, title="Note (/20)", range=[0, 22]),
        legend=dict(font=dict(color=T_MID), bgcolor="rgba(0,0,0,0)",
                    orientation="h", yanchor="top", y=1.12, xanchor="right", x=1),
        barmode="group", bargap=0.4, bargroupgap=0.1,
        height=320, margin=dict(l=10, r=20, t=50, b=40),
    ))
    return fig


def plot_uc(student) -> go.Figure:
    """Graphique barres groupées UC S1/S2 (ancien code)."""
    metrics = [("approved", "Validées"), ("enrolled", "Inscrites"),
               ("evaluations", "Évaluations"), ("credited", "Créditées"),
               ("without_eval", "Sans éval.")]
    labels = [m[1] for m in metrics]
    v1 = [safe_val(student, f"{k}_s1") or 0 for k, _ in metrics]
    v2 = [safe_val(student, f"{k}_s2") or 0 for k, _ in metrics]
    if all(x == 0 for x in v1 + v2):
        return None
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="S1", x=labels, y=v1,
        marker=dict(color=C_COBALT, opacity=0.82, line=dict(width=0)),
        text=[str(int(v)) for v in v1], textposition="outside",
        hovertemplate="<b>%{x}</b><br>S1 : %{y}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="S2", x=labels, y=v2,
        marker=dict(color=C_VIOLET, opacity=0.82, line=dict(width=0)),
        text=[str(int(v)) for v in v2], textposition="outside",
        hovertemplate="<b>%{x}</b><br>S2 : %{y}<extra></extra>",
    ))
    fig.update_layout(**base_layout(
        title="<b>Unités Curriculaires S1/S2</b>", title_font=dict(size=13, color=T_DARK),
        xaxis=dict(**AXIS_STYLE), yaxis=dict(**AXIS_STYLE, title="Nombre"),
        legend=dict(font=dict(color=T_MID), bgcolor="rgba(0,0,0,0)",
                    orientation="h", yanchor="top", y=1.12, xanchor="right", x=1),
        barmode="group", bargap=0.28, bargroupgap=0.08,
        height=320, margin=dict(l=10, r=20, t=50, b=40),
    ))
    return fig


def plot_radar_uc(student) -> go.Figure:
    """Radar comparatif UC S1 vs S2 (ancien code enrichi)."""
    metrics = [("approved", "Validées"), ("enrolled", "Inscrites"),
               ("evaluations", "Évaluations"), ("credited", "Créditées"),
               ("without_eval", "Sans éval.")]
    labels = [m[1] for m in metrics]
    v1 = [safe_val(student, f"{k}_s1") or 0 for k, _ in metrics]
    v2 = [safe_val(student, f"{k}_s2") or 0 for k, _ in metrics]
    if all(v == 0 for v in v1 + v2):
        return None
    cats = labels + [labels[0]]
    v1c  = v1 + [v1[0]]
    v2c  = v2 + [v2[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=v1c, theta=cats, fill="toself", name="Semestre 1",
        line=dict(color=C_COBALT, width=2),
        fillcolor=hex_rgba(C_COBALT, 0.10),
        hovertemplate="<b>%{theta}</b><br>S1 : %{r}<extra></extra>",
    ))
    fig.add_trace(go.Scatterpolar(
        r=v2c, theta=cats, fill="toself", name="Semestre 2",
        line=dict(color=C_VIOLET, width=2),
        fillcolor=hex_rgba(C_VIOLET, 0.10),
        hovertemplate="<b>%{theta}</b><br>S2 : %{r}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        polar=dict(
            bgcolor=BG_CARD,
            radialaxis=dict(visible=True, gridcolor=BORDER, linecolor=BORDER,
                            tickfont=dict(color=T_LIGHT, size=9)),
            angularaxis=dict(linecolor=BORDER, gridcolor=BORDER,
                             tickfont=dict(color=T_MID, size=10)),
        ),
        title="<b>Comparaison UC — S1 / S2</b>",
        title_font=dict(size=13, color=T_DARK),
        legend=dict(font=dict(color=T_MID), bgcolor="rgba(0,0,0,0)",
                    orientation="h", yanchor="bottom", y=-0.18,
                    xanchor="center", x=0.5),
        font=dict(family="Outfit, sans-serif", color=T_MID),
        margin=dict(l=20, r=20, t=50, b=50),
        height=320,
    )
    return fig


def plot_admission(student) -> go.Figure:
    """Graphique comparaison note d'admission vs qualification (nouveau)."""
    ag = safe_val(student, "admission_grade")
    pq = safe_val(student, "prev_qualification_grade")
    if ag is None and pq is None:
        return None
    labels, vals, colors = [], [], []
    if ag is not None:
        labels.append("Note Admission"); vals.append(ag); colors.append(C_COBALT)
    if pq is not None:
        labels.append("Qualification antérieure"); vals.append(pq); colors.append(C_CYAN)
    fig = go.Figure(go.Bar(
        x=labels, y=vals,
        marker=dict(color=colors, opacity=0.85, line=dict(width=0)),
        text=[f"{v:.1f}" for v in vals], textposition="outside",
        hovertemplate="<b>%{x}</b><br>Note : %{y:.1f}/200<extra></extra>",
    ))
    fig.add_hline(y=100, line_color=C_AMBER, line_dash="dash", line_width=1.5,
                  annotation_text="50% (100/200)",
                  annotation_font=dict(color=C_AMBER, size=10),
                  annotation_position="top right")
    fig.update_layout(**base_layout(
        title="<b>Notes d'Admission (/200)</b>",
        title_font=dict(size=13, color=T_DARK),
        xaxis=dict(**AXIS_STYLE),
        yaxis=dict(**AXIS_STYLE, title="Note (/200)", range=[0, 220]),
        showlegend=False,
        height=280, margin=dict(l=10, r=20, t=50, b=40),
    ))
    return fig


def plot_taux_validation(student) -> go.Figure:
    """Jauge taux de validation S1 et S2 (nouveau)."""
    data = []
    for sem, col_app, col_enr in [("S1", "approved_s1", "enrolled_s1"),
                                   ("S2", "approved_s2", "enrolled_s2")]:
        a = safe_val(student, col_app)
        e = safe_val(student, col_enr)
        if a is not None and e is not None and e > 0:
            data.append((sem, round(a / e * 100, 1)))
    if not data:
        return None

    fig = go.Figure()
    palette = [C_COBALT, C_VIOLET]
    for i, (sem, taux) in enumerate(data):
        color = C_EMERALD if taux >= 80 else C_AMBER if taux >= 50 else C_CORAL
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=taux,
            number=dict(suffix="%", font=dict(size=26, color=color, family="Outfit, sans-serif")),
            title=dict(text=f"<b>Taux validation {sem}</b>",
                       font=dict(size=11, color=T_MID)),
            gauge=dict(
                axis=dict(range=[0, 100], tickwidth=1, tickcolor=T_LIGHT,
                          tickfont=dict(color=T_LIGHT, size=9), dtick=25),
                bar=dict(color=color, thickness=0.28),
                bgcolor=BG_PAGE, borderwidth=0,
                steps=[
                    dict(range=[0, 50],   color="rgba(220,38,38,0.08)"),
                    dict(range=[50, 80],  color="rgba(217,119,6,0.08)"),
                    dict(range=[80, 100], color="rgba(5,150,105,0.08)"),
                ],
            ),
            domain=dict(x=[i * 0.52, i * 0.52 + 0.48], y=[0, 1]),
        ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, sans-serif", color=T_MID),
        margin=dict(l=10, r=10, t=20, b=10),
        height=200,
    )
    return fig


def plot_profil_complet(student, df_all: pd.DataFrame, pct: float) -> go.Figure:
    """Radar comparaison étudiant vs moyenne globale (nouveau)."""
    def norm(val, col, max_val):
        v = safe_val(student, col)
        return round((v / max_val) * 100, 1) if v is not None else 0

    cats = ["Note S1", "Note S2", "Admission", "UC validées S1", "UC validées S2"]

    g1  = (safe_val(student, "grade_s1") or 0) / 20 * 100
    g2  = (safe_val(student, "grade_s2") or 0) / 20 * 100
    adm = (safe_val(student, "admission_grade") or 0) / 200 * 100
    uv1 = min((safe_val(student, "approved_s1") or 0) / 10 * 100, 100)
    uv2 = min((safe_val(student, "approved_s2") or 0) / 10 * 100, 100)
    vals_stu = [g1, g2, adm, uv1, uv2]

    # Moyennes globales
    mg1  = df_all["grade_s1"].mean()  / 20 * 100  if "grade_s1"   in df_all else 50
    mg2  = df_all["grade_s2"].mean()  / 20 * 100  if "grade_s2"   in df_all else 50
    madm = df_all["admission_grade"].mean() / 200 * 100 if "admission_grade" in df_all else 50
    mu1  = min(df_all["approved_s1"].mean() / 10 * 100, 100) if "approved_s1" in df_all else 50
    mu2  = min(df_all["approved_s2"].mean() / 10 * 100, 100) if "approved_s2" in df_all else 50
    vals_moy = [mg1, mg2, madm, mu1, mu2]

    cats_c   = cats + [cats[0]]
    vals_s_c = vals_stu  + [vals_stu[0]]
    vals_m_c = vals_moy  + [vals_moy[0]]

    color_stu = alert_color(student["alert_level"])

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals_m_c, theta=cats_c, fill="toself", name="Moyenne globale",
        line=dict(color=T_LIGHT, width=1.5, dash="dot"),
        fillcolor="rgba(148,163,184,0.08)",
        hovertemplate="<b>%{theta}</b><br>Moyenne : %{r:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatterpolar(
        r=vals_s_c, theta=cats_c, fill="toself", name="Cet étudiant",
        line=dict(color=color_stu, width=2.5),
        fillcolor=hex_rgba(color_stu, 0.12),
        hovertemplate="<b>%{theta}</b><br>Étudiant : %{r:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        polar=dict(
            bgcolor=BG_CARD,
            radialaxis=dict(visible=True, gridcolor=BORDER, linecolor=BORDER,
                            tickfont=dict(color=T_LIGHT, size=9), range=[0, 110]),
            angularaxis=dict(linecolor=BORDER, gridcolor=BORDER,
                             tickfont=dict(color=T_MID, size=10)),
        ),
        title="<b>Profil vs Moyenne Globale</b>",
        title_font=dict(size=13, color=T_DARK),
        legend=dict(font=dict(color=T_MID, size=10), bgcolor="rgba(0,0,0,0)",
                    orientation="h", yanchor="bottom", y=-0.18,
                    xanchor="center", x=0.5),
        font=dict(family="Outfit, sans-serif", color=T_MID),
        margin=dict(l=20, r=20, t=50, b=50),
        height=340,
    )
    return fig



# ─────────────────────────────────────────────────────────────────
# PAGE PRINCIPALE
# ─────────────────────────────────────────────────────────────────
section_header(
    "🔍", "Recherche Étudiant",
    guide_title="Comment rechercher ?",
    guide_text="Entrez l'ID numérique de l'étudiant (ex: 1 → ETU-0001). "
               "Utilisez le bouton 🎲 Aléatoire pour explorer un profil au hasard. "
               "L'ID minimum et maximum sont affichés sous le champ."
)

guide_banner(
    "Astuce — Navigation rapide",
    "Utilisez 🎲 Aléatoire pour explorer différents profils et comprendre "
    "la distribution des risques. Les tooltips <b>?</b> de chaque section "
    "expliquent comment lire chaque graphique.",
    steps=["Choisir un étudiant", "Lire la jauge de risque",
           "Analyser les facteurs SHAP", "Consulter l'historique académique"]
)

st.markdown("<br style='margin:6px 0'>", unsafe_allow_html=True)

st.markdown(f"""
<div style="background:{BG_CARD};border:1px solid {BORDER};border-radius:16px;
            padding:26px 26px 20px;box-shadow:0 1px 6px rgba(15,23,42,0.05);margin-bottom:4px;">
  <div style="font-size:15px;font-weight:800;color:{T_DARK};margin-bottom:4px;">
      Saisir l'identifiant étudiant
  </div>
  <div style="font-size:12px;color:{T_LIGHT};font-family:'JetBrains Mono',monospace;margin-bottom:14px;">
      IDs disponibles : {int(df['student_id'].min())} → {int(df['student_id'].max())}
  </div>
""", unsafe_allow_html=True)

col_inp, col_btn, col_rnd = st.columns([3, 1, 1], gap="small")
with col_inp:
    student_id_input = st.number_input(
        "ID", min_value=int(df["student_id"].min()),
        max_value=int(df["student_id"].max()),
        value=int(df["student_id"].min()),
        step=1, label_visibility="collapsed",
    )
with col_btn:
    search = st.button("🔍 Rechercher", type="primary", use_container_width=True)
with col_rnd:
    rnd = st.button("🎲 Aléatoire", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

if rnd:
    st.session_state["active_id"] = int(df.sample(1)["student_id"].iloc[0])
elif search or "active_id" not in st.session_state:
    st.session_state["active_id"] = student_id_input

active_id   = st.session_state.get("active_id", student_id_input)
student_row = df[df["student_id"] == active_id]

if student_row.empty:
    st.markdown(f"""
    <div style="text-align:center;padding:60px 20px;background:{BG_CARD};
                border:1px solid {BORDER};border-radius:16px;margin-top:16px;">
      <div style="font-size:52px;margin-bottom:16px;">🔎</div>
      <div style="font-size:18px;font-weight:800;color:{T_DARK};margin-bottom:8px;">
          Étudiant introuvable
      </div>
      <div style="font-size:13px;color:{T_LIGHT};">
          L'ID <b>{active_id}</b> n'existe pas. Utilisez 🎲 Aléatoire.
      </div>
    </div>""", unsafe_allow_html=True)
    st.stop()

student = student_row.iloc[0]
level   = student["alert_level"]
pct     = student["score_pct"]
color   = alert_color(level)
shap_df = parse_shap(student.get("shap_values", "{}"))
rank    = int((df["score_pct"] > pct).sum()) + 1

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# BLOC 1 : Profil + Jauge + Recommandations
# ══════════════════════════════════════════════════════════════════
section_header(
    "🎯", "Profil & Score de Risque",
    guide_title="Lire la jauge",
    guide_text="La jauge affiche le score de 0 à 100%. "
               "Zone verte (0-40%) = stable, orange (40-70%) = surveiller, "
               "rouge (70-100%) = intervention urgente. "
               "Le rang indique la position parmi tous les étudiants."
)

col_profil, col_gauge, col_reco = st.columns([1.2, 1.5, 1.3], gap="medium")

with col_profil:
    st.markdown(f"""
    <div class="profile-card {level}">
      <div class="profile-avatar {level}">{alert_emoji(level)}</div>
      <div class="profile-id">ETU-{int(student['student_id']):04d}</div>
      <div class="profile-sub">Étudiant · ID #{int(student['student_id'])}</div>
      <div class="profile-badges">
        {badge_alert(level)}
        {badge_pred(student['pred_label'])}
        <span class="badge badge-blue">Rang #{rank}/{len(df)}</span>
      </div>
      <div class="profile-divider"></div>
      <div class="profile-meta">
        <div class="meta-row">
          <span class="meta-key">Score de risque</span>
          <span class="meta-val" style="color:{color};">{pct:.1f}%</span>
        </div>
        <div class="meta-row">
          <span class="meta-key">Niveau d'alerte</span>
          <span class="meta-val">{alert_emoji(level)} {level.capitalize()}</span>
        </div>
        <div class="meta-row">
          <span class="meta-key">Prédiction ML</span>
          <span class="meta-val">{student['pred_label']}</span>
        </div>
        <div class="meta-row">
          <span class="meta-key">Réalité terrain</span>
          <span class="meta-val">{student.get('true_label','—')}</span>
        </div>
        <div class="meta-row">
          <span class="meta-key">Statut prédiction</span>
          <span class="meta-val">{"✅ Correcte" if str(student['pred_label'])==str(student.get('true_label','')) else "❌ Incorrecte"}</span>
        </div>
        <div class="meta-row">
          <span class="meta-key">Note S1</span>
          <span class="meta-val">{f"{safe_val(student,'grade_s1'):.2f}/20" if safe_val(student,'grade_s1') is not None else '—'}</span>
        </div>
        <div class="meta-row">
          <span class="meta-key">Note S2</span>
          <span class="meta-val">{f"{safe_val(student,'grade_s2'):.2f}/20" if safe_val(student,'grade_s2') is not None else '—'}</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with col_gauge:
    st.markdown('<div class="glass-card" style="text-align:center;">'
                '<div class="gauge-label">Score de Risque de Décrochage</div>',
                unsafe_allow_html=True)
    st.plotly_chart(plot_gauge(pct, level), use_container_width=True,
                    config={"displayModeBar": False})
    st.markdown(f"""
    <div style="text-align:center;margin-top:4px;">
      <span style="display:inline-block;
          background:{'rgba(220,38,38,.1)' if level=='rouge' else 'rgba(217,119,6,.1)' if level=='orange' else 'rgba(5,150,105,.1)'};
          border:1px solid {color}44;color:{color};border-radius:20px;
          padding:6px 20px;font-size:13px;font-weight:800;
          font-family:'JetBrains Mono',monospace;letter-spacing:.8px;">
          {alert_emoji(level)} {risk_label(pct)} — {pct:.1f}%
      </span>
    </div>
    <div style="display:flex;justify-content:center;gap:20px;margin-top:16px;flex-wrap:wrap;">
        <div style="text-align:center;">
            <div style="font-size:9px;color:{T_LIGHT};font-family:'JetBrains Mono',monospace;
                        letter-spacing:1px;text-transform:uppercase;margin-bottom:2px;">Vert</div>
            <div style="font-size:11px;color:{C_EMERALD};font-weight:700;">0–40%</div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:9px;color:{T_LIGHT};font-family:'JetBrains Mono',monospace;
                        letter-spacing:1px;text-transform:uppercase;margin-bottom:2px;">Orange</div>
            <div style="font-size:11px;color:{C_AMBER};font-weight:700;">40–70%</div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:9px;color:{T_LIGHT};font-family:'JetBrains Mono',monospace;
                        letter-spacing:1px;text-transform:uppercase;margin-bottom:2px;">Rouge</div>
            <div style="font-size:11px;color:{C_CORAL};font-weight:700;">70–100%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_reco:
    st.markdown(f'<div class="glass-card">'
                f'<div style="font-size:10px;font-weight:700;letter-spacing:2px;'
                f'text-transform:uppercase;color:{T_LIGHT};'
                f'font-family:JetBrains Mono,monospace;margin-bottom:12px;">💡 Recommandations</div>',
                unsafe_allow_html=True)
    recs = get_recommendations(level, shap_df)
    for r_level, ico, title, desc in recs:
        st.markdown(f"""
        <div class="reco-card {r_level}">
          <div class="reco-title">{ico} {title}</div>
          <div class="reco-desc">{desc}</div>
        </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# BLOC 3 : SHAP
# ══════════════════════════════════════════════════════════════════
section_header(
    "🧠", "Analyse des Facteurs de Risque (SHAP)",
    guide_title="Comprendre les SHAP",
    guide_text="SHAP mesure la contribution de chaque variable à la prédiction. "
               "Barre rouge → ce facteur AUGMENTE le risque. "
               "Barre verte → ce facteur RÉDUIT le risque. "
               "La longueur de la barre = intensité de l'impact."
)

if shap_df.empty:
    st.info("Aucune valeur SHAP disponible pour cet étudiant.")
else:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.plotly_chart(plot_shap(shap_df), use_container_width=True,
                    config={"displayModeBar": False})
    st.markdown(f"""
    <div style="display:flex;gap:16px;margin-top:6px;flex-wrap:wrap;">
      <span style="display:inline-flex;align-items:center;gap:6px;font-size:11px;color:{T_MID};">
        <span style="width:12px;height:12px;background:{C_CORAL};border-radius:3px;display:inline-block;"></span>
        Augmente le risque de décrochage
      </span>
      <span style="display:inline-flex;align-items:center;gap:6px;font-size:11px;color:{T_MID};">
        <span style="width:12px;height:12px;background:{C_EMERALD};border-radius:3px;display:inline-block;"></span>
        Réduit le risque de décrochage
      </span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# BLOC 4 : Notes S1/S2 + Admission
# ══════════════════════════════════════════════════════════════════
section_header(
    "📊", "Notes & Résultats Académiques",
    guide_title="Lire les notes",
    guide_text="Le graphique de gauche compare les notes S1 et S2 sur 20. "
               "La ligne orange = seuil de 10/20. "
               "Le graphique de droite montre la note d'admission et "
               "la qualification antérieure sur 200."
)

notes_fig    = plot_notes(student)
admission_fig = plot_admission(student)

if notes_fig or admission_fig:
    col_n, col_a = st.columns(2, gap="medium")
    if notes_fig:
        with col_n:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.plotly_chart(notes_fig, use_container_width=True,
                            config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)
    if admission_fig:
        with col_a:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.plotly_chart(admission_fig, use_container_width=True,
                            config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="glass-card" style="text-align:center;padding:40px;">
        <div style="font-size:14px;color:{T_LIGHT};">Données de notes non disponibles.</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# BLOC 5 : Taux de validation (jauges)
# ══════════════════════════════════════════════════════════════════
taux_fig = plot_taux_validation(student)
if taux_fig:
    section_header(
        "✅", "Taux de Validation par Semestre",
        guide_title="Lire les jauges de validation",
        guide_text="Ces jauges montrent le pourcentage d'unités curriculaires "
                   "validées par rapport aux unités inscrites. "
                   "Vert ≥ 80%, orange entre 50% et 80%, rouge < 50%."
    )
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.plotly_chart(taux_fig, use_container_width=True,
                    config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# BLOC 6 : UC barres groupées + Radar UC S1 vs S2
# ══════════════════════════════════════════════════════════════════
section_header(
    "📚", "Unités Curriculaires — S1 / S2",
    guide_title="Données UC",
    guide_text="UC = Unités Curriculaires (crédits académiques). "
               "Le graphique en barres compare les volumes S1 vs S2. "
               "Le radar superpose les deux semestres pour voir "
               "les forces et faiblesses sur chaque type d'UC."
)

uc_fig    = plot_uc(student)
radar_fig = plot_radar_uc(student)

if uc_fig or radar_fig:
    if uc_fig and radar_fig:
        col_uc, col_r = st.columns([3, 2], gap="medium")
        with col_uc:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.plotly_chart(uc_fig, use_container_width=True,
                            config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)
        with col_r:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.plotly_chart(radar_fig, use_container_width=True,
                            config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)
    elif uc_fig:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.plotly_chart(uc_fig, use_container_width=True,
                        config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="glass-card" style="text-align:center;padding:40px;">
        <div style="font-size:14px;color:{T_LIGHT};">Données UC non disponibles.</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# BLOC 7 : Radar profil vs moyenne globale (nouveau)
# ══════════════════════════════════════════════════════════════════
section_header(
    "🎯", "Profil Étudiant vs Moyenne Globale",
    guide_title="Radar comparatif",
    guide_text="Ce radar compare les performances de l'étudiant (trait coloré) "
               "à la moyenne de tous les étudiants (trait gris pointillé). "
               "Un point en-dehors du trait gris = performance au-dessus de la moyenne."
)

profil_radar = plot_profil_complet(student, df, pct)
if profil_radar:
    col_r1, col_r2 = st.columns([1, 1], gap="medium")
    with col_r1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.plotly_chart(profil_radar, use_container_width=True,
                        config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)
    with col_r2:
        # Résumé comparatif textuel
        g1 = safe_val(student, "grade_s1")
        g2 = safe_val(student, "grade_s2")
        mg1 = df["grade_s1"].mean() if "grade_s1" in df else None
        mg2 = df["grade_s2"].mean() if "grade_s2" in df else None

        def delta_html(val, ref, label, unit=""):
            if val is None or ref is None:
                return ""
            diff  = val - ref
            arrow = "▲" if diff >= 0 else "▼"
            clr   = C_EMERALD if diff >= 0 else C_CORAL
            return (f'<div class="meta-row" style="padding:10px 0;border-bottom:1px solid {BORDER};">'
                    f'<span class="meta-key">{label}</span>'
                    f'<span style="display:flex;align-items:center;gap:8px;">'
                    f'<span class="meta-val">{val:.2f}{unit}</span>'
                    f'<span style="font-size:11px;color:{clr};font-weight:700;'
                    f'font-family:JetBrains Mono,monospace;">'
                    f'{arrow} {abs(diff):.2f} vs moy.</span></span></div>')

        adm  = safe_val(student, "admission_grade")
        madm = df["admission_grade"].mean() if "admission_grade" in df else None
        av1  = safe_val(student, "approved_s1")
        mav1 = df["approved_s1"].mean() if "approved_s1" in df else None
        av2  = safe_val(student, "approved_s2")
        mav2 = df["approved_s2"].mean() if "approved_s2" in df else None

        rows = (delta_html(g1, mg1, "Note S1", "/20") +
                delta_html(g2, mg2, "Note S2", "/20") +
                delta_html(adm, madm, "Admission", "/200") +
                delta_html(av1, mav1, "UC validées S1") +
                delta_html(av2, mav2, "UC validées S2"))

        st.markdown(f"""
        <div class="glass-card">
          <div style="font-size:10px;font-weight:700;letter-spacing:2px;
                      text-transform:uppercase;color:{T_LIGHT};
                      font-family:JetBrains Mono,monospace;margin-bottom:14px;">
              📈 Comparaison vs Moyenne Globale
          </div>
          <div class="profile-meta">{rows}</div>
          <div style="margin-top:16px;font-size:11px;color:{T_LIGHT};line-height:1.7;">
              ▲ = au-dessus de la moyenne · ▼ = en-dessous de la moyenne
          </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# BLOC 8 : Données brutes
# ══════════════════════════════════════════════════════════════════
with st.expander("🗂️ Voir toutes les données brutes de l'étudiant"):
    raw   = student.drop(labels=["shap_values"], errors="ignore").to_dict()
    items = list(raw.items())
    mid   = len(items) // 2
    ca, cb = st.columns(2, gap="medium")
    for col, chunk in [(ca, items[:mid]), (cb, items[mid:])]:
        with col:
            rows_html = "".join(
                f'<div style="display:flex;justify-content:space-between;'
                f'padding:7px 0;border-bottom:1px solid {BORDER};font-size:12px;">'
                f'<span style="font-weight:500;color:{T_LIGHT};">{k}</span>'
                f'<span style="font-weight:700;color:{T_DARK};font-family:JetBrains Mono,monospace;">'
                f'{round(v, 4) if isinstance(v, float) else v}</span></div>'
                for k, v in chunk
            )
            st.markdown(f'<div style="background:{BG_CARD};border:1px solid {BORDER};'
                        f'border-radius:12px;padding:12px 16px;">{rows_html}</div>',
                        unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    f"<div class='page-footer'>VUE INDIVIDUELLE &nbsp;·&nbsp; ETU-{int(active_id):04d} "
    f"&nbsp;·&nbsp; SCORE {pct:.1f}% &nbsp;·&nbsp; {level.upper()}</div>",
    unsafe_allow_html=True,
)