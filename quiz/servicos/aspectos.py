"""Normalizacao dos aspectos da Kerykeion.

O ponto mais perigoso do sistema mora aqui. Num mapa de transito a Kerykeion
devolve p1 = ponto NATAL e p2 = planeta em TRANSITO, porque create_chart_data
chama dual_chart_aspects(first_subject=natal, ..., first_subject_is_fixed=True).
Trocar os dois inverte todo veredito e o texto continua parecendo plausivel:
"Lua em transito pesada sobre Saturno" quando e Saturno em transito sobre a Lua.
Nao da para perceber lendo. Por isso a inversao vira excecao, nao aviso.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from .pesos import PESO_ASPECTO, PESO_NATAL, PESO_TRANSITO


class OrientacaoInvertida(RuntimeError):
    """p1/p2 nao vieram na orientacao natal/transito esperada."""


@dataclass(frozen=True)
class AspectoNorm:
    transito: str          # planeta que se move (p2_name)
    natal: str             # ponto parado do mapa dela (p1_name)
    aspecto: str
    orbe: float
    orbe_max: float
    movimento: str         # Applying | Static | Separating
    casa_transito: Optional[int] = None   # casa natal pisada pelo transito
    casa_natal: Optional[int] = None      # casa natal do ponto tocado
    grau_transito: Optional[float] = None
    signo_transito: Optional[str] = None
    signo_natal: Optional[str] = None
    retrogrado: bool = False
    velocidade: float = 0.0   # graus/dia do planeta em transito, para estimar a janela


@dataclass(frozen=True)
class PresencaNorm:
    """Planeta em transito atravessando uma casa natal."""
    planeta: str
    casa: int
    signo: Optional[str] = None
    grau: Optional[float] = None
    retrogrado: bool = False


def orbes_maximos(active_aspects: Iterable[dict]) -> dict[str, float]:
    """A Kerykeion usa orbe por aspecto. Normalizar tudo por 8 faz um sextil
    de 7 graus pontuar como se fosse exato."""
    out: dict[str, float] = {}
    for item in active_aspects or []:
        nome = item.get("name") if isinstance(item, dict) else getattr(item, "name", None)
        orbe = item.get("orb") if isinstance(item, dict) else getattr(item, "orb", None)
        if nome and orbe is not None:
            out[nome] = float(orbe)
    return out


def normalizar(
    aspects,
    nome_natal: str,
    nome_transito: str,
    orbes_max: dict[str, float],
    casa_natal_de: Optional[dict] = None,
    casa_transito_de: Optional[dict] = None,
    retrogrados: Optional[set] = None,
) -> list[AspectoNorm]:
    """Converte AspectModel da Kerykeion em AspectoNorm, descartando o que os
    dicionarios de peso nao conhecem.

    A Kerykeion trabalha com 11 tipos de aspecto e dezenas de pontos (Quiron,
    nodos, Lilith, Vertex). PESO_ASPECTO cobre 5 e os de ponto cobrem 10. O que
    sobra e descartado aqui, senao vira KeyError la na frente.
    """
    casa_natal_de = casa_natal_de or {}
    casa_transito_de = casa_transito_de or {}
    retrogrados = retrogrados or set()
    out: list[AspectoNorm] = []

    for a in aspects or []:
        p1_owner = getattr(a, "p1_owner", None)
        p2_owner = getattr(a, "p2_owner", None)

        # a guarda que impede o veredito invertido silencioso
        if p1_owner != nome_natal or p2_owner != nome_transito:
            raise OrientacaoInvertida(
                f"esperava p1={nome_natal!r}/p2={nome_transito!r}, "
                f"veio p1={p1_owner!r}/p2={p2_owner!r}"
            )

        natal = getattr(a, "p1_name", None)
        transito = getattr(a, "p2_name", None)
        aspecto = getattr(a, "aspect", None)

        if aspecto not in PESO_ASPECTO:
            continue
        if transito not in PESO_TRANSITO or natal not in PESO_NATAL:
            continue

        orbe = abs(float(getattr(a, "orbit", 0.0)))
        omax = orbes_max.get(aspecto, 8.0)
        if orbe > omax:
            continue

        out.append(AspectoNorm(
            transito=transito,
            natal=natal,
            aspecto=aspecto,
            orbe=orbe,
            orbe_max=omax,
            movimento=getattr(a, "aspect_movement", "Static") or "Static",
            casa_transito=casa_transito_de.get(transito),
            casa_natal=casa_natal_de.get(natal),
            grau_transito=getattr(a, "p2_abs_pos", None),
            retrogrado=transito in retrogrados,
            velocidade=float(getattr(a, "p2_speed", 0.0) or 0.0),
        ))
    return out
