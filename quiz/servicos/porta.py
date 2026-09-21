# -*- coding: utf-8 -*-
"""Parte 2 da leitura: qual porta da vida esta aberta agora.

Enquanto a Parte 1 compra credibilidade, esta parte gasta essa credibilidade em
direcao. E ela e SEMPRE uma porta aberta, nunca uma porta errada - e essa a
diferenca em relacao ao veredito antigo, que comparava a casa eleita com a area
que a pessoa escolheu no quiz e frequentemente respondia "voce olhou para o
lugar errado" tres telas antes da oferta.

O criterio e deliberadamente simples e auditavel: onde os planetas rapidos
estao se acumulando agora. Rapido muda de casa a cada poucas semanas, entao a
leitura se renova sozinha - ao contrario da Parte 1, onde um lento fica anos no
mesmo aspecto.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Optional

from .aspectos import PresencaNorm

# Os quatro que atravessam o mapa depressa. Jupiter fica de fora: um ano por
# signo ja e lento demais para caracterizar "agora".
RAPIDOS = ("Sun", "Mercury", "Venus", "Mars")

# O Sol e o criterio de desempate, sempre. Com quatro planetas, todo empate no
# topo necessariamente inclui a casa do Sol - num 2x2 os quatro estao nas duas
# casas empatadas, e num 1x1x1x1 cada um esta na sua. A ressalva abaixo existe
# so para o caso de o Sol nao ter vindo na lista.
DESEMPATE = "Sun"


@dataclass(frozen=True)
class Porta:
    casa: int
    planetas: tuple[str, ...]      # os rapidos que estao nessa casa
    empate: bool                   # houve empate no topo
    por_desempate: bool            # venceu pela regra do Sol


def eleger_porta(presencas: Iterable[PresencaNorm]) -> Optional[Porta]:
    """A casa com mais rapidos. None quando nao ha casa confiavel."""
    por_casa: dict[int, list[str]] = defaultdict(list)
    casa_do_sol: Optional[int] = None

    for p in presencas:
        if p.planeta not in RAPIDOS:
            continue
        if not isinstance(p.casa, int) or not (1 <= p.casa <= 12):
            continue
        por_casa[p.casa].append(p.planeta)
        if p.planeta == DESEMPATE:
            casa_do_sol = p.casa

    if not por_casa:
        return None

    teto = max(len(v) for v in por_casa.values())
    empatadas = sorted(c for c, v in por_casa.items() if len(v) == teto)
    empate = len(empatadas) > 1

    if not empate:
        casa = empatadas[0]
        por_desempate = False
    elif casa_do_sol in empatadas:
        casa = casa_do_sol
        por_desempate = True
    else:
        # nao deveria acontecer com os quatro rapidos presentes; se o Sol nao
        # veio na lista, a menor casa e um criterio estavel e reproduzivel,
        # melhor do que depender da ordem de iteracao
        casa = empatadas[0]
        por_desempate = False

    # ordem de leitura fixa, para o texto sempre citar na mesma sequencia
    planetas = tuple(sorted(por_casa[casa], key=RAPIDOS.index))
    return Porta(casa=casa, planetas=planetas, empate=empate,
                 por_desempate=por_desempate)
