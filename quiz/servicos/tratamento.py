# -*- coding: utf-8 -*-
"""Como falar com a pessoa: o nome dela e a concordancia certa.

O quiz nunca perguntou o genero, e perguntar seria mais um campo antes da
venda. Mas o portugues cobra concordancia em quase toda frase sobre alguem
("voce ja ficou BOM demais nisso"), e errar isso derruba a leitura inteira: um
leitor recebeu a carta toda no feminino e a primeira coisa que ele viu foi que
o texto nao fazia ideia de quem ele era.

A causa nao era so a falta do dado. O proprio prompt chamava a leitora de
"ela" setenta e seis vezes contra dezessete "ele", e o modelo espelhava isso.

Entao aqui ha duas defesas:

  1. O primeiro nome quase sempre diz, em portugues brasileiro, e este modulo
     le isso com regras de terminacao mais uma lista de excecoes.
  2. Quando NAO da para ter certeza, a resposta e None - e o prompt recebe a
     ordem de escrever sem marcar genero, que e sempre melhor do que chutar.

Funcao pura, sem rede e sem dependencia: da para testar com uma lista de nomes.
"""
from __future__ import annotations

import unicodedata
from typing import Optional

MASCULINO = "m"
FEMININO = "f"


def _limpo(nome: str) -> str:
    """Primeiro nome, sem acento, em minuscula."""
    n = (nome or "").strip().split()
    if not n:
        return ""
    base = unicodedata.normalize("NFD", n[0])
    return "".join(c for c in base if unicodedata.category(c) != "Mn").lower()


# Terminam em -a e sao masculinos. Lista curta de proposito: nomes assim sao
# raros no Brasil, e inchar a lista so aumenta a chance de errar para o outro
# lado.
MASC_EM_A = frozenset("""
luca juca noa barnaba nicola dica tiaga
""".split())

# Terminam em consoante ou -o e sao femininos. Esta lista precisa ser mais
# generosa: e o caso que mais aparece, e chamar uma Raquel de "ele" e o erro
# mais visivel que a carta pode cometer.
FEM_EM_CONSOANTE = frozenset("""
ester esther raquel rachel isabel mabel cristal jasmin karen karin kelen
miriam mirian iris beatriz ruth judith elizabeth elisabeth lilian gisel
yasmin iasmin jasmim carmem ines lais tais thais luz mel
jaqueline? ines agnes lourdes mercedes dulcineis carmen solange? heloise
soraia? liz maribel marisol nicol nicole? noemi? sol
""".replace("?", "").split())

# Terminam em -e, -i, -u ou -y: a terminacao nao decide, entao so a lista
# decide. Fora dela a resposta e None e o texto sai sem marcar genero.
FEM_OUTROS = frozenset("""
adriane ariane bruna? clarice alice beatrice denise elaine eloise eveline
ivone ivete janaine? josiane juliane luane mercedes rosane simone silvane
suzane taine viviane yasmine amanda? gabriele daniele michele rafaele
nataly emilly kelly sally ellen? abegail
""".replace("?", "").split())

FEM_OUTROS = frozenset(x for x in FEM_OUTROS if x)

MASC_OUTROS = frozenset("""
alexandre andre felipe filipe henrique jorge vicente clemente jaime
daniel gabriel rafael israel manuel miguel samuel ariel
davi levi eli noe ze the
""".split())


def genero_do_nome(nome: str) -> Optional[str]:
    """MASCULINO, FEMININO, ou None quando nao da para saber com seguranca.

    None NAO e falha: e a resposta honesta, e o prompt sabe o que fazer com
    ela. Chutar concordancia e pior do que escrever sem marcar.
    """
    n = _limpo(nome)
    if len(n) < 2:
        return None

    if n in MASC_EM_A:
        return MASCULINO
    if n in FEM_EM_CONSOANTE or n in FEM_OUTROS:
        return FEMININO
    if n in MASC_OUTROS:
        return MASCULINO

    # -a e o sinal mais forte do portugues brasileiro
    if n.endswith("a"):
        return FEMININO
    # -o e -ao, idem do outro lado
    if n.endswith("o"):
        return MASCULINO
    # consoantes que quase sempre fecham nome masculino
    if n[-1] in "rlnzms":
        return MASCULINO
    # -e, -i, -u, -y nao decidem nada sozinhos
    return None


def bloco_tratamento(primeiro_nome: str) -> str:
    """A instrucao de tratamento que vai junto com os FATOS."""
    g = genero_do_nome(primeiro_nome)
    nome = (primeiro_nome or "").strip()

    if g == MASCULINO:
        regra = (f"{nome} e HOMEM. Toda concordancia sobre ele no masculino: "
                 "'voce ja ficou BOM demais nisso', 'voce esta cansaDO', "
                 "'sozinHO'. NUNCA escreva no feminino.")
    elif g == FEMININO:
        regra = (f"{nome} e MULHER. Toda concordancia sobre ela no feminino: "
                 "'voce ja ficou BOA demais nisso', 'voce esta cansaDA', "
                 "'sozinHA'. NUNCA escreva no masculino.")
    else:
        regra = (f"NAO DA PARA SABER o genero de {nome} pelo nome. Entao "
                 "ESCREVA SEM MARCAR GENERO NENHUM sobre a pessoa. Nao use "
                 "adjetivo ou participio que mude com o genero ('cansado', "
                 "'sozinha', 'pronto', 'presa'). Reescreva a frase: em vez de "
                 "'voce ficou bom demais nisso', 'voce ja pegou o jeito "
                 "disso'; em vez de 'voce esta cansada', 'o cansaco ja "
                 "apareceu'. Isso e sempre possivel e ninguem percebe.")

    return (f"como chamar: {nome}\n"
            f"concordancia: {regra}")
