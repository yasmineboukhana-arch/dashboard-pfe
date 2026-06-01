"""
╔══════════════════════════════════════════════════════════════════╗
║  app_config.py  — Module partagé (palette, CSS, DB, helpers)    ║
║  Importé par main.py et toutes les pages.                       ║
╚══════════════════════════════════════════════════════════════════╝
"""
import json
import sqlite3

import pandas as pd
import streamlit as st

# ─────────────────────────────────────────────────────────────────
# CHEMIN BASE DE DONNÉES
# ─────────────────────────────────────────────────────────────────
DB_PATH = "students.db"

# ─────────────────────────────────────────────────────────────────
# PALETTE DE COULEURS — Design "Blanc & Cobalt" production
# ─────────────────────────────────────────────────────────────────
BG_PAGE    = "#F8FAFC"
BG_CARD    = "#FFFFFF"
BG_SIDEBAR = "#0F172A"
BG_SECTION = "#F1F5F9"
BG_TOPBAR  = "#0F172A"

C_COBALT   = "#1B4FD8"
C_NAVY     = "#0F172A"
C_EMERALD  = "#059669"
C_AMBER    = "#D97706"
C_CORAL    = "#DC2626"
C_VIOLET   = "#7C3AED"
C_CYAN     = "#0891B2"

T_DARK     = "#0F172A"
T_MID      = "#475569"
T_LIGHT    = "#94A3B8"
T_WHITE    = "#F8FAFC"

BORDER     = "#E2E8F0"
BORDER2    = "#CBD5E1"

C_COBALT_H  = "#1D4ED8"
C_EMERALD_H = "#047857"
C_AMBER_H   = "#B45309"
C_CORAL_H   = "#B91C1C"

# Plotly axis style — défini ici car utilisé par les pages
AXIS_STYLE = dict(
    gridcolor=BORDER,
    linecolor=BORDER,
    zerolinecolor=BORDER,
    tickfont=dict(color=T_LIGHT, size=11),
)


# ─────────────────────────────────────────────────────────────────
# CSS GLOBAL
# ─────────────────────────────────────────────────────────────────
def inject_css() -> None:
    """Injecte le CSS global dans l'application Streamlit."""
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {{
    font-family: 'Outfit', sans-serif !important;
}}
.stApp {{ background: {BG_PAGE} !important; }}
.block-container {{
    padding: 0 2rem 3rem !important;
    max-width: 100% !important;
}}
header[data-testid="stHeader"] {{ background: transparent !important; }}
footer {{ display: none !important; }}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
    background: {BG_SIDEBAR} !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}}
section[data-testid="stSidebar"] * {{ color: {T_WHITE} !important; }}
section[data-testid="stSidebar"] hr {{
    border-color: rgba(255,255,255,0.1) !important;
    margin: 10px 0 !important;
}}
[data-testid="stSidebarNav"] a {{
    border-radius: 10px !important;
    padding: 10px 14px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    letter-spacing: .2px !important;
    transition: all .2s ease !important;
    color: rgba(248,250,252,0.7) !important;
}}
[data-testid="stSidebarNav"] a:hover {{
    background: rgba(27,79,216,0.25) !important;
    color: {T_WHITE} !important;
}}
[data-testid="stSidebarNav"] a[aria-current="page"] {{
    background: rgba(27,79,216,0.35) !important;
    border-left: 3px solid {C_COBALT} !important;
    color: {T_WHITE} !important;
}}

/* ── Topbar ── */
.topbar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 18px 28px;
    background: {BG_SIDEBAR};
    margin: 0 -2rem 2rem -2rem;
    box-shadow: 0 4px 24px rgba(15,23,42,0.25);
    position: sticky;
    top: 0;
    z-index: 100;
}}
.topbar-left {{ display: flex; align-items: center; gap: 14px; }}
.topbar-icon {{ font-size: 30px; }}
.topbar-title {{
    font-size: 18px; font-weight: 800; color: {T_WHITE};
    margin: 0; letter-spacing: -.4px;
}}
.topbar-sub {{
    font-size: 11px; color: rgba(248,250,252,.42);
    margin: 2px 0 0; letter-spacing: .5px;
}}
.topbar-right {{ display: flex; align-items: center; gap: 10px; }}

