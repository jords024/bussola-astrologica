# -*- coding: utf-8 -*-
"""POST /api/evento — coleta do funil.

Responde **204 sempre**, mesmo com lote inválido. Três motivos: o navegador não
tem a que reagir, então não existe tempestade de retry; um 422 apareceria no
console de qualquer pessoa que inspecione a página; e `sendBeacon` não consegue
ler resposta de qualquer forma. Rejeições vão para o log do servidor.
"""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Request, Response

from servicos import eventos

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_CORPO = 16 * 1024


@router.post("/api/evento", status_code=204)
async def receber(request: Request) -> Response:
    vazio = Response(status_code=204, headers={"Cache-Control": "no-store"})
    try:
        bruto = await request.body()
        if len(bruto) > MAX_CORPO:
            logger.warning("lote de eventos grande demais: %d bytes", len(bruto))
            return vazio

        import json
        lote = json.loads(bruto or b"{}")
        if not isinstance(lote, dict):
            return vazio

        ip = (request.client.host if request.client else "") or "?"
        ua = request.headers.get("user-agent", "")
        linhas = eventos.normalizar(lote, ip, ua)
        if linhas:
            await asyncio.to_thread(eventos.gravar, linhas)
    except Exception as e:
        # nada aqui pode escapar: o funil da pessoa nao depende disto
        logger.warning("evento descartado: %s", str(e)[:160])
    return vazio
