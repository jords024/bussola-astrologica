# -*- coding: utf-8 -*-
"""Testes do serviço de tempo real (WebSocket) e rastreamento de contatos ativos."""
import asyncio
import json
import time
import unittest
from unittest import mock

from fastapi.testclient import TestClient

import config
from main import app
from servicos.tempo_real import RastreadorPresenca, PainelWebSocketManager, ETAPAS_ROTULOS
from api.painel import gerar_token_ws, validar_token_ws


class TestRastreadorPresenca(unittest.TestCase):
    def test_registrar_atividade_e_obter_ativos(self):
        rastreador = RastreadorPresenca(ttl_padrao=5.0)
        # Registra atividade na tela 2
        d1 = rastreador.registrar_atividade(sid="sessao-1", tela=2, nome="Maria")
        self.assertEqual(d1["tela"], 2)
        self.assertEqual(d1["rotulo"], "Tela 2 (Área)")
        self.assertEqual(d1["nome"], "Maria")
        self.assertTrue(d1["ativo"])

        # Consulta ativos
        ativos = rastreador.obter_ativos()
        self.assertEqual(len(ativos), 1)
        self.assertEqual(ativos[0]["sid"], "sessao-1")

    def test_expiracao_ttl(self):
        rastreador = RastreadorPresenca(ttl_padrao=0.1)
        rastreador.registrar_atividade(sid="sessao-curta", tela=3)
        time.sleep(0.15)
        # Já deve ter expirado
        ativos = rastreador.obter_ativos()
        self.assertEqual(len(ativos), 0)

    def test_vincular_leitura_e_ids_leitura_ativos(self):
        rastreador = RastreadorPresenca(ttl_padrao=10.0)
        rastreador.registrar_atividade(sid="sid-abc", tela=5)
        rastreador.vincular_leitura("20260907-120000-aaaa1111", "sid-abc", nome="Carlos")

        # Atualiza tela do mesmo sid para tela 8
        rastreador.registrar_atividade(sid="sid-abc", tela=8)

        ids = rastreador.obter_ids_leitura_ativos()
        self.assertIn("20260907-120000-aaaa1111", ids)

        ativos = rastreador.obter_ativos()
        self.assertEqual(len(ativos), 1)
        self.assertEqual(ativos[0]["leitura_id"], "20260907-120000-aaaa1111")
        self.assertEqual(ativos[0]["tela"], 8)
        self.assertEqual(ativos[0]["rotulo"], "Tela 8 (Portas)")

    def test_ocultar_atividade_visibility(self):
        rastreador = RastreadorPresenca(ttl_padrao=10.0)
        rastreador.registrar_atividade(sid="sid-xyz", tela=7)
        self.assertEqual(len(rastreador.obter_ativos()), 1)

        # Aba ficou em segundo plano
        rastreador.registrar_atividade(sid="sid-xyz", oculto=True)
        self.assertEqual(len(rastreador.obter_ativos()), 0)

        # Aba voltou a ficar visível
        rastreador.registrar_atividade(sid="sid-xyz", oculto=False)
        self.assertEqual(len(rastreador.obter_ativos()), 1)


class TestWebSocketPainel(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_conexao_rejeitada_sem_autenticacao(self):
        with self.assertRaises(Exception):
            with self.client.websocket_connect("/painel/ws"):
                pass

    def test_conexao_rejeitada_com_token_invalido(self):
        with self.assertRaises(Exception):
            with self.client.websocket_connect("/painel/ws?token=token-falso"):
                pass

    def test_conexao_aceita_com_token_valido_e_recebe_snapshot(self):
        from servicos.tempo_real import rastreador_presenca
        rastreador_presenca.registrar_atividade(sid="teste-ws-sid", tela=7, nome="Visitante Ao Vivo")

        token = gerar_token_ws()
        self.assertTrue(validar_token_ws(token))

        with self.client.websocket_connect(f"/painel/ws?token={token}") as ws:
            # Primeiro pacote recebido deve ser o snapshot
            msg = ws.receive_json()
            self.assertEqual(msg.get("tipo"), "snapshot")
            self.assertIn("total_ao_vivo", msg)
            self.assertGreaterEqual(msg["total_ao_vivo"], 1)

            # Teste de ping-pong
            ws.send_text("ping")
            resp = ws.receive_text()
            self.assertEqual(resp, "pong")

    def test_broadcast_notifica_clientes_conectados(self):
        from servicos.tempo_real import ws_manager
        token = gerar_token_ws()

        with self.client.websocket_connect(f"/painel/ws?token={token}") as ws:
            _ = ws.receive_json()  # descarta snapshot

            # Dispara um broadcast síncrono
            ws_manager.broadcast_sync({
                "tipo": "progresso",
                "leitura_id": "20260907-999999-bbbb2222",
                "tela": 10,
                "rotulo": "Tela 10 (Oferta)",
                "checkout": True,
                "ativo": True,
                "total_ao_vivo": 4
            })

            # Recebe a mensagem transmitida
            msg = ws.receive_json()
            self.assertEqual(msg.get("tipo"), "progresso")
            self.assertEqual(msg.get("leitura_id"), "20260907-999999-bbbb2222")
            self.assertEqual(msg.get("tela"), 10)
            self.assertTrue(msg.get("checkout"))


if __name__ == "__main__":
    unittest.main()
