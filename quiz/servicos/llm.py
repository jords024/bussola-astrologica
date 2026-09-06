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
from .verificacao import auditar, auditar_simplicidade, texto_da_carta

logger = logging.getLogger(__name__)

MAX_TENTATIVAS = 2

ESQUEMA = {
    "name": "carta_bussola",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["titulo", "destaque", "paragrafos", "espera", "janela"],
        "properties": {
            "titulo": {
                "type": "string",
                "description": "4 a 7 palavras, minusculas, sem ponto final. A direcao do momento em forma de verbo. Ex: reorganizar antes de expandir",
            },
            "destaque": {
                "type": "string",
                "description": "UMA frase completa, de 8 a 18 palavras, que a pessoa releria e mandaria para uma amiga. DIFERENTE do titulo: o titulo e a direcao em forma de verbo, o destaque e uma sentenca inteira. Sem jargao, sem nome de planeta, sem numero de casa. Nao repita literalmente nenhum paragrafo.",
            },
            "paragrafos": {
                "type": "array",
                "minItems": 4,
                "maxItems": 6,
                "items": {"type": "string"},
                "description": "A carta. Prosa corrida, sem rotulo e sem titulo de secao. Cada paragrafo com no maximo quatro linhas.",
            },
            "espera": {
                "type": ["string", "null"],
                "description": "Uma frase de no maximo 20 palavras sobre a area que pede espera. null quando o veredito nao trouxer area de espera.",
            },
            "janela": {
                "type": "string",
                "description": "SOMENTE o fragmento de tempo, em minusculas, sem verbo e sem ponto final. Exemplos corretos: 'ate meados de marco', 'nas proximas duas ou tres semanas'. NAO escreva frase completa como 'Essa configuracao perde forca ate marco'. Use a janela estimada que veio nos FATOS.",
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
        "<FATOS>", fatos["bloco_fatos"], "</FATOS>", "",
        "<VEREDITO>", fatos["bloco_veredito"], "</VEREDITO>", "",
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
            problemas = auditar(corpo, permitido) + auditar_simplicidade(corpo)
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
