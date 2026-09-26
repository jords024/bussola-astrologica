# -*- coding: utf-8 -*-
"""Cálculo e agregação de custos financeiros com IA / LLM.

Este módulo centraliza os preços por modelo, a estimativa e cálculo exato de
tokens consumidos (prompt e resposta/raciocínio), o valor em USD e conversão
para BRL, além da economia gerada pelo sistema de cache e cartas de reserva.
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Preços por 1 milhão de tokens (USD / 1M tokens) conforme tabela OpenAI
# Referência: https://openai.com/api/pricing/
TABELA_PRECOS = {
    # gpt-5.6-luna e modelos flagship / raciocínio
    "gpt-5.6-luna": {"prompt": 2.50 / 1_000_000, "completion": 10.00 / 1_000_000},
    "gpt-4o": {"prompt": 2.50 / 1_000_000, "completion": 10.00 / 1_000_000},
    "gpt-4o-2024-08-06": {"prompt": 2.50 / 1_000_000, "completion": 10.00 / 1_000_000},
    "gpt-4o-mini": {"prompt": 0.15 / 1_000_000, "completion": 0.60 / 1_000_000},
    "gpt-4-turbo": {"prompt": 10.00 / 1_000_000, "completion": 30.00 / 1_000_000},
    "cache": {"prompt": 0.0, "completion": 0.0},
    "reserva": {"prompt": 0.0, "completion": 0.0},
}

PRECO_PADRAO = {"prompt": 2.50 / 1_000_000, "completion": 10.00 / 1_000_000}
TAXA_CAMBIO_BRL = 5.50  # 1 USD = 5,50 BRL (cotação base)

# Valores médios de tokens para leituras legadas sem metadados exatos de tokens
PROMPT_TOKENS_MEDIO = 1200
COMPLETION_TOKENS_MEDIO = 1500


def calcular_custo_tokens(modelo: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calcula o custo em USD a partir do modelo e quantidade de tokens."""
    precos = TABELA_PRECOS.get(modelo, PRECO_PADRAO)
    return float((prompt_tokens * precos["prompt"]) + (completion_tokens * precos["completion"]))


def calcular_custo_item(dados: dict, leitura_id: str = "") -> dict:
    """Extrai informações e calcula custos de uma leitura específica."""
    meta = dados.get("meta") or {}
    modelo = meta.get("modelo")
    validacao = meta.get("validacao")
    tentativas = max(1, int(meta.get("tentativas") or 1))
    ms_llm = int(meta.get("ms_llm") or 0)

    # Identifica o tipo de geração
    if validacao == "cache" or modelo == "cache":
        tipo = "cache"
        modelo_nome = "cache"
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        custo_usd = 0.0
        custo_brl = 0.0
        # Economia gerada por não ter feito a chamada LLM
        economia_usd = calcular_custo_tokens("gpt-5.6-luna", PROMPT_TOKENS_MEDIO, COMPLETION_TOKENS_MEDIO)
        economia_brl = economia_usd * TAXA_CAMBIO_BRL
        estimado = False
    elif validacao == "reserva" or modelo in ("reserva", None):
        tipo = "reserva"
        modelo_nome = "reserva"
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        custo_usd = 0.0
        custo_brl = 0.0
        economia_usd = 0.0
        economia_brl = 0.0
        estimado = False
    else:
        tipo = "llm"
        modelo_nome = modelo or "gpt-5.6-luna"
        # Se os tokens foram registrados no meta, usa os valores exatos
        p_tok = meta.get("prompt_tokens")
        c_tok = meta.get("completion_tokens")
        if p_tok is not None and c_tok is not None:
            prompt_tokens = int(p_tok)
            completion_tokens = int(c_tok)
            estimado = False
        else:
            # Estimativa para leituras legadas baseada no tamanho do prompt e tentativas
            prompt_tokens = PROMPT_TOKENS_MEDIO * tentativas
            completion_tokens = COMPLETION_TOKENS_MEDIO * tentativas
            estimado = True

        total_tokens = prompt_tokens + completion_tokens
        custo_usd = calcular_custo_tokens(modelo_nome, prompt_tokens, completion_tokens)
        custo_brl = custo_usd * TAXA_CAMBIO_BRL
        economia_usd = 0.0
        economia_brl = 0.0

    nome = (dados.get("nome_completo") or "Anônimo").strip()
    whatsapp = (dados.get("whatsapp") or "").strip()
    quiz = dados.get("quiz") or {}
    area = quiz.get("area") or "desconhecida"
    data_bsb = dados.get("gravado_em_bsb") or dados.get("chegou_em_bsb") or "—"

    return {
        "leitura_id": leitura_id,
        "data_bsb": data_bsb,
        "nome": nome,
        "whatsapp": whatsapp,
        "area": area,
        "modelo": modelo_nome,
        "tipo": tipo,
        "tentativas": tentativas,
        "validacao": validacao or ("cache" if tipo == "cache" else "reserva" if tipo == "reserva" else "ok"),
        "ms_llm": ms_llm,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "custo_usd": custo_usd,
        "custo_brl": custo_brl,
        "economia_usd": economia_usd,
        "economia_brl": economia_brl,
        "estimado": estimado,
    }


