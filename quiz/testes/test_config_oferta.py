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
        self.assertIn("segundos: 16", conteudo)
        self.assertIn("garantiaBotao: 16000", conteudo)
        self.assertIn("decorrido < (VSL.segundos * 1000)", conteudo)
        self.assertIn("function vslPlayer()", conteudo)
        self.assertIn("btn.scrollIntoView", conteudo)
        self.assertIn("atualizarBotaoContinuarEscolha", conteudo)
        self.assertIn("btn-continuar-escolha", conteudo)
        self.assertIn("dadosPasso(de > T.dados ? 2 : 0)", conteudo)
        self.assertIn("const SKIP = {[T.oferta]:T.leitura};", conteudo)
        self.assertIn("if(S.leitura){", conteudo)
        self.assertIn("embed=c6818306-fbe3-4919-b404-2f5b99424bc1&ratio=9:16&width=350px&transparent=1", conteudo)
        self.assertIn("var floatingWidth = 140;", conteudo)

    def test_login_painel_tela_customizada_e_super_admin(self):
        """Verifica que GET /painel sem auth retorna a tela HTML bonita (sem popup WWW-Authenticate) e aceita login via Super Admin."""
        with mock.patch.object(config, "PAINEL_SENHA", "senha_teste"), \
             mock.patch.object(config, "SUPER_ADMIN_EMAIL", "aryarajmarketing@gmail.com"), \
             mock.patch.object(config, "SUPER_ADMIN_PASSWORD", "123456"):
            # 1. GET /painel sem login -> 401 com HTML da tela de login e SEM cabeçalho WWW-Authenticate
            r_login_html = self.client.get("/painel", headers={"Accept": "text/html"})
            self.assertEqual(r_login_html.status_code, 401)
            self.assertNotIn("www-authenticate", {k.lower(): v for k, v in r_login_html.headers.items()})
            self.assertIn('id="form-login-painel"', r_login_html.text)
            self.assertIn('id="login-email"', r_login_html.text)
            self.assertIn('id="login-senha"', r_login_html.text)

            # 2. POST /painel/login com senha errada -> 401
            r_erro = self.client.post("/painel/login", json={"email": "aryarajmarketing@gmail.com", "senha": "000"})
            self.assertEqual(r_erro.status_code, 401)

            # 3. POST /painel/login com aryarajmarketing@gmail.com e 123456 -> 200 e cookie de sessão
            r_ok = self.client.post("/painel/login", json={"email": "aryarajmarketing@gmail.com", "senha": "123456"})
            self.assertEqual(r_ok.status_code, 200)
            self.assertTrue(r_ok.json().get("ok"))

            # 4. GET /painel agora autenticado pelo cookie -> 200
            r_painel = self.client.get("/painel")
            self.assertEqual(r_painel.status_code, 200)
            self.assertIn("Sair da conta", r_painel.text)

            # 5. POST /painel/logout -> encerra a sessão
            r_out = self.client.post("/painel/logout")
            self.assertEqual(r_out.status_code, 200)
            self.assertEqual(self.client.get("/painel").status_code, 401)

    def test_vsl_oferta_formato_vertical_9_16(self):
        """Garante que a VSL da oferta está configurada no formato vertical (9:16) e não 16:9."""
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        html = r.text
        self.assertIn("vturb-wrapper-c6818306-fbe3-4919-b404-2f5b99424bc1", html)
        self.assertIn("padding-top:177.77%", html)
        self.assertIn("ratio=9:16", html)
        self.assertIn("videoRatio = '9:16'", html)
        self.assertNotIn("ratio=16:9", html)
        self.assertNotIn("videoRatio = '16:9'", html)

    def test_atalho_dev_ultimo_slide_localhost(self):
        """Valida que o atalho dev para o último slide existe apenas para localhost / 127.0.0.1."""
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        html = r.text
        self.assertIn("['localhost', '127.0.0.1'].includes(window.location.hostname)", html)
        self.assertIn("devJumpInicioBtn", html)
        self.assertIn("devFloatJumpBtn", html)
        self.assertIn("go(T.oferta)", html)

    def test_player_flutuante_sem_bloqueio_de_transform(self):
        """Garante que .scr.flow.on não possui animação/transform ativo que prenda o iframe flutuante."""
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        html = r.text
        self.assertIn(".scr.flow.on{animation:none !important;transform:none !important;}", html)
        self.assertIn("scr10.style.transform = 'none'", html)

    def test_player_flutuante_tamanho_pequeno_vertical(self):
        """Garante que o player flutuante no formato vertical 9:16 usa dimensões compactas proporcionais (140px desktop e <=130px mobile)."""
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        html = r.text
        self.assertIn("var floatingWidth = 140;", html)
        self.assertIn("var isVertical = videoRatio === '9:16';", html)
        self.assertIn("Math.min(130, Math.round(window.innerWidth * 0.35)) : 140", html)
        self.assertIn("floatHeight = isVertical ? Math.round((actualWidth * 16) / 9)", html)


if __name__ == "__main__":
    unittest.main()