/* ── Chips ── */
.chip {{
    padding: 5px 14px; border-radius: 20px;
    font-size: 10px; font-weight: 700; letter-spacing: 1.2px;
    text-transform: uppercase; font-family: 'JetBrains Mono', monospace;
    display: inline-flex; align-items: center; gap: 6px;
}}
.chip-live {{
    background: rgba(5,150,105,.18);
    border: 1px solid rgba(5,150,105,.4); color: #34D399;
}}
.chip-live::before {{
    content: ''; width: 6px; height: 6px; background: #34D399;
    border-radius: 50%; animation: blink 2s infinite;
}}
.chip-db {{
    background: rgba(248,250,252,.08);
    border: 1px solid rgba(248,250,252,.18); color: {T_WHITE};
}}
@keyframes blink {{ 0%,100%{{opacity:1}} 50%{{opacity:.15}} }}

/* ── Section header ── */
.sec-header {{
    display: flex; align-items: center; gap: 10px;
    margin: 28px 0 16px; padding-bottom: 12px;
    border-bottom: 2px solid {BORDER};
}}
.sec-icon {{ font-size: 18px; }}
.sec-title {{
    font-size: 11px; font-weight: 700; letter-spacing: 2.5px;
    text-transform: uppercase; color: {C_COBALT};
    font-family: 'JetBrains Mono', monospace;
}}

/* ── Glass Card ── */
.glass-card {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 22px;
    box-shadow: 0 1px 3px rgba(15,23,42,0.05);
}}

/* ── KPI Cards ── */
.kpi {{
    background: {BG_CARD}; border: 1px solid {BORDER};
    border-radius: 16px; padding: 22px 20px 18px;
    position: relative; overflow: hidden;
    box-shadow: 0 1px 3px rgba(15,23,42,0.05);
    transition: all .25s ease;
}}
.kpi:hover {{
    transform: translateY(-4px);
    box-shadow: 0 12px 32px rgba(15,23,42,0.10);
}}
.kpi::before {{
    content: ''; position: absolute; top: 0; left: 0; right: 0;
    height: 4px; border-radius: 16px 16px 0 0;
}}
.kpi.cobalt::before  {{ background: linear-gradient(90deg,{C_COBALT},{C_COBALT}88); }}
.kpi.coral::before   {{ background: linear-gradient(90deg,{C_CORAL},{C_CORAL}88); }}
.kpi.amber::before   {{ background: linear-gradient(90deg,{C_AMBER},{C_AMBER}88); }}
.kpi.emerald::before {{ background: linear-gradient(90deg,{C_EMERALD},{C_EMERALD}88); }}
.kpi.violet::before  {{ background: linear-gradient(90deg,{C_VIOLET},{C_VIOLET}88); }}
.kpi-bg-icon {{
    position: absolute; bottom: -6px; right: 10px;
    font-size: 56px; opacity: .05; pointer-events: none;
}}
.kpi-label {{
    font-size: 9px; font-weight: 700; letter-spacing: 2px;
    text-transform: uppercase; color: {T_LIGHT};
    font-family: 'JetBrains Mono', monospace; margin-bottom: 10px;
}}
.kpi-val {{
    font-size: 40px; font-weight: 800; line-height: 1;
    margin-bottom: 8px; letter-spacing: -2px;
}}
.kpi-val.cobalt  {{ color: {C_COBALT}; }}
.kpi-val.coral   {{ color: {C_CORAL}; }}
.kpi-val.amber   {{ color: {C_AMBER}; }}
.kpi-val.emerald {{ color: {C_EMERALD}; }}
.kpi-val.violet  {{ color: {C_VIOLET}; }}
.kpi-sub {{
    font-size: 11px; color: {T_MID}; font-weight: 500;
    display: inline-flex; align-items: center; gap: 5px;
    background: {BG_PAGE}; border: 1px solid {BORDER};
    border-radius: 8px; padding: 3px 9px;
}}
.kpi-bar-bg {{
    width: 100%; height: 4px; background: {BORDER};
    border-radius: 4px; margin-top: 14px; overflow: hidden;
}}
.kpi-bar {{ height: 100%; border-radius: 4px; }}
.kpi-bar.cobalt  {{ background: {C_COBALT}; }}
.kpi-bar.coral   {{ background: {C_CORAL}; }}
.kpi-bar.amber   {{ background: {C_AMBER}; }}
.kpi-bar.emerald {{ background: {C_EMERALD}; }}

