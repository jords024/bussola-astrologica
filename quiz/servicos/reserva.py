# -*- coding: utf-8 -*-
"""A carta de reserva, escrita à mão e preenchida com os fatos reais.

Entra quando o modelo cai, estoura o timeout ou reprova na auditoria duas vezes.
A leitora nunca vê erro e o funil nunca tem beco sem saída: ela passou por oito
telas para chegar aqui.

Construída a partir dos MESMOS fatos calculados, nunca de texto genérico. Por
isso passa na auditoria por construção, e ainda assim fala do mapa dela de
verdade. A prosa é mais dura que a do modelo. A astrologia é igualmente exata.
"""
from __future__ import annotations

from typing import Optional

from .nomes import ASPECTO_HUMANO, CASA_VIDA, PLANETA_VIDA
from .veredito import CAUSA_OCULTA, CONFIRMACAO, DESLOCAMENTO

AREA_ASSUNTO = {
    "dinheiro": "dinheiro",
    "amor": "seus vínculos",
    "carreira": "seu trabalho",
    "casa": "sua casa",
    "corpo": "seu corpo e sua rotina",
    "caminhos": "sua direção",
}

AREA_FOCO = {
    "dinheiro": "rever um número que você aceitou quando valia menos do que vale hoje",
    "amor": "observar o que costuma ser aceito no começo e cobrado no fim",
    "carreira": "ocupar formalmente um lugar que você já ocupa informalmente",
    "casa": "nomear o que se repete e decidir o que se carrega e o que se devolve",
    "corpo": "mudar uma coisa pequena e sustentável, não a rotina inteira",
    "caminhos": "testar uma direção nova em escala pequena, antes de virar a mesa",
}

AREA_SOLTAR = {
    "dinheiro": "trabalhar mais horas esperando que o volume resolva",
    "amor": "começar algo novo para não olhar para o que já existe",
    "carreira": "provar competência entregando ainda mais",
    "casa": "resolver com logística o que é de outra ordem",
    "corpo": "adiar o que o corpo vem sinalizando há meses",
    "caminhos": "exigir de si uma resposta definitiva sobre propósito",
}

# A frase que a pessoa releria. Na reserva ela e fixa por area, mas continua
# sem nenhum termo de astrologia, como a do modelo.
DESTAQUE = {
    "dinheiro": "Fase de ajuste raramente pede mais volume. Costuma pedir um preço revisto.",
    "amor": "Quando muda a pessoa e o final é o mesmo, o padrão costuma ser mais antigo que a relação.",
    "carreira": "Reconhecimento raramente vem de entregar mais. Costuma vir de ocupar o lugar por inteiro.",
    "casa": "O que se repete em família costuma aliviar no dia em que finalmente ganha nome.",
    "corpo": "O corpo costuma avisar bem antes de gritar, e o aviso é sempre pequeno.",
    "caminhos": "Direção não aparece como resposta pronta. Aparece como um passo que dá para dar agora.",
}

TITULO = {
    "dinheiro": "reorganizar antes de expandir",
    "amor": "ver o padrão antes de escolher de novo",
    "carreira": "assumir a posição, não a tarefa",
    "casa": "nomear o que vem de antes",
    "corpo": "ajustar antes que grite",
    "caminhos": "escolher a rota, não o destino",
}


