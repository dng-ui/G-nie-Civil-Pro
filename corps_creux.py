"""
Calcul d'un plancher à corps creux (poutrelle) — BAEL 91, fonction AUTONOME.
Pas relié à l'app Streamlit. Sert uniquement à valider la méthode.

Hypothèses (à faire valider) :
- Poutrelle calculée en flexion simple : section en T en travée, rectangulaire b0 x h sur appui.
- Largeur de table b = 2*b1 + b0, b1 = min((L - b0)/2, portée/10)   (BAEL A.4.1,3)
- d = 0.9 h
- Non-fragilité : Amin = 0.23 * b * d * ft28 / fe avec b = largeur de table (convention prudente,
  celle de l'exemple publié utilisé pour la validation)
- Treillis soudé (table de compression) : A_perp >= 200/fe si L <= 50 cm ; 4L/fe si 50 < L < 80 cm ;
  A_par >= A_perp/2 ; mailles max 20 cm (perp.) et 33 cm (par.)
- Flèche : conditions BAEL B.6.5,1 NON confirmées par une source web ici -> signalées "indicatif".
"""
import math

GAMMA_B, GAMMA_S = 1.5, 1.15
DIAMS = {6: 28.27, 8: 50.27, 10: 78.54, 12: 113.1, 14: 153.94}   # mm² — HA14 = diamètre maximal disponible
HOURDIS = {"12+4": (12, 4), "15+5": (15, 5), "16+4": (16, 4), "20+5": (20, 5), "25+5": (25, 5)}
FILS_TREILLIS = [5, 6, 7, 8, 10]   # mm


def _aire_fil(d):
    return math.pi * d**2 / 4      # mm²


def _alpha_mu(mu):
    return 1.25 * (1 - math.sqrt(max(1 - 2 * mu, 0)))


def largeur_table(L, b0, portee):
    """b = 2*b1 + b0 avec b1 = min((L-b0)/2 ; portee/10), en cm."""
    b1 = min((L - b0) / 2, portee * 100 / 10)
    return 2 * b1 + b0


def treillis(L, fe_t=500.0):
    """Treillis soudé de la table de compression. L = entraxe en cm, fe_t en MPa. Retourne cm²/m."""
    if L <= 50:
        a_perp = 200 / fe_t
    elif L < 80:
        a_perp = 4 * L / fe_t
    else:
        raise ValueError("Entraxe >= 80 cm : hors du domaine de la règle forfaitaire")
    a_par = a_perp / 2

    def choix(a, esp):
        for d in FILS_TREILLIS:
            sec = _aire_fil(d) / (esp / 100) / 100       # cm²/m
            if sec >= a:
                return f"∅{d} / {esp} cm ({round(sec, 2)} cm²/m)"
        return "À augmenter (fils > ∅10)"

    return {"A_perp": round(a_perp, 3), "A_par": round(a_par, 3),
            "choix_perp": choix(a_perp, 20), "choix_par": choix(a_par, 33)}


def section_acier(Mu, b, b0, h0, d, fc28, fe):
    """Armature tendue (cm²) pour un moment Mu (kN.m) : rectangulaire b x d si l'axe neutre est
    dans la table, sinon section en T. Retourne (As_cm2, mode, alertes)."""
    fbu = 0.85 * fc28 / GAMMA_B
    fsu = fe / GAMMA_S
    mu_l = 0.392 if fe == 400 else 0.372
    alertes = []
    if Mu <= 0:
        return 0.0, "nul", alertes
    M = Mu * 1e6                                               # N.mm
    bb, bb0, hh0, dd = b * 10, b0 * 10, h0 * 10, d * 10        # mm
    Mtable = fbu * bb * hh0 * (dd - hh0 / 2)
    if M <= Mtable:
        mu = M / (bb * dd**2 * fbu)
        mode = "rectangulaire (axe neutre dans la table)"
        if mu > mu_l:
            alertes.append("mu > mu_lim : armatures comprimées nécessaires")
        a = _alpha_mu(mu)
        z = dd * (1 - 0.4 * a)
        As = M / (z * fsu)
    else:
        mode = "en T (axe neutre dans la nervure)"
        M1 = fbu * (bb - bb0) * hh0 * (dd - hh0 / 2)
        M2 = M - M1
        mu = M2 / (bb0 * dd**2 * fbu)
        if mu > mu_l:
            alertes.append("mu > mu_lim : armatures comprimées nécessaires")
        a = _alpha_mu(mu)
        z = dd * (1 - 0.4 * a)
        As = M1 / (fsu * (dd - hh0 / 2)) + M2 / (z * fsu)
    return As / 100, mode, alertes                              # cm²


