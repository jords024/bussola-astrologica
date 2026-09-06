# -*- coding: utf-8 -*-
"""A conferencia depois da geracao.

Modelo medio escorrega. Antes de mostrar na tela, varre o texto gerado
procurando nome de planeta, numero de casa e nome de signo, e confere se cada
um aparece nos fatos calculados. Achou algo que nao existe, descarta e gera de
novo. Na segunda falha entra o texto de reserva.

A leitora nunca ve erro, e o Crassus nunca assina uma astrologia que nao existe.
"""
from __future__ import annotations

import re
import unicodedata

from .nomes import PLANETA_PT, SIGNO_PT

TODOS_PLANETAS = set(PLANETA_PT.values())
TODOS_SIGNOS = set(SIGNO_PT.values())

# "Casa 7", "casa 7", "Casa 7." - exige o numero, entao "casa e familia" e
# "dentro de casa" nao disparam falso positivo
RE_CASA = re.compile(r"\bcasas?\s+(\d{1,2})\b", re.IGNORECASE)


def _sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").lower()


def _mencionados(texto: str, vocabulario: set[str]) -> set[str]:
    """Casa palavra inteira, ignorando acento e caixa.

    Ignorar acento evita que "Vênus" escrito "Venus" passe despercebido pela
    allow-list e depois seja acusado de invencao.
    """
    alvo = _sem_acento(texto)
    achados = set()
    for termo in vocabulario:
        t = _sem_acento(termo)
        if re.search(r"\b" + re.escape(t) + r"\b", alvo):
            achados.add(termo)
    return achados


def auditar(texto: str, permitido: dict) -> list[str]:
    """Devolve a lista de termos citados que nao existem nos fatos.

    Lista vazia = pode mostrar.
    """
    problemas: list[str] = []

    ok_planetas = set(permitido.get("planetas_pt") or [])
    ok_signos = set(permitido.get("signos_pt") or [])
    ok_casas = set(permitido.get("casas") or [])

    for p in sorted(_mencionados(texto, TODOS_PLANETAS) - ok_planetas):
        problemas.append(f"planeta inexistente nos fatos: {p}")

    for s in sorted(_mencionados(texto, TODOS_SIGNOS) - ok_signos):
        problemas.append(f"signo inexistente nos fatos: {s}")

    for m in RE_CASA.finditer(texto):
        n = int(m.group(1))
        if n not in ok_casas:
            # quando a hora e desconhecida, ok_casas vem vazia de proposito:
            # sem hora as doze casas sao ruido e o texto nao pode cita-las
            problemas.append(f"casa inexistente nos fatos: Casa {n}")

    return problemas


def texto_da_carta(carta: dict) -> str:
    """Junta tudo que o modelo escreveu, para auditar de uma vez."""
    partes = [
        carta.get("titulo") or "",
        carta.get("selo") or "",
        carta.get("saudacao") or "",
        carta.get("destaque") or "",
        *(carta.get("paragrafos") or []),
        carta.get("espera") or "",
        carta.get("janela") or "",
    ]
    return "\n".join(p for p in partes if p)


# ---------------------------------------------------------------------------
# Auditoria de simplicidade.
#
# Com o corpo da carta proibido de citar astrologia, a auditoria de invencao
# acima perde o alvo: nao havendo termo tecnico, nao ha o que conferir. O freio
# passa a ser o contrario: procurar o jargao que NAO deveria estar ali.
#
# A prova astrologica nao some, ela migra para a nota tecnica ao pe da carta,
# que e montada por codigo e nunca passa por aqui.
# ---------------------------------------------------------------------------

RE_JARGAO = [
    (re.compile(r"\bcasas?\s+\d{1,2}\b", re.I), "número de casa"),
    (re.compile(r"\borbes?\b", re.I), "orbe"),
    (re.compile(r"\b\d+[.,]?\d*\s*graus?\b", re.I), "graus"),
    (re.compile(r"\bgraus?\b", re.I), "graus"),
    (re.compile(r"\bretr[óo]grad[ao]s?\b", re.I), "retrógrado"),
    (re.compile(r"\bnatal\b|\bnatais\b", re.I), "natal"),
    (re.compile(r"\btr[âa]nsitos?\b", re.I), "trânsito"),
    (re.compile(r"\baplicativ[ao]s?\b|\baplicando\b", re.I), "aplicativo"),
    (re.compile(r"\bseparativ[ao]s?\b|\bseparando\b", re.I), "separativo"),
    (re.compile(r"\bconjun[çc][ãa]o\b", re.I), "conjunção"),
    (re.compile(r"\boposi[çc][ãa]o\b", re.I), "oposição"),
    (re.compile(r"\bquadratura\b", re.I), "quadratura"),
    (re.compile(r"\btr[íi]gono\b", re.I), "trígono"),
    (re.compile(r"\bsextil\b", re.I), "sextil"),
    (re.compile(r"\bef[ée]m[ée]rides?\b", re.I), "efemérides"),
    (re.compile(r"\bmapa astral\b|\bcarta natal\b", re.I), "jargão de mapa"),
    (re.compile(r"\bmeio do c[ée]u\b|\bascendente\b|\bdescendente\b", re.I), "eixo do mapa"),
]


def auditar_simplicidade(texto: str) -> list[str]:
    """Devolve o jargão encontrado no corpo. Lista vazia = pode mostrar.

    Planeta e signo entram pela allow-list invertida: no corpo, NENHUM deles é
    permitido.
    """
    problemas: list[str] = []

    for regex, rotulo in RE_JARGAO:
        if regex.search(texto):
            problemas.append(f"termo técnico no corpo da carta: {rotulo}")

    for p in sorted(_mencionados(texto, TODOS_PLANETAS)):
        problemas.append(f"nome de planeta no corpo da carta: {p}")
    for s in sorted(_mencionados(texto, TODOS_SIGNOS)):
        problemas.append(f"nome de signo no corpo da carta: {s}")

    return problemas
