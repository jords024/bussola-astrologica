"""Os pesos que decidem qual porta esta aberta.

Fica num modulo separado e versionado de proposito: mexer em um numero aqui
muda o veredito de muita gente. PESOS_V vai gravado em todo log, senao nao da
para comparar conversao antes e depois de um ajuste.
"""

PESOS_V = 1

# quanto mais lento o planeta, mais ele estrutura a vida
PESO_TRANSITO = {
    "Pluto": 10, "Neptune": 9, "Uranus": 9, "Saturn": 8, "Jupiter": 6,
    "Mars": 3, "Sun": 3, "Venus": 2, "Mercury": 2, "Moon": 1,
}

# quanto mais pessoal o ponto tocado, mais a pessoa sente na pele
PESO_NATAL = {
    "Sun": 10, "Moon": 10, "Ascendant": 10, "Medium_Coeli": 9,
    "Venus": 5, "Mars": 5, "Mercury": 4, "Saturn": 4, "Jupiter": 4,
}

# o tipo de conversa entre os dois
PESO_ASPECTO = {
    "conjunction": 10, "opposition": 8, "square": 8, "trine": 6, "sextile": 4,
}

# o que esta chegando pesa mais que o que ja passou
PESO_MOVIMENTO = {"Applying": 1.30, "Static": 1.10, "Separating": 0.65}

# planetas pesados o bastante para caracterizar resistencia
PESADOS = ("Saturn", "Pluto", "Neptune")

# presenca: planeta lento parado numa casa ja vale por si
MULT_PRESENCA = 4

# a casa natal do ponto tocado recebe menos que a casa pisada pelo transito
MULT_CASA_NATAL = 0.8

# O orbe de verdade de cada aspecto. Continua mandando na PONTUACAO mesmo
# depois de pedirmos 10 graus para a Kerykeion: normalizar tudo por 10 faria
# uma quadratura de 7 graus valer quase como uma exata.
ORBES_CANONICOS = {"conjunction": 10.0, "opposition": 10.0, "trine": 8.0,
                   "sextile": 6.0, "square": 5.0}

# ---- Parte 1: o que faz um transito ser DELA, e nao de todo mundo ----
# Nada aqui e ordem fixa de planeta. Cada fator olha para o mapa da pessoa.
MULT_REGENTE = 1.75   # o transitante rege o signo do Sol, da Lua ou do Asc
MULT_ESTACAO = 1.50   # planeta quase parado: estaciona em cima do ponto dela
VEL_ESTACIONARIO = 0.012   # graus/dia abaixo disto ja e estacao
PESO_ANGULAR = 0.60   # quanto a proximidade de um angulo reforca Sol ou Lua