def moment_resistant(As_cm2, b, b0, h0, d, fc28, fe):
    """Moment ultime résistant (kN.m) d'une section avec As donnée (axe neutre dans la table ou la nervure)."""
    fbu = 0.85 * fc28 / GAMMA_B
    fsu = fe / GAMMA_S
    As = As_cm2 * 100
    bb, bb0, hh0, dd = b * 10, b0 * 10, h0 * 10, d * 10
    y = As * fsu / (0.8 * bb * fbu)
    if 0.8 * y <= hh0:
        return As * fsu * (dd - 0.4 * y) / 1e6
    # axe neutre dans la nervure : équilibre en T (bloc rectangulaire 0.8 y)
    Cf = fbu * (bb - bb0) * hh0
    y = (As * fsu - Cf) / (0.8 * bb0 * fbu)
    zf = dd - hh0 / 2
    return (Cf * zf + fbu * bb0 * 0.8 * y * (dd - 0.4 * y)) / 1e6


def sigma_bc(Mser, As_cm2, b, d, n=15.0):
    """Contrainte béton ELS section rectangulaire b x d (cm), Mser en kN.m, retourne (MPa, y1 mm)."""
    bb, dd, As = b * 10, d * 10, As_cm2 * 100
    A_ = bb / 2
    B_ = n * As
    C_ = -n * As * dd
    y1 = (-B_ + math.sqrt(B_**2 - 4 * A_ * C_)) / (2 * A_)
    I = bb * y1**3 / 3 + n * As * (dd - y1)**2
    return Mser * 1e6 * y1 / I, y1


def choisir_barres(As, nmax=4):
    """Choix de barres HA : retourne (texte, section réelle cm², diamètre mm, nombre) ; section None si hors capacité.
    On préfère le plus petit nombre de barres (2 sur une nervure de 10 cm, comme dans les exemples publiés),
    puis le plus petit diamètre qui convient."""
    if As <= 0:
        return "—", 0.0, None, 0
    for n in range(2, nmax + 1):
        for dia in [8, 10, 12, 14]:           # HA14 = plus gros diamètre disponible sur le marché
            sc = DIAMS[dia] / 100
            if n * sc >= As:
                note = " — 2 lits (d réduit)" if n > 2 else ""
                return f"{n}HA{dia} ({round(n * sc, 2)} cm²){note}", n * sc, dia, n
    return f"As={round(As, 2)} cm² (> {nmax}HA14 : section à revoir)", None, None, 0


def barres(As, nmax=4):
    return choisir_barres(As, nmax)[0]


def moments_forfaitaire(portees, G, Q, L_cm, facteurs=(1.35, 1.5), inertie_constante=True,
                        fissuration_peu_prejudiciable=True):
    """Méthode forfaitaire (BAEL B.6.2,210) pour une poutrelle continue.
    portees en m ; G, Q en kN/m² ; L_cm = entraxe. facteurs = coefficients appliqués à G et Q
    ((1.35, 1.5) pour l'ELU ; (1, 1) pour les charges de service). Retourne dict (moments kN.m + conditions).
    Les conditions « inertie constante » et « fissuration peu préjudiciable » sont déclarées par l'utilisateur
    (le programme ne peut pas les déduire)."""
    g, q = G * L_cm / 100, Q * L_cm / 100
    pu = facteurs[0] * g + facteurs[1] * q
    al = q / (g + q) if (g + q) > 0 else 0.0
    n = len(portees)
    M0 = [pu * l**2 / 8 for l in portees]
    cond = {
        "Q <= max(2G ; 5 kN/m²)": Q <= max(2 * G, 5.0),
        "rapports de portées entre 0.8 et 1.25": all(0.8 <= portees[i] / portees[i + 1] <= 1.25 for i in range(n - 1)),
        "inertie constante": bool(inertie_constante),
        "fissuration peu préjudiciable": bool(fissuration_peu_prejudiciable),
    }
    if n == 1 or pu <= 0:
        return {"M0": M0, "Mt": M0[:] if n == 1 else [0.0] * n, "Ma": [0.0] * (n + 1), "pu": pu, "conditions": cond}
    coef = []
    for j in range(1, n):                       # appuis intermédiaires
        if n == 2:
            coef.append(0.6)
        elif n == 3 or j in (1, n - 1):
            coef.append(0.5)
        else:
            coef.append(0.4)
    Ma = [0.0] + [coef[j - 1] * max(M0[j - 1], M0[j]) for j in range(1, n)] + [0.0]
    Mt = []
    for i in range(n):
        Mw, Me = Ma[i], Ma[i + 1]
        m = max(1.05 * M0[i], (1 + 0.3 * al) * M0[i]) - (Mw + Me) / 2
        rive = i in (0, n - 1)
        mini = ((1.2 + 0.3 * al) / 2 if rive else (1 + 0.3 * al) / 2) * M0[i]
        Mt.append(max(m, mini))
    return {"M0": M0, "Mt": Mt, "Ma": Ma, "pu": pu, "conditions": cond}


