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

from config import DIR_PROMPTS, MAX_TOKENS_SAIDA, MODELOS, OPENAI_API_KEY, TIMEOUT_LLM
from . import reserva
from .verificacao import (auditar, auditar_destaque, auditar_porta,
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
                "description": "UMA frase completa, de 8 a 16 palavras, que a pessoa releria e mandaria para uma amiga. DIFERENTE do titulo: o titulo e a direcao em forma de verbo, o destaque e uma sentenca inteira. TEM QUE CARREGAR ALGO QUE SO EXISTE NO MAPA DESTA PESSOA ou na frase que ela escolheu no quiz - a cena do primeiro paragrafo, o assunto concreto do transito. Se couber na carta de outra pessoa, esta errada. PROIBIDO proverbio, verdade universal e frase de autoajuda. Sem jargao, sem nome de planeta, sem numero de casa. Nao repita literalmente nenhum paragrafo.",
            },
            "identificacao": {
                "type": "object",
                "additionalProperties": False,
                "required": ["abertura", "paragrafos"],
                "description": "PARTE 1. O que esta acontecendo com ela. So identificacao: nada de conselho aqui.",
                "properties": {
                    "abertura": {
                        "type": "string",
                        "description": "UMA frase de ate 12 palavras, do jeito que ela contaria para uma amiga. NAO precisa carregar o reconhecimento sozinha: pode dizer que alguma coisa se MOVEU, que abriu espaco. Comeca por 'Voce' ou pelo assunto concreto. PROIBIDO comecar por 'O que', 'Voce tende a', 'E comum que', 'Talvez'. Descreva terreno, nunca prometa resultado. Sem jargao e sem poesia.",
                    },
                    "paragrafos": {
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 2,
                        "items": {"type": "string"},
                        "description": "EXATAMENTE DOIS, de no maximo 32 palavras cada. O PRIMEIRO e a cena da semana dela MAIS A VIRADA: a situacao concreta e a consequencia que ela nao tinha ligado aquela situacao. Lista de tres coisas que ela faz nao serve - precisa ter um porem. E o paragrafo mais importante da carta. O SEGUNDO aponta para onde isso vai e para num ponto que deixa a pessoa pronta para a parte 2, sem nomear a area dela nem adiantar o conteudo. A CARTA NUNCA FALA DE SI MESMA: proibido escrever 'a proxima parte', 'logo abaixo', 'a seguir', 'esta leitura', 'esta carta' - ela esta lendo um texto, nao um indice. Proibido filosofar e proibido soar poetico: palavra curta e comum, do jeito que se fala. PROIBIDO 'o que pesa', 'o que trava', 'aquilo que', 'esta pedindo X', 'dar nome a'.",
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
                        "description": "UM SO, de no maximo 32 palavras. Por que essa area destrava o que ela quer trabalhar, em termos praticos. RESPONDE A FRASE DO ESPELHO que ela escolheu: duas pessoas na mesma casa com frases diferentes nao podem receber o mesmo paragrafo. Nada de explicacao longa: as acoes abaixo fazem o trabalho.",
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


async def _chamar(modelo: str, sistema: str, usuario: str) -> dict:
    kwargs = dict(
        model=modelo,
        messages=[{"role": "system", "content": sistema},
                  {"role": "user", "content": usuario}],
        response_format={"type": "json_schema", "json_schema": ESQUEMA},
        max_completion_tokens=MAX_TOKENS_SAIDA,
    )
    try:
        r = await cliente().chat.completions.create(reasoning_effort="medium", **kwargs)
    except TypeError:
        r = await cliente().chat.completions.create(**kwargs)
    except Exception as e:
        # modelos sem reasoning_effort devolvem 400 em vez de TypeError
        if "reasoning" in str(e).lower():
            r = await cliente().chat.completions.create(**kwargs)
        else:
            raise
    escolha = r.choices[0]
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
    t0 = time.time()

    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY ausente: indo direto para a carta de reserva")
        return {"carta": reserva.montar(fatos, veredito, quiz, precisao), "meta": meta}

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        meta["tentativas"] = tentativa
        usuario = montar_user(fatos, correcao)

        for modelo in MODELOS:
            try:
                carta = await asyncio.wait_for(
                    _chamar(modelo, sistema, usuario), timeout=TIMEOUT_LLM)
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
            problemas = (auditar(corpo, permitido)
                         + auditar_simplicidade(corpo)
                         + auditar_porta(carta)
                         + auditar_registro(carta)
                         + auditar_destaque(carta))
            if not problemas:
                meta["validacao"] = "ok" if tentativa == 1 else "regenerado"
                meta["ms_llm"] = int((time.time() - t0) * 1000)
                return {"carta": carta, "meta": meta}

            logger.warning("carta reprovada na auditoria (tentativa %d): %s",
                           tentativa, problemas)
            correcao = problemas
            break  # troca de tentativa, não de modelo

    meta["ms_llm"] = int((time.time() - t0) * 1000)
    logger.error("duas reprovacoes ou falha total: entrando com a carta de reserva")
    return {"carta": reserva.montar(fatos, veredito, quiz, precisao), "meta": meta}
