"""
╔══════════════════════════════════════════════════════════════════╗
║  pages/05_Rapports_PDF.py                                        ║
║  Tâche 9 — Génération Automatique de Rapports PDF                ║
║  ─────────────────────────────────────────────────────────────── ║
║  ✅ Fiche individuelle par étudiant à risque                      ║
║  ✅ Contenu : ID anonymisé, score, niveau alerte, top 5 SHAP     ║
║  ✅ Graphique d'évolution académique (notes S1/S2, UC validées)  ║
║  ✅ Recommandations générées dynamiquement selon le profil        ║
║  ✅ Bouton de téléchargement directement dans le dashboard        ║
║  ✅ Génération en lot pour tous les étudiants en zone rouge       ║
║  ✅ Archive ZIP multi-PDF téléchargeable                          ║
║  ✅ Design professionnel cohérent (palette cobalt/blanc)          ║
║                                                                  ║
║  CORRECTIFS APPLIQUÉS :                                          ║
║  - FIX 1 : Suppression de st.set_page_config() (doublon)        ║
║  - FIX 2 : _evolution_cell() déplacée AVANT generer_pdf_...()   ║
║  - FIX 3 : colors.toHex() remplacé par rl_to_hex() (maison)    ║
║  - FIX 4 : BORDER2 ajouté aux imports depuis app_config         ║
╚══════════════════════════════════════════════════════════════════╝
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
import json
import sqlite3
import zipfile
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import streamlit as st

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, Image, NextPageTemplate,
    PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)
from reportlab.platypus.flowables import KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app_config import (
    inject_css, render_topbar, section_header, sidebar_kpis,
    load_predictions, compute_kpis, guide_banner, guide_tooltip,
    badge_alert, badge_pred,
    BG_CARD, BG_PAGE, BG_SIDEBAR, BORDER, BORDER2, T_DARK, T_MID, T_LIGHT, T_WHITE,
    C_COBALT, C_CORAL, C_AMBER, C_EMERALD, C_VIOLET,
    DB_PATH,
)

# ─────────────────────────────────────────────────────────────────
#  PALETTE REPORTLAB (hex -> RGB 0-1)
# ─────────────────────────────────────────────────────────────────

def hex_to_rl(hex_color: str):
    """Convertit un code hex '#RRGGBB' en couleur ReportLab."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return colors.Color(r / 255, g / 255, b / 255)


def rl_to_hex(c) -> str:
    """
    Convertit une couleur ReportLab en chaîne '#rrggbb'.
    Remplace colors.toHex() absent des versions récentes de ReportLab.
    """
    r = int(round(c.red   * 255))
    g = int(round(c.green * 255))
    b = int(round(c.blue  * 255))
    return "#{:02x}{:02x}{:02x}".format(r, g, b)


COB  = hex_to_rl("#1B4FD8")   # cobalt
COR  = hex_to_rl("#DC2626")   # coral/rouge
AMB  = hex_to_rl("#D97706")   # amber/orange
EME  = hex_to_rl("#059669")   # emerald/vert
VIO  = hex_to_rl("#6D28D9")   # violet
DARK = hex_to_rl("#0F172A")   # texte sombre
MID  = hex_to_rl("#475569")   # texte moyen
LIGH = hex_to_rl("#94A3B8")   # texte clair
BG   = hex_to_rl("#F8FAFC")   # fond page
BORD = hex_to_rl("#E2E8F0")   # bordures

ALERT_COLORS = {"rouge": COR, "orange": AMB, "vert": EME}
ALERT_BG     = {
    "rouge":  hex_to_rl("#FEF2F2"),
    "orange": hex_to_rl("#FFFBEB"),
    "vert":   hex_to_rl("#ECFDF5"),
}
ALERT_EMOJI  = {"rouge": "ROUGE", "orange": "ORANGE", "vert": "VERT"}
ALERT_LABEL  = {
    "rouge":  "Risque Élevé — Intervention Immédiate",
    "orange": "Risque Modéré — Surveillance Renforcée",
    "vert":   "Situation Stable — Suivi Mensuel",
}

# ─────────────────────────────────────────────────────────────────
#  TRADUCTIONS SHAP
# ─────────────────────────────────────────────────────────────────

TRADUCTIONS = {
    "Curricular units 1st sem (approved)":            "Unités validées S1",
    "Curricular units 2nd sem (approved)":            "Unités validées S2",
    "Curricular units 1st sem (grade)":               "Moyenne S1",
    "Curricular units 2nd sem (grade)":               "Moyenne S2",
    "Curricular units 1st sem (enrolled)":            "Unités inscrites S1",
    "Curricular units 2nd sem (enrolled)":            "Unités inscrites S2",
    "Curricular units 1st sem (evaluations)":         "Évaluations S1",
    "Curricular units 2nd sem (evaluations)":         "Évaluations S2",
    "Curricular units 1st sem (without evaluations)": "Sans évaluation S1",
    "Curricular units 2nd sem (without evaluations)": "Sans évaluation S2",
    "Curricular units 1st sem (credited)":            "Crédits S1",
    "Curricular units 2nd sem (credited)":            "Crédits S2",
    "Tuition fees up to date":                        "Frais de scolarité à jour",
    "Age at enrollment":                              "Âge à l'inscription",
    "Scholarship holder":                             "Boursier",
    "Gender":                                         "Genre",
    "Debtor":                                         "Situation d'endettement",
    "Displaced":                                      "Étudiant déplacé",
    "Admission grade":                                "Note d'admission",
    "Previous qualification (grade)":                 "Qualification antérieure",
    "Unemployment rate":                              "Taux de chômage",
    "Inflation rate":                                 "Taux d'inflation",
    "GDP":                                            "PIB",
    "International":                                  "Étudiant international",
    "Educational special needs":                      "Besoins éducatifs spéciaux",
    "Mother's qualification":                         "Niveau éducation (mère)",
    "Father's qualification":                         "Niveau éducation (père)",
    "Application order":                              "Ordre de candidature",
    "Daytime/evening attendance_1":                   "Cours en journée",
}