def agregar_financeiro(itens_processados: list[dict]) -> dict:
    """Agrega os custos financeiros para exibição no painel."""
    total_leituras = len(itens_processados)
    qtd_llm = 0
    qtd_cache = 0
    qtd_reserva = 0

    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0

    custo_total_usd = 0.0
    custo_total_brl = 0.0
    economia_total_usd = 0.0
    economia_total_brl = 0.0

    por_modelo: dict[str, dict] = {}
    por_area: dict[str, dict] = {}

    for item in itens_processados:
        tipo = item["tipo"]
        mod = item["modelo"]
        area = item["area"]

        if tipo == "llm":
            qtd_llm += 1
        elif tipo == "cache":
            qtd_cache += 1
        else:
            qtd_reserva += 1

        total_prompt_tokens += item["prompt_tokens"]
        total_completion_tokens += item["completion_tokens"]
        total_tokens += item["total_tokens"]

        custo_total_usd += item["custo_usd"]
        custo_total_brl += item["custo_brl"]
        economia_total_usd += item["economia_usd"]
        economia_total_brl += item["economia_brl"]

        # Agrupamento por modelo
        if mod not in por_modelo:
            por_modelo[mod] = {
                "modelo": mod,
                "qtd": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "custo_usd": 0.0,
                "custo_brl": 0.0,
            }
        por_modelo[mod]["qtd"] += 1
        por_modelo[mod]["prompt_tokens"] += item["prompt_tokens"]
        por_modelo[mod]["completion_tokens"] += item["completion_tokens"]
        por_modelo[mod]["total_tokens"] += item["total_tokens"]
        por_modelo[mod]["custo_usd"] += item["custo_usd"]
        por_modelo[mod]["custo_brl"] += item["custo_brl"]

        # Agrupamento por área
        if area not in por_area:
            por_area[area] = {
                "area": area,
                "qtd": 0,
                "qtd_llm": 0,
                "custo_usd": 0.0,
                "custo_brl": 0.0,
                "tokens": 0,
            }
        por_area[area]["qtd"] += 1
        if tipo == "llm":
            por_area[area]["qtd_llm"] += 1
        por_area[area]["custo_usd"] += item["custo_usd"]
        por_area[area]["custo_brl"] += item["custo_brl"]
        por_area[area]["tokens"] += item["total_tokens"]

    custo_medio_geral_usd = (custo_total_usd / total_leituras) if total_leituras > 0 else 0.0
    custo_medio_geral_brl = (custo_total_brl / total_leituras) if total_leituras > 0 else 0.0
    custo_medio_llm_usd = (custo_total_usd / qtd_llm) if qtd_llm > 0 else 0.0
    custo_medio_llm_brl = (custo_total_brl / qtd_llm) if qtd_llm > 0 else 0.0

    # Ordenações
    lista_modelos = sorted(por_modelo.values(), key=lambda x: x["custo_brl"], reverse=True)
    lista_areas = sorted(por_area.values(), key=lambda x: x["custo_brl"], reverse=True)

    return {
        "total_leituras": total_leituras,
        "qtd_llm": qtd_llm,
        "qtd_cache": qtd_cache,
        "qtd_reserva": qtd_reserva,
        "pct_cache": (qtd_cache / total_leituras * 100) if total_leituras > 0 else 0.0,
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_tokens": total_tokens,
        "custo_total_usd": round(custo_total_usd, 4),
        "custo_total_brl": round(custo_total_brl, 2),
        "economia_total_usd": round(economia_total_usd, 4),
        "economia_total_brl": round(economia_total_brl, 2),
        "custo_medio_geral_usd": round(custo_medio_geral_usd, 4),
        "custo_medio_geral_brl": round(custo_medio_geral_brl, 3),
        "custo_medio_llm_usd": round(custo_medio_llm_usd, 4),
        "custo_medio_llm_brl": round(custo_medio_llm_brl, 3),
        "por_modelo": lista_modelos,
        "por_area": lista_areas,
        "itens": itens_processados,
    }
