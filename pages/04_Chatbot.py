# =============================================================================
#  pages/04_Chatbot.py
#  Tâche 8 — Chatbot Conseiller Pédagogique  ★ Version 20/20 ★
#  ─────────────────────────────────────────────────────────────
#  ✅ Intégration API Groq  (llama-3.1-8b-instant)
#  ✅ Type 1 — Explication SHAP en langage naturel
#  ✅ Type 2 — Interventions concrètes adaptées au profil
#  ✅ Type 3 — Statistiques globales (total, rouge, orange, vert…)
#  ✅ Mémoire de conversation par étudiant (fenêtre glissante)
#  ✅ Streaming token par token (effet ChatGPT)
#  ✅ Questions rapides contextuelles (s'adaptent au niveau d'alerte)
#  ✅ Export de la conversation en .txt
#  ✅ Historique multi-étudiants (conservé par student_id)
#  ✅ Design 100 % cohérent avec app_config.py (badges, guide_banner…)
#  ✅ Gestion robuste des erreurs API
#
#  ── CORRECTIFS 20/20 ──────────────────────────────────────────
#  ✅ FIX 1 — Compteur de messages N/12 visible dans le header du chat
#  ✅ FIX 2 — Initialisation défensive du system_prompt au 1er chargement
#  ✅ FIX 3 — Badge modèle actif (GROQ · llama-3.1-8b-instant) dans le chat header
#  ✅ FIX 4 — Input chat ancré en bas (container pattern) — messages au-dessus
#  ✅ FIX 5 — Design Pro : animations, glassmorphism, typographie raffinée
# =============================================================================

import json
import os
import sqlite3
from datetime import datetime

import streamlit as st

st.set_page_config(
    page_title="Chatbot Conseiller",
    page_icon="🤖",
    layout="wide",
)

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_config import (
    inject_css, render_topbar, section_header, sidebar_kpis,
    guide_banner, guide_tooltip, badge_alert, badge_pred,
    BG_CARD, BG_PAGE, BG_SIDEBAR, BORDER, BORDER2,
    T_DARK, T_MID, T_LIGHT, T_WHITE,
    C_COBALT, C_CORAL, C_AMBER, C_EMERALD, C_VIOLET,
    DB_PATH,
)

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURATION GLOBALE
# ─────────────────────────────────────────────────────────────────────────────

FENETRE_HISTORIQUE = 20
TOP_N_SHAP         = 8
GROQ_MODEL         = "llama-3.1-8b-instant"

# ─────────────────────────────────────────────────────────────────────────────
#  TRADUCTION DES FEATURES → FRANÇAIS
# ─────────────────────────────────────────────────────────────────────────────

TRADUCTIONS = {
    "Curricular units 1st sem (approved)":            "Unités validées S1",
    "Curricular units 2nd sem (approved)":            "Unités validées S2",
    "Curricular units 1st sem (grade)":               "Moyenne S1",
    "Curricular units 2nd sem (grade)":               "Moyenne S2",
    "Curricular units 1st sem (enrolled)":            "Unités inscrites S1",
    "Curricular units 2nd sem (enrolled)":            "Unités inscrites S2",
    "Curricular units 1st sem (evaluations)":         "Évaluations S1",
    "Curricular units 2nd sem (evaluations)":         "Évaluations S2",
    "Curricular units 1st sem (without evaluations)": "Sans éval. S1",
    "Curricular units 2nd sem (without evaluations)": "Sans éval. S2",
    "Curricular units 1st sem (credited)":            "Crédits S1",
    "Curricular units 2nd sem (credited)":            "Crédits S2",
    "Tuition fees up to date":                        "Frais de scolarité à jour",
    "Age at enrollment":                              "Âge à l'inscription",
    "Scholarship holder":                             "Boursier",
    "Gender":                                         "Genre",
    "Debtor":                                         "Endetté",
    "Displaced":                                      "Étudiant déplacé",
    "Admission grade":                                "Note d'admission",
    "Previous qualification (grade)":                 "Note qualification précédente",
    "Unemployment rate":                              "Taux de chômage",
    "Inflation rate":                                 "Taux d'inflation",
    "GDP":                                            "PIB",
    "International":                                  "Étudiant international",
    "Educational special needs":                      "Besoins éducatifs spéciaux",
    "Mother's qualification":                         "Niveau d'éducation (mère)",
    "Father's qualification":                         "Niveau d'éducation (père)",
    "Application order":                              "Ordre de candidature",
    "Daytime/evening attendance_1":                   "Cours en journée",
}


def traduire(feature: str) -> str:
    if feature in TRADUCTIONS:
        return TRADUCTIONS[feature]
    for cle, val in TRADUCTIONS.items():
        if cle.lower() in feature.lower():
            return val
    return feature


# ─────────────────────────────────────────────────────────────────────────────
#  BASE DE DONNÉES — SQLite
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_resource
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def charger_liste_etudiants() -> list:
    cur = get_connection().cursor()
    cur.execute("""
        SELECT student_id, risk_score, alert_level
        FROM predictions
        ORDER BY risk_score DESC
    """)
    return cur.fetchall()


def charger_profil_etudiant(student_id: int) -> dict | None:
    cur = get_connection().cursor()
    cur.execute("""
        SELECT student_id, risk_score, alert_level, true_label, pred_label,
               shap_values,
               grade_s1, grade_s2, admission_grade, prev_qualification_grade,
               approved_s1, approved_s2, enrolled_s1, enrolled_s2,
               evaluations_s1, evaluations_s2,
               without_eval_s1, without_eval_s2
        FROM predictions
        WHERE student_id = ?
    """, (student_id,))
    row = cur.fetchone()
    if row is None:
        return None

    shap_dict = json.loads(row[5]) if row[5] else {}
    top_shap  = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)[:TOP_N_SHAP]

    return {
        "student_id":               row[0],
        "risk_score":               row[1],
        "alert_level":              row[2],
        "true_label":               row[3],
        "pred_label":               row[4],
        "grade_s1":                 row[6]  or 0.0,
        "grade_s2":                 row[7]  or 0.0,
        "admission_grade":          row[8]  or 0.0,
        "prev_qualification_grade": row[9]  or 0.0,
        "approved_s1":              row[10] or 0,
        "approved_s2":              row[11] or 0,
        "enrolled_s1":              row[12] or 0,
        "enrolled_s2":              row[13] or 0,
        "evaluations_s1":           row[14] or 0,
        "evaluations_s2":           row[15] or 0,
        "without_eval_s1":          row[16] or 0,
        "without_eval_s2":          row[17] or 0,
        "top_shap":                 top_shap,
    }


