# -*- coding: utf-8 -*-
"""Testes do rastreamento, do agregador e do painel.

Cada teste aqui corresponde a um jeito concreto de o painel mentir.
"""
import json
import unittest
from datetime import date, datetime, timedelta, timezone
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
            self.assertNotIn('data-tab="aba-agente"', html_text)
            # Painéis correspondentes
            self.assertIn('id="aba-funil"', html_text)
            self.assertIn('id="aba-leituras"', html_text)
            self.assertIn('id="aba-formulario"', html_text)
            self.assertIn('id="aba-astrologia"', html_text)
            self.assertNotIn('id="aba-agente"', html_text)
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
                corpo_p0, total_p0, pags_p0, unicos_p0, chk_p0, geral_p0 = _tabela_leituras(pagina=0, por_pagina=20)
                self.assertEqual(total_p0, 25)
                self.assertEqual(geral_p0, 25)
                self.assertEqual(unicos_p0, 25)
                self.assertEqual(pags_p0, 2)
                # O corpo da página 0 tem 20 linhas de dados (mais o cabeçalho)
                self.assertEqual(corpo_p0.count("<tr"), 21)

                # Página 1 (deve trazer os 5 itens restantes)
                corpo_p1, total_p1, pags_p1, unicos_p1, chk_p1, geral_p1 = _tabela_leituras(pagina=1, por_pagina=20)
                self.assertEqual(total_p1, 25)
                self.assertEqual(geral_p1, 25)
                self.assertEqual(unicos_p1, 25)
                self.assertEqual(pags_p1, 2)
                self.assertEqual(corpo_p1.count("<tr"), 6)

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
                corpo, total, pags, unicos, chk, geral = _tabela_leituras(pagina=0, por_pagina=20)
                self.assertEqual(total, 1)
                self.assertEqual(geral, 1)
                self.assertEqual(chk, 1)
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
        """Verifica se envios repetidos da mesma pessoa exibem o botão de acordeão e contam como 1 única pessoa."""
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
                corpo, total, pags, unicos, chk, geral = _tabela_leituras(pagina=0, por_pagina=20)
                self.assertEqual(total, 4)
                self.assertEqual(geral, 4)
                self.assertEqual(unicos, 2)  # 4 envios, mas apenas 2 pessoas únicas
                self.assertIn("Carlos Eduardo", corpo)
                self.assertIn("btn-acordeao", corpo)
                self.assertIn("toggleAcordeao", corpo)
                self.assertIn('title="Preencheu o formulário 3 vezes">3x</span>', corpo)
                self.assertIn("Fernanda Lima", corpo)
                self.assertNotIn("Fernanda Lima <button", corpo)
                # Verifica se as sub-linhas foram renderizadas ocultas
                self.assertIn("tr-subleitura", corpo)
                self.assertIn("↳ tentativa anterior", corpo)
                self.assertIn('style="display:none;"', corpo)

    def test_filtro_so_checkout_na_tabela_e_painel(self):
        """Verifica o botão e filtro para exibir exclusivamente leads que foram ao checkout."""
        from api.painel import _tabela_leituras, painel
        from starlette.requests import Request
        with TemporaryDirectory() as tmpdir:
            dir_leituras = Path(tmpdir)
            # Lead 1: foi ao checkout
            arq1 = dir_leituras / "20260907-100000-11111111.json"
            arq1.write_text(json.dumps({
                "nome_completo": "Lead Com Checkout 1",
                "checkout": True,
                "etapa_max": 10,
                "nascimento": {"dia": 1, "mes": 1, "ano": 1990},
            }), encoding="utf-8")

            # Lead 2: foi ao checkout
            arq2 = dir_leituras / "20260907-100100-22222222.json"
            arq2.write_text(json.dumps({
                "nome_completo": "Lead Com Checkout 2",
                "checkout": True,
                "etapa_max": 10,
                "nascimento": {"dia": 2, "mes": 2, "ano": 1991},
            }), encoding="utf-8")

            # Lead 3: parou na tela 7, NÃO foi ao checkout
            arq3 = dir_leituras / "20260907-100200-33333333.json"
            arq3.write_text(json.dumps({
                "nome_completo": "Lead Sem Checkout",
                "checkout": False,
                "etapa_max": 7,
                "nascimento": {"dia": 3, "mes": 3, "ano": 1992},
            }), encoding="utf-8")

            with mock.patch.object(config, "DIR_LEITURAS", dir_leituras):
                # 1. Sem filtro: traz os 3
                corpo_all, tot_all, pags_all, unicos_all, chk_all, geral_all = _tabela_leituras(pagina=0, so_checkout=False)
                self.assertEqual(tot_all, 3)
                self.assertEqual(chk_all, 2)
                self.assertEqual(geral_all, 3)
                self.assertIn("Lead Com Checkout 1", corpo_all)
                self.assertIn("Lead Com Checkout 2", corpo_all)
                self.assertIn("Lead Sem Checkout", corpo_all)

                # 2. Com filtro so_checkout=True: traz somente os 2 de checkout
                corpo_chk, tot_chk, pags_chk, unicos_chk, chk_chk, geral_chk = _tabela_leituras(pagina=0, so_checkout=True)
                self.assertEqual(tot_chk, 2)
                self.assertEqual(chk_chk, 2)
                self.assertEqual(geral_chk, 3)
                self.assertIn("Lead Com Checkout 1", corpo_chk)
                self.assertIn("Lead Com Checkout 2", corpo_chk)
                self.assertNotIn("Lead Sem Checkout", corpo_chk)

                # 3. Testa resposta HTML de /painel com so_checkout=1
                req = Request({"type": "http", "method": "GET", "path": "/painel", "headers": []})
                resp = painel(req, _="crassus", so_checkout=1)
                html_resp = resp.body.decode("utf-8")
                self.assertIn("✦ Só quem foi pro checkout", html_resp)
                self.assertIn("Todas as leituras", html_resp)
                self.assertIn("btn-filtro-leituras chk on", html_resp)
                self.assertIn("Lead Com Checkout 1", html_resp)
                self.assertNotIn("Lead Sem Checkout", html_resp)

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

        # Testa renderização no HTML do painel
        from api.painel import painel
        from starlette.requests import Request
        with mock.patch("servicos.eventos.ler_dias", return_value=d):
            req = Request({"type": "http", "method": "GET", "path": "/painel", "headers": []})
            resp = painel(req, _="crassus")
            html = resp.body.decode("utf-8")
            self.assertIn("pessoas únicas", html)
            self.assertIn("sessões", html)
            self.assertIn("Funil por tela", html)

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
                self.assertIn("🗑️ Excluir Leitura", html_resp)
                self.assertIn("modal-excluir-backdrop", html_resp)

    def test_deletar_leitura_sucesso_e_casos_de_erro(self):
        """Verifica a exclusão física da leitura, erros 404, formato inválido e 401 sem autenticação."""
        from main import app
        client = TestClient(app)

        with TemporaryDirectory() as tmpdir:
            dir_leituras = Path(tmpdir)
            lid = "20260907-150000-aaaaaaaa"
            arq = dir_leituras / f"{lid}.json"
            arq.write_text(json.dumps({"nome_completo": "Visitante Deletável"}), encoding="utf-8")
            self.assertTrue(arq.exists())

            with mock.patch.object(config, "DIR_LEITURAS", dir_leituras):
                # 1. Sem autenticação -> 401
                r_sem_auth = client.post(f"/painel/leitura/{lid}/deletar")
                self.assertEqual(r_sem_auth.status_code, 401)
                self.assertTrue(arq.exists())  # arquivo preservado

                # 2. ID com formato inválido -> 400 ou 404
                r_invalido = client.post(
                    "/painel/leitura/id-invalido-123/deletar",
                    auth=(config.PAINEL_USUARIO, config.PAINEL_SENHA)
                )
                self.assertIn(r_invalido.status_code, (400, 404))

                # 3. ID inexistente com formato válido -> 404
                r_404 = client.post(
                    "/painel/leitura/20260907-150000-99999999/deletar",
                    auth=(config.PAINEL_USUARIO, config.PAINEL_SENHA)
                )
                self.assertEqual(r_404.status_code, 404)

                # 4. Exclusão com sucesso -> 200 e arquivo removido do disco
                r_ok = client.post(
                    f"/painel/leitura/{lid}/deletar",
                    auth=(config.PAINEL_USUARIO, config.PAINEL_SENHA)
                )
                self.assertEqual(r_ok.status_code, 200)
                dados_resp = r_ok.json()
                self.assertTrue(dados_resp.get("ok"))
                self.assertEqual(dados_resp.get("leitura_id"), lid)
                self.assertFalse(arq.exists())  # arquivo foi excluído permanentemente

    def test_tabela_e_painel_renderizam_botao_e_modal_excluir(self):
        """Verifica se a tabela de leituras e o painel contêm o botão de deletar e o popup modal centralizado com opções."""
        from api.painel import _tabela_leituras, painel
        from starlette.requests import Request

        with TemporaryDirectory() as tmpdir:
            dir_leituras = Path(tmpdir)
            lid = "20260907-160000-bbbbbbbb"
            arq = dir_leituras / f"{lid}.json"
            arq.write_text(json.dumps({
                "nome_completo": "Marcos Silva",
                "nascimento": {"dia": 1, "mes": 1, "ano": 1990},
                "etapa_max": 7,
            }), encoding="utf-8")

            with mock.patch.object(config, "DIR_LEITURAS", dir_leituras):
                corpo, _, _, _, _, _ = _tabela_leituras(pagina=0)
                # Verifica a coluna 'ações' no cabeçalho
                self.assertIn("ações", corpo)
                # Verifica o ID da linha da pessoa para remoção dinâmica no DOM
                self.assertIn(f'id="row-pessoa-{lid}"', corpo)
                # Verifica o botão de exclusão
                self.assertIn('class="btn-del"', corpo)
                self.assertIn("🗑️ Excluir", corpo)
                self.assertIn(f"abrirModalExcluir('{lid}', 'Marcos Silva'", corpo)

                # Verifica o HTML completo do painel
                req = Request({"type": "http", "method": "GET", "path": "/painel", "headers": []})
                resp = painel(req, _="crassus")
                html_resp = resp.body.decode("utf-8")

                # Verifica se o popup modal centralizado está presente no HTML
                self.assertIn('id="modal-excluir-backdrop"', html_resp)
                # Garante que o backdrop não fecha o popup ao clicar fora (sem onclick no backdrop)
                self.assertIn('<div id="modal-excluir-backdrop" class="modal-backdrop">', html_resp)
                self.assertNotIn('onclick="if(event.target===this) fecharModalExcluir();"', html_resp)
                self.assertIn("Confirmar Exclusão", html_resp)
                self.assertIn("btn-modal-cancelar", html_resp)
                self.assertIn("btn-modal-confirmar", html_resp)
                self.assertIn("fecharModalExcluir()", html_resp)
                self.assertIn("executarExclusao()", html_resp)
                self.assertIn('id="modal-del-opcoes"', html_resp)
                self.assertIn('name="modo_exclusao"', html_resp)

    def test_agrupamento_acordeao_consolidacao_checkout(self):
        """Verifica se uma pessoa com múltiplos envios consolida o status de checkout na linha principal."""
        from api.painel import _tabela_leituras
        with TemporaryDirectory() as tmpdir:
            dir_leituras = Path(tmpdir)
            # Tentativa 1 (mais antiga): chegou ao checkout
            arq1 = dir_leituras / "20260907-100000-aaaa0001.json"
            arq1.write_text(json.dumps({
                "nome_completo": "Juliana Santos",
                "whatsapp": "11988887777",
                "checkout": True,
                "etapa_max": 10,
                "nascimento": {"dia": 5, "mes": 5, "ano": 1992},
            }), encoding="utf-8")

            # Tentativa 2 (mais recente): desistiu na tela 7, sem checkout
            arq2 = dir_leituras / "20260907-110000-aaaa0002.json"
            arq2.write_text(json.dumps({
                "nome_completo": "Juliana Santos",
                "whatsapp": "11988887777",
                "checkout": False,
                "etapa_max": 7,
                "nascimento": {"dia": 5, "mes": 5, "ano": 1992},
            }), encoding="utf-8")

            with mock.patch.object(config, "DIR_LEITURAS", dir_leituras):
                corpo, total, pags, unicos, chk, geral = _tabela_leituras(pagina=0)
                # Consolidação: teve_checkout é True porque a tentativa anterior foi ao checkout
                self.assertEqual(unicos, 1)
                self.assertEqual(chk, 1)
                self.assertEqual(total, 2)
                # Linha principal deve ter data-checkout="1" e tag-checkout sim
                self.assertIn('id="row-pessoa-20260907-110000-aaaa0002" class="tr-pessoa" data-checkout="1"', corpo)
                self.assertIn("✦ SIM", corpo)
                # Sub-linha da tentativa anterior deve existir
                self.assertIn('id="row-leitura-20260907-100000-aaaa0001"', corpo)

    def test_deletar_leitura_modo_todos(self):
        """Verifica a exclusão em lote de todos os envios de uma mesma pessoa com modo=todos."""
        from starlette.testclient import TestClient
        from main import app
        client = TestClient(app)

        with TemporaryDirectory() as tmpdir:
            dir_leituras = Path(tmpdir)
            # 2 envios da mesma pessoa (mesmo whatsapp)
            lid1 = "20260907-140000-11111111"
            lid2 = "20260907-140500-22222222"
            arq1 = dir_leituras / f"{lid1}.json"
            arq2 = dir_leituras / f"{lid2}.json"
            arq1.write_text(json.dumps({"nome_completo": "Ana Paula", "whatsapp": "11999990000"}), encoding="utf-8")
            arq2.write_text(json.dumps({"nome_completo": "Ana Paula", "whatsapp": "11999990000"}), encoding="utf-8")

            # 1 envio de outra pessoa
            lid3 = "20260907-150000-33333333"
            arq3 = dir_leituras / f"{lid3}.json"
            arq3.write_text(json.dumps({"nome_completo": "Outro Visitante", "whatsapp": "21988881111"}), encoding="utf-8")

            with mock.patch.object(config, "DIR_LEITURAS", dir_leituras):
                # Executa exclusão com modo=todos usando o id do envio 2
                res = client.post(
                    f"/painel/leitura/{lid2}/deletar?modo=todos",
                    auth=(config.PAINEL_USUARIO, config.PAINEL_SENHA)
                )
                self.assertEqual(res.status_code, 200)
                dados = res.json()
                self.assertTrue(dados.get("ok"))
                self.assertEqual(dados.get("modo"), "todos")
                self.assertIn(lid1, dados.get("removidos", []))
                self.assertIn(lid2, dados.get("removidos", []))

                # Verifica se ambos os arquivos de Ana Paula foram removidos
                self.assertFalse(arq1.exists())
                self.assertFalse(arq2.exists())
                # E o outro visitante continua intacto
                self.assertTrue(arq3.exists())

    def test_arrasto_scroll_horizontal_tabela(self):
        """Verifica se os estilos e scripts de arrasto horizontal (drag-to-scroll) com botão esquerdo estão presentes e restritos à aba Leituras."""
        from api.painel import ESTILO, JS_PAINEL, painel, lista, _tabela
        from starlette.requests import Request

        # 1. Verifica que tabelas gerais não têm mãozinha e apenas a tabela de Leituras tem cursor:grab
        self.assertIn(".tbl-wrap{width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch;margin-bottom:12px;cursor:default}", ESTILO)
        self.assertIn("#aba-leituras .tbl-wrap, .tbl-wrap-leituras{cursor:grab}", ESTILO)
        self.assertIn(".tbl-wrap-leituras.arrastando{cursor:grabbing !important;user-select:none !important", ESTILO)
        self.assertIn(".tbl-wrap-leituras.arrastando *{cursor:grabbing !important", ESTILO)

        # 2. Verifica funções e listeners no JS_PAINEL
        self.assertIn("window.abrirAba", JS_PAINEL)
        self.assertIn("vincularAbas", JS_PAINEL)
        self.assertIn("iniciarArrastoScroll", JS_PAINEL)
        self.assertIn("_activeWrap", JS_PAINEL)
        self.assertIn("wrap.classList.add(\"arrastando\")", JS_PAINEL)
        self.assertIn("wrap.scrollLeft", JS_PAINEL)
        self.assertIn("window.addEventListener(\"mousemove\"", JS_PAINEL)
        self.assertIn("window.addEventListener(\"mouseup\"", JS_PAINEL)

        # 3. Verifica se a função _tabela gera container com classe .tbl-wrap e suporta wrap_class
        html_tbl = _tabela(["id", "nome"], [["1", "Teste"]])
        self.assertIn('<div class="tbl-wrap">', html_tbl)
        html_tbl_leituras = _tabela(["id", "nome"], [["1", "Teste"]], wrap_class="tbl-wrap tbl-wrap-leituras")
        self.assertIn('<div class="tbl-wrap tbl-wrap-leituras">', html_tbl_leituras)

        # 4. Verifica se /painel e /painel/leituras incluem o script de arrasto e controle de abas
        req = Request({"type": "http", "method": "GET", "path": "/painel", "headers": []})
        resp_painel = painel(req, _="crassus")
        html_p = resp_painel.body.decode("utf-8")
        self.assertIn("iniciarArrastoScroll", html_p)
        self.assertIn("window.abrirAba", html_p)
        self.assertIn("vincularAbas", html_p)

        resp_lista = lista(_="crassus")
        self.assertIn("iniciarArrastoScroll", resp_lista.body.decode("utf-8"))

    def test_filtro_ao_vivo_e_tempo_real(self):
        """Verifica o filtro de contatos ao vivo agora e elementos WebSocket no painel."""
        from api.painel import _tabela_leituras, painel, lista
        from servicos.tempo_real import rastreador_presenca
        from starlette.requests import Request

        with TemporaryDirectory() as tmpdir:
            dir_leituras = Path(tmpdir)
            lid1 = "20260907-160000-aaaa0001"
            lid2 = "20260907-160500-bbbb0002"

            (dir_leituras / f"{lid1}.json").write_text(json.dumps({
                "nome_completo": "Contato Ao Vivo",
                "whatsapp": "11988880001",
                "cliente_id": "sid-ao-vivo-1",
            }), encoding="utf-8")

            (dir_leituras / f"{lid2}.json").write_text(json.dumps({
                "nome_completo": "Contato Offline",
                "whatsapp": "11988880002",
                "cliente_id": "sid-offline-2",
            }), encoding="utf-8")

            # Simula que o visitante 1 está ativo agora vendo a tela 8
            rastreador_presenca.registrar_atividade(sid="sid-ao-vivo-1", leitura_id=lid1, tela=8)

            with mock.patch.object(config, "DIR_LEITURAS", dir_leituras):
                # 1. Tabela com so_ao_vivo=False deve trazer ambos
                res_all = _tabela_leituras(pagina=0, so_ao_vivo=False)
                corpo_all, tot_all, pags_all, unicos_all, chk_all, geral_all = res_all
                self.assertEqual(unicos_all, 2)
                self.assertEqual(res_all.total_ao_vivo, 1)

                # Verifica que a tag ao vivo aparece para o contato 1
                self.assertIn(f'id="live-tag-{lid1}">🟢 Ao vivo</span>', corpo_all)

                # 2. Tabela com so_ao_vivo=True deve trazer apenas o contato ao vivo
                res_vivo = _tabela_leituras(pagina=0, so_ao_vivo=True)
                corpo_vivo, tot_v, pags_v, unicos_v, chk_v, geral_v = res_vivo
                self.assertEqual(unicos_v, 1)
                self.assertIn(lid1[:15], corpo_vivo)
                self.assertNotIn(lid2[:15], corpo_vivo)

                # 3. Verifica se /painel renderiza o filtro "Ao vivo agora", ws-status e window._wsToken
                req = Request({"type": "http", "method": "GET", "path": "/painel", "headers": []})
                resp_painel = painel(req, _="crassus")
                html_p = resp_painel.body.decode("utf-8")
                self.assertIn("🟢 Ao vivo agora", html_p)
                self.assertIn('id="badge-count-vivo"', html_p)
                self.assertIn('id="ws-status"', html_p)
                self.assertIn("window._wsToken =", html_p)

                # 4. Verifica se /painel/leituras também renderiza o filtro e token
                resp_l = lista(_="crassus", so_ao_vivo=1)
                html_l = resp_l.body.decode("utf-8")
                self.assertIn("🟢 Ao vivo agora", html_l)
                self.assertIn('id="badge-count-vivo"', html_l)
                self.assertIn('id="ws-status"', html_l)
                self.assertIn("window._wsToken =", html_l)

    def test_status_compra_e_filtro(self):
        """Verifica marcação de compra, persistência, websocket, filtro no painel e endpoint."""
        from api.painel import _tabela_leituras, painel, lista, detalhe, router
        from servicos import registro
        from starlette.requests import Request
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        import base64

        with TemporaryDirectory() as tmpdir:
            dir_leituras = Path(tmpdir)
            lid1 = "20260907-170000-aaaa0001"
            lid2 = "20260907-170500-bbbb0002"

            (dir_leituras / f"{lid1}.json").write_text(json.dumps({
                "nome_completo": "Cliente Comprador",
                "whatsapp": "11999990001",
                "comprou": False,
            }), encoding="utf-8")

            (dir_leituras / f"{lid2}.json").write_text(json.dumps({
                "nome_completo": "Visitante Sem Compra",
                "whatsapp": "11999990002",
                "comprou": False,
            }), encoding="utf-8")

            with mock.patch.object(config, "DIR_LEITURAS", dir_leituras):
                # 1. Testar serviço registro.atualizar_status_compra
                ok = registro.atualizar_status_compra(lid1, True)
                self.assertTrue(ok)
                dados1 = json.loads((dir_leituras / f"{lid1}.json").read_text(encoding="utf-8"))
                self.assertTrue(dados1.get("comprou"))
                self.assertTrue("comprado_em" in dados1)

                # 2. Testar _tabela_leituras sem filtro de compra
                res_todas = _tabela_leituras(pagina=0, so_comprou=False)
                corpo_todas, tot_t, pags_t, unicos_t, chk_t, geral_t = res_todas
                self.assertEqual(unicos_t, 2)
                self.assertEqual(res_todas.total_comprou, 1)
                # Verifica se o cliente 1 tem tag-comprou e data-comprou="1"
                self.assertIn(f'id="tag-comprou-{lid1}">✅ Comprou</span>', corpo_todas)
                self.assertIn(f'id="btn-compra-{lid1}" class="btn-compra comprou"', corpo_todas)
                self.assertIn('data-comprou="1"', corpo_todas)

                # 3. Testar _tabela_leituras com so_comprou=True
                res_compra = _tabela_leituras(pagina=0, so_comprou=True)
                corpo_compra, tot_c, pags_c, unicos_c, chk_c, geral_c = res_compra
                self.assertEqual(unicos_c, 1)
                self.assertIn(lid1[:15], corpo_compra)
                self.assertNotIn(lid2[:15], corpo_compra)

                # 4. Testar renderização de /painel com filtro comprou
                req = Request({"type": "http", "method": "GET", "path": "/painel", "headers": []})
                resp_painel = painel(req, _="crassus")
                html_p = resp_painel.body.decode("utf-8")
                self.assertIn("💰 Só quem comprou", html_p)
                self.assertIn('id="badge-count-comprou"', html_p)
                self.assertIn("alternarCompra", html_p)
                self.assertIn("aplicarStatusCompraNoDOM", html_p)

                # 5. Testar renderização de /painel/leituras com filtro comprou
                resp_l = lista(_="crassus", so_comprou=1)
                html_l = resp_l.body.decode("utf-8")
                self.assertIn("💰 Só quem comprou", html_l)
                self.assertIn('id="badge-count-comprou"', html_l)

                # 6. Testar renderização do botão no detalhe
                resp_det = detalhe(lid1, _="crassus")
                html_det = resp_det.body.decode("utf-8")
                self.assertIn(f'id="btn-compra-{lid1}"', html_det)
                self.assertIn("✅ Comprou", html_det)

                # 7. Testar endpoint HTTP POST /painel/leitura/{id}/status-compra
                app = FastAPI()
                app.include_router(router)
                client = TestClient(app)

                # Desmarcar compra
                resp_post = client.post(
                    f"/painel/leitura/{lid1}/status-compra?comprou=false",
                    auth=(config.PAINEL_USUARIO, config.PAINEL_SENHA)
                )
                self.assertEqual(resp_post.status_code, 200)
                data = resp_post.json()
                self.assertTrue(data["ok"])
                self.assertFalse(data["comprou"])
                self.assertEqual(data["total_comprou"], 0)

                # Verificar arquivo persistido
                dados1_after = json.loads((dir_leituras / f"{lid1}.json").read_text(encoding="utf-8"))
                self.assertFalse(dados1_after.get("comprou"))

                # Marcar novamente como comprou
                resp_post2 = client.post(
                    f"/painel/leitura/{lid1}/status-compra?comprou=true",
                    auth=(config.PAINEL_USUARIO, config.PAINEL_SENHA)
                )
                self.assertEqual(resp_post2.status_code, 200)
                data2 = resp_post2.json()
                self.assertTrue(data2["ok"])
                self.assertTrue(data2["comprou"])
                self.assertEqual(data2["total_comprou"], 1)

    def test_modal_confirmacao_compra(self):
        """Verifica se o popup modal de confirmação de compra está presente no HTML, CSS e JS do painel."""
        from api.painel import ESTILO, JS_PAINEL, _modal_confirmar_compra, painel, lista, detalhe
        from starlette.requests import Request

        # 1. Estrutura do modal
        modal_html = _modal_confirmar_compra()
        self.assertIn('id="modal-compra-backdrop"', modal_html)
        self.assertIn('id="modal-compra-card"', modal_html)
        self.assertIn('id="modal-compra-icone"', modal_html)
        self.assertIn('id="modal-compra-titulo"', modal_html)
        self.assertIn('id="modal-compra-nome"', modal_html)
        self.assertIn('id="modal-compra-id"', modal_html)
        self.assertIn('id="modal-compra-desc"', modal_html)
        self.assertIn('id="modal-compra-erro"', modal_html)
        self.assertIn('id="btn-modal-confirmar-compra"', modal_html)
        self.assertIn('onclick="fecharModalCompra()"', modal_html)
        self.assertIn('onclick="executarConfirmacaoCompra()"', modal_html)
        self.assertIn('class="modal-fechar-btn"', modal_html)

        # 2. Estilos CSS
        self.assertIn(".modal-card-compra", ESTILO)
        self.assertIn(".modal-card-compra.desmarcar", ESTILO)
        self.assertIn(".modal-icone-wrap", ESTILO)
        self.assertIn(".modal-info-box", ESTILO)
        self.assertIn(".btn-modal-confirmar-compra", ESTILO)
        self.assertIn(".btn-modal-confirmar-compra.desmarcar", ESTILO)

        # 3. Funções JavaScript
        self.assertIn("function abrirModalCompra(", JS_PAINEL)
        self.assertIn("function fecharModalCompra(", JS_PAINEL)
        self.assertIn("function executarConfirmacaoCompra(", JS_PAINEL)
        self.assertIn("fecharModalCompra()", JS_PAINEL)

        # 4. Presença do modal nas páginas do painel
        req = Request({"type": "http", "method": "GET", "path": "/painel", "headers": []})
        resp_p = painel(req, _="crassus")
        html_p = resp_p.body.decode("utf-8")
        self.assertIn('id="modal-compra-backdrop"', html_p)
        self.assertIn('abrirModalCompra', html_p)

        resp_l = lista(_="crassus")
        html_l = resp_l.body.decode("utf-8")
        self.assertIn('id="modal-compra-backdrop"', html_l)
        self.assertIn('abrirModalCompra', html_l)

    def test_filtro_periodo_na_tabela_leituras(self):
        """Verifica se o filtro de data (ex: hoje vs 7 dias) restringe as leituras exibidas."""
        from api.painel import _tabela_leituras, painel
        from starlette.requests import Request

        with TemporaryDirectory() as tmpdir:
            dir_leituras = Path(tmpdir)
            stem_hoje = f"{HOJE:%Y%m%d}-100000-11111111"
            stem_antigo = f"{(HOJE - timedelta(days=3)):%Y%m%d}-100000-22222222"

            (dir_leituras / f"{stem_hoje}.json").write_text(json.dumps({
                "nome_completo": "Lead Chegou Hoje",
                "chegou_em_bsb": f"{HOJE:%d/%m/%Y} 10:00:00",
                "gravado_em_bsb": f"{HOJE:%d/%m/%Y} 10:05:00",
                "etapa_max": 7,
                "nascimento": {"dia": 1, "mes": 1, "ano": 1990},
            }), encoding="utf-8")

            (dir_leituras / f"{stem_antigo}.json").write_text(json.dumps({
                "nome_completo": "Lead Chegou Dias Atras",
                "chegou_em_bsb": f"{(HOJE - timedelta(days=3)):%d/%m/%Y} 10:00:00",
                "gravado_em_bsb": f"{(HOJE - timedelta(days=3)):%d/%m/%Y} 10:05:00",
                "etapa_max": 7,
                "nascimento": {"dia": 2, "mes": 2, "ano": 1991},
            }), encoding="utf-8")

            with mock.patch.object(config, "DIR_LEITURAS", dir_leituras):
                # 1. Filtro "hoje" (de=HOJE, ate=HOJE)
                corpo_hoje, tot_hoje, _, _, _, _ = _tabela_leituras(pagina=0, de=HOJE, ate=HOJE)
                self.assertEqual(tot_hoje, 1)
                self.assertIn("Lead Chegou Hoje", corpo_hoje)
                self.assertNotIn("Lead Chegou Dias Atras", corpo_hoje)

                # 2. Filtro 7 dias (de=HOJE-7d, ate=HOJE)
                corpo_7d, tot_7d, _, _, _, _ = _tabela_leituras(pagina=0, de=HOJE - timedelta(days=7), ate=HOJE)
                self.assertEqual(tot_7d, 2)
                self.assertIn("Lead Chegou Hoje", corpo_7d)
                self.assertIn("Lead Chegou Dias Atras", corpo_7d)

                # 3. GET /painel?dias=1 (Hoje)
                req_hoje = Request({"type": "http", "method": "GET", "path": "/painel", "headers": []})
                resp_hoje = painel(req_hoje, _="crassus", dias=1)
                html_hoje = resp_hoje.body.decode("utf-8")
                self.assertIn("Lead Chegou Hoje", html_hoje)
                self.assertNotIn("Lead Chegou Dias Atras", html_hoje)

                # 4. GET /painel?dias=7 (7 dias)
                req_7d = Request({"type": "http", "method": "GET", "path": "/painel", "headers": []})
                resp_7d = painel(req_7d, _="crassus", dias=7)
                html_7d = resp_7d.body.decode("utf-8")
                self.assertIn("Lead Chegou Hoje", html_7d)
                self.assertIn("Lead Chegou Dias Atras", html_7d)

    def test_filtro_whatsapp_na_tabela_leituras(self):
        """Verifica o filtro 'Só com WhatsApp' no backend e no HTML do painel."""
        from api.painel import _tabela_leituras, painel, lista
        from starlette.requests import Request

        with TemporaryDirectory() as tmpdir:
            dir_leituras = Path(tmpdir)
            stem_wa = f"{HOJE:%Y%m%d}-110000-aaaaaaaa"
            stem_sem_wa = f"{HOJE:%Y%m%d}-120000-bbbbbbbb"

            (dir_leituras / f"{stem_wa}.json").write_text(json.dumps({
                "nome_completo": "Lead Tem WhatsApp",
                "whatsapp": "+55 (85) 98888-7777",
                "nascimento": {"dia": 1, "mes": 1, "ano": 1995},
            }), encoding="utf-8")

            (dir_leituras / f"{stem_sem_wa}.json").write_text(json.dumps({
                "nome_completo": "Lead Sem WhatsApp",
                "whatsapp": "—",
                "nascimento": {"dia": 2, "mes": 2, "ano": 1996},
            }), encoding="utf-8")

            with mock.patch.object(config, "DIR_LEITURAS", dir_leituras):
                # 1. Sem filtro traz ambos
                res_todos = _tabela_leituras(pagina=0, so_whatsapp=False)
                self.assertEqual(res_todos[1], 2)
                self.assertEqual(res_todos.total_whatsapp, 1)
                self.assertIn("Lead Tem WhatsApp", res_todos[0])
                self.assertIn("Lead Sem WhatsApp", res_todos[0])

                # 2. Com so_whatsapp=True traz apenas quem tem WhatsApp
                res_wa = _tabela_leituras(pagina=0, so_whatsapp=True)
                self.assertEqual(res_wa[1], 1)
                self.assertEqual(res_wa.total_whatsapp, 1)
                self.assertIn("Lead Tem WhatsApp", res_wa[0])
                self.assertNotIn("Lead Sem WhatsApp", res_wa[0])

                # 3. HTML em /painel?so_whatsapp=1
                req = Request({"type": "http", "method": "GET", "path": "/painel", "headers": []})
                resp = painel(req, _="crassus", so_whatsapp=1)
                html = resp.body.decode("utf-8")
                self.assertIn("btn-filtro-leituras wa on", html)
                self.assertIn("📱 Só com WhatsApp", html)
                self.assertIn("Lead Tem WhatsApp", html)
                self.assertNotIn("Lead Sem WhatsApp", html)

                # 4. HTML em /painel/leituras?so_whatsapp=1
                resp_l = lista(_="crassus", so_whatsapp=1)
                html_l = resp_l.body.decode("utf-8")
                self.assertIn("Lead Tem WhatsApp", html_l)
                self.assertNotIn("Lead Sem WhatsApp", html_l)

    def test_selecao_e_exportacao_csv(self):
        """Verifica checkboxes de seleção no HTML e geração da planilha CSV pelo endpoint."""
        from main import app
        client = TestClient(app)

        with TemporaryDirectory() as tmpdir:
            dir_leituras = Path(tmpdir)
            stem1 = f"{HOJE:%Y%m%d}-130000-cccccccc"
            stem2 = f"{HOJE:%Y%m%d}-140000-dddddddd"

            (dir_leituras / f"{stem1}.json").write_text(json.dumps({
                "nome_completo": "Carlos Teste CSV",
                "whatsapp": "+55 (11) 97777-6666",
                "nascimento": {"dia": 15, "mes": 8, "ano": 1985, "hora": 10, "minuto": 30},
                "cidade": {"nome": "São Paulo", "uf": "SP", "pais": "Brasil"},
                "quiz": {"area": "caminhos"},
                "veredito": {"tipo": "CAUSA_OCULTA", "casa_eleita_real": True, "casa_aberta": 9},
                "tempo_quiz_ms": 120000,
                "checkout": True,
                "comprou": True,
            }), encoding="utf-8")

            (dir_leituras / f"{stem2}.json").write_text(json.dumps({
                "nome_completo": "Fernanda Teste CSV",
                "whatsapp": "—",
                "nascimento": {"dia": 20, "mes": 4, "ano": 1993},
                "cidade": {"nome": "Curitiba", "uf": "PR", "pais": "Brasil"},
                "quiz": {"area": "amor"},
                "veredito": {"tipo": "DESLOCAMENTO", "casa_eleita_real": False},
                "tempo_quiz_ms": 90000,
                "checkout": False,
                "comprou": False,
            }), encoding="utf-8")

            with mock.patch.object(config, "DIR_LEITURAS", dir_leituras):
                # 1. Sem autenticação -> 401
                r_sem_auth = client.get("/painel/exportar-csv")
                self.assertEqual(r_sem_auth.status_code, 401)

                # 2. Com autenticação -> 200 e arquivo CSV formatado
                r = client.get(
                    "/painel/exportar-csv",
                    auth=(config.PAINEL_USUARIO, config.PAINEL_SENHA)
                )
                self.assertEqual(r.status_code, 200)
                self.assertIn("text/csv", r.headers.get("content-type", ""))
                self.assertIn("attachment; filename=", r.headers.get("content-disposition", ""))

                csv_text = r.content.decode("utf-8-sig")
                # Verifica cabeçalhos esperados
                self.assertIn("ID da Leitura", csv_text)
                self.assertIn("Nome Completo", csv_text)
                self.assertIn("WhatsApp", csv_text)
                self.assertIn("Etapa Alcançada", csv_text)
                self.assertIn("Fez Checkout", csv_text)
                self.assertIn("Comprou", csv_text)
                self.assertIn("Área do Quiz", csv_text)
                self.assertIn("Cenário Astrológico", csv_text)

                # Verifica dados dos 2 contatos
                self.assertIn("Carlos Teste CSV", csv_text)
                self.assertIn("+55 (11) 97777-6666", csv_text)
                self.assertIn("Fernanda Teste CSV", csv_text)

                # 3. Exportação filtrando por IDs específicos
                r_ids = client.get(
                    f"/painel/exportar-csv?ids={stem1}",
                    auth=(config.PAINEL_USUARIO, config.PAINEL_SENHA)
                )
                self.assertEqual(r_ids.status_code, 200)
                csv_ids = r_ids.content.decode("utf-8-sig")
                self.assertIn("Carlos Teste CSV", csv_ids)
                self.assertNotIn("Fernanda Teste CSV", csv_ids)

                # 4. Exportação filtrando por so_whatsapp=1
                r_wa = client.get(
                    "/painel/exportar-csv?so_whatsapp=1",
                    auth=(config.PAINEL_USUARIO, config.PAINEL_SENHA)
                )
                self.assertEqual(r_wa.status_code, 200)
                csv_wa = r_wa.content.decode("utf-8-sig")
                self.assertIn("Carlos Teste CSV", csv_wa)
                self.assertNotIn("Fernanda Teste CSV", csv_wa)

                # 5. Validação dos elementos HTML e JS no painel
                from api.painel import painel, ESTILO, JS_PAINEL
                from starlette.requests import Request
                req = Request({"type": "http", "method": "GET", "path": "/painel", "headers": []})
                resp = painel(req, _="crassus")
                html = resp.body.decode("utf-8")

                self.assertIn('id="chk-selecionar-todos-topo"', html)
                self.assertIn('id="chk-selecionar-todos-barra"', html)
                self.assertIn('class="chk-selecao chk-contato"', html)
                self.assertIn('id="btn-exportar-csv"', html)
                self.assertIn('exportarContatosCSV()', html)
                self.assertIn('toggleSelecionarTodos(this)', html)
                self.assertIn('window._contatosExportacao', html)

                self.assertIn("function toggleSelecionarTodos(", JS_PAINEL)
                self.assertIn("function atualizarContadorSelecao(", JS_PAINEL)
                self.assertIn("function exportarContatosCSV(", JS_PAINEL)
                self.assertIn(".barra-acoes-leituras", ESTILO)
                self.assertIn(".btn-exportar-csv", ESTILO)
                self.assertIn(".btn-filtro-leituras.wa", ESTILO)