def montar(fatos: dict, veredito, quiz: dict, precisao: dict) -> dict:
    area = quiz.get("area") or "caminhos"
    assunto = AREA_ASSUNTO.get(area, "sua direção")
    casas_ok = bool(precisao.get("casas_confiaveis"))
    ap = fatos.get("aspecto_principal") or {}

    p: list[str] = []

    # 1 - onde ela está, em fato puro
    if ap:
        # mesma regra da carta do modelo: nenhum termo de astrologia no corpo.
        # A prova tecnica vai na nota ao pe, montada por fatos.nota_tecnica().
        chega = PLANETA_VIDA.get(ap["transito"], "algo que vem de fora")
        toca = PLANETA_VIDA.get(ap["natal"], "uma parte sua")
        humano = ASPECTO_HUMANO.get(ap["aspecto"], "")
        chegando = ("ainda está se aproximando, então tende a apertar mais"
                    if ap["movimento"] == "Applying"
                    else "já passou do ponto mais forte, e agora é assimilar")
        onde = ""
        if casas_ok and ap.get("casa_transito"):
            onde = (" E isso pesa mais num lugar específico: "
                    f"{CASA_VIDA.get(ap['casa_transito'],'')}.")
        # as descricoes de PLANETA_VIDA e CASA_VIDA sao oracoes, nao sintagmas.
        # Entram por aposicao com dois-pontos; depois de preposicao sairia
        # "encosta em a parte que sente".
        p.append(
            f"Neste momento há um encontro entre duas forças suas. De um lado, "
            f"{chega}. Do outro, {toca}. As duas estão {humano}, e esse encontro "
            f"{chegando}.{onde}"
        )
        if ap.get("retrogrado"):
            p.append(
                "O que se move está voltando sobre o próprio caminho. Isso não é um "
                "problema, é um recado sobre o verbo: esta fase costuma render mais "
                "em rever, retomar e renegociar do que em começar do zero."
            )
    else:
        p.append(
            f"O céu de hoje está encostando no céu do dia em que você nasceu, e é sobre "
            f"{assunto} que essa conversa está acontecendo agora."
        )

    # 2 - o cenário, que é o que dá o valor da leitura
    if not casas_ok:
        p.append(f"Você escolheu olhar para {assunto}. Sem a hora exata, essa escolha orienta o assunto da carta; os aspectos entre os planetas dão o recorte, sem apontar uma casa específica.")
    elif veredito.cenario == CONFIRMACAO:
        p.append(
            f"Você escolheu olhar para {assunto}, e é exatamente aí que o movimento está "
            "mais forte agora. Não é coincidência bonita, é o que o cálculo mostrou."
        )
    elif veredito.cenario == DESLOCAMENTO:
        viz = CASA_VIDA.get(veredito.casa_aberta, "") if casas_ok else ""
        extra = f" Ele está aqui: {viz}." if viz else ""
        p.append(
            f"Você olhou para {assunto}. O movimento mais forte está meio passo ao "
            f"lado, numa área que conversa diretamente com essa.{extra} "
            "Costuma ser por ali que a resposta aparece."
        )
    else:
        outra = CASA_VIDA.get(veredito.casa_aberta, "") if casas_ok else ""
        extra = f" Ele está aqui: {outra}." if outra else ""
        p.append(
            f"Você veio falar de {assunto}, e faz sentido ter vindo. Só que o que "
            f"está mais forte agora está em outro lugar.{extra} Costuma acontecer de "
            "uma coisa estar consumindo a energia da outra sem que ninguém perceba."
        )

    # 3 - onde colocar energia
    p.append(
        f"Nas próximas semanas, o esforço tende a render mais em "
        f"{AREA_FOCO.get(area, AREA_FOCO['caminhos'])}. É pequeno e é concreto, e é "
        "geralmente assim que fase de ajuste se resolve."
    )

    # 4 - o que não rende, calibrado pela resposta sobre insistência
    duro = quiz.get("quebra") == "muitas"
    abertura = "O que tende a não render agora é" if duro else "O que talvez não renda tanto agora é"
    p.append(
        f"{abertura} {AREA_SOLTAR.get(area, AREA_SOLTAR['caminhos'])}. "
        "Quando o céu pede revisão, insistir no volume costuma cansar sem mover."
    )

    # 5 - fecho
    p.append(
        "Nada aqui é sentença. É terreno. Saber em que terreno se está pisando é o que "
        "muda a decisão da semana."
    )

    espera = None
    if casas_ok and veredito.casa_fechada:
        espera = ("O que mais pede espera neste momento: "
                  f"{CASA_VIDA.get(veredito.casa_fechada,'')}.")
        if veredito.casa_fechada == 6:
            espera = "Evite sobrecarregar a rotina com mais tarefas. Cuidados de saúde não devem esperar por uma leitura astrológica."

    return {
        "titulo": TITULO.get(area, TITULO["caminhos"]),
        "destaque": DESTAQUE.get(area, DESTAQUE["caminhos"]),
        "paragrafos": p,
        "espera": espera,
        "janela": fatos.get("janela") or "nas próximas semanas",
    }
