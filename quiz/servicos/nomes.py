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
    # Aspecto duro nao e castigo: e o que tira do lugar. Quadratura e motor -
    # sem ela ninguem muda nada, so reclama. Dizer so "da trabalho" entregava
    # ao modelo a metade chata da verdade.
    "conjunction": "em cima, misturado: vira o assunto central da vida agora",
    "opposition": "puxando dos dois lados, ate voce achar o jeito de ter os dois",
    "square": "batendo de frente: da trabalho, e e o que faz sair do lugar",
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

# OS LENTOS TEM DOIS LADOS, E OS DOIS VAO PARA O MODELO.
#
# Por muito tempo cada um destes era so um problema: Saturno era "a cobranca e
# a demora que vem junto", Plutao era "o que acaba de vez e nao tem volta".
# Como a Parte 1 e escrita a partir daqui, a carta saia pesada por construcao -
# e nenhuma regra de tom no prompt vencia isso, porque o modelo nao tinha do
# que fazer incentivo. Ele recebia so peso e era mandado animar.
#
# Agora cada um traz o que aperta E o que isso constroi. A leitura continua
# honesta - o aperto esta la, com o nome dele - mas a pessoa sai sabendo para
# onde aquilo leva, que e a leitura que o Crassus faz.
PLANETA_VIDA = {
    "Sun": "quem voce e, e a vontade de ser levado a serio",
    "Moon": "o que voce sente antes de pensar, e a necessidade de se sentir seguro",
    "Mercury": "a cabeca: conversa, mensagem, combinado, decisao",
    "Venus": "gosto, afeto, dinheiro e o quanto voce se da valor",
    "Mars": "a vontade de agir, de brigar, de comecar e de ir atras",
    "Jupiter": "o que aumenta, da espaco e abre porta",
    "Saturn": "a cobranca que constroi: prova, prazo e responsabilidade. Pesa, e e o unico jeito de ganhar a autoridade que ninguem tira "
              "depois, porque foi feita no osso",
    "Uranus": "a virada: cansou do mesmo e quer ar. Sacode, e e ela que devolve "
              "o direito de fazer do seu jeito depois de anos no jeito dos outros",
    "Neptune": "a nevoa que afina a percepcao: imaginar no lugar de saber, e junto "
               "com isso perceber o que ninguem falou em voz alta",
    "Pluto": "a virada funda: o que acabou nao volta. E o que devolve forca, porque "
             "quem larga o que ja morreu para de gastar energia segurando",
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
# O que a pessoa PRECISA quando cada lento esta apertando.
#
# Esta e a peca que ligava a Parte 1 a Parte 2 e nao existia. A carta
# diagnosticava o aperto num bloco e anunciava a porta no outro, sem nunca
# dizer que um responde ao outro - entao a porta parecia assunto novo, e a
# leitura terminava sem caminho. Com isto, a casa aberta deixa de ser
# territorio e vira a saida daquele aperto especifico.
PLANETA_ALIVIO = {
    "Saturn": "chao firme: uma coisa de cada vez, prazo que cabe, e prova de "
              "que ja deu conta antes",
    "Uranus": "espaco para mudar sem quebrar tudo, e permissao para querer "
              "outra coisa sem se explicar",
    "Neptune": "informacao confirmada e coisa escrita: parar de adivinhar e "
               "passar a conferir",
    "Pluto": "encerrar de vez o que ja acabou, em vez de administrar o resto",
}


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
    # "publicar" virava "publique uma hipotese" na carta, que nao e portugues
    # de gente. O sentido e mostrar o proprio trabalho para fora do circulo.
    9: ("estudar de verdade, viajar, mostrar o seu trabalho para gente de fora, "
        "procurar sentido, olhar mais longe do que o mes que vem",
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
