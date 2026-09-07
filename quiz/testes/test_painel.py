# -*- coding: utf-8 -*-
"""Testes do rastreamento, do agregador e do painel.

Cada teste aqui corresponde a um jeito concreto de o painel mentir.
"""
import json
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from fastapi.testclient import TestClient

import config
from servicos import eventos
from servicos.agregador import MIN_PARA_PORCENTAGEM, agregar

HOJE = date.today()
T0 = datetime.now().astimezone() - timedelta(hours=2)


def ev(sid, seq, evt, props=None, off=0, **kw):
    return {"sid": sid, "seq": seq, "evt": evt, "props": props or {},
            "ts": (T0 + timedelta(seconds=off)).isoformat(),
            "bot": False, "teste": False, "disp": "movel", **kw}


class Agregador(unittest.TestCase):
    def test_duplicata_nao_conta_duas_vezes(self):
        """O replay da fila após um fechamento no meio do voo reenvia eventos."""
        d = [ev("a", 1, "tela", {"de": 0, "para": 1}),
             ev("a", 1, "tela", {"de": 0, "para": 1})]
        r = agregar(d, HOJE, HOJE)
        self.assertEqual(r["sessoes"], 1)
        self.assertEqual(r["funil"][1]["sessoes"], 1)

    def test_voltar_nao_vira_abandono(self):
        """Com o botão voltar, o conjunto de telas não é um prefixo."""
        d = [ev("b", 1, "tela", {"de": 4, "para": 5}),
             ev("b", 2, "tela", {"de": 5, "para": 4}),
             ev("b", 3, "tela", {"de": 4, "para": 5})]
        r = agregar(d, HOJE, HOJE)
        self.assertEqual(r["funil"][5]["sessoes"], 1)
        self.assertEqual(r["funil"][4]["sessoes"], 1)

    def test_sessao_atravessa_meia_noite_conta_uma_vez(self):
        ontem = HOJE - timedelta(days=1)
        t = datetime.combine(ontem, datetime.min.time()).astimezone() + timedelta(hours=23, minutes=57)
        d = [{"sid": "c", "seq": 1, "evt": "tela", "props": {"de": 0, "para": 1},
              "ts": t.isoformat(), "bot": False, "teste": False},
             {"sid": "c", "seq": 2, "evt": "tela", "props": {"de": 1, "para": 2},
              "ts": (t + timedelta(minutes=10)).isoformat(), "bot": False, "teste": False}]
        self.assertEqual(agregar(d, ontem, HOJE)["sessoes"], 1)

    def test_bot_e_teste_saem_por_padrao(self):
        d = [ev("d1", 1, "tela", {"de": 0, "para": 1}, bot=True),
             ev("d2", 1, "tela", {"de": 0, "para": 1}, teste=True),
             ev("d3", 1, "tela", {"de": 0, "para": 1})]
        self.assertEqual(agregar(d, HOJE, HOJE)["sessoes"], 1)
        self.assertEqual(agregar(d, HOJE, HOJE, incluir_bots=True,
                                 incluir_teste=True)["sessoes"], 3)

    def test_cacheada_fora_da_mediana(self):
        """ms_llm 0 puxaria a mediana para baixo e esconderia lentidão real."""
        d = [ev("e1", -1, "leitura_entregue", {"cached": True, "ms_llm": 0}),
             ev("e2", -1, "leitura_entregue", {"cached": False, "ms_llm": 12000})]
        g = agregar(d, HOJE, HOJE)["geracao"]
        self.assertEqual(g["mediana_ms"], 12000)
        self.assertEqual(g["cacheadas"], 1)

    def test_leitura_sem_casa_real_fora_do_cenario(self):
        """Sem hora não há placar; incluir faria um cenário dominar à toa."""
        d = [ev("f1", -1, "leitura_entregue", {"casa_eleita_real": False, "cenario": "SEM_CASAS"}),
             ev("f2", -1, "leitura_entregue", {"casa_eleita_real": True,
                                               "cenario": "CAUSA_OCULTA", "casa_aberta": 9})]
        c = agregar(d, HOJE, HOJE)["cenarios"]
        self.assertEqual(c["total"], 1)
        self.assertEqual(c["excluidas_sem_casa"], 1)

    def test_porcentagem_suprimida_com_amostra_pequena(self):
        d = [ev("g", 1, "tela", {"de": 0, "para": 1})]
        self.assertIsNone(agregar(d, HOJE, HOJE)["funil"][0]["pct_do_topo"])

    def test_ultima_escolha_de_area_vale(self):
        """Quem clica em três opções não pode virar três pessoas."""
        d = [ev("h", 1, "escolha", {"campo": "area", "valor": "carreira"}),
             ev("h", 2, "escolha", {"campo": "area", "valor": "amor"})]
        self.assertEqual(agregar(d, HOJE, HOJE)["areas"], [("amor", 1)])

    def test_clique_checkout_no_funil(self):
        """Verifica se o clique no checkout na tela da oferta é agregado corretamente no funil."""
        d = [
            ev("chk", 1, "tela", {"de": 0, "para": 10}),
            ev("chk", 2, "oferta_clique", {"botao": "principal"}),
        ]
        r = agregar(d, HOJE, HOJE)
        self.assertEqual(r["checkout"]["cliques"], 1)
        self.assertEqual(r["funil"][10]["nome"], "A oferta")
        self.assertEqual(r["funil"][10]["sessoes"], 1)
        self.assertEqual(r["funil"][11]["nome"], "Clique no Checkout")
        self.assertEqual(r["funil"][11]["sessoes"], 1)
        self.assertEqual(r["funil"][11]["tela"], "✦")


