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
from typing import Optional

from config import DIR_PROMPTS

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
    # A formula que mais saiu nas aberturas reprovadas: "Uma conversa simples
    # anda virando um problema grande", "Uma conversa simples esta virando
    # duvida demais". Sempre a mesma engenharia - substantivo abstrato, verbo
    # de transformacao, substantivo abstrato - e sempre sem nenhuma cena.
    (re.compile(r"(anda|esta|vem|comecou a|passou a) virand[oa]|"
                r"virou (um|uma|assunto|problema|duvida|questao)"),
     "formula 'X esta virando Y': troque por uma coisa que aconteceu"),
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


# ---------------------------------------------------------------------------
# O PLAGIO DOS PROPRIOS EXEMPLOS
#
# O prompt ensina pelo exemplo: mostra uma frase fraca e uma forte, e pede a
# forte. O modelo entendeu como molde. Numa carta medida aqui, o exemplo
#
#     "Voce rele a mensagem procurando o tom, e responde para a versao que
#      imaginou."
#
# saiu quase inteiro no paragrafo 1 de uma pessoa cujo mapa nao tinha nada a
# ver com mensagem nenhuma - e o mesmo aconteceu com "nao conta isso para
# ninguem". A carta parecia precisa e era decorada: a pessoa recebia a cena de
# outra pessoa, escrita por mim, com o nome dela em cima.
#
# Nenhuma regra em texto resolve isto, porque a regra mora no mesmo arquivo dos
# exemplos e perde para eles. Entao a checagem e mecanica: as frases de exemplo
# sao extraidas do proprio prompt e comparadas com o que voltou.

_RE_EXEMPLO = re.compile(
    r'^\s*(?:certo|forte|boa|com dente|→)\s*:?\s*"([^"]{20,})"', re.MULTILINE)

# acima disso, a frase da carta e uma parafrase do exemplo, nao uma cena dela
_LIMITE_PLAGIO = 0.55
# exemplos curtos demais nao dao para julgar sem acusar falso
_MINIMO_EXEMPLO = 5

_EXEMPLOS_DO_PROMPT: Optional[list] = None


_TAMANHO_RADICAL = 5


def _radical(p: str) -> str:
    """O comeco da palavra, que e onde o portugues guarda o sentido.

    A primeira versao tirava o "s" final e nao servia para nada: "mensagens"
    virava "mensagen" e nunca encontrava "mensagem", "responder" nunca
    encontrava "responde". O auditor aprovava paragrafos copiados porque
    comparava terminacao em vez de raiz. Cortar no prefixo resolve os dois
    casos e ainda pega "interpretacoes"/"interpretacao".

    Grosseiro de proposito: junta demais em alguns casos ("conta", "contar",
    "contato" viram "conta"). Como a decisao final depende de varias palavras
    coincidirem, juntar demais custa menos do que deixar passar.
    """
    return p[:_TAMANHO_RADICAL]


def _carregar_exemplos() -> list:
    """As frases de exemplo do proprio prompt, em conjuntos de radicais."""
    global _EXEMPLOS_DO_PROMPT
    if _EXEMPLOS_DO_PROMPT is None:
        try:
            texto = (DIR_PROMPTS / "carta.txt").read_text(encoding="utf-8")
        except Exception:
            _EXEMPLOS_DO_PROMPT = []
            return _EXEMPLOS_DO_PROMPT
        fora = []
        for frase in _RE_EXEMPLO.findall(texto):
            radicais = {_radical(x) for x in _palavras_de_conteudo(frase)}
            if len(radicais) >= _MINIMO_EXEMPLO:
                fora.append((frase, radicais))
        _EXEMPLOS_DO_PROMPT = fora
    return _EXEMPLOS_DO_PROMPT


def auditar_exemplos(carta: dict) -> list[str]:
    """A carta reaproveitou a cena de um exemplo do prompt. Vazia = pode."""
    if not isinstance(carta, dict):
        return []
    exemplos = _carregar_exemplos()
    if not exemplos:
        return []

    for trecho in _frases_da_carta(carta):
        radicais = {_radical(x) for x in _palavras_de_conteudo(trecho)}
        if len(radicais) < _MINIMO_EXEMPLO:
            continue
        for frase, alvo in exemplos:
            comum = len(radicais & alvo)
            if comum / len(alvo) >= _LIMITE_PLAGIO:
                return ["uma frase da carta reaproveita a CENA de um exemplo "
                        "das instrucoes (\"" + frase[:60] + "...\"). Os exemplos "
                        "mostram a FORMA, nunca o assunto. Escreva a cena que "
                        "sai dos FATOS desta pessoa."]
    return []


