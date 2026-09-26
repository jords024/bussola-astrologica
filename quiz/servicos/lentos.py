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

# Sol e Lua: os dois pontos que a pessoa sente como "eu", e nao como um setor
# da vida.
ALVOS = ("Sun", "Moon")

# Ascendente e Meio do Ceu. Ficaram de fora por muito tempo com a justificativa
# de que "dependem de hora exata e sairiam do ar para boa parte dos leads".
# Medido nas 88 leituras reais no disco, isso era falso: 97% tem hora exata e
# casas confiaveis, porque o quiz pede a hora para montar o mapa.
#
# O custo era alto. Nos 85 mapas com casas confiaveis:
#   82% tinham aspecto lento fechado em MC ou Ascendente
#   40% tinham nesses pontos o aspecto MAIS APERTADO do mapa inteiro
#   39% recebiam a carta escrita sobre um aspecto mais largo, com o mais
#       apertado calculado e descartado ali do lado
#   15% nao tinham NADA fechado em Sol ou Lua e caiam para criterios mais
#       fracos, mesmo tendo um angulo exato
#
# Os dois sao eixos do mapa, nao comodos: o Ascendente e como ela chega, o Meio
# do Ceu e o lugar que ela ocupa aos olhos dos outros. Falam da vida inteira, e
# e por isso que entram aqui e nao na Parte 2.
#
# So entram quando a hora e confiavel. Sem hora, angulo e chute, e a carta
# voltaria a afirmar uma precisao que o calculo nao tem.
ANGULOS = ("Medium_Coeli", "Ascendant")

# qual campo do Perfil pesa cada ponto. Antes isto era uma linha binaria -
# "peso_sol se for Sol, senao peso_lua" - que daria ao Meio do Ceu o peso da
# Lua no instante em que os angulos entrassem.
CAMPO_DO_PONTO = {
    "Sun": "peso_sol", "Moon": "peso_lua",
    "Medium_Coeli": "peso_mc", "Ascendant": "peso_asc",
}

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
    # os proprios eixos. Ficam em 1.0 de proposito: entram na disputa pelo
    # merito do orbe, do tempo e do tipo de aspecto, sem um bonus inventado.
    # Um Sol colado no Meio do Ceu continua valendo mais (chega a 1.6) do que
    # um aspecto morno no eixo.
    peso_mc: float = 1.0
    peso_asc: float = 1.0
    # so o calculo sabe se a hora daquela pessoa aguenta angulo
    angulos_ok: bool = False


PERFIL_NEUTRO = Perfil()

# Acima disto o transito ainda nao e "agora": conta como pano de fundo.
HORIZONTE_DIAS = 60.0


def dias_para_exato(a: AspectoNorm) -> Optional[float]:
    """Quantos dias faltam (ou fazem) para o aspecto ficar exato.

    Orbe sozinho mente sobre o tempo. Saturno anda 0,077 grau por dia e Urano
    0,012: o MESMO grau de orbe significa treze dias para um e oitenta e um
    para o outro. Quem fala de momento precisa do tempo, nao da distancia.
    """
    if not a.velocidade:
        return None
    return abs(a.orbe) / abs(a.velocidade)