/* ── Boutons ── */
.stButton > button {{
    border-radius: 10px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 10px 22px !important;
    transition: all .2s ease !important;
    border: none !important;
}}
.stButton > button[kind="primary"] {{
    background: {C_COBALT} !important;
    color: white !important;
    box-shadow: 0 2px 8px rgba(27,79,216,0.28) !important;
}}
.stButton > button[kind="primary"]:hover {{
    background: {C_COBALT_H} !important;
    box-shadow: 0 6px 20px rgba(27,79,216,0.40) !important;
    transform: translateY(-1px) !important;
}}
.stButton > button[kind="secondary"] {{
    background: {BG_CARD} !important;
    color: {T_DARK} !important;
    border: 1.5px solid {BORDER} !important;
}}
.stButton > button[kind="secondary"]:hover {{
    border-color: {C_COBALT} !important;
    color: {C_COBALT} !important;
}}

/* ── Inputs ── */
div[data-testid="stNumberInput"] input,
div[data-testid="stTextInput"] input {{
    background: {BG_CARD} !important;
    border: 1.5px solid {BORDER2} !important;
    border-radius: 10px !important;
    color: {T_DARK} !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 14px !important;
}}
div[data-testid="stNumberInput"] input:focus,
div[data-testid="stTextInput"] input:focus {{
    border-color: {C_COBALT} !important;
    box-shadow: 0 0 0 3px rgba(27,79,216,0.12) !important;
}}
div[data-testid="stMultiSelect"] > div,
div[data-testid="stSelectbox"] > div > div {{
    background: {BG_CARD} !important;
    border: 1.5px solid {BORDER} !important;
    border-radius: 10px !important;
    color: {T_DARK} !important;
}}

/* ── Badges ── */
.badge {{
    display: inline-flex; align-items: center; gap: 4px;
    padding: 3px 10px; border-radius: 20px;
    font-size: 10px; font-weight: 700; letter-spacing: .6px;
    font-family: 'JetBrains Mono', monospace; white-space: nowrap;
}}
.badge-rouge   {{ background: rgba(220,38,38,.1);   border: 1px solid {C_CORAL}44;   color: {C_CORAL}; }}
.badge-orange  {{ background: rgba(217,119,6,.1);   border: 1px solid {C_AMBER}44;   color: {C_AMBER}; }}
.badge-vert    {{ background: rgba(5,150,105,.1);   border: 1px solid {C_EMERALD}44; color: {C_EMERALD}; }}
.badge-dropout  {{ background: rgba(220,38,38,.08);  border: 1px solid {C_CORAL}33;   color: {C_CORAL}; }}
.badge-enrolled {{ background: rgba(217,119,6,.08);  border: 1px solid {C_AMBER}33;   color: {C_AMBER}; }}
.badge-graduate {{ background: rgba(5,150,105,.08);  border: 1px solid {C_EMERALD}33; color: {C_EMERALD}; }}
.badge-blue     {{ background: rgba(27,79,216,.08);  border: 1px solid {C_COBALT}33;  color: {C_COBALT}; }}

/* ── Tags SHAP ── */
.shap-pos {{
    background: rgba(220,38,38,.07); border: 1px solid {C_CORAL}33;
    color: {C_CORAL}; border-radius: 5px; padding: 1px 7px;
    font-size: 10px; font-family: 'JetBrains Mono',monospace; white-space: nowrap;
}}
.shap-neg {{
    background: rgba(5,150,105,.07); border: 1px solid {C_EMERALD}33;
    color: {C_EMERALD}; border-radius: 5px; padding: 1px 7px;
    font-size: 10px; font-family: 'JetBrains Mono',monospace; white-space: nowrap;
}}

/* ── Student ID ── */
.stu-id {{
    font-family: 'JetBrains Mono', monospace; font-size: 12px;
    font-weight: 600; color: {C_COBALT};
    background: rgba(27,79,216,0.08); border: 1px solid {C_COBALT}33;
    padding: 2px 8px; border-radius: 6px;
}}

