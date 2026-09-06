"""A heuristica que elege a porta aberta.

Nao e a IA escolhendo o que achou mais bonito: e uma pontuacao que qualquer
astrologo consegue auditar e discordar. Se o Crassus achar que Jupiter deveria
pesar mais que Saturno, muda um numero em pesos.py e pronto.

Funcoes puras sobre AspectoNorm. Nao importa Kerykeion de proposito, para
poder testar com dados sinteticos.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Optional

from .aspectos import AspectoNorm, PresencaNorm
from .pesos import (
    MULT_CASA_NATAL, MULT_PRESENCA, PESADOS, PESO_ASPECTO,
    PESO_MOVIMENTO, PESO_NATAL, PESO_TRANSITO,
)

DUROS = ("square", "opposition")


def forca(a: AspectoNorm) -> float:
    """Peso do transito x peso do ponto natal tocado x tipo de aspecto,
    modulado pelo quanto o orbe esta fechado e pela direcao do movimento.

    O orbe maximo e por aspecto e vem do proprio retorno da Kerykeion:
    conjuncao vai ate 10 graus, quadratura so ate 5. Normalizar tudo por 8
    super-pontuaria quadraturas largas e produziria valor negativo em
    conjuncoes largas.
    """
    t = PESO_TRANSITO.get(a.transito, 0)
    n = PESO_NATAL.get(a.natal, 0)
    asp = PESO_ASPECTO.get(a.aspecto, 0)
    if not (t and n and asp):
        return 0.0

    omax = a.orbe_max or 8.0
    if abs(a.orbe) > omax:
        return 0.0

    fechado = max(0.15, 1 - (abs(a.orbe) / omax))
    mov = PESO_MOVIMENTO.get(a.movimento, 1.0)
    return t * n * asp * fechado * mov


@dataclass
class Placar:
    casas: dict[int, float]
    tensao: dict[int, float]
    casa_aberta: Optional[int]
    casa_fechada: Optional[int]
    aspecto_principal: Optional[AspectoNorm]
    ordenados: list[tuple[AspectoNorm, float]]
    empate_tecnico: bool


def eleger(
    aspectos: Iterable[AspectoNorm],
    presencas: Iterable[PresencaNorm] = (),
    casas_confiaveis: bool = True,
) -> Placar:
    casas: dict[int, float] = defaultdict(float)
    tensao: dict[int, float] = defaultdict(float)
    ordenados: list[tuple[AspectoNorm, float]] = []

    if casas_confiaveis:
        # 1 - presenca: planeta lento parado numa casa ja vale por si
        for p in presencas:
            peso = PESO_TRANSITO.get(p.planeta, 0)
            if peso and 1 <= p.casa <= 12:
                casas[p.casa] += peso * MULT_PRESENCA

    for a in aspectos:
        f = forca(a)
        if f <= 0:
            continue
        ordenados.append((a, f))

        if not casas_confiaveis:
            continue

        # 2 - aspectos: distribui a forca nas duas casas envolvidas
        if a.casa_transito:
            casas[a.casa_transito] += f
        if a.casa_natal:
            casas[a.casa_natal] += f * MULT_CASA_NATAL

        # 3 - o que resiste: duro + aplicativo + planeta pesado
        if a.aspecto in DUROS and a.movimento == "Applying" and a.transito in PESADOS:
            if a.casa_natal:
                tensao[a.casa_natal] += f

    ordenados.sort(key=lambda x: x[1], reverse=True)

    casa_aberta = max(casas, key=casas.get) if casas else None
    casa_fechada = _eleger_fechada(tensao, ordenados, casa_aberta) if casas_confiaveis else None

    return Placar(
        casas=dict(casas),
        tensao=dict(tensao),
        casa_aberta=casa_aberta,
        casa_fechada=casa_fechada,
        aspecto_principal=_principal(ordenados, casa_aberta),
        ordenados=ordenados,
        empate_tecnico=_empate(casas, casa_aberta),
    )


def _eleger_fechada(tensao, ordenados, casa_aberta) -> Optional[int]:
    """Cascata explicita. O criterio estrito e 3 corpos x 2 aspectos x 1 direcao,
    entao em muitos dias nao ha candidato nenhum. Nesse caso a leitura omite o
    trecho em vez de inventar uma porta fechada."""
    if tensao:
        return max(tensao, key=tensao.get)

    # 2 - qualquer aspecto duro de maior forca, ignorando o movimento
    for a, _ in ordenados:
        if a.aspecto in DUROS and a.casa_natal and a.casa_natal != casa_aberta:
            return a.casa_natal

    # 3 - sem porta fechada. O texto simplesmente nao fala disso.
    return None


def _principal(ordenados, casa_aberta) -> Optional[AspectoNorm]:
    """O aspecto que vira prosa. Prefere um que toque a casa eleita, para o
    texto falar da mesma porta que a bussola apontou."""
    if not ordenados:
        return None
    if casa_aberta:
        for a, _ in ordenados:
            if casa_aberta in (a.casa_transito, a.casa_natal):
                return a
    return ordenados[0][0]


def _empate(casas: dict[int, float], casa_aberta: Optional[int]) -> bool:
    """Empate tecnico e sinal, nao bug: costuma significar tema atravessado,
    tipo carreira mexendo com a casa. A leitura pode dizer isso."""
    if not casa_aberta or len(casas) < 2:
        return False
    valores = sorted(casas.values(), reverse=True)
    if valores[0] <= 0:
        return False
    return (valores[0] - valores[1]) / valores[0] < 0.08