def verifier_entrees(portees, G, Q, fc28, fe, b0, entraxe):
    """Contrôle des données : valeurs strictement positives / admissibles (ValueError explicite)."""
    if any(p is None or p <= 0 for p in portees):
        raise ValueError("Les portées doivent être strictement positives (m)")
    if G is None or G <= 0 or Q is None or Q < 0:
        raise ValueError("G doit être > 0 et Q >= 0 (kN/m²)")
    if fe not in (400, 500):
        raise ValueError("fe doit valoir 400 ou 500 MPa")
    if not 16 <= fc28 <= 40:
        raise ValueError("fc28 hors du domaine 16–40 MPa")
    if b0 < 8 or b0 > 30:
        raise ValueError("b0 hors du domaine 8–30 cm")
    if entraxe <= 0:
        raise ValueError("L'entraxe doit être strictement positif (cm)")


def calc_corps_creux(hourdis, entraxe, portee, G, Q, fc28=25, fe=400,
                     type_poutrelle="sur_place", b0=10.0, As_prefab=None,
                     Mt_ELU=None, Ma_ELU=None, Vu_facteur=1.0, Mser_ratio=None,
                     fe_treillis=500.0, G_j=None, r_moment=None,
                     Mrd_fabricant=None, d_prefab=None, precontrainte=False, M_cases=None):
    """
    hourdis        : "16+4" ... ou tuple (hauteur_creux_cm, table_cm)
    entraxe        : entraxe des poutrelles en cm
    portee         : portée de la poutrelle en m
    G, Q           : kN/m² (plancher complet)
    type_poutrelle : "sur_place" (armatures calculées) ou "prefabriquee"
    Mt_ELU, Ma_ELU : moments (kN.m) imposés (poutrelle continue). Sinon travée isostatique M0 = pu L²/8.
    Vu_facteur     : 1.0 isostatique ; majoration pour poutrelle continue.
    Mser_ratio     : Mser/Mu pour l'ELS si imposé (sinon (G+Q)/(1.35G+1.5Q) proportionnel).
    M_cases        : moments de service en travée par cas de charge {"g","j","gq"} (kN.m) pour la flèche.
    Préfabriquée   : fournir Mrd_fabricant (kN.m, fiche du fabricant) ou As_prefab (+ d_prefab) ;
                     précontrainte=True -> non calculable ici (fiche du fabricant).
    Largeur de table : b = 2 b1 + b0, b1 = min((entraxe - b0)/2 ; portée/10). La limite b1 <= 2x/3 n'est pas
    appliquée : à mi-travée elle donne L/3, donc jamais déterminante.
    """
    alertes = []
    verifier_entrees([portee], G, Q, fc28, fe, b0, entraxe)
    hc, h0 = HOURDIS[hourdis] if isinstance(hourdis, str) else hourdis
    h = hc + h0
    d = 0.9 * h
    if h0 < 4:
        alertes.append("Table de compression < 4 cm (non admis)")
    if not 25 <= entraxe < 80:
        alertes.append("Entraxe hors de 25–80 cm : règle du treillis non applicable")
    ft28 = 0.6 + 0.06 * fc28

    g_ml, q_ml = G * entraxe / 100, Q * entraxe / 100
    pu = 1.35 * g_ml + 1.5 * q_ml
    ps = g_ml + q_ml
    M0 = pu * portee**2 / 8
    Mt = M0 if Mt_ELU is None else Mt_ELU
    Ma = 0.0 if Ma_ELU is None else Ma_ELU
    b = largeur_table(entraxe, b0, portee)

    As_t, mode_t, al = section_acier(Mt, b, b0, h0, d, fc28, fe)
    alertes += al
    As_a, _, al = section_acier(Ma, b0, b0, h0, d, fc28, fe)    # appui : rectangulaire b0 x d
    alertes += al

    Amin = 0.23 * b * d * ft28 / fe                              # travée : largeur totale (convention prudente)
    Amin_a = 0.23 * b0 * d * ft28 / fe if Ma > 0 else 0.0        # appui : largeur de la nervure b0
    As_req_t = max(As_t, Amin)
    As_req_a = max(As_a, Amin_a) if Ma > 0 else As_a

    res = {
        "h": h, "d": round(d, 1), "b": round(b, 1), "b0": b0,
        "pu_ml": round(pu, 2), "ps_ml": round(ps, 2),
        "M0": round(M0, 2), "Mt": round(Mt, 2), "Ma": round(Ma, 2),
        "mode": mode_t,
        "As_calc": round(As_t, 2), "As_min": round(Amin, 2), "As_min_appui": round(Amin_a, 2),
        "As_req": round(As_req_t, 2), "As_appui": round(As_req_a, 2),
    }

    # Flexion impossible en section simplement armée : on s'arrête, on ne présente pas un résultat trompeur.
    if any("mu > mu_lim" in a for a in alertes):
        res.update({"flexion_valide": False,
                    "statut": "NON VALIDE : section simplement armée insuffisante (armatures comprimées non gérées) "
                              "— augmenter b0 ou la hauteur, ou réduire la portée",
                    "alertes": alertes})
        return res
    res["flexion_valide"] = True

    As_adopte = None
    if type_poutrelle == "prefabriquee":
        if precontrainte:
            res["prefab_ok"] = None
            res["renfort"] = "Poutrelle précontrainte : non calculable ici — utiliser la fiche du fabricant"
            alertes.append("Précontrainte (force, pertes, excentricité) non traitée : se référer au fabricant")
        else:
            if Mrd_fabricant is not None:
                Mrd = Mrd_fabricant
            elif As_prefab is not None:
                d_p = d if d_prefab is None else d_prefab
                if d_prefab is None:
                    alertes.append("Préfabriquée : position des armatures non fournie, d = 0.9 h supposé")
                Mrd = moment_resistant(As_prefab, b, b0, h0, d_p, fc28, fe)
            else:
                raise ValueError("Poutrelle préfabriquée : fournir Mrd_fabricant (kN.m) ou As_prefab (cm²)")
            res["Mrd"] = round(Mrd, 2)
            res["prefab_ok"] = Mrd >= Mt
            res["renfort"] = ("aucun" if Mrd >= Mt else
                              f"Insuffisante (Mrd {Mrd:.2f} < Mt {Mt:.2f} kN.m) : renfort à dimensionner avec le "
                              f"fabricant ou un ingénieur (section totale indicative {As_req_t:.2f} cm² à d = 0.9 h)")
            alertes.append("Préfabriquée : phase provisoire (poids propre, béton frais, 100 kg/ml de chantier, étais) "
                           "et liaison avec la table NON vérifiées — voir la fiche du fabricant")
            if As_prefab is not None:
                As_adopte = As_prefab
                res["As_adopte"] = As_prefab
            else:
                alertes.append("ELS et flèche non vérifiées : As_prefab non fourni")
    else:
        txt, sec, _, _ = choisir_barres(As_req_t)
        res["disp_travee"] = txt
        if sec is None:
            alertes.append("Armatures de travée > 4HA14 : section à revoir")
            As_adopte = As_req_t
        else:
            As_adopte = sec
        res["As_adopte"] = round(As_adopte, 2)
        res["disp_appui"] = barres(As_req_a, 3) if As_req_a > 0 else "—"

    # Cisaillement
    Vu = Vu_facteur * pu * portee / 2
    tau = Vu * 1e3 / (b0 * 10 * d * 10)
    tau_lim = min(0.2 * fc28 / GAMMA_B, 5.0)
    res.update({"Vu": round(Vu, 2), "tau": round(tau, 3), "tau_lim": round(tau_lim, 2),
                "cis_ok": tau <= tau_lim})

    if As_adopte is not None:
        # ELS : section fissurée réelle (en T si l'axe neutre descend sous la table)
        ratio = Mser_ratio if Mser_ratio is not None else ps / pu
        Mser = Mt * ratio
        y1, Icr = section_fissuree(b, b0, h0, d, As_adopte)
        sbc = Mser * 1e6 * y1 / Icr
        res.update({"Mser": round(Mser, 2), "sigma_bc": round(sbc, 2), "sigma_lim": 0.6 * fc28,
                    "els_ok": sbc <= 0.6 * fc28,
                    "els_section": "en T" if y1 > h0 * 10 else "rectangulaire (axe neutre dans la table)"})

        # Flèche : dispense (BAEL B.6.5,1) puis calcul. h/L >= 1/16 et A/(b0 d) <= 4.2/fe sont confirmées par des
        # cours ; Mt/(10 M0) reste NON confirmée par un document (cohérente avec la mémoire du BAEL et avec l'audit).
        res["fleche_dispense"] = {
            "h/L >= 1/16": h / (portee * 100) >= 1 / 16,
            "A/(b0*d) <= 4.2/fe": As_adopte / (b0 * d) <= 4.2 / fe,
            "h/L >= Mt/(10*M0) [non confirmée par un document]": h / (portee * 100) >= Mt / (10 * M0),
        }
        # La limite de 8 m restreint le DOMAINE de la dispense (planchers supportant des cloisons) : ce n'est pas
        # une 4e inégalité. Au-delà, la dispense est refusée quel que soit le résultat des 3 conditions.
        res["fleche_dispense_domaine_8m"] = portee <= 8.0
        res["fleche_dispense_possible"] = bool(portee <= 8.0 and all(res["fleche_dispense"].values()))
        rm = (Mt / M0) if r_moment is None else r_moment
        fl = fleche_poutrelle(h, h0, b0, b, d, As_adopte, fc28, portee, G, Q, entraxe, G_j, rm, M_cases)
        res["fleche"] = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in fl.items()}
        if G_j is None:
            alertes.append("Flèche : G_j (permanentes avant cloisons) non fourni, hypothèse prudente G_j = 0")
        if not fl["ok"]:
            alertes.append(f"Flèche nuisible {fl['delta_f']:.1f} mm > limite {fl['limite']:.1f} mm")
    else:
        res["fleche"] = None

    if 25 <= entraxe < 80:
        res["treillis"] = treillis(entraxe, fe_treillis)
    res["alertes"] = alertes
    return res


