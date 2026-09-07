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
        # Simula resposta 200 do ZapVoice
        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 200
        mock_resp.read.return_value = b'{"status":"success","history_id":999}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        ok = disparar_webhook_leitura(
            nome_completo="Aryaraj Alves Fernandes",
            whatsapp="+55 (85) 99999-8888",
            carta=self.carta_exemplo,
            leitura_id="leitura-teste-001"
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
        self.assertEqual(dados_enviados["data"]["buyer"]["name"], "Aryaraj Alves Fernandes")
        self.assertEqual(dados_enviados["data"]["buyer"]["phone"], "+55 (85) 99999-8888")
        self.assertEqual(dados_enviados["data"]["custom_fields"]["mensagem"], dados_enviados["mensagem"])

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


if __name__ == "__main__":
    unittest.main()