/* ── Tableau Top 10 ── */
.top10-wrap {{ overflow-x: auto; border-radius: 14px; border: 1px solid {BORDER}; }}
.top10-table {{ width: 100%; border-collapse: collapse; }}
.top10-table thead tr {{ background: {BG_SIDEBAR}; }}
.top10-table thead th {{
    padding: 13px 16px; font-size: 9px; font-weight: 700;
    letter-spacing: 1.8px; text-transform: uppercase;
    color: rgba(248,250,252,.55); font-family: 'JetBrains Mono',monospace;
    text-align: left; white-space: nowrap;
}}
.top10-table tbody tr {{
    border-bottom: 1px solid {BORDER}; background: {BG_CARD};
    transition: background .15s;
}}
.top10-table tbody tr:nth-child(odd)  {{ background: #F8FAFC; }}
.top10-table tbody tr:hover           {{ background: rgba(27,79,216,0.04); }}
.top10-table td {{ padding: 12px 16px; font-size: 13px; color: {T_MID}; vertical-align: middle; }}
.rank-badge {{
    width: 30px; height: 30px; border-radius: 8px;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 800; font-family: 'JetBrains Mono',monospace;
}}
.rank-1 {{ background: rgba(220,38,38,.12);  color:{C_CORAL};   border:1px solid {C_CORAL}44; }}
.rank-2 {{ background: rgba(217,119,6,.12);  color:{C_AMBER};   border:1px solid {C_AMBER}44; }}
.rank-3 {{ background: rgba(27,79,216,.12);  color:{C_COBALT};  border:1px solid {C_COBALT}44; }}
.rank-n {{ background: {BG_PAGE};            color:{T_LIGHT};   border:1px solid {BORDER}; }}
.score-bar-wrap {{ display: flex; align-items: center; gap: 8px; min-width: 160px; }}
.score-bar-bg   {{ flex: 1; height: 7px; background: {BORDER}; border-radius: 4px; overflow: hidden; }}
.score-bar-fill {{ height: 100%; border-radius: 4px; }}
.score-txt {{ font-size: 12px; font-weight: 700; color: {T_DARK}; font-family: 'JetBrains Mono',monospace; white-space: nowrap; min-width: 45px; }}

/* ── Alert bar ── */
.alert-bar-wrap {{ margin-bottom: 10px; }}
.alert-bar {{ display: flex; height: 14px; border-radius: 8px; overflow: hidden; gap: 3px; }}
.alert-seg {{ height: 100%; border-radius: 5px; }}
.stat-pills {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; }}
.stat-pill {{
    display: inline-flex; align-items: center; gap: 7px;
    background: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 10px;
    padding: 6px 14px; font-size: 12px; color: {T_MID}; font-weight: 500;
}}
.stat-dot {{ width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }}

/* ── Summary rows ── */
.summary-row {{
    display: flex; justify-content: space-between; align-items: center;
    padding: 9px 0; border-bottom: 1px solid {BORDER};
    font-size: 13px; color: {T_MID};
}}
.summary-row:last-child {{ border-bottom: none; }}
.summary-key {{ font-weight: 500; }}
.summary-val {{ font-weight: 700; color: {T_DARK}; font-family: 'JetBrains Mono',monospace; }}

/* ── Profile card ── */
.profile-card {{
    background: {BG_CARD}; border: 1px solid {BORDER};
    border-radius: 16px; padding: 26px 24px;
    box-shadow: 0 1px 3px rgba(15,23,42,0.05);
    position: relative; overflow: hidden;
}}
.profile-card::before {{
    content:''; position:absolute; top:0; left:0; right:0;
    height: 5px; border-radius: 16px 16px 0 0;
}}
.profile-card.rouge::before  {{ background: linear-gradient(90deg,{C_CORAL},{C_CORAL}90); }}
.profile-card.orange::before {{ background: linear-gradient(90deg,{C_AMBER},{C_AMBER}90); }}
.profile-card.vert::before   {{ background: linear-gradient(90deg,{C_EMERALD},{C_EMERALD}90); }}
.profile-avatar {{
    width: 52px; height: 52px; border-radius: 12px;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 22px; margin-bottom: 14px;
}}
.profile-avatar.rouge  {{ background: rgba(220,38,38,.1);  border: 1px solid {C_CORAL}33; }}
.profile-avatar.orange {{ background: rgba(217,119,6,.1);  border: 1px solid {C_AMBER}33; }}
.profile-avatar.vert   {{ background: rgba(5,150,105,.1);  border: 1px solid {C_EMERALD}33; }}
.profile-id {{
    font-family: 'JetBrains Mono',monospace; font-size: 22px;
    font-weight: 800; color: {T_DARK}; letter-spacing: -.5px; margin-bottom: 4px;
}}
.profile-sub {{
    font-size: 10px; color: {T_LIGHT}; font-family: 'JetBrains Mono',monospace;
    letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 14px;
}}
.profile-badges {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }}
.profile-divider {{ width:100%; height:1px; background:{BORDER}; margin:12px 0; }}
.profile-meta {{ display:flex; flex-direction:column; gap:8px; }}
.meta-row {{ display:flex; justify-content:space-between; align-items:center; font-size:12px; }}
.meta-key {{ color:{T_LIGHT}; font-weight:500; }}
.meta-val {{ color:{T_DARK}; font-weight:700; font-family:'JetBrains Mono',monospace; }}