def _frases_da_carta(carta: dict) -> list:
    ident = carta.get("identificacao") or {}
    porta = carta.get("porta") or {}
    return [x for x in [
        carta.get("destaque"),
        ident.get("abertura"), porta.get("abertura"), porta.get("cuidado"),
        *(ident.get("paragrafos") or []),
        *(porta.get("paragrafos") or []),
        *(porta.get("aproveitar") or []),
        *(carta.get("paragrafos") or []),
    ] if isinstance(x, str) and x.strip()]


# ---------------------------------------------------------------------------
# A RECITACAO DO DICIONARIO
#
# Os FATOS chegam ao modelo em "linguagem de vida": a casa 3 vai como "as
# conversas do dia a dia, as mensagens, os combinados curtos, o vaivem com quem
# esta perto". Isso existe para o modelo saber DE QUE ASSUNTO se trata sem
# poder citar casa nenhuma.
#
# So que ele passou a devolver a propria definicao em prosa. Numa carta medida
# aqui, com Netuno atravessando a casa 3, saiu: "Uma conversa simples esta
# virando duvida demais. Nas mensagens... Um combinado curto vira tres
# interpretacoes." Tres substantivos da definicao, em ordem, sem uma cena.
#
# Nao e plagio de exemplo e nao e invencao: e aritmetica de dicionario. E o
# jeito mais discreto de a carta parecer precisa sem dizer nada, porque a
# definicao serve para todo mundo que tem aquela casa ativada.
#
# A definicao entrega o TERRITORIO. Quem escreve escolhe UMA coisa dali e faz
# a cena. Recitar a lista e o contrario disso.

# quantos substantivos da MESMA definicao um paragrafo pode usar antes de
# estar recitando em vez de escrevendo
_LIMITE_RECITACAO = 4

_DEFINICOES: Optional[list] = None


def _definicoes() -> list:
    """Cada entrada dos dicionarios de vida, como conjunto de radicais."""
    global _DEFINICOES
    if _DEFINICOES is None:
        from .nomes import CASA_VIDA, PLANETA_VIDA
        fora = []
        for origem in (CASA_VIDA, PLANETA_VIDA):
            for texto in origem.values():
                radicais = {_radical(x) for x in _palavras_de_conteudo(texto)}
                if len(radicais) >= _LIMITE_RECITACAO:
                    fora.append((texto, radicais))
        _DEFINICOES = fora
    return _DEFINICOES


# Uma ancora e o que prova que existe uma CENA: um numero, uma fala entre
# aspas, uma hora do dia. Definicao nunca tem nenhuma das tres.
RE_ANCORA = re.compile(
    r"\d|[\"\u201c\u201d\u2018\u2019\']|"
    r"\b(manha|tarde|noite|madrugada|almoco|jantar|domingo|segunda|sabado|"
    r"ontem|amanha|semana|mes|ano)\b")


def auditar_recitacao(carta: dict) -> list[str]:
    """Um bloco que repete a definicao da area em vez de escrever a cena.

    So acusa quando NAO ha nenhuma ancora concreta no bloco. Varias definicoes
    sao listas curtas - PLANETA_VIDA['Mercury'] e "a cabeca: conversa,
    mensagem, combinado, decisao" - e uma carta legitima sobre comunicacao
    esbarra em quatro daquelas palavras sem estar recitando nada. O que separa
    recitacao de escrita nao e a contagem sozinha: e a contagem SEM cena.
    """
    if not isinstance(carta, dict):
        return []

    # O bloco INTEIRO, nao frase a frase: a recitacao se espalha entre a
    # abertura e o paragrafo, e cada pedaco sozinho parece inocente.
    for trecho in _blocos_da_carta(carta):
        if RE_ANCORA.search(_sem_acento(trecho).lower()):
            continue
        radicais = {_radical(x) for x in _palavras_de_conteudo(trecho)}
        for texto, alvo in _definicoes():
            if len(radicais & alvo) >= _LIMITE_RECITACAO:
                return ["um trecho recita a definicao da area (\"" + texto[:55]
                        + "...\") em vez de escrever uma cena. A definicao diz "
                        "DE QUE ASSUNTO se trata: escolha UMA coisa dela e "
                        "conte o que acontece com esta pessoa, com objeto, "
                        "hora ou numero. Listar os termos da area nao e "
                        "precisao, e enchimento."]
    return []


def _blocos_da_carta(carta: dict) -> list:
    """Cada parte da carta como um texto so."""
    fora = []
    for parte in ("identificacao", "porta"):
        bloco = carta.get(parte)
        if not isinstance(bloco, dict):
            continue
        pedacos = [bloco.get("abertura") or "",
                   *(bloco.get("paragrafos") or []),
                   *(bloco.get("aproveitar") or []),
                   bloco.get("cuidado") or ""]
        junto = " ".join(x for x in pedacos if isinstance(x, str))
        if junto.strip():
            fora.append(junto)
    return fora


