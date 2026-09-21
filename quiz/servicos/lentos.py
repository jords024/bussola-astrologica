# -*- coding: utf-8 -*-
"""Parte 1 da leitura: o transito que gera identificacao.

A pessoa precisa pensar "isso e sobre mim" antes de aceitar qualquer direcao.
Quem faz isso e o planeta lento tocando Sol ou Lua: e o unico movimento que
descreve a vida inteira dela, e nao um comodo da casa.

Quatro criterios em CASCATA, parando no primeiro que achar. A ordem vai do mais
sentido para o mais distante:

  1. aspecto fechado (<=5 graus) a Sol ou Lua  -> esta acontecendo AGORA
  2. lento recem-entrado numa casa natal       -> comecou a acontecer
  3. aspecto largo (5 a 10) ja separando       -> acabou de acontecer
  4. aspecto largo (5 a 10) ainda aplicando    -> esta a caminho

NAO HA ORDEM FIXA DE PLANETA. Quando mais de um transito qualifica dentro do
mesmo criterio, quem decide e o MAPA DELA, nao uma constante global. Uma regra
tipo "Plutao sempre primeiro" entregava Plutao a 61% das pessoas - medido em 60
mapas -, que e exatamente o generico que a leitura existe para evitar.

Funcoes puras sobre AspectoNorm e PresencaNorm. Nao importa Kerykeion de
proposito, pelo mesmo motivo de heuristica.py: da para testar com dados
sinteticos, sem efemeride.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

from .aspectos import AspectoNorm, PresencaNorm
from .pesos import (MULT_ESTACAO, MULT_REGENTE, ORBES_CANONICOS,
                    PESO_ASPECTO, PESO_MOVIMENTO, VEL_ESTACIONARIO)

LENTOS = ("Pluto", "Neptune", "Uranus", "Saturn")

# So Sol e Lua. Sao os dois pontos que a pessoa sente como "eu", e nao como um
# setor da vida. Ascendente e Meio do Ceu dependem de hora exata e sairiam do
# ar para boa parte dos leads.
ALVOS = ("Sun", "Moon")

# A conjuncao entra: e o aspecto de maior impacto identificatorio, e sem ela
# "Plutao conjunto ao Sol" cairia para um criterio mais fraco.
ASPECTOS = ("conjunction", "opposition", "square", "trine", "sextile")

ORBE_FECHADO = 5.0
ORBE_LARGO = 10.0
GRAUS_DE_ENTRADA = 10.0


@dataclass(frozen=True)
class Perfil:
    """O que o mapa DELA diz sobre o que a toca mais.

    Montado em astro.py a partir do natal. Existe para manter este modulo puro:
    a personalizacao entra como dado, nao como dependencia de efemeride.
    """
    # planetas que regem o signo do Sol, da Lua ou do Ascendente dela.
    # Saturno transitando o Sol de quem tem Ascendente em Capricornio nao e a
    # mesma coisa que Saturno transitando o Sol de qualquer outra pessoa.
    regentes: frozenset = field(default_factory=frozenset)
    # quanto Sol e Lua pesam NESTE mapa: perto de um angulo, o ponto e mais
    # sentido. Sem hora confiavel os dois ficam em 1.0 e nao desempatam nada.
    peso_sol: float = 1.0
    peso_lua: float = 1.0


PERFIL_NEUTRO = Perfil()


@dataclass(frozen=True)
class Identificacao:
    criterio: int
    planeta: str
    aspecto: Optional[AspectoNorm] = None   # criterios 1, 3 e 4
    casa: Optional[int] = None              # criterio 2
    graus_na_casa: Optional[float] = None   # criterio 2
    forca: float = 0.0


def forca_identificacao(a: AspectoNorm, perfil: Perfil = PERFIL_NEUTRO) -> float:
    """O quanto ESTE transito e desta pessoa.

    Cinco fatores, todos relativos ao mapa dela ou ao proprio aspecto:

    - fechamento PROPORCIONAL ao orbe daquele aspecto. Comparar graus crus
      favoreceria sempre os aspectos de tolerancia larga.
    - o TIPO de aspecto, reaproveitando PESO_ASPECTO. Sem isto um trigono
      largo passava na frente de uma quadratura apertada, porque o trigono
      tolera 8 graus e a quadratura so 5 - e quadratura e o que se SENTE.
    - o ponto tocado, com o peso que ELE tem neste mapa.
    - vinculo de regencia: o transitante manda em algum ponto central dela.
    - direcao, reaproveitando PESO_MOVIMENTO, que ja existe.
    - estacao: planeta quase parado em cima do ponto e evento de vida.
    """
    omax = ORBES_CANONICOS.get(a.aspecto)
    if not omax:
        return 0.0
    fechamento = max(0.10, 1.0 - abs(a.orbe) / omax)
    tipo = PESO_ASPECTO.get(a.aspecto, 0) / 10.0
    ponto = perfil.peso_sol if a.natal == "Sun" else perfil.peso_lua
    vinculo = MULT_REGENTE if a.transito in perfil.regentes else 1.0
    direcao = PESO_MOVIMENTO.get(a.movimento, 1.0)
    estacao = MULT_ESTACAO if abs(a.velocidade) < VEL_ESTACIONARIO else 1.0
    return fechamento * tipo * ponto * vinculo * direcao * estacao


def _candidatos(aspectos, piso, teto, movimento=None):
    fora = []
    for a in aspectos:
        if a.transito not in LENTOS or a.natal not in ALVOS:
            continue
        if a.aspecto not in ASPECTOS:
            continue
        orbe = abs(a.orbe)
        if not (piso < orbe <= teto if piso else orbe <= teto):
            continue
        if movimento and a.movimento != movimento:
            continue
        fora.append(a)
    return fora


def _melhor(aspectos, perfil: Perfil) -> Optional[tuple]:
    if not aspectos:
        return None
    # desempate final por nome, so para a mesma entrada nunca dar duas saidas
    pontuados = sorted(((forca_identificacao(a, perfil), a) for a in aspectos),
                       key=lambda par: (-par[0], par[1].transito, par[1].aspecto))
    return pontuados[0]


def eleger_identificacao(
    aspectos: Iterable[AspectoNorm],
    presencas: Iterable[PresencaNorm] = (),
    perfil: Perfil = PERFIL_NEUTRO,
) -> Optional[Identificacao]:
    """Devolve UM transito, ou None quando nada qualifica."""
    aspectos = list(aspectos)

    # 1 - o que esta apertando agora
    escolha = _melhor(_candidatos(aspectos, 0.0, ORBE_FECHADO), perfil)
    if escolha:
        f, a = escolha
        return Identificacao(1, a.transito, aspecto=a, forca=f)

    # 2 - o que acabou de entrar numa area da vida
    entradas = [p for p in presencas
                if p.planeta in LENTOS and p.graus_na_casa is not None
                and 0 <= p.graus_na_casa <= GRAUS_DE_ENTRADA]
    if entradas:
        # mais recem-entrado primeiro: quanto mais perto da cuspide, mais o
        # tema esta comecando agora e mais a pessoa reconhece a virada
        entradas.sort(key=lambda p: (p.graus_na_casa, p.planeta))
        p = entradas[0]
        return Identificacao(2, p.planeta, casa=p.casa,
                             graus_na_casa=p.graus_na_casa)

    # 3 - o que ja passou o pico e agora e assimilacao
    escolha = _melhor(_candidatos(aspectos, ORBE_FECHADO, ORBE_LARGO,
                                  "Separating"), perfil)
    if escolha:
        f, a = escolha
        return Identificacao(3, a.transito, aspecto=a, forca=f)

    # 4 - o que ainda esta a caminho. Fecha o caso em que a Parte 1 sairia
    # vazia, e e honesto: fala do que esta se formando, nao do que passou.
    escolha = _melhor(_candidatos(aspectos, ORBE_FECHADO, ORBE_LARGO,
                                  "Applying"), perfil)
    if escolha:
        f, a = escolha
        return Identificacao(4, a.transito, aspecto=a, forca=f)

    return None