class Eventos(unittest.TestCase):
    def test_evento_invalido_e_descartado(self):
        lote = {"sid": "abcd1234-aa", "aid": "wxyz9876-bb", "eventos": [
            {"seq": 1, "evt": "tela", "props": {}},
            {"seq": 2, "evt": "inventado", "props": {}},
        ]}
        self.assertEqual(len(eventos.normalizar(lote, "1.1.1.1", "")), 1)

    def test_sid_malformado_rejeita_o_lote(self):
        lote = {"sid": "x", "aid": "wxyz9876-bb", "eventos": [{"seq": 1, "evt": "tela"}]}
        self.assertEqual(eventos.normalizar(lote, "1.1.1.1", ""), [])

    def test_deteccao_de_bot(self):
        self.assertTrue(eventos.e_bot("WhatsApp/2.23"))
        self.assertTrue(eventos.e_bot("facebookexternalhit/1.1"))
        self.assertFalse(eventos.e_bot("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)"))

    def test_ua_crua_nao_e_gravada(self):
        ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) segredo"
        linha = eventos.normalizar(
            {"sid": "abcd1234-aa", "aid": "wxyz9876-bb",
             "eventos": [{"seq": 1, "evt": "tela"}]}, "1.1.1.1", ua)[0]
        self.assertNotIn("segredo", json.dumps(linha))
        self.assertEqual(linha["disp"], "movel")


class Endpoint(unittest.TestCase):
    def setUp(self):
        from main import app
        self.c = TestClient(app)

    def test_sempre_204(self):
        """4xx apareceria no console de quem inspecionar a página."""
        self.assertEqual(self.c.post("/api/evento", json={"sid": "x"}).status_code, 204)
        self.assertEqual(self.c.post("/api/evento", content=b"nao e json").status_code, 204)
        self.assertEqual(self.c.post("/api/evento", content=b"x" * 20000).status_code, 204)

    def test_painel_exige_senha(self):
        with mock.patch.object(config, "PAINEL_SENHA", "senha_teste"):
            self.assertEqual(self.c.get("/painel").status_code, 401)
            self.assertEqual(self.c.get("/painel", auth=("crassus", "errada")).status_code, 401)

    def test_painel_desativado_quando_sem_senha(self):
        with mock.patch.object(config, "PAINEL_SENHA", ""):
            self.assertEqual(self.c.get("/painel").status_code, 503)

    def test_dados_nao_sao_servidos(self):
        self.assertEqual(self.c.get("/dados/leituras/x.json").status_code, 404)
        self.assertEqual(self.c.get("/estatico/../.env").status_code, 404)

    def test_falha_ao_gravar_evento_nao_derruba_o_endpoint(self):
        with mock.patch.object(eventos, "gravar", side_effect=RuntimeError("disco")):
            r = self.c.post("/api/evento", json={
                "sid": "abcd1234-aa", "aid": "wxyz9876-bb",
                "eventos": [{"seq": 1, "evt": "tela"}]})
        self.assertEqual(r.status_code, 204)

    def test_painel_renderiza_abas_e_conteudo(self):
        with mock.patch.object(config, "PAINEL_SENHA", "senha_teste"), \
             mock.patch.object(config, "PAINEL_USUARIO", "crassus"):
            resp = self.c.get("/painel", auth=("crassus", "senha_teste"))
            self.assertEqual(resp.status_code, 200)
            html_text = resp.text
            # Barra de navegação de abas
            self.assertIn('<nav class="abas">', html_text)
            self.assertIn('data-tab="aba-funil"', html_text)
            self.assertIn('data-tab="aba-formulario"', html_text)
            self.assertIn('data-tab="aba-astrologia"', html_text)
            self.assertIn('data-tab="aba-agente"', html_text)
            # Painéis correspondentes
            self.assertIn('id="aba-funil"', html_text)
            self.assertIn('id="aba-formulario"', html_text)
            self.assertIn('id="aba-astrologia"', html_text)
            self.assertIn('id="aba-agente"', html_text)
            # Script de alternância e persistência de abas
            self.assertIn('function abrirAba(id)', html_text)
            self.assertIn('painel_aba_ativa', html_text)
            # Métricas e linha de checkout
            self.assertIn('foram ao checkout', html_text)
            self.assertIn('Clique no Checkout', html_text)


class Mascaramento(unittest.TestCase):
    def test_nome_data_e_fone(self):
        from api.painel import m_data, m_fone, m_nome
        self.assertEqual(m_nome("Maria Silva Souza"), "Mar** S. S.")
        self.assertNotIn("Silva", m_nome("Maria Silva Souza"))
        self.assertNotIn("1991", m_data({"dia": 14, "mes": 3, "ano": 1991}))
        self.assertEqual(m_fone("(54) 99999-1234"), "…1234")


if __name__ == "__main__":
    unittest.main()
