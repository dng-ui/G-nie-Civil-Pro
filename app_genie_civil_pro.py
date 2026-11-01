"""
╔══════════════════════════════════════════════════════════════╗
║          GÉNIE CIVIL PRO v9 — Application Web Complète       ║
║          BAEL 91 — Mbouda, Cameroun                          ║
║          DALOKO — +237 681 605 462                           ║
║          Lancer : streamlit run app_genie_civil_pro.py       ║
╚══════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import math
from datetime import datetime

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

# ══════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ══════════════════════════════════════════════════════════════
def fbu(b):
    return 0.85 * BETONS[b] / GAMMA_B

def fsu(a):
    return ACIERS[a] / GAMMA_S

def barres(As, larg=None, nv=None):
    if As <= 0: return "—"
    for di in [10, 12, 14, 16, 20, 25, 32]:
        sc = DIAMS[di] / 100
        for n in (nv or [3, 4, 5, 6, 8]):
            if n * sc < As: continue
            if larg and n > 1 and (larg - 6) / max(n - 1, 1) < 2.5: continue
            return f"{n}HA{di} ({round(n * sc, 2)} cm²)"
    return f"As={round(As, 2)} cm²"

def barres_dalle(As):
    if As <= 0: return "—"
    for di, sm in sorted(DIAMS.items()):
        sc = sm / 100
        for e in [7.5, 10, 12.5, 15, 17.5, 20, 25, 30]:
            if sc / (e / 100) >= As:
                return f"HA{di} / {e} cm  ({round(sc / (e / 100), 2)} cm²/ml)"
    return f"As={round(As, 2)} cm²/ml"

# ══════════════════════════════════════════════════════════════
# MOTEUR DE CALCUL BAEL 91
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
        "As": round(As, 2), "disp": barres(As, larg),
        "cadres": f"∅6 / {int(st_cm)} cm",
        "tau": round(tau, 3), "tau_lim": round(tau_lim, 2),
        "cis_ok": tau <= tau_lim, "beton": beton, "acier": acier
    }


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

        def br(A):
            for di in [10, 12, 14, 16, 20]:
                sc = DIAMS[di] / 100
                for n in [4, 6, 8]:
                    if n * sc >= A: return f"{n}HA{di} ({round(n * sc, 2)} cm²)"
            return f"As={round(A, 2)} cm²"

        disp = br(As / 100)
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
        disp = barres(As / 100, cote, [4, 6, 8])
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
        for di, sm in sorted(DIAMS.items()):
            sc = sm / 100
            for e in [7.5, 10, 12.5, 15, 20, 25]:
                if sc / (e / 100) >= As:
                    return f"HA{di}/{e}cm ({round(sc / (e / 100), 2)} cm²/ml)"
        return f"As={round(As, 2)} cm²/ml"

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

            if t == "DALLE":
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


# ══════════════════════════════════════════════════════════════
# CONFIGURATION STREAMLIT
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Génie Civil Pro",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
[data-testid="stSidebar"] { display: none; }
[data-testid="collapsedControl"] { display: none; }
.stButton > button {
    background: #E07B39; color: white; font-weight: bold;
    border: none; border-radius: 6px; width: 100%;
}
.stButton > button:hover { background: #C8632A; color: white; }
h1, h2, h3 { color: #1C2B3A; }
.ok  { color: #2E7D32; font-weight: bold; }
.nok { color: #C62828; font-weight: bold; }
div[data-testid="metric-container"] { background: #F5F5F5; border-radius: 8px; padding: 10px; }
.nav-bar {
    background: #1C2B3A; padding: 12px 16px; border-radius: 10px;
    margin-bottom: 20px; display: flex; flex-wrap: wrap; gap: 8px;
    align-items: center;
}
.nav-title {
    color: white; font-weight: bold; font-size: 16px; margin-right: 10px;
}
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ──
if "resultats" not in st.session_state: st.session_state.resultats = []
if "charges"   not in st.session_state: st.session_state.charges   = {"G": 0.0, "Q": 0.0}
if "projet_nom" not in st.session_state: st.session_state.projet_nom = "Mon Projet"
if "page" not in st.session_state: st.session_state.page = "⚖️ Calcul G et Q"

# ── NAVIGATION EN HAUT ──
st.markdown(f"""
<div class="nav-bar">
  <span class="nav-title">🏗️ Génie Civil Pro</span>
