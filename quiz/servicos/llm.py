# -*- coding: utf-8 -*-
"""A chamada ao agente que escreve a carta.

Saída estruturada por JSON Schema: o servidor obriga o formato, então não há
parsing por regex nem seção faltando. É a diferença em relação ao Sirius, que
parseia marcadores ===SECAO:=== e precisa de uma função inteira para recuperar
seções que vieram vazias.

O modelo NÃO escreve saudação, selo nem assinatura. Esses são fato puro,
compostos em código, e cada campo que sai da mão do modelo é uma superfície a
menos para alucinação.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Optional

from openai import AsyncOpenAI

from config import (DIR_PROMPTS, MAX_TOKENS_SAIDA, MODELOS, OPENAI_API_KEY,
                    ORCAMENTO_LLM, RACIOCINIO, RESERVA_REGENERACAO,
                    TIMEOUT_LLM)
from . import reserva
from .verificacao import (auditar, auditar_destaque, auditar_exemplos,
                          auditar_expressao,
                          auditar_porta, auditar_recitacao,
                          auditar_registro, auditar_simplicidade,
                          texto_da_carta)

logger = logging.getLogger(__name__)

MAX_TENTATIVAS = 2

ESQUEMA = {
    "name": "carta_bussola",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["titulo", "destaque", "identificacao", "porta", "janela"],
        "properties": {
            "titulo": {
                "type": "string",
                "description": "4 a 7 palavras, minusculas, sem ponto final, comecando por VERBO: a COISA que ela faz agora. Concreto e falado, nada de conceito. Ex: cobrar o que ficou combinado. PROIBIDO: dar nome ao que pesa, revisar o padrao, acolher o proprio ritmo.",
            },
            "destaque": {
                "type": "string",
                "description": "UMA frase completa, de 8 a 16 palavras, que a pessoa releria e mandaria para uma amiga. PUXA PARA A FRENTE: nomeia uma capacidade que ela ja tem ou uma porta aberta agora, nunca um diagnostico e nunca uma negacao. TESTE EM VOZ ALTA: se soar como reuniao de empresa ou trabalho de faculdade, esta errado. PROIBIDO hipotese, validar, alinhar, processo, jornada, estruturar, otimizar, mapear, engajar, mindset, performance. Pode ter dente e ser acida, mas nao pode deixar a pessoa sem o que fazer. DIFERENTE do titulo: o titulo e a direcao em forma de verbo, o destaque e uma sentenca inteira. TEM QUE CARREGAR ALGO QUE SO EXISTE NO MAPA DESTA PESSOA ou na frase que ela escolheu no quiz - a cena do primeiro paragrafo, o assunto concreto do transito. Se couber na carta de outra pessoa, esta errada. PROIBIDO proverbio, verdade universal e frase de autoajuda. Sem jargao, sem nome de planeta, sem numero de casa. Nao repita literalmente nenhum paragrafo.",
            },
            "identificacao": {
                "type": "object",
                "additionalProperties": False,
                "required": ["abertura", "paragrafos"],
                "description": "PARTE 1. O que esta acontecendo com ela. So identificacao: nada de conselho aqui.",
                "properties": {
                    "abertura": {
                        "type": "string",
                        "description": "A RECEPCAO: a primeira frase que ela le depois de esperar o calculo, ate 12 palavras. RECEBE antes de diagnosticar - mostra que voce olhou para a vida DELA, nao para uma tabela. Tem duas metades: o que esta acontecendo, e um sinal curto de que aquilo FAZ SENTIDO. A segunda metade VALIDA O ESFORCO, nunca anuncia o estrago ('e esta certo em conferir', 'e ja ficou bom demais nisso', 'porque ela mudou de preco'). A primeira metade pode ser dura; a segunda nunca e. Nao repita a mesma palavra de enfase nas duas. PROIBIDA a formula 'X esta virando Y' - substantivo abstrato, verbo de transformacao, substantivo abstrato - troque por uma coisa que aconteceu. Comeca por 'Voce' ou pelo assunto concreto. PROIBIDO comecar por 'O que', 'Voce tende a', 'E comum que', 'Talvez'. Descreva terreno, nunca prometa resultado. Sem jargao e sem poesia.",
                    },
                    "paragrafos": {
                        "type": "array",
                        "minItems": 3,
                        "maxItems": 3,
                        "items": {"type": "string"},
                        "description": "EXATAMENTE TRES, de no maximo 55 palavras cada. O NOME DA PESSOA APARECE UMA VEZ no corpo inteiro da carta (duas no maximo), onde o Crassus falaria o nome de quem esta na frente dele para marcar o ponto: 'Olha, Jordao: o que acabou nao precisa de mais uma explicacao.' Tres ou mais vira mala direta. A CONCORDANCIA de genero vem da linha 'concordancia' nos FATOS e NUNCA se chuta; quando ela mandar escrever sem marcar genero, reescreva a frase em vez de adivinhar. A CARTA PRECISA DE PELO MENOS UMA EXPRESSAO POPULAR BRASILEIRA - 'empurrar com a barriga', 'segurar a barra', 'dar tiro no escuro', 'chutar o balde', 'virar a pagina' - de preferencia no primeiro paragrafo ou no destaque, e no maximo duas na carta inteira. Sem isso o texto sai correto e morno, tipo manual. A expressao tem que dizer o assunto com MAIS precisao, nao com mais enfeite. CADA UM PRECISA DE UMA ANCORA CONCRETA - um objeto, uma hora do dia, um numero, uma fala entre aspas, um lugar - senao e definicao disfarcada. E PROIBIDO RECITAR A DEFINICAO DA AREA que veio nos FATOS: ela diz DE QUE ASSUNTO se trata, nao e vocabulario. Escolha UMA coisa dela e conte o que acontece com esta pessoa. O PRIMEIRO e a cena da semana dela MAIS A VIRADA, dentro da AREA DA VIDA que os FATOS marcaram como ONDE isso esta acontecendo: a situacao concreta e a consequencia que ela nao tinha ligado aquela situacao. ELE TERMINA NO QUE AQUILO REVELA DELA, NUNCA NO QUE AQUILO CUSTA - a cena pode ser dura, o fecho nao pode ser derrota. Lista de tres coisas que ela faz nao serve - precisa ter um porem. E o paragrafo mais importante da carta. O SEGUNDO e ONDE A CARTA VIRA: mostra o que esse aperto esta CONSTRUINDO nela. Os FATOS trazem dois movimentos lentos ao mesmo tempo - a leitura fraca chama isso de conflito e descreve a pessoa dividida e travada; esta leitura diz que sao duas forcas dela CRESCENDO juntas, e por isso se esbarrando. Continua cena concreta com hora, objeto ou gesto; o que muda e o sentido. Se os FATOS trazem so um movimento, mostre o que ELE esta desenvolvendo nela. O TERCEIRO e A VIRADA e NAO pode ser so mau presagio: diz QUANDO, usando a data aproximada dos FATOS em linguagem de calendario ('ate meados de novembro', 'daqui a umas tres semanas'), depois PARA QUE ESSE APERTO SERVE - a correcao que ele esta forcando, dita como alivio e nunca como sermao - e so entao O QUE FAZER enquanto a janela esta aberta. Se a pessoa sai deste paragrafo com menos chao do que entrou, esta errado. Nunca nomeie a area da parte 2 nem adiante o conteudo dela. A CARTA NUNCA FALA DE SI MESMA: proibido escrever 'a proxima parte', 'logo abaixo', 'a seguir', 'esta leitura', 'esta carta' - ela esta lendo um texto, nao um indice. Proibido filosofar e proibido soar poetico: palavra curta e comum, do jeito que se fala. PROIBIDO 'o que pesa', 'o que trava', 'aquilo que', 'esta pedindo X', 'dar nome a'.",
                    },
                },
            },
            "porta": {
                "type": "object",
                "additionalProperties": False,
                "required": ["abertura", "paragrafos", "aproveitar", "cuidado"],
                "description": "PARTE 2. A porta aberta agora, e ela e a MELHOR NOTICIA da carta: a area onde existe energia sobrando nesta semana. NUNCA diga que ela olhou para o lugar errado e NUNCA escreva a porta como algo que cede, resta ou sobra.",
                "properties": {
                    "abertura": {
                        "type": "string",
                        "description": "UMA frase de ate 12 palavras que ANUNCIA O QUE ESTA ABERTO, em voz de boa noticia. Nao cite aqui a area que ela escolheu: isso e trabalho do paragrafo. PROIBIDO verbo de concessao (cede, resta, sobra, abrir mao, o jeito e). Sem numero de casa.",
                    },
                    "paragrafos": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 1,
                        "items": {"type": "string"},
                        "description": "UM SO, de 40 a 55 palavras. ABRE COM O ELO: o que esta area entrega CONTRA o aperto descrito na parte 1, usando a linha 'O ELO COM O APERTO DA PARTE 1' que vem nos FATOS. Escreva o ENCONTRO dos dois em cena concreta, nunca uma lista do que a area permite. Depois, por que isso destrava o que ela quer trabalhar, em termos praticos. RESPONDE A FRASE DO ESPELHO que ela escolheu: duas pessoas na mesma casa com frases diferentes nao podem receber o mesmo paragrafo. Nada de explicacao longa: as acoes abaixo fazem o trabalho.",
                    },
                    "aproveitar": {
                        "type": "array",
                        "minItems": 3,
                        "maxItems": 3,
                        "items": {"type": "string"},
                        "description": "TRES acoes, cada uma com no maximo 14 palavras, comecando por VERBO. Coisas que dao para fazer nesta semana e que qualquer pessoa saberia executar sem perguntar nada. ELAS SAEM DA FRASE DO ESPELHO, NAO SO DA CASA: a casa da o territorio, a frase dela decide QUAL acao. Quem disse que da mais do que recebe e quem disse que tem opcoes demais recebem acoes diferentes na mesma casa. Se as tres serviriam para qualquer frase do quiz, esta generica demais.",
                    },
                    "cuidado": {
                        "type": ["string", "null"],
                        "description": "Uma frase de ate 16 palavras sobre onde a mesma energia atrapalha. null quando nao houver cuidado relevante.",
                    },
                },
            },
            "janela": {
                "type": "string",
                "description": "SOMENTE o fragmento de tempo, em minusculas, sem verbo e sem ponto final. Exemplos corretos: 'ate meados de marco', 'nas proximas duas ou tres semanas'. NAO escreva frase completa. Use a janela estimada que veio nos FATOS.",
            },
        },
    },
}


_cliente: Optional[AsyncOpenAI] = None


def cliente() -> AsyncOpenAI:
    global _cliente
    if _cliente is None:
        _cliente = AsyncOpenAI(api_key=OPENAI_API_KEY, timeout=TIMEOUT_LLM)
    return _cliente


def _sistema() -> str:
    return Path(DIR_PROMPTS / "carta.txt").read_text(encoding="utf-8")


def montar_user(fatos: dict, correcao: Optional[list[str]] = None) -> str:
    partes = [
        "<PARTE_1_IDENTIFICACAO>", fatos.get("bloco_identificacao", ""),
        "</PARTE_1_IDENTIFICACAO>", "",
        "<PARTE_2_PORTA>", fatos.get("bloco_porta", ""),
        "</PARTE_2_PORTA>", "",
        "<QUIZ>", fatos["bloco_quiz"], "</QUIZ>", "",
    ]
    if correcao:
        partes += [
            "<CORRECAO>",
            "A tentativa anterior citou coisa que NAO existe no mapa dela:",
            *(f"  - {c}" for c in correcao),
            "Reescreva usando apenas o que esta em FATOS.",
            "</CORRECAO>", "",
        ]
    partes.append("Escreva a carta seguindo todas as regras.")
    return "\n".join(partes)


async def _chamar(modelo: str, sistema: str, usuario: str,
                  esforco: Optional[str] = None) -> dict:
    kwargs = dict(
        model=modelo,
        messages=[{"role": "system", "content": sistema},
                  {"role": "user", "content": usuario}],
        response_format={"type": "json_schema", "json_schema": ESQUEMA},
        max_completion_tokens=MAX_TOKENS_SAIDA,
    )
    try:
        r = await cliente().chat.completions.create(
            reasoning_effort=esforco or RACIOCINIO, **kwargs)
    except TypeError:
        r = await cliente().chat.completions.create(**kwargs)
    except Exception as e:
        # modelos sem reasoning_effort devolvem 400 em vez de TypeError
        if "reasoning" in str(e).lower():
            r = await cliente().chat.completions.create(**kwargs)
        else:
            raise
    escolha = r.choices[0]
    # quanto do teto o raciocinio comeu: e o numero que decide se da para subir
    # o esforco de novo, ou se o teto e que precisa subir antes.
    uso = getattr(r, "usage", None)
    if uso is not None:
        det = getattr(uso, "completion_tokens_details", None)
        logger.info("%s (%s): %s tokens de saida, %s de raciocinio, teto %s",
                    modelo, esforco or RACIOCINIO,
                    getattr(uso, "completion_tokens", "?"),
                    getattr(det, "reasoning_tokens", "?"), MAX_TOKENS_SAIDA)
    conteudo = (escolha.message.content or "").strip()
    if not conteudo:
        # 200 com corpo vazio: quase sempre o raciocinio consumiu todo o teto de
        # tokens. Sem esta checagem vira "Expecting value: line 1 column 1" e a
        # causa real fica escondida.
        uso = getattr(r, "usage", None)
        raise RuntimeError(
            f"resposta vazia de {modelo} (finish_reason={escolha.finish_reason}, "
            f"tokens={getattr(uso, 'completion_tokens', '?')}/{MAX_TOKENS_SAIDA}). "
            "Provavelmente o teto de tokens nao cobriu raciocinio + saida."
        )
    return json.loads(conteudo)


async def escrever(fatos: dict, veredito, quiz: dict, precisao: dict) -> dict:
    """Devolve {carta, meta}. Nunca levanta: se tudo falhar, entra a reserva.

    A pessoa passou por oito telas para chegar aqui. O funil não pode ter beco
    sem saída.
    """
    meta = {"modelo": None, "tentativas": 0, "validacao": "reserva", "ms_llm": 0}
    permitido = fatos["permitido"]
    sistema = _sistema()
    correcao: Optional[list[str]] = None
    # a melhor carta ate agora: escrita, com defeito de estilo, mas sem
    # nenhum erro de astrologia. Vale mais do que a reserva de molde.
    ultima_limpa: Optional[dict] = None
    t0 = time.time()

    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY ausente: indo direto para a carta de reserva")
        return {"carta": reserva.montar(fatos, veredito, quiz, precisao), "meta": meta}

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        # O RELOGIO DO NAVEGADOR MANDA. Tentar de novo so vale se houver tempo
        # de a resposta chegar; passando do orcamento, insistir troca uma carta
        # imperfeita por uma tela de erro.
        gasto = time.time() - t0
        if tentativa > 1 and gasto + RESERVA_REGENERACAO > ORCAMENTO_LLM:
            logger.warning("regeneracao nao cabe no orcamento (%.0fs gastos + "
                           "%.0fs de reserva passam de %.0fs): entrego o que ja "
                           "tenho", gasto, RESERVA_REGENERACAO, ORCAMENTO_LLM)
            break
        meta["tentativas"] = tentativa
        usuario = montar_user(fatos, correcao)

        for modelo in MODELOS:
            try:
                # A REGENERACAO NUNCA PODE SER MAIS LENTA QUE A PRIMEIRA.
                #
                # Esta linha ja fixou "medium" na segunda tentativa. Fazia
                # sentido quando a base era "high", onde medium era um freio.
                # Com a base em "low" ela virou o contrario: a primeira
                # passada levava 8s e a regeneracao 30s, e o total estourava o
                # video. A regeneracao ja recebe a lista do que errou, entao e
                # tarefa mais facil - nao precisa de mais raciocinio, precisa
                # de menos tempo.
                esforco = RACIOCINIO
                if tentativa > 1 and RACIOCINIO == "high":
                    esforco = "medium"
                carta = await asyncio.wait_for(
                    _chamar(modelo, sistema, usuario, esforco),
                    timeout=TIMEOUT_LLM)
            except asyncio.TimeoutError:
                logger.warning("modelo %s estourou %ss", modelo, TIMEOUT_LLM)
                continue
            except Exception as e:
                logger.warning("modelo %s falhou: %s", modelo, str(e)[:200])
                continue

            meta["modelo"] = modelo
            corpo = texto_da_carta(carta)
            # duas guardas: nao inventar astrologia, e nao usar jargao no corpo.
            # A prova tecnica vive na nota ao pe da carta, montada por codigo.
            # DURAS: astrologia que nao existe no calculo, e verbo de
            # concessao na porta. Nenhuma das duas pode ir para a tela.
            duras = auditar(corpo, permitido) + auditar_porta(carta)
            # DE ESTILO: tom, repeticao, plagio de exemplo, recitacao. Valem
            # uma regeneracao, mas nao valem o tombo para a reserva.
            estilo = (auditar_simplicidade(corpo)
                      + auditar_registro(carta)
                      + auditar_destaque(carta)
                      + auditar_exemplos(carta)
                      + auditar_recitacao(carta)
                      + auditar_expressao(carta))
            problemas = duras + estilo
            if not problemas:
                meta["validacao"] = "ok" if tentativa == 1 else "regenerado"
                meta["ms_llm"] = int((time.time() - t0) * 1000)
                return {"carta": carta, "meta": meta}

            logger.warning("carta reprovada na auditoria (tentativa %d): %s",
                           tentativa, problemas)
            if not duras:
                ultima_limpa = carta   # serve, se nada melhor aparecer
            correcao = problemas
            break  # troca de tentativa, não de modelo

    meta["ms_llm"] = int((time.time() - t0) * 1000)

    # A RESERVA E O ULTIMO RECURSO, NAO O SEGUNDO.
    #
    # Ela e um texto de molde: recita as definicoes das areas inteiras, porque
    # foi escrita por codigo e nao tem como inventar cena. Cair nela por causa
    # de um problema de TOM e trocar uma carta boa com um defeito por um
    # formulario sem nenhum acerto - e foi exatamente isso que um leitor
    # recebeu: "as conversas do dia a dia, as mensagens, os combinados curtos"
    # copiado do dicionario, porque duas geracoes tinham sido reprovadas no
    # estilo. A carta escrita, mesmo imperfeita, fala da vida dele. A reserva
    # nao fala da vida de ninguem.
    #
    # Entao a reserva so entra quando NAO ha nenhuma carta sem problema duro:
    # astrologia inventada ou verbo de concessao na porta.
    if ultima_limpa is not None:
        logger.warning("reprovada so no estilo: vai a ultima carta escrita, "
                       "e nao a reserva")
        meta["validacao"] = "estilo"
        return {"carta": ultima_limpa, "meta": meta}

    logger.error("duas reprovacoes duras ou falha total: entrando com a reserva")
    return {"carta": reserva.montar(fatos, veredito, quiz, precisao), "meta": meta}
