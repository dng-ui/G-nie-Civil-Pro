"""
╔══════════════════════════════════════════════════════════════╗
║          GÉNIE CIVIL PRO v10 — Application Web Complète      ║
║          BAEL 91 — Mbouda, Cameroun                          ║
║          DALOKO — +237 681 605 462                           ║
║          Lancer : streamlit run app_genie_civil_pro.py       ║
╚══════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import math
import os
from string import Template
from datetime import datetime

try:                                  # module de calcul des planchers à corps creux (fichier corps_creux.py, même dossier)
    import corps_creux as ccm
    CC_OK = True
except Exception:                     # pragma: no cover
    ccm = None
    CC_OK = False

# ══════════════════════════════════════════════════════════════
# CONSTANTES ET MATÉRIAUX
# ══════════════════════════════════════════════════════════════
GAMMA_B, GAMMA_S = 1.5, 1.15

BETONS = {"C20/25": 20, "C25/30": 25, "C30/37": 30, "C35/45": 35}
ACIERS = {"HA400": 400, "HA500": 500}

DIAMS = {
    6: 28.27, 8: 50.27, 10: 78.54, 12: 113.1,
    14: 153.94, 16: 201.06, 20: 314.16, 25: 490.87, 32: 804.25
}
DIAM_MAX = 14      # plus gros diamètre d'acier HA disponible sur le marché local : aucun choix ne dépasse HA14

CORPS_CREUX = {
    "12+4": 2.20, "15+5": 2.50, "16+4": 2.80,
    "20+5": 3.20, "25+5": 3.80
}

CHARGES_Q = {
    "Habitation": 1.5,
    "Studio / Appartement": 2.0,
    "Bureau / Administration": 2.5,
    "Usage éducatif (salle de classe)": 3.5,
    "Commerce RDC": 5.0,
    "Escalier commun": 2.5,
    "Toiture inaccessible": 1.0,
    "Toiture terrasse accessible": 3.5,
    "Balcon / Véranda": 3.5,
}

# Marqueur visuel des champs obligatoires (étoile rouge)
REQ = " :red[*]"
OPT = " *(facultatif)*"

# ══════════════════════════════════════════════════════════════
# THÈMES (le choix se fait dans la barre latérale)
# ══════════════════════════════════════════════════════════════
THEMES = {
    "🔵 Bleu Ingénieur": {
        "primary": "#1C2B3A", "accent": "#E07B39", "accent_hover": "#C8632A",
        "bg": "#FFFFFF", "surface": "#F5F5F5", "text": "#1C2B3A", "border": "#E0E0E0",
        "side_bg": "#1C2B3A", "side_bg2": "#26394D", "side_text": "#FFFFFF",
    },
    "🌙 Sombre": {
        "primary": "#F2F4F7", "accent": "#F59E0B", "accent_hover": "#D98A06",
        "bg": "#0F172A", "surface": "#1E293B", "text": "#E5E7EB", "border": "#334155",
        "side_bg": "#020617", "side_bg2": "#0B1226", "side_text": "#E5E7EB",
    },
    "🌿 Vert Chantier": {
        "primary": "#1B4332", "accent": "#2D9F6B", "accent_hover": "#238156",
        "bg": "#F7FBF8", "surface": "#E6F2EA", "text": "#1B4332", "border": "#C5DFCF",
        "side_bg": "#1B4332", "side_bg2": "#2D6A4F", "side_text": "#FFFFFF",
    },
    "🟠 Terre Cuite": {
        "primary": "#7C2D12", "accent": "#EA580C", "accent_hover": "#C2410C",
        "bg": "#FFFBF7", "surface": "#FDEBDD", "text": "#431407", "border": "#F5CBA7",
        "side_bg": "#7C2D12", "side_bg2": "#9A3412", "side_text": "#FFFFFF",
    },
    "🟣 Violet Moderne": {
        "primary": "#3B0764", "accent": "#9333EA", "accent_hover": "#7E22CE",
        "bg": "#FDFAFF", "surface": "#F1E8FB", "text": "#3B0764", "border": "#DCC8F2",
        "side_bg": "#3B0764", "side_bg2": "#581C87", "side_text": "#FFFFFF",
    },
    "⚪ Clair Minimal": {
        "primary": "#111827", "accent": "#2563EB", "accent_hover": "#1D4ED8",
        "bg": "#FFFFFF", "surface": "#F3F4F6", "text": "#111827", "border": "#E5E7EB",
        "side_bg": "#F3F4F6", "side_bg2": "#E5E7EB", "side_text": "#111827",
    },
}

CSS_TEMPLATE = Template("""
<style>
/* ---------- Fond général ---------- */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background: ${bg} !important;
}
.stApp p, .stApp li, .stApp label, .stApp summary,
[data-testid="stMetricLabel"], [data-testid="stMetricValue"],
[data-testid="stCaptionContainer"] {
    color: ${text};
}

/* ---------- Titres en GRAS ---------- */
h1, h2, h3, h4,
[data-testid="stHeading"] h1, [data-testid="stHeading"] h2, [data-testid="stHeading"] h3 {
    font-weight: 800 !important;
    color: ${primary} !important;
    letter-spacing: -0.2px;
}
h1 { border-bottom: 4px solid ${accent}; padding-bottom: 8px; }
[data-testid="stMetricLabel"] p { font-weight: 700 !important; }
[data-testid="stMetricValue"] { font-weight: 800 !important; }
[data-testid="stExpander"] summary p { font-weight: 700 !important; }
label p { font-weight: 600 !important; }

/* ---------- Barre latérale ---------- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, ${side_bg} 0%, ${side_bg2} 100%) !important;
}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
[data-testid="stSidebar"] small, [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: ${side_text} !important;
}
[data-testid="stSidebar"] .stRadio label {
    padding: 6px 8px; border-radius: 8px;
}
[data-testid="stSidebar"] .stRadio label:hover { background: rgba(255,255,255,0.10); }
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="input"] {
    background: rgba(255,255,255,0.12) !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
}
[data-testid="stSidebar"] input, [data-testid="stSidebar"] [data-baseweb="select"] * {
    color: ${side_text} !important;
}

/* ---------- Boutons ---------- */
.stButton > button, .stDownloadButton > button {
    background: ${accent}; color: white !important; font-weight: 700;
    border: none; border-radius: 8px; width: 100%; padding: 0.55rem 1rem;
    box-shadow: 0 2px 6px rgba(0,0,0,0.15); transition: all .15s ease-in-out;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    background: ${accent_hover}; color: white !important; transform: translateY(-1px);
}
.stButton > button p, .stDownloadButton > button p { color: white !important; font-weight: 700; }

/* ---------- Champs de saisie ---------- */
.stApp input, .stApp textarea,
.stApp [data-baseweb="select"] > div, .stApp [data-baseweb="input"],
.stApp [data-baseweb="base-input"] {
    background: ${surface} !important; color: ${text} !important;
}
.stApp [data-baseweb="select"] * { color: ${text}; }

/* ---------- Cartes / métriques ---------- */
div[data-testid="metric-container"] {
    background: ${surface}; border: 1px solid ${border};
    border-left: 5px solid ${accent}; border-radius: 10px; padding: 12px;
}
[data-testid="stExpander"] {
    border: 1px solid ${border}; border-radius: 10px; background: ${surface};
}
hr { border-color: ${border} !important; }

