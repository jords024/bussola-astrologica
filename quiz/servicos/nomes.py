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

# Como explicar o aspecto para quem nunca abriu um mapa.
# Registro: conversa de bar, nao ensaio literario. O modelo ECOA o registro
# deste arquivo, entao "em atrito, pedindo trabalho" volta como "esta pedindo
# contorno" e a carta sai poetica. Escreva como o Crassus fala.
ASPECTO_HUMANO = {
    "conjunction": "em cima, misturado, sem separacao",
    "opposition": "puxando para os dois lados, e voce no meio",
    "square": "batendo de frente, da trabalho",
    "trine": "a favor, sai facil",
    "sextile": "tem chance, mas so se voce for atras",
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
    "Sun": "quem voce e, e a vontade de ser levado a serio",
    "Moon": "o que voce sente antes de pensar, e a necessidade de se sentir seguro",
    "Mercury": "a cabeca: conversa, mensagem, combinado, decisao",
    "Venus": "gosto, afeto, dinheiro e o quanto voce se da valor",
    "Mars": "a vontade de agir, de brigar, de comecar e de ir atras",
    "Jupiter": "o que aumenta, da espaco e abre porta",
    "Saturn": "a cobranca: prova, prazo e responsabilidade, e a demora que vem junto",
    "Uranus": "a virada de repente: cansou, nao aguenta mais o mesmo e quer liberdade",
    "Neptune": "a falta de clareza: cansaco sem motivo, e imaginar no lugar de saber",
    "Pluto": "a reviravolta funda: o que acaba de vez e nao tem volta",
    "Ascendant": "o jeito como voce chega e como te veem antes de voce falar",
    "Medium_Coeli": "o lugar que voce ocupa aos olhos dos outros",
}

CASA_VIDA = {
    1: "você mesma, seu corpo, sua presença e o jeito como chega nos lugares",
    2: "o que você tem, o quanto cobra e o quanto acha que vale",
    3: "as conversas do dia a dia, as mensagens, os combinados curtos, o vaivém com quem está perto",
    4: "a casa, a família, o que vem de antes e o que se herda sem escolher",
    5: "o que você cria, a diversão, o namoro e o que você faz por gosto",
    6: "a rotina, o trabalho de todo dia, o corpo e o cuidado que ele pede",
    7: "os vínculos de igual para igual: quem escolhe você e quem você escolhe",
    8: "o que é dividido com alguém: dívida, herança, dinheiro que depende do outro, e o assunto que ninguém toca",
    9: "estudo, viagem, fé, e a vontade de ver mais longe que o mês que vem",
    10: "a carreira, o lugar público, o que você constrói para ser visto",
    11: "os grupos, as amizades, e o futuro que você quer alcançar",
    12: "o bastidor: o que você resolve sozinho, longe de todo mundo",
}

