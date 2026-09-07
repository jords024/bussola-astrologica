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

    def test_cronometro_e_tempos_por_tela(self):
        """Verifica se o tempo em cada tela e o cronômetro acumulado são calculados."""
        d = [
            ev("time1", 1, "tela", {"de": 0, "para": 1, "ms_na_anterior": 4000, "ms_acumulado": 4000}),
            ev("time1", 2, "tela", {"de": 1, "para": 5, "ms_na_anterior": 2000, "ms_acumulado": 6000}),
            ev("time1", 3, "form_envio", {"ms_na_tela5": 15000}),
            ev("time1", 4, "tela", {"de": 5, "para": 10, "ms_na_anterior": 15000, "ms_acumulado": 21000}),
            ev("time1", 5, "oferta_clique", {"ms_na_tela": 8000, "ms_acumulado": 29000}),
        ]
        r = agregar(d, HOJE, HOJE)
        funil = {f["tela"]: f for f in r["funil"]}
        # Tela 0: durou 4000ms, cronômetro inicial 0
        self.assertEqual(funil[0]["tempo_na_tela_ms"], 4000.0)
        self.assertEqual(funil[0]["cronometro_ms"], 0.0)
        # Tela 1: durou 2000ms, cronômetro acumulado 4000ms
        self.assertEqual(funil[1]["tempo_na_tela_ms"], 2000.0)
        self.assertEqual(funil[1]["cronometro_ms"], 4000.0)
        # Tela 5: durou 15000ms, cronômetro acumulado 6000ms
        self.assertEqual(funil[5]["tempo_na_tela_ms"], 15000.0)
        self.assertEqual(funil[5]["cronometro_ms"], 6000.0)
        # Tela 10 (A oferta): durou 8000ms, cronômetro acumulado 21000ms
        self.assertEqual(funil[10]["tempo_na_tela_ms"], 8000.0)
        self.assertEqual(funil[10]["cronometro_ms"], 21000.0)
        # Checkout (✦): cronômetro acumulado 29000ms
        self.assertEqual(funil["✦"]["cronometro_ms"], 29000.0)
        # Resumo de tempos
        self.assertEqual(r["tempos"]["mediana_ate_oferta_ms"], 21000.0)
        self.assertEqual(r["tempos"]["mediana_ate_checkout_ms"], 29000.0)


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
            self.assertIn('data-tab="aba-leituras"', html_text)
            self.assertIn('data-tab="aba-formulario"', html_text)
            self.assertIn('data-tab="aba-astrologia"', html_text)
            self.assertIn('data-tab="aba-agente"', html_text)
            # Painéis correspondentes
            self.assertIn('id="aba-funil"', html_text)
            self.assertIn('id="aba-leituras"', html_text)
            self.assertIn('id="aba-formulario"', html_text)
            self.assertIn('id="aba-astrologia"', html_text)
            self.assertIn('id="aba-agente"', html_text)
            # Script de alternância e persistência de abas
            self.assertIn('function abrirAba(id)', html_text)
            self.assertIn('painel_aba_ativa', html_text)
            # Métricas e linha de checkout
            self.assertIn('foram ao checkout', html_text)
            self.assertIn('Clique no Checkout', html_text)
            # Métricas de tempo e cronômetro
            self.assertIn('tempo na tela', html_text)
            self.assertIn('cronômetro', html_text)
            self.assertIn('tempo médio no funil', html_text)
            self.assertIn('tempo até a oferta', html_text)


class Mascaramento(unittest.TestCase):
    def test_nome_data_e_fone(self):
        from api.painel import m_data, m_fone, m_nome
        self.assertEqual(m_nome("Maria Silva Souza"), "Mar** S. S.")
        self.assertNotIn("Silva", m_nome("Maria Silva Souza"))
        self.assertNotIn("1991", m_data({"dia": 14, "mes": 3, "ano": 1991}))
        self.assertEqual(m_fone("(54) 99999-1234"), "…1234")