/* ── Recommendation cards ── */
.reco-card {{
    background:{BG_CARD}; border:1px solid {BORDER};
    border-radius:12px; padding:14px 16px;
    border-left:4px solid {C_COBALT}; margin-bottom:8px;
}}
.reco-card.rouge  {{ border-left-color:{C_CORAL}; }}
.reco-card.orange {{ border-left-color:{C_AMBER}; }}
.reco-card.vert   {{ border-left-color:{C_EMERALD}; }}
.reco-title {{ font-size:13px; font-weight:700; color:{T_DARK}; margin-bottom:3px; }}
.reco-desc  {{ font-size:11px; color:{T_MID}; line-height:1.6; }}

/* ── Gauge label ── */
.gauge-label {{
    text-align:center; font-size:10px; font-weight:700; letter-spacing:2px;
    text-transform:uppercase; color:{T_LIGHT};
    font-family:'JetBrains Mono',monospace; margin-bottom:4px;
}}

/* ── Footer ── */
.page-footer {{
    text-align:center; padding:24px 0 0; margin-top:12px;
    border-top:1px solid {BORDER}; font-size:10px; color:{T_LIGHT};
    font-family:'JetBrains Mono',monospace; letter-spacing:1.5px;
    text-transform:uppercase;
}}

/* ── Filière table ── */
.ftable-wrap {{
    background:{BG_CARD}; border:1px solid {BORDER};
    border-radius:14px; overflow:hidden;
}}
.ftable-head {{
    display:grid;
    grid-template-columns: 2fr 0.7fr 0.8fr 1fr 1fr 1fr 0.9fr;
    background:{BG_SIDEBAR}; padding:10px 18px;
    font-size:9px; font-weight:700; letter-spacing:1.8px;
    text-transform:uppercase; color:rgba(248,250,252,.5);
    font-family:'JetBrains Mono',monospace;
}}
.ftable-row {{
    display:grid;
    grid-template-columns: 2fr 0.7fr 0.8fr 1fr 1fr 1fr 0.9fr;
    padding:12px 18px; border-bottom:1px solid {BORDER};
    align-items:center; transition:background .15s;
}}
.ftable-row:hover {{ background:{BG_PAGE}; }}
.ftable-row:last-child {{ border-bottom:none; }}
.fil-name {{ font-size:13px; font-weight:700; color:{T_DARK}; }}
.fil-sub  {{ font-size:10px; color:{T_LIGHT}; font-family:'JetBrains Mono',monospace; margin-top:2px; }}
.cell-mono {{ font-family:'JetBrains Mono',monospace; font-size:12px; font-weight:700; color:{T_DARK}; }}

/* ══════════════════════════════════════════════════════════
   TOOLTIPS GUIDE EN BULLES
   ══════════════════════════════════════════════════════════ */
