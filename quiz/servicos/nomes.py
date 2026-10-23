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
    1: "seu posicionamento: sua postura, sua presença e a clareza de como você se coloca no mundo",
    2: "valores e recursos: o que você constrói, a sua remuneração e a valorização da sua entrega",
    3: "comunicação e acordos: conversas diretas, negociações objetivas e alinhamento prático de decisões",
    4: "casa e raízes: sua base íntima, estrutura familiar e o chão seguro onde você recarrega",
    5: "autenticidade e criação: projetos autorais, expressão viva, verdade e o que leva a sua assinatura",
    6: "rotina e métodos: método de trabalho, ritmo prático e a organização que sustenta a sua energia diária",
    7: "parcerias e alianças: acordos de igual para igual, compromissos mútuos e escolhas conscientes",
    8: "transformação e estratégia: cortes estratégicos, gestão de recursos compartilhados e encerramento de ciclos",
    9: "visão e expansão: estratégia de longo prazo, estudo direcionado e ampliação do seu horizonte",
    10: "carreira e autoridade: posicionamento profissional, visibilidade, liderança e reconhecimento do que constrói",
    11: "alianças e futuro: rede de contatos, projetos estratégicos em grupo e portas abertas para os próximos anos",
    12: "bastidores e planejamento: estratégia silenciosa, filtro de ruídos e preparação calculada nos bastidores",
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
    1: ("assumir a frente com firmeza, definir limites inegociáveis, bancar as suas escolhas e projetar autoridade na sua presença",
        "esperar que os outros aprovem suas decisões ou recuar por medo de incomodar"),
    2: ("precificar com firmeza, cobrar o valor justo pelo que entrega, valorizar seus recursos e renegociar acordos materiais",
        "misturar autovalor com escassez ou gastar impulsivamente para aliviar tensão"),
    3: ("abrir conversas diretas, alinhar expectativas com clareza, negociar com objetividade e botar as cartas na mesa",
        "dispersar a atenção em mil assuntos sem fechar o que é prioridade"),
    4: ("organizar a sua base íntima, proteger o seu refúgio, estabelecer acordos claros no ambiente pessoal e criar chão para recuar",
        "isolar-se em ressentimentos antigos ou paralisar as decisões práticas da vida"),
    5: ("assumir sua assinatura única, expor projetos autorais, agir com entusiasmo genuíno e dar espaço para a criação e a verdade",
        "depender de aplauso alheio ou dispersar energia em vaidades passageiras"),
    6: ("organizar o método de trabalho, otimizar processos práticos, cuidar da energia diária e eliminar gargalos que travam o dia",
        "virar refém de perfeccionismo inútil e se sobrecarregar com excesso de tarefas"),
    7: ("fechar acordos claros de igual para igual, alinhar expectativas com transparência e escolher conscientemente quem caminha com você",
        "fazer concessões unilaterais só para evitar atrito e chamar isso de acordo"),
    8: ("renegociar termos estruturais, cortar dependências financeiras ou emocionais, encerrar o que esgotou e renascer com força estratégica",
        "alimentar mágoas em vez de virar a página com pragmatismo e foco"),
    9: ("expandir a visão de longo prazo, estudar o que realmente dá tração, buscar novos mercados e pensar estrategicamente",
        "ficar desenhando planos gigantes no papel sem dar o primeiro passo no chão"),
    10: ("assumir o protagonismo profissional, exigir reconhecimento pelo que entrega, posicionar-se com liderança e definir rumos claros",
         "trabalhar nos bastidores esperando que alguém adivinhe o seu mérito"),
    11: ("ativar a sua rede de alianças, aproximar-se de pessoas que abrem portas, propor projetos conjuntos e olhar para o futuro",
         "diluir sua energia com quem não tem o mesmo nível de compromisso"),
    12: ("filtrar o excesso de ruído externo, fazer o planejamento estratégico nos bastidores e recuperar a clareza mental e o fôlego",
         "usar o recolhimento como desculpa para fugir da ação necessária"),
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
