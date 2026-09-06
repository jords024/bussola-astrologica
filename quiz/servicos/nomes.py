# -*- coding: utf-8 -*-
"""Traducao dos literais da Kerykeion para portugues."""

PLANETA_PT = {
    "Sun": "Sol", "Moon": "Lua", "Mercury": "Mercúrio", "Venus": "Vênus",
    "Mars": "Marte", "Jupiter": "Júpiter", "Saturn": "Saturno",
    "Uranus": "Urano", "Neptune": "Netuno", "Pluto": "Plutão",
    "Ascendant": "Ascendente", "Medium_Coeli": "Meio do Céu",
}

SIGNO_PT = {
    "Ari": "Áries", "Tau": "Touro", "Gem": "Gêmeos", "Can": "Câncer",
    "Leo": "Leão", "Vir": "Virgem", "Lib": "Libra", "Sco": "Escorpião",
    "Sag": "Sagitário", "Cap": "Capricórnio", "Aqu": "Aquário", "Pis": "Peixes",
}

ASPECTO_PT = {
    "conjunction": "conjunção", "opposition": "oposição", "square": "quadratura",
    "trine": "trígono", "sextile": "sextil",
}

# como explicar o aspecto para quem nunca abriu um mapa
ASPECTO_HUMANO = {
    "conjunction": "colado, agindo junto",
    "opposition": "de frente, puxando para lados opostos",
    "square": "em atrito, pedindo trabalho",
    "trine": "em fluxo, abrindo sem esforço",
    "sextile": "em oportunidade, se você for atrás",
}

MES_PT = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
          "agosto", "setembro", "outubro", "novembro", "dezembro"]


# ---------------------------------------------------------------------------
# Vocabulario de DESTINO da traducao.
#
# O corpo da carta nao pode citar planeta, casa, signo, orbe nem nome de
# aspecto. Sem um vocabulario para onde traduzir, o modelo simplifica cortando
# conteudo. Com estes dicionarios ele troca o termo tecnico por uma descricao
# de vida que carrega o mesmo significado.
#
# Os nomes tecnicos continuam existindo em PLANETA_PT, SIGNO_PT e CASA_NOME,
# usados no selo e na nota tecnica ao pe da carta.
# ---------------------------------------------------------------------------

PLANETA_VIDA = {
    "Sun": "o que em você quer ser reconhecido do jeito que é",
    "Moon": "a parte que sente antes de entender, e que pede abrigo",
    "Mercury": "o que pensa, fala, combina e interpreta",
    "Venus": "o que atrai, o que agrada e o quanto você se valoriza",
    "Mars": "o que empurra, reage e vai atrás",
    "Jupiter": "o que amplia, dá espaço e abre horizonte",
    "Saturn": "o que cobra estrutura, tempo e prova",
    "Uranus": "o que quebra de repente e não aceita mais o molde",
    "Neptune": "o que dissolve contorno, onde a imaginação preenche o que falta",
    "Pluto": "o que revira por dentro e não aceita mais viver na superfície",
    "Ascendant": "a forma como você chega e é vista antes de falar",
    "Medium_Coeli": "o lugar que você ocupa aos olhos dos outros",
}

CASA_VIDA = {
    1: "você mesma, seu corpo, sua presença e o jeito como chega nos lugares",
    2: "o que você tem, o quanto cobra e o quanto acha que vale",
    3: "as conversas do dia a dia, as mensagens, os combinados curtos, o vaivém com quem está perto",
    4: "a casa, a família, o que vem de antes e o que se herda sem escolher",
    5: "o que você cria, o prazer, o brilho e o que faz por gosto",
    6: "a rotina, o trabalho de todo dia, o corpo e o cuidado que ele pede",
    7: "os vínculos de igual para igual: quem escolhe você e quem você escolhe",
    8: "o que é dividido com outro, o dinheiro que passa pelas mãos alheias, o que é íntimo demais para falar",
    9: "o sentido, a direção, o que amplia o mundo e o que se acredita",
    10: "a carreira, o lugar público, o que você constrói para ser visto",
    11: "os grupos, as amizades, e o futuro que você quer alcançar",
    12: "o bastidor, o silêncio, o que só acontece longe dos olhos",
}