class TestFiltrosDataEFusoHorario(unittest.TestCase):
    """Valida o fuso horário de Brasília (UTC-3) e filtros por período (presets e De/Até)."""

    def setUp(self):
        self.tmp_dir = TemporaryDirectory()
        self.dir_leituras = Path(self.tmp_dir.name) / "leituras"
        self.dir_eventos = Path(self.tmp_dir.name) / "eventos"
        self.dir_leituras.mkdir(parents=True, exist_ok=True)
        self.dir_eventos.mkdir(parents=True, exist_ok=True)
        self.patch_leituras = mock.patch.object(config, "DIR_LEITURAS", self.dir_leituras)
        self.patch_eventos = mock.patch.object(config, "DIR_EVENTOS", self.dir_eventos)
        self.patch_leituras.start()
        self.patch_eventos.start()

    def tearDown(self):
        self.patch_eventos.stop()
        self.patch_leituras.stop()
        self.tmp_dir.cleanup()

    def test_fuso_horario_brasilia_nao_muda_as_21h(self):
        """Às 21:30 em Brasília (00:30 UTC do dia seguinte), ainda deve ser o dia de Brasília."""
        from api.painel import hoje_bsb, _periodo, FUSO_BSB
        from servicos.agregador import _ts, agregar

        # 00:30 UTC de 09/09/2026 equivale a 21:30 BSB de 08/09/2026
        dt_utc_21h_bsb = datetime(2026, 9, 9, 0, 30, tzinfo=timezone.utc)
        with mock.patch("api.painel.datetime") as mock_dt:
            mock_dt.now.side_effect = lambda tz=None: dt_utc_21h_bsb.astimezone(tz) if tz else dt_utc_21h_bsb
            mock_dt.fromisoformat = datetime.fromisoformat
            self.assertEqual(hoje_bsb(), date(2026, 9, 8))
            d1, d2 = _periodo(None, None, 1)
            self.assertEqual((d1, d2), (date(2026, 9, 8), date(2026, 9, 8)))

        # Verifica conversão em agregador._ts
        ev_utc = {"ts": "2026-09-09T00:30:00+00:00", "sid": "s-21h", "seq": 1, "evt": "tela", "props": {"para": 1}}
        t = _ts(ev_utc)
        self.assertIsNotNone(t)
        self.assertEqual(t.date(), date(2026, 9, 8))
        self.assertEqual(t.hour, 21)
        self.assertEqual(t.minute, 30)

        # Agregação para o dia de Brasília (08/09) inclui o evento de 21:30
        res = agregar([ev_utc], date(2026, 9, 8), date(2026, 9, 8))
        self.assertEqual(res["sessoes"], 1)

    def test_presets_data_semana_e_ontem(self):
        """Verifica a renderização dos presets 'esta semana', 'semana passada', 'hoje' e 'ontem'."""
        from api.painel import painel
        from starlette.requests import Request

        # Simula terça-feira 08/09/2026
        dt_simulada = datetime(2026, 9, 8, 14, 0, tzinfo=timezone(timedelta(hours=-3)))
        with mock.patch("api.painel.datetime") as mock_dt:
            mock_dt.now.side_effect = lambda tz=None: dt_simulada.astimezone(tz) if tz else dt_simulada
            mock_dt.fromisoformat = datetime.fromisoformat

            # 1. Página inicial sem parâmetros (padrão 7 dias)
            req = Request({"type": "http", "method": "GET", "path": "/painel", "headers": []})
            resp = painel(req, _="crassus")
            html = resp.body.decode("utf-8")

            self.assertIn("esta semana", html)
            self.assertIn("semana passada", html)
            self.assertIn("ontem", html)
            self.assertIn("hoje", html)
            self.assertIn("de=2026-09-07&ate=2026-09-08", html)  # Segunda até terça (esta semana)
            self.assertIn("de=2026-08-31&ate=2026-09-06", html)  # Segunda até domingo da semana anterior

            # 2. Requisição do preset 'esta semana'
            resp_semana = painel(req, _="crassus", de="2026-09-07", ate="2026-09-08")
            html_semana = resp_semana.body.decode("utf-8")
            self.assertIn("07/09/2026 a 08/09/2026", html_semana)
            self.assertIn('class="f on" href="/painel?de=2026-09-07&ate=2026-09-08">esta semana</a>', html_semana)

            # 3. Requisição do preset 'semana passada'
            resp_passada = painel(req, _="crassus", de="2026-08-31", ate="2026-09-06")
            html_passada = resp_passada.body.decode("utf-8")
            self.assertIn("31/08/2026 a 06/09/2026", html_passada)
            self.assertIn('class="f on" href="/painel?de=2026-08-31&ate=2026-09-06">semana passada</a>', html_passada)

    def test_filtro_personalizado_de_e_ate(self):
        """Verifica o formulário De/Até e a filtragem correspondente no painel, leituras e CSV."""
        from main import app
        from starlette.testclient import TestClient
        client = TestClient(app)

        # Cria leads em datas distintas
        # Lead 1: 03/09/2026
        # Lead 2: 07/09/2026
        stem1 = "20260903-150000-lead0001"
        stem2 = "20260907-160000-lead0002"

        (self.dir_leituras / f"{stem1}.json").write_text(json.dumps({
            "nome_completo": "Lead Inicio Mes",
            "whatsapp": "11988887777",
            "chegou_em_bsb": "03/09/2026 14:58",
            "gravado_em_bsb": "03/09/2026 15:00",
            "nascimento": {"dia": 10, "mes": 1, "ano": 1990},
            "cidade": {"nome": "Campinas", "uf": "SP"},
            "quiz": {"area": "dinheiro"},
            "veredito": {"tipo": "ORIGEM", "casa_eleita_real": True, "casa_aberta": 2},
            "tempo_quiz_ms": 120000,
        }), encoding="utf-8")

        (self.dir_leituras / f"{stem2}.json").write_text(json.dumps({
            "nome_completo": "Lead Fim Semana",
            "whatsapp": "11999998888",
            "chegou_em_bsb": "07/09/2026 15:58",
            "gravado_em_bsb": "07/09/2026 16:00",
            "nascimento": {"dia": 15, "mes": 5, "ano": 1992},
            "cidade": {"nome": "Santos", "uf": "SP"},
            "quiz": {"area": "amor"},
            "veredito": {"tipo": "RETORNO", "casa_eleita_real": True, "casa_aberta": 7},
            "tempo_quiz_ms": 110000,
        }), encoding="utf-8")

        # 1. Formulário customizado exibido no GET /painel?de=2026-09-01&ate=2026-09-04
        r = client.get(
            "/painel?de=2026-09-01&ate=2026-09-04",
            auth=(config.PAINEL_USUARIO, config.PAINEL_SENHA)
        )
        self.assertEqual(r.status_code, 200)
        html = r.text
        self.assertIn('class="form-filtro-datas"', html)
        self.assertIn('name="de" value="2026-09-01"', html)
        self.assertIn('name="ate" value="2026-09-04"', html)
        self.assertIn("Lead Inicio Mes", html)
        self.assertNotIn("Lead Fim Semana", html)

        # 2. Endpoint /painel/leituras respeita de e ate
        r_leit = client.get(
            "/painel/leituras?de=2026-09-05&ate=2026-09-08",
            auth=(config.PAINEL_USUARIO, config.PAINEL_SENHA)
        )
        self.assertEqual(r_leit.status_code, 200)
        html_leit = r_leit.text
        self.assertIn("Lead Fim Semana", html_leit)
        self.assertNotIn("Lead Inicio Mes", html_leit)

        # 3. Exportar CSV respeita de e ate
        r_csv = client.get(
            "/painel/exportar-csv?de=2026-09-01&ate=2026-09-04",
            auth=(config.PAINEL_USUARIO, config.PAINEL_SENHA)
        )
        self.assertEqual(r_csv.status_code, 200)
        csv_text = r_csv.content.decode("utf-8-sig")
        self.assertIn("Lead Inicio Mes", csv_text)
        self.assertNotIn("Lead Fim Semana", csv_text)


