# -*- coding: utf-8 -*-
"""Testes unitários do serviço de configuração da VSL da oferta e Teste A/B."""
import json
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from fastapi.testclient import TestClient
from starlette.requests import Request

import config
import main
from servicos import config_oferta


class TestConfigOferta(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.dados_dir = Path(self.temp_dir.name)
        self.patcher = mock.patch.object(config, "DIR_DADOS", self.dados_dir)
        self.patcher.start()
        # Limpa cache de sessões entre testes
        config_oferta._SESSOES_VARIANTES.clear()
        self.client = TestClient(main.app)

    def tearDown(self):
        self.patcher.stop()
        self.temp_dir.cleanup()

    def test_obter_config_oferta_padrao(self):
        """Se o arquivo não existir, retorna 'delay' como modo padrão."""
        cfg = config_oferta.obter_config_oferta()
        self.assertEqual(cfg["modo_vsl"], "delay")
        self.assertEqual(cfg["contador_ab"], 0)
        self.assertTrue((self.dados_dir / "config_oferta.json").exists())

    def test_salvar_config_oferta_valida_e_invalida(self):
        """Valida que apenas modos válidos são salvos e persistem em disco com webhook_vsl_play_url."""
        cfg = config_oferta.salvar_config_oferta("imediato", webhook_vsl_play_url="https://exemplo.com/webhook")
        self.assertEqual(cfg["modo_vsl"], "imediato")
        self.assertEqual(cfg["webhook_vsl_play_url"], "https://exemplo.com/webhook")

        # Verifica leitura
        lido = config_oferta.obter_config_oferta()
        self.assertEqual(lido["modo_vsl"], "imediato")
        self.assertEqual(lido["webhook_vsl_play_url"], "https://exemplo.com/webhook")

        # Modo inválido levanta ValueError
        with self.assertRaises(ValueError):
            config_oferta.salvar_config_oferta("modo_inexistente")

    def test_variante_modo_imediato_e_delay(self):
        """No modo imediato sempre dá pitch_imediato=True; no delay dá False."""
        config_oferta.salvar_config_oferta("imediato")
        res_imediato = config_oferta.obter_variante_para_cliente(sid="s1", aid="a1")
        self.assertEqual(res_imediato["modo"], "imediato")
        self.assertEqual(res_imediato["variante"], "A")
        self.assertTrue(res_imediato["pitch_imediato"])

        config_oferta.salvar_config_oferta("delay")
        res_delay = config_oferta.obter_variante_para_cliente(sid="s2", aid="a2")
        self.assertEqual(res_delay["modo"], "delay")
        self.assertEqual(res_delay["variante"], "B")
        self.assertFalse(res_delay["pitch_imediato"])

    def test_teste_ab_alternancia_um_a_um(self):
        """No teste A/B, alterna 1 a 1 entre Variante A (imediato) e Variante B (delay)."""
        config_oferta.salvar_config_oferta("teste_ab")

        # Contato 1 -> Ímpar -> Variante A (imediato)
        c1 = config_oferta.obter_variante_para_cliente(sid="sessao-1", aid="aid-1")
        self.assertEqual(c1["modo"], "teste_ab")
        self.assertEqual(c1["variante"], "A")
        self.assertTrue(c1["pitch_imediato"])

        # Contato 2 -> Par -> Variante B (delay)
        c2 = config_oferta.obter_variante_para_cliente(sid="sessao-2", aid="aid-2")
        self.assertEqual(c2["modo"], "teste_ab")
        self.assertEqual(c2["variante"], "B")
        self.assertFalse(c2["pitch_imediato"])

        # Contato 3 -> Ímpar -> Variante A (imediato)
        c3 = config_oferta.obter_variante_para_cliente(sid="sessao-3", aid="aid-3")
        self.assertEqual(c3["variante"], "A")
        self.assertTrue(c3["pitch_imediato"])

        # Contato 4 -> Par -> Variante B (delay)
        c4 = config_oferta.obter_variante_para_cliente(sid="sessao-4", aid="aid-4")
        self.assertEqual(c4["variante"], "B")
        self.assertFalse(c4["pitch_imediato"])

        # Se o Contato 1 retornar (mesmo aid), deve manter a Variante A atribuída
        c1_retorno = config_oferta.obter_variante_para_cliente(sid="sessao-1", aid="aid-1")
        self.assertEqual(c1_retorno["variante"], "A")

    def test_api_publica_config_oferta(self):
        """GET /api/config-oferta responde publicamente com a variante."""
        config_oferta.salvar_config_oferta("imediato")
        resp = self.client.get("/api/config-oferta?sid=teste-api&aid=aid-api")
        self.assertEqual(resp.status_code, 200)
        dados = resp.json()
        self.assertEqual(dados["modo"], "imediato")
        self.assertTrue(dados["pitch_imediato"])

    def test_api_painel_config_oferta_seguranca_e_crud(self):
        """Endpoints /painel/api/config-oferta exigem autenticação e salvam alterações."""
        # 1. Sem autenticação -> 401
        r_sem_auth = self.client.get("/painel/api/config-oferta")
        self.assertEqual(r_sem_auth.status_code, 401)
        r_post_sem_auth = self.client.post("/painel/api/config-oferta", json={"modo_vsl": "imediato"})
        self.assertEqual(r_post_sem_auth.status_code, 401)

        # 2. Com autenticação GET -> 200
        auth = (config.PAINEL_USUARIO, config.PAINEL_SENHA)
        r_get = self.client.get("/painel/api/config-oferta", auth=auth)
        self.assertEqual(r_get.status_code, 200)
        self.assertTrue(r_get.json().get("ok"))

        # 3. Com autenticação POST -> atualiza para teste_ab e webhook_url
        r_post = self.client.post(
            "/painel/api/config-oferta",
            json={"modo_vsl": "teste_ab", "webhook_vsl_play_url": "https://turb-back.exemplo.com/play"},
            auth=auth
        )
        self.assertEqual(r_post.status_code, 200)
        self.assertEqual(r_post.json()["modo_vsl"], "teste_ab")
        self.assertEqual(r_post.json()["webhook_vsl_play_url"], "https://turb-back.exemplo.com/play")
        self.assertTrue(r_post.json()["ok"])

        # 4. Verifica se salvou
        cfg = config_oferta.obter_config_oferta()
        self.assertEqual(cfg["modo_vsl"], "teste_ab")
        self.assertEqual(cfg["webhook_vsl_play_url"], "https://turb-back.exemplo.com/play")

        # 5. POST com modo inválido -> 422
        r_invalido = self.client.post("/painel/api/config-oferta", json={"modo_vsl": "invalido"}, auth=auth)
        self.assertEqual(r_invalido.status_code, 422)

    def test_painel_renderiza_botao_configuracoes_e_secao(self):
        """Verifica se o botão na sidebar e a seção central estão no HTML do painel."""
        from api.painel import painel

        req = Request({"type": "http", "method": "GET", "path": "/painel", "headers": []})
        resp = painel(req, _="crassus", view="configuracoes")
        html_resp = resp.body.decode("utf-8")

        # 1. Botão na sidebar
        self.assertIn('id="btn-visao-configuracoes"', html_resp)
        self.assertIn("Configurações", html_resp)

        # 2. Seção de configurações
        self.assertIn('id="visao-configuracoes"', html_resp)
        self.assertIn("Configurações da VSL & Oferta", html_resp)
        self.assertIn("⏱️ Sempre com Delay do Pitch", html_resp)
        self.assertIn("🚀 Sempre com Pitch Imediato", html_resp)
        self.assertIn("🧪 Teste A / B (Alternado 50% / 50%)", html_resp)
        self.assertIn("salvarConfigOferta()", html_resp)

    def test_frontend_index_html_contem_suporte_a_config_oferta(self):
        """Verifica se o index.html possui a rotina de carregar a configuração e aplicar o pitch imediato."""
        caminho_index = config.DIR_PUBLICO / "index.html"
        self.assertTrue(caminho_index.exists())
        conteudo = caminho_index.read_text(encoding="utf-8")

        self.assertIn("vslCarregarConfig", conteudo)
        self.assertIn("/api/config-oferta", conteudo)
        self.assertIn("pitch_imediato", conteudo)
        self.assertIn("vslConfigOferta", conteudo)
        self.assertIn("vslNotificarPlay", conteudo)
        self.assertIn("/api/vsl-play", conteudo)
        self.assertIn("window.S = S", conteudo)
        self.assertIn('data-src="https://turb-front.aryaraj.shop/?embed=65cb9c18-e117-4734-a983-2fc6275c2061', conteudo)
        self.assertIn("!nome && !whatsapp && !leituraId", conteudo)


if __name__ == "__main__":
    unittest.main()