# ---- Parte 2: o que se abre em cada porta, e o que pede cuidado ----
# Sem este dicionario o modelo escreve "aproveite a energia da casa 5" e a
# leitura vira horoscopo. Com ele, ele tem materia concreta para traduzir: o
# que da para FAZER na segunda-feira, e onde a mesma energia atrapalha.
# O primeiro item e a oportunidade, o segundo e o cuidado.
CASA_PORTA = {
    1: ("aparecer, tomar a frente, mudar algo no visual ou no jeito de se "
        "apresentar, comecar o que depende so de voce",
        "atropelar os outros na pressa de se afirmar"),
    2: ("cobrar o que vale, renegociar preco, organizar as contas, comprar "
        "ou vender o que estava parado",
        "confundir seguranca com acumular, ou gastar para se sentir melhor"),
    3: ("mandar a mensagem que estava parada, retomar contato, estudar algo "
        "curto, resolver combinados e burocracia do dia a dia",
        "falar demais e fechar de menos; dispersar em mil assuntos"),
    4: ("cuidar da casa, aproximar-se da familia, resolver o que ficou "
        "pendente com quem veio antes, criar uma base para recuar",
        "se recolher tanto que o resto da vida para"),
    5: ("criar, se expor, namorar, brincar, mostrar o trabalho, fazer pelo "
        "gosto e nao pela obrigacao",
        "querer plateia para tudo, ou se cansar quando o aplauso demora"),
    6: ("ajustar a rotina, cuidar do corpo, melhorar o metodo de trabalho, "
        "resolver o detalhe que trava o resto",
        "virar refem da lista de tarefas e chamar isso de produtividade"),
    7: ("conversar com quem importa, fechar parceria, alinhar expectativa, "
        "definir o que estava no ar entre voce e alguem",
        "ceder demais para manter a paz, e chamar isso de acordo"),
    8: ("acertar o que e dividido, renegociar divida, encerrar o que ja "
        "acabou, falar do que costuma ficar sem nome",
        "remoer em vez de resolver; transformar intimidade em cobranca"),
    9: ("estudar, viajar, publicar, procurar sentido, olhar mais longe do "
        "que o mes que vem",
        "trocar a decisao concreta por um plano grande que nunca comeca"),
    10: ("aparecer no trabalho, pedir o que merece, assumir o passo publico, "
         "deixar claro onde quer chegar",
         "medir o proprio valor so pelo que os outros reconhecem"),
    11: ("procurar gente, entrar num grupo, pedir ajuda na rede, comecar o "
         "que so anda com mais de uma pessoa",
         "diluir o proprio projeto no projeto de todo mundo"),
    12: ("descansar de verdade, fechar ciclos em silencio, cuidar do que "
         "ninguem ve, terapia, sono, o bastidor",
         "sumir do mundo e chamar de recolhimento o que e fuga"),
}


# ---- Parte 2: o que cada planeta rapido torna DISPONIVEL na porta ----
# O curso de transitos do Crassus e organizado exatamente assim: quatro
# planetas rapidos, doze casas, e em cada aula o que aquilo ativa na vida real,
# como aparece no dia a dia, o que fazer e o que evitar.
#
# O ponto que o curso deixa claro e que aqui estava errado: a porta NUNCA e uma
# area que cede. E onde existe luz, movimento e energia disponivel agora. O Sol
# "coloca um holofote"; Mercurio deixa a area "mais movimentada mentalmente";
# Venus mostra "onde a vida esta ficando mais agradavel"; Marte mostra "onde
# existe mais energia disponivel". Nenhum deles cede: todos oferecem.
#
# O primeiro item e o que fica disponivel, o segundo e onde a mesma energia
# atrapalha.
PLANETA_PORTA = {
    "Sun": ("o holofote do mes esta ai: e o assunto que puxa a atencao, com "
            "mais energia, clareza e vontade de tomar a frente",
            "querer resolver tudo de uma vez e fazer daquilo o unico assunto"),
    "Mercury": ("a cabeca esta ai: e a vez de conversar, perguntar, negociar, "
                "comparar precos e resolver o que e de papel e de combinado",
                "pensar mais rapido que a realidade: falar muito e fechar pouco"),
    "Venus": ("ali esta mais leve e com menos resistencia: gente se aproxima, "
              "conversa flui, e vale cuidar, valorizar e cobrar o que merece",
              "escolher o conforto e adiar o que precisa ser enfrentado"),
    "Mars": ("a forca esta ai: da para comecar, cortar, disputar e destravar o "
             "que estava parado ha tempo",
             "descarregar no impulso e criar atrito onde nao precisava"),
}

# Vem direto do curso e muda o TOM das acoes: "enquanto Marte empurra, Venus
# aproxima; enquanto Marte conquista, Venus atrai". Recomendar que ela va para
# cima numa semana de Venus, ou que espere acontecer numa semana de Marte, e
# errar o conselho mesmo acertando a area.
PLANETA_MODO = {
    "Mars": ("MODO EMPURRAR. As acoes sao de ir atras, cortar, comecar e "
             "disputar. Aqui esperar acontecer e desperdicar a semana."),
    "Venus": ("MODO ATRAIR. As acoes sao de criar condicao favoravel, cuidar, "
              "valorizar e se abrir. Forcar aqui estraga: o proprio Crassus "
              "ensina que enquanto Marte empurra, Venus aproxima."),
    "ambos": ("Marte E Venus estao na mesma area: da para ir atras e da para "
              "atrair. Escolha o modo conforme o que ela trouxe, e nao misture "
              "os dois na mesma acao."),
}
