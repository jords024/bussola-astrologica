# -*- coding: utf-8 -*-
"""Gerenciamento de configuração da VSL da Oferta e Teste A/B.

Permite alternar entre três modos para a página da oferta (Tela 10):
1. "delay": As informações abaixo da VSL ficam presas até o pitch aos 3min50 (230s).
2. "imediato": O vídeo e todas as informações abaixo já aparecem de primeira.
3. "teste_ab": Alterna 1 a 1 entre os contatos: 1 recebe Variante A (imediato) e 1 recebe Variante B (delay).
"""
from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import config

logger = logging.getLogger(__name__)

FUSO_BSB = timezone(timedelta(hours=-3))

MODOS_VALIDOS = {"delay", "imediato", "teste_ab"}
PADRAO_MODO = "delay"

_LOCK = threading.Lock()
# Cache em memória para garantir consistência de variante na mesma sessão
_SESSOES_VARIANTES: dict[str, str] = {}


def _arquivo_config() -> Path:
    return getattr(config, "DIR_DADOS", config.RAIZ / "dados") / "config_oferta.json"


def obter_config_oferta() -> dict:
    """Retorna a configuração atual da oferta. Cria com defaults se não existir."""
    caminho = _arquivo_config()
    with _LOCK:
        url_padrao = getattr(config, "WEBHOOK_VSL_PLAY_URL", "")
        if caminho.exists():
            try:
                dados = json.loads(caminho.read_text(encoding="utf-8"))
                modo = dados.get("modo_vsl")
                if modo in MODOS_VALIDOS:
                    return {
                        "modo_vsl": modo,
                        "contador_ab": int(dados.get("contador_ab", 0)),
                        "atualizado_em": dados.get("atualizado_em"),
                        "webhook_vsl_play_url": dados.get("webhook_vsl_play_url") if dados.get("webhook_vsl_play_url") is not None else url_padrao,
                    }
            except Exception as e:
                logger.warning("Falha ao ler config_oferta.json: %s", e)

        # Configuração padrão caso não exista
        padrao = {
            "modo_vsl": PADRAO_MODO,
            "contador_ab": 0,
            "atualizado_em": datetime.now(FUSO_BSB).isoformat(),
            "webhook_vsl_play_url": url_padrao,
        }
        try:
            caminho.parent.mkdir(parents=True, exist_ok=True)
            caminho.write_text(json.dumps(padrao, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning("Falha ao salvar config_oferta padrão: %s", e)
        return padrao


def salvar_config_oferta(modo_vsl: str, webhook_vsl_play_url: Optional[str] = None) -> dict:
    """Atualiza o modo da VSL da oferta ('delay', 'imediato' ou 'teste_ab') e a URL do webhook."""
    if modo_vsl not in MODOS_VALIDOS:
        raise ValueError(f"Modo inválido: {modo_vsl}. Opções válidas: {MODOS_VALIDOS}")

    caminho = _arquivo_config()
    with _LOCK:
        cfg = {}
        if caminho.exists():
            try:
                cfg = json.loads(caminho.read_text(encoding="utf-8"))
            except Exception:
                cfg = {}

        cfg["modo_vsl"] = modo_vsl
        if webhook_vsl_play_url is not None:
            cfg["webhook_vsl_play_url"] = str(webhook_vsl_play_url).strip()
        elif "webhook_vsl_play_url" not in cfg:
            cfg["webhook_vsl_play_url"] = getattr(config, "WEBHOOK_VSL_PLAY_URL", "")

        if "contador_ab" not in cfg:
            cfg["contador_ab"] = 0
        cfg["atualizado_em"] = datetime.now(FUSO_BSB).isoformat()

        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Configuração da VSL atualizada para '%s' (webhook_vsl='%s')", modo_vsl, cfg.get("webhook_vsl_play_url"))
        return cfg


def obter_variante_para_cliente(sid: str = "", aid: str = "") -> dict:
    """Define se a oferta para o cliente atual terá pitch imediato ou com delay.

    No teste A/B: alterna rigorosamente 1 a 1 entre Variante A (imediato) e
    Variante B (delay), mantendo a mesma variante se a mesma sessão retornar.
    """
    cfg = obter_config_oferta()
    modo = cfg.get("modo_vsl", PADRAO_MODO)

    if modo == "imediato":
        return {
            "modo": "imediato",
            "variante": "A",
            "pitch_imediato": True,
            "descricao": "Pitch liberado de primeira",
        }
    elif modo == "delay":
        return {
            "modo": "delay",
            "variante": "B",
            "pitch_imediato": False,
            "descricao": "Pitch com delay (3min50)",
        }

    # Modo Teste A / B
    chave_sessao = str(aid or sid or "").strip()
    with _LOCK:
        # Se a sessão já possui variante atribuída, mantém para não trocar enquanto a pessoa navega
        if chave_sessao and chave_sessao in _SESSOES_VARIANTES:
            var_atribuida = _SESSOES_VARIANTES[chave_sessao]
            return {
                "modo": "teste_ab",
                "variante": var_atribuida,
                "pitch_imediato": (var_atribuida == "A"),
                "descricao": "Variante A (imediato)" if var_atribuida == "A" else "Variante B (delay)",
            }

        # Novo contato: alterna o contador sequencial atômico
        caminho = _arquivo_config()
        contador = int(cfg.get("contador_ab", 0)) + 1
        cfg["contador_ab"] = contador

        # Alternância 1 a 1: Ímpar = A (Imediato), Par = B (Delay)
        var_atribuida = "A" if (contador % 2 == 1) else "B"

        if chave_sessao:
            _SESSOES_VARIANTES[chave_sessao] = var_atribuida
            if len(_SESSOES_VARIANTES) > 5000:
                for k in list(_SESSOES_VARIANTES.keys())[:1000]:
                    _SESSOES_VARIANTES.pop(k, None)

        try:
            caminho.parent.mkdir(parents=True, exist_ok=True)
            caminho.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning("Falha ao atualizar contador_ab: %s", e)

        return {
            "modo": "teste_ab",
            "variante": var_atribuida,
            "pitch_imediato": (var_atribuida == "A"),
            "descricao": "Variante A (imediato)" if var_atribuida == "A" else "Variante B (delay)",
        }
