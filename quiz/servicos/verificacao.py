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
from collections import deque

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
    """Junta tudo que O MODELO escreveu, para auditar de uma vez.

    O selo fica DE FORA de proposito. Ele e montado por codigo a partir do
    calculo e diz "Plutao em Aquario, quadratura com o seu Sol, orbe 2,3" -
    exatamente o vocabulario que a auditoria de simplicidade rejeita no corpo.
    Auditar o selo derrubaria toda carta por causa da propria prova.
    """
    ident = carta.get("identificacao") or {}
    porta = carta.get("porta") or {}
    partes = [
        carta.get("titulo") or "",
        carta.get("destaque") or "",
        ident.get("abertura") or "",
        *(ident.get("paragrafos") or []),
        porta.get("abertura") or "",
        *(porta.get("paragrafos") or []),
        *(porta.get("aproveitar") or []),
        porta.get("cuidado") or "",
        # formato antigo e carta de reserva
        *(carta.get("paragrafos") or []),
        carta.get("espera") or "",
        carta.get("janela") or "",
    ]
    return "\n".join(x for x in partes if x)


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


# A porta e a MELHOR noticia da carta: a area onde ha energia sobrando agora.
# Escrita com verbo de concessao ela vira premio de consolacao, e o calculo
# passa a dizer o contrario do que calculou. O prompt e o schema ja proibem;
# esta guarda existe porque a abertura e a unica frase que a pessoa le em voz
# alta na cabeca, e um escorregao ali estraga a revelacao inteira.
RE_CONCESSAO = [
    (re.compile(r"\bced[ea]m?\b|\bceder\b|\bcedendo\b"), "ceder"),
    (re.compile(r"\bo que resta\b|\bo que sobra\b|\bresta\b"), "restar/sobrar"),
    (re.compile(r"\babrir mao\b"), "abrir mao"),
    (re.compile(r"\bse contentar\b|\bcontente-se\b"), "se contentar"),
    (re.compile(r"\bo jeito e\b"), "o jeito e"),
]


def auditar_porta(carta: dict) -> list[str]:
    """Verbo de concessao na abertura da Parte 2. Lista vazia = pode mostrar.

    So a abertura. No cuidado, "ceder demais para manter a paz" e legitimo.
    """
    porta = carta.get("porta") if isinstance(carta, dict) else None
    if not isinstance(porta, dict):
        return []
    abertura = _sem_acento(str(porta.get("abertura") or "")).lower()
    if not abertura:
        return []
    return [f"verbo de concessao na abertura da porta: {rotulo}"
            for regex, rotulo in RE_CONCESSAO if regex.search(abertura)]


# O modelo ECOA o registro do que recebe. Enquanto PLANETA_VIDA dizia que
# Netuno era "o que dissolve contorno", saia "o que voce sente esta pedindo
# contorno, mas nao aceita pressa" - bonito e ininteligivel. O vocabulario ja
# foi reescrito em portugues falado; esta guarda cuida da reincidencia.
#
# So o TITULO e as duas ABERTURAS: sao as tres frases que aparecem grandes na
# tela, e uma unica delas em tom de verso derruba a credibilidade das outras.
RE_POESIA = [
    (re.compile(r"^o que "), "abertura comecando por 'O que'"),
    (re.compile(r"o que (pesa|trava|falta|dói|doi|incomoda|nao foi dito)"),
     "abstracao no lugar da coisa concreta"),
    (re.compile(r"aquilo que"), "aquilo que"),
    (re.compile(r"(esta|estao) pedindo |[^a-z]pede (abrigo|contorno|revisao|espaco|nome)"),
     "verbo 'pedir' com sujeito abstrato"),
    (re.compile(r"dar nome a|nomear o |colocar em palavras"), "dar nome a"),
]