.guide-tooltip {{
    position: relative;
    display: inline-flex;
    align-items: center;
    cursor: pointer;
    margin-left: 6px;
}}
.guide-tooltip .gt-icon {{
    width: 18px; height: 18px; border-radius: 50%;
    background: {C_COBALT}18; border: 1.5px solid {C_COBALT}44;
    color: {C_COBALT}; font-size: 11px; font-weight: 700;
    display: inline-flex; align-items: center; justify-content: center;
    font-family: 'JetBrains Mono', monospace;
    transition: all .2s;
    user-select: none;
    flex-shrink: 0;
}}
.guide-tooltip:hover .gt-icon {{
    background: {C_COBALT}; color: white;
    box-shadow: 0 2px 10px rgba(27,79,216,0.35);
}}
.guide-tooltip .gt-bubble {{
    display: none;
    position: absolute;
    left: 26px; top: 50%;
    transform: translateY(-50%);
    background: {BG_SIDEBAR};
    color: {T_WHITE};
    border-radius: 12px;
    padding: 14px 16px;
    width: 260px;
    font-size: 12px;
    line-height: 1.65;
    z-index: 9999;
    box-shadow: 0 8px 32px rgba(15,23,42,0.35), 0 2px 8px rgba(15,23,42,0.2);
    pointer-events: none;
}}
.guide-tooltip .gt-bubble::before {{
    content: '';
    position: absolute;
    left: -7px; top: 50%;
    transform: translateY(-50%);
    border: 7px solid transparent;
    border-right-color: {BG_SIDEBAR};
    border-left-width: 0;
}}
.guide-tooltip .gt-bubble .gt-title {{
    font-size: 12px; font-weight: 700; color: {T_WHITE};
    margin-bottom: 6px; letter-spacing: .3px;
    display: flex; align-items: center; gap: 6px;
}}
.guide-tooltip .gt-bubble .gt-body {{
    color: rgba(248,250,252,.72); font-size: 11px;
}}
.guide-tooltip:hover .gt-bubble {{
    display: block;
}}

/* Bulle qui s'ouvre à gauche (pour éléments en bout de ligne) */
.guide-tooltip.left .gt-bubble {{
    left: auto;
    right: 26px;
}}
.guide-tooltip.left .gt-bubble::before {{
    left: auto;
    right: -7px;
    border-right-color: transparent;
    border-left-color: {BG_SIDEBAR};
    border-left-width: 7px;
    border-right-width: 0;
}}