# ════════════════════════════════════════════════════════════════════
# MÉTHODE DE CAQUOT (poutrelle continue, inertie constante)
# Sources : Univ. Batna 2 (chap. poutres continues, BAEL annexe E.2) et cours IUP GCI3 (mcours.net)
#   Ma = (pw*l'w³ + pe*l'e³) / (8.5 (l'w + l'e)) ; l' = l (travée de rive), 0.8 l (travée intermédiaire)
#   Caquot minorée : g' = 2g/3 pour les moments sur appui uniquement
#   X = l/2 + (|Mw| - |Me|)/(p l) ; Mt = p l X/2 - p X²/2 - |Mw|(1 - X/l) - |Me| X/l
# ════════════════════════════════════════════════════════════════════
def moments_caquot(portees, gu, qu, minoree=False):
    """portees en m ; gu = 1.35*g et qu = 1.5*q en kN/ml (charges ELU de la poutrelle).
    Retourne les moments (kN.m) : Ma_max (appuis, extrémités = 0), Mt par travée, x0, efforts tranchants."""
    n = len(portees)
    lp = [l if i in (0, n - 1) else 0.8 * l for i, l in enumerate(portees)]
    g_app = gu * (2 / 3 if minoree else 1.0)           # permanentes réduites pour les appuis seulement
    C_app, D_app = g_app + qu, g_app                   # travée chargée / déchargée (calcul des appuis)
    C = gu + qu                                        # charge complète sur la travée (calcul de Mt)
    if C <= 0:
        return {"lp": lp, "Ma": [0.0] * (n + 1), "Mt": [0.0] * n, "x0": [0.0] * n, "V": [0.0] * n, "C": 0.0, "minoree": minoree}

    def Ma(i, p_gauche, p_droite):                     # appui i entre les travées i-1 et i  (moment en valeur absolue)
        if i <= 0 or i >= n:
            return 0.0
        a, b = lp[i - 1], lp[i]
        return (p_gauche * a**3 + p_droite * b**3) / (8.5 * (a + b))

    Ma_max = [Ma(i, C_app, C_app) for i in range(n + 1)]
    Mt, X, V = [], [], []
    for k in range(n):
        l = portees[k]
        Mw = Ma(k, D_app, C_app)                       # voisines déchargées : Mt maximal
        Me = Ma(k + 1, C_app, D_app)
        x0 = min(max(l / 2 + (Mw - Me) / (C * l), 0.0), l)
        mt = C * l * x0 / 2 - C * x0**2 / 2 - Mw * (1 - x0 / l) - Me * x0 / l
        Mt.append(mt); X.append(x0)
        # effort tranchant maximal : appui voisin le plus chargé
        Vw = C * l / 2 + (Ma_max[k] - Me) / l
        Ve = C * l / 2 + (Ma_max[k + 1] - Mw) / l
        V.append(max(Vw, Ve))
    return {"lp": lp, "Ma": Ma_max, "Mt": Mt, "x0": X, "V": V, "C": C, "minoree": minoree}