def traduire(feature: str) -> str:
    if feature in TRADUCTIONS:
        return TRADUCTIONS[feature]
    for cle, val in TRADUCTIONS.items():
        if cle.lower() in feature.lower():
            return val
    clean = feature.split("(")[0].strip()
    return clean[:45]


# ─────────────────────────────────────────────────────────────────
#  BASE DE DONNÉES
# ─────────────────────────────────────────────────────────────────

@st.cache_resource
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def charger_profil(student_id: int) -> dict | None:
    cur = get_connection().cursor()
    cur.execute("""
        SELECT student_id, risk_score, alert_level, true_label, pred_label,
               shap_values, grade_s1, grade_s2, admission_grade,
               approved_s1, approved_s2, enrolled_s1, enrolled_s2,
               without_eval_s1, without_eval_s2
        FROM predictions WHERE student_id = ?
    """, (student_id,))
    row = cur.fetchone()
    if row is None:
        return None

    shap_dict = json.loads(row[5]) if row[5] else {}
    top_shap  = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)[:5]

    def sv(v): return float(v) if v is not None else 0.0

    return {
        "student_id":       row[0],
        "risk_score":       sv(row[1]),
        "alert_level":      row[2],
        "true_label":       row[3],
        "pred_label":       row[4],
        "grade_s1":         sv(row[6]),
        "grade_s2":         sv(row[7]),
        "admission_grade":  sv(row[8]),
        "approved_s1":      sv(row[9]),
        "approved_s2":      sv(row[10]),
        "enrolled_s1":      sv(row[11]),
        "enrolled_s2":      sv(row[12]),
        "without_eval_s1":  sv(row[13]),
        "without_eval_s2":  sv(row[14]),
        "top_shap":         top_shap,
    }


def charger_etudiants_zone(zone: str = "rouge") -> list:
    cur = get_connection().cursor()
    cur.execute("""
        SELECT student_id, risk_score, alert_level
        FROM predictions
        WHERE alert_level = ?
        ORDER BY risk_score DESC
    """, (zone,))
    return cur.fetchall()


# ─────────────────────────────────────────────────────────────────
#  RECOMMANDATIONS DYNAMIQUES
# ─────────────────────────────────────────────────────────────────

def generer_recommandations(profil: dict) -> list:
    """Génère 3-5 recommandations adaptées au profil SHAP de l'étudiant."""
    niveau = profil["alert_level"]
    recs   = []

    if niveau == "rouge":
        recs.append((
            "Entretien individuel urgent",
            "Planifier un rendez-vous avec le conseiller pédagogique dans les 48 heures. "
            "Évaluer la situation globale de l'étudiant et les obstacles à sa réussite."
        ))
        recs.append((
            "Contact avec la famille",
            "Informer les responsables légaux de la situation et activer le dispositif "
            "d'accompagnement institutionnel prévu par l'établissement."
        ))
        recs.append((
            "Plan de remédiation personnalisé",
            "Définir des objectifs hebdomadaires mesurables avec l'étudiant. "
            "Mettre en place un suivi rapproché et des points de contrôle réguliers."
        ))
    elif niveau == "orange":
        recs.append((
            "Renforcement du suivi pédagogique",
            "Augmenter la fréquence des entretiens de suivi à une fois par semaine. "
            "Identifier les matières en difficulté et proposer un accompagnement ciblé."
        ))
        recs.append((
            "Programme de tutorat par les pairs",
            "Proposer un binôme avec un étudiant performant de la même filière "
            "pour renforcer la compréhension et la motivation."
        ))
    else:
        recs.append((
            "Maintien du suivi mensuel",
            "Continuer le suivi habituel avec des points mensuels. "
            "Encourager la participation aux activités parascolaires et associatives."
        ))

    for feature, valeur in profil["top_shap"]:
        if valeur <= 0:
            continue
        feat_low = feature.lower()

        if any(x in feat_low for x in ["grade", "note", "approved", "curricular"]):
            recs.append((
                "Soutien académique renforcé",
                f"Les résultats académiques ({traduire(feature)}) constituent un facteur "
                "de risque majeur. Orienter vers des séances de soutien scolaire "
                "ou des ressources pédagogiques complémentaires."
            ))
            break

        if any(x in feat_low for x in ["debt", "tuition", "financ"]):
            recs.append((
                "Accompagnement financier",
                f"Des difficultés financières ont été détectées ({traduire(feature)}). "
                "Orienter l'étudiant vers le service des aides sociales et des bourses "
                "disponibles au sein de l'établissement."
            ))
            break

        if any(x in feat_low for x in ["without_eval", "evaluations", "enrolled"]):
            recs.append((
                "Suivi de la présence aux évaluations",
                "Un nombre élevé d'unités sans évaluation a été détecté. "
                "Vérifier les raisons des absences aux examens et proposer "
                "des aménagements si nécessaire."
            ))
            break

    return recs[:5]


# ─────────────────────────────────────────────────────────────────
#  HELPER — CELLULE ÉVOLUTION  (FIX 2 : défini AVANT generer_pdf_individuel)
# ─────────────────────────────────────────────────────────────────

def _make_body_style():
    """Crée un style body réutilisable pour _evolution_cell."""
    return ParagraphStyle(
        "BodyEvo",
        fontSize=9.5, textColor=hex_to_rl("#0F172A"),
        fontName="Helvetica", alignment=TA_CENTER, leading=13,
    )


