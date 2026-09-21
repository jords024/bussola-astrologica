# -*- coding: utf-8 -*-
"""A única porta para a Kerykeion.

Padrões herdados do Sirius (backend/services/astro_service.py): online=False
porque as coordenadas já vêm do autocomplete, Placidus, zodíaco trópico, e a
resolução de DST com pytz.

Passamos active_points explicitamente. Por padrão a Kerykeion ativa nodos,
Quíron, Lilith, Descendente e Imum Coeli, que não existem em nenhum dos
dicionários de peso. Restringir na origem elimina KeyError, reduz a contagem
de aspectos e deixa o SVG mais limpo.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import pytz
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer

from .aspectos import AspectoNorm, PresencaNorm, normalizar, orbes_maximos
from .pesos import ORBES_CANONICOS, PESO_ANGULAR
from .lentos import Perfil
from .regencia import (CUSPIDE, NUM_DA_CASA, PONTO_ATTR, SIGN_RULER)

logger = logging.getLogger(__name__)

# A efeméride de Quíron (seas_18.se1) não vem no pacote e a Kerykeion loga erro
# ao construir o subject. Não usamos Quíron, então o ruído é irrelevante.

PONTOS = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
          "Uranus", "Neptune", "Pluto", "Ascendant", "Medium_Coeli"]

# eixos em transito nao sao presenca: o Ascendente do momento gira 360 graus por
# dia e depende de onde a pessoa esta agora, nao do mapa dela
EIXOS = {"Ascendant", "Medium_Coeli", "Descendant", "Imum_Coeli"}

PERIODO_HORA = {"madrugada": (0, 3, 6), "manha": (6, 9, 12),
                "tarde": (12, 15, 18), "noite": (18, 21, 23)}

# A Kerykeion corta por orbe ANTES de nos entregar os aspectos: quadratura so
# ate 5 graus, sextil ate 6. A Parte 1 precisa enxergar aspectos de 5 a 10
# graus ja separando, para reconhecer o que a pessoa acabou de atravessar.
# Entao pedimos 10 para todos, e o orbe canonico volta em ORBES_CANONICOS
# so para pontuar - assim o placar de casas nao muda em nada.
ASPECTOS_MAIORES = ("conjunction", "opposition", "square", "trine", "sextile")
ORBE_LARGO = 10.0
ASPECTOS_LARGOS = [{"name": n, "orb": ORBE_LARGO} for n in ASPECTOS_MAIORES]

GRAUS_POR_CASA = 30.0


@dataclass
class Mapa:
    natal: object
    transito: object
    chart: object
    aspectos: list[AspectoNorm]
    presencas: list[PresencaNorm]
    casas_confiaveis: bool
    lua_confiavel: bool
    # Sem hora, as casas sao SOLARES: o signo do Sol vai para a cuspide da
    # casa 1. Tecnica tradicional, usada justamente quando nao ha horario.
    # Precisa ser declarado na tela - fingir precisao e o que o Crassus combate.
    casas_solares: bool = False
    # o que o mapa DELA diz sobre o que a toca mais, para a Parte 1 nao
    # depender de uma ordem de planetas igual para todo mundo
    perfil: Perfil = field(default_factory=Perfil)
    sol_signo: Optional[str] = None
    lua_signo: Optional[str] = None
    asc_signo: Optional[str] = None
    aviso: Optional[str] = None
    alternativas: list = field(default_factory=list)


def _resolver_dst(ano, mes, dia, hora, minuto, tz_str, is_dst=None):
    """Diagnóstico de horário de verão. Quem de fato aplica o offset é a
    Kerykeion, a partir do tz_str; isto aqui só detecta os dois casos
    patológicos e registra."""
    try:
        tz = pytz.timezone(tz_str)
        dt = datetime(ano, mes, dia, hora, minuto)
        try:
            tz.localize(dt, is_dst=is_dst)
        except pytz.exceptions.NonExistentTimeError:
            logger.warning("horario inexistente (virada de DST) em %s: %02d:%02d", tz_str, hora, minuto)
            return hora, minuto, "esse horário não existiu na virada do horário de verão"
        except pytz.exceptions.AmbiguousTimeError:
            logger.warning("horario ambiguo (fim de DST) em %s: %02d:%02d", tz_str, hora, minuto)
            return hora, minuto, "esse horário aconteceu duas vezes na virada do horário de verão"
    except Exception as e:
        logger.warning("falha ao resolver DST em %s: %s", tz_str, e)
    return hora, minuto, None


def _subject(nome, ano, mes, dia, hora, minuto, cidade, is_dst=None):
    return AstrologicalSubjectFactory.from_birth_data(
        name=nome, year=ano, month=mes, day=dia, hour=hora, minute=minuto,
        lat=cidade["lat"], lng=cidade["lng"], tz_str=cidade["tz"],
        city=cidade.get("nome") or "Desconhecida",
        nation=cidade.get("cc") or "BR",
        online=False, zodiac_type="Tropical", houses_system_identifier="P",
        active_points=PONTOS, is_dst=is_dst,
    )


def _signo(subject, attr):
    p = getattr(subject, attr, None)
    return getattr(p, "sign", None) if p else None


def _casa_dos_pontos_natais(natal) -> dict[str, int]:
    """Em que casa natal cada ponto do mapa dela está."""
    out: dict[str, int] = {}
    for ponto, attr in PONTO_ATTR.items():
        p = getattr(natal, attr, None)
        n = NUM_DA_CASA.get(getattr(p, "house", None)) if p else None
        if n:
            out[ponto] = n
    out["Ascendant"] = 1
    out["Medium_Coeli"] = 10
    return out


def _cuspides(natal) -> dict[int, float]:
    """Posicao absoluta das doze cuspides. Confirmado na 5.12.9: todas expoem
    abs_pos."""
    fora: dict[int, float] = {}
    for n, attr in CUSPIDE.items():
        c = getattr(natal, attr, None)
        pos = getattr(c, "abs_pos", None) if c is not None else None
        if pos is not None:
            fora[n] = float(pos)
    return fora


def _quanto_andou_na_casa(cuspides: dict[int, float], abs_pos: Optional[float],
                          casa: Optional[int]) -> Optional[float]:
    """Quantos graus o planeta ja percorreu DENTRO da casa, desde a cuspide.

    Um lento recem-entrado numa casa e um evento de vida; no meio dela, ja e
    paisagem. E essa diferenca que o criterio 2 da Parte 1 usa.
    """
    if abs_pos is None or not casa or casa not in cuspides:
        return None
    return (float(abs_pos) - cuspides[casa]) % 360.0


def _perfil(natal, casas_ok: bool) -> Perfil:
    """O que torna um transito DESTA pessoa, e nao de qualquer uma.

    Duas coisas, ambas lidas do natal:

    Regencia - quem manda no signo do Sol, da Lua e do Ascendente dela.
    Saturno sobre o Sol de quem tem Ascendente em Capricornio nao e a mesma
    coisa que Saturno sobre o Sol de outra pessoa qualquer.

    Angularidade - Sol ou Lua perto de um angulo sao mais sentidos. Depende de
    hora, entao sem casas os dois voltam a pesar igual e simplesmente nao
    desempatam.
    """
    regentes = set()
    for attr in ("sun", "moon"):
        ponto = getattr(natal, attr, None)
        r = SIGN_RULER.get(getattr(ponto, "sign", None)) if ponto else None
        if r:
            regentes.add(r)
    if casas_ok:
        asc = getattr(natal, "first_house", None)
        r = SIGN_RULER.get(getattr(asc, "sign", None)) if asc else None
        if r:
            regentes.add(r)

    peso_sol = peso_lua = 1.0
    if casas_ok:
        angulos = []
        for attr in ("first_house", "tenth_house"):
            c = getattr(natal, attr, None)
            pos = getattr(c, "abs_pos", None) if c is not None else None
            if pos is not None:
                angulos += [float(pos), (float(pos) + 180.0) % 360.0]
        if angulos:
            def peso(attr):
                ponto = getattr(natal, attr, None)
                pos = getattr(ponto, "abs_pos", None) if ponto else None
                if pos is None:
                    return 1.0
                d = min(min(abs(float(pos) - x), 360 - abs(float(pos) - x))
                        for x in angulos)
                return 1.0 + PESO_ANGULAR * max(0.0, 1.0 - d / 30.0)
            peso_sol, peso_lua = peso("sun"), peso("moon")

    return Perfil(regentes=frozenset(regentes),
                  peso_sol=peso_sol, peso_lua=peso_lua)


def _presencas_solares(natal, transito) -> list[PresencaNorm]:
    """Casas solares: o signo do Sol natal ocupa a casa 1, doze setores de 30.

    E o caminho para quem nao sabe a hora de nascer. Sem isto a Parte 2 morre
    justamente para a maior fatia dos leads, e a leitura fica sem direcao.
    """
    sol = getattr(natal, "sun", None)
    base = getattr(sol, "abs_pos", None) if sol else None
    if base is None:
        return []
    inicio = (float(base) // GRAUS_POR_CASA) * GRAUS_POR_CASA

    fora: list[PresencaNorm] = []
    for nome, attr in PONTO_ATTR.items():
        ponto = getattr(transito, attr, None)
        pos = getattr(ponto, "abs_pos", None) if ponto else None
        if pos is None:
            continue
        d = (float(pos) - inicio) % 360.0
        fora.append(PresencaNorm(
            planeta=nome,
            casa=int(d // GRAUS_POR_CASA) + 1,
            signo=getattr(ponto, "sign", None),
            grau=getattr(ponto, "position", None),
            retrogrado=bool(getattr(ponto, "retrograde", False)),
            graus_na_casa=d % GRAUS_POR_CASA,
        ))
    return fora


def _presencas_e_casas(chart, nome_transito, natal=None, transito=None):
    """O que os planetas em trânsito estão pisando nas casas natais dela.

    Usa second_points_in_first_houses: pontos do segundo subject (trânsito)
    projetados nas casas do primeiro (natal). O point_owner_house_number é a
    casa no mapa de trânsito, inútil aqui.
    """
    presencas: list[PresencaNorm] = []
    casa_de: dict[str, int] = {}
    hc = getattr(chart, "house_comparison", None)
    if not hc:
        return presencas, casa_de

    cusp = _cuspides(natal) if natal is not None else {}

    for p in getattr(hc, "second_points_in_first_houses", []) or []:
        if p.point_owner_name != nome_transito or p.point_name in EIXOS:
            continue
        casa = p.projected_house_number
        casa_de[p.point_name] = casa

        # o point_degree do overlay e a posicao dentro do SIGNO; a distancia
        # ate a cuspide exige a posicao absoluta, que vem do proprio subject
        abs_pos = None
        if transito is not None:
            ponto = getattr(transito, PONTO_ATTR.get(p.point_name, ""), None)
            abs_pos = getattr(ponto, "abs_pos", None) if ponto else None

        presencas.append(PresencaNorm(
            planeta=p.point_name, casa=casa,
            signo=p.point_sign, grau=p.point_degree,
            graus_na_casa=_quanto_andou_na_casa(cusp, abs_pos, casa),
        ))
    return presencas, casa_de


def _retrogrados(subject) -> set:
    out = set()
    for ponto, attr in PONTO_ATTR.items():
        p = getattr(subject, attr, None)
        if p is not None and getattr(p, "retrograde", False):
            out.add(ponto)
    return out


def calcular(nascimento: dict, cidade: dict, nome: str, agora: Optional[datetime] = None) -> Mapa:
    """Monta natal + trânsito de agora e devolve tudo já normalizado."""
    agora = agora or datetime.now(timezone.utc)
    if agora.tzinfo is None:
        agora = pytz.timezone(cidade["tz"]).localize(agora)
    agora = agora.astimezone(pytz.timezone(cidade["tz"]))
    precisao = nascimento.get("precisao") or "exata"

    hora = nascimento.get("hora")
    minuto = nascimento.get("minuto") or 0
    aviso = None
    casas_confiaveis = True

    if precisao == "exata":
        hora, minuto, aviso = _resolver_dst(
            nascimento["ano"], nascimento["mes"], nascimento["dia"],
            int(hora or 0), int(minuto), cidade["tz"], nascimento.get("is_dst"),
        )
    elif precisao == "periodo":
        faixa = PERIODO_HORA.get(nascimento.get("periodo") or "tarde", (12, 15, 18))
        hora, minuto = faixa[1], 0
    else:
        hora, minuto = 12, 0
        casas_confiaveis = False

    nome_natal = (nome or "Consulente").strip()[:40] or "Consulente"
    nome_transito = f"Transito_{agora:%Y-%m-%d}"
    if nome_transito == nome_natal:
        nome_natal = nome_natal + " (natal)"

    natal = _subject(nome_natal, nascimento["ano"], nascimento["mes"],
                     nascimento["dia"], hora, minuto, cidade, nascimento.get("is_dst"))
    transito = _subject(nome_transito, agora.year, agora.month, agora.day,
                        agora.hour, agora.minute, cidade, bool(agora.dst()))

    chart = ChartDataFactory.create_transit_chart_data(
        natal, transito, active_points=PONTOS, include_house_comparison=True,
        active_aspects=ASPECTOS_LARGOS,
    )

    presencas, casa_transito_de = _presencas_e_casas(
        chart, nome_transito, natal, transito)
    casa_natal_de = _casa_dos_pontos_natais(natal)
    retro = _retrogrados(transito)
    for p in presencas:
        if p.planeta in retro:
            presencas[presencas.index(p)] = PresencaNorm(
                p.planeta, p.casa, p.signo, p.grau, True, p.graus_na_casa)

    # ORBE CANONICO para pontuar, LARGO para entrar. A heuristica de casas
    # continua enxergando exatamente o que enxergava; os aspectos largos
    # chegam com forca zero e servem so a Parte 1.
    aspectos = normalizar(
        chart.aspects, nome_natal, nome_transito,
        ORBES_CANONICOS,
        casa_natal_de=casa_natal_de,
        casa_transito_de=casa_transito_de,
        retrogrados=retro,
        limites=orbes_maximos(chart.active_aspects),
    )
    aspectos = _com_signos(aspectos, natal, transito)

    lua_confiavel = True
    if precisao != "exata":
        lua_confiavel = _lua_estavel(nascimento, cidade)
        if not lua_confiavel:
            aspectos = [a for a in aspectos if a.natal != "Moon"]

    if precisao == "periodo":
        casas_confiaveis = _casas_estaveis(nascimento, cidade, nome_natal, transito, agora)

    casas_solares = False
    if not casas_confiaveis:
        from dataclasses import replace
        aspectos = [replace(a, casa_natal=None, casa_transito=None)
                    for a in aspectos if a.natal not in EIXOS]
        # As casas de Placidus caem, mas a leitura nao fica sem direcao: entra
        # a camada solar, que nao depende de hora nenhuma.
        presencas = _presencas_solares(natal, transito)
        casas_solares = bool(presencas)

    return Mapa(
        natal=natal, transito=transito, chart=chart,
        aspectos=aspectos, presencas=presencas,
        casas_confiaveis=casas_confiaveis, lua_confiavel=lua_confiavel,
        casas_solares=casas_solares,
        perfil=_perfil(natal, casas_confiaveis),
        sol_signo=_signo(natal, "sun"), lua_signo=_signo(natal, "moon"),
        asc_signo=_signo(natal, "first_house"), aviso=aviso,
    )


def _com_signos(aspectos, natal, transito) -> list[AspectoNorm]:
    from dataclasses import replace
    out = []
    for a in aspectos:
        st = _signo(transito, PONTO_ATTR.get(a.transito, ""))
        sn = _signo(natal, PONTO_ATTR.get(a.natal, ""))
        out.append(replace(a, signo_transito=st, signo_natal=sn))
    return out


def _lua_estavel(nascimento, cidade) -> bool:
    """A Lua anda 13 graus por dia. Sem hora, em boa parte dos dias ela muda de
    signo dentro do intervalo de incerteza, e Lua é peso 10 no mapa natal.
    Quando muda, ela sai dos fatos."""
    try:
        a = _subject("chk0", nascimento["ano"], nascimento["mes"], nascimento["dia"], 0, 0, cidade)
        b = _subject("chk1", nascimento["ano"], nascimento["mes"], nascimento["dia"], 23, 59, cidade)
        return _signo(a, "moon") == _signo(b, "moon")
    except Exception as e:
        logger.warning("falha ao checar estabilidade da Lua: %s", e)
        return False


def _casas_estaveis(nascimento, cidade, nome_natal, transito, agora) -> bool:
    """No modo período, confere se a casa vencedora é a mesma nas duas bordas.
    Se não for, as casas não sustentam a leitura e degrada para o caminho sem casas."""
    from .heuristica import eleger
    faixa = PERIODO_HORA.get(nascimento.get("periodo") or "tarde", (12, 15, 18))
    vencedoras = set()
    try:
        for h in (faixa[0], faixa[2]):
            n = _subject(f"{nome_natal}_{h}", nascimento["ano"], nascimento["mes"],
                         nascimento["dia"], min(h, 23), 0, cidade)
            ch = ChartDataFactory.create_transit_chart_data(
                n, transito, active_points=PONTOS, include_house_comparison=True)
            pres, ct = _presencas_e_casas(ch, transito.name)
            asp = normalizar(ch.aspects, n.name, transito.name,
                             orbes_maximos(ch.active_aspects),
                             casa_natal_de=_casa_dos_pontos_natais(n),
                             casa_transito_de=ct)
            vencedoras.add(eleger(asp, pres, True).casa_aberta)
    except Exception as e:
        logger.warning("falha ao checar estabilidade das casas: %s", e)
        return False
    return len(vencedoras) == 1


def desenhar(chart) -> str:
    """A roda do trânsito sobre o natal, tema escuro, em português.

    remove_css_variables=True é obrigatório: sem ele o SVG depende de variáveis
    de CSS que não existem dentro da nossa página e o mapa sai sem cor.
    Sem minify: economiza 75 KB mas custa 1,2s, e gzip já resolve isso na rede.
    """
    drawer = ChartDrawer(chart_data=chart, theme="dark", chart_language="PT")
    return drawer.generate_wheel_only_svg_string(remove_css_variables=True)