# ════════════════════════════════════════════════════════════════════
# FLÈCHE (BAEL B.6.5,2) — formules confirmées par 2 cours (Batna 2 ; IUP GCI3) :
#   If = 1.1 I0 / (1 + λ μ) ; λi = 0.05 ft28 / (ρ (2 + 3 b0/b)) ; λv = 0.4 λi ; ρ = As/(b0 d)
#   μ = max(0 ; 1 - 1.75 ft28 / (4 ρ σs + ft28)) ; f = Mser L² / (10 E If)
#   Ei = 11000 fc28^(1/3) ; Ev = 3700 fc28^(1/3)  (confirmé par une troisième source)
#   Flèche nuisible : Δf = fgv - fji + fpi - fgi ; limite L/500 (L <= 5 m) ou 0.5 cm + L/1000
# ════════════════════════════════════════════════════════════════════
def inertie_homogene(b, b0, h0, h, d, As_cm2, n=15.0):
    """Section en T non fissurée homogénéisée (acier n=15) : retourne (yG mm depuis la fibre sup., I0 mm⁴)."""
    bb, bb0, hh0, hh, dd, As = b * 10, b0 * 10, h0 * 10, h * 10, d * 10, As_cm2 * 100
    aires = [(bb * hh0, hh0 / 2, bb * hh0**3 / 12),
             (bb0 * (hh - hh0), hh0 + (hh - hh0) / 2, bb0 * (hh - hh0)**3 / 12),
             (n * As, dd, 0.0)]
    A = sum(a for a, _, _ in aires)
    yG = sum(a * y for a, y, _ in aires) / A
    I0 = sum(i + a * (y - yG)**2 for a, y, i in aires)
    return yG, I0


