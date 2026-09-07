# -*- coding: utf-8 -*-
"""Disparo de webhook para ZapVoice / Hotmart com os dados da leitura gerada."""
from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from typing import Optional

from config import WEBHOOK_HOTMART_URL

logger = logging.getLogger("bussola.webhook")
FUSO_BRASILIA = timezone(timedelta(hours=-3))


def formatar_mensagem(nome: str, carta: dict) -> str:
    """Formata a mensagem completa da leitura para envio no WhatsApp."""
    partes = []
    primeiro_nome = (nome or "").strip().split()[0] if (nome or "").strip() else ""
    if primeiro_nome:
        partes.append(f"Olá, {primeiro_nome}! Aqui está a sua leitura da Bússola Astrológica:")
    else:
        partes.append("Aqui está a sua leitura da Bússola Astrológica:")

    if carta.get("selo"):
        partes.append(f"✦ {carta['selo']}")

    if carta.get("titulo"):
        partes.append(f"*{str(carta['titulo']).upper()}*")

    if carta.get("destaque"):
        partes.append(f"_{carta['destaque']}_")

    if carta.get("paragrafos") and isinstance(carta["paragrafos"], list):
        partes.extend(carta["paragrafos"])

    espera = carta.get("espera") or ""
    janela = carta.get("janela") or ""
    espera_janela = f"{espera} {janela}".strip()
    if espera_janela:
        partes.append(f"⏳ {espera_janela}")

    return "\n\n".join(partes)


def disparar_webhook_leitura(
    nome_completo: str,
    whatsapp: str,
    carta: dict,
    leitura_id: str = "",
    meta: Optional[dict] = None,
    url: Optional[str] = None,
) -> bool:
    """Dispara webhook POST para a URL configurada com nome, numero e mensagem."""
    destino = WEBHOOK_HOTMART_URL if url is None else url
    if not destino:
        logger.warning("Webhook não configurado; pulando disparo.")
        return False

    agora_brasilia = datetime.now(FUSO_BRASILIA)
    data_hora_fmt = agora_brasilia.strftime("%d/%m/%Y, %H:%M:%S")

    clean_digits = re.sub(r"\D", "", whatsapp or "")
    mensagem_formatada = formatar_mensagem(nome_completo, carta)

    payload = {
        "event": "PURCHASE_OUT_OF_SHOPPING_CART",
        "tipo": "leitura_concluida",
        "origem": "quiz_bussola",
        "leitura_id": leitura_id,
        "data_hora_brasilia": data_hora_fmt,
        # Campos solicitados explicitamente:
        "nome_completo": nome_completo,
        "nome": nome_completo,
        "name": nome_completo,
        "numero": whatsapp,
        "whatsapp": whatsapp,
        "telefone": whatsapp,
        "phone": clean_digits or whatsapp,
        "mensagem": mensagem_formatada,
        "message": mensagem_formatada,
        "texto": mensagem_formatada,
        "carta": carta,
        "data": {
            "product": {
                "name": "Bússola Astrológica",
            },
            "buyer": {
                "name": nome_completo,
                "phone": whatsapp,
                "checkout_phone": clean_digits,
            },
            "purchase": {
                "order_date": int(agora_brasilia.timestamp() * 1000),
                "order_date_brasilia": data_hora_fmt,
            },
            "reading": {
                "leitura_id": leitura_id,
                "mensagem": mensagem_formatada,
                "titulo": carta.get("titulo", ""),
                "destaque": carta.get("destaque", ""),
                **(meta or {}),
            },
            "custom_fields": {
                "nome_completo": nome_completo,
                "numero": whatsapp,
                "mensagem": mensagem_formatada,
                "leitura_id": leitura_id,
            },
        },
    }

    try:
        corpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            destino,
            data=corpo,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": "BussolaQuiz/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as res:
            codigo = res.getcode()
            resposta_texto = res.read().decode("utf-8", errors="replace")
            logger.info("Webhook disparado com sucesso (%s) para %s: %s", codigo, destino, resposta_texto[:200])
            return 200 <= codigo < 300
    except urllib.error.HTTPError as e:
        corpo_erro = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
        logger.warning("Erro HTTP ao disparar webhook (%s): %s | %s", e.code, e.reason, corpo_erro[:200])
        return False
    except Exception as e:
        logger.error("Falha ao disparar webhook para %s: %s", destino, e)
        return False