def _evolution_cell(v1: float, v2: float, style, inversed: bool = False):
    """Cellule affichant la tendance entre S1 et S2."""
    diff = v2 - v1
    if abs(diff) < 0.01:
        return Paragraph("→ Stable", style)
    if (diff > 0 and not inversed) or (diff < 0 and inversed):
        arrow    = "▲"
        rl_color = "#059669"  # vert
    else:
        arrow    = "▼"
        rl_color = "#DC2626"  # rouge
    sign = "+" if diff > 0 else ""
    return Paragraph(
        f'<font color="{rl_color}"><b>{arrow} {sign}{diff:.2f}</b></font>',
        style,
    )


# ─────────────────────────────────────────────────────────────────
#  GRAPHIQUE MATPLOTLIB — ÉVOLUTION ACADÉMIQUE
# ─────────────────────────────────────────────────────────────────

def generer_graphique_evolution(profil: dict) -> io.BytesIO:
    """
    Génère un graphique double axe :
    - Barres : notes S1 / S2 (axe gauche)
    - Barres secondaires : UC validées S1/S2 (axe droit)
    Retourne un buffer PNG.
    """
    fig, ax1 = plt.subplots(figsize=(7, 3.2))
    fig.patch.set_facecolor("#FFFFFF")
    ax1.set_facecolor("#F8FAFC")

    categories  = ["Semestre 1", "Semestre 2"]
    notes       = [profil["grade_s1"], profil["grade_s2"]]
    uc_validees = [profil["approved_s1"], profil["approved_s2"]]

    x     = np.arange(len(categories))
    width = 0.35

    bars1 = ax1.bar(
        x - width / 2, notes, width,
        label="Moyenne (/20)",
        color=["#1B4FD8", "#6D28D9"],
        alpha=0.82, zorder=3,
        linewidth=0, edgecolor="none",
    )
    ax1.set_ylabel("Note (/20)", color="#475569", fontsize=10, labelpad=8)
    ax1.set_ylim(0, 24)
    ax1.tick_params(axis="y", labelcolor="#475569", labelsize=9)
    ax1.axhline(y=10, color="#D97706", linestyle="--", linewidth=1.2,
                alpha=0.7, label="Seuil 10/20", zorder=2)

    for bar in bars1:
        h = bar.get_height()
        if h > 0:
            ax1.text(
                bar.get_x() + bar.get_width() / 2, h + 0.3,
                f"{h:.1f}", ha="center", va="bottom",
                fontsize=9, fontweight="bold", color="#0F172A",
            )

    ax2 = ax1.twinx()
    bars2 = ax2.bar(
        x + width / 2, uc_validees, width,
        label="UC Validées",
        color=["#059669", "#34D399"],
        alpha=0.75, zorder=3,
        linewidth=0, edgecolor="none",
    )
    ax2.set_ylabel("UC Validées", color="#059669", fontsize=10, labelpad=8)
    ax2.set_ylim(0, max(max(uc_validees) * 1.6, 12))
    ax2.tick_params(axis="y", labelcolor="#059669", labelsize=9)

    for bar in bars2:
        h = bar.get_height()
        if h > 0:
            ax2.text(
                bar.get_x() + bar.get_width() / 2, h + 0.15,
                f"{int(h)}", ha="center", va="bottom",
                fontsize=9, fontweight="bold", color="#059669",
            )

    ax1.set_xticks(x)
    ax1.set_xticklabels(categories, fontsize=10, color="#0F172A", fontweight="600")
    ax1.grid(axis="y", color="#E2E8F0", linewidth=0.8, zorder=0)
    ax1.set_axisbelow(True)

    for spine in ax1.spines.values():
        spine.set_color("#E2E8F0")
    for spine in ax2.spines.values():
        spine.set_color("#E2E8F0")

    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(
        handles1 + handles2, labels1 + labels2,
        loc="upper right", fontsize=8,
        framealpha=0.9, edgecolor="#E2E8F0",
        fancybox=True, frameon=True,
    )

    plt.title("Évolution Académique — S1 / S2", fontsize=11,
              fontweight="bold", color="#0F172A", pad=12)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="#FFFFFF")
    plt.close(fig)
    buf.seek(0)
    return buf


# ─────────────────────────────────────────────────────────────────
#  GRAPHIQUE MATPLOTLIB — SHAP BARRES HORIZONTALES
# ─────────────────────────────────────────────────────────────────

def generer_graphique_shap(profil: dict) -> io.BytesIO:
    """Génère le graphique des 5 facteurs SHAP les plus influents."""
    top_shap = profil["top_shap"]
    if not top_shap:
        fig, ax = plt.subplots(figsize=(7, 2))
        ax.text(0.5, 0.5, "Données SHAP non disponibles",
                ha="center", va="center", color="#94A3B8")
        ax.axis("off")
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=120, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return buf

    features    = [traduire(f)[:38] for f, _ in top_shap]
    values      = [v for _, v in top_shap]
    colors_bars = ["#DC2626" if v > 0 else "#059669" for v in values]

    fig, ax = plt.subplots(figsize=(7, max(2.8, len(features) * 0.65)))
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F8FAFC")

    y_pos = range(len(features) - 1, -1, -1)
    bars  = ax.barh(
        list(y_pos), values, color=colors_bars,
        alpha=0.82, height=0.55,
        linewidth=0, edgecolor="none",
    )

    for bar, val in zip(bars, values):
        direction = "Aggravant ↑" if val > 0 else "Protecteur ↓"
        x_pos = bar.get_width() + (0.001 if val >= 0 else -0.001)
        ha    = "left" if val >= 0 else "right"
        ax.text(x_pos, bar.get_y() + bar.get_height() / 2,
                f" {direction}", va="center", ha=ha,
                fontsize=7.5, color="#475569")

    ax.axvline(x=0, color="#94A3B8", linewidth=1.2, linestyle="-")
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(features, fontsize=9, color="#0F172A")
    ax.set_xlabel("Valeur SHAP (impact sur le score de risque)", fontsize=9,
                  color="#475569", labelpad=6)
    ax.grid(axis="x", color="#E2E8F0", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)

    for spine in ax.spines.values():
        spine.set_color("#E2E8F0")

    patch_rouge = mpatches.Patch(color="#DC2626", alpha=0.82, label="Augmente le risque")
    patch_vert  = mpatches.Patch(color="#059669", alpha=0.82, label="Réduit le risque")
    ax.legend(handles=[patch_rouge, patch_vert], loc="lower right",
              fontsize=8, framealpha=0.9, edgecolor="#E2E8F0")

    plt.title("Top 5 Facteurs de Risque (SHAP)", fontsize=11,
              fontweight="bold", color="#0F172A", pad=10)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="#FFFFFF")
    plt.close(fig)
    buf.seek(0)
    return buf