class TestImportarCSV(unittest.TestCase):
    """Testes unitários da funcionalidade de importação de contatos via CSV."""

    def setUp(self):
        self.tmp_dir = TemporaryDirectory()
        self.dir_leituras = Path(self.tmp_dir.name) / "leituras"
        self.dir_eventos = Path(self.tmp_dir.name) / "eventos"
        self.dir_leituras.mkdir(parents=True, exist_ok=True)
        self.dir_eventos.mkdir(parents=True, exist_ok=True)
        self.patch_leituras = mock.patch.object(config, "DIR_LEITURAS", self.dir_leituras)
        self.patch_eventos = mock.patch.object(config, "DIR_EVENTOS", self.dir_eventos)
        self.patch_leituras.start()
        self.patch_eventos.start()

    def tearDown(self):
        self.patch_eventos.stop()
        self.patch_leituras.stop()
        self.tmp_dir.cleanup()

    def test_importar_csv_sem_autenticacao(self):
        """Endpoint /painel/importar-csv exige credenciais HTTP Basic."""
        from main import app
        client = TestClient(app)
        csv_bytes = b"Nome;WhatsApp\nCarlos;11999998888"
        r = client.post(
            "/painel/importar-csv",
            files={"arquivo": ("contatos.csv", csv_bytes, "text/csv")},
            data={"atualizar": 1}
        )
        self.assertEqual(r.status_code, 401)

    def test_importar_csv_criacao_e_atualizacao(self):
        """Verifica importação com criação de novos leads e atualização de existentes."""
        from main import app
        client = TestClient(app)

        # 1. Cria lead pré-existente
        lid_existente = "20260908-120000-exist001"
        (self.dir_leituras / f"{lid_existente}.json").write_text(json.dumps({
            "leitura_id": lid_existente,
            "nome_completo": "Nome Antigo",
            "whatsapp": "11911112222",
            "comprou": False,
            "checkout": False,
            "cidade": {"nome": "Campinas", "uf": "SP", "pais": "Brasil"},
            "quiz": {"primeiro_nome": "Nome", "area": "amor"},
            "etapa_max": 7,
            "etapa_nome": "Tela 7 (Leitura)"
        }), encoding="utf-8")

        # 2. Monta planilha CSV compatível (delimitador ;)
        csv_conteudo = (
            "ID da Leitura;Nome Completo;WhatsApp;Data de Nascimento;Hora de Nascimento;Cidade;UF;País;Comprou;Fez Checkout;Área do Quiz;Cenário Astrológico;Casa Astrológica\n"
            f"{lid_existente};Nome Atualizado;11988887777;10/05/1988;14:20;São Paulo;SP;Brasil;SIM;SIM;dinheiro;ORIGEM;Casa 2\n"
            ";Novo Cliente Criado;21977776666;15/12/1995;18h30;Rio de Janeiro;RJ;Brasil;NÃO;SIM;trabalho;RETORNO;Casa 6\n"
        )
        csv_bytes = csv_conteudo.encode("utf-8-sig")

        r = client.post(
            "/painel/importar-csv",
            auth=(config.PAINEL_USUARIO, config.PAINEL_SENHA),
            files={"arquivo": ("planilha_teste.csv", csv_bytes, "text/csv")},
            data={"atualizar": 1}
        )
        self.assertEqual(r.status_code, 200)
        res = r.json()
        self.assertTrue(res["sucesso"])
        self.assertEqual(res["total"], 2)
        self.assertEqual(res["atualizados"], 1)
        self.assertEqual(res["criados"], 1)

        # 3. Valida contato atualizado
        d_atualizado = json.loads((self.dir_leituras / f"{lid_existente}.json").read_text(encoding="utf-8"))
        self.assertEqual(d_atualizado["nome_completo"], "Nome Atualizado")
        self.assertEqual(d_atualizado["whatsapp"], "11988887777")
        self.assertTrue(d_atualizado["comprou"])
        self.assertTrue(d_atualizado["checkout"])
        self.assertEqual(d_atualizado["cidade"]["nome"], "São Paulo")
        self.assertEqual(d_atualizado["quiz"]["area"], "dinheiro")
        self.assertEqual(d_atualizado["nascimento"], {"dia": 10, "mes": 5, "ano": 1988, "hora": 14, "minuto": 20})

        # 4. Valida contato criado
        arquivos = [f for f in self.dir_leituras.glob("*.json") if f.stem != lid_existente]
        self.assertEqual(len(arquivos), 1)
        d_novo = json.loads(arquivos[0].read_text(encoding="utf-8"))
        self.assertEqual(d_novo["nome_completo"], "Novo Cliente Criado")
        self.assertEqual(d_novo["whatsapp"], "21977776666")
        self.assertFalse(d_novo["comprou"])
        self.assertTrue(d_novo["checkout"])
        self.assertEqual(d_novo["cidade"]["nome"], "Rio de Janeiro")
        self.assertEqual(d_novo["cidade"]["uf"], "RJ")
        self.assertEqual(d_novo["nascimento"]["dia"], 15)
        self.assertEqual(d_novo["nascimento"]["mes"], 12)
        self.assertEqual(d_novo["nascimento"]["ano"], 1995)
        self.assertEqual(d_novo["nascimento"]["hora"], 18)
        self.assertEqual(d_novo["nascimento"]["minuto"], 30)

    def test_importar_csv_sem_atualizar_flag_zero(self):
        """Quando atualizar=0, contatos com ID já existente não sofrem alteração."""
        from main import app
        client = TestClient(app)

        lid_existente = "20260908-120000-exist002"
        (self.dir_leituras / f"{lid_existente}.json").write_text(json.dumps({
            "leitura_id": lid_existente,
            "nome_completo": "Nome Intocado",
            "whatsapp": "11900000000",
            "comprou": False,
        }), encoding="utf-8")

        csv_conteudo = f"ID da Leitura;Nome Completo;Comprou\n{lid_existente};Nome Modificado;SIM\n"
        r = client.post(
            "/painel/importar-csv",
            auth=(config.PAINEL_USUARIO, config.PAINEL_SENHA),
            files={"arquivo": ("leads.csv", csv_conteudo.encode("utf-8"), "text/csv")},
            data={"atualizar": 0}
        )
        self.assertEqual(r.status_code, 200)
        res = r.json()
        self.assertEqual(res["atualizados"], 0)

        d = json.loads((self.dir_leituras / f"{lid_existente}.json").read_text(encoding="utf-8"))
        self.assertEqual(d["nome_completo"], "Nome Intocado")
        self.assertFalse(d["comprou"])

    def test_importar_csv_delimitador_virgula_e_latin1(self):
        """Testa importação com delimitador vírgula e encoding Latin-1 (com acentos)."""
        from main import app
        client = TestClient(app)

        csv_conteudo = "Nome,Telefone,Cidade,Estado\nJoão da Conceição,19988776655,Ribeirão Preto,SP\n"
        csv_bytes = csv_conteudo.encode("latin-1")

        r = client.post(
            "/painel/importar-csv",
            auth=(config.PAINEL_USUARIO, config.PAINEL_SENHA),
            files={"arquivo": ("leads_latin1.csv", csv_bytes, "text/csv")},
            data={"atualizar": 1}
        )
        self.assertEqual(r.status_code, 200)
        res = r.json()
        self.assertTrue(res["sucesso"])
        self.assertEqual(res["criados"], 1)

        arquivos = list(self.dir_leituras.glob("*.json"))
        self.assertEqual(len(arquivos), 1)
        d = json.loads(arquivos[0].read_text(encoding="utf-8"))
        self.assertEqual(d["nome_completo"], "João da Conceição")
        self.assertEqual(d["cidade"]["nome"], "Ribeirão Preto")

    def test_importar_csv_validacoes_de_erro(self):
        """Valida erros quando arquivo não é .csv, está vazio ou sem cabeçalhos válidos."""
        from main import app
        client = TestClient(app)

        # 1. Arquivo não .csv
        r1 = client.post(
            "/painel/importar-csv",
            auth=(config.PAINEL_USUARIO, config.PAINEL_SENHA),
            files={"arquivo": ("dados.txt", b"Nome;Telefone\nFulano;123", "text/plain")}
        )
        self.assertEqual(r1.status_code, 400)
        self.assertIn(".csv", r1.json()["detail"])

        # 2. Arquivo vazio
        r2 = client.post(
            "/painel/importar-csv",
            auth=(config.PAINEL_USUARIO, config.PAINEL_SENHA),
            files={"arquivo": ("vazio.csv", b"   ", "text/csv")}
        )
        self.assertEqual(r2.status_code, 400)
        self.assertIn("vazio", r2.json()["detail"])

        # 3. CSV sem colunas mínimas
        r3 = client.post(
            "/painel/importar-csv",
            auth=(config.PAINEL_USUARIO, config.PAINEL_SENHA),
            files={"arquivo": ("invalido.csv", b"Cor;Fruta\nAzul;Banana", "text/csv")}
        )
        self.assertEqual(r3.status_code, 400)
        self.assertIn("colunas mínimas", r3.json()["detail"])

    def test_elementos_frontend_e_interface_importar_csv(self):
        """Verifica a presença dos elementos HTML, modais, classes CSS e funções JS de importação."""
        from main import app
        from api.painel import ESTILO, JS_PAINEL, _modal_importar_csv
        client = TestClient(app)

        # 1. Botão e modal na tela principal /painel
        r_painel = client.get("/painel", auth=(config.PAINEL_USUARIO, config.PAINEL_SENHA))
        self.assertEqual(r_painel.status_code, 200)
        html_p = r_painel.text
        self.assertIn('id="btn-importar-csv"', html_p)
        self.assertIn("abrirModalImportarCSV()", html_p)
        self.assertIn('id="modal-importar-csv-backdrop"', html_p)
        self.assertIn('id="dropzone-csv"', html_p)
        self.assertIn('id="input-arquivo-csv"', html_p)
        self.assertIn('id="btn-modal-enviar-csv"', html_p)

        # 2. Botão e modal na rota /painel/leituras
        r_leit = client.get("/painel/leituras", auth=(config.PAINEL_USUARIO, config.PAINEL_SENHA))
        self.assertEqual(r_leit.status_code, 200)
        html_l = r_leit.text
        self.assertIn('id="btn-importar-csv"', html_l)
        self.assertIn('id="modal-importar-csv-backdrop"', html_l)

        # 3. Função do componente modal isolada
        modal_html = _modal_importar_csv()
        self.assertIn('id="modal-importar-csv-card"', modal_html)
        self.assertIn('id="chk-importar-atualizar"', modal_html)

        # 4. Estilos CSS em ESTILO
        self.assertIn(".btn-importar-csv", ESTILO)
        self.assertIn(".dropzone-csv", ESTILO)
        self.assertIn(".modal-importar-status", ESTILO)

        # 5. Funções JavaScript em JS_PAINEL
        self.assertIn("function abrirModalImportarCSV(", JS_PAINEL)
        self.assertIn("function fecharModalImportarCSV(", JS_PAINEL)
        self.assertIn("function arquivoCSVSelecionado(", JS_PAINEL)
        self.assertIn("function definirArquivoCSV(", JS_PAINEL)
        self.assertIn("function inicializarDropzoneCSV(", JS_PAINEL)
        self.assertIn("function executarImportacaoCSV(", JS_PAINEL)
        self.assertIn("fecharModalImportarCSV()", JS_PAINEL)