def section_fissuree(b, b0, h0, d, As_cm2, n=15.0):
    """Axe neutre y1 (mm) et inertie fissurée Icr (mm⁴) d'une section en T (ou rectangulaire si y1 <= h0)."""
    bb, bb0, hh0, dd, As = b * 10, b0 * 10, h0 * 10, d * 10, As_cm2 * 100
    y = (-n * As + math.sqrt((n * As)**2 + 2 * bb * n * As * dd)) / bb        # rectangulaire b x d
    if y <= hh0:
        I = bb * y**3 / 3 + n * As * (dd - y)**2
        return y, I
    a2 = bb0 / 2
    a1 = (bb - bb0) * hh0 + n * As
    a0 = -((bb - bb0) * hh0**2 / 2 + n * As * dd)
    y = (-a1 + math.sqrt(a1**2 - 4 * a2 * a0)) / (2 * a2)
    I = bb * y**3 / 3 - (bb - bb0) * (y - hh0)**3 / 3 + n * As * (dd - y)**2
    return y, I


def fleche_poutrelle(h, h0, b0, b, d, As_cm2, fc28, portee, G, Q, entraxe, Gj=None, r_moment=1.0, M_cases=None):
    """Flèche d'une poutrelle (mm). G, Q, Gj en kN/m².
    Moments de service en travée : soit M_cases = {"g","j","gq"} (kN.m, calculés cas de charge par cas de charge
    avec la même méthode que l'ELU), soit r_moment * q e L²/8 (r_moment = Mt/M0 ; 1 si travée isostatique).
    Gj = charges permanentes déjà présentes à la pose des cloisons ; None -> 0 (hypothèse prudente).
    Retourne la flèche nuisible Δf = fgv - fji + fpi - fgi (comparée à la limite) et la flèche totale
    fgv + fpi - fgi (affichée sans verdict : limite non confirmée)."""
    ft28 = 0.6 + 0.06 * fc28
    Ei, Ev = 11000 * fc28 ** (1 / 3), 3700 * fc28 ** (1 / 3)
    yG, I0 = inertie_homogene(b, b0, h0, h, d, As_cm2)
    y1, Icr = section_fissuree(b, b0, h0, d, As_cm2)
    rho = As_cm2 * 100 / (b0 * 10 * d * 10)
    lam_i = 0.05 * ft28 / (rho * (2 + 3 * b0 / b))
    lam_v = 0.4 * lam_i
    L = portee * 1000.0
    e = entraxe / 100.0
    gj = 0.0 if Gj is None else Gj

    def M_ser(cle, qsurf):                                    # kN.m -> N.mm
        if M_cases is not None:
            return M_cases[cle] * 1e6
        return r_moment * qsurf * e * portee**2 / 8 * 1e6

    def f(M, E, lam):
        if M <= 0:
            return 0.0, 0.0, 0.0
        sig = 15 * M * (d * 10 - y1) / Icr                    # contrainte acier ELS (section fissurée)
        mu = max(0.0, 1 - 1.75 * ft28 / (4 * rho * sig + ft28))
        If = 1.1 * I0 / (1 + lam * mu)
        return M * L**2 / (10 * E * If), sig, mu

    fgv, sg, mug = f(M_ser("g", G), Ev, lam_v)
    fgi, _, _ = f(M_ser("g", G), Ei, lam_i)
    fji, _, _ = f(M_ser("j", gj), Ei, lam_i)
    fpi, _, _ = f(M_ser("gq", G + Q), Ei, lam_i)
    df = fgv - fji + fpi - fgi
    lim = L / 500 if portee <= 5 else 5 + L / 1000
    return {"I0": I0, "Icr": Icr, "yG": yG, "y1": y1, "rho": rho, "lam_i": lam_i, "lam_v": lam_v,
            "sigma_s_g": sg, "mu_g": mug, "fgi": fgi, "fgv": fgv, "fji": fji, "fpi": fpi,
            "delta_f": df, "limite": lim, "ok": df <= lim, "fleche_totale": fgv - fgi + fpi,
            "moments": "par cas de charge" if M_cases is not None else "Mt/M0 appliqué",
            "hypothese_Gj": "Gj non fourni : 0 (prudent)" if Gj is None else f"Gj = {Gj} kN/m²"}


