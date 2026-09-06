# -*- coding: utf-8 -*-
"""O bloco de FATOS que vai para o modelo, e a allow-list que audita a resposta.

O to_context() da Kerykeion não serve aqui por dois motivos. Primeiro, o ramo
de trânsito descarta o aspect_movement (ky_context_serializer.py:200-211), que
é justamente o que separa "está chegando" de "já passou". Segundo, ele serializa
os dois mapas inteiros mais o overlay bidirecional completo, vários KB de
tokens que custam latência sem acrescentar nada.

Então o bloco é montado à mão e podado.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from .aspectos import AspectoNorm, PresencaNorm
from .heuristica import Placar
from .nomes import (ASPECTO_HUMANO, ASPECTO_PT, CASA_VIDA, MES_PT,
                    PLANETA_PT, PLANETA_VIDA, SIGNO_PT)
from .veredito import CASA_NOME, Veredito

MAX_ASPECTOS = 5


def _pt_planeta(n: Optional[str]) -> str:
    return PLANETA_PT.get(n or "", n or "")


def _pt_signo(n: Optional[str]) -> str:
    return SIGNO_PT.get(n or "", n or "")


def janela_em_palavras(a: Optional[AspectoNorm], hoje: date) -> str:
    """Quando essa configuração perde força, em linguagem comum.

    Estimativa honesta: quanto tempo o planeta leva para percorrer o orbe que
    falta, na velocidade em que está andando. Dá urgência real, sem contador
    falso.
    """
    if not a or not a.velocidade:
        return "nas próximas semanas"

    restante = a.orbe_max - abs(a.orbe) if a.movimento == "Separating" else abs(a.orbe)
    dias = abs(restante / a.velocidade) if a.velocidade else 0

    if dias <= 10:
        return "nos próximos dias"
    if dias <= 21:
        return "nas próximas duas ou três semanas"
    if dias <= 75:
        alvo = _somar_dias(hoje, int(dias))
        return f"até meados de {MES_PT[alvo.month - 1]}"
    if dias <= 200:
        alvo = _somar_dias(hoje, int(dias))
        return f"até por volta de {MES_PT[alvo.month - 1]}"
    return "ao longo dos próximos meses"


def _somar_dias(d: date, n: int) -> date:
    from datetime import timedelta
    return d + timedelta(days=n)


def descrever_aspecto(a: AspectoNorm, casas_ok: bool) -> str:
    """O aspecto contado em linguagem de vida.

    O modelo nao pode citar planeta, casa, orbe nem nome de aspecto no corpo da
    carta, entao o bloco de FATOS entrega o SIGNIFICADO em vez do rotulo. Sem
    isto o modelo simplifica cortando conteudo; com isto ele troca o termo pela
    descricao que carrega o mesmo peso.
    """
    t = PLANETA_VIDA.get(a.transito, _pt_planeta(a.transito))
    n = PLANETA_VIDA.get(a.natal, _pt_planeta(a.natal))
    humano = ASPECTO_HUMANO.get(a.aspecto, "")
    mov = {
        "Applying": "esta CHEGANDO, ainda vai apertar",
        "Separating": "JA PASSOU o pico, agora e assimilacao",
        "Static": "esta parado, sem se aproximar nem se afastar",
    }.get(a.movimento, a.movimento)
    forca = "muito fechado, pesa bastante" if abs(a.orbe) <= 2 else (
            "fechado" if abs(a.orbe) <= 4 else "ainda largo, pesa menos")

    partes = [f"o que chega de fora: {t}"]
    partes.append(f"toca em voce: {n}")
    partes.append(f"como se encontram: {humano}")
    partes.append(f"{mov}; {forca}")
    if a.retrogrado:
        partes.append("VOLTANDO sobre o proprio caminho: e hora de rever, retomar e "
                      "renegociar, nunca de comecar do zero")
    if casas_ok:
        if a.casa_transito:
            partes.append(f"area da vida onde isso acontece: {CASA_VIDA.get(a.casa_transito,'')}")
        if a.casa_natal:
            partes.append(f"area de onde vem o que foi tocado: {CASA_VIDA.get(a.casa_natal,'')}")
    sep = chr(10) + "    "   # uma linha por fato, indentada sob o marcador
    return "  - " + sep.join(partes)


def nota_tecnica(a: AspectoNorm) -> str:
    """A prova, montada por codigo a partir do que foi calculado.

    O modelo NAO escreve isto. Se escrevesse, poderia inventar um orbe. Assim a
    nota e verdadeira por construcao.
    """
    partes = [_pt_planeta(a.transito)]
    if a.signo_transito:
        partes[0] += f" em {SIGNO_PT.get(a.signo_transito, a.signo_transito)}"
    if a.retrogrado:
        partes[0] += ", retrógrado"
    partes.append(f"{ASPECTO_PT.get(a.aspecto, a.aspecto)} com {_pt_planeta(a.natal)} natal")
    partes.append(f"orbe {abs(a.orbe):.1f}°")
    partes.append({"Applying": "aplicando", "Separating": "separando",
                   "Static": "estacionário"}.get(a.movimento, a.movimento))
    if a.casa_transito:
        partes.append(f"casa {a.casa_transito}")
    return " · ".join(partes)


def montar(
    placar: Placar,
    veredito: Veredito,
    presencas: list[PresencaNorm],
    quiz: dict,
    precisao: dict,
    hoje: date,
) -> dict:
    casas_ok = bool(precisao.get("casas_confiaveis"))
    principais = [a for a, _ in placar.ordenados[:MAX_ASPECTOS]]
    if placar.aspecto_principal and placar.aspecto_principal not in principais:
        principais = [placar.aspecto_principal, *principais[:MAX_ASPECTOS - 1]]

    linhas: list[str] = []
    linhas.append(f"data de hoje: {hoje.day} de {MES_PT[hoje.month-1]} de {hoje.year}")
    linhas.append(f"casas_confiaveis: {'true' if casas_ok else 'false'}")
    if not casas_ok:
        linhas.append(
            "  ATENCAO: sem hora de nascimento confiavel. E PROIBIDO citar "
            "qualquer numero de casa. Escreva por planeta, signo e aspecto."
        )

    linhas.append("")
    linhas.append("ASPECTOS ATIVOS, do mais forte para o mais fraco:")
    for a in principais:
        linhas.append(descrever_aspecto(a, casas_ok))

    if casas_ok and presencas:
        linhas.append("")
        linhas.append("PLANETAS ATRAVESSANDO CASAS NATAIS AGORA:")
        for p in presencas:
            if p.planeta in PLANETA_PT:
                r = ", retrogrado" if p.retrogrado else ""
                linhas.append(
                    f"  - {_pt_planeta(p.planeta)} na casa {p.casa} "
                    f"({CASA_NOME.get(p.casa,'')}), em {_pt_signo(p.signo)}{r}"
                )

    principal = placar.aspecto_principal
    janela = janela_em_palavras(principal, hoje)
    linhas.append("")
    linhas.append(f"janela estimada desta configuracao: {janela}")

    if placar.empate_tecnico:
        linhas.append(
            "empate tecnico no placar: duas areas quase iguais. Costuma significar "
            "tema atravessado, uma area mexendo com a outra. Pode dizer isso."
        )

    bloco_fatos = "\n".join(linhas)

    # ---- veredito ----
    v: list[str] = [f"cenario: {veredito.cenario}"]
    if casas_ok and veredito.casa_aberta:
        v.append(f"casa da demanda (o que ela escolheu olhar): casa {veredito.casa_demanda} "
                 f"({CASA_NOME.get(veredito.casa_demanda,'')})")
        v.append(f"casa mais forte no ceu agora: casa {veredito.casa_aberta} "
                 f"({CASA_NOME.get(veredito.casa_aberta,'')})")
        if veredito.casa_fechada:
            v.append(f"area que pede espera: casa {veredito.casa_fechada} "
                     f"({CASA_NOME.get(veredito.casa_fechada,'')})")
        else:
            v.append("area que pede espera: nenhuma clara. NAO invente uma, "
                     "simplesmente nao fale disso.")
    if not veredito.casa_aberta:
        # sem placar de casas nao existe veredito de casa: nao ha coincidencia a
        # reconhecer nem area vizinha a apontar. So o assunto que ela escolheu.
        v.append("NAO ha casa eleita: sem hora confiavel o placar de casas nao "
                 "existe. NAO diga que o ceu confirma, contraria ou desloca a "
                 "escolha dela, porque essa comparacao nao foi feita. Fale do "
                 "assunto que ela escolheu, lendo pelos aspectos.")

    if veredito.via_regente and veredito.regente:
        r = veredito.regente
        v.append(
            f"a casa da demanda nao tem transito nenhum. Quem responde por ela e "
            f"{_pt_planeta(r['planeta'])}, regente do signo da cuspide"
            + (f", que no mapa natal esta na casa {r['casa_natal']}" if r.get("casa_natal") else "")
            + ". A leitura sai dai."
        )
    bloco_veredito = "\n".join(v)

    # ---- quiz ----
    bloco_quiz = "\n".join([
        f"nome: {quiz.get('primeiro_nome','')}",
        f"area escolhida: {quiz.get('area','')}",
        f"frase do espelho: {quiz.get('espelho','')}",
        f"resposta sobre insistencia: {quiz.get('quebra_texto','')}",
    ])

    return {
        "bloco_fatos": bloco_fatos,
        "bloco_veredito": bloco_veredito,
        "bloco_quiz": bloco_quiz,
        "janela": janela,
        "aspecto_principal": _serializar(principal, casas_ok),
        "aspectos": [_serializar(a, casas_ok) for a in principais],
        # a prova que vai ao pe da carta, pronta e verificada por construcao
        "notas": [nota_tecnica(a) for a in principais],
        "permitido": _allow_list(principais, presencas, placar, veredito, casas_ok),
    }


def _serializar(a: Optional[AspectoNorm], casas_ok: bool) -> Optional[dict]:
    if not a:
        return None
    return {
        "transito": a.transito, "transito_pt": _pt_planeta(a.transito),
        "natal": a.natal, "natal_pt": _pt_planeta(a.natal),
        "aspecto": a.aspecto, "aspecto_pt": ASPECTO_PT.get(a.aspecto, a.aspecto),
        "orbe": round(abs(a.orbe), 2), "orbe_max": a.orbe_max,
        "movimento": a.movimento, "retrogrado": a.retrogrado,
        "casa_transito": a.casa_transito if casas_ok else None,
        "casa_natal": a.casa_natal if casas_ok else None,
    }


def _allow_list(aspectos, presencas, placar, veredito, casas_ok: bool) -> dict:
    """O que o texto tem permissão de citar. Tudo fora disso é invenção.

    Quando as casas não são confiáveis a lista de casas fica VAZIA de propósito,
    e a auditoria passa a rejeitar qualquer menção de casa.
    """
    planetas, signos, casas = set(), set(), set()

    for a in aspectos:
        planetas.add(_pt_planeta(a.transito))
        planetas.add(_pt_planeta(a.natal))
        if casas_ok:
            casas.update(x for x in (a.casa_transito, a.casa_natal) if x)
        if a.signo_transito:
            signos.add(_pt_signo(a.signo_transito))
        if a.signo_natal:
            signos.add(_pt_signo(a.signo_natal))

    for p in presencas:
        if p.planeta in PLANETA_PT:
            planetas.add(_pt_planeta(p.planeta))
            if p.signo:
                signos.add(_pt_signo(p.signo))
            if casas_ok:
                casas.add(p.casa)

    if casas_ok:
        for c in (veredito.casa_demanda, veredito.casa_aberta, veredito.casa_fechada):
            if c:
                casas.add(c)

    if veredito.regente:
        planetas.add(_pt_planeta(veredito.regente.get("planeta")))
        for s in (veredito.regente.get("signo_cuspide"), veredito.regente.get("signo_natal")):
            if s:
                signos.add(_pt_signo(s))

    return {
        "planetas_pt": sorted(x for x in planetas if x),
        "signos_pt": sorted(x for x in signos if x),
        "casas": sorted(casas) if casas_ok else [],
    }