class TestFiltroUFCidade(unittest.TestCase):
    """Testes unitários para o filtro de UF / Cidade na aba de leituras (Backend e Frontend)."""

    def test_dropdown_filtro_uf_renderizacao(self):
        from api.painel import _dropdown_filtro_uf

        # Lista vazia não deve renderizar dropdown
        self.assertEqual(_dropdown_filtro_uf([]), "")

        # Lista preenchida
        lista = [("BA", 1), ("RS", 3), ("SP", 8)]
        html = _dropdown_filtro_uf(lista, uf_selecionado="SP")
        self.assertIn('class="filtro-uf-wrap"', html)
        self.assertIn('id="select-filtro-uf"', html)
        self.assertIn('class="select-filtro-uf"', html)
        self.assertIn('onchange="filtrarPorUFClient(this.value)"', html)
        self.assertIn('<option value="">Todos os estados / UFs</option>', html)
        self.assertIn('<option value="BA">BA (1)</option>', html)
        self.assertIn('<option value="RS">RS (3)</option>', html)
        self.assertIn('<option value="SP" selected>SP (8)</option>', html)

        # Case-insensitivity ao marcar selected
        html_lower = _dropdown_filtro_uf(lista, uf_selecionado="rs")
        self.assertIn('<option value="RS" selected>RS (3)</option>', html_lower)

    def test_tabela_leituras_filtro_uf_backend(self):
        from api.painel import _tabela_leituras

        with TemporaryDirectory() as tmpdir:
            dir_leituras = Path(tmpdir)
            leituras = [
                ("20260908-100000-00000001", "Alice Gaúcha", "51999991111", "Porto Alegre", "RS"),
                ("20260908-110000-00000002", "Bruno Paulista", "11988882222", "São Paulo", "SP"),
                ("20260908-120000-00000003", "Carla Campineira", "19977773333", "Campinas", "SP"),
                ("20260908-130000-00000004", "Daniel Baiano", "71966664444", "Salvador", "BA"),
            ]
            for lid, nome, wa, cid_nome, cid_uf in leituras:
                (dir_leituras / f"{lid}.json").write_text(json.dumps({
                    "nome_completo": nome,
                    "whatsapp": wa,
                    "cidade": {"nome": cid_nome, "uf": cid_uf, "pais": "Brasil"},
                    "nascimento": {"dia": 10, "mes": 5, "ano": 1990},
                    "checkout": False,
                }), encoding="utf-8")

            with mock.patch.object(config, "DIR_LEITURAS", dir_leituras):
                # 1. Sem filtro
                res = _tabela_leituras(pagina=0)
                corpo, total_exibidos, total_pags, total_pessoas, total_chk, total_geral = res
                self.assertEqual(total_pessoas, 4)
                self.assertEqual(getattr(res, "lista_ufs", []), [("BA", 1), ("RS", 1), ("SP", 2)])
                self.assertIn('data-uf="rs"', corpo)
                self.assertIn('data-uf="sp"', corpo)
                self.assertIn('data-uf="ba"', corpo)

                # 2. Filtrando por SP
                res_sp = _tabela_leituras(pagina=0, uf="SP")
                corpo_sp, _, _, total_sp, _, _ = res_sp
                self.assertEqual(total_sp, 2)
                self.assertIn("Bruno Paulista", corpo_sp)
                self.assertIn("Carla Campineira", corpo_sp)
                self.assertNotIn("Alice Gaúcha", corpo_sp)
                self.assertNotIn("Daniel Baiano", corpo_sp)

                # 3. Filtrando por rs minúsculo (case-insensitive)
                res_rs = _tabela_leituras(pagina=0, uf="rs")
                corpo_rs, _, _, total_rs, _, _ = res_rs
                self.assertEqual(total_rs, 1)
                self.assertIn("Alice Gaúcha", corpo_rs)
                self.assertNotIn("Bruno Paulista", corpo_rs)

                # 4. Filtrando por estado inexistente
                res_invalido = _tabela_leituras(pagina=0, uf="AC")
                _, _, _, total_invalido, _, _ = res_invalido
                self.assertEqual(total_invalido, 0)

    def test_endpoints_com_filtro_uf(self):
        from main import app
        client = TestClient(app)

        with TemporaryDirectory() as tmpdir:
            dir_leituras = Path(tmpdir)
            leituras = [
                ("20260908-100000-00000001", "Alice Gaúcha", "51999991111", "Porto Alegre", "RS"),
                ("20260908-110000-00000002", "Bruno Paulista", "11988882222", "São Paulo", "SP"),
            ]
            for lid, nome, wa, cid_nome, cid_uf in leituras:
                (dir_leituras / f"{lid}.json").write_text(json.dumps({
                    "nome_completo": nome,
                    "whatsapp": wa,
                    "cidade": {"nome": cid_nome, "uf": cid_uf, "pais": "Brasil"},
                    "nascimento": {"dia": 10, "mes": 5, "ano": 1990},
                    "checkout": False,
                }), encoding="utf-8")

            with mock.patch.object(config, "DIR_LEITURAS", dir_leituras):
                # 1. Rota /painel?uf=SP
                r_painel = client.get("/painel?uf=SP", auth=(config.PAINEL_USUARIO, config.PAINEL_SENHA))
                self.assertEqual(r_painel.status_code, 200)
                html_p = r_painel.text
                self.assertIn('id="select-filtro-uf"', html_p)
                self.assertIn('value="SP" selected', html_p)
                self.assertIn("Bruno Paulista", html_p)
                self.assertNotIn("Alice Gaúcha", html_p)

                # 2. Rota /painel/leituras?uf=RS
                r_leit = client.get("/painel/leituras?uf=RS", auth=(config.PAINEL_USUARIO, config.PAINEL_SENHA))
                self.assertEqual(r_leit.status_code, 200)
                html_l = r_leit.text
                self.assertIn('id="select-filtro-uf"', html_l)
                self.assertIn('value="RS" selected', html_l)
                self.assertIn("Alice Gaúcha", html_l)
                self.assertNotIn("Bruno Paulista", html_l)

                # 3. Rota /painel/exportar-csv?uf=SP
                r_csv = client.get("/painel/exportar-csv?uf=SP", auth=(config.PAINEL_USUARIO, config.PAINEL_SENHA))
                self.assertEqual(r_csv.status_code, 200)
                csv_text = r_csv.text
                self.assertIn("Bruno Paulista", csv_text)
                self.assertNotIn("Alice Gaúcha", csv_text)

    def test_elementos_frontend_filtro_uf(self):
        from api.painel import ESTILO, JS_PAINEL

        # CSS
        self.assertIn(".filtro-uf-wrap", ESTILO)
        self.assertIn(".lbl-filtro-uf", ESTILO)
        self.assertIn(".select-filtro-uf", ESTILO)

        # JS
        self.assertIn("function filtrarPorUFClient(", JS_PAINEL)
        self.assertIn("data-uf", JS_PAINEL)
        self.assertIn("select-filtro-uf", JS_PAINEL)