# ════════════════════════════════════════════════════════════════════
# POUTRELLE CONTINUE : choix de la méthode + calcul de chaque travée + chapeaux
# ════════════════════════════════════════════════════════════════════
def chapeau(Mu, b0, d, h0, fc28, fe, longueur_ref, rive, voisin_rive=False):
    """Armature supérieure d'un appui (section rectangulaire b0 x d). Mu en kN.m, longueur_ref en m
    (rive : portée de la travée, prolongement L/4 ; intermédiaire : plus grande portée voisine, L/5 — cours Univ. Béchar).
    Ancrage ls = Ø fe / (4 τsu), τsu = 0.6 ψs² ft28, ψs = 1.5 (formule BAEL A.6.1,22 de mémoire : à confirmer)."""
    ft28 = 0.6 + 0.06 * fc28
    As, _, al = section_acier(Mu, b0, b0, h0, d, fc28, fe)
    Amin = 0.23 * b0 * d * ft28 / fe
    As_req = max(As, Amin)
    txt, sec, dia, n = choisir_barres(As_req, 3)
    out = {"Mu": round(Mu, 2), "As_calc": round(As, 2), "As_min": round(Amin, 2), "As_req": round(As_req, 2),
           "barres": txt, "alertes": al}
    if dia:
        tau_su = 0.6 * 1.5**2 * ft28
        ls_calc = dia * fe / (4 * tau_su) / 10
        ls_forf = dia * (40 if fe == 400 else 50) / 10      # valeurs forfaitaires BAEL (40 Ø FeE400 / 50 Ø FeE500)
        out["ancrage_ls_calcule_cm"] = round(ls_calc, 1)
        out["ancrage_ls_forfaitaire_cm"] = round(ls_forf, 1)
        out["ancrage_ls_cm"] = round(max(ls_calc, ls_forf), 1)   # valeur retenue : la plus prudente
    # BAEL annexe E.1.3 : rive -> L/4 ; intermédiaire voisin d'un appui de rive -> 1/4 de la plus grande portée voisine ;
    # autre intermédiaire -> 1/5 de la plus grande portée voisine.
    out["prolongement_depuis_nu_cm"] = round(longueur_ref * 100 / (4 if (rive or voisin_rive) else 5), 1)
    out["note_ancrage"] = ("ls calculé pour barres isolées (non groupées en paquet : majorer sinon) ; "
                           "vérifier la longueur réellement disponible et l'enrobage/confinement.")
    return out


