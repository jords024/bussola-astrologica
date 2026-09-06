"""Regencia de casa. A Kerykeion nao expoe isso.

Confirmado no fonte da 5.12.9: a unica ocorrencia de "ruler" no pacote e o anel
graduado do desenho (_draw_ruler_ring). Nenhuma regencia astrologica.

Regentes tradicionais de proposito. A heuristica ja da peso 9-10 aos
transaturninos como transitantes; usa-los tambem como regentes natais dobraria
a contagem e enviesaria o placar.
"""
from __future__ import annotations

from typing import Optional

# literal de 3 letras da Kerykeion -> regente tradicional
SIGN_RULER = {
    "Ari": "Mars",    "Tau": "Venus",   "Gem": "Mercury",
    "Can": "Moon",    "Leo": "Sun",     "Vir": "Mercury",
    "Lib": "Venus",   "Sco": "Mars",    "Sag": "Jupiter",
    "Cap": "Saturn",  "Aqu": "Saturn",  "Pis": "Jupiter",
}

# co-regentes modernos, guardados para exibicao e nunca para pontuar
CO_REGENTE = {"Sco": "Pluto", "Aqu": "Uranus", "Pis": "Neptune"}

CUSPIDE = {
    1: "first_house", 2: "second_house", 3: "third_house", 4: "fourth_house",
    5: "fifth_house", 6: "sixth_house", 7: "seventh_house", 8: "eighth_house",
    9: "ninth_house", 10: "tenth_house", 11: "eleventh_house", 12: "twelfth_house",
}

PONTO_ATTR = {
    "Sun": "sun", "Moon": "moon", "Mercury": "mercury", "Venus": "venus",
    "Mars": "mars", "Jupiter": "jupiter", "Saturn": "saturn",
    "Uranus": "uranus", "Neptune": "neptune", "Pluto": "pluto",
}

NUM_DA_CASA = {
    "First_House": 1, "Second_House": 2, "Third_House": 3, "Fourth_House": 4,
    "Fifth_House": 5, "Sixth_House": 6, "Seventh_House": 7, "Eighth_House": 8,
    "Ninth_House": 9, "Tenth_House": 10, "Eleventh_House": 11, "Twelfth_House": 12,
}


def regente_da_casa(natal, casa: int) -> Optional[dict]:
    """Quem responde pela casa e onde ele esta.

    Casa nenhuma fica muda: ou tem alguem dentro, ou o dono dela esta em algum
    lugar dizendo o que esta acontecendo.
    """
    attr = CUSPIDE.get(casa)
    if not attr:
        return None
    cusp = getattr(natal, attr, None)
    if cusp is None:
        return None

    signo = getattr(cusp, "sign", None)
    planeta = SIGN_RULER.get(signo)
    if not planeta:
        return None

    ponto = getattr(natal, PONTO_ATTR.get(planeta, ""), None)
    casa_natal = NUM_DA_CASA.get(getattr(ponto, "house", None)) if ponto else None

    return {
        "planeta": planeta,
        "signo_cuspide": signo,
        "casa_natal": casa_natal,
        "signo_natal": getattr(ponto, "sign", None) if ponto else None,
    }