class LeiturasPainelSemMascara(unittest.TestCase):
    def setUp(self):
        from main import app
        self.c = TestClient(app)

    def test_formatadores_completos(self):
        from api.painel import f_data, f_hora, f_tempo
        # Data com ano de 2 dígitos (ex: 09/03/98, 05/11/03)
        self.assertEqual(f_data({"dia": 9, "mes": 3, "ano": 1998}), "09/03/98")
        self.assertEqual(f_data({"dia": 5, "mes": 11, "ano": 2003}), "05/11/03")
        self.assertEqual(f_data({}), "—")

        # Hora e minuto de nascimento
        self.assertEqual(f_hora({"hora": 18, "minuto": 35}), "18h35")
        self.assertEqual(f_hora({"hora": 4, "minuto": 5}), "04h05")
        self.assertEqual(f_hora({"hora": 0, "minuto": 0}), "00h00")
        self.assertEqual(f_hora({"hora": None, "periodo": "manha"}), "manha")
        self.assertEqual(f_hora({"hora": None}, {"modo_hora": "desconhecida"}), "desconhecida")
        self.assertEqual(f_hora({}), "—")

        # Formatador de tempo e cronômetro
        self.assertEqual(f_tempo(None), "—")
        self.assertEqual(f_tempo(-10), "—")
        self.assertEqual(f_tempo(3500), "4s")
        self.assertEqual(f_tempo(45000), "45s")
        self.assertEqual(f_tempo(60000), "1m")
        self.assertEqual(f_tempo(75000), "1m 15s")
        self.assertEqual(f_tempo(135000), "2m 15s")

    def test_lista_e_detalhe_leituras_mostram_dados_completos(self):
        """Verifica se /painel/leituras e /painel/leitura/{id} exibem nome completo, ano completo, hora/minuto e tempo no quiz."""
        leitura_id = "20260907-123456-abcdef12"
        dados_leitura = {
            "cliente_id": "test-id",
            "nome_completo": "Aryaraj Alves Fernandes",
            "nascimento": {
                "ano": 1998,
                "mes": 3,
                "dia": 9,
                "hora": 18,
                "minuto": 35,
                "precisao": "exata",
            },
            "cidade": {"nome": "Fortaleza", "uf": "Ceará"},
            "quiz": {"area": "amor"},
            "tempo_quiz_ms": 95000,
            "veredito": {"tipo": "CONFIRMACAO", "casa_eleita_real": True, "casa_aberta": 7},
            "precisao": {"modo_hora": "exata"},
            "whatsapp": "85999998888",
            "carta": {
                "selo": "Selo Teste",
                "titulo": "Titulo Teste",
                "destaque": "Destaque Teste",
                "paragrafos": ["Paragrafo 1"],
                "notas": ["Nota 1"]
            },
            "meta": {}
        }
        with TemporaryDirectory() as tmpdir:
            dir_leituras = Path(tmpdir)
            arq_leitura = dir_leituras / f"{leitura_id}.json"
            arq_leitura.write_text(json.dumps(dados_leitura), encoding="utf-8")

            with mock.patch.object(config, "DIR_LEITURAS", dir_leituras), \
                 mock.patch.object(config, "PAINEL_SENHA", "senha_teste"), \
                 mock.patch.object(config, "PAINEL_USUARIO", "crassus"):

                # Teste da lista de leituras
                resp_lista = self.c.get("/painel/leituras", auth=("crassus", "senha_teste"))
                self.assertEqual(resp_lista.status_code, 200)
                txt_lista = resp_lista.text

                # Nome completo sem asteriscos
                self.assertIn("Aryaraj Alves Fernandes", txt_lista)
                self.assertNotIn("Ary***", txt_lista)

                # Data com ano de 2 dígitos
                self.assertIn("09/03/98", txt_lista)
                self.assertNotIn("19XX", txt_lista)

                # Horário e minuto
                self.assertIn("18h35", txt_lista)

                # WhatsApp completo
                self.assertIn("85999998888", txt_lista)

                # Tempo no quiz
                self.assertIn("tempo no quiz", txt_lista)
                self.assertIn("1m 35s", txt_lista)

                # Data e horário de chegada no quiz em horário de Brasília
                self.assertIn("chegou ao quiz (bsb)", txt_lista)

                # Teste do detalhe da leitura
                resp_detalhe = self.c.get(f"/painel/leitura/{leitura_id}", auth=("crassus", "senha_teste"))
                self.assertEqual(resp_detalhe.status_code, 200)
                txt_detalhe = resp_detalhe.text

                self.assertIn("Aryaraj Alves Fernandes", txt_detalhe)
                self.assertIn("09/03/98", txt_detalhe)
                self.assertIn("18h35", txt_detalhe)
                self.assertIn("85999998888", txt_detalhe)
                self.assertIn("https://wa.me/5585999998888", txt_detalhe)
                self.assertIn("tempo no quiz: 1m 35s", txt_detalhe)
                self.assertIn("chegou ao quiz", txt_detalhe)
                self.assertIn("(BSB)", txt_detalhe)

    def test_f_wa_link(self):
        from api.painel import f_wa
        self.assertEqual(f_wa(None), "—")
        self.assertEqual(f_wa(""), "—")
        self.assertEqual(f_wa("—"), "—")
        # Número brasileiro sem DDI recebe 55 no wa.me
        link_br = f_wa("11987654321")
        self.assertIn('href="https://wa.me/5511987654321"', link_br)
        self.assertIn('11987654321', link_br)
        # Número com DDI +55 e máscara
        link_br_formatado = f_wa("+55 (11) 98765-4321")
        self.assertIn('href="https://wa.me/5511987654321"', link_br_formatado)
        self.assertIn('+55 (11) 98765-4321', link_br_formatado)
        # Número internacional (Portugal)
        link_pt = f_wa("+351 912 345 678")
        self.assertIn('href="https://wa.me/351912345678"', link_pt)
        self.assertIn('+351 912 345 678', link_pt)

    def test_f_chegada_bsb_calculo_correto(self):
        from api.painel import f_chegada_bsb
        # 2026-09-07 13:26:22 UTC = 10:26:22 BSB.
        # Com tempo_quiz_ms = 197000 ms (3m 17s), chegada = 10:23:05 BSB -> formato curto 07/09/26 10:23.
        d = {
            "gravado_em": "2026-09-07T13:26:22",
            "tempo_quiz_ms": 197000
        }
        chegada, gerada = f_chegada_bsb(d, "20260907-132622")
        self.assertEqual(chegada, "07/09/26 10:23")
        self.assertEqual(gerada, "07/09/26 10:26")

        # Teste quando tempo_quiz_ms é ausente ou zero
        d2 = {"gravado_em": "2026-09-07T13:00:00"}
        chegada2, gerada2 = f_chegada_bsb(d2, "20260907-130000")
        self.assertEqual(chegada2, "07/09/26 10:00")
        self.assertEqual(gerada2, "07/09/26 10:00")

    def test_f_data_dois_digitos(self):
        from api.painel import f_data
        self.assertEqual(f_data({"dia": 9, "mes": 3, "ano": 1998}), "09/03/98")
        self.assertEqual(f_data({"dia": 7, "mes": 9, "ano": 2026}), "07/09/26")
        self.assertEqual(f_data({"dia": 15, "mes": 8, "ano": 1995}), "15/08/95")
        self.assertEqual(f_data({}), "—")

    def test_paginacao_leituras_20_por_pagina(self):
        from api.painel import _tabela_leituras
        with TemporaryDirectory() as tmpdir:
            dir_leituras = Path(tmpdir)
            # Cria 25 leituras fictícias
            for i in range(25):
                arq = dir_leituras / f"20260907-12{i:02d}00-abcdef{i:02d}.json"
                conteudo = {
                    "nome_completo": f"Usuario Teste {i}",
                    "nascimento": {"dia": 1, "mes": 1, "ano": 1990, "hora": 12, "minuto": 0},
                    "cidade": {"nome": "Sao Paulo", "uf": "SP"},
                    "quiz": {"area": "amor"},
                    "tempo_quiz_ms": 60000,
                    "veredito": {"tipo": "CAUSA_OCULTA", "casa_eleita_real": True, "casa_aberta": 7}
                }
                arq.write_text(json.dumps(conteudo), encoding="utf-8")

            with mock.patch.object(config, "DIR_LEITURAS", dir_leituras):
                # Página 0 (deve trazer 20 itens)
                corpo_p0, total_p0, pags_p0, unicos_p0 = _tabela_leituras(pagina=0, por_pagina=20)
                self.assertEqual(total_p0, 25)
                self.assertEqual(unicos_p0, 25)
                self.assertEqual(pags_p0, 2)
                # O corpo da página 0 tem 20 linhas de dados (mais o cabeçalho)
                self.assertEqual(corpo_p0.count("<tr>"), 21)

                # Página 1 (deve trazer os 5 itens restantes)
                corpo_p1, total_p1, pags_p1, unicos_p1 = _tabela_leituras(pagina=1, por_pagina=20)
                self.assertEqual(total_p1, 25)
                self.assertEqual(unicos_p1, 25)
                self.assertEqual(pags_p1, 2)
                self.assertEqual(corpo_p1.count("<tr>"), 6)

    def test_barra_paginacao_html(self):
        from api.painel import _barra_paginacao
        # Teste com 25 itens, página 0
        html_p0 = _barra_paginacao(0, 25, "/painel", {"dias": 7}, por_pagina=20, param_nome="pag_leituras", hash_tab="#aba-leituras")
        self.assertIn("Mostrando <b>1–20</b> de <b>25</b> leituras", html_p0)
        self.assertIn("Página 1 de 2", html_p0)
        self.assertIn("class=\"pag-btn disabled\">← Anterior", html_p0)
        self.assertIn("pag_leituras=1#aba-leituras", html_p0)
        self.assertIn("Próxima →", html_p0)

        # Teste na página 1 (última página)
        html_p1 = _barra_paginacao(1, 25, "/painel", {"dias": 7}, por_pagina=20, param_nome="pag_leituras", hash_tab="#aba-leituras")
        self.assertIn("Mostrando <b>21–25</b> de <b>25</b> leituras", html_p1)
        self.assertIn("Página 2 de 2", html_p1)
        self.assertIn("← Anterior", html_p1)
        self.assertIn("pag_leituras=0#aba-leituras", html_p1)
        self.assertIn("class=\"pag-btn disabled\">Próxima →", html_p1)

    def test_atualizar_progresso_registro(self):
        from servicos import registro
        with TemporaryDirectory() as tmpdir:
            dir_leituras = Path(tmpdir)
            with mock.patch.object(config, "DIR_LEITURAS", dir_leituras), \
                 mock.patch.object(registro, "DIR_LEITURAS", dir_leituras):
                lid = "20260907-120000-11223344"
                dados = {
                    "nome_completo": "Cliente Teste",
                    "etapa_max": 7,
                    "etapa_nome": "Tela 7 (Leitura)",
                    "checkout": False,
                }
                (dir_leituras / f"{lid}.json").write_text(json.dumps(dados), encoding="utf-8")

                # Atualiza para tela 8
                ok = registro.atualizar_progresso(lid, tela=8)
                self.assertTrue(ok)
                d_pos = json.loads((dir_leituras / f"{lid}.json").read_text(encoding="utf-8"))
                self.assertEqual(d_pos["etapa_max"], 8)
                self.assertEqual(d_pos["etapa_nome"], "Tela 8 (Portas)")
                self.assertFalse(d_pos["checkout"])

                # Atualiza para checkout
                ok2 = registro.atualizar_progresso(lid, tela=10, checkout=True)
                self.assertTrue(ok2)
                d_pos2 = json.loads((dir_leituras / f"{lid}.json").read_text(encoding="utf-8"))
                self.assertEqual(d_pos2["etapa_max"], 10)
                self.assertEqual(d_pos2["etapa_nome"], "Tela 10 (Oferta)")
                self.assertTrue(d_pos2["checkout"])

    def test_obter_progresso_leituras_eventos(self):
        from api.painel import obter_progresso_leituras
        with TemporaryDirectory() as tmpdir:
            dir_ev = Path(tmpdir)
            hoje_str = date.today().strftime("%Y-%m-%d")
            arq_ev = dir_ev / f"{hoje_str}.jsonl"

            # Eventos: sid1 avançou até tela 8 (portas), sid2 avançou até tela 10 e clicou checkout
            linhas_ev = [
                {"sid": "sid1", "seq": 1, "evt": "tela", "props": {"de": 7, "para": 8}},
                {"sid": "sid2", "seq": 1, "evt": "tela", "props": {"de": 7, "para": 10}},
                {"sid": "sid2", "seq": 2, "evt": "oferta_clique", "props": {"botao": "principal"}},
            ]
            arq_ev.write_text("\n".join(json.dumps(e) for e in linhas_ev) + "\n", encoding="utf-8")

            with mock.patch.object(config, "DIR_EVENTOS", dir_ev):
                itens = [
                    ("20260907-100000-aaaa1111", {"cliente_id": "sid1", "etapa_max": 7}),
                    ("20260907-100500-bbbb2222", {"cliente_id": "sid2", "etapa_max": 7}),
                    ("20260907-101000-cccc3333", {"cliente_id": "sid3", "etapa_max": 7}),
                ]
                prog = obter_progresso_leituras(itens)

                self.assertEqual(prog["20260907-100000-aaaa1111"]["max_tela"], 8)
                self.assertEqual(prog["20260907-100000-aaaa1111"]["rotulo"], "Tela 8 (Portas)")
                self.assertFalse(prog["20260907-100000-aaaa1111"]["checkout"])

                self.assertEqual(prog["20260907-100500-bbbb2222"]["max_tela"], 10)
                self.assertEqual(prog["20260907-100500-bbbb2222"]["rotulo"], "Tela 10 (Oferta)")
                self.assertTrue(prog["20260907-100500-bbbb2222"]["checkout"])

                self.assertEqual(prog["20260907-101000-cccc3333"]["max_tela"], 7)
                self.assertEqual(prog["20260907-101000-cccc3333"]["rotulo"], "Tela 7 (Leitura)")
                self.assertFalse(prog["20260907-101000-cccc3333"]["checkout"])

    def test_tabela_leituras_exibe_novas_colunas(self):
        from api.painel import _tabela_leituras
        with TemporaryDirectory() as tmpdir:
            dir_leituras = Path(tmpdir)
            arq = dir_leituras / "20260907-120000-12345678.json"
            conteudo = {
                "nome_completo": "Ana Pereira",
                "gravado_em": "2026-09-07T13:30:00",
                "chegou_em_bsb": "07/09/2026 10:25:00",
                "gravado_em_bsb": "07/09/2026 10:30:00",
                "etapa_max": 10,
                "etapa_nome": "Tela 10 (Oferta)",
                "checkout": True,
                "nascimento": {"dia": 10, "mes": 5, "ano": 1992, "hora": 14, "minuto": 30},
                "cidade": {"nome": "Campinas", "uf": "SP"},
                "quiz": {"area": "carreira"},
                "whatsapp": "+55 (19) 99999-8888",
                "tempo_quiz_ms": 300000,
                "veredito": {"tipo": "CAUSA_OCULTA", "casa_eleita_real": True, "casa_aberta": 10}
            }
            arq.write_text(json.dumps(conteudo), encoding="utf-8")

            with mock.patch.object(config, "DIR_LEITURAS", dir_leituras):
                corpo, total, pags, unicos = _tabela_leituras(pagina=0, por_pagina=20)
                self.assertEqual(total, 1)
                self.assertEqual(unicos, 1)
                # Verifica cabeçalhos esperados
                self.assertIn("chegou ao quiz (bsb)", corpo)
                self.assertIn("preencheu dados (bsb)", corpo)
                self.assertIn("etapa alcançada", corpo)
                self.assertIn("checkout", corpo)

                # Verifica valores na linha de dados (formato curto: 2 dígitos no ano e sem segundos)
                self.assertIn("07/09/26 10:25", corpo)
                self.assertIn("07/09/26 10:30", corpo)
                self.assertIn("10/05/92", corpo)
                self.assertIn("Tela 10 (Oferta)", corpo)
                self.assertIn("tag-checkout sim", corpo)
                self.assertIn("✦ SIM", corpo)
                self.assertIn("Ana Pereira", corpo)

    def test_deduplicacao_leituras_e_badge_repeticao(self):
        """Verifica se envios repetidos da mesma pessoa exibem a tag Nx e contam como 1 única pessoa."""
        from api.painel import _tabela_leituras, _contagens_leituras
        with TemporaryDirectory() as tmpdir:
            dir_leituras = Path(tmpdir)
            # Pessoa A enviou 3 vezes (com o mesmo WhatsApp)
            for i in range(3):
                arq = dir_leituras / f"20260907-120{i}00-aaaa000{i}.json"
                conteudo = {
                    "nome_completo": "Carlos Eduardo",
                    "nascimento": {"dia": 15, "mes": 4, "ano": 1985},
                    "whatsapp": "(11) 98888-1234",
                    "cliente_id": f"sid-a-{i}",
                }
                arq.write_text(json.dumps(conteudo), encoding="utf-8")

            # Pessoa B enviou 1 vez
            arq_b = dir_leituras / "20260907-121000-bbbb0001.json"
            conteudo_b = {
                "nome_completo": "Fernanda Lima",
                "nascimento": {"dia": 20, "mes": 8, "ano": 1993},
                "whatsapp": "21977775555",
                "cliente_id": "sid-b",
            }
            arq_b.write_text(json.dumps(conteudo_b), encoding="utf-8")

            with mock.patch.object(config, "DIR_LEITURAS", dir_leituras):
                corpo, total, pags, unicos = _tabela_leituras(pagina=0, por_pagina=20)
                self.assertEqual(total, 4)
                self.assertEqual(unicos, 2)  # 4 envios, mas apenas 2 pessoas únicas
                self.assertIn('Carlos Eduardo <span class="tag-rep" title="Preencheu o formulário 3 vezes">3x</span>', corpo)
                self.assertIn("Fernanda Lima", corpo)
                self.assertNotIn("Fernanda Lima <span class=\"tag-rep\"", corpo)

    def test_pessoas_unicas_no_agregador(self):
        """Verifica se o agregador contabiliza pessoas únicas via aid e inclui no funil."""
        # 3 sessões do mesmo visitante (aid: aid-1) em telas diferentes
        d = [
            {"sid": "s1", "aid": "aid-1", "seq": 1, "evt": "tela", "props": {"de": 0, "para": 1}, "ts": T0.isoformat(), "bot": False, "teste": False},
            {"sid": "s2", "aid": "aid-1", "seq": 1, "evt": "tela", "props": {"de": 0, "para": 5}, "ts": T0.isoformat(), "bot": False, "teste": False},
            {"sid": "s2", "aid": "aid-1", "seq": 2, "evt": "form_envio", "props": {}, "ts": T0.isoformat(), "bot": False, "teste": False},
            {"sid": "s3", "aid": "aid-1", "seq": 1, "evt": "tela", "props": {"de": 0, "para": 10}, "ts": T0.isoformat(), "bot": False, "teste": False},
            # 1 sessão de outro visitante (aid: aid-2)
            {"sid": "s4", "aid": "aid-2", "seq": 1, "evt": "tela", "props": {"de": 0, "para": 1}, "ts": T0.isoformat(), "bot": False, "teste": False},
        ]
        r = agregar(d, HOJE, HOJE)
        self.assertEqual(r["sessoes"], 4)
        self.assertEqual(r["pessoas_unicas"], 2)

        # No funil:
        funil_map = {f["tela"]: f for f in r["funil"]}
        # Tela 0: 4 sessões, 2 pessoas
        self.assertEqual(funil_map[0]["sessoes"], 4)
        self.assertEqual(funil_map[0]["pessoas"], 2)
        # Tela 5: 1 sessão, 1 pessoa
        self.assertEqual(funil_map[5]["sessoes"], 1)
        self.assertEqual(funil_map[5]["pessoas"], 1)
        # Formulário:
        self.assertEqual(r["formulario"]["chegaram_pessoas"], 1)
        self.assertEqual(r["formulario"]["enviaram_pessoas"], 1)

    def test_detalhe_leitura_exibe_progresso_e_checkout(self):
        from api.painel import detalhe
        with TemporaryDirectory() as tmpdir:
            dir_leituras = Path(tmpdir)
            lid = "20260907-120000-87654321"
            arq = dir_leituras / f"{lid}.json"
            conteudo = {
                "nome_completo": "Juliana Souza",
                "gravado_em": "2026-09-07T13:30:00",
                "chegou_em_bsb": "07/09/2026 10:20:00",
                "gravado_em_bsb": "07/09/2026 10:30:00",
                "etapa_max": 8,
                "etapa_nome": "Tela 8 (Portas)",
                "checkout": False,
                "nascimento": {"dia": 22, "mes": 3, "ano": 1988, "hora": 8, "minuto": 15},
                "cidade": {"nome": "Rio de Janeiro", "uf": "RJ"},
                "quiz": {"area": "amor"},
                "whatsapp": "+55 (21) 98888-7777",
                "tempo_quiz_ms": 600000,
                "veredito": {"tipo": "CAUSA_OCULTA", "casa_eleita_real": True, "casa_aberta": 7},
                "carta": {"selo": "Casa 7", "titulo": "A porta do encontro", "destaque": "Destaque", "paragrafos": ["P1"], "notas": ["N1"]}
            }
            arq.write_text(json.dumps(conteudo), encoding="utf-8")

            with mock.patch.object(config, "DIR_LEITURAS", dir_leituras):
                resp = detalhe(lid, _="crassus")
                html_resp = resp.body.decode("utf-8")
                self.assertIn("chegou ao quiz:", html_resp)
                self.assertIn("07/09/26 10:20", html_resp)
                self.assertIn("preencheu dados:", html_resp)
                self.assertIn("07/09/26 10:30", html_resp)
                self.assertIn("22/03/88", html_resp)
                self.assertIn("etapa:", html_resp)
                self.assertIn("Tela 8 (Portas)", html_resp)
                self.assertIn("checkout:", html_resp)
                self.assertIn("Não", html_resp)


if __name__ == "__main__":
    unittest.main()
