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

from servicos import eventos, registro
from servicos.tempo_real import rastreador_presenca, ws_manager

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
            for lin in linhas:
                sid = lin.get("sid", "")
                aid = lin.get("aid", "")
                evt = lin.get("evt")
                props = lin.get("props") or {}
                lid = props.get("leitura_id")

                tela = props.get("para") if evt == "tela" else (props.get("tela") if evt == "ping" else (10 if evt == "oferta_clique" else None))
                checkout = True if evt == "oferta_clique" else None
                oculto = True if (evt == "visibilidade" and props.get("estado") == "oculto") else False

                if lid and (tela is not None or checkout is not None):
                    await asyncio.to_thread(registro.atualizar_progresso, lid, tela, checkout)

                sessao_atual = rastreador_presenca.registrar_atividade(
                    sid=sid,
                    aid=aid,
                    tela=tela,
                    leitura_id=lid,
                    checkout=checkout,
                    oculto=oculto
                )

                if evt in ("tela", "oferta_clique", "ping", "visibilidade"):
                    ws_manager.broadcast_sync({
                        "tipo": "checkout" if evt == "oferta_clique" else ("progresso" if evt in ("tela", "ping") else "presenca"),
                        "sid": sid,
                        "aid": aid,
                        "leitura_id": sessao_atual.get("leitura_id") or lid,
                        "tela": sessao_atual.get("tela", tela),
                        "rotulo": sessao_atual.get("rotulo", f"Tela {tela}"),
                        "checkout": sessao_atual.get("checkout", checkout or False),
                        "ativo": sessao_atual.get("ativo", True),
                        "ts": sessao_atual.get("ts"),
                        "total_ao_vivo": len(rastreador_presenca.obter_ativos(90.0))
                    })
    except Exception as e:
        # nada aqui pode escapar: o funil da pessoa nao depende disto
        logger.warning("evento descartado: %s", str(e)[:160])
    return vazio