# ─────────────────────────────────────────────────────────────────
#  GÉNÉRATION DU PDF — FICHE INDIVIDUELLE
# ─────────────────────────────────────────────────────────────────

def generer_pdf_individuel(profil: dict, include_graphs: bool = True) -> bytes:
    """
    Génère la fiche PDF complète d'un étudiant à risque.
    Retourne les bytes du PDF.
    """
    buf       = io.BytesIO()
    niveau    = profil["alert_level"]
    al_color  = ALERT_COLORS.get(niveau, COB)
    al_bg     = ALERT_BG.get(niveau, BG)
    score_pct = round(profil["risk_score"] * 100, 1)
    date_str  = datetime.now().strftime("%d/%m/%Y à %H:%M")

    # FIX 3 : rl_to_hex() remplace colors.toHex() (inexistant dans certaines versions)
    al_color_hex = rl_to_hex(al_color)   # ex: '#dc2626'
    cob_hex      = rl_to_hex(COB)        # '#1b4fd8'
    cor_hex      = rl_to_hex(COR)        # '#dc2626'
    eme_hex      = rl_to_hex(EME)        # '#059669'

    # ── Styles ──────────────────────────────────────────────────
    def make_style(name, **kwargs):
        return ParagraphStyle(name, **kwargs)

    style_section = make_style(
        "Section",
        fontSize=11, textColor=COB, fontName="Helvetica-Bold",
        alignment=TA_LEFT, spaceBefore=14, spaceAfter=6,
    )
    style_body = make_style(
        "Body",
        fontSize=9.5, textColor=DARK, fontName="Helvetica",
        alignment=TA_LEFT, leading=14, spaceAfter=4,
    )
    style_small = make_style(
        "Small",
        fontSize=8, textColor=MID, fontName="Helvetica",
        alignment=TA_LEFT, leading=12,
    )
    style_reco_title = make_style(
        "RecoTitle",
        fontSize=10, textColor=DARK, fontName="Helvetica-Bold",
        alignment=TA_LEFT, spaceBefore=6, spaceAfter=2,
    )
    style_reco_body = make_style(
        "RecoBody",
        fontSize=9, textColor=MID, fontName="Helvetica",
        alignment=TA_LEFT, leading=13, spaceAfter=4,
    )
    style_footer = make_style(
        "Footer",
        fontSize=7.5, textColor=LIGH, fontName="Helvetica",
        alignment=TA_CENTER,
    )
    style_center = make_style(
        "Center",
        fontSize=9.5, textColor=DARK, fontName="Helvetica",
        alignment=TA_CENTER, leading=13,
    )

    # ── Document ─────────────────────────────────────────────────
    PAGE_W, PAGE_H = A4
    MARGIN = 1.8 * cm

    def header_footer(canvas_obj, doc_obj):
        canvas_obj.saveState()

        # En-tête
        canvas_obj.setFillColor(COB)
        canvas_obj.rect(0, PAGE_H - 3.6 * cm, PAGE_W, 3.6 * cm, fill=1, stroke=0)

        canvas_obj.setFillColor(colors.white)
        canvas_obj.setFont("Helvetica-Bold", 16)
        canvas_obj.drawString(
            MARGIN, PAGE_H - 1.4 * cm,
            f"FICHE DE SUIVI — ETU-{profil['student_id']:04d}"
        )

        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(colors.Color(1, 1, 1, 0.65))
        canvas_obj.drawString(
            MARGIN, PAGE_H - 2.0 * cm,
            f"Système Anti-Décrochage Scolaire  ·  Généré le {date_str}  ·  Modèle ML + SHAP"
        )

        # Badge niveau d'alerte (coin droit)
        badge_label = ALERT_EMOJI.get(niveau, "—").upper()
        bx = PAGE_W - MARGIN - 2.8 * cm
        by = PAGE_H - 2.4 * cm
        canvas_obj.setFillColor(colors.white)
        canvas_obj.roundRect(bx, by, 2.8 * cm, 0.85 * cm, 4, fill=1, stroke=0)
        canvas_obj.setFillColor(al_color)
        canvas_obj.setFont("Helvetica-Bold", 9)
        canvas_obj.drawCentredString(
            bx + 1.4 * cm, by + 0.27 * cm,
            f"ZONE {badge_label}"
        )

        # Barre de couleur sous l'en-tête
        canvas_obj.setFillColor(al_color)
        canvas_obj.rect(0, PAGE_H - 3.8 * cm, PAGE_W, 0.22 * cm, fill=1, stroke=0)

        # Pied de page
        canvas_obj.setFillColor(BORD)
        canvas_obj.rect(0, 0, PAGE_W, 1.2 * cm, fill=1, stroke=0)
        canvas_obj.setFillColor(MID)
        canvas_obj.setFont("Helvetica", 7.5)
        canvas_obj.drawCentredString(
            PAGE_W / 2, 0.42 * cm,
            f"Document confidentiel — Usage pédagogique interne  ·  "
            f"Page {doc_obj.page}  ·  ETU-{profil['student_id']:04d}  ·  "
            f"Score {score_pct}%"
        )
        canvas_obj.restoreState()

    frame    = Frame(
        MARGIN, 1.6 * cm,
        PAGE_W - 2 * MARGIN,
        PAGE_H - 3.8 * cm - 1.6 * cm,
        id="main",
    )
    template = PageTemplate(id="all", frames=[frame], onPage=header_footer)
    doc = BaseDocTemplate(
        buf, pagesize=A4, pageTemplates=[template],
        title=f"Fiche ETU-{profil['student_id']:04d}",
        author="Système Anti-Décrochage",
    )

    story = []

    # ═══════════════════════════════════════════════════════
    # SECTION 1 — RÉSUMÉ EXÉCUTIF
    # ═══════════════════════════════════════════════════════
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("📋  Résumé du Profil", style_section))
    story.append(HRFlowable(width="100%", thickness=1, color=BORD, spaceAfter=8))

    filled   = int(score_pct / 5)
    empty    = 20 - filled
    bar_text = "█" * filled + "░" * empty

    summary_data = [
        ["Identifiant",     f"ETU-{profil['student_id']:04d}",
         "Score de risque", f"{score_pct:.1f} %"],
        ["Niveau d'alerte", ALERT_LABEL.get(niveau, niveau.upper()),
         "Prédiction ML",   profil["pred_label"]],
        ["Situation réelle", profil["true_label"] or "—",
         "Note admission",   f"{profil['admission_grade']:.1f} / 200"],
    ]
    summary_table = Table(
        summary_data,
        colWidths=[3.2 * cm, 6.2 * cm, 3.2 * cm, 4.0 * cm],
    )
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), hex_to_rl("#EFF6FF")),
        ("BACKGROUND", (2, 0), (2, -1), hex_to_rl("#EFF6FF")),
        ("BACKGROUND", (0, 1), (-1, 1), al_bg),
        ("TEXTCOLOR",  (0, 0), (0, -1), COB),
        ("TEXTCOLOR",  (2, 0), (2, -1), COB),
        ("TEXTCOLOR",  (1, 0), (1, -1), DARK),
        ("TEXTCOLOR",  (3, 0), (3, -1), al_color),
        ("FONTNAME",   (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",   (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTNAME",   (1, 0), (1, -1), "Helvetica"),
        ("FONTNAME",   (3, 0), (3, -1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("PADDING",    (0, 0), (-1, -1), 7),
        ("GRID",       (0, 0), (-1, -1), 0.5, BORD),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, al_bg, colors.white]),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(summary_table)

    # Barre de score visuelle
    story.append(Spacer(1, 0.3 * cm))
    bar_data = [
        [
            Paragraph("<b>Score de risque</b>", style_small),
            Paragraph(
                f'<font name="Courier" size="9" color="{al_color_hex}">'
                f'{bar_text}</font>',
                style_small,
            ),
            Paragraph(
                f'<b><font color="{al_color_hex}">{score_pct:.1f}%</font></b>',
                make_style("SP", fontSize=11, fontName="Helvetica-Bold",
                           alignment=TA_RIGHT, textColor=al_color),
            ),
        ]
    ]
    bar_table = Table(bar_data, colWidths=[3 * cm, 9.8 * cm, 2.2 * cm])
    bar_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), al_bg),
        ("GRID",       (0, 0), (-1, -1), 0.5, BORD),
        ("PADDING",    (0, 0), (-1, -1), 7),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(bar_table)

    # ═══════════════════════════════════════════════════════
    # SECTION 2 — GRAPHIQUE ÉVOLUTION ACADÉMIQUE
    # ═══════════════════════════════════════════════════════
    if include_graphs:
        story.append(Spacer(1, 0.4 * cm))
        story.append(Paragraph("📈  Évolution Académique", style_section))
        story.append(HRFlowable(width="100%", thickness=1, color=BORD, spaceAfter=6))

        graph_buf = generer_graphique_evolution(profil)
        img_evo   = Image(graph_buf, width=14.5 * cm, height=6.2 * cm)
        story.append(img_evo)

    # ═══════════════════════════════════════════════════════
    # SECTION 3 — TOP 5 FACTEURS SHAP
    # ═══════════════════════════════════════════════════════
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("🔍  Top 5 Facteurs de Risque (Analyse SHAP)", style_section))
    story.append(HRFlowable(width="100%", thickness=1, color=BORD, spaceAfter=6))

    if profil["top_shap"]:
        shap_rows = [[
            Paragraph("<b>Rang</b>",      style_small),
            Paragraph("<b>Facteur</b>",   style_small),
            Paragraph("<b>Direction</b>", style_small),
            Paragraph("<b>Intensité</b>", style_small),
        ]]
        for i, (feature, valeur) in enumerate(profil["top_shap"], 1):
            direction = "Augmente le risque ↑" if valeur > 0 else "Réduit le risque ↓"
            # FIX 3 : utiliser cor_hex / eme_hex (issus de rl_to_hex)
            dir_hex  = cor_hex if valeur > 0 else eme_hex
            dir_rl   = COR    if valeur > 0 else EME
            abs_v    = abs(valeur)
            intensite = "MAJEUR" if abs_v > 0.03 else "MODÉRÉ" if abs_v > 0.01 else "MINEUR"

            shap_rows.append([
                Paragraph(
                    f"<b>#{i}</b>",
                    make_style(f"R{i}", fontSize=9, fontName="Helvetica-Bold",
                               alignment=TA_CENTER, textColor=COB),
                ),
                Paragraph(traduire(feature), style_body),
                Paragraph(
                    f'<font color="{dir_hex}">{direction}</font>',
                    make_style(f"D{i}", fontSize=9, fontName="Helvetica-Bold",
                               alignment=TA_LEFT, textColor=dir_rl),
                ),
                Paragraph(
                    f'<font color="{dir_hex}">{intensite}</font>',
                    make_style(f"I{i}", fontSize=9, fontName="Helvetica-Bold",
                               alignment=TA_CENTER, textColor=dir_rl),
                ),
            ])

        shap_table = Table(
            shap_rows,
            colWidths=[1.2 * cm, 7.5 * cm, 4.8 * cm, 2.5 * cm],
        )
        shap_table.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0),  hex_to_rl("#EFF6FF")),
            ("TEXTCOLOR",      (0, 0), (-1, 0),  COB),
            ("FONTNAME",       (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",       (0, 0), (-1, -1), 9),
            ("PADDING",        (0, 0), (-1, -1), 6),
            ("GRID",           (0, 0), (-1, -1), 0.5, BORD),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, hex_to_rl("#F8FAFC")]),
            ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN",          (0, 0), (0, -1),  "CENTER"),
            ("ALIGN",          (3, 0), (3, -1),  "CENTER"),
        ]))
        story.append(shap_table)

        if include_graphs:
            story.append(Spacer(1, 0.3 * cm))
            shap_buf = generer_graphique_shap(profil)
            img_shap = Image(shap_buf, width=14.5 * cm, height=5.5 * cm)
            story.append(img_shap)
    else:
        story.append(Paragraph(
            "Données SHAP non disponibles pour cet étudiant.", style_body
        ))

    # ═══════════════════════════════════════════════════════
    # SECTION 4 — DONNÉES ACADÉMIQUES DÉTAILLÉES
    # ═══════════════════════════════════════════════════════
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("📚  Données Académiques Détaillées", style_section))
    story.append(HRFlowable(width="100%", thickness=1, color=BORD, spaceAfter=6))

    acad_data = [
        [
            Paragraph("<b>Indicateur</b>",   style_small),
            Paragraph("<b>Semestre 1</b>",   style_small),
            Paragraph("<b>Semestre 2</b>",   style_small),
            Paragraph("<b>Évolution</b>",    style_small),
        ],
        [
            Paragraph("Moyenne générale", style_body),
            Paragraph(f"{profil['grade_s1']:.2f} / 20", style_center),
            Paragraph(f"{profil['grade_s2']:.2f} / 20", style_center),
            _evolution_cell(profil["grade_s1"], profil["grade_s2"], style_center),
        ],
        [
            Paragraph("Unités curriculaires validées", style_body),
            Paragraph(f"{int(profil['approved_s1'])}", style_center),
            Paragraph(f"{int(profil['approved_s2'])}", style_center),
            _evolution_cell(profil["approved_s1"], profil["approved_s2"], style_center),
        ],
        [
            Paragraph("Unités curriculaires inscrites", style_body),
            Paragraph(f"{int(profil['enrolled_s1'])}", style_center),
            Paragraph(f"{int(profil['enrolled_s2'])}", style_center),
            _evolution_cell(profil["enrolled_s1"], profil["enrolled_s2"], style_center),
        ],
        [
            Paragraph("Unités sans évaluation", style_body),
            Paragraph(f"{int(profil['without_eval_s1'])}", style_center),
            Paragraph(f"{int(profil['without_eval_s2'])}", style_center),
            _evolution_cell(
                profil["without_eval_s1"], profil["without_eval_s2"],
                style_center, inversed=True,
            ),
        ],
    ]

    acad_table = Table(
        acad_data,
        colWidths=[6.5 * cm, 2.8 * cm, 2.8 * cm, 4.4 * cm],
    )
    acad_table.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0), hex_to_rl("#EFF6FF")),
        ("TEXTCOLOR",      (0, 0), (-1, 0), COB),
        ("FONTNAME",       (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",       (0, 0), (-1, -1), 9),
        ("PADDING",        (0, 0), (-1, -1), 6),
        ("GRID",           (0, 0), (-1, -1), 0.5, BORD),
        ("ALIGN",          (1, 0), (3, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, hex_to_rl("#F8FAFC")]),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(acad_table)

    # ═══════════════════════════════════════════════════════
    # SECTION 5 — RECOMMANDATIONS
    # ═══════════════════════════════════════════════════════
    recs = generer_recommandations(profil)
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("💡  Recommandations d'Intervention", style_section))
    story.append(HRFlowable(width="100%", thickness=1, color=BORD, spaceAfter=6))

    reco_rows = []
    for i, (titre, desc) in enumerate(recs, 1):
        reco_rows.append([
            Paragraph(
                f'<b><font color="{al_color_hex}">{i}.</font></b>',
                make_style(f"N{i}", fontSize=11, fontName="Helvetica-Bold",
                           alignment=TA_CENTER, textColor=al_color),
            ),
            [
                Paragraph(f"<b>{titre}</b>", style_reco_title),
                Paragraph(desc, style_reco_body),
            ],
        ])

    reco_table = Table(reco_rows, colWidths=[1.0 * cm, 15.5 * cm])
    reco_table.setStyle(TableStyle([
        ("FONTSIZE",       (0, 0), (-1, -1), 9),
        ("PADDING",        (0, 0), (-1, -1), 7),
        ("GRID",           (0, 0), (-1, -1), 0.5, BORD),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, al_bg]),
        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
        ("ALIGN",          (0, 0), (0, -1),  "CENTER"),
    ]))
    story.append(reco_table)

    # ═══════════════════════════════════════════════════════
    # SECTION 6 — NOTE FINALE
    # ═══════════════════════════════════════════════════════
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORD, spaceAfter=6))
    story.append(Paragraph(
        "Ce document est généré automatiquement par le Système Intelligent de Prédiction "
        "du Décrochage Scolaire. Les prédictions sont basées sur un modèle de Machine Learning "
        "et les valeurs SHAP. Elles ne remplacent pas le jugement professionnel du conseiller "
        "pédagogique. Usage strictement confidentiel et réservé au personnel pédagogique autorisé.",
        style_footer,
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()


# ─────────────────────────────────────────────────────────────────
#  GÉNÉRATION EN LOT — ZIP
# ─────────────────────────────────────────────────────────────────

def generer_lot_zip(
    etudiants: list,
    include_graphs: bool = True,
    progress_bar=None,
) -> bytes:
    """
    Génère un ZIP contenant un PDF par étudiant.
    etudiants : list de (student_id, risk_score, alert_level)
    """
    zip_buf = io.BytesIO()
    total   = len(etudiants)

    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for i, (sid, rscore, level) in enumerate(etudiants):
            profil = charger_profil(sid)
            if profil is None:
                continue
            try:
                pdf_bytes = generer_pdf_individuel(profil, include_graphs)
                filename  = f"fiche_ETU-{sid:04d}_{level}.pdf"
                zf.writestr(filename, pdf_bytes)
            except Exception as e:
                st.warning(f"ETU-{sid:04d} : erreur PDF ({e})")

            if progress_bar:
                progress_bar.progress(
                    (i + 1) / total,
                    text=f"Génération {i+1}/{total}…"
                )

    zip_buf.seek(0)
    return zip_buf.read()


# ─────────────────────────────────────────────────────────────────
#  PAGE STREAMLIT
# ─────────────────────────────────────────────────────────────────

def main():
    # FIX 1 : PAS de st.set_page_config() ici — c'est main.py qui le fait.
    inject_css()

    df   = load_predictions(DB_PATH)
    kpis = compute_kpis(df)
    sidebar_kpis(kpis, "📄", "Rapports PDF", "GÉNÉRATION AUTOMATIQUE")
    render_topbar(
        "📄", "Génération Automatique de Rapports PDF",
        "Fiches individuelles · Top 5 SHAP · Graphiques · Lot ZIP",
        kpis["total"],
    )

    guide_banner(
        "Comment générer un rapport ?",
        "Deux modes disponibles : <b>Individuel</b> pour télécharger la fiche d'un étudiant "
        "précis, ou <b>Lot</b> pour générer tous les étudiants d'une zone en un seul ZIP.",
        steps=[
            "Choisissez le mode (individuel ou lot)",
            "Sélectionnez l'étudiant ou la zone d'alerte",
            "Cliquez sur Générer",
            "Téléchargez le PDF ou le ZIP",
        ],
    )

    st.markdown("<br>", unsafe_allow_html=True)

    tab_ind, tab_lot = st.tabs(["📝 Rapport Individuel", "📦 Génération en Lot"])

    # ════════════════════════════════════════════════════════════
    # TAB 1 — INDIVIDUEL
    # ════════════════════════════════════════════════════════════
    with tab_ind:
        section_header(
            "👤", "Rapport Individuel",
            guide_title="Rapport par étudiant",
            guide_text="Saisissez l'ID d'un étudiant pour générer sa fiche complète : "
                       "résumé, graphiques d'évolution, top 5 SHAP et recommandations.",
        )

        col1, col2, col3 = st.columns([2, 1, 1], gap="medium")
        with col1:
            student_id_input = st.number_input(
                "ID Étudiant",
                min_value=int(df["student_id"].min()),
                max_value=int(df["student_id"].max()),
                value=int(df["student_id"].min()),
                step=1,
            )
        with col2:
            include_graphs = st.toggle("Inclure les graphiques", value=True)
        with col3:
            btn_gen = st.button("⚙️ Générer la fiche", type="primary",
                                use_container_width=True)
            btn_rnd = st.button("🎲 Étudiant aléatoire", use_container_width=True)

        if btn_rnd:
            student_id_input = int(df.sample(1)["student_id"].iloc[0])
            st.session_state["pdf_sid"] = student_id_input
            st.rerun()

        if "pdf_sid" in st.session_state:
            student_id_input = st.session_state["pdf_sid"]

        if btn_gen or "pdf_sid" in st.session_state:
            profil = charger_profil(student_id_input)

            if profil is None:
                st.error(f"Étudiant ETU-{student_id_input:04d} introuvable.")
            else:
                niveau        = profil["alert_level"]
                score_pct     = round(profil["risk_score"] * 100, 1)
                al_color_hex  = {"rouge": C_CORAL, "orange": C_AMBER,
                                 "vert": C_EMERALD}.get(niveau, C_COBALT)

                st.markdown(f"""
                <div style="background:{BG_CARD};border:1px solid {BORDER};
                            border-left:5px solid {al_color_hex};
                            border-radius:14px;padding:20px 24px;margin:12px 0;">
                    <div style="display:flex;justify-content:space-between;
                                align-items:center;flex-wrap:wrap;gap:12px;">
                        <div>
                            <div style="font-size:18px;font-weight:800;
                                        color:{T_DARK};">
                                ETU-{profil['student_id']:04d}
                            </div>
                            <div style="font-size:12px;color:{T_MID};margin-top:4px;">
                                Prédiction : <b>{profil['pred_label']}</b>  ·
                                Réalité : <b>{profil['true_label'] or '—'}</b>  ·
                                Admission : <b>{profil['admission_grade']:.1f}/200</b>
                            </div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:32px;font-weight:900;
                                        color:{al_color_hex};letter-spacing:-1px;">
                                {score_pct}%
                            </div>
                            <div style="font-size:10px;color:{T_LIGHT};
                                        font-weight:700;text-transform:uppercase;
                                        letter-spacing:1px;">
                                Score de risque
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                with st.spinner("Génération du PDF en cours…"):
                    try:
                        pdf_bytes = generer_pdf_individuel(profil, include_graphs)
                        filename  = (
                            f"fiche_ETU-{profil['student_id']:04d}_"
                            f"{niveau}_{datetime.now().strftime('%Y%m%d')}.pdf"
                        )
                        st.success("✅ Rapport généré avec succès !")
                        st.download_button(
                            label=f"📥 Télécharger — {filename}",
                            data=pdf_bytes,
                            file_name=filename,
                            mime="application/pdf",
                            use_container_width=True,
                            type="primary",
                        )

                        recs = generer_recommandations(profil)
                        st.markdown(f"""
                        <div style="background:{BG_CARD};border:1px solid {BORDER};
                                    border-radius:12px;padding:16px 20px;margin-top:12px;">
                            <div style="font-size:10px;font-weight:800;letter-spacing:2px;
                                        text-transform:uppercase;color:{T_LIGHT};
                                        margin-bottom:12px;">
                                💡 Aperçu des recommandations incluses
                            </div>
                        """, unsafe_allow_html=True)
                        for i, (titre, desc) in enumerate(recs, 1):
                            st.markdown(f"""
                            <div style="padding:10px 0;border-bottom:1px solid {BORDER};">
                                <div style="font-size:12px;font-weight:700;
                                            color:{al_color_hex};">
                                    {i}. {titre}
                                </div>
                                <div style="font-size:11px;color:{T_MID};
                                            margin-top:3px;line-height:1.6;">
                                    {desc}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                        if "pdf_sid" in st.session_state:
                            del st.session_state["pdf_sid"]

                    except Exception as e:
                        st.error(f"❌ Erreur lors de la génération : {e}")

    # ════════════════════════════════════════════════════════════
    # TAB 2 — LOT
    # ════════════════════════════════════════════════════════════
    with tab_lot:
        section_header(
            "📦", "Génération en Lot",
            guide_title="Génération groupée",
            guide_text="Générez les fiches PDF de tous les étudiants d'une zone d'alerte "
                       "en une seule opération. Le résultat est un fichier ZIP téléchargeable.",
        )

        col_z1, col_z2, col_z3 = st.columns([1.5, 1, 1], gap="medium")

        with col_z1:
            zone_sel = st.selectbox(
                "Zone d'alerte cible",
                options=["rouge", "orange", "vert"],
                format_func=lambda x: {
                    "rouge":  "🔴 Zone Rouge (intervention urgente)",
                    "orange": "🟠 Zone Orange (surveillance)",
                    "vert":   "🟢 Zone Verte (stable)",
                }[x],
                index=0,
            )

        etudiants_zone = charger_etudiants_zone(zone_sel)
        nb_zone        = len(etudiants_zone)
        al_color_hex   = {"rouge": C_CORAL, "orange": C_AMBER,
                          "vert": C_EMERALD}.get(zone_sel, C_COBALT)

        with col_z2:
            max_lot = st.number_input(
                "Limite (0 = tous)",
                min_value=0, max_value=nb_zone,
                value=min(nb_zone, 20),
                step=5,
            )
        with col_z3:
            include_graphs_lot = st.toggle(
                "Inclure graphiques", value=False,
                help="Désactiver pour une génération plus rapide",
            )

        nb_effectif = nb_zone if max_lot == 0 else min(max_lot, nb_zone)
        st.markdown(f"""
        <div style="background:{BG_CARD};border:1px solid {BORDER};
                    border-left:5px solid {al_color_hex};
                    border-radius:12px;padding:16px 20px;margin:12px 0;">
            <div style="font-size:14px;font-weight:700;color:{T_DARK};">
                <b style="color:{al_color_hex};">{nb_zone}</b> étudiants en zone
                {zone_sel.upper()} dans la base
            </div>
            <div style="font-size:12px;color:{T_MID};margin-top:6px;">
                Fiches à générer : <b>{nb_effectif}</b>  ·
                Taille estimée : ~{nb_effectif * (180 if include_graphs_lot else 60)} Ko
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander(f"👁️ Aperçu des {min(nb_effectif, 10)} premiers étudiants"):
            preview = etudiants_zone[:10]
            for sid, rscore, level in preview:
                sc = round(rscore * 100, 1)
                col_a, col_b, col_c = st.columns([1, 2, 1])
                col_a.markdown(f"**ETU-{sid:04d}**")
                col_b.progress(sc / 100, text=f"{sc}%")
                col_c.markdown(badge_alert(level), unsafe_allow_html=True)

        btn_lot = st.button(
            f"⚙️ Générer {nb_effectif} fiches PDF → ZIP",
            type="primary",
            use_container_width=True,
            disabled=(nb_zone == 0),
        )

        if btn_lot:
            etus = etudiants_zone[:nb_effectif] if max_lot > 0 else etudiants_zone
            pbar = st.progress(0, text="Initialisation…")
            st.info(f"Génération de {len(etus)} fiches PDF…")

            with st.spinner("Génération du lot en cours…"):
                try:
                    zip_bytes = generer_lot_zip(
                        etus,
                        include_graphs=include_graphs_lot,
                        progress_bar=pbar,
                    )
                    pbar.progress(1.0, text="✅ Terminé !")
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                    zip_name  = (
                        f"rapports_{zone_sel}_{nb_effectif}etudiants_{timestamp}.zip"
                    )

                    st.success(
                        f"✅ {nb_effectif} fiches générées — "
                        f"{round(len(zip_bytes) / 1024, 1)} Ko"
                    )
                    st.download_button(
                        label=f"📦 Télécharger l'archive — {zip_name}",
                        data=zip_bytes,
                        file_name=zip_name,
                        mime="application/zip",
                        use_container_width=True,
                        type="primary",
                    )
                except Exception as e:
                    st.error(f"❌ Erreur lors de la génération du lot : {e}")

    # ── Footer ────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='page-footer'>RAPPORTS PDF &nbsp;·&nbsp; "
        f"{kpis['total']:,} ÉTUDIANTS &nbsp;·&nbsp; "
        f"REPORTLAB &nbsp;·&nbsp; SHAP</div>",
        unsafe_allow_html=True,
    )


main()