</div>
""", unsafe_allow_html=True)

pages = [
    "⚖️ Calcul G et Q",
    "📐 Dalle",
    "🔩 Poutre",
    "🏛️ Poteau",
    "🏗️ Fondation",
    "📋 Projet Complet",
    "📄 Note PDF",
]

page = st.selectbox("", pages, index=pages.index(st.session_state.page), label_visibility="collapsed")
st.session_state.page = page
st.markdown("---")


# ════════════════════════════════════════════════════════════
# PAGE 1 — CALCUL G ET Q
# ════════════════════════════════════════════════════════════
if page == "⚖️  Calcul G et Q":
    st.title("⚖️ Calcul des Charges G et Q")
    st.write("Calculez automatiquement les charges permanentes **G** et d'exploitation **Q** selon BAEL 91.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📦 Charges permanentes G (kN/m²)")
        composants = []

        type_plancher = st.selectbox("Type de plancher", ["Corps creux", "Dalle pleine béton armé"])
        if type_plancher == "Corps creux":
            cc = st.selectbox("Type corps creux", list(CORPS_CREUX.keys()), index=2)
            composants.append({"nom": f"Corps creux {cc}", "G": CORPS_CREUX[cc]})
        else:
            ep = st.number_input("Épaisseur dalle (cm)", 10, 30, 14)
            composants.append({"nom": f"Dalle BA {ep}cm", "G": round(25.0 * ep / 100, 3)})

        ep_chape = st.number_input("Chape mortier (cm)", 0, 10, 4)
        if ep_chape > 0:
            composants.append({"nom": f"Chape mortier {ep_chape}cm", "G": round(20.0 * ep_chape / 100, 3)})

        ep_carr = st.number_input("Carrelage (cm)", 0, 5, 2)
        if ep_carr > 0:
            composants.append({"nom": f"Carrelage {ep_carr}cm", "G": round(20.0 * ep_carr / 100, 3)})

        type_cl = st.selectbox("Cloisons", ["Légères (0.75)", "Parpaing 10cm (1.20)", "Parpaing 15cm (1.60)", "Brique 10cm (1.40)", "Aucune (0)"])
        G_cl = {"Légères (0.75)": 0.75, "Parpaing 10cm (1.20)": 1.20, "Parpaing 15cm (1.60)": 1.60, "Brique 10cm (1.40)": 1.40, "Aucune (0)": 0.0}[type_cl]
        if G_cl > 0:
            composants.append({"nom": f"Cloisons {type_cl}", "G": G_cl})

        ep_end = st.number_input("Enduit plafond (cm)", 0.0, 5.0, 1.5)
        if ep_end > 0:
            composants.append({"nom": f"Enduit plafond {ep_end}cm", "G": round(18.0 * ep_end / 100, 3)})

        fp = st.selectbox("Faux-plafond", ["Enduit (0.20)", "Plâtre (0.15)", "Bois (0.10)", "Aucun (0)"])
        G_fp = {"Enduit (0.20)": 0.20, "Plâtre (0.15)": 0.15, "Bois (0.10)": 0.10, "Aucun (0)": 0.0}[fp]
        if G_fp > 0:
            composants.append({"nom": f"Faux-plafond {fp}", "G": G_fp})

        toiture = st.checkbox("Ajouter toiture bois + tôle ?")
        if toiture:
            type_ch = st.selectbox("Charpente bois", ["Légère (0.15)", "Standard (0.25)", "Lourde (0.40)"])
            G_ch = {"Légère (0.15)": 0.15, "Standard (0.25)": 0.25, "Lourde (0.40)": 0.40}[type_ch]
            composants.append({"nom": f"Charpente bois {type_ch}", "G": G_ch})
            ep_tole = st.number_input("Épaisseur tôle (mm)", 0.4, 1.5, 0.63, step=0.01)
            composants.append({"nom": f"Tôle galvanisée {ep_tole}mm", "G": round(77.0 * ep_tole / 1000, 3)})

        G_total = round(sum(c["G"] for c in composants), 3)
        st.subheader("🏃 Charge d'exploitation Q (kN/m²)")
        usage = st.selectbox("Usage du bâtiment", list(CHARGES_Q.keys()))
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
        st.metric("pu ELU = 1.35G + 1.5Q  (kN/m²)", round(1.35 * G_total + 1.5 * Q_val, 3))
        st.metric("pser ELS = G + Q  (kN/m²)", round(G_total + Q_val, 3))

        if st.button("✅ Utiliser ces valeurs dans les calculs"):
            st.session_state.charges = {"G": G_total, "Q": Q_val}
            st.success(f"✅ G = {G_total} kN/m² et Q = {Q_val} kN/m² enregistrés !")


# ════════════════════════════════════════════════════════════
# PAGE 2 — DALLE
# ════════════════════════════════════════════════════════════
elif page == "📐  Dalle":
    st.title("📐 Calcul de Dalle — BAEL 91 (Pivot A)")
    col1, col2 = st.columns([1, 1.3])

    with col1:
        st.subheader("Paramètres")
        lx    = st.number_input("Petite portée lx (m)", 1.0, 15.0, 4.2, 0.1)
        ly    = st.number_input("Grande portée ly (m)", lx, 20.0, 5.1, 0.1)
        G_d   = st.number_input("G (kN/m²)", 0.5, 30.0,
                    float(st.session_state.charges["G"]) if st.session_state.charges["G"] > 0 else 5.5, 0.1)
        Q_d   = st.number_input("Q (kN/m²)", 0.5, 10.0,
                    float(st.session_state.charges["Q"]) if st.session_state.charges["Q"] > 0 else 2.0, 0.1)
        beton = st.selectbox("Béton", list(BETONS.keys()), index=1, key="b_d")
        acier = st.selectbox("Acier", list(ACIERS.keys()), index=1, key="a_d")
        calc  = st.button("⚙️ CALCULER LA DALLE")

    with col2:
        st.subheader("Résultats")
        if calc:
            r = calc_dalle(lx, ly, G_d, Q_d, beton, acier)
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

            r["type"] = "DALLE"
            st.session_state.resultats.append(r)
            st.info("💾 Résultat sauvegardé pour la note de calcul PDF")


# ════════════════════════════════════════════════════════════
# PAGE 3 — POUTRE
# ════════════════════════════════════════════════════════════
elif page == "🔩  Poutre":
    st.title("🔩 Calcul de Poutre — BAEL 91 (Pivot B)")
    col1, col2 = st.columns([1, 1.3])

    with col1:
        st.subheader("Paramètres")
        portee = st.number_input("Portée (m)", 1.0, 20.0, 5.0, 0.1)
        G_ml   = st.number_input("G réparti (kN/m)", 0.0, 200.0, 22.0, 0.5)
        Q_ml   = st.number_input("Q réparti (kN/m)", 0.0, 100.0, 8.0, 0.5)
        larg   = st.number_input("Largeur imposée b (cm)", 15, 60, 20)
        beton  = st.selectbox("Béton", list(BETONS.keys()), index=1, key="b_p")
        acier  = st.selectbox("Acier", list(ACIERS.keys()), index=1, key="a_p")
        calc   = st.button("⚙️ CALCULER LA POUTRE")

    with col2:
        st.subheader("Résultats")
        if calc:
            r = calc_poutre(portee, G_ml, Q_ml, larg, beton, acier)
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
            r["type"] = "POUTRE"
            st.session_state.resultats.append(r)
            st.info("💾 Résultat sauvegardé")


# ════════════════════════════════════════════════════════════
# PAGE 4 — POTEAU
# ════════════════════════════════════════════════════════════
elif page == "🏛️  Poteau":
    st.title("🏛️ Calcul de Poteau — BAEL 91")
    col1, col2 = st.columns([1, 1.3])

    with col1:
        st.subheader("Paramètres")
        type_pot = st.radio("Type de section", ["Carré (auto-dimensionné)", "Rectangulaire (imposé)"])
        b_cm = h_cm_p = None
        if "Rectangulaire" in type_pot:
            b_cm   = st.number_input("b (petite dimension, cm)", 15, 100, 20)
            h_cm_p = st.number_input("h (grande dimension, cm)", b_cm, 150, 30)
        h_libre = st.number_input("Hauteur libre (m)", 2.0, 10.0, 3.2, 0.1)
        G_pot   = st.number_input("G cumulé (kN)", 0.0, 5000.0, 180.0, 5.0)
        Q_pot   = st.number_input("Q cumulé (kN)", 0.0, 3000.0, 45.0, 5.0)
        beton   = st.selectbox("Béton", list(BETONS.keys()), index=1, key="b_po")
        acier   = st.selectbox("Acier", list(ACIERS.keys()), index=1, key="a_po")
        calc    = st.button("⚙️ CALCULER LE POTEAU")

    with col2:
        st.subheader("Résultats")
        if calc:
            r = calc_poteau(h_libre, G_pot, Q_pot, beton, acier, b_cm, h_cm_p)
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
            r["type"] = "POTEAU RECT" if r.get("rect") else "POTEAU"
            st.session_state.resultats.append(r)
            st.info("💾 Résultat sauvegardé")


# ════════════════════════════════════════════════════════════
# PAGE 5 — FONDATION
# ════════════════════════════════════════════════════════════
elif page == "🏗️  Fondation":
    st.title("🏗️ Fondation Superficielle — Méthode des bielles (BAEL 91)")
    col1, col2 = st.columns([1, 1.3])

    with col1:
        st.subheader("Paramètres")
        G_f      = st.number_input("G cumulé (kN)", 0.0, 5000.0, 180.0, 5.0)
        Q_f      = st.number_input("Q cumulé (kN)", 0.0, 3000.0, 45.0, 5.0)
        cote_pot = st.number_input("Côté poteau (cm)", 15, 100, 25)
        q_sol    = st.number_input("Contrainte sol (kPa)", 50.0, 2000.0, 200.0, 10.0)
        type_sol = st.radio("Type contrainte sol", ["admissible", "rupture"])
        st.caption("Admissible : valeur déjà divisée par coeff sécurité\nRupture : l'outil divise par 2 automatiquement")
        beton    = st.selectbox("Béton", list(BETONS.keys()), index=1, key="b_f")
        acier    = st.selectbox("Acier", list(ACIERS.keys()), index=1, key="a_f")
        calc     = st.button("⚙️ CALCULER LA FONDATION")

    with col2:
        st.subheader("Résultats")
        if calc:
            r = calc_fondation(G_f, Q_f, cote_pot, q_sol, beton, acier, type_sol)
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
            r["type"] = "FONDATION"
            st.session_state.resultats.append(r)
            st.info("💾 Résultat sauvegardé")


# ════════════════════════════════════════════════════════════
# PAGE 6 — PROJET COMPLET
# ════════════════════════════════════════════════════════════
elif page == "📋  Projet Complet":
    st.title("📋 Projet Complet — Calcul automatique")
    st.session_state.projet_nom = st.text_input("Nom du projet", st.session_state.projet_nom)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Paramètres généraux")
        n_niv   = st.number_input("Nombre de niveaux (RDC inclus)", 1, 10, 3)
        lx_p    = st.number_input("Portée lx (m)", 2.0, 15.0, 4.2, 0.1)
        ly_p    = st.number_input("Portée ly (m)", lx_p, 20.0, 5.1, 0.1)
        h_niv   = st.number_input("Hauteur par niveau (m)", 2.5, 5.0, 3.2, 0.1)
        G_proj  = st.number_input("G dalle (kN/m²)", 0.5, 30.0, 5.5, 0.1)
        Q_proj  = st.number_input("Q dalle (kN/m²)", 0.5, 10.0, 2.0, 0.1)
        q_sol_p = st.number_input("Contrainte sol (kPa)", 50.0, 2000.0, 200.0, 10.0)
        type_sol_p = st.radio("Type contrainte sol", ["admissible", "rupture"])
        beton_p = st.selectbox("Béton", list(BETONS.keys()), index=1, key="b_pr")
        acier_p = st.selectbox("Acier", list(ACIERS.keys()), index=1, key="a_pr")
        type_pot_p = st.radio("Poteau", ["Carré", "Rectangulaire"])
        b_p = h_p = None
        if type_pot_p == "Rectangulaire":
            b_p = st.number_input("b poteau (cm)", 15, 100, 20)
            h_p = st.number_input("h poteau (cm)", b_p, 150, 30)
        calc_p = st.button("⚙️ CALCULER TOUT LE PROJET")

    with col2:
        st.subheader("Résultats")
        if calc_p:
            S_trib = (lx_p / 2) * (ly_p / 2)
            G_pot_p = G_proj * S_trib * n_niv
            Q_pot_p = Q_proj * S_trib * n_niv

            rd  = calc_dalle(lx_p, ly_p, G_proj, Q_proj, beton_p, acier_p)
            rp  = calc_poutre(lx_p, G_proj * ly_p / 2, Q_proj * ly_p / 2, 20, beton_p, acier_p)
            rpo = calc_poteau(h_niv, G_pot_p, Q_pot_p, beton_p, acier_p, b_p, h_p)
            cote_pot_calc = rpo.get("cote") or rpo.get("b_cm", 25)
            rf  = calc_fondation(G_pot_p, Q_pot_p, cote_pot_calc, q_sol_p, beton_p, acier_p, type_sol_p)

            for r, t in [(rd,"DALLE"),(rp,"POUTRE"),(rpo,"POTEAU"),(rf,"FONDATION")]:
                r["type"] = t
                st.session_state.resultats.append(r)

            st.success("✅ Projet calculé complet !")

            sect = f"{rpo['b_cm']}×{rpo['h_cm']}cm" if rpo.get("rect") else f"{rpo['cote']}×{rpo['cote']}cm"

            col_a, col_b = st.columns(2)
            col_a.metric("Dalle", f"e={rd['h']}cm")
            col_b.metric("Poutre", f"{rp['larg']}×{rp['h']}cm")
            col_a.metric("Poteau", sect)
            col_b.metric("Fondation", f"{rf['cote']}×{rf['cote']}×{rf['h']}cm")

            st.info("👉 Allez dans **Note de Calcul PDF** pour télécharger le rapport complet.")


# ════════════════════════════════════════════════════════════
# PAGE 7 — NOTE DE CALCUL PDF
# ════════════════════════════════════════════════════════════
elif page == "📄  Note de Calcul PDF":
    st.title("📄 Note de Calcul — Export PDF")

    if not st.session_state.resultats:
        st.warning("⚠️ Aucun calcul en mémoire. Effectuez d'abord un calcul dans les autres pages.")
    else:
        st.write(f"**{len(st.session_state.resultats)} élément(s)** prêt(s) à exporter :")
        for i, r in enumerate(st.session_state.resultats):
            st.write(f"  {i+1}. **{r.get('type','?')}**")

        st.markdown("---")
        nom_pdf   = st.text_input("Nom du projet pour le PDF", st.session_state.projet_nom)
        beton_pdf = st.selectbox("Béton", list(BETONS.keys()), index=1, key="b_pdf")
        acier_pdf = st.selectbox("Acier", list(ACIERS.keys()), index=1, key="a_pdf")

        if st.button("📄 GÉNÉRER LA NOTE DE CALCUL PDF"):
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
            st.success("✅ Historique vidé.")

# ── FOOTER ──
st.markdown("---")
st.caption("🏗️ Génie Civil Pro v9 — BAEL 91 — Outil de pré-dimensionnement béton armé. Validation par ingénieur structure recommandée avant exécution.")