@dataclass(frozen=True)
class Identificacao:
    criterio: int
    planeta: str
    aspecto: Optional[AspectoNorm] = None   # criterios 1, 3 e 4
    casa: Optional[int] = None              # criterio 2
    graus_na_casa: Optional[float] = None   # criterio 2
    forca: float = 0.0
    # O SEGUNDO transito lento, quando existe outro pegando Sol ou Lua ao
    # mesmo tempo. Nao e enfeite: quando dois lentos apertam juntos, e isso
    # que explica a sensacao de estar sendo puxada por dois lados. A carta
    # mencionava um e jogava o outro fora.
    segundo: Optional[AspectoNorm] = None


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
    ponto = getattr(perfil, CAMPO_DO_PONTO.get(a.natal, ""), 1.0)
    vinculo = MULT_REGENTE if a.transito in perfil.regentes else 1.0
    direcao = PESO_MOVIMENTO.get(a.movimento, 1.0)
    estacao = MULT_ESTACAO if abs(a.velocidade) < VEL_ESTACIONARIO else 1.0

    # IMINENCIA: o quanto isto e AGORA, em dias, e nao em graus.
    #
    # Sem este fator a eleicao errava feio. Num mapa medido aqui havia Saturno
    # em quadratura ao Sol com orbe 0,04 grau - exato no mesmo dia - e Urano em
    # quadratura a Lua com 0,28 grau, exato so dali a vinte e tres dias. O
    # bonus de 1,2 da Lua regente atropelava a diferenca e a carta falava do
    # transito distante, ignorando o que estava fechando naquele dia.
    dias = dias_para_exato(a)
    if dias is None:
        iminencia = 1.0
    else:
        iminencia = 1.0 + max(0.0, (HORIZONTE_DIAS - dias) / HORIZONTE_DIAS)

    return fechamento * tipo * ponto * vinculo * direcao * estacao * iminencia


def alvos_de(perfil: Perfil) -> tuple:
    """Quais pontos natais contam para esta pessoa.

    Os eixos entram so quando a hora de nascimento aguenta: sem ela, o
    Ascendente pode estar a um signo inteiro de distancia do real.
    """
    return ALVOS + ANGULOS if perfil.angulos_ok else ALVOS


def _candidatos(aspectos, piso, teto, movimento=None, alvos=ALVOS):
    fora = []
    for a in aspectos:
        if a.transito not in LENTOS or a.natal not in alvos:
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


def _segundo(aspectos, principal: AspectoNorm,
             perfil: Perfil) -> Optional[AspectoNorm]:
    """O outro lento que esta apertando junto, se houver.

    Precisa ser outro PLANETA - dois aspectos do mesmo transitante sao a mesma
    noticia contada duas vezes. Quando pega OUTRO PONTO, melhor ainda: quem ela
    e e como ela aparece sao historias diferentes, e o atrito entre as duas e
    o que a carta tem de mais util para contar.
    """
    outros = [a for a in aspectos if a.transito != principal.transito]
    if not outros:
        return None
    # o de outro ponto natal tem preferencia; depois, forca
    def chave(a):
        mesmo_ponto = (a.natal == principal.natal)
        return (mesmo_ponto, -forca_identificacao(a, perfil), a.transito)
    return sorted(outros, key=chave)[0]


def eleger_identificacao(
    aspectos: Iterable[AspectoNorm],
    presencas: Iterable[PresencaNorm] = (),
    perfil: Perfil = PERFIL_NEUTRO,
) -> Optional[Identificacao]:
    """Devolve UM transito, ou None quando nada qualifica."""
    aspectos = list(aspectos)
    alvos = alvos_de(perfil)

    # 1 - o que esta apertando agora
    fechados = _candidatos(aspectos, 0.0, ORBE_FECHADO, alvos=alvos)
    escolha = _melhor(fechados, perfil)
    if escolha:
        f, a = escolha
        return Identificacao(1, a.transito, aspecto=a, forca=f,
                             segundo=_segundo(fechados, a, perfil))

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
                                  "Separating", alvos), perfil)
    if escolha:
        f, a = escolha
        return Identificacao(3, a.transito, aspecto=a, forca=f)

    # 4 - o que ainda esta a caminho. Fecha o caso em que a Parte 1 sairia
    # vazia, e e honesto: fala do que esta se formando, nao do que passou.
    escolha = _melhor(_candidatos(aspectos, ORBE_FECHADO, ORBE_LARGO,
                                  "Applying", alvos), perfil)
    if escolha:
        f, a = escolha
        return Identificacao(4, a.transito, aspecto=a, forca=f)

    return None