class TestSelecaoGlobalContatos(unittest.TestCase):
    """Testes unitários para a seleção e exportação de todos os contatos (todas as páginas)."""

    def test_renderizacao_selecao_global_mais_de_20_contatos(self):
        """Quando há mais de 20 contatos, deve renderizar botão de selecionar todos e banner global."""
        from api.painel import _tabela_leituras

        with TemporaryDirectory() as tmpdir:
            dir_leituras = Path(tmpdir)
            # Cria 22 contatos
            for i in range(22):
                lid = f"20260908-1000{i:02d}-00000000"
                (dir_leituras / f"{lid}.json").write_text(json.dumps({
                    "nome_completo": f"Contato Multi {i}",
                    "whatsapp": f"119888800{i:02d}",
                    "nascimento": {"dia": 1, "mes": 1, "ano": 1990},
                }), encoding="utf-8")

            with mock.patch.object(config, "DIR_LEITURAS", dir_leituras):
                corpo, exibidos, pags, unicos, chk, geral = _tabela_leituras(pagina=0, por_pagina=20)
                self.assertEqual(unicos, 22)
                self.assertEqual(pags, 2)

                # Elementos de seleção global devem estar presentes
                self.assertIn('id="btn-sel-todos-filtro"', corpo)
                self.assertIn('Selecionar todos os <span class="num-total-filtro">22</span> contatos', corpo)
                self.assertIn('id="banner-selecao-global"', corpo)
                self.assertIn('data-total-filtro="22"', corpo)
                self.assertIn('data-total-pagina="20"', corpo)
                self.assertIn('id="btn-limpar-selecao"', corpo)
                self.assertIn('window._totalLeiturasFiltro = 22', corpo)
                self.assertIn('window._totalLeiturasPagina = 20', corpo)
                self.assertIn('(todos: 22)', corpo)

    def test_elementos_frontend_selecao_global(self):
        """Verifica a presença de CSS e JavaScript para a seleção global e exportação via servidor."""
        from api.painel import ESTILO, JS_PAINEL

        # CSS
        self.assertIn(".btn-sel-todos-filtro", ESTILO)
        self.assertIn(".btn-sel-todos-filtro.ativo", ESTILO)
        self.assertIn(".banner-selecao-global", ESTILO)
        self.assertIn(".btn-link-banner", ESTILO)
        self.assertIn(".btn-limpar-selecao", ESTILO)

        # JS
        self.assertIn("var _selecionarTodosFiltro = false;", JS_PAINEL)
        self.assertIn("var _idsSelecionados = new Set();", JS_PAINEL)
        self.assertIn("function obterAssinaturaFiltro(", JS_PAINEL)
        self.assertIn("function salvarEstadoSelecao(", JS_PAINEL)
        self.assertIn("function carregarEstadoSelecao(", JS_PAINEL)
        self.assertIn("function aplicarSelecaoNoDOM(", JS_PAINEL)
        self.assertIn("function toggleContatoIndividual(", JS_PAINEL)
        self.assertIn("function obterTotalFiltro(", JS_PAINEL)
        self.assertIn("function obterTotalPagina(", JS_PAINEL)
        self.assertIn("function toggleSelecionarTodosFiltro(", JS_PAINEL)
        self.assertIn("function selecionarTodosFiltro(", JS_PAINEL)
        self.assertIn("function limparSelecao(", JS_PAINEL)
        self.assertIn("function exportarTodosViaServidor(", JS_PAINEL)
        self.assertIn("function exportarSelecionadosViaServidor(", JS_PAINEL)
        self.assertIn("function exportarContatosCSV(", JS_PAINEL)
        self.assertIn("sessionStorage.getItem(\"painel_sel_todos\")", JS_PAINEL)
        self.assertIn("sessionStorage.getItem(\"painel_sel_ids\")", JS_PAINEL)
        self.assertIn("aplicarSelecaoNoDOM();", JS_PAINEL)
        self.assertIn("function atualizarLinksPresetsAba(", JS_PAINEL)

    def test_sintaxe_javascript_painel(self):
        """Valida que o script JS_PAINEL não contém erros de sintaxe."""
        import shutil
        import subprocess
        from api.painel import JS_PAINEL

        self.assertGreater(len(JS_PAINEL), 1000)
        self.assertIn("function abrirAba(", JS_PAINEL)

        node_bin = shutil.which("node")
        if node_bin:
            res = subprocess.run([node_bin, "--check", "-"], input=JS_PAINEL.encode("utf-8"), capture_output=True)
            self.assertEqual(res.returncode, 0, f"Erro de sintaxe em JS_PAINEL: {res.stderr.decode('utf-8', errors='ignore')}")

    def test_exportar_todos_via_servidor_com_mais_de_20_contatos(self):
        """Valida que /painel/exportar-csv exporta todos os contatos de todas as páginas."""
        from main import app
        client = TestClient(app)

        with TemporaryDirectory() as tmpdir:
            dir_leituras = Path(tmpdir)
            for i in range(25):
                lid = f"20260908-1200{i:02d}-11111111"
                (dir_leituras / f"{lid}.json").write_text(json.dumps({
                    "nome_completo": f"Pessoa Geral {i}",
                    "whatsapp": f"119777700{i:02d}",
                    "cidade": {"nome": "São Paulo", "uf": "SP"},
                    "nascimento": {"dia": 10, "mes": 2, "ano": 1985},
                }), encoding="utf-8")

            with mock.patch.object(config, "DIR_LEITURAS", dir_leituras):
                resp = client.get("/painel/exportar-csv", auth=(config.PAINEL_USUARIO, config.PAINEL_SENHA))
                self.assertEqual(resp.status_code, 200)
                csv_txt = resp.content.decode("utf-8-sig")

                # Todos os 25 contatos devem estar presentes no arquivo CSV
                for i in range(25):
                    self.assertIn(f"Pessoa Geral {i}", csv_txt)

    def test_exportar_por_lista_de_ids_selecionados_multiplas_paginas(self):
        """Valida que /painel/exportar-csv?ids=... exporta apenas os IDs selecionados entre múltiplas páginas."""
        from main import app
        client = TestClient(app)

        with TemporaryDirectory() as tmpdir:
            dir_leituras = Path(tmpdir)
            # Cria 25 contatos (página 1: 0 a 19, página 2: 20 a 24)
            for i in range(25):
                lid = f"20260908-1400{i:02d}-99999999"
                (dir_leituras / f"{lid}.json").write_text(json.dumps({
                    "nome_completo": f"MultiPag Pessoa {i}",
                    "whatsapp": f"119666600{i:02d}",
                    "cidade": {"nome": "Campinas", "uf": "SP"},
                    "nascimento": {"dia": 5, "mes": 5, "ano": 1992},
                }), encoding="utf-8")

            with mock.patch.object(config, "DIR_LEITURAS", dir_leituras):
                # Seleciona contato 2 (página 1) e contato 22 (página 2)
                id_p1 = "20260908-140002-99999999"
                id_p2 = "20260908-140022-99999999"
                url = f"/painel/exportar-csv?ids={id_p1},{id_p2}"
                resp = client.get(url, auth=(config.PAINEL_USUARIO, config.PAINEL_SENHA))
                self.assertEqual(resp.status_code, 200)
                csv_txt = resp.content.decode("utf-8-sig")

                self.assertIn("MultiPag Pessoa 2", csv_txt)
                self.assertIn("MultiPag Pessoa 22", csv_txt)
                # Não deve exportar outros contatos não selecionados
                self.assertNotIn("MultiPag Pessoa 0", csv_txt)
                self.assertNotIn("MultiPag Pessoa 10", csv_txt)
                self.assertNotIn("MultiPag Pessoa 24", csv_txt)

    def test_persistencia_selecao_renderizacao_paginas(self):
        """Valida que as checkboxes em todas as páginas contêm toggleContatoIndividual e script para reidratar seleção."""
        from api.painel import _tabela_leituras

        with TemporaryDirectory() as tmpdir:
            dir_leituras = Path(tmpdir)
            for i in range(25):
                lid = f"20260908-1500{i:02d}-88888888"
                (dir_leituras / f"{lid}.json").write_text(json.dumps({
                    "nome_completo": f"Persistência {i}",
                    "whatsapp": f"119555500{i:02d}",
                    "nascimento": {"dia": 1, "mes": 1, "ano": 1995},
                }), encoding="utf-8")

            with mock.patch.object(config, "DIR_LEITURAS", dir_leituras):
                # Página 1 (índice 0)
                res_p1 = _tabela_leituras(pagina=0, por_pagina=20)
                corpo_p1 = res_p1[0]
                self.assertIn('onchange="toggleContatoIndividual(this)"', corpo_p1)
                self.assertIn('setTimeout(aplicarSelecaoNoDOM, 30);', corpo_p1)

                # Página 2 (índice 1)
                res_p2 = _tabela_leituras(pagina=1, por_pagina=20)
                corpo_p2 = res_p2[0]
                self.assertIn('onchange="toggleContatoIndividual(this)"', corpo_p2)
                self.assertIn('setTimeout(aplicarSelecaoNoDOM, 30);', corpo_p2)


if __name__ == "__main__":
    unittest.main()