.legende-requis {
    background: ${surface}; border: 1px dashed ${accent}; border-radius: 8px;
    padding: 6px 12px; font-size: 0.9rem; margin-bottom: 10px;
}
.ok  { color: #2E7D32; font-weight: bold; }
.nok { color: #C62828; font-weight: bold; }

/* ---------- Bouton d'ouverture du menu (flèche ») : grand et attractif ---------- */
[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapsedControl"] button,
[data-testid="collapsedControl"] button {
    background: ${accent} !important;
    color: #FFFFFF !important;
    border: 3px solid #FFFFFF !important;
    border-radius: 999px !important;
    min-width: 64px !important;
    height: 56px !important;
    padding: 0 20px 0 14px !important;
    margin: 6px 0 0 6px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    z-index: 999999 !important;
    box-shadow: 0 6px 18px rgba(0,0,0,0.35) !important;
    animation: gcp-pulse 1.8s ease-in-out infinite;
    transition: transform .15s ease-in-out, background .15s ease-in-out;
}
[data-testid="stExpandSidebarButton"] *,
[data-testid="stSidebarCollapsedControl"] button *,
[data-testid="collapsedControl"] button * {
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
    font-size: 2.2rem !important;
    font-weight: 900 !important;
}
[data-testid="stExpandSidebarButton"]::after,
[data-testid="stSidebarCollapsedControl"] button::after,
[data-testid="collapsedControl"] button::after {
    content: "MENU";
    color: #FFFFFF;
    font-size: 1rem;
    font-weight: 900;
    letter-spacing: 1.5px;
    margin-left: 8px;
}
[data-testid="stExpandSidebarButton"]:hover,
[data-testid="stSidebarCollapsedControl"] button:hover,
[data-testid="collapsedControl"] button:hover {
    background: ${accent_hover} !important;
    transform: scale(1.08);
}
[data-testid="stExpandSidebarButton"]:active,
[data-testid="stSidebarCollapsedControl"] button:active,
[data-testid="collapsedControl"] button:active {
    transform: scale(0.95);
}
@keyframes gcp-pulse {
    0%   { box-shadow: 0 6px 18px rgba(0,0,0,0.35), 0 0 0 0 ${accent}; }
    70%  { box-shadow: 0 6px 18px rgba(0,0,0,0.35), 0 0 0 16px rgba(255,255,255,0); }
    100% { box-shadow: 0 6px 18px rgba(0,0,0,0.35), 0 0 0 0 rgba(255,255,255,0); }
}

/* ---------- Masquer barre d'outils Streamlit et Manage app ---------- */
[data-testid="stToolbarActions"] { display: none !important; }
[data-testid="stMainMenu"] { display: none !important; }
[data-testid="stAppDeployButton"] { display: none !important; }
.stAppDeployButton { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="manage-app-button"] { display: none !important; }
[class*="viewerBadge"] { display: none !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
</style>
""")

# ══════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ══════════════════════════════════════════════════════════════
def fbu(b):
    return 0.85 * BETONS[b] / GAMMA_B

def fsu(a):
    return ACIERS[a] / GAMMA_S

def barres(As, larg=None, nv=None):
    """Choix de barres (poteaux/poutres) limité à HA14."""
    if As <= 0: return "—"
    for di in [10, 12, 14]:
        sc = DIAMS[di] / 100
        for n in (nv or [3, 4, 5, 6, 8]):
            if n * sc < As: continue
            if larg and n > 1 and (larg - 6) / max(n - 1, 1) < 2.5: continue
            return f"{n}HA{di} ({round(n * sc, 2)} cm²)"
    return f"As={round(As, 2)} cm² (> HA14 : augmenter le nombre de barres ou la section)"

def choix_nappe(As, d_min, espacements, esp_pref=15.0, esp_min=10.0):
    """Choix d'une nappe HA/espacement pour As (cm²/ml).
    Logique : on cherche d'abord un espacement >= esp_pref (15 cm) avec le plus petit diamètre >= d_min,
    en prenant à chaque fois l'espacement le PLUS LARGE possible ; sinon >= esp_min (10 cm) ; sinon tout espacement.
    Retourne (diamètre, espacement, section fournie) ou None."""
    for emin in (esp_pref, esp_min, 0.0):
        for di, sm in sorted(DIAMS.items()):
            if di < d_min or di > DIAM_MAX:
                continue
            sc = sm / 100
            for e in sorted(espacements, reverse=True):          # du plus large au plus serré
                if e >= emin and sc / (e / 100) >= As:
                    return di, e, sc / (e / 100)
    return None

def barres_dalle(As):
    """Dalle : HA8 minimum, espacement le plus large possible (max 25 cm)."""
    if As <= 0: return "—"
    ch = choix_nappe(As, 8, [25, 20, 17.5, 15, 12.5, 10, 7.5])
    if ch:
        di, e, sec = ch
        return f"HA{di} / {e:g} cm  ({round(sec, 2)} cm²/ml)"
    return f"As={round(As, 2)} cm²/ml (> HA14 / 7,5 cm : augmenter l'épaisseur)"

# ══════════════════════════════════════════════════════════════
# MOTEUR DE CALCUL BAEL 91  (LOGIQUE INCHANGÉE)
# ══════════════════════════════════════════════════════════════

def calc_dalle(lx, ly, G, Q, beton="C25/30", acier="HA400"):
    fc28 = BETONS[beton]; fbu_ = fbu(beton); fsu_ = fsu(acier)
    rho = lx / ly; pu = 1.35 * G + 1.5 * Q; pser = G + Q
    mu_x = 1 / (8 * (1 + 2.4 * rho**3)); mu_y = rho**3 * mu_x
    Mtx = 0.75 * mu_x * pu * lx**2
    Mty = 0.75 * mu_y * pu * lx**2
    Max_ = 0.5 * mu_x * pu * lx**2
    Mtx_s = 0.75 * mu_x * pser * lx**2
    h = max(math.ceil(math.sqrt(max(Mtx, Max_) * 1e6 / (0.186 * 1000 * fbu_)) / 0.9 / 10), 12)
    d = 0.9 * h * 10

    def As(M):
        if M <= 0: return 0
        mu = M * 1e6 / (1000 * d**2 * fbu_)
        a = 1.25 * (1 - math.sqrt(max(1 - 2 * mu, 0)))
        return M * 1e6 / (d * (1 - 0.4 * a) * fsu_) / 100

    r0 = 0.0008 if ACIERS[acier] == 400 else 0.0006
    Ax = max(As(Mtx), r0 * (3 - rho) / 2 * h * 10)
    Ay = max(As(Mty), r0 * h * 10) if Mty > 0 else max(r0 * h * 10, Ax * 0.25)
    Aax = max(As(Max_), r0 * (3 - rho) / 2 * h * 10)
    Aay = max(r0 * h * 10, Aax * 0.25)

    try:
        n = 15; B_ = n * Ax * 100; C_ = -n * Ax * 100 * d
        disc = B_**2 - 4 * 500 * C_
        y1 = (-B_ + math.sqrt(max(disc, 0))) / (2 * 500)
        I = (1000 * y1**3) / 3 + n * Ax * 100 * (d - y1)**2
        sbc = round(Mtx_s * 1e6 * y1 / I, 2) if I > 0 else 0
    except:
        sbc = 0

    return {
        "type": "DALLE", "h": h, "d": round(d / 10, 1),
        "lx": lx, "ly": ly, "rho": round(rho, 3),
        "pu": round(pu, 2), "pser": round(pser, 2),
        "Mtx": round(Mtx, 3), "Mty": round(Mty, 3), "Max": round(Max_, 3),
        "Ax": round(Ax, 2), "Ay": round(Ay, 2), "Aax": round(Aax, 2), "Aay": round(Aay, 2),
        "disp_tx": barres_dalle(Ax), "disp_ty": barres_dalle(Ay),
        "disp_ax": barres_dalle(Aax), "disp_ay": barres_dalle(Aay),
        "sbc": sbc, "sbc_lim": round(0.6 * fc28, 1), "els_ok": sbc <= 0.6 * fc28,
        "beton": beton, "acier": acier
    }


def calc_poutre(portee, G_ml, Q_ml, larg=20, beton="C25/30", acier="HA400"):
    fc28 = BETONS[beton]; fbu_ = fbu(beton); fsu_ = fsu(acier)
    pu = 1.35 * G_ml + 1.5 * Q_ml
    Mt = pu * portee**2 / 8
    Vu = pu * portee / 2
    b = larg * 10
    d = math.sqrt(Mt * 1e6 / (0.269 * b * fbu_))
    h = max(math.ceil(d / 0.875 / 50) * 5, 20)
    d = h * 10 - 50
    mu = Mt * 1e6 / (b * d**2 * fbu_)
    a = 1.25 * (1 - math.sqrt(max(1 - 2 * mu, 0)))
    As = Mt * 1e6 / (d * (1 - 0.4 * a) * fsu_) / 100
    tau = Vu * 1000 / (b * d)
    tau_lim = min(0.2 * fc28 / GAMMA_B, 5.0)
    At = 2 * DIAMS[6]; ftj = 0.6 + 0.06 * fc28
    st = min(
        (At * 0.8 * ACIERS[acier]) / (b * max(tau - 0.3 * ftj, 0.1)) if tau > 0.3 * ftj
        else At * ACIERS[acier] / (0.4 * b),
        0.9 * d, 400
    )
    st_cm = max(math.floor(st / 50) * 5, 5)
    return {
        "type": "POUTRE", "h": h, "d": round(d / 10, 1),
        "portee": portee, "larg": larg,
        "pu": round(pu, 2), "Mt": round(Mt, 2), "Vu": round(Vu, 2),
        "As": round(As, 2), "disp": barres_poutre(As, larg),
        "cadres": f"∅6 / {int(st_cm)} cm",
        "tau": round(tau, 3), "tau_lim": round(tau_lim, 2),
        "cis_ok": tau <= tau_lim, "beton": beton, "acier": acier
    }


def barres_poutre(As, larg):
    """Choix de barres tendues d'une poutre de largeur larg (cm), HA14 MAXIMUM.
    1 lit d'abord (section fournie minimale) ; sinon 2 lits, avec As majorée de 6 % pour la perte de hauteur utile.
    Enrobage 3 cm + cadre ∅6 ; distance libre entre barres >= max(Ø ; 2,5 cm)."""
    if As <= 0: return "—"
    utile = larg - 2 * 3.6
    for lits in (1, 2):
        need = As * (1.0 if lits == 1 else 1.06)
        best = None
        for di in (10, 12, 14):
            sc = DIAMS[di] / 100
            for n_lit in range(2, 7):
                n = n_lit * lits
                if n * sc < need - 1e-9:
                    continue
                if (utile - n_lit * di / 10) / (n_lit - 1) < max(di / 10, 2.5):
                    continue
                cand = (round(n * sc, 4), n, di)
                if best is None or cand < best:
                    best = cand
        if best:
            note = "" if lits == 1 else " — 2 lits"
            return f"{best[1]}HA{best[2]} ({round(best[1] * DIAMS[best[2]] / 100, 2)} cm²){note}"
    return f"As={round(As, 2)} cm² — dépasse 2 lits de HA14 : augmenter b ou la hauteur"


def barres_poteau(A, b_cm, h_cm):
    """Armatures longitudinales de poteau, HA14 MAXIMUM : barres réparties sur le pourtour
    (enrobage 3 cm + cadre ∅6, distance moyenne entre barres >= max(Ø ; 2,5 cm))."""
    if A <= 0: return "—"
    perim = 2 * ((b_cm - 7.2) + (h_cm - 7.2))
    for di in (10, 12, 14):
        sc = DIAMS[di] / 100
        for n in (4, 6, 8, 10, 12, 14, 16, 20, 24):
            if n * sc < A - 1e-9:
                continue
            if perim / n < max(di / 10, 2.5) + di / 10:
                continue
            return f"{n}HA{di} ({round(n * sc, 2)} cm²)"
    return f"As={round(A, 2)} cm² (> 24HA14 : augmenter la section du poteau)"


def _cadres(tau, b, d, fc28, acier):
    """Cadres ∅6 : espacement par la même formule que la poutre isostatique."""
    At = 2 * DIAMS[6]; ftj = 0.6 + 0.06 * fc28
    st_ = min(
        (At * 0.8 * ACIERS[acier]) / (b * max(tau - 0.3 * ftj, 0.1)) if tau > 0.3 * ftj
        else At * ACIERS[acier] / (0.4 * b),
        0.9 * d, 400
    )
    return f"∅6 / {int(max(math.floor(st_ / 50) * 5, 5))} cm"


def calc_poutre_continue(portees, G_ml, Q_ml, larg=20, beton="C25/30", acier="HA400",
                         methode="auto", fiss_ok=True, solidaire=True):
    """Poutre continue (2 à 6 travées) sous charges linéiques uniformes G_ml, Q_ml (kN/m).
    Moments : méthode forfaitaire ou Caquot (minorée) du module corps_creux.py (validé). Section constante."""
    if not CC_OK:
        raise ValueError("Le fichier corps_creux.py est introuvable (méthodes forfaitaire/Caquot).")
    if len(portees) < 2 or any(l <= 0 for l in portees):
        raise ValueError("Une poutre continue demande au moins 2 travées de portées strictement positives.")
    if G_ml <= 0 or Q_ml < 0:
        raise ValueError("G doit être > 0 et Q >= 0 (kN/m).")
    fc28 = BETONS[beton]; fbu_ = fbu(beton); fsu_ = fsu(acier); fe = ACIERS[acier]
    ft28 = 0.6 + 0.06 * fc28
    n = len(portees)

    forf = ccm.moments_forfaitaire(portees, G_ml, Q_ml, 100.0, inertie_constante=True,
                                   fissuration_peu_prejudiciable=fiss_ok)
    cond = {k: v for k, v in forf["conditions"].items() if not k.startswith("Q <=")}
    cond["Q <= 2G (charges linéiques)"] = Q_ml <= 2 * G_ml
    if methode == "forfaitaire" and not all(cond.values()):
        raise ValueError("Méthode forfaitaire imposée mais conditions non satisfaites : "
                         + " ; ".join(k for k, v in cond.items() if not v) + ".")
    if methode == "auto":
        methode = "forfaitaire" if all(cond.values()) else ("caquot_minoree" if Q_ml <= 2 * G_ml else "caquot")

    pu = 1.35 * G_ml + 1.5 * Q_ml
    if methode == "forfaitaire":
        Mt, Ma = forf["Mt"], forf["Ma"]
        vf = [1.15, 1.15] if n == 2 else [1.10 if k in (0, n - 1) else 1.0 for k in range(n)]
        V = [pu * portees[k] / 2 * vf[k] for k in range(n)]
    else:
        cq = ccm.moments_caquot(portees, 1.35 * G_ml, 1.5 * Q_ml, minoree=(methode == "caquot_minoree"))
        Mt, Ma, V = cq["Mt"], cq["Ma"], cq["V"]

    M0 = [pu * l**2 / 8 for l in portees]
    Mu_appuis = []
    for i in range(n + 1):
        if i in (0, n):
            Mu_appuis.append(0.15 * M0[0 if i == 0 else n - 1] if (methode == "forfaitaire" and solidaire) else 0.0)
        else:
            Mu_appuis.append(Ma[i])
    Mmax = max(max(Mt), max(Mu_appuis))

    b = larg * 10
    d = math.sqrt(Mmax * 1e6 / (0.269 * b * fbu_))
    h = max(math.ceil(d / 0.875 / 50) * 5, 20)
    d = h * 10 - 50
    Amin = 0.23 * b * d * ft28 / fe / 100

    def As_(M):
        if M <= 0: return 0.0
        mu = M * 1e6 / (b * d**2 * fbu_)
        a = 1.25 * (1 - math.sqrt(max(1 - 2 * mu, 0)))
        return M * 1e6 / (d * (1 - 0.4 * a) * fsu_) / 100

    import re
    tau_lim = min(0.2 * fc28 / GAMMA_B, 5.0)
    travees = []
    for k in range(n):
        As_k = max(As_(Mt[k]), Amin)
        tau = V[k] * 1000 / (b * d)
        travees.append({"k": k + 1, "portee": portees[k], "Mt": round(Mt[k], 2), "Vu": round(V[k], 2),
                        "As": round(As_k, 2), "disp": barres_poutre(As_k, larg), "tau": round(tau, 3),
                        "cis_ok": tau <= tau_lim, "cadres": _cadres(tau, b, d, fc28, acier)})
    appuis = []
    tau_su = 0.6 * 1.5**2 * ft28
    for i in range(n + 1):
        rive = i in (0, n)
        As_i = max(As_(Mu_appuis[i]), Amin)
        txt = barres_poutre(As_i, larg)
        m = re.search(r"HA(\d+)", txt)
        ls = None
        if m:
            dia = int(m.group(1))
            ls = round(max(dia * fe / (4 * tau_su), dia * (40 if fe == 400 else 50)) / 10, 1)
        if rive:
            ref = portees[0 if i == 0 else n - 1]; div = 4
            nature = ("rive — 0,15 M0 (poutre solidaire de l'appui, encastrement partiel)"
                      if Mu_appuis[i] > 0 else "rive — armature minimale")
        else:
            ref = max(portees[i - 1], portees[i]); div = 4 if i in (1, n - 1) else 5
            nature = "intermédiaire — moment calculé"
        appuis.append({"appui": i + 1, "Mu": round(Mu_appuis[i], 2), "As": round(As_i, 2), "disp": txt,
                       "ls_cm": ls, "prolong_cm": round(ref * 100 / div, 1), "nature": nature})
    avert = []
    if Q_ml > G_ml:
        avert.append("Q > G : longueurs forfaitaires d'arrêt des barres (annexe E.1.3) non applicables — "
                     "tracer les courbes enveloppes des moments.")
    avert.append("Flèche non vérifiée. Charges linéiques supposées uniformes et identiques sur toutes les travées.")
    return {"type": "POUTRE_CONTINUE", "portees": list(portees), "larg": larg, "h": h, "d": round(d / 10, 1),
            "G": G_ml, "Q": Q_ml, "pu": round(pu, 2), "methode": methode, "conditions": cond,
            "As_min": round(Amin, 2), "tau_lim": round(tau_lim, 2), "travees": travees, "appuis": appuis,
            "avert": avert, "beton": beton, "acier": acier}


def calc_poteau(h_libre, G, Q, beton="C25/30", acier="HA400", b_cm=None, h_cm=None):
    fc28 = BETONS[beton]; fe = ACIERS[acier]
    Nu = 1.35 * G + 1.5 * Q; Nser = G + Q
    lf = 0.7 * h_libre * 1000
    rect = b_cm is not None and h_cm is not None

    if rect:
        lam_b = lf / ((b_cm * 10) / math.sqrt(12))
        lam_h = lf / ((h_cm * 10) / math.sqrt(12))
        lam = max(lam_b, lam_h)
        a0 = 0.65 / (1 + 0.2 * (lam / 35)**2) if lam <= 50 else 0.6 * (50 / lam)**2
        alpha = a0 / 1.10; tb = fc28 / (0.9 * GAMMA_B)
        Br = (b_cm * 10 - 20) * (h_cm * 10 - 20); B = b_cm * 10 * h_cm * 10
        As_th = max((Nu * 1000 / alpha - Br * tb) * GAMMA_S / fe, 0)
        As_min = max(4 * (2 * (b_cm + h_cm) * 10 / 1000) * 100, 0.002 * B)
        As = min(max(As_th, As_min), 0.05 * B)
        Nulim = alpha * (Br * tb + As * fe / GAMMA_S) / 1000
        cote = None; sbc = round(Nser * 1000 / B, 2); sbc_lim = round(0.6 * fc28, 2)
        dl = 10 if min(b_cm, h_cm) <= 20 else 12
        dc = 6 if dl <= 14 else 8
        st = max(math.floor(min(15 * dl, 400) / 10 / 5) * 5, 10)

        disp = barres_poteau(As / 100, b_cm, h_cm)
    else:
        a0 = 0.65 / (1 + 0.2 * (35 / 35)**2); alpha = a0 / 1.10
        tb = fc28 / (0.9 * GAMMA_B); ta = 0.01 * fe / GAMMA_S
        Br_min = Nu * 1000 / (alpha * (tb + ta))
        cote = max(math.ceil((math.sqrt(Br_min) + 20) / 50) * 5, 20)
        a_mm = cote * 10
        lam = lf / (a_mm / math.sqrt(12))
        ar0 = 0.65 / (1 + 0.2 * (lam / 35)**2) if lam <= 50 else 0.6 * (50 / lam)**2
        alpha = ar0 / 1.10; tb = fc28 / (0.9 * GAMMA_B)
        Br = (a_mm - 20)**2; B = a_mm**2
        As_th = max((Nu * 1000 / alpha - Br * tb) * GAMMA_S / fe, 0)
        As_min = max(4 * (4 * a_mm / 1000) * 100, 0.002 * a_mm**2)
        As = min(max(As_th, As_min), 0.05 * a_mm**2)
        Nulim = alpha * (Br * tb + As * fe / GAMMA_S) / 1000
        sbc = round(Nser * 1000 / a_mm**2, 2); sbc_lim = round(0.6 * fc28, 2)
        dl = 10 if cote <= 20 else 12 if cote <= 25 else 14
        dc = 6 if dl <= 14 else 8
        st = max(math.floor(min(15 * dl, 400) / 10 / 5) * 5, 10)
        disp = barres_poteau(As / 100, cote, cote)
        lam_b = lam_h = lam; b_cm = h_cm = cote

    return {
        "type": "POTEAU RECT" if rect else "POTEAU",
        "cote": cote, "b_cm": b_cm, "h_cm": h_cm, "rect": rect,
        "h_libre": h_libre, "lf": round(lf / 1000, 2), "lam": round(lam, 1),
        "Nu": round(Nu, 1), "Nser": round(Nser, 1),
        "As": round(As / 100, 2), "As_min": round(As_min / 100, 2),
        "disp": disp, "cadres": f"∅{dc}/{st}cm",
        "Nulim": round(Nulim, 1), "elu_ok": Nu <= Nulim,
        "sbc": sbc, "sbc_lim": sbc_lim, "els_ok": sbc <= sbc_lim,
        "beton": beton, "acier": acier
    }


def calc_fondation(G, Q, cote_pot, q_sol, beton="C25/30", acier="HA400", type_sol="admissible"):
    fc28 = BETONS[beton]; fsu_ = fsu(acier)
    Nu = 1.35 * G + 1.5 * Q; Nser = G + Q
    qu = q_sol if type_sol == "admissible" else q_sol / 2
    S = Nu / qu
    cote = max(math.ceil(math.sqrt(S) * 100 / 5) * 5, 60)
    A = cote * 10; a = cote_pot * 10
    d_cm = max(math.ceil((A - a) / 4 / 10 / 5) * 5, 20)
    h_cm = d_cm + 5; d_mm = d_cm * 10
    Ast = Nu * 1000 * (A - a) / (8 * d_mm * fsu_) / 100
    q_eff = (Nser + (cote / 100)**2 * (h_cm / 100) * 25) / (cote / 100)**2

    def fe(As):
        """Semelle : HA10 minimum, espacement le plus large possible (max 25 cm)."""
        ch = choix_nappe(As, 10, [25, 20, 17.5, 15, 12.5, 10, 7.5])
        if ch:
            di, e, sec = ch
            return f"HA{di}/{e:g}cm ({round(sec, 2)} cm²/ml)"
        return f"As={round(As, 2)} cm²/ml (> HA14 / 7,5 cm : augmenter l'épaisseur)"

    return {
        "type": "FONDATION",
        "cote": cote, "h": h_cm, "d": d_cm,
        "Nu": round(Nu, 1), "Nser": round(Nser, 1), "qu": round(qu, 1),
        "Ast": round(Ast, 2), "disp": fe(Ast / (cote / 100)),
        "nappes": "2 lits croisés identiques",
        "q_eff": round(q_eff, 1), "sol_ok": q_eff <= qu,
        "beton": beton, "acier": acier
    }


# ══════════════════════════════════════════════════════════════
# GÉNÉRATION PDF
# ══════════════════════════════════════════════════════════════
def generer_pdf(resultats, projet_nom, beton, acier):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        import tempfile

        BLEU   = colors.HexColor("#1C2B3A")
        ORANGE = colors.HexColor("#E07B39")
        VERT   = colors.HexColor("#2E7D32")
        GRIS   = colors.HexColor("#F5F5F5")
        GRIS2  = colors.HexColor("#E0E0E0")

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        doc = SimpleDocTemplate(tmp.name, pagesize=A4,
            leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

        sT = ParagraphStyle("t", fontSize=18, fontName="Helvetica-Bold", textColor=BLEU, spaceAfter=2)
        sS = ParagraphStyle("s", fontSize=10, fontName="Helvetica", textColor=ORANGE, spaceAfter=6)
        sH = ParagraphStyle("h", fontSize=12, fontName="Helvetica-Bold", textColor=BLEU, spaceBefore=12, spaceAfter=4)
        sN = ParagraphStyle("n", fontSize=9, fontName="Helvetica", leading=13)

        def tab(data, widths, header=True):
            t = Table(data, colWidths=widths)
            s = [
                ("FONTNAME",  (0,0), (-1,-1), "Helvetica"),
                ("FONTSIZE",  (0,0), (-1,-1), 8.5),
                ("GRID",      (0,0), (-1,-1), 0.4, GRIS2),
                ("TOPPADDING",(0,0), (-1,-1), 4),
                ("BOTTOMPADDING",(0,0),(-1,-1), 4),
                ("LEFTPADDING",(0,0),(-1,-1), 6),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, GRIS]),
            ]
            if header:
                s += [
                    ("BACKGROUND",  (0,0), (-1,0), BLEU),
                    ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
                    ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
                ]
            t.setStyle(TableStyle(s))
            return t

        c = []
        c.append(Paragraph("GÉNIE CIVIL PRO", sT))
        c.append(Paragraph("Note de calcul de structure — BAEL 91", sS))
        c.append(HRFlowable(width="100%", thickness=2, color=BLEU))
        c.append(Spacer(1, 0.3*cm))

        info = [
            ["Projet", projet_nom, "Date", datetime.now().strftime("%d/%m/%Y")],
            ["Béton", beton, "Acier", acier],
            ["Norme", "BAEL 91", "Contact", "+237 681 605 462 — Mbouda"],
        ]
        ti = Table(info, colWidths=[3*cm, 5.5*cm, 3*cm, 5.5*cm])
        ti.setStyle(TableStyle([
            ("FONTNAME",  (0,0),(0,-1), "Helvetica-Bold"),
            ("FONTNAME",  (2,0),(2,-1), "Helvetica-Bold"),
            ("FONTSIZE",  (0,0),(-1,-1), 8.5),
            ("BACKGROUND",(0,0),(0,-1), GRIS),
            ("BACKGROUND",(2,0),(2,-1), GRIS),
            ("GRID",      (0,0),(-1,-1), 0.3, GRIS2),
            ("TOPPADDING",(0,0),(-1,-1), 4),
            ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ]))
        c.append(ti)
        c.append(Spacer(1, 0.3*cm))
        c.append(HRFlowable(width="100%", thickness=1.5, color=BLEU))

        for el in resultats:
            t = el.get("type", "")

            if t == "CHARGES":
                c.append(Paragraph("CHARGES G ET Q — Descente de charges de plancher (BAEL 91)", sH))
                data = [["Composant", "G (kN/m²)"]]
                for comp in el["composants"]:
                    data.append([comp["nom"], str(comp["G"])])
                data += [
                    ["G total", f"{el['G']} kN/m²"],
                    [f"Q — {el['usage']}", f"{el['Q']} kN/m²"],
                    ["pu ELU = 1.35G + 1.5Q", f"{el['pu']} kN/m²"],
                    ["pser ELS = G + Q", f"{el['pser']} kN/m²"],
                ]
                c.append(tab(data, [11*cm, 6*cm]))

            elif t == "DALLE":
                c.append(Paragraph("DALLE — Méthode Rankine-Grashoff (BAEL 91)", sH))
                data = [["Paramètre", "Valeur"],
                    ["Dimensions", f"lx={el['lx']}m × ly={el['ly']}m  —  ρ={el['rho']}"],
                    ["Épaisseur retenue", f"{el['h']} cm"],
                    ["Hauteur utile d", f"{el['d']} cm"],
                    ["Charge ELU pu", f"{el['pu']} kN/m²"],
                    ["Charge ELS pser", f"{el['pser']} kN/m²"],
                    ["Moment travée x Mtx", f"{el['Mtx']} kN.m/ml"],
                    ["Moment travée y Mty", f"{el['Mty']} kN.m/ml"],
                    ["Moment appui x Max", f"{el['Max']} kN.m/ml"],
                    ["Ferraillage travée x", f"As={el['Ax']} cm²/ml  —  {el['disp_tx']}"],
                    ["Ferraillage travée y", f"As={el['Ay']} cm²/ml  —  {el['disp_ty']}"],
                    ["Ferraillage appui x",  f"As={el['Aax']} cm²/ml  —  {el['disp_ax']}"],
                    ["Vérif ELS béton", f"σbc={el['sbc']} / {el['sbc_lim']} MPa  —  {'CONFORME' if el['els_ok'] else 'NON CONFORME'}"],
                ]
                c.append(tab(data, [7*cm, 10*cm]))

            elif t == "CORPS_CREUX":
                def _t(x):
                    x = str(x)
                    for a_, b_ in (("∅", "Ø"), ("≤", "<="), ("≥", ">="), ("σ", "sigma"), ("τ", "tau"),
                                   ("Δ", "Delta"), ("λ", "lambda"), ("→", "->"), ("✓", "OK"), ("✗", "NON OK")):
                        x = x.replace(a_, b_)
                    return x
                c.append(Paragraph("PLANCHER À CORPS CREUX — Poutrelles et hourdis (BAEL 91)", sH))
                tp = "Coulée sur place" if el["type_poutrelle"] == "sur_place" else "Préfabriquée"
                data = [["Paramètre", "Valeur"],
                    ["Hourdis", f"{el['hourdis']}  —  hauteur totale {el['travees'][0]['h']} cm"],
                    ["Entraxe / âme b0", f"{el['entraxe']:g} cm / {el['b0']:g} cm"],
                    ["Poutrelle", tp],
                    ["Portées", " ; ".join(f"{x:g} m" for x in el["portees"])],
                    ["Charges G / Q", f"{el['G']} / {el['Q']} kN/m²"],
                    ["Méthode des moments", el["methode"]],
                ]
                c.append(tab(data, [7*cm, 10*cm]))
                for tv in el["travees"]:
                    c.append(Paragraph(f"Travée {tv['travee']} — portée {el['portees'][tv['travee'] - 1]:g} m", sH))
                    d2 = [["Paramètre", "Valeur"],
                        ["Moments ELU", f"Mt={tv['Mt']} / Ma={tv['Ma']} / M0={tv['M0']} kN.m"],
                        ["Table b / section", f"b={tv['b']} cm  —  {tv['mode']}"],
                        ["Armatures en travée", f"As={tv['As_calc']} cm² (min {tv['As_min']})  —  {tv.get('disp_travee', '—')}"],
                        ["Effort tranchant", f"Vu={tv['Vu']} kN  —  tau={tv['tau']} / {tv['tau_lim']} MPa  —  {'CONFORME' if tv['cis_ok'] else 'NON CONFORME'}"],
                    ]
                    if "sigma_bc" in tv:
                        d2.append(["Vérif ELS béton", f"sigma_bc={tv['sigma_bc']} / {tv['sigma_lim']} MPa  —  {'CONFORME' if tv['els_ok'] else 'NON CONFORME'}"])
                    if "fleche" in tv:
                        fl = tv["fleche"]
                        d2.append(["Flèche nuisible", f"Delta f={fl['delta_f']} mm / limite {fl['limite']} mm  —  {'CONFORME' if fl['ok'] else 'NON CONFORME'}"])
                    if tv.get("treillis"):
                        d2.append(["Treillis soudé", f"{tv['treillis']['choix_perp']} / {tv['treillis']['choix_par']}"])
                    c.append(tab([[_t(x) for x in row] for row in d2], [7*cm, 10*cm]))
                    for al in tv.get("alertes", []):
                        c.append(Paragraph("Alerte : " + _t(al), sN))
                if el["chapeaux"]:
                    c.append(Paragraph("Chapeaux sur appuis", sH))
                    d3 = [["Appui", "Mu (kN.m)", "Armatures", "ls (cm)", "Prolong. (cm)"]]
                    for ch in el["chapeaux"]:
                        d3.append([str(ch["appui"]), str(ch["Mu"]), _t(ch["barres"]),
                                   str(ch["ancrage_ls_cm"]), str(ch["prolongement_depuis_nu_cm"])])
                    c.append(tab(d3, [2*cm, 3*cm, 6*cm, 2.5*cm, 3.5*cm]))
                    c.append(Paragraph(_t(el["chapeaux"][0]["note_ancrage"]), sN))
                for al in el["avert"]:
                    c.append(Paragraph("Avertissement : " + _t(al), sN))

            elif t == "POUTRE_CONTINUE":
                def _tp(x):
                    x = str(x)
                    for a_, b_ in (("∅", "Ø"), ("≤", "<="), ("≥", ">="), ("σ", "sigma"), ("τ", "tau"), ("→", "->")):
                        x = x.replace(a_, b_)
                    return x
                c.append(Paragraph("POUTRE CONTINUE — Méthode forfaitaire / Caquot (BAEL 91)", sH))
                data = [["Paramètre", "Valeur"],
                    ["Portées", " ; ".join(f"{x:g} m" for x in el["portees"])],
                    ["Section retenue", f"{el['larg']} × {el['h']} cm  (d = {el['d']} cm)"],
                    ["Charges G / Q", f"{el['G']} / {el['Q']} kN/m  —  pu = {el['pu']} kN/m"],
                    ["Méthode des moments", el["methode"]],
                    ["As minimum", f"{el['As_min']} cm²"],
                ]
                c.append(tab(data, [7*cm, 10*cm]))
                c.append(Paragraph("Travées", sH))
                d2 = [["Travée", "Mt (kN.m)", "Armatures", "Vu (kN)", "tau (MPa)", "Cadres"]]
                for tv in el["travees"]:
                    d2.append([f"{tv['k']} ({tv['portee']:g} m)", str(tv["Mt"]), _tp(tv["disp"]), str(tv["Vu"]),
                               f"{tv['tau']} {'OK' if tv['cis_ok'] else 'NON OK'}", _tp(tv["cadres"])])
                c.append(tab(d2, [2.6*cm, 2.2*cm, 4.2*cm, 2*cm, 3*cm, 3*cm]))
                c.append(Paragraph("Appuis (chapeaux)", sH))
                d3 = [["Appui", "Mu (kN.m)", "Armatures", "ls (cm)", "Prolong. (cm)"]]
                for a_ in el["appuis"]:
                    d3.append([str(a_["appui"]), str(a_["Mu"]), _tp(a_["disp"]), str(a_["ls_cm"] or "—"), str(a_["prolong_cm"])])
                c.append(tab(d3, [2*cm, 3*cm, 6*cm, 2.5*cm, 3.5*cm]))
                for av in el["avert"]:
                    c.append(Paragraph("Avertissement : " + _tp(av), sN))

            elif t == "POUTRE":
                c.append(Paragraph("POUTRE — Cas isostatique, Pivot B (BAEL 91)", sH))
                data = [["Paramètre", "Valeur"],
                    ["Portée", f"{el['portee']} m"],
                    ["Section retenue", f"{el['larg']} × {el['h']} cm"],
                    ["Hauteur utile d", f"{el['d']} cm"],
                    ["Charge ELU pu", f"{el['pu']} kN/m"],
                    ["Moment travée Mt", f"{el['Mt']} kN.m"],
                    ["Effort tranchant Vu", f"{el['Vu']} kN"],
                    ["As longitudinaux", f"As={el['As']} cm²  —  {el['disp']}"],
                    ["Cadres transversaux", el['cadres']],
                    ["Vérif cisaillement", f"τu={el['tau']} / τlim={el['tau_lim']} MPa  —  {'CONFORME' if el['cis_ok'] else 'NON CONFORME'}"],
                ]
                c.append(tab(data, [7*cm, 10*cm]))

            elif t in ("POTEAU", "POTEAU RECT"):
                titre = "POTEAU RECTANGULAIRE" if el.get("rect") else "POTEAU CARRÉ"
                c.append(Paragraph(f"{titre} — Compression centrée (BAEL 91)", sH))
                sect = f"{el['b_cm']}×{el['h_cm']} cm" if el.get("rect") else f"{el['cote']}×{el['cote']} cm"
                data = [["Paramètre", "Valeur"],
                    ["Section retenue", sect],
                    ["Hauteur libre / lf", f"{el['h_libre']} m  —  lf={el['lf']} m"],
                    ["Élancement λ", f"{el['lam']}  (limite 50)  —  {'OK' if el['lam']<=50 else 'DÉPASSE'}"],
                    ["Effort ELU Nu", f"{el['Nu']} kN"],
                    ["As calculé", f"{el['As']} cm²  —  {el['disp']}"],
                    ["As minimum", f"{el['As_min']} cm²"],
                    ["Cadres", el['cadres']],
                    ["Nulim", f"{el['Nulim']} kN  —  {'CONFORME' if el['elu_ok'] else 'NON CONFORME'}"],
                    ["Vérif ELS béton", f"σbc={el['sbc']} / {el['sbc_lim']} MPa  —  {'CONFORME' if el['els_ok'] else 'NON CONFORME'}"],
                ]
                c.append(tab(data, [7*cm, 10*cm]))

            elif t == "FONDATION":
                c.append(Paragraph("FONDATION SUPERFICIELLE — Méthode des bielles (BAEL 91)", sH))
                data = [["Paramètre", "Valeur"],
                    ["Semelle retenue", f"{el['cote']}×{el['cote']}×{el['h']} cm"],
                    ["Hauteur utile d", f"{el['d']} cm"],
                    ["Effort ELU Nu", f"{el['Nu']} kN"],
                    ["Effort ELS Nser", f"{el['Nser']} kN"],
                    ["Contrainte de calcul qu", f"{el['qu']} kPa"],
                    ["As par lit", f"As={el['Ast']} cm²/ml  —  {el['disp']}"],
                    ["Disposition", el['nappes']],
                    ["Vérif contrainte sol", f"q_eff={el['q_eff']} / qu={el['qu']} kPa  —  {'CONFORME' if el['sol_ok'] else 'NON CONFORME'}"],
                ]
                c.append(tab(data, [7*cm, 10*cm]))

            c.append(Spacer(1, 0.3*cm))

        c.append(HRFlowable(width="100%", thickness=1, color=BLEU))
        c.append(Spacer(1, 0.2*cm))
        c.append(Paragraph(
            "Outil de pré-dimensionnement BAEL 91. Validation par ingénieur structure agréé requise avant exécution.",
            ParagraphStyle("av", fontSize=7.5, textColor=colors.grey, fontName="Helvetica-Oblique")
        ))
        c.append(Paragraph(
            f"GÉNIE CIVIL PRO — DALOKO — +237 681 605 462 — Mbouda — {datetime.now().strftime('%d/%m/%Y')}",
            ParagraphStyle("f", fontSize=8, fontName="Helvetica-Bold", textColor=BLEU, alignment=1)
        ))
        doc.build(c)
        return tmp.name
    except Exception as e:
        st.error(f"Erreur PDF : {e}")
        return None


def pdf_bytes(elements, nom, beton, acier):
    """Génère le PDF et le renvoie sous forme d'octets (pour download_button)."""
    chemin = generer_pdf(elements, nom, beton, acier)
    if not chemin:
        return None
    try:
        with open(chemin, "rb") as f:
            data = f.read()
    finally:
        try:
            os.remove(chemin)
        except OSError:
            pass
    return data


# ══════════════════════════════════════════════════════════════
# CONFIGURATION STREAMLIT
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Génie Civil Pro",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── SESSION STATE ──
if "resultats"  not in st.session_state: st.session_state.resultats  = []
if "charges"    not in st.session_state: st.session_state.charges    = {"G": 0.0, "Q": 0.0}
if "projet_nom" not in st.session_state: st.session_state.projet_nom = "Mon Projet"
if "last"       not in st.session_state: st.session_state.last       = {}
if "theme"      not in st.session_state: st.session_state.theme      = list(THEMES.keys())[0]


def nom_projet():
    return (st.session_state.projet_nom or "").strip()


def projet_valide():
    """Vérifie le champ obligatoire 'Nom du projet'."""
    if not nom_projet():
        st.error("⚠️ Le **nom du projet** (barre latérale) est obligatoire avant de lancer un calcul.")
        return False
    return True


def legende_requis():
    st.markdown(
        "<div class='legende-requis'>Les champs marqués d'une <b style='color:#D32F2F'>*</b> "
        "sont <b>obligatoires</b>. Les autres sont facultatifs.</div>",
        unsafe_allow_html=True,
    )


def entete(titre, description):
    st.title(titre)
    st.caption(description)
    legende_requis()


def bouton_pdf(cle, elements, beton, acier, label="📥 Télécharger la note de calcul (PDF)"):
    """Bouton de téléchargement PDF direct (présent dans chaque onglet)."""
    data = pdf_bytes(elements, nom_projet() or "Mon Projet", beton, acier)
    if data:
        st.download_button(
            label=label,
            data=data,
            file_name=f"note_calcul_{cle}_{(nom_projet() or 'projet').replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key=f"dl_{cle}",
        )
    else:
        st.warning("Le PDF n'a pas pu être généré. Vérifiez que reportlab est installé : pip install reportlab")


def placeholder_resultat():
    st.info("👈 Renseignez les paramètres puis cliquez sur le bouton de calcul pour afficher les résultats.")


def _opt0(x):
    """0 saisi par l'utilisateur = donnée non fournie."""
    return None if not x else x


def resultat_cc(hourdis, entraxe, typ, b0, portees, G, Q, beton, acier, G_j=None, methode="auto",
                solidaire=True, inertie_cte=True, fiss_ok=True, Mrd_fab=None, As_pref=None, d_pref=None, precont=False):
    """Calcule un plancher à corps creux (poutrelle isostatique ou continue) et renvoie un dictionnaire
    prêt pour l'affichage, la mémoire de session et le PDF."""
    fc28, fe_ = BETONS[beton], ACIERS[acier]
    out = {"type": "CORPS_CREUX", "hourdis": hourdis, "entraxe": entraxe, "type_poutrelle": typ, "b0": b0,
           "portees": list(portees), "G": G, "Q": Q, "beton": beton, "acier": acier,
           "chapeaux": [], "avert": [], "conditions": {}, "methode": "isostatique"}
    if len(portees) == 1:
        r = ccm.calc_corps_creux(hourdis, entraxe, portees[0], G, Q, fc28, fe_, typ, b0,
                                 As_prefab=As_pref, G_j=G_j, Mrd_fabricant=Mrd_fab, d_prefab=d_pref,
                                 precontrainte=precont)
        r["travee"] = 1
        out["travees"] = [r]
    else:
        c = ccm.calc_poutrelle_continue(hourdis, entraxe, list(portees), G, Q, fc28, fe_, typ, b0, methode=methode,
                                        G_j=G_j, As_prefab=As_pref, inertie_constante=inertie_cte,
                                        fissuration_peu_prejudiciable=fiss_ok, Mrd_fabricant=Mrd_fab,
                                        d_prefab=d_pref, precontrainte=precont, appui_rive_solidaire=solidaire)
        out.update({"methode": c["methode"], "travees": c["travees"], "chapeaux": c["chapeaux"],
                    "conditions": c["conditions_forfaitaire"], "avert": list(c["avertissements_chapeaux"])})
    if typ == "prefabriquee":
        out["avert"].append("Poutrelles préfabriquées : phase provisoire (avant coulage de la table), connexion et "
                            "précontrainte NON calculées — se référer à la fiche technique du fabricant.")
    return out


def affiche_resultat_cc(r):
    """Affichage Streamlit d'un résultat de plancher à corps creux."""
    tr = r["travees"]
    h_tot = tr[0]["h"]
    invalide = [t for t in tr if t.get("flexion_valide") is False]
    if invalide:
        st.error("❌ " + str(invalide[0].get("statut", "Section insuffisante : augmenter la hauteur de l'hourdis ou b0.")))
    else:
        st.success(f"✅ Plancher {r['hourdis']} — hauteur totale **{h_tot} cm**, entraxe **{r['entraxe']:g} cm**")
    c1, c2, c3 = st.columns(3)
    c1.metric("Hauteur totale", f"{h_tot} cm")
    c2.metric("Poutrelle", "Coulée sur place" if r["type_poutrelle"] == "sur_place" else "Préfabriquée")
    c3.metric("Méthode", r["methode"])
    if r["conditions"]:
        with st.expander("📋 Conditions de la méthode forfaitaire", expanded=False):
            for k, v in r["conditions"].items():
                st.write(("✓ " if v else "✗ ") + k)
    for t in tr:
        with st.expander(f"📐 Travée {t['travee']} — portée {r['portees'][t['travee'] - 1]:g} m", expanded=(len(tr) == 1)):
            st.write(f"**Moments ELU** : Mt = {t['Mt']} kN.m · Ma = {t['Ma']} kN.m · M0 = {t['M0']} kN.m")
            st.write(f"**Largeur de table** b = {t['b']} cm · **Section** : {t['mode']}")
            if t.get("disp_travee"):
                st.write(f"**Armatures en travée** : {t['disp_travee']}  (As calculé = {t['As_calc']} cm², As min = {t['As_min']} cm²)")
            if t.get("prefab_ok") is not None:
                st.write(f"**Poutrelle préfabriquée** : Mrd = {t.get('Mrd')} kN.m — "
                         + ("✓ suffisant" if t["prefab_ok"] else "✗ insuffisant"))
            st.write(f"**Cisaillement** : τu = {t['tau']} MPa (limite {t['tau_lim']}) — "
                     + ("✓ OK" if t["cis_ok"] else "✗ NON OK"))
            if "sigma_bc" in t:
                st.write(f"**ELS béton** : σbc = {t['sigma_bc']} MPa (limite {t['sigma_lim']}) — "
                         + ("✓ OK" if t["els_ok"] else "✗ NON OK"))
            if "fleche" in t:
                f = t["fleche"]
                disp = "dispense possible" if t.get("fleche_dispense_possible") else "calcul de flèche nécessaire"
                st.write(f"**Flèche nuisible** Δf = {f['delta_f']} mm (limite {f['limite']} mm) — "
                         + ("✓ OK" if f["ok"] else "✗ NON OK") + f"  · {disp}")
            tz = t.get("treillis")
            if tz:
                st.write(f"**Treillis soudé de la table** : {tz['choix_perp']} (perpendiculaire) · {tz['choix_par']} (parallèle)")
            for a in t.get("alertes", []):
                st.warning(a)
    if r["chapeaux"]:
        with st.expander("🔝 Chapeaux sur appuis", expanded=False):
            for c in r["chapeaux"]:
                st.write(f"**Appui {c['appui']}** — {c['type']}")
                st.write(f"Mu = {c['Mu']} kN.m → **{c['barres']}** (As = {c['As_req']} cm²) · "
                         f"ancrage ls = {c['ancrage_ls_cm']} cm · prolongement depuis le nu = {c['prolongement_depuis_nu_cm']} cm")
                if c.get("prolongement_convention"):
                    st.caption(c["prolongement_convention"])
            st.caption(c["note_ancrage"])
    for a in r["avert"]:
        st.warning(a)
    st.caption("Outil de pré-dimensionnement : phase provisoire des poutrelles préfabriquées et poutrelles précontraintes "
               "non calculées. Vérification par un ingénieur structure requise avant exécution.")


def affiche_poutre_continue(r):
    """Affichage Streamlit d'une poutre continue."""
    ok = all(t["cis_ok"] for t in r["travees"])
    (st.success if ok else st.error)(
        f"{'✅' if ok else '❌'} Poutre continue {len(r['portees'])} travées — section **{r['larg']} × {r['h']} cm** "
        f"· méthode **{r['methode']}**")
    c1, c2, c3 = st.columns(3)
    c1.metric("Section", f"{r['larg']}×{r['h']} cm")
    c2.metric("pu ELU", f"{r['pu']} kN/m")
    c3.metric("As min", f"{r['As_min']} cm²")
    with st.expander("📋 Conditions de la méthode forfaitaire", expanded=False):
        for k, v in r["conditions"].items():
            st.write(("✓ " if v else "✗ ") + k)
    for t in r["travees"]:
        with st.expander(f"📐 Travée {t['k']} — portée {t['portee']:g} m", expanded=False):
            st.write(f"**Mt** = {t['Mt']} kN.m → **{t['disp']}** (As = {t['As']} cm²)")
            st.write(f"**Effort tranchant** Vu = {t['Vu']} kN · τu = {t['tau']} MPa (limite {r['tau_lim']}) — "
                     + ("✓ OK" if t["cis_ok"] else "✗ NON OK"))
            st.write(f"**Cadres** : {t['cadres']}")
    with st.expander("🔝 Appuis (chapeaux)", expanded=False):
        for a in r["appuis"]:
            ls = f" · ancrage ls = {a['ls_cm']} cm" if a["ls_cm"] else ""
            st.write(f"**Appui {a['appui']}** ({a['nature']}) — Mu = {a['Mu']} kN.m → **{a['disp']}** "
                     f"(As = {a['As']} cm²){ls} · prolongement depuis le nu = {a['prolong_cm']} cm")
        st.caption("Prolongement de rive : L/4 par convention ; appuis intermédiaires : annexe E.1.3 (L/4 voisin de rive, L/5 sinon).")
    for a in r["avert"]:
        st.warning(a)


def bloc_cumul(prefixe):
    """Saisie des charges cumulées G et Q (kN) : directe ou calculée automatiquement depuis G et Q de plancher."""
    mode = st.radio("Mode de saisie des charges" + REQ,
                    ["Saisie directe (G et Q cumulés)", "Calcul automatique depuis G et Q de plancher"],
                    key=f"mode_{prefixe}")
    if mode.startswith("Saisie"):
        G = st.number_input("G cumulé (kN)" + REQ, 0.0, 5000.0, 180.0, 5.0, key=f"Gc_{prefixe}")
        Q = st.number_input("Q cumulé (kN)" + REQ, 0.0, 3000.0, 45.0, 5.0, key=f"Qc_{prefixe}")
        return G, Q
    g_def = float(st.session_state.charges["G"]) if st.session_state.charges["G"] > 0 else 5.5
    q_def = float(st.session_state.charges["Q"]) if st.session_state.charges["Q"] > 0 else 2.0
    g_pl = st.number_input("G de plancher (kN/m²)" + REQ, 0.5, 30.0, g_def, 0.1, key=f"Gp_{prefixe}")
    q_pl = st.number_input("Q de plancher (kN/m²)" + REQ, 0.5, 10.0, q_def, 0.1, key=f"Qp_{prefixe}")
    surf = st.number_input("Surface reprise par niveau (m²)" + REQ, 1.0, 200.0, 20.0, 0.5, key=f"S_{prefixe}",
                           help="Surface de plancher reprise par ce poteau à chaque niveau (surface d'influence).")
    niv = st.number_input("Nombre de niveaux repris" + REQ, 1, 15, 3, key=f"N_{prefixe}")
    maj = st.number_input("Majoration poids propre poutres/poteaux (%)" + OPT, 0, 50, 0, key=f"M_{prefixe}")
    G = round(g_pl * surf * niv * (1 + maj / 100), 1)
    Q = round(q_pl * surf * niv, 1)
    st.info(f"G cumulé = **{G} kN** · Q cumulé = **{Q} kN**  \n"
            "Q cumulé sans dégression des charges d'exploitation (hypothèse prudente).")
    return G, Q


# ── SIDEBAR ──
with st.sidebar:
    st.markdown("## 🏗️ Génie Civil Pro")
    st.markdown("**BAEL 91 — Mbouda, Cameroun**")
    st.markdown("---")

    st.selectbox("🎨 **Thème de l'application**", list(THEMES.keys()), key="theme")

    st.text_input(
        "📁 **Nom du projet** :red[*]", key="projet_nom",
        help="Obligatoire : utilisé dans tous les PDF téléchargés.",
    )
    st.markdown("---")
    page = st.radio("**Navigation**", [
        "⚖️  Calcul G et Q",
        "📐  Dalle",
        "🧱  Plancher corps creux",
        "🔩  Poutre",
        "🏛️  Poteau",
        "🏗️  Fondation",
        "📋  Projet Complet",
        "📄  Note de Calcul PDF",
    ])
    st.markdown("---")
    st.caption(f"📅 {datetime.now().strftime('%d/%m/%Y')}")
    st.caption("DALOKO · +237 681 605 462")
    st.caption("Mbouda · Région de l'Ouest")
    st.caption(f"💾 {len(st.session_state.resultats)} calcul(s) en mémoire")

# Application du thème choisi
st.markdown(CSS_TEMPLATE.substitute(THEMES[st.session_state.theme]), unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# PAGE 1 — CALCUL G ET Q
# ════════════════════════════════════════════════════════════
if page == "⚖️  Calcul G et Q":
    entete("⚖️ Calcul des Charges G et Q",
           "Calculez automatiquement les charges permanentes G et d'exploitation Q selon BAEL 91.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📦 Charges permanentes G (kN/m²)")
        composants = []

        type_plancher = st.selectbox("Type de plancher" + REQ, ["Corps creux", "Dalle pleine béton armé"])
        if type_plancher == "Corps creux":
            cc = st.selectbox("Type corps creux" + REQ, list(CORPS_CREUX.keys()), index=2)
            composants.append({"nom": f"Corps creux {cc}", "G": CORPS_CREUX[cc]})
        else:
            ep = st.number_input("Épaisseur dalle (cm)" + REQ, 10, 30, 14)
            composants.append({"nom": f"Dalle BA {ep}cm", "G": round(25.0 * ep / 100, 3)})

        ep_chape = st.number_input("Chape mortier (cm)" + OPT, 0, 10, 4)
        if ep_chape > 0:
            composants.append({"nom": f"Chape mortier {ep_chape}cm", "G": round(20.0 * ep_chape / 100, 3)})

        ep_carr = st.number_input("Carrelage (cm)" + OPT, 0, 5, 2)
        if ep_carr > 0:
            composants.append({"nom": f"Carrelage {ep_carr}cm", "G": round(20.0 * ep_carr / 100, 3)})

        type_cl = st.selectbox("Cloisons" + OPT, ["Légères (0.75)", "Parpaing 10cm (1.20)", "Parpaing 15cm (1.60)", "Brique 10cm (1.40)", "Aucune (0)"])
        G_cl = {"Légères (0.75)": 0.75, "Parpaing 10cm (1.20)": 1.20, "Parpaing 15cm (1.60)": 1.60, "Brique 10cm (1.40)": 1.40, "Aucune (0)": 0.0}[type_cl]
        if G_cl > 0:
            composants.append({"nom": f"Cloisons {type_cl}", "G": G_cl})

        ep_end = st.number_input("Enduit plafond (cm)" + OPT, 0.0, 5.0, 1.5)
        if ep_end > 0:
            composants.append({"nom": f"Enduit plafond {ep_end}cm", "G": round(18.0 * ep_end / 100, 3)})

        fp = st.selectbox("Faux-plafond" + OPT, ["Enduit (0.20)", "Plâtre (0.15)", "Bois (0.10)", "Aucun (0)"])
        G_fp = {"Enduit (0.20)": 0.20, "Plâtre (0.15)": 0.15, "Bois (0.10)": 0.10, "Aucun (0)": 0.0}[fp]
        if G_fp > 0:
            composants.append({"nom": f"Faux-plafond {fp}", "G": G_fp})

        toiture = st.checkbox("Ajouter toiture bois + tôle ?" + OPT)
        if toiture:
            type_ch = st.selectbox("Charpente bois" + REQ, ["Légère (0.15)", "Standard (0.25)", "Lourde (0.40)"])
            G_ch = {"Légère (0.15)": 0.15, "Standard (0.25)": 0.25, "Lourde (0.40)": 0.40}[type_ch]
            composants.append({"nom": f"Charpente bois {type_ch}", "G": G_ch})
            ep_tole = st.number_input("Épaisseur tôle (mm)" + REQ, 0.4, 1.5, 0.63, step=0.01)
            composants.append({"nom": f"Tôle galvanisée {ep_tole}mm", "G": round(77.0 * ep_tole / 1000, 3)})

        G_total = round(sum(c["G"] for c in composants), 3)
        st.subheader("🏃 Charge d'exploitation Q (kN/m²)")
        usage = st.selectbox("Usage du bâtiment" + REQ, list(CHARGES_Q.keys()))
        Q_val = CHARGES_Q[usage]
        st.info(f"Q = **{Q_val} kN/m²** ({usage})")

    with col2:
        st.subheader("📊 Résultats")
        if composants:
            for comp in composants:
                c_a, c_b = st.columns([3, 1])
                c_a.write(f"• {comp['nom']}")
                c_b.write(f"**{comp['G']}**")
            st.markdown("---")
        c1, c2 = st.columns(2)
        c1.metric("G total (kN/m²)", G_total)
        c2.metric("Q (kN/m²)", Q_val)
        pu_gq = round(1.35 * G_total + 1.5 * Q_val, 3)
        pser_gq = round(G_total + Q_val, 3)
        st.metric("pu ELU = 1.35G + 1.5Q  (kN/m²)", pu_gq)
        st.metric("pser ELS = G + Q  (kN/m²)", pser_gq)

        if st.button("✅ Utiliser ces valeurs dans les calculs"):
            st.session_state.charges = {"G": G_total, "Q": Q_val}
            st.toast("Charges enregistrées", icon="✅")
            st.success(f"✅ G = {G_total} kN/m² et Q = {Q_val} kN/m² enregistrés !")

        st.markdown("---")
        el_charges = {
            "type": "CHARGES", "composants": composants, "usage": usage,
            "G": G_total, "Q": Q_val, "pu": pu_gq, "pser": pser_gq,
        }
        bouton_pdf("charges", [el_charges], "—", "—")


# ════════════════════════════════════════════════════════════
# PAGE 2 — DALLE
# ════════════════════════════════════════════════════════════
elif page == "📐  Dalle":
    entete("📐 Calcul de Dalle — BAEL 91 (Pivot A)",
           "Dimensionnement d'une dalle pleine sur appuis par la méthode Rankine-Grashoff.")
    col1, col2 = st.columns([1, 1.3])

    with col1:
        st.subheader("Paramètres")
        lx    = st.number_input("Petite portée lx (m)" + REQ, 1.0, 15.0, 4.2, 0.1)
        ly    = st.number_input("Grande portée ly (m)" + REQ, lx, 20.0, 5.1, 0.1)
        G_d   = st.number_input("G (kN/m²)" + REQ, 0.5, 30.0,
                    float(st.session_state.charges["G"]) if st.session_state.charges["G"] > 0 else 5.5, 0.1)
        Q_d   = st.number_input("Q (kN/m²)" + REQ, 0.5, 10.0,
                    float(st.session_state.charges["Q"]) if st.session_state.charges["Q"] > 0 else 2.0, 0.1)
        beton = st.selectbox("Béton" + REQ, list(BETONS.keys()), index=1, key="b_d")
        acier = st.selectbox("Acier" + REQ, list(ACIERS.keys()), index=1, key="a_d")
        calc  = st.button("⚙️ CALCULER LA DALLE")

    with col2:
        st.subheader("Résultats")
        if calc and projet_valide():
            r = calc_dalle(lx, ly, G_d, Q_d, beton, acier)
            r["type"] = "DALLE"
            st.session_state.resultats.append(r)
            st.session_state.last["dalle"] = r
            st.toast("Dalle calculée", icon="✅")

        r = st.session_state.last.get("dalle")
        if r:
            st.success(f"✅ Dalle dimensionnée — épaisseur = **{r['h']} cm**")
            c1, c2, c3 = st.columns(3)
            c1.metric("Épaisseur", f"{r['h']} cm")
            c2.metric("Hauteur utile d", f"{r['d']} cm")
            c3.metric("pu ELU", f"{r['pu']} kN/m²")

            with st.expander("📐 Moments fléchissants (ELU)", expanded=True):
                st.write(f"**Mtx** (travée x) = {r['Mtx']} kN.m/ml → {r['disp_tx']}")
                st.write(f"**Mty** (travée y) = {r['Mty']} kN.m/ml → {r['disp_ty']}")
                st.write(f"**Max** (appui x)  = {r['Max']} kN.m/ml → {r['disp_ax']}")
                st.write(f"**May** (appui y)  → {r['disp_ay']}")

            with st.expander("✅ Vérification ELS", expanded=True):
                st.write(f"σbc = {r['sbc']} MPa  /  limite = {r['sbc_lim']} MPa")
                if r['els_ok']:
                    st.success("✓ État limite de service SATISFAIT")
                else:
                    st.error("✗ État limite de service NON SATISFAIT")

            st.caption("💾 Résultat sauvegardé pour la note de calcul globale")
            bouton_pdf("dalle", [r], r["beton"], r["acier"])
        else:
            placeholder_resultat()


# ════════════════════════════════════════════════════════════
# PAGE — PLANCHER À CORPS CREUX
# ════════════════════════════════════════════════════════════
elif page == "🧱  Plancher corps creux":
    entete("🧱 Plancher à corps creux — Poutrelles + hourdis (BAEL 91)",
           "Poutrelles isostatiques ou continues (méthode forfaitaire / Caquot), choix de l'hourdis, de l'entraxe et du type de poutrelle.")
    if not CC_OK:
        st.error("Le fichier **corps_creux.py** est introuvable : placez-le dans le même dossier que l'application.")
        st.stop()
    col1, col2 = st.columns([1, 1.3])

    with col1:
        st.subheader("Paramètres")
        hourdis = st.selectbox("Hourdis (corps creux + table)" + REQ, list(ccm.HOURDIS.keys()), index=2,
                               help="Exemple 16+4 : corps creux de 16 cm + dalle de compression de 4 cm.")
        entraxe = st.number_input("Entraxe des poutrelles (cm)" + REQ, 25.0, 79.0, 60.0, 1.0)
        typ_lbl = st.radio("Type de poutrelle" + REQ, ["Coulée sur place", "Préfabriquée"])
        typ = "sur_place" if typ_lbl.startswith("Coulée") else "prefabriquee"
        b0 = st.number_input("Largeur de l'âme b0 (cm)" + REQ, 8.0, 30.0, 10.0, 1.0)
        n_tr = st.selectbox("Nombre de travées" + REQ, [1, 2, 3, 4, 5, 6], index=0)
        portees = [st.number_input(f"Portée travée {i + 1} (m)" + REQ, 1.0, 12.0, 3.5, 0.1, key=f"ptr_{i}")
                   for i in range(n_tr)]
        G_c = st.number_input("G (kN/m²)" + REQ, 0.5, 30.0,
                              float(st.session_state.charges["G"]) if st.session_state.charges["G"] > 0 else 5.5, 0.1, key="G_cc")
        Q_c = st.number_input("Q (kN/m²)" + REQ, 0.5, 10.0,
                              float(st.session_state.charges["Q"]) if st.session_state.charges["Q"] > 0 else 1.5, 0.1, key="Q_cc")
        G_j = st.number_input("G avant pose des cloisons/revêtements (kN/m²)" + OPT, 0.0, 30.0, 0.0, 0.1,
                              help="Pour la flèche. Laissé à 0 : hypothèse prudente.")
        beton = st.selectbox("Béton" + REQ, list(BETONS.keys()), index=1, key="b_cc")
        acier = st.selectbox("Acier" + REQ, list(ACIERS.keys()), index=1, key="a_cc")

        methode, solidaire, inertie_cte, fiss_ok = "auto", True, True, True
        if n_tr > 1:
            with st.expander("⚙️ Poutrelle continue — options", expanded=False):
                methode = st.selectbox("Méthode de calcul des moments",
                                       ["auto", "forfaitaire", "caquot_minoree", "caquot"],
                                       help="auto : forfaitaire si toutes ses conditions sont remplies, sinon Caquot (minorée si Q <= max(2G ; 5)).")
                inertie_cte = st.checkbox("Inertie constante dans toutes les travées", True)
                fiss_ok = st.checkbox("Fissuration peu préjudiciable", True)
                solidaire = st.checkbox("Poutrelle solidaire de son appui de rive (poteau ou poutre)", True,
                                        help="Coché : chapeau de rive dimensionné pour 0,15 M0 (encastrement partiel).")
        Mrd_fab = As_pref = d_pref = None
        precont = False
        if typ == "prefabriquee":
            st.warning("Poutrelle préfabriquée : fournissez la donnée du fabricant (moment résistant OU section d'acier).")
            Mrd_fab = _opt0(st.number_input("Moment résistant fabricant Mrd (kN.m)" + OPT, 0.0, 200.0, 0.0, 0.1))
            As_pref = _opt0(st.number_input("Section d'acier de la poutrelle (cm²)" + OPT, 0.0, 30.0, 0.0, 0.05))
            d_pref = _opt0(st.number_input("Hauteur utile d de la poutrelle (cm)" + OPT, 0.0, 60.0, 0.0, 0.5))
            precont = st.checkbox("Poutrelle précontrainte (non calculée par l'outil)", False)
        calc = st.button("⚙️ CALCULER LE PLANCHER")

    with col2:
        st.subheader("Résultats")
        if calc and projet_valide():
            try:
                r = resultat_cc(hourdis, entraxe, typ, b0, portees, G_c, Q_c, beton, acier, _opt0(G_j), methode,
                                solidaire, inertie_cte, fiss_ok, Mrd_fab, As_pref, d_pref, precont)
                st.session_state.resultats.append(r)
                st.session_state.last["corps_creux"] = r
                st.toast("Plancher calculé", icon="✅")
            except ValueError as e:
                st.session_state.last.pop("corps_creux", None)
                st.error(f"⚠️ {e}")

        r = st.session_state.last.get("corps_creux")
        if r:
            affiche_resultat_cc(r)
            st.caption("💾 Résultat sauvegardé pour la note de calcul globale")
            bouton_pdf("corps_creux", [r], r["beton"], r["acier"])
        else:
            placeholder_resultat()


# ════════════════════════════════════════════════════════════
# PAGE 3 — POUTRE
# ════════════════════════════════════════════════════════════
elif page == "🔩  Poutre":
    entete("🔩 Calcul de Poutre — BAEL 91 (Pivot B)",
           "Poutre isostatique ou continue (2 à 6 travées, méthode forfaitaire / Caquot) sous charge uniformément répartie.")
    col1, col2 = st.columns([1, 1.3])

    with col1:
        st.subheader("Paramètres")
        mode_p = st.radio("Type de poutre" + REQ, ["Isostatique (1 travée)", "Continue (2 à 6 travées)"], key="mode_poutre")
        continue_ = mode_p.startswith("Continue")
        if continue_:
            n_pc = st.selectbox("Nombre de travées" + REQ, [2, 3, 4, 5, 6], key="n_pc")
            portees_pc = [st.number_input(f"Portée travée {i + 1} (m)" + REQ, 1.0, 20.0, 5.0, 0.1, key=f"pc_{i}")
                          for i in range(n_pc)]
            portee = None
        else:
            portee = st.number_input("Portée (m)" + REQ, 1.0, 20.0, 5.0, 0.1)
        G_ml   = st.number_input("G réparti (kN/m)" + REQ, 0.0, 200.0, 22.0, 0.5)
        Q_ml   = st.number_input("Q réparti (kN/m)" + REQ, 0.0, 100.0, 8.0, 0.5)
        larg   = st.number_input("Largeur imposée b (cm)" + REQ, 15, 60, 20)
        beton  = st.selectbox("Béton" + REQ, list(BETONS.keys()), index=1, key="b_p")
        acier  = st.selectbox("Acier" + REQ, list(ACIERS.keys()), index=1, key="a_p")
        methode_pc, fiss_pc, solid_pc = "auto", True, True
        if continue_:
            with st.expander("⚙️ Poutre continue — options", expanded=False):
                methode_pc = st.selectbox("Méthode de calcul des moments",
                                          ["auto", "forfaitaire", "caquot_minoree", "caquot"], key="m_pc",
                                          help="auto : forfaitaire si ses conditions sont remplies, sinon Caquot (minorée si Q <= 2G).")
                fiss_pc = st.checkbox("Fissuration peu préjudiciable", True, key="f_pc")
                solid_pc = st.checkbox("Poutre solidaire de ses appuis de rive (poteaux)", True, key="s_pc",
                                       help="Coché : chapeau de rive dimensionné pour 0,15 M0.")
        calc   = st.button("⚙️ CALCULER LA POUTRE")

    with col2:
        st.subheader("Résultats")
        if calc and projet_valide():
            if continue_:
                try:
                    r = calc_poutre_continue(portees_pc, G_ml, Q_ml, larg, beton, acier, methode_pc, fiss_pc, solid_pc)
                    st.session_state.resultats.append(r)
                    st.session_state.last["poutre_continue"] = r
                    st.session_state.last["poutre_mode"] = "continue"
                    st.toast("Poutre continue calculée", icon="✅")
                except ValueError as e:
                    st.session_state.last.pop("poutre_continue", None)
                    st.error(f"⚠️ {e}")
            else:
                r = calc_poutre(portee, G_ml, Q_ml, larg, beton, acier)
                r["type"] = "POUTRE"
                st.session_state.resultats.append(r)
                st.session_state.last["poutre"] = r
                st.session_state.last["poutre_mode"] = "iso"
                st.toast("Poutre calculée", icon="✅")

        if continue_:
            r = st.session_state.last.get("poutre_continue")
            if r:
                affiche_poutre_continue(r)
                st.caption("💾 Résultat sauvegardé pour la note de calcul globale")
                bouton_pdf("poutre_continue", [r], r["beton"], r["acier"])
            else:
                placeholder_resultat()
        else:
            r = st.session_state.last.get("poutre")
            if r:
                st.success(f"✅ Section retenue : **{r['larg']} × {r['h']} cm**")
                c1, c2, c3 = st.columns(3)
                c1.metric("Section", f"{r['larg']}×{r['h']} cm")
                c2.metric("Moment Mt", f"{r['Mt']} kN.m")
                c3.metric("Effort Vu", f"{r['Vu']} kN")
                st.write(f"**Ferraillage longitudinal** : {r['disp']}  (As = {r['As']} cm²)")
                st.write(f"**Cadres transversaux** : {r['cadres']}")
                if r['cis_ok']:
                    st.success(f"✓ Cisaillement OK : τu = {r['tau']} ≤ τlim = {r['tau_lim']} MPa")
                else:
                    st.error(f"✗ Cisaillement NON OK : τu = {r['tau']} > τlim = {r['tau_lim']} MPa")
                st.caption("💾 Résultat sauvegardé pour la note de calcul globale")
                bouton_pdf("poutre", [r], r["beton"], r["acier"])
            else:
                placeholder_resultat()


# ════════════════════════════════════════════════════════════
# PAGE 4 — POTEAU
# ════════════════════════════════════════════════════════════
elif page == "🏛️  Poteau":
    entete("🏛️ Calcul de Poteau — BAEL 91",
           "Dimensionnement d'un poteau en compression centrée (section carrée ou rectangulaire).")
    col1, col2 = st.columns([1, 1.3])

    with col1:
        st.subheader("Paramètres")
        type_pot = st.radio("Type de section" + REQ, ["Carré (auto-dimensionné)", "Rectangulaire (imposé)"])
        b_cm = h_cm_p = None
        if "Rectangulaire" in type_pot:
            b_cm   = st.number_input("b (petite dimension, cm)" + REQ, 15, 100, 20)
            h_cm_p = st.number_input("h (grande dimension, cm)" + REQ, b_cm, 150, 30)
        h_libre = st.number_input("Hauteur libre (m)" + REQ, 2.0, 10.0, 3.2, 0.1)
        G_pot, Q_pot = bloc_cumul("pot")
        beton   = st.selectbox("Béton" + REQ, list(BETONS.keys()), index=1, key="b_po")
        acier   = st.selectbox("Acier" + REQ, list(ACIERS.keys()), index=1, key="a_po")
        calc    = st.button("⚙️ CALCULER LE POTEAU")

    with col2:
        st.subheader("Résultats")
        if calc and projet_valide():
            r = calc_poteau(h_libre, G_pot, Q_pot, beton, acier, b_cm, h_cm_p)
            r["type"] = "POTEAU RECT" if r.get("rect") else "POTEAU"
            st.session_state.resultats.append(r)
            st.session_state.last["poteau"] = r
            st.toast("Poteau calculé", icon="✅")

        r = st.session_state.last.get("poteau")
        if r:
            sect = f"{r['b_cm']}×{r['h_cm']} cm" if r.get("rect") else f"{r['cote']}×{r['cote']} cm"
            st.success(f"✅ Section retenue : **{sect}**")
            c1, c2, c3 = st.columns(3)
            c1.metric("Section", sect)
            c2.metric("Nu ELU", f"{r['Nu']} kN")
            c3.metric("Nulim", f"{r['Nulim']} kN")
            st.write(f"**Élancement λ** : {r['lam']}  {'✓ OK' if r['lam'] <= 50 else '✗ DÉPASSE 50'}")
            st.write(f"**Ferraillage** : {r['disp']}  (As = {r['As']} cm²)")
            st.write(f"**As minimum** : {r['As_min']} cm²")
            st.write(f"**Cadres** : {r['cadres']}")
            if r['elu_ok']:
                st.success(f"✓ ELU : Nu = {r['Nu']} ≤ Nulim = {r['Nulim']} kN")
            else:
                st.error(f"✗ ELU : Nu = {r['Nu']} > Nulim = {r['Nulim']} kN")
            if r['els_ok']:
                st.success(f"✓ ELS : σbc = {r['sbc']} ≤ {r['sbc_lim']} MPa")
            else:
                st.error(f"✗ ELS : σbc = {r['sbc']} > {r['sbc_lim']} MPa")
            st.caption("💾 Résultat sauvegardé pour la note de calcul globale")
            bouton_pdf("poteau", [r], r["beton"], r["acier"])
        else:
            placeholder_resultat()


# ════════════════════════════════════════════════════════════
# PAGE 5 — FONDATION
# ════════════════════════════════════════════════════════════
elif page == "🏗️  Fondation":
    entete("🏗️ Fondation Superficielle — Méthode des bielles (BAEL 91)",
           "Dimensionnement d'une semelle isolée sous poteau.")
    col1, col2 = st.columns([1, 1.3])

    with col1:
        st.subheader("Paramètres")
        G_f, Q_f = bloc_cumul("fond")
        cote_pot = st.number_input("Côté poteau (cm)" + REQ, 15, 100, 25)
        q_sol    = st.number_input("Contrainte sol (kPa)" + REQ, 50.0, 2000.0, 200.0, 10.0)
        type_sol = st.radio("Type contrainte sol" + REQ, ["admissible", "rupture"])
        st.caption("Admissible : valeur déjà divisée par coeff sécurité\nRupture : l'outil divise par 2 automatiquement")
        beton    = st.selectbox("Béton" + REQ, list(BETONS.keys()), index=1, key="b_f")
        acier    = st.selectbox("Acier" + REQ, list(ACIERS.keys()), index=1, key="a_f")
        calc     = st.button("⚙️ CALCULER LA FONDATION")

    with col2:
        st.subheader("Résultats")
        if calc and projet_valide():
            r = calc_fondation(G_f, Q_f, cote_pot, q_sol, beton, acier, type_sol)
            r["type"] = "FONDATION"
            st.session_state.resultats.append(r)
            st.session_state.last["fondation"] = r
            st.toast("Fondation calculée", icon="✅")

        r = st.session_state.last.get("fondation")
        if r:
            st.success(f"✅ Semelle : **{r['cote']}×{r['cote']}×{r['h']} cm**")
            c1, c2, c3 = st.columns(3)
            c1.metric("Semelle", f"{r['cote']}×{r['cote']} cm")
            c2.metric("Hauteur", f"{r['h']} cm")
            c3.metric("qu calcul", f"{r['qu']} kPa")
            st.write(f"**Ferraillage par lit** : {r['disp']}  (As = {r['Ast']} cm²/ml)")
            st.write(f"**Nappes** : {r['nappes']}")
            if r['sol_ok']:
                st.success(f"✓ Sol OK : q_eff = {r['q_eff']} ≤ qu = {r['qu']} kPa")
            else:
                st.error(f"✗ Sol NON OK : q_eff = {r['q_eff']} > qu = {r['qu']} kPa")
            st.caption("💾 Résultat sauvegardé pour la note de calcul globale")
            bouton_pdf("fondation", [r], r["beton"], r["acier"])
        else:
            placeholder_resultat()


# ════════════════════════════════════════════════════════════
# PAGE 6 — PROJET COMPLET
# ════════════════════════════════════════════════════════════
elif page == "📋  Projet Complet":
    entete("📋 Projet Complet — Calcul automatique",
           "Dimensionne d'un seul coup la dalle, la poutre, le poteau et la fondation.")
    st.info(f"📁 Projet : **{nom_projet() or '— à renseigner dans la barre latérale —'}**")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Paramètres généraux")
        n_niv   = st.number_input("Nombre de niveaux (RDC inclus)" + REQ, 1, 10, 3)
        lx_p    = st.number_input("Portée lx (m)" + REQ, 2.0, 15.0, 4.2, 0.1)
        ly_p    = st.number_input("Portée ly (m)" + REQ, lx_p, 20.0, 5.1, 0.1)
        h_niv   = st.number_input("Hauteur par niveau (m)" + REQ, 2.5, 5.0, 3.2, 0.1)
        poutre_p = st.radio("Poutre porteuse" + REQ, ["Isostatique (1 travée)", "Continue (travées identiques)"], key="pt_pr")
        n_pc_p = 1
        if poutre_p.startswith("Continue"):
            n_pc_p = st.selectbox("Nombre de travées de la poutre" + REQ, [2, 3, 4, 5, 6], key="npc_pr",
                                  help="Toutes les travées ont la portée de la poutre porteuse (ly en corps creux, lx en dalle pleine).")
        plancher_p = st.radio("Type de plancher" + REQ, ["Dalle pleine", "Corps creux (poutrelles)"])
        if plancher_p.startswith("Corps") and CC_OK:
            hourdis_p = st.selectbox("Hourdis" + REQ, list(ccm.HOURDIS.keys()), index=2, key="h_pr")
            entraxe_p = st.number_input("Entraxe des poutrelles (cm)" + REQ, 25.0, 79.0, 60.0, 1.0, key="e_pr")
            typ_p_lbl = st.radio("Type de poutrelle" + REQ, ["Coulée sur place", "Préfabriquée"], key="t_pr")
            if typ_p_lbl.startswith("Préf"):
                st.warning("Préfabriquée : fournissez la donnée du fabricant (obligatoire).")
                Mrd_pr = _opt0(st.number_input("Moment résistant fabricant Mrd (kN.m)" + REQ, 0.0, 200.0, 0.0, 0.1, key="mrd_pr"))
            else:
                Mrd_pr = None
        G_proj  = st.number_input("G plancher (kN/m²)" + REQ, 0.5, 30.0, 5.5, 0.1)
        Q_proj  = st.number_input("Q plancher (kN/m²)" + REQ, 0.5, 10.0, 2.0, 0.1)
        q_sol_p = st.number_input("Contrainte sol (kPa)" + REQ, 50.0, 2000.0, 200.0, 10.0)
        type_sol_p = st.radio("Type contrainte sol" + REQ, ["admissible", "rupture"])
        beton_p = st.selectbox("Béton" + REQ, list(BETONS.keys()), index=1, key="b_pr")
        acier_p = st.selectbox("Acier" + REQ, list(ACIERS.keys()), index=1, key="a_pr")
        type_pot_p = st.radio("Poteau" + REQ, ["Carré", "Rectangulaire"])
        b_p = h_p = None
        if type_pot_p == "Rectangulaire":
            b_p = st.number_input("b poteau (cm)" + REQ, 15, 100, 20)
            h_p = st.number_input("h poteau (cm)" + REQ, b_p, 150, 30)
        calc_p = st.button("⚙️ CALCULER TOUT LE PROJET")

    with col2:
        st.subheader("Résultats")
        if calc_p and projet_valide():
            S_trib = (lx_p / 2) * (ly_p / 2)
            G_pot_p = G_proj * S_trib * n_niv
            Q_pot_p = Q_proj * S_trib * n_niv

            cc_projet = plancher_p.startswith("Corps") and CC_OK
            erreur_cc = None
            if cc_projet:
                try:
                    # poutrelles portant dans la petite portée lx ; les poutres porteuses (portée ly) reprennent lx/2
                    rd = resultat_cc(hourdis_p, entraxe_p, "sur_place" if typ_p_lbl.startswith("Coul") else "prefabriquee",
                                     10.0, [lx_p], G_proj, Q_proj, beton_p, acier_p, Mrd_fab=Mrd_pr)
                    if n_pc_p > 1:
                        rp = calc_poutre_continue([ly_p] * n_pc_p, G_proj * lx_p / 2, Q_proj * lx_p / 2, 20, beton_p, acier_p)
                    else:
                        rp = calc_poutre(ly_p, G_proj * lx_p / 2, Q_proj * lx_p / 2, 20, beton_p, acier_p)
                except ValueError as e:
                    erreur_cc = str(e)
            else:
                rd  = calc_dalle(lx_p, ly_p, G_proj, Q_proj, beton_p, acier_p)
                if n_pc_p > 1:
                    try:
                        rp = calc_poutre_continue([lx_p] * n_pc_p, G_proj * ly_p / 2, Q_proj * ly_p / 2, 20, beton_p, acier_p)
                    except ValueError as e:
                        erreur_cc = str(e)
                else:
                    rp  = calc_poutre(lx_p, G_proj * ly_p / 2, Q_proj * ly_p / 2, 20, beton_p, acier_p)
            if erreur_cc:
                st.error(f"⚠️ {erreur_cc}")
            else:
                rpo = calc_poteau(h_niv, G_pot_p, Q_pot_p, beton_p, acier_p, b_p, h_p)
                cote_pot_calc = rpo.get("cote") or rpo.get("b_cm", 25)
                rf  = calc_fondation(G_pot_p, Q_pot_p, cote_pot_calc, q_sol_p, beton_p, acier_p, type_sol_p)

                for r, t in [(rd,"CORPS_CREUX" if cc_projet else "DALLE"),(rp,"POUTRE_CONTINUE" if n_pc_p > 1 else "POUTRE"),(rpo,"POTEAU"),(rf,"FONDATION")]:
                    r["type"] = t
                    st.session_state.resultats.append(r)

                st.session_state.last["projet"] = {
                    "rd": rd, "rp": rp, "rpo": rpo, "rf": rf,
                    "beton": beton_p, "acier": acier_p, "cc": cc_projet,
                }
                st.toast("Projet complet calculé", icon="✅")

        pj = st.session_state.last.get("projet")
        if pj:
            rd, rp, rpo, rf = pj["rd"], pj["rp"], pj["rpo"], pj["rf"]
            st.success("✅ Projet calculé complet !")

            sect = f"{rpo['b_cm']}×{rpo['h_cm']}cm" if rpo.get("rect") else f"{rpo['cote']}×{rpo['cote']}cm"

            col_a, col_b = st.columns(2)
            if pj.get("cc"):
                col_a.metric("Plancher corps creux", f"{rd['hourdis']} — h={rd['travees'][0]['h']}cm")
            else:
                col_a.metric("Dalle", f"e={rd['h']}cm")
            col_b.metric("Poutre" + (f" continue ({len(rp['portees'])} tr.)" if rp.get("type") == "POUTRE_CONTINUE" else ""),
                         f"{rp['larg']}×{rp['h']}cm")
            col_a.metric("Poteau", sect)
            col_b.metric("Fondation", f"{rf['cote']}×{rf['cote']}×{rf['h']}cm")

            bouton_pdf("projet", [rd, rp, rpo, rf], pj["beton"], pj["acier"],
                       label="📥 Télécharger la note de calcul du projet (PDF)")
        else:
            placeholder_resultat()


# ════════════════════════════════════════════════════════════
# PAGE 7 — NOTE DE CALCUL PDF
# ════════════════════════════════════════════════════════════
elif page == "📄  Note de Calcul PDF":
    entete("📄 Note de Calcul — Export PDF",
           "Regroupe tous les calculs effectués pendant la session dans un seul rapport.")

    if not st.session_state.resultats:
        st.warning("⚠️ Aucun calcul en mémoire. Effectuez d'abord un calcul dans les autres pages.")
    else:
        st.write(f"**{len(st.session_state.resultats)} élément(s)** prêt(s) à exporter :")
        for i, r in enumerate(st.session_state.resultats):
            st.write(f"  {i+1}. **{r.get('type','?')}**")

        st.markdown("---")
        nom_pdf   = st.text_input("Nom du projet pour le PDF" + REQ, st.session_state.projet_nom)
        beton_pdf = st.selectbox("Béton" + REQ, list(BETONS.keys()), index=1, key="b_pdf")
        acier_pdf = st.selectbox("Acier" + REQ, list(ACIERS.keys()), index=1, key="a_pdf")

        if st.button("📄 GÉNÉRER LA NOTE DE CALCUL PDF"):
            if not nom_pdf.strip():
                st.error("⚠️ Le nom du projet est obligatoire.")
            else:
                with st.spinner("Génération en cours..."):
                    chemin = generer_pdf(st.session_state.resultats, nom_pdf, beton_pdf, acier_pdf)
                if chemin:
                    with open(chemin, "rb") as f:
                        st.download_button(
                            label="⬇️ Télécharger la Note de Calcul PDF",
                            data=f,
                            file_name=f"note_calcul_{nom_pdf.replace(' ','_')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    st.success("✅ PDF généré avec succès !")
                else:
                    st.error("❌ Erreur. Vérifiez que reportlab est installé : pip install reportlab")

        st.markdown("---")
        if st.button("🗑️ Vider l'historique des calculs"):
            st.session_state.resultats = []
            st.session_state.last = {}
            st.success("✅ Historique vidé.")

# ── FOOTER ──
st.markdown("---")
st.caption("🏗️ Génie Civil Pro v11 — BAEL 91 — Outil de pré-dimensionnement béton armé. Validation par ingénieur structure recommandée avant exécution.")