# ---------------------------------------------------------------------------
# A EXPRESSAO QUE O BRASILEIRO USA
#
# "Voce esta empurrando uma coisa que nao anda na carreira" e
# "Voce esta empurrando COM A BARRIGA uma coisa que nao anda na carreira"
# carregam a mesma informacao. A segunda e a que a pessoa fala - e por isso e a
# que ela reconhece. Sem a expressao o texto sai correto e morno, tipo manual,
# e morno nao gruda.
#
# Pedir isso em prosa nao bastou: numa carta medida aqui o modelo leu a regra,
# reaproveitou a frase do proprio quiz e nao usou expressao nenhuma. Entao a
# conferencia e mecanica, como a do plagio.
#
# O banco de expressoes mora no prompt, nao aqui: um lugar so para manter, e
# quem edita o texto edita a regra junto.

# _sem_acento() tambem poe em minuscula, entao o padrao ignora caixa.
_RE_BANCO = re.compile(r"banco de expressoes(.+?)regra de ouro", re.S | re.I)

# Palavras que aparecem no banco mas NAO denunciam expressao nenhuma: sao
# vocabulario comum. "dinheiro" sai de "o dinheiro nao estica" e faria toda
# carta sobre dinheiro passar de graca; "frente", "depois" e "cima" idem. O
# auditor procura SABOR, nao assunto.
_COMUNS_DEMAIS = frozenset(
    "dinheiro frente fora depois cima sabe corpo conta tempo coisa parte".split())

_EXPRESSOES: Optional[frozenset] = None


def _carregar_expressoes() -> frozenset:
    """As palavras que denunciam uma expressao popular no texto.

    De cada expressao guarda a palavra DISTINTIVA: "barriga" em empurrar com a
    barriga, "balde" em chutar o balde, "tranco" em aguentar o tranco. E quase
    sempre o substantivo, entao os verbos no infinitivo saem da disputa - a
    primeira versao pegava a palavra mais longa e escolhia "empurrar" em vez de
    "barriga", justamente a metade que nao tem graca nenhuma sozinha.

    Guardar o substantivo tambem resolve a conjugacao: "empurrando com a
    barriga" continua tendo barriga.
    """
    global _EXPRESSOES
    if _EXPRESSOES is not None:
        return _EXPRESSOES
    try:
        texto = (DIR_PROMPTS / "carta.txt").read_text(encoding="utf-8")
    except Exception:
        _EXPRESSOES = frozenset()
        return _EXPRESSOES
    bloco = _RE_BANCO.search(_sem_acento(texto))
    if not bloco:
        _EXPRESSOES = frozenset()
        return _EXPRESSOES
    fora = set()
    for linha in bloco.group(1).split("\n"):
        if "\u00b7" not in linha and "·" not in linha:
            continue
        for frase in re.split(r"[\u00b7·]", linha):
            palavras = [w for w in re.findall(r"[a-z]{4,}", frase.lower())
                        if w not in _VAZIAS]
            if not palavras:
                continue
            # o substantivo manda; o infinitivo so serve se nao sobrar mais nada
            nomes = [w for w in palavras if not w.endswith(("ar", "er", "ir"))]
            escolha = max(nomes or palavras, key=len)
            if escolha not in _COMUNS_DEMAIS:
                fora.add(escolha)
    _EXPRESSOES = frozenset(fora)
    return _EXPRESSOES


def auditar_expressao(carta: dict) -> list[str]:
    """A carta inteira sem nenhuma expressao popular. Vazia = pode mostrar."""
    if not isinstance(carta, dict):
        return []
    marcas = _carregar_expressoes()
    if not marcas:
        return []          # banco sumiu do prompt: nao inventa exigencia

    texto = _sem_acento(" ".join(_frases_da_carta(carta))).lower()
    palavras = set(re.findall(r"[a-z]{4,}", texto))
    # carta vazia ou truncada nao e problema de ESTILO: quem cuida disso e a
    # checagem de estrutura. Cobrar expressao de um texto que nao existe so
    # acrescentaria um problema falso a lista de correcao.
    if len(palavras) < 10:
        return []
    if palavras & marcas:
        return []
    return ["a carta inteira nao tem uma expressao popular brasileira. Use UMA, "
            "do banco do prompt, de preferencia no primeiro paragrafo ou no "
            "destaque: empurrar com a barriga, segurar a barra, dar tiro no "
            "escuro, chutar o balde, virar a pagina, se virar nos trinta. Sem "
            "ela o texto fica correto e morno, tipo manual."]