def auditar_registro(carta: dict) -> list[str]:
    """Tom de verso no titulo e nas duas aberturas. Lista vazia = pode mostrar.

    Nenhum brasileiro fala assim, e o Crassus menos ainda.
    """
    if not isinstance(carta, dict):
        return []

    alvos = [("titulo", carta.get("titulo"))]
    for parte in ("identificacao", "porta"):
        bloco = carta.get(parte)
        if isinstance(bloco, dict):
            alvos.append((f"abertura da {parte}", bloco.get("abertura")))

    problemas: list[str] = []
    for onde, texto in alvos:
        s = _sem_acento(str(texto or "")).lower().strip()
        if not s:
            continue
        for regex, rotulo in RE_POESIA:
            if regex.search(s):
                problemas.append(f"tom poetico em {onde}: {rotulo}")
    return problemas


# O destaque e a frase que a pessoa releria e mandaria para uma amiga. Se ela
# cabe na carta de qualquer outra pessoa, nao e dela - e sem uma trava o modelo
# volta ao proverbio, que e o caminho mais curto para uma frase bonita.
#
# Duas checagens, porque a repeticao aparece de duas formas diferentes:
#
#   1. a mesma frase com outras palavras
#      "A conta dos outros nao pode CONTINUAR sendo paga com o seu corpo"
#      "A conta dos outros nao pode SEGUIR sendo paga com o seu corpo"
#      pega por sobreposicao de palavras de conteudo.
#
#   2. a mesma FORMULA com assunto trocado - a que mais apareceu nos testes
#      "Reciprocidade comeca quando o que pesa ganha nome."
#      "Reciprocidade comeca quando o que voce entrega deixa de ser subentendido."
#      a sobreposicao aqui e baixa (0,33) e passaria batido; o que denuncia
#      e o comeco identico. Duas cartas seguidas nao abrem o destaque com as
#      mesmas duas palavras de conteudo.
#
# A memoria e um anel em processo, sem disco: zera quando o servidor reinicia,
# o que e aceitavel num container so e evita I/O em toda geracao.
_DESTAQUES_RECENTES: deque = deque(maxlen=200)

# palavras de funcao nao contam: duas frases podem repetir "o", "de", "que" a
# vontade sem serem a mesma frase.
_VAZIAS = frozenset("""
a as o os um uma uns umas de do da dos das em no na nos nas por para com sem
que quem se ja e ou mas nem ao aos la ali aqui isso isto aquilo aquele aquela
seu sua seus suas meu minha teu tua dele dela deles delas
voce vc eu ele ela nos eles elas lhe me te si
ser estar ter haver fazer ficar vir ir sao esta estao tem foi era sera seja
mais menos muito pouco tao ainda so apenas agora hoje quando onde como porque
nao sim tambem cada todo toda todos todas outro outra outros outras
""".split())

# acima disso, duas frases dizem a mesma coisa com outras palavras
_LIMITE_REPETICAO = 0.70
# e este e o tamanho do comeco que nao pode se repetir
_ABERTURA_IGUAL = 2


def _palavras_de_conteudo(texto: str) -> list[str]:
    """As palavras que carregam o sentido, na ordem em que aparecem."""
    limpo = _sem_acento(str(texto or "")).lower()
    return [p for p in re.findall(r"[a-z]{3,}", limpo) if p not in _VAZIAS]


def auditar_destaque(carta: dict, lembrar: bool = True) -> list[str]:
    """Destaque parecido demais com um recente. Lista vazia = pode mostrar.

    `lembrar=False` serve aos testes, que nao querem sujar o anel.
    """
    if not isinstance(carta, dict):
        return []
    palavras = _palavras_de_conteudo(carta.get("destaque"))
    if len(palavras) < 3:
        # curta demais para julgar; o limite de palavras do esquema ja cuida
        return []

    nucleo = frozenset(palavras)
    abertura = tuple(palavras[:_ABERTURA_IGUAL])

    for antes_nucleo, antes_abertura in _DESTAQUES_RECENTES:
        if abertura == antes_abertura:
            return ["destaque abre igual a uma carta recente: comece a frase "
                    "em destaque por outro assunto"]
        comum = len(nucleo & antes_nucleo)
        menor = min(len(nucleo), len(antes_nucleo))
        if menor and (comum / menor) >= _LIMITE_REPETICAO:
            return ["destaque repete uma carta recente: troque a frase em "
                    "destaque por uma que so sirva para esta pessoa"]

    if lembrar:
        _DESTAQUES_RECENTES.append((nucleo, abertura))
    return []