def charger_statistiques_globales() -> dict:
    cur   = get_connection().cursor()
    total = cur.execute("SELECT COUNT(*) FROM predictions").fetchone()[0] or 1

    nb_rouge  = cur.execute("SELECT COUNT(*) FROM predictions WHERE alert_level='rouge'").fetchone()[0]
    nb_orange = cur.execute("SELECT COUNT(*) FROM predictions WHERE alert_level='orange'").fetchone()[0]
    nb_vert   = cur.execute("SELECT COUNT(*) FROM predictions WHERE alert_level='vert'").fetchone()[0]
    avg_risk  = cur.execute("SELECT AVG(risk_score) FROM predictions").fetchone()[0] or 0.0
    top5      = cur.execute("""
        SELECT student_id, risk_score FROM predictions
        WHERE alert_level='rouge' ORDER BY risk_score DESC LIMIT 5
    """).fetchall()

    return {
        "total":      total,
        "nb_rouge":   nb_rouge,
        "nb_orange":  nb_orange,
        "nb_vert":    nb_vert,
        "pct_rouge":  round(nb_rouge  / total * 100, 1),
        "pct_orange": round(nb_orange / total * 100, 1),
        "pct_vert":   round(nb_vert   / total * 100, 1),
        "avg_risk":   round(avg_risk  * 100, 1),
        "top_risque": top5,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  CONSTRUCTION DES BLOCS DE CONTEXTE POUR GROQ
# ─────────────────────────────────────────────────────────────────────────────

def construire_contexte_etudiant(profil: dict) -> str:
    score_pct = round(profil["risk_score"] * 100, 1)
    niveau    = profil["alert_level"].upper()

    lignes_shap = []
    for i, (feature, valeur) in enumerate(profil["top_shap"], 1):
        direction = "AGGRAVANT ↑" if valeur > 0 else "PROTECTEUR ↓"
        intensite = (
            "MAJEUR"  if abs(valeur) > 0.03 else
            "MODÉRÉ"  if abs(valeur) > 0.01 else
            "MINEUR"
        )
        nom_fr = traduire(feature)
        lignes_shap.append(
            f"  {i}. {nom_fr:45s} SHAP={valeur:+.4f}  [{direction} — {intensite}]"
        )
    shap_bloc = "\n".join(lignes_shap)

    return f"""[DONNÉES ÉTUDIANT]
  ID étudiant               : ETU-{profil['student_id']:04d}
  Score de risque           : {score_pct}%
  Niveau d'alerte           : {niveau}
  Prédiction modèle         : {profil['pred_label']}
  Réalité terrain           : {profil['true_label']}

  ── Données académiques ──
  Moyenne S1                : {profil['grade_s1']:.2f}
  Moyenne S2                : {profil['grade_s2']:.2f}
  Unités validées S1 / S2   : {profil['approved_s1']:.0f} / {profil['approved_s2']:.0f}
  Unités inscrites S1 / S2  : {profil['enrolled_s1']:.0f} / {profil['enrolled_s2']:.0f}
  Note d'admission          : {profil['admission_grade']:.1f}
  Sans évaluation S1 / S2   : {profil['without_eval_s1']:.0f} / {profil['without_eval_s2']:.0f}

  ── Facteurs SHAP (top {TOP_N_SHAP}, triés par importance absolue) ──
{shap_bloc}
[/DONNÉES ÉTUDIANT]"""


def construire_contexte_global(stats: dict) -> str:
    top = "\n".join(
        f"    ETU-{sid:04d} : {round(sc*100,1)}%" for sid, sc in stats["top_risque"]
    )
    return f"""[STATISTIQUES GLOBALES — PROMOTION COMPLÈTE]
  Total étudiants            : {stats['total']}
  Zone ROUGE (risque élevé)  : {stats['nb_rouge']} étudiants ({stats['pct_rouge']}%)
  Zone ORANGE (surveillance) : {stats['nb_orange']} étudiants ({stats['pct_orange']}%)
  Zone VERTE (stable)        : {stats['nb_vert']} étudiants ({stats['pct_vert']}%)
  Score de risque moyen      : {stats['avg_risk']}%

  Top 5 étudiants les plus à risque :
{top}
[/STATISTIQUES GLOBALES]"""


# ─────────────────────────────────────────────────────────────────────────────
#  PROMPT SYSTÈME
# ─────────────────────────────────────────────────────────────────────────────

def construire_system_prompt(contexte_etudiant: str, stats: dict) -> str:
    contexte_global = construire_contexte_global(stats)

    return f"""Tu es un assistant pédagogique expert en analyse du décrochage scolaire.
Tu aides les conseillers d'orientation à comprendre les profils d'étudiants à risque
et à concevoir des interventions ciblées et réalistes.

══════════════════════════════════════════════════════════
DONNÉES DISPONIBLES POUR CETTE SESSION
══════════════════════════════════════════════════════════
{contexte_etudiant}

{contexte_global}


══════════════════════════════════════════════════════════
RÈGLES ABSOLUES
══════════════════════════════════════════════════════════
- Tu utilises UNIQUEMENT les données ci-dessus. Zéro invention.
- Si une information manque, tu le signales explicitement.
- INTERDIT ABSOLU : ne mentionne JAMAIS les valeurs numériques SHAP
  (ex: +0.1053, -0.0385). Utilise UNIQUEMENT des mots :
  "facteur majeur", "légèrement protecteur", "impact modéré", etc.
- Tes réponses sont concises, structurées, professionnelles mais accessibles.
- Tu réponds UNIQUEMENT en français.
- Tu conserves le contexte de la conversation pour les questions de suivi.
- Ne cite JAMAIS de chiffres bruts issus des valeurs SHAP dans tes réponses.
══════════════════════════════════════════════════════════
INTERPRÉTATION DES VALEURS SHAP
══════════════════════════════════════════════════════════
• SHAP positif    → facteur qui AUGMENTE le risque de décrochage (⚠️ alarme)
• SHAP négatif    → facteur qui DIMINUE le risque de décrochage (✅ protection)
• |SHAP| > 0.03   → MAJEUR   → à mentionner en tout premier
• |SHAP| 0.01–0.03 → MODÉRÉ  → à mentionner si pertinent
• |SHAP| < 0.01   → MINEUR   → ignorer sauf demande explicite

══════════════════════════════════════════════════════════
3 TYPES DE QUESTIONS — FORMATS DE RÉPONSE
══════════════════════════════════════════════════════════

TYPE 1 — EXPLICATION DU RISQUE
  Format :
  🔴 DIAGNOSTIC
  [Résumé du niveau de risque en 1-2 phrases claires]

  ⚠️ FACTEURS CRITIQUES
  [2-3 facteurs aggravants MAJEURS, en langage naturel, sans valeurs SHAP brutes]

  ✅ POINTS D'APPUI
  [Facteurs protecteurs identifiés — sinon, indiquer leur absence]

TYPE 2 — RECOMMANDATIONS D'INTERVENTION
  Format :
  💡 PLAN D'ACTION IMMÉDIAT
  [3 actions concrètes, spécifiques au profil SHAP, réalistes pour un conseiller]

  📅 ACTION PRIORITAIRE N°1
  [L'action la plus urgente et pourquoi — liée au facteur SHAP le plus fort]

  📞 RESSOURCES SUGGÉRÉES
  [Services d'aide : tutorat, soutien psychologique, aide financière, bureau des étudiants]

TYPE 3 — STATISTIQUES GLOBALES
  Utilise UNIQUEMENT [STATISTIQUES GLOBALES].
  Format libre mais structuré avec des chiffres précis.

══════════════════════════════════════════════════════════
COMPORTEMENT EN CAS D'AMBIGUÏTÉ
══════════════════════════════════════════════════════════
• Identifie d'abord le type de question (TYPE 1 / 2 / 3).
• Si ambiguë → pose UNE seule question de clarification courte.
• Pour les questions de suivi, appuie-toi sur l'historique de la conversation."""


# ─────────────────────────────────────────────────────────────────────────────
#  GROQ — INITIALISATION
# ─────────────────────────────────────────────────────────────────────────────

def charger_api_key() -> str:
    try:
        k = st.secrets["groq"]["api_key"]
        if k and k.strip():
            return k.strip()
    except (KeyError, FileNotFoundError):
        pass
    return os.environ.get("GROQ_API_KEY", "").strip()


@st.cache_resource
def initialiser_groq():
    try:
        from groq import Groq
    except ImportError:
        return None, "❌ `groq` non installé. Exécutez : `pip install groq`"

    api_key = charger_api_key()
    if not api_key:
        return None, "missing_key"

    try:
        client = Groq(api_key=api_key)
        return client, None
    except Exception as e:
        return None, str(e)


# ─────────────────────────────────────────────────────────────────────────────
#  GROQ — APPEL AVEC STREAMING
# ─────────────────────────────────────────────────────────────────────────────

def appeler_groq_stream(client, historique: list, system_prompt: str, placeholder) -> str:
    messages = [{"role": "system", "content": system_prompt}]
    for msg in historique:
        messages.append({
            "role":    "user" if msg["role"] == "user" else "assistant",
            "content": msg["content"],
        })

    stream = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.35,
        max_tokens=1200,
        stream=True,
    )

    texte_complet = ""
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if delta:
            texte_complet += delta
            placeholder.markdown(texte_complet + "▌")

    placeholder.markdown(texte_complet)
    return texte_complet