/* ── Bandeau de guide ── */
.guide-banner {{
    background: linear-gradient(135deg, {C_COBALT}0A 0%, {C_COBALT}18 100%);
    border: 1px solid {C_COBALT}22;
    border-radius: 14px; padding: 14px 20px;
    display: flex; align-items: flex-start; gap: 14px;
    margin-bottom: 4px;
}}
.guide-banner-icon {{
    font-size: 22px; flex-shrink: 0; margin-top: 2px;
}}
.guide-banner-content {{ flex: 1; }}
.guide-banner-title {{
    font-size: 13px; font-weight: 700; color: {C_COBALT}; margin-bottom: 4px;
}}
.guide-banner-text {{
    font-size: 12px; color: {T_MID}; line-height: 1.6;
}}
.guide-steps {{
    display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px;
}}
.guide-step {{
    display: inline-flex; align-items: center; gap: 6px;
    background: {BG_CARD}; border: 1px solid {BORDER};
    border-radius: 8px; padding: 5px 12px;
    font-size: 11px; color: {T_MID}; font-weight: 500;
}}
.guide-step-num {{
    width: 18px; height: 18px; border-radius: 50%;
    background: {C_COBALT}; color: white;
    font-size: 10px; font-weight: 700;
    display: inline-flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# HELPERS HTML PURS (retournent des str — pas de st.markdown)
# ─────────────────────────────────────────────────────────────────

def score_color(pct: float) -> str:
    """Retourne la couleur correspondant à un score de risque."""
    if pct >= 70:
        return C_CORAL
    if pct >= 40:
        return C_AMBER
    return C_EMERALD


def alert_color(level: str) -> str:
    """Retourne la couleur d'alerte pour un niveau donné."""
    return {"rouge": C_CORAL, "orange": C_AMBER, "vert": C_EMERALD}.get(level, C_COBALT)


def badge_alert(level: str) -> str:
    """Génère le HTML d'un badge de niveau d'alerte."""
    return f'<span class="badge badge-{level}">● {level.capitalize()}</span>'


def badge_pred(label: str) -> str:
    """Génère le HTML d'un badge de prédiction (Dropout / Enrolled / Graduate)."""
    cls = {"Dropout": "dropout", "Enrolled": "enrolled", "Graduate": "graduate"}.get(label, "blue")
    return f'<span class="badge badge-{cls}">{label}</span>'


def rank_badge(n: int) -> str:
    """Génère le HTML d'un badge de classement (Top 10)."""
    cls = {1: "rank-1", 2: "rank-2", 3: "rank-3"}.get(n, "rank-n")
    return f'<span class="rank-badge {cls}">#{n}</span>'


def hex_rgba(h: str, a: float) -> str:
    """Convertit un code hex + alpha en chaîne rgba() CSS."""
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{a})"


def guide_tooltip(title: str, text: str, direction: str = "") -> str:
    """
    Retourne le HTML d'un tooltip bulle standalone.
    Paramètres :
        title     — Titre affiché dans la bulle (sans emoji, il est ajouté).
        text      — Corps de la bulle.
        direction — "left" pour ouvrir la bulle à gauche (fin de ligne).
    Usage :
        html = f'Mon label {guide_tooltip("Aide", "Explication…")}'
        st.markdown(html, unsafe_allow_html=True)
    """
    cls = f"guide-tooltip {direction}".strip()
    return (
        f'<span class="{cls}">'
        f'  <span class="gt-icon">?</span>'
        f'  <div class="gt-bubble">'
        f'    <div class="gt-title">💡 {title}</div>'
        f'    <div class="gt-body">{text}</div>'
        f'  </div>'
        f'</span>'
    )


def top3_shap(shap_json: str) -> list:
    """
    Retourne les 3 features SHAP les plus importantes depuis un JSON.
    Retourne une liste de tuples (nom_court, valeur).
    """
    try:
        d = json.loads(shap_json)
        top = sorted(d.items(), key=lambda kv: abs(kv[1]), reverse=True)[:3]
        return [(k.split("(")[0].strip()[:24], v) for k, v in top]
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────
# HELPERS UI (appelés dans des fonctions, jamais au niveau global)
# ─────────────────────────────────────────────────────────────────

def render_topbar(icon: str, title: str, subtitle: str, total: int = 0) -> None:
    """Affiche la barre de navigation supérieure (sticky, fond sombre)."""
    total_str = f"🗄️ {total:,} étudiants" if total else ""
    chip_db = (
        f"<span class='chip chip-db'>{total_str}</span>"
        if total_str else ""
    )
    st.markdown(f"""
    <div class="topbar">
      <div class="topbar-left">
        <span class="topbar-icon">{icon}</span>
        <div>
          <p class="topbar-title">{title}</p>
          <p class="topbar-sub">{subtitle}</p>
        </div>
      </div>
      <div class="topbar-right">
        {chip_db}
        <span class="chip chip-live">En ligne</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


def section_header(
    icon: str,
    title: str,
    guide_title: str = "",
    guide_text: str = "",
    guide_direction: str = "left",
) -> None:
    """
    Affiche un en-tête de section avec icône et titre.
    Si guide_title et guide_text sont fournis, un tooltip '?' est ajouté.

    Paramètres :
        icon            — Emoji ou caractère affiché à gauche.
        title           — Texte du titre (affiché en majuscules via CSS).
        guide_title     — Titre de la bulle d'aide (optionnel).
        guide_text      — Corps de la bulle d'aide (optionnel).
        guide_direction — "left" (défaut) ou "" pour ouvrir à droite.
    """
    tooltip_html = ""
    if guide_title and guide_text:
        tooltip_html = guide_tooltip(guide_title, guide_text, direction=guide_direction)

    st.markdown(
        f'<div class="sec-header">'
        f'  <span class="sec-icon">{icon}</span>'
        f'  <span class="sec-title">{title}</span>'
        f'  {tooltip_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def guide_banner(title: str, text: str, steps: list | None = None) -> None:
    """
    Affiche un bandeau d'aide contextuel (fond bleu pâle).

    Paramètres :
        title — Titre en gras cobalt.
        text  — Description courte.
        steps — Liste optionnelle d'étapes numérotées (list[str]).
    """
    steps_html = ""
    if steps:
        items = "".join(
            f'<span class="guide-step">'
            f'  <span class="guide-step-num">{i}</span>{step}'
            f'</span>'
            for i, step in enumerate(steps, 1)
        )
        steps_html = f'<div class="guide-steps">{items}</div>'

    st.markdown(
        f'<div class="guide-banner">'
        f'  <div class="guide-banner-icon">💡</div>'
        f'  <div class="guide-banner-content">'
        f'    <div class="guide-banner-title">{title}</div>'
        f'    <div class="guide-banner-text">{text}</div>'
        f'    {steps_html}'
        f'  </div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def sidebar_kpis(
    kpis: dict,
    page_icon: str,
    page_title: str,
    page_sub: str = "",
) -> None:
    """Affiche les KPI globaux dans la sidebar (nom de page + compteurs)."""
    with st.sidebar:
        st.write("")
        st.markdown(
            f'<div style="padding:6px 0 18px;">'
            f'  <div style="font-size:24px; margin-bottom:6px;">{page_icon}</div>'
            f'  <div style="font-size:14px; font-weight:800; color:{T_WHITE};">{page_title}</div>'
            f'  <div style="font-size:9px; color:rgba(248,250,252,.35);'
            f'              font-family:\'JetBrains Mono\',monospace;'
            f'              letter-spacing:1.5px; margin-top:3px;">'
            f'    {page_sub}'
            f'  </div>'
            f'</div>'
            f'<hr>',
            unsafe_allow_html=True,
        )
        if kpis:
            st.markdown(
                f'<div style="font-size:11px; line-height:2.4;'
                f'            color:rgba(248,250,252,.6);'
                f'            font-family:\'JetBrains Mono\',monospace;">'
                f'  TOTAL &nbsp;&nbsp;: {kpis["total"]}<br>'
                f'  🔴 ROUGE &nbsp;: {kpis["rouge"]} ({kpis["pct_rouge"]}%)<br>'
                f'  🟠 ORANGE : {kpis["orange"]} ({kpis["pct_orange"]}%)<br>'
                f'  🟢 VERT &nbsp;&nbsp;: {kpis["vert"]} ({kpis["pct_vert"]}%)<br>'
                f'  📉 TAUX &nbsp;&nbsp;: {kpis["taux"]}%'
                f'</div>',
                unsafe_allow_html=True,
            )


# ─────────────────────────────────────────────────────────────────
# BASE DE DONNÉES
# ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def load_predictions(path: str = DB_PATH) -> pd.DataFrame:
    """
    Charge la table `predictions` depuis la base SQLite.
    Ajoute une colonne `score_pct` (risque en %).
    Lève st.stop() si la base est introuvable.
    """
    try:
        con = sqlite3.connect(path)
        df  = pd.read_sql_query("SELECT * FROM predictions", con)
        con.close()
        df["score_pct"] = (df["risk_score"] * 100).round(1)
        return df
    except Exception as e:
        st.error(f"❌ Base de données introuvable : {e}")
        st.stop()


def compute_kpis(df: pd.DataFrame) -> dict:
    """
    Calcule les KPI globaux à partir du DataFrame de prédictions.
    Retourne un dict avec les clés :
        total, rouge, orange, vert,
        dropout, enrolled, graduate,
        taux, pct_rouge, pct_orange, pct_vert,
        score_moy, accuracy.
    """
    total    = len(df)
    rouge    = int((df["alert_level"] == "rouge").sum())
    orange   = int((df["alert_level"] == "orange").sum())
    vert     = int((df["alert_level"] == "vert").sum())
    dropout  = int((df["pred_label"]  == "Dropout").sum())
    enrolled = int((df["pred_label"]  == "Enrolled").sum())
    graduate = int((df["pred_label"]  == "Graduate").sum())
    return dict(
        total=total,
        rouge=rouge,
        orange=orange,
        vert=vert,
        dropout=dropout,
        enrolled=enrolled,
        graduate=graduate,
        taux=round(dropout / total * 100, 1) if total else 0,
        pct_rouge=round(rouge   / total * 100, 1) if total else 0,
        pct_orange=round(orange / total * 100, 1) if total else 0,
        pct_vert=round(vert     / total * 100, 1) if total else 0,
        score_moy=round(df["score_pct"].mean(), 1) if total else 0,
        accuracy=round(
            (df["true_label"] == df["pred_label"]).sum() / total * 100, 1
        ) if total and "true_label" in df.columns else 0,
    )


# ─────────────────────────────────────────────────────────────────
# HELPERS PLOTLY
# ─────────────────────────────────────────────────────────────────

def base_layout(**kwargs) -> dict:
    """
    Retourne un dict de layout Plotly de base (fond transparent, police Outfit).
    Les kwargs surchargent les valeurs par défaut.
    """
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=BG_CARD,
        font=dict(family="Outfit, sans-serif", color=T_MID, size=12),
        margin=dict(l=10, r=10, t=44, b=10),
    )
    layout.update(kwargs)
    return layout