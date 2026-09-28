# -*- coding: utf-8 -*-
import json
import unittest
from unittest.mock import MagicMock, patch

from servicos.webhook import disparar_webhook_leitura, formatar_mensagem


class TestWebhook(unittest.TestCase):
    def setUp(self):
        self.carta_exemplo = {
            "selo": "Casa 7 · parcerias e vínculos · Vênus em trânsito",
            "titulo": "ver o padrão antes de escolher de novo",
            "destaque": "Quando muda a pessoa e o final é o mesmo, o padrão costuma ser mais antigo.",
            "paragrafos": [
                "Neste momento há um movimento forte nos seus vínculos.",
                "O que se move pede olhar com mais calma antes de decidir o próximo passo."
            ],
            "espera": "O que mais pede espera neste momento: definir o longo prazo.",
            "janela": "até por volta de dezembro"
        }

    def test_formatar_mensagem(self):
        msg = formatar_mensagem("Aryaraj Alves Fernandes", self.carta_exemplo)
        # Saudação com primeiro nome
        self.assertIn("Olá, Aryaraj!", msg)
        # Título em destaque/caixa alta
        self.assertIn("*VER O PADRÃO ANTES DE ESCOLHER DE NOVO*", msg)
        # Destaque
        self.assertIn("_Quando muda a pessoa e o final é o mesmo", msg)
        # Parágrafos
        self.assertIn("Neste momento há um movimento forte", msg)
        # Janela de tempo
        self.assertIn("até por volta de dezembro", msg)

    @patch("urllib.request.urlopen")
    def test_disparar_webhook_sucesso(self, mock_urlopen):
        # Simula resposta 200 do ZapVoice / automação
        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 200
        mock_resp.read.return_value = b'{"status":"success","history_id":999}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        meta_exemplo = {
            "nascimento": {"ano": 1995, "mes": 5, "dia": 20, "hora": 14, "minuto": 30},
            "cidade": {"nome": "São Paulo", "uf": "SP"},
            "quiz": {"area": "dinheiro", "espelho": "Insegurança", "quebra": "sim"},
            "casa_aberta": 12,
        }

        ok = disparar_webhook_leitura(
            nome_completo="Aryaraj Alves Fernandes",
            whatsapp="+55 (85) 99999-8888",
            carta=self.carta_exemplo,
            leitura_id="leitura-teste-001",
            meta=meta_exemplo,
        )
        self.assertTrue(ok)

        # Verifica dados enviados na requisição
        args, kwargs = mock_urlopen.call_args
        req = args[0]
        self.assertEqual(req.method, "POST")
        dados_enviados = json.loads(req.data.decode("utf-8"))

        self.assertEqual(dados_enviados["nome_completo"], "Aryaraj Alves Fernandes")
        self.assertEqual(dados_enviados["numero"], "+55 (85) 99999-8888")
        self.assertEqual(dados_enviados["phone"], "5585999998888")
        self.assertIn("VER O PADRÃO", dados_enviados["mensagem"])
        # Validação do envio conjunto de nascimento, cidade e quiz
        self.assertEqual(dados_enviados["nascimento"]["ano"], 1995)
        self.assertEqual(dados_enviados["cidade"]["nome"], "São Paulo")
        self.assertEqual(dados_enviados["quiz"]["area"], "dinheiro")
        self.assertEqual(dados_enviados["data"]["buyer"]["name"], "Aryaraj Alves Fernandes")
        self.assertEqual(dados_enviados["data"]["buyer"]["phone"], "+55 (85) 99999-8888")
        self.assertEqual(dados_enviados["data"]["custom_fields"]["mensagem"], dados_enviados["mensagem"])
        self.assertEqual(dados_enviados["data"]["custom_fields"]["nascimento"]["ano"], 1995)
        self.assertEqual(dados_enviados["data"]["custom_fields"]["cidade"]["uf"], "SP")

    @patch("urllib.request.urlopen")
    def test_disparar_webhook_com_estrelas_e_feedback(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 200
        mock_resp.read.return_value = b'{"status":"success"}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        ok = disparar_webhook_leitura(
            nome_completo="Aryaraj Alves Fernandes",
            whatsapp="+55 (85) 99999-8888",
            carta=self.carta_exemplo,
            leitura_id="leitura-teste-estrelas",
            estrelas=5,
            pulou=False,
        )
        self.assertTrue(ok)
        args, kwargs = mock_urlopen.call_args
        dados = json.loads(args[0].data.decode("utf-8"))

        self.assertEqual(dados["estrelas"], 5)
        self.assertEqual(dados["feedback_estrelas"], 5)
        self.assertEqual(dados["nota"], 5)
        self.assertFalse(dados["feedback_pulou"])
        self.assertEqual(dados["data"]["reading"]["estrelas"], 5)
        self.assertEqual(dados["data"]["reading"]["feedback_estrelas"], 5)
        self.assertEqual(dados["data"]["custom_fields"]["estrelas"], 5)
        self.assertEqual(dados["data"]["custom_fields"]["feedback_estrelas"], 5)

    @patch("servicos.webhook.disparar_webhook_leitura")
    def test_feedback_antecipa_e_cancela_timer(self, mock_disparar):
        from servicos.webhook import agendar_webhook_leitura, notificar_feedback_leitura, obter_agendamento, cancelar_agendamento

        lid = "leitura-teste-timer-001"
        agendar_webhook_leitura(
            leitura_id=lid,
            nome_completo="Lead Teste",
            whatsapp="+55 (85) 99999-1111",
            carta=self.carta_exemplo,
            delay_segundos=300.0,
        )

        ag = obter_agendamento(lid)
        self.assertIsNotNone(ag)
        self.assertFalse(ag["disparado"])

        # Usuário preenche a nota com 4 estrelas antes dos 5 minutos
        sucesso = notificar_feedback_leitura(lid, estrelas=4, pulou=False)
        self.assertTrue(sucesso)

        import time
        time.sleep(0.05)

        mock_disparar.assert_called_once()
        args, kwargs = mock_disparar.call_args
        self.assertEqual(kwargs.get("estrelas"), 4)
        self.assertFalse(kwargs.get("pulou"))
        self.assertIsNone(obter_agendamento(lid))

    @patch("servicos.webhook.disparar_webhook_leitura")
    def test_feedback_pulou_antecipa_e_cancela_timer(self, mock_disparar):
        from servicos.webhook import agendar_webhook_leitura, notificar_feedback_leitura, obter_agendamento

        lid = "leitura-teste-pulou-002"
        agendar_webhook_leitura(
            leitura_id=lid,
            nome_completo="Lead Pulou",
            whatsapp="+55 (85) 99999-2222",
            carta=self.carta_exemplo,
            delay_segundos=300.0,
        )

        sucesso = notificar_feedback_leitura(lid, estrelas=None, pulou=True)
        self.assertTrue(sucesso)

        import time
        time.sleep(0.05)

        mock_disparar.assert_called_once()
        args, kwargs = mock_disparar.call_args
        self.assertIsNone(kwargs.get("estrelas"))
        self.assertTrue(kwargs.get("pulou"))

    def test_webhook_leitura_url_configurada(self):
        import config
        self.assertTrue(hasattr(config, "WEBHOOK_LEITURA_URL"))
        self.assertTrue(len(config.WEBHOOK_LEITURA_URL) > 0)

    @patch("urllib.request.urlopen")
    def test_disparar_webhook_falha_resiliente(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Falha de rede simulada")
        ok = disparar_webhook_leitura(
            nome_completo="Pessoa Teste",
            whatsapp="+55 (11) 98765-4321",
            carta=self.carta_exemplo,
        )
        self.assertFalse(ok)

    def test_disparar_webhook_sem_url(self):
        ok = disparar_webhook_leitura(
            nome_completo="Pessoa Teste",
            whatsapp="+55 (11) 98765-4321",
            carta=self.carta_exemplo,
            url=""
        )
        self.assertFalse(ok)

    @patch("urllib.request.urlopen")
    def test_disparar_webhook_vsl_play_sucesso(self, mock_urlopen):
        from servicos.webhook import disparar_webhook_vsl_play

        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 200
        mock_resp.read.return_value = b'{"status":"ok"}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        ok = disparar_webhook_vsl_play(
            nome="Aline Yamamoto",
            whatsapp="+55 (16) 99600-3769",
            video_id="c6818306-fbe3-4919-b404-2f5b99424bc1",
            video_tipo="oferta",
            leitura_id="leitura-vsl-001",
            url="https://turb-back.exemplo.com/api/webhooks/vsl-play",
        )
        self.assertTrue(ok)

        args, kwargs = mock_urlopen.call_args
        req = args[0]
        self.assertEqual(req.method, "POST")
        dados = json.loads(req.data.decode("utf-8"))

        self.assertEqual(dados["event"], "vsl_play")
        self.assertEqual(dados["name"], "Aline Yamamoto")
        self.assertEqual(dados["nome"], "Aline Yamamoto")
        self.assertEqual(dados["phone"], "5516996003769")
        self.assertEqual(dados["numero"], "+55 (16) 99600-3769")
        self.assertEqual(dados["video_id"], "c6818306-fbe3-4919-b404-2f5b99424bc1")
        self.assertEqual(dados["video_tipo"], "oferta")
        self.assertEqual(dados["lead_id"], "leitura-vsl-001")
        self.assertEqual(dados["data"]["lead"]["name"], "Aline Yamamoto")
        self.assertEqual(dados["data"]["lead"]["clean_phone"], "5516996003769")
        self.assertEqual(dados["data"]["video"]["video_id"], "c6818306-fbe3-4919-b404-2f5b99424bc1")
        self.assertEqual(dados["data"]["video"]["tipo"], "oferta")

    @patch("urllib.request.urlopen")
    def test_disparar_webhook_vsl_play_falha_resiliente(self, mock_urlopen):
        from servicos.webhook import disparar_webhook_vsl_play

        mock_urlopen.side_effect = Exception("Conexão recusada")
        ok = disparar_webhook_vsl_play(
            nome="Falha Teste",
            whatsapp="11999999999",
            url="https://turb-back.exemplo.com/play",
        )
        self.assertFalse(ok)

    def test_disparar_webhook_vsl_play_sem_url(self):
        from servicos.webhook import disparar_webhook_vsl_play
        ok = disparar_webhook_vsl_play(nome="Teste", whatsapp="11999999999", url="")
        self.assertFalse(ok)

    @patch("servicos.webhook.disparar_webhook_vsl_play")
    def test_api_vsl_play_endpoint(self, mock_disparar):
        from fastapi.testclient import TestClient
        import main

        client = TestClient(main.app)
        payload = {
            "video_id": "c6818306-fbe3-4919-b404-2f5b99424bc1",
            "video_tipo": "oferta",
            "nome": "Maria Souza",
            "whatsapp": "+55 (11) 98888-7777",
            "leitura_id": "leitura-abc-123"
        }
        res = client.post("/api/vsl-play", json=payload)
        self.assertEqual(res.status_code, 200)
        dados = res.json()
        self.assertTrue(dados.get("ok"))
        self.assertEqual(dados.get("event"), "vsl_play")


if __name__ == "__main__":
    unittest.main()