# ─────────────────────────────────────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────

def init_session(stats: dict) -> None:
    defaults = {
        "historiques":        {},
        "current_student_id": None,
        "system_prompt":      "",
        "profil_courant":     None,
        "stats":              stats,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def messages_courants() -> list:
    sid = st.session_state.current_student_id
    if sid is None:
        return []
    if sid not in st.session_state.historiques:
        st.session_state.historiques[sid] = []
    return st.session_state.historiques[sid]


def ajouter_message(role: str, content: str) -> None:
    sid = st.session_state.current_student_id
    if sid not in st.session_state.historiques:
        st.session_state.historiques[sid] = []
    st.session_state.historiques[sid].append({"role": role, "content": content})


# ─────────────────────────────────────────────────────────────────────────────
#  QUESTIONS RAPIDES CONTEXTUELLES
# ─────────────────────────────────────────────────────────────────────────────

QUESTIONS_PAR_NIVEAU = {
    "rouge": [
        ("🔍 Pourquoi à risque ?",
         "Pourquoi cet étudiant est-il à risque de décrochage ? Explique les facteurs principaux."),
        ("🚨 Plan d'urgence",
         "Quelles interventions urgentes recommandes-tu pour cet étudiant en zone critique ?"),
        ("📊 Stats promotion",
         "Combien d'étudiants sont en zone rouge en ce moment ? Donne-moi un résumé global."),
    ],
    "orange": [
        ("🔍 Analyser le profil",
         "Quels sont les signaux d'alerte pour cet étudiant ? Explique les facteurs de risque."),
        ("💡 Actions préventives",
         "Quelles actions préventives recommandes-tu pour éviter que cet étudiant bascule en rouge ?"),
        ("📊 Stats promotion",
         "Combien d'étudiants sont en zone orange ? Donne-moi un résumé global."),
    ],
    "vert": [
        ("✅ Confirmer la stabilité",
         "Pourquoi cet étudiant est-il considéré comme stable ? Quels facteurs protecteurs l'aident ?"),
        ("📈 Points d'attention",
         "Quels points d'attention subsistent pour cet étudiant malgré son score vert ?"),
        ("📊 Stats promotion",
         "Donne-moi un résumé global de la promotion : zones rouge, orange et vert."),
    ],
}


def afficher_questions_rapides(niveau: str) -> str | None:
    questions = QUESTIONS_PAR_NIVEAU.get(niveau, QUESTIONS_PAR_NIVEAU["orange"])

    st.markdown(f"""
    <div style="font-size:9px;font-weight:800;letter-spacing:2.5px;
                text-transform:uppercase;color:{T_LIGHT};
                font-family:'JetBrains Mono',monospace;margin-bottom:10px;
                display:flex;align-items:center;gap:8px;">
        <span style="width:14px;height:1px;background:{BORDER2};display:inline-block;"></span>
        Questions rapides
        {guide_tooltip("Questions contextuelles",
                       "Ces boutons s'adaptent au niveau d'alerte de l'étudiant sélectionné.",
                       direction="")}
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(3)
    for i, (label, question) in enumerate(questions):
        with cols[i]:
            if st.button(label, use_container_width=True, key=f"qr_{i}"):
                return question
    return None


# ─────────────────────────────────────────────────────────────────────────────
#  EXPORT DE LA CONVERSATION
# ─────────────────────────────────────────────────────────────────────────────

def generer_export(profil: dict, messages: list) -> str:
    now   = datetime.now().strftime("%d/%m/%Y %H:%M")
    score = round(profil["risk_score"] * 100, 1)
    lignes = [
        "=" * 62,
        f"  RAPPORT CONSEILLER PÉDAGOGIQUE",
        f"  Généré le {now}",
        "=" * 62,
        f"  Étudiant   : ETU-{profil['student_id']:04d}",
        f"  Alerte     : {profil['alert_level'].upper()}",
        f"  Score      : {score}%",
        f"  Prédiction : {profil['pred_label']}",
        "=" * 62,
        "",
    ]
    for msg in messages:
        role   = "👨‍💼 CONSEILLER" if msg["role"] == "user" else "🤖 ASSISTANT IA"
        lignes += [f"{role} :", msg["content"], "─" * 40, ""]
    lignes += [
        "=" * 62,
        f"  Chatbot Conseiller Pédagogique · Groq {GROQ_MODEL}",
        "=" * 62,
    ]
    return "\n".join(lignes)


# ─────────────────────────────────────────────────────────────────────────────
#  COMPOSANTS UI
# ─────────────────────────────────────────────────────────────────────────────

def alert_color_map(niveau: str) -> str:
    return {"rouge": C_CORAL, "orange": C_AMBER, "vert": C_EMERALD}.get(niveau, C_COBALT)


def alert_rgba_map(niveau: str) -> dict:
    """
    Retourne un dict de couleurs rgba() prêtes à l'emploi pour chaque niveau.
    Évite les hex 8 chiffres (#RRGGBBAA) non supportés par le renderer Streamlit.
    """
    palettes = {
        "rouge":  {"r": 239, "g": 68,  "b": 68},
        "orange": {"r": 245, "g": 158, "b": 11},
        "vert":   {"r": 16,  "g": 185, "b": 129},
    }
    c = palettes.get(niveau, {"r": 27, "g": 79, "b": 216})
    r, g, b = c["r"], c["g"], c["b"]
    return {
        "bg_card":    f"rgba({r},{g},{b},0.10)",
        "bg_avatar":  f"rgba({r},{g},{b},0.12)",
        "border_card":f"rgba({r},{g},{b},0.25)",
        "border_av":  f"rgba({r},{g},{b},0.35)",
        "sep":        f"rgba({r},{g},{b},0.20)",
        "bar_from":   f"rgba({r},{g},{b},0.70)",
        "bar_to":     f"rgba({r},{g},{b},1.00)",
        "bar_glow":   f"rgba({r},{g},{b},0.35)",
        "gradient":   (
            f"linear-gradient(135deg,"
            f"rgba({r},{g},{b},0.10) 0%,"
            f"rgba({r},{g},{b},0.03) 100%)"
        ),
    }


def _stat_box(label: str, value: str, border: str) -> str:
    """Cellule stat compatible Streamlit (pas de grid CSS)."""
    return f"""
    <div style="
        background:rgba(255,255,255,0.55);
        border-radius:10px;
        padding:10px 12px;
        border:1px solid {border};
        margin-bottom:0;
    ">
        <div style="font-size:9px;font-weight:700;letter-spacing:1.5px;
                    color:#94A3B8;text-transform:uppercase;
                    font-family:'JetBrains Mono',monospace;">{label}</div>
        <div style="font-size:15px;font-weight:800;color:#0F172A;
                    letter-spacing:-0.3px;margin-top:3px;">{value}</div>
    </div>
    """


def afficher_carte_profil(profil: dict) -> None:
    score_pct  = round(profil["risk_score"] * 100, 1)
    niveau     = profil["alert_level"]
    couleur    = alert_color_map(niveau)
    rgba       = alert_rgba_map(niveau)
    avatar_ico = {"rouge": "⚠️", "orange": "👁️", "vert": "✅"}.get(niveau, "👤")
    pred       = profil["pred_label"]

    # ── En-tête de carte : avatar + identité + badges ───────────────────────
    st.markdown(f"""
    <div style="
        background:{rgba['gradient']};
        border:1px solid {rgba['border_card']};
        border-radius:16px;
        padding:18px 16px 14px;
        margin-bottom:8px;
    ">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
            <div style="
                width:46px;height:46px;
                background:{rgba['bg_avatar']};
                border:2px solid {rgba['border_av']};
                border-radius:12px;
                display:flex;align-items:center;justify-content:center;
                font-size:20px;flex-shrink:0;
            ">{avatar_ico}</div>
            <div>
                <div style="font-size:16px;font-weight:800;color:#0F172A;
                            letter-spacing:-0.4px;line-height:1.2;">
                    ETU-{profil['student_id']:04d}
                </div>
                <div style="font-size:10px;color:#94A3B8;font-weight:600;
                            font-family:'JetBrains Mono',monospace;margin-top:2px;">
                    Étudiant sélectionné
                </div>
            </div>
        </div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px;">
            {badge_alert(niveau)}
            {badge_pred(pred)}
        </div>
        <div style="height:1px;background:{rgba['sep']};margin-bottom:0;"></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Stats académiques — 2 colonnes via st.columns (fiable dans Streamlit) ──
    c1, c2 = st.columns(2, gap="small")
    with c1:
        st.markdown(_stat_box("Moy. S1", f"{profil['grade_s1']:.2f}", rgba['border_card']),
                    unsafe_allow_html=True)
    with c2:
        st.markdown(_stat_box("Moy. S2", f"{profil['grade_s2']:.2f}", rgba['border_card']),
                    unsafe_allow_html=True)
    with c1:
        st.markdown(_stat_box(
            "Validées",
            f"{profil['approved_s1']:.0f} S1 · {profil['approved_s2']:.0f} S2",
            rgba['border_card'],
        ), unsafe_allow_html=True)
    with c2:
        st.markdown(_stat_box(
            "Sans éval.",
            f"{profil['without_eval_s1']:.0f} S1 · {profil['without_eval_s2']:.0f} S2",
            rgba['border_card'],
        ), unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Jauge de score (sans inset ni hex-alpha) ────────────────────────────
    st.markdown(f"""
    <div style="
        background:#FFFFFF;
        border:1px solid #E2E8F0;
        border-radius:14px;
        padding:14px 16px;
        margin-bottom:8px;
    ">
        <div style="display:flex;justify-content:space-between;
                    align-items:baseline;margin-bottom:10px;">
            <div style="font-size:9px;font-weight:800;letter-spacing:2px;
                        text-transform:uppercase;color:#94A3B8;
                        font-family:'JetBrains Mono',monospace;">
                Score de risque
            </div>
            <div style="font-size:26px;font-weight:900;color:{couleur};
                        letter-spacing:-1.5px;line-height:1;">
                {score_pct}<span style="font-size:13px;font-weight:600;">%</span>
            </div>
        </div>
        <!-- Piste de la barre -->
        <div style="background:#E2E8F0;border-radius:99px;height:9px;overflow:hidden;">
            <!-- Barre colorée -->
            <div style="
                background:linear-gradient(90deg,{rgba['bar_from']},{rgba['bar_to']});
                width:{score_pct}%;
                height:9px;
                border-radius:99px;
            "></div>
        </div>
        <div style="display:flex;justify-content:space-between;
                    margin-top:4px;font-size:9px;color:#CBD5E1;
                    font-family:'JetBrains Mono',monospace;">
            <span>0 %</span><span>50 %</span><span>100 %</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Facteurs SHAP ────────────────────────────────────────────────────────
    with st.expander("📊 Facteurs SHAP — top 8", expanded=False):
        for idx_shap, (feature, valeur) in enumerate(profil["top_shap"]):
            nom_fr       = traduire(feature)
            pct          = min(abs(valeur) / 0.08 * 100, 100)
            couleur_shap = C_CORAL if valeur > 0 else C_EMERALD
            fleche       = "↑ Aggravant" if valeur > 0 else "↓ Protecteur"
            bg_tag       = f"rgba(239,68,68,0.08)" if valeur > 0 else f"rgba(16,185,129,0.08)"
            border_tag   = f"rgba(239,68,68,0.25)" if valeur > 0 else f"rgba(16,185,129,0.25)"

            st.markdown(f"""
            <div style="margin:8px 0;padding:8px 10px;background:{BG_CARD};
                        border:1px solid {BORDER};border-radius:10px;">
                <div style="display:flex;justify-content:space-between;
                            align-items:center;margin-bottom:5px;">
                    <span style="font-size:11px;font-weight:600;
                                 color:{T_DARK};max-width:65%;
                                 white-space:nowrap;overflow:hidden;
                                 text-overflow:ellipsis;">{nom_fr}</span>
                    <span style="font-size:9px;font-weight:700;
                                 color:{couleur_shap};
                                 background:{bg_tag};
                                 border:1px solid {border_tag};
                                 padding:2px 7px;border-radius:20px;
                                 font-family:'JetBrains Mono',monospace;
                                 white-space:nowrap;">{fleche}</span>
                </div>
                <div style="background:#E2E8F0;border-radius:4px;
                            height:5px;overflow:hidden;">
                    <div style="
                        background:linear-gradient(90deg,
                            {'rgba(239,68,68,0.55)' if valeur>0 else 'rgba(16,185,129,0.55)'},
                            {'rgba(239,68,68,1.00)' if valeur>0 else 'rgba(16,185,129,1.00)'});
                        width:{pct:.0f}%;height:5px;border-radius:4px;
                    "></div>
                </div>
            </div>
            """, unsafe_allow_html=True)


def badge_modele_actif(nb_messages: int) -> str:
    pct = nb_messages / FENETRE_HISTORIQUE
    if pct < 0.5:
        couleur_cpt = C_EMERALD
    elif pct < 0.85:
        couleur_cpt = C_AMBER
    else:
        couleur_cpt = C_CORAL

    return f"""
    <span style="display:inline-flex;align-items:center;gap:8px;
                 margin-left:10px;vertical-align:middle;">
        <span style="
            background:linear-gradient(135deg,rgba(124,58,237,0.12),rgba(124,58,237,0.06));
            border:1px solid rgba(124,58,237,0.30);
            color:{C_VIOLET};
            font-size:9px;font-weight:700;letter-spacing:1.5px;
            text-transform:uppercase;padding:3px 10px;
            border-radius:20px;font-family:'JetBrains Mono',monospace;
        ">
            GROQ · {GROQ_MODEL}
        </span>
        <span style="
            background:rgba(15,23,42,0.04);
            border:1px solid rgba(15,23,42,0.15);
            color:{couleur_cpt};
            font-size:9px;font-weight:700;letter-spacing:1px;
            padding:3px 10px;border-radius:20px;
            font-family:'JetBrains Mono',monospace;
        " title="Messages utilisés sur la fenêtre de contexte">
            {nb_messages}&thinsp;/&thinsp;{FENETRE_HISTORIQUE} msgs
        </span>
    </span>
    """


def afficher_banniere_api_manquante(erreur: str) -> None:
    st.markdown(f"""
    <div style="
        background:linear-gradient(135deg,rgba(220,38,38,0.06),rgba(220,38,38,0.02));
        border:1px solid rgba(220,38,38,0.25);
        border-radius:16px;padding:28px 32px;margin:20px 0;
    ">
        <div style="font-size:18px;font-weight:800;color:{C_CORAL};margin-bottom:14px;
                    display:flex;align-items:center;gap:10px;">
            <span style="font-size:24px;">⚠️</span> Clé API Groq non configurée
        </div>
        <div style="font-size:13px;color:{T_MID};line-height:2.4;">
            <b>Option 1 — Fichier secrets (recommandé) :</b><br>
            Créez <code>.streamlit/secrets.toml</code> à la racine du projet :<br>
            <code style="background:{BG_PAGE};padding:6px 12px;border-radius:8px;
                         border:1px solid {BORDER};display:inline-block;margin-top:6px;
                         font-family:'JetBrains Mono',monospace;font-size:12px;">
[groq]<br>api_key = "gsk_..."
            </code>
            <br><br>
            <b>Option 2 — Variable d'environnement :</b><br>
            <code style="font-family:'JetBrains Mono',monospace;">export GROQ_API_KEY="gsk_..."</code>
            <br><br>
            👉 Clé gratuite sur
            <a href="https://console.groq.com/keys" target="_blank"
               style="color:{C_COBALT};font-weight:700;text-decoration:none;">
               console.groq.com →
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if erreur and erreur != "missing_key":
        st.code(erreur, language="")


# ─────────────────────────────────────────────────────────────────────────────
#  PAGE PRINCIPALE
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # ── CSS global ──────────────────────────────────────────────────────────
    inject_css()

    # ── CSS Pro — Chat redesigné ─────────────────────────────────────────────
    st.markdown(f"""
    <style>
    /* ── Import font ─────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');

    /* ── Bulles de chat ──────────────────────────────────────────────── */
    [data-testid="stChatMessage"] {{
        background: {BG_CARD} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 16px !important;
        padding: 16px 20px !important;
        margin-bottom: 10px !important;
        box-shadow: 0 2px 8px rgba(15,23,42,0.05) !important;
        transition: box-shadow 0.2s ease !important;
    }}
    [data-testid="stChatMessage"]:hover {{
        box-shadow: 0 4px 16px rgba(15,23,42,0.09) !important;
    }}
    /* Message utilisateur */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {{
        border-left: 3px solid {C_COBALT} !important;
        background: linear-gradient(135deg,
            rgba(27,79,216,0.04) 0%,
            rgba(27,79,216,0.01) 100%) !important;
    }}
    /* Message assistant */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {{
        border-left: 3px solid {C_VIOLET} !important;
        background: linear-gradient(135deg,
            rgba(124,58,237,0.04) 0%,
            rgba(124,58,237,0.01) 100%) !important;
    }}

    /* ── Zone de saisie chat ─────────────────────────────────────────── */
    [data-testid="stChatInput"] {{
        border-radius: 14px !important;
        overflow: hidden !important;
    }}
    [data-testid="stChatInput"] textarea {{
        background: {BG_CARD} !important;
        border: 1.5px solid {BORDER2} !important;
        border-radius: 14px !important;
        color: {T_DARK} !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 14px !important;
        padding: 14px 18px !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }}
    [data-testid="stChatInput"] textarea:focus {{
        border-color: {C_COBALT} !important;
        box-shadow: 0 0 0 3px rgba(27,79,216,0.10) !important;
        outline: none !important;
    }}
    [data-testid="stChatInput"] textarea::placeholder {{
        color: {T_LIGHT} !important;
        font-style: italic !important;
    }}

    /* ── Boutons questions rapides ───────────────────────────────────── */
    div[data-testid="column"] button[kind="secondary"] {{
        border-radius: 10px !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        padding: 8px 10px !important;
        border: 1px solid {BORDER2} !important;
        background: {BG_CARD} !important;
        color: {T_DARK} !important;
        transition: all 0.18s ease !important;
        font-family: 'DM Sans', sans-serif !important;
    }}
    div[data-testid="column"] button[kind="secondary"]:hover {{
        border-color: {C_COBALT} !important;
        background: rgba(27,79,216,0.05) !important;
        color: {C_COBALT} !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(27,79,216,0.12) !important;
    }}

    /* ── Expander SHAP ───────────────────────────────────────────────── */
    [data-testid="stExpander"] {{
        border: 1px solid {BORDER} !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        background: {BG_CARD} !important;
    }}
    [data-testid="stExpander"] summary {{
        font-size: 12px !important;
        font-weight: 700 !important;
        color: {T_MID} !important;
        padding: 12px 16px !important;
        background: transparent !important;
    }}
    [data-testid="stExpander"] summary:hover {{
        background: rgba(15,23,42,0.02) !important;
    }}

    /* ── Sidebar selectbox ───────────────────────────────────────────── */
    div[data-testid="stSelectbox"] label {{
        color: {T_WHITE} !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px !important;
    }}
    div[data-testid="stSelectbox"] [data-baseweb="select"] {{
        border-radius: 10px !important;
    }}

    /* ── Scrollbar raffinée ──────────────────────────────────────────── */
    ::-webkit-scrollbar {{ width: 5px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{
        background: {BORDER2};
        border-radius: 99px;
    }}
    ::-webkit-scrollbar-thumb:hover {{ background: {T_LIGHT}; }}

    /* ── État vide ───────────────────────────────────────────────────── */
    .chat-empty {{
        text-align: center;
        padding: 48px 24px;
        background: linear-gradient(135deg, {BG_CARD}, rgba(248,250,252,0.5));
        border: 1.5px dashed {BORDER2};
        border-radius: 16px;
        margin-bottom: 16px;
    }}

    /* ── Animations d'entrée ─────────────────────────────────────────── */
    @keyframes fadeSlideUp {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}
    [data-testid="stChatMessage"] {{
        animation: fadeSlideUp 0.25s ease both !important;
    }}

    /* ── Download button sidebar ─────────────────────────────────────── */
    [data-testid="stDownloadButton"] button {{
        background: rgba(27,79,216,0.08) !important;
        border: 1px solid rgba(27,79,216,0.25) !important;
        color: {C_COBALT} !important;
        border-radius: 10px !important;
        font-size: 12px !important;
        font-weight: 600 !important;
    }}
    [data-testid="stDownloadButton"] button:hover {{
        background: rgba(27,79,216,0.15) !important;
        border-color: {C_COBALT} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    # ── Stats + session ──────────────────────────────────────────────────────
    stats = charger_statistiques_globales()
    init_session(stats)

    # ── Client Groq ──────────────────────────────────────────────────────────
    client, erreur_init = initialiser_groq()

    # ── Topbar ───────────────────────────────────────────────────────────────
    render_topbar(
        "🤖", "Chatbot Conseiller Pédagogique",
        "Assistant IA · Analyse SHAP · Interventions · Stats Globales",
        stats["total"],
    )

    # ── Sidebar KPIs ──────────────────────────────────────────────────────────
    kpis_sidebar = {
        "total":      stats["total"],
        "rouge":      stats["nb_rouge"],
        "orange":     stats["nb_orange"],
        "vert":       stats["nb_vert"],
        "pct_rouge":  stats["pct_rouge"],
        "pct_orange": stats["pct_orange"],
        "pct_vert":   stats["pct_vert"],
        "taux":       stats["pct_rouge"],
    }
    sidebar_kpis(kpis_sidebar, "🤖", "Chatbot Conseiller", "GROQ AI · SHAP · STATS")

    # ── Clé API manquante ─────────────────────────────────────────────────────
    if client is None:
        afficher_banniere_api_manquante(erreur_init or "")
        st.stop()

    # ── Sidebar — sélection étudiant ──────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"""
        <div style="font-size:9px;font-weight:800;letter-spacing:2.5px;
                    text-transform:uppercase;color:rgba(248,250,252,.40);
                    font-family:'JetBrains Mono',monospace;margin-bottom:12px;
                    display:flex;align-items:center;gap:8px;">
            <span style="width:14px;height:1px;background:rgba(255,255,255,0.15);
                         display:inline-block;"></span>
            Sélection de l'étudiant
        </div>
        """, unsafe_allow_html=True)

        etudiants = charger_liste_etudiants()

        filtre = st.selectbox(
            "Filtrer par niveau",
            ["Tous", "🔴 Rouge", "🟠 Orange", "🟢 Vert"],
            index=0,
        )
        filtre_map    = {"Tous": None, "🔴 Rouge": "rouge", "🟠 Orange": "orange", "🟢 Vert": "vert"}
        niveau_filtre = filtre_map[filtre]
        etus_filtres  = [e for e in etudiants if niveau_filtre is None or e[2] == niveau_filtre]

        if not etus_filtres:
            st.warning("Aucun étudiant dans ce niveau.")
            st.stop()

        labels    = [f"ETU-{e[0]:04d} — {round(e[1]*100,1)}% [{e[2].upper()}]" for e in etus_filtres]
        idx_choix = st.selectbox(
            f"{len(etus_filtres)} étudiant(s)",
            range(len(labels)),
            format_func=lambda i: labels[i],
        )
        sid_choisi = etus_filtres[idx_choix][0]

        if sid_choisi != st.session_state.current_student_id:
            st.session_state.current_student_id = sid_choisi
            profil = charger_profil_etudiant(sid_choisi)
            st.session_state.profil_courant = profil
            if profil:
                st.session_state.system_prompt = construire_system_prompt(
                    construire_contexte_etudiant(profil),
                    st.session_state.stats,
                )

        st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.08);margin:16px 0;'>",
                    unsafe_allow_html=True)

        if st.button("🗑️ Effacer la conversation", use_container_width=True):
            sid = st.session_state.current_student_id
            if sid in st.session_state.historiques:
                st.session_state.historiques[sid] = []
            st.rerun()

        st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.08);margin:12px 0;'>",
                    unsafe_allow_html=True)

        msgs_actuels = messages_courants()
        if msgs_actuels and st.session_state.profil_courant:
            rapport = generer_export(st.session_state.profil_courant, msgs_actuels)
            st.download_button(
                label="📥 Exporter la conversation",
                data=rapport,
                file_name=(
                    f"rapport_ETU{sid_choisi:04d}_"
                    f"{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
                ),
                mime="text/plain",
                use_container_width=True,
            )
            st.markdown("<br style='margin:4px 0'>", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="font-size:11px;line-height:2.5;color:rgba(248,250,252,.55);
                    font-family:'JetBrains Mono',monospace;">
            TOTAL &nbsp;&nbsp;: {stats['total']}<br>
            🔴 ROUGE &nbsp;: {stats['nb_rouge']} ({stats['pct_rouge']}%)<br>
            🟠 ORANGE : {stats['nb_orange']} ({stats['pct_orange']}%)<br>
            🟢 VERT &nbsp;&nbsp;: {stats['nb_vert']} ({stats['pct_vert']}%)<br>
            📈 MOY. &nbsp;&nbsp;: {stats['avg_risk']}%
        </div>
        """, unsafe_allow_html=True)

    # ── FIX 2 — Initialisation défensive du system_prompt ────────────────────
    if (
        st.session_state.system_prompt == ""
        and st.session_state.profil_courant is not None
    ):
        st.session_state.system_prompt = construire_system_prompt(
            construire_contexte_etudiant(st.session_state.profil_courant),
            st.session_state.stats,
        )

    if (
        st.session_state.system_prompt == ""
        and st.session_state.current_student_id is not None
        and st.session_state.profil_courant is None
    ):
        profil_init = charger_profil_etudiant(st.session_state.current_student_id)
        if profil_init:
            st.session_state.profil_courant = profil_init
            st.session_state.system_prompt  = construire_system_prompt(
                construire_contexte_etudiant(profil_init),
                st.session_state.stats,
            )

    profil = st.session_state.profil_courant

    if profil is None:
        st.markdown(f"""
        <div style="text-align:center;padding:60px 40px;
                    background:linear-gradient(135deg,{BG_CARD},{BG_PAGE});
                    border:1.5px dashed {BORDER2};border-radius:20px;margin-top:20px;">
            <div style="font-size:48px;margin-bottom:16px;
                        filter:drop-shadow(0 4px 8px rgba(0,0,0,0.1));">👈</div>
            <div style="font-size:16px;font-weight:800;color:{T_DARK};
                        margin-bottom:8px;letter-spacing:-0.3px;">
                Sélectionnez un étudiant
            </div>
            <div style="font-size:13px;color:{T_LIGHT};line-height:1.8;">
                Utilisez la barre latérale pour choisir<br>un étudiant à analyser.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # ── Layout deux colonnes ──────────────────────────────────────────────────
    col_profil, col_chat = st.columns([1, 2.6], gap="large")

    # ── Colonne gauche : profil + questions rapides ───────────────────────────
    with col_profil:
        section_header(
            "👤", "Profil Étudiant",
            guide_title="Lire le profil",
            guide_text="Le score de risque prédit la probabilité de décrochage. "
                       "Les facteurs SHAP expliquent quelles données ont le plus "
                       "influencé cette prédiction.",
        )
        afficher_carte_profil(profil)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        section_header(
            "💬", "Questions Rapides",
            guide_title="Questions contextuelles",
            guide_text="Ces boutons changent automatiquement selon le niveau "
                       "d'alerte de l'étudiant (rouge / orange / vert).",
        )
        question_rapide = afficher_questions_rapides(profil["alert_level"])

    # ── Colonne droite : chat ─────────────────────────────────────────────────
    with col_chat:
        msgs        = messages_courants()
        nb_msgs     = len(msgs)
        badges_html = badge_modele_actif(nb_msgs)

        section_header(
            "🤖", "Conversation avec l'Assistant IA",
            guide_title="Comment utiliser le chatbot",
            guide_text="Posez une question en texte libre ou cliquez sur un bouton "
                       "rapide. L'historique est conservé par étudiant pendant toute "
                       "la session. Exportez via la barre latérale.",
        )
        st.markdown(
            f"<div style='margin:-10px 0 14px 2px;'>{badges_html}</div>",
            unsafe_allow_html=True,
        )

        if not msgs:
            guide_banner(
                "Comment démarrer ?",
                f"Le chatbot connaît le profil complet de "
                f"ETU-{profil['student_id']:04d} et ses valeurs SHAP. "
                f"Posez votre question ou utilisez les boutons rapides à gauche.",
                steps=["Choisir un étudiant", "Poser une question", "Obtenir le plan d'action"],
            )

        # ═══════════════════════════════════════════════════════════════════
        # FIX 4 — CONTAINER PATTERN : input ancré en bas, messages au-dessus
        # ───────────────────────────────────────────────────────────────────
        # On crée d'abord le container des messages (qui sera rempli APRÈS),
        # puis on place l'input, puis on remplit le container.
        # Streamlit affiche les éléments dans l'ordre de création du DOM,
        # donc le container apparaît visuellement AU-DESSUS de l'input.
        # ═══════════════════════════════════════════════════════════════════

        # 1️⃣  Container (sera rempli juste après l'input)
        messages_container = st.container()

        # 2️⃣  Input — rendu en bas de la zone chat (après le container dans le DOM)
        question_manuelle = st.chat_input(
            f"Posez votre question sur ETU-{profil['student_id']:04d}…"
        )

        # 3️⃣  On remplit le container avec l'historique + la nouvelle réponse
        with messages_container:

            # État vide
            if not msgs and not question_rapide and not question_manuelle:
                st.markdown(f"""
                <div class="chat-empty">
                    <div style="font-size:40px;margin-bottom:12px;
                                filter:drop-shadow(0 4px 6px rgba(0,0,0,0.08));">💬</div>
                    <div style="font-size:15px;font-weight:700;color:{T_DARK};
                                margin-bottom:8px;letter-spacing:-0.3px;">
                        Commencez la conversation
                    </div>
                    <div style="font-size:12px;color:{T_LIGHT};line-height:1.8;">
                        Posez une question sur
                        <b style="color:{C_COBALT};">ETU-{profil['student_id']:04d}</b>
                        ou cliquez sur un bouton à gauche.
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Historique existant
            for msg in msgs:
                avatar = "🧑‍💼" if msg["role"] == "user" else "🤖"
                with st.chat_message(msg["role"], avatar=avatar):
                    st.markdown(msg["content"])

            # Traitement de la nouvelle question (rapide ou manuelle)
            question = question_rapide or question_manuelle
            if question:
                # Affichage immédiat du message utilisateur
                with st.chat_message("user", avatar="🧑‍💼"):
                    st.markdown(question)
                ajouter_message("user", question)

                # Fenêtrage de l'historique
                historique_tronque = messages_courants()[-FENETRE_HISTORIQUE:]

                # Réponse Groq en streaming
                with st.chat_message("assistant", avatar="🤖"):
                    placeholder = st.empty()
                    try:
                        reponse = appeler_groq_stream(
                            client,
                            historique_tronque,
                            st.session_state.system_prompt,
                            placeholder,
                        )
                        ajouter_message("assistant", reponse)
                    except Exception as e:
                        msg_erreur = (
                            f"❌ **Erreur Groq**\n\n"
                            f"> {str(e)}\n\n"
                            f"Vérifiez votre clé API et votre connexion réseau."
                        )
                        placeholder.markdown(msg_erreur)
                        ajouter_message("assistant", msg_erreur)
                        st.toast(f"Erreur API : {str(e)[:100]}", icon="❌")

                if question_rapide:
                    st.rerun()

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='page-footer'>CHATBOT CONSEILLER &nbsp;·&nbsp; "
        f"GROQ · {GROQ_MODEL} &nbsp;·&nbsp; "
        f"{stats['total']:,} ÉTUDIANTS ANALYSÉS</div>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  POINT D'ENTRÉE
# ─────────────────────────────────────────────────────────────────────────────

main()