def calc_poutrelle_continue(hourdis, entraxe, portees, G, Q, fc28=25, fe=400, type_poutrelle="sur_place",
                            b0=10.0, methode="auto", G_j=None, As_prefab=None, inertie_constante=True,
                            fissuration_peu_prejudiciable=True, Mrd_fabricant=None, d_prefab=None,
                            precontrainte=False, appui_rive_solidaire=True):
    """methode : 'auto' -> forfaitaire si TOUTES ses conditions sont remplies ; sinon Caquot minorée si
    Q <= max(2G ; 5) ; sinon Caquot. Ou 'forfaitaire' / 'caquot_minoree' / 'caquot' imposé.
    La flèche est calculée avec les moments de service de chaque cas de charge (g ; j ; g+q), par la même méthode."""
    verifier_entrees(portees, G, Q, fc28, fe, b0, entraxe)
    forf = moments_forfaitaire(portees, G, Q, entraxe, inertie_constante=inertie_constante,
                               fissuration_peu_prejudiciable=fissuration_peu_prejudiciable)
    if methode == "forfaitaire" and not all(forf["conditions"].values()):
        manque = [k for k, v in forf["conditions"].items() if not v]
        raise ValueError("Méthode forfaitaire imposée mais conditions non satisfaites : " + " ; ".join(manque)
                         + ". Utiliser methode='auto', 'caquot_minoree' ou 'caquot'.")
    if methode == "auto":
        if all(forf["conditions"].values()):
            methode = "forfaitaire"
        elif Q <= max(2 * G, 5.0):
            methode = "caquot_minoree"
        else:
            methode = "caquot"
    n = len(portees)
    e = entraxe / 100
    mino = (methode == "caquot_minoree")
    pu = 1.35 * G * e + 1.5 * Q * e
    if methode == "forfaitaire":
        Mt, Ma = forf["Mt"], forf["Ma"]
        # Majoration de l'effort tranchant isostatique (valeurs non confirmées par un document, recoupées par l'audit) :
        # 15 % à l'appui intermédiaire d'une poutre à 2 travées ; 10 % à l'appui voisin de rive si > 2 travées.
        # Seules les travées touchant cet appui sont majorées ; les travées centrales restent à V0.
        if n == 1:
            V_fact = [1.0]
        elif n == 2:
            V_fact = [1.15, 1.15]
        else:
            V_fact = [1.10 if k in (0, n - 1) else 1.0 for k in range(n)]
    else:
        cq = moments_caquot(portees, 1.35 * G * e, 1.5 * Q * e, minoree=mino)
        Mt, Ma = cq["Mt"], cq["Ma"]
        V_fact = [cq["V"][k] / (pu * portees[k] / 2) for k in range(n)]

    def Mt_service(Gc, Qc):
        if methode == "forfaitaire":
            return moments_forfaitaire(portees, Gc, Qc, entraxe, (1.0, 1.0))["Mt"]
        return moments_caquot(portees, Gc * e, Qc * e, minoree=mino)["Mt"]

    Mt_g, Mt_j, Mt_gq = Mt_service(G, 0.0), Mt_service(G_j or 0.0, 0.0), Mt_service(G, Q)

    resultats = []
    for k in range(n):
        M0k = pu * portees[k]**2 / 8
        Ma_k = max(Ma[k], Ma[k + 1]) if n > 1 else 0.0
        r = calc_corps_creux(hourdis, entraxe, portees[k], G, Q, fc28, fe, type_poutrelle, b0,
                             As_prefab=As_prefab, Mt_ELU=Mt[k], Ma_ELU=Ma_k, Vu_facteur=V_fact[k],
                             G_j=G_j, Mrd_fabricant=Mrd_fabricant, d_prefab=d_prefab, precontrainte=precontrainte,
                             M_cases={"g": Mt_g[k], "j": Mt_j[k], "gq": Mt_gq[k]})
        r["travee"] = k + 1
        resultats.append(r)

    # Chapeaux : appuis intermédiaires (moment calculé) et appuis de rive (0.15 M0 forfaitaire, non calculé)
    hc, h0 = HOURDIS[hourdis] if isinstance(hourdis, str) else hourdis
    d = 0.9 * (hc + h0)
    chapeaux = []
    for i in range(n + 1):
        rive = i in (0, n)
        if rive:
            k = 0 if i == 0 else n - 1
            # 0,15 M0 : préfabriquées -> imposé par B.6.8,414. Coulées sur place -> disposition de ferraillage de la
            # méthode forfaitaire (ne pas l'attribuer à B.6.2,210 ni à B.6.8,414), retenue quand la poutrelle est
            # solidaire de son appui de rive (poteau/poutre : encastrement partiel). Deux avis d'ingénieur divergent
            # sur le cas « appui simplement posé » : par défaut appui_rive_solidaire=True ; False -> As min seulement.
            if type_poutrelle == "prefabriquee":
                Mu, src = 0.15 * pu * portees[k]**2 / 8, "0.15 M0 — B.6.8,414 (préfabriquée)"
            elif methode == "forfaitaire" and appui_rive_solidaire:
                Mu = 0.15 * pu * portees[k]**2 / 8
                src = ("Armatures supérieures d'appui de rive : moment forfaitaire de 0,15 M0 retenu lorsque la "
                       "poutrelle est solidaire de son appui (poteau ou poutre), pour tenir compte d'un encastrement partiel.")
            else:
                Mu, src = 0.0, "pas de 0.15 M0 imposé : As min seulement"
            ref = portees[k]
        else:
            Mu = Ma[i]
            ref = max(portees[i - 1], portees[i])
        voisin_rive = (not rive) and (i == 1 or i == n - 1)   # appui intermédiaire voisin d'un appui de rive
        c = chapeau(Mu, b0, d, h0, fc28, fe, ref, rive, voisin_rive)
        c["appui"] = i + 1
        c["type"] = ("rive (" + src + ")") if rive else "intermédiaire (moment calculé)"
        if rive:
            c["prolongement_convention"] = ("L/4 = convention de calcul, non prescrit par l'annexe E.1.3 "
                                            "(qui ne vise que les appuis intermédiaires)")
        chapeaux.append(c)
    # Annexe E.1.3 : longueurs forfaitaires valables si Q <= G et charges uniformément réparties ; sinon enveloppes.
    e13 = Q <= G
    avert = [] if e13 else ["Q > G : longueurs forfaitaires de chapeaux (annexe E.1.3) non applicables — "
                            "tracer les courbes enveloppes des moments pour arrêter les barres."]
    return {"methode": methode, "conditions_forfaitaire": forf["conditions"], "travees": resultats,
            "chapeaux_domaine_E13": e13, "avertissements_chapeaux": avert,
            "Ma": [round(x, 2) for x in Ma], "Mt": [round(x, 2) for x in Mt], "chapeaux": chapeaux}
