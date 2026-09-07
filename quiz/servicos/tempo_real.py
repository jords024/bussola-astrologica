# -*- coding: utf-8 -*-
"""Serviço de tempo real (WebSocket) e rastreamento de contatos ativos na tela."""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)

ETAPAS_ROTULOS = {
    0: "Tela 0 (Início)",
    1: "Tela 1 (Contexto)",
    2: "Tela 2 (Área)",
    3: "Tela 3 (Espelho)",
    4: "Tela 4 (Quebra)",
    5: "Tela 5 (Dados)",
    6: "Tela 6 (Cálculo)",
    7: "Tela 7 (Leitura)",
    8: "Tela 8 (Portas)",
    9: "Tela 9 (Ponte)",
    10: "Tela 10 (Oferta)",
}


class RastreadorPresenca:
    """Mantém em memória os visitantes e leads que estão navegando nas telas agora."""

    def __init__(self, ttl_padrao: float = 90.0):
        self.ttl_padrao = ttl_padrao
        # Chave: sid (ou leitura_id se não houver sid) -> dados
        self._sessoes: dict[str, dict[str, Any]] = {}
        # Mapeamento rápido: leitura_id -> sid
        self._leitura_para_sid: dict[str, str] = {}
        # Mapeamento reverso: sid -> leitura_id
        self._sid_para_leitura: dict[str, str] = {}

    def registrar_atividade(
        self,
        sid: str,
        aid: Optional[str] = None,
        tela: Optional[int] = None,
        leitura_id: Optional[str] = None,
        checkout: Optional[bool] = None,
        oculto: bool = False,
        nome: Optional[str] = None,
    ) -> dict[str, Any]:
        """Registra atividade recente de um visitante e retorna os dados consolidados."""
        agora = time.time()
        sid = (sid or "").strip()
        leitura_id = (leitura_id or "").strip() or None

        # Se já conhecemos a leitura_id para este sid ou vice-versa
        if sid and not leitura_id and sid in self._sid_para_leitura:
            leitura_id = self._sid_para_leitura[sid]
        elif leitura_id and not sid and leitura_id in self._leitura_para_sid:
            sid = self._leitura_para_sid[leitura_id]

        chave = sid or leitura_id or "desconhecido"
        if sid and leitura_id:
            self._sid_para_leitura[sid] = leitura_id
            self._leitura_para_sid[leitura_id] = sid

        atual = self._sessoes.get(chave, {
            "sid": sid or chave,
            "aid": aid or "",
            "leitura_id": leitura_id,
            "tela": 0,
            "rotulo": ETAPAS_ROTULOS.get(0, "Tela 0 (Início)"),
            "checkout": False,
            "nome": nome or "",
            "ts": agora,
            "ativo": True,
        })

        if aid:
            atual["aid"] = aid
        if leitura_id:
            atual["leitura_id"] = leitura_id
        if nome:
            atual["nome"] = nome
        if tela is not None:
            tela_int = int(tela)
            atual["tela"] = tela_int
            atual["rotulo"] = ETAPAS_ROTULOS.get(tela_int, f"Tela {tela_int}")
        if checkout is not None:
            atual["checkout"] = bool(checkout)

        if oculto:
            atual["ativo"] = False
        else:
            atual["ts"] = agora
            atual["ativo"] = True

        self._sessoes[chave] = atual
        return atual

    def vincular_leitura(self, leitura_id: str, sid: str, nome: Optional[str] = None) -> None:
        if not leitura_id:
            return
        if sid:
            self._sid_para_leitura[sid] = leitura_id
            self._leitura_para_sid[leitura_id] = sid
            if sid in self._sessoes:
                self._sessoes[sid]["leitura_id"] = leitura_id
                if nome:
                    self._sessoes[sid]["nome"] = nome
        else:
            self.registrar_atividade(sid=leitura_id, leitura_id=leitura_id, nome=nome)

    def obter_ativos(self, limite_segundos: Optional[float] = None) -> list[dict[str, Any]]:
        """Retorna lista de todas as sessões ativas com atividade dentro do limite de segundos."""
        limite = limite_segundos if limite_segundos is not None else self.ttl_padrao
        agora = time.time()
        ativos = []
        for d in self._sessoes.values():
            if d.get("ativo", True) and (agora - d.get("ts", 0)) <= limite:
                ativos.append(dict(d, segundos_atras=round(agora - d.get("ts", 0), 1)))
        ativos.sort(key=lambda x: x.get("ts", 0), reverse=True)
        return ativos

    def obter_ids_leitura_ativos(self, limite_segundos: Optional[float] = None) -> set[str]:
        """Retorna conjunto de IDs de leituras que estão com visitantes vendo alguma tela agora."""
        ativos = self.obter_ativos(limite_segundos)
        ids = set()
        for a in ativos:
            lid = a.get("leitura_id")
            if lid:
                ids.add(lid)
        return ids

    def limpar_expirados(self, max_idade: float = 600.0) -> int:
        """Limpa registros mais velhos que max_idade segundos para liberar memória."""
        agora = time.time()
        chaves_remover = [k for k, v in self._sessoes.items() if (agora - v.get("ts", 0)) > max_idade]
        for k in chaves_remover:
            self._sessoes.pop(k, None)
        return len(chaves_remover)


class PainelWebSocketManager:
    """Gerencia conexões WebSocket ativas do painel administrativo."""

    def __init__(self):
        self.conexoes: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def conectar(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._loop = asyncio.get_running_loop()
        async with self._lock:
            self.conexoes.add(websocket)
        logger.info("WebSocket do painel conectado (%d conexões ativas).", len(self.conexoes))

    async def desconectar(self, websocket: WebSocket) -> None:
        async with self._lock:
            self.conexoes.discard(websocket)
        logger.info("WebSocket do painel desconectado (%d conexões ativas).", len(self.conexoes))

    async def broadcast(self, mensagem: dict[str, Any]) -> None:
        """Envia mensagem JSON para todos os clientes conectados."""
        if not self.conexoes:
            return
        desconectados = set()
        async with self._lock:
            for ws in list(self.conexoes):
                try:
                    await ws.send_json(mensagem)
                except Exception:
                    desconectados.add(ws)
            for ws in desconectados:
                self.conexoes.discard(ws)

    def broadcast_sync(self, mensagem: dict[str, Any]) -> None:
        """Helper para envio síncrono ou a partir de threads/outros contextos."""
        try:
            loop = getattr(self, "_loop", None)
            if loop and loop.is_running():
                asyncio.run_coroutine_threadsafe(self.broadcast(mensagem), loop)
            else:
                cur_loop = asyncio.get_running_loop()
                cur_loop.create_task(self.broadcast(mensagem))
        except Exception:
            pass


# Instâncias globais únicas para o aplicativo
rastreador_presenca = RastreadorPresenca(ttl_padrao=90.0)
ws_manager = PainelWebSocketManager()
