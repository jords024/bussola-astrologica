# -*- coding: utf-8 -*-
"""Testes unitários para o módulo financeiro e visualização de custos no painel.

Testa:
1. Cálculos de custos de tokens para LLM (OpenAI), Cache e Reserva.
2. Agregação financeira com divisão por modelo, área e médias.
3. Elementos frontend da barra lateral (Sidebar) com botões Dashboard e Financeiro.
4. Renderização da tela financeira com KPIs, tabelas de modelos/áreas e extrato detalhado.
5. Endpoint de exportação CSV financeiro com validação de autenticação e formato.
"""
import io
import json
import unittest
from datetime import date, datetime, timedelta
from unittest import mock

from fastapi import Request
from starlette.testclient import TestClient

import config
from main import app
from servicos.financeiro import (
    TABELA_PRECOS, TAXA_CAMBIO_BRL, PROMPT_TOKENS_MEDIO, COMPLETION_TOKENS_MEDIO,
    calcular_custo_tokens, calcular_custo_item, agregar_financeiro
)


class TestServicoFinanceiro(unittest.TestCase):
    """Testes unitários das funções puras de cálculo e agregação financeira."""

    def test_calcular_custo_tokens_modelos(self):
        # Modelo Luna (padrão)
        custo_luna = calcular_custo_tokens("gpt-5.6-luna", 1000, 1000)
        esperado_luna = (1000 * 2.50 / 1_000_000) + (1000 * 10.00 / 1_000_000)
        self.assertAlmostEqual(custo_luna, esperado_luna, places=6)

        # Modelo mini
        custo_mini = calcular_custo_tokens("gpt-4o-mini", 10000, 10000)
        esperado_mini = (10000 * 0.15 / 1_000_000) + (10000 * 0.60 / 1_000_000)
        self.assertAlmostEqual(custo_mini, esperado_mini, places=6)

        # Cache e reserva têm custo zero
        self.assertEqual(calcular_custo_tokens("cache", 5000, 5000), 0.0)
        self.assertEqual(calcular_custo_tokens("reserva", 5000, 5000), 0.0)

    def test_calcular_custo_item_llm_com_tokens_reais(self):
        dados = {
            "nome_completo": "Clarice Lispector",
            "whatsapp": "85999990001",
            "quiz": {"area": "amor"},
            "meta": {
                "modelo": "gpt-5.6-luna",
                "validacao": "ok",
                "tentativas": 1,
                "ms_llm": 12500,
                "prompt_tokens": 1500,
                "completion_tokens": 1200,
            }
        }
        res = calcular_custo_item(dados, "20260926-000001")
        self.assertEqual(res["tipo"], "llm")
        self.assertEqual(res["modelo"], "gpt-5.6-luna")
        self.assertFalse(res["estimado"])
        self.assertEqual(res["prompt_tokens"], 1500)
        self.assertEqual(res["completion_tokens"], 1200)
        self.assertEqual(res["total_tokens"], 2700)
        esperado_usd = (1500 * 2.50 / 1_000_000) + (1200 * 10.00 / 1_000_000)
        self.assertAlmostEqual(res["custo_usd"], esperado_usd, places=6)
        self.assertAlmostEqual(res["custo_brl"], esperado_usd * TAXA_CAMBIO_BRL, places=4)
        self.assertEqual(res["economia_usd"], 0.0)

    def test_calcular_custo_item_llm_legado_estimado(self):
        dados = {
            "nome_completo": "Lead Sem Metadados Exatos",
            "whatsapp": "11988887777",
            "quiz": {"area": "carreira"},
            "meta": {
                "modelo": "gpt-5.6-luna",
                "validacao": "regenerado",
                "tentativas": 2,
                "ms_llm": 25000,
            }
        }
        res = calcular_custo_item(dados, "20260926-000002")
        self.assertEqual(res["tipo"], "llm")
        self.assertTrue(res["estimado"])
        self.assertEqual(res["prompt_tokens"], PROMPT_TOKENS_MEDIO * 2)
        self.assertEqual(res["completion_tokens"], COMPLETION_TOKENS_MEDIO * 2)
        self.assertEqual(res["total_tokens"], (PROMPT_TOKENS_MEDIO + COMPLETION_TOKENS_MEDIO) * 2)
        self.assertGreater(res["custo_usd"], 0.0)
        self.assertGreater(res["custo_brl"], 0.0)

    def test_calcular_custo_item_cache_economia(self):
        dados = {
            "nome_completo": "Lead Que Usou Cache",
            "whatsapp": "21977776666",
            "quiz": {"area": "dinheiro"},
            "meta": {
                "modelo": "cache",
                "validacao": "cache",
                "tentativas": 0,
                "ms_llm": 0,
            }
        }
        res = calcular_custo_item(dados, "20260926-000003")
        self.assertEqual(res["tipo"], "cache")
        self.assertEqual(res["custo_usd"], 0.0)
        self.assertEqual(res["custo_brl"], 0.0)
        self.assertEqual(res["total_tokens"], 0)
        self.assertGreater(res["economia_usd"], 0.0)
        self.assertGreater(res["economia_brl"], 0.0)

    def test_calcular_custo_item_reserva_custo_zero(self):
        dados = {
            "nome_completo": "Lead Que Caiu Na Reserva",
            "whatsapp": "",
            "quiz": {"area": "casa"},
            "meta": {
                "modelo": None,
                "validacao": "reserva",
                "tentativas": 0,
                "ms_llm": 0,
            }
        }
        res = calcular_custo_item(dados, "20260926-000004")
        self.assertEqual(res["tipo"], "reserva")
        self.assertEqual(res["custo_usd"], 0.0)
        self.assertEqual(res["custo_brl"], 0.0)
        self.assertEqual(res["economia_usd"], 0.0)

    def test_agregar_financeiro_multiplos_itens(self):
        itens = [
            {
                "leitura_id": "id-1", "nome": "A", "area": "amor", "modelo": "gpt-5.6-luna",
                "tipo": "llm", "prompt_tokens": 1000, "completion_tokens": 1000, "total_tokens": 2000,
                "custo_usd": 0.0125, "custo_brl": 0.06875, "economia_usd": 0.0, "economia_brl": 0.0,
                "tentativas": 1, "validacao": "ok", "ms_llm": 12000, "data_bsb": "26/09/26 10:00",
                "whatsapp": "85999990001", "estimado": False
            },
            {
                "leitura_id": "id-2", "nome": "B", "area": "amor", "modelo": "cache",
                "tipo": "cache", "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
                "custo_usd": 0.0, "custo_brl": 0.0, "economia_usd": 0.018, "economia_brl": 0.099,
                "tentativas": 0, "validacao": "cache", "ms_llm": 0, "data_bsb": "26/09/26 10:05",
                "whatsapp": "85999990002", "estimado": False
            },
            {
                "leitura_id": "id-3", "nome": "C", "area": "dinheiro", "modelo": "reserva",
                "tipo": "reserva", "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
                "custo_usd": 0.0, "custo_brl": 0.0, "economia_usd": 0.0, "economia_brl": 0.0,
                "tentativas": 0, "validacao": "reserva", "ms_llm": 0, "data_bsb": "26/09/26 10:10",
                "whatsapp": "", "estimado": False
            },
        ]
        res = agregar_financeiro(itens)
        self.assertEqual(res["total_leituras"], 3)
        self.assertEqual(res["qtd_llm"], 1)
        self.assertEqual(res["qtd_cache"], 1)
        self.assertEqual(res["qtd_reserva"], 1)
        self.assertAlmostEqual(res["pct_cache"], 33.333, places=2)
        self.assertEqual(res["total_tokens"], 2000)
        self.assertAlmostEqual(res["custo_total_usd"], 0.0125, places=4)
        self.assertAlmostEqual(res["economia_total_usd"], 0.018, places=4)
        self.assertGreater(res["custo_medio_geral_brl"], 0.0)
        self.assertGreater(res["custo_medio_llm_brl"], 0.0)
        self.assertEqual(len(res["por_modelo"]), 3)
        self.assertEqual(len(res["por_area"]), 2)


class TestPainelFinanceiro(unittest.TestCase):
    """Testes de integração e interface para a tela Financeiro e barra lateral do painel."""

    def setUp(self):
        self.client = TestClient(app)
        self.auth = ("crassus", "senha_teste")

    def test_sidebar_renderiza_botoes_dashboard_e_financeiro(self):
        with mock.patch.object(config, "PAINEL_SENHA", "senha_teste"), \
             mock.patch.object(config, "PAINEL_USUARIO", "crassus"):
            resp = self.client.get("/painel", auth=self.auth)
            self.assertEqual(resp.status_code, 200)
            html_text = resp.text

            # Layout e Sidebar
            self.assertIn('class="layout-painel"', html_text)
            self.assertIn('class="sidebar-painel"', html_text)

            # Botão 1: Dashboard
            self.assertIn('id="btn-visao-dashboard"', html_text)
            self.assertIn('Dashboard', html_text)
            self.assertIn('📊', html_text)

            # Botão 2: Financeiro
            self.assertIn('id="btn-visao-financeiro"', html_text)
            self.assertIn('Financeiro', html_text)
            self.assertIn('💰', html_text)

            # Containers das duas telas/visões
            self.assertIn('id="visao-dashboard"', html_text)
            self.assertIn('id="visao-financeiro"', html_text)

            # Scripts de chaveamento
            self.assertIn('function trocarVisao(visao)', html_text)
            self.assertIn('function filtrarTabelaFinanceiro(termo)', html_text)

    def test_painel_visao_financeiro_ativada_via_parametro(self):
        with mock.patch.object(config, "PAINEL_SENHA", "senha_teste"), \
             mock.patch.object(config, "PAINEL_USUARIO", "crassus"):
            resp = self.client.get("/painel?view=financeiro", auth=self.auth)
            self.assertEqual(resp.status_code, 200)
            html_text = resp.text

            # Botão financeiro ativado
            self.assertIn('id="btn-visao-financeiro" onclick="trocarVisao(\'financeiro\'); return false;" title="Visualizar custos e gastos com geração de mensagens pela IA">', html_text)
            # Tela Financeiro visível (com classe on)
            self.assertIn('id="visao-financeiro" class="visao-painel on"', html_text)

    def test_conteudo_e_metricas_tela_financeiro(self):
        with mock.patch.object(config, "PAINEL_SENHA", "senha_teste"), \
             mock.patch.object(config, "PAINEL_USUARIO", "crassus"):
            resp = self.client.get("/painel?view=financeiro", auth=self.auth)
            self.assertEqual(resp.status_code, 200)
            html_text = resp.text

            # Título da tela financeira
            self.assertIn("Financeiro · Custos de Geração", html_text)

            # Cards de custos
            self.assertIn("gasto total no período", html_text)
            self.assertIn("custo médio / leitura total", html_text)
            self.assertIn("custo médio / mensagem IA", html_text)
            self.assertIn("economia gerada com cache", html_text)
            self.assertIn("tokens totais", html_text)

            # Tabelas de distribuição
            self.assertIn("Distribuição por Modelo / Origem", html_text)
            self.assertIn("Gastos por Área do Quiz", html_text)
            self.assertIn("Extrato Detalhado de Gerações", html_text)

            # Campo de busca e exportação CSV
            self.assertIn('id="busca-tabela-financeiro"', html_text)
            self.assertIn('/painel/financeiro/exportar-csv', html_text)

    def test_exportar_csv_financeiro_autenticado_e_sem_auth(self):
        with mock.patch.object(config, "PAINEL_SENHA", "senha_teste"), \
             mock.patch.object(config, "PAINEL_USUARIO", "crassus"):
            # 1. Sem autenticação -> 401
            resp_no_auth = self.client.get("/painel/financeiro/exportar-csv")
            self.assertEqual(resp_no_auth.status_code, 401)

            # 2. Com autenticação -> 200 CSV válido
            resp_auth = self.client.get("/painel/financeiro/exportar-csv", auth=self.auth)
            self.assertEqual(resp_auth.status_code, 200)
            self.assertIn("text/csv", resp_auth.headers.get("content-type", ""))
            self.assertIn("attachment; filename=", resp_auth.headers.get("content-disposition", ""))

            linhas = resp_auth.text.splitlines()
            self.assertGreater(len(linhas), 0)
            cabecalho = linhas[0]
            self.assertIn("Data (BSB)", cabecalho)
            self.assertIn("Leitura ID", cabecalho)
            self.assertIn("Nome Completo", cabecalho)
            self.assertIn("Custo (USD)", cabecalho)
            self.assertIn("Custo (BRL)", cabecalho)
            self.assertIn("Economia (BRL)", cabecalho)

    def test_filtros_periodo_financeiro_mantem_visao_financeiro_ativa(self):
        with mock.patch.object(config, "PAINEL_SENHA", "senha_teste"), \
             mock.patch.object(config, "PAINEL_USUARIO", "crassus"):
            # 1. Filtro com preset de dias (ex: 30 dias)
            resp_dias = self.client.get("/painel?view=financeiro&dias=30", auth=self.auth)
            self.assertEqual(resp_dias.status_code, 200)
            html_dias = resp_dias.text
            self.assertIn('id="visao-financeiro" class="visao-painel on"', html_dias)
            self.assertIn('href="/painel?view=financeiro&preset=30dias&dias=30#financeiro"', html_dias)
            self.assertIn('<input type="hidden" name="view" value="financeiro">', html_dias)
            self.assertIn('action="/painel#financeiro"', html_dias)

            # 2. Filtro com datas personalizadas
            resp_datas = self.client.get("/painel?view=financeiro&de=2026-09-01&ate=2026-09-05", auth=self.auth)
            self.assertEqual(resp_datas.status_code, 200)
            html_datas = resp_datas.text
            self.assertIn('id="visao-financeiro" class="visao-painel on"', html_datas)
            self.assertIn('name="de" value="2026-09-01"', html_datas)
            self.assertIn('name="ate" value="2026-09-05"', html_datas)

    def test_paginacao_financeiro_estrutura_e_funcoes_js(self):
        with mock.patch.object(config, "PAINEL_SENHA", "senha_teste"), \
             mock.patch.object(config, "PAINEL_USUARIO", "crassus"):
            resp = self.client.get("/painel?view=financeiro", auth=self.auth)
            self.assertEqual(resp.status_code, 200)
            html_text = resp.text

            # Container da paginação financeira
            self.assertIn('id="paginacao-financeiro"', html_text)
            self.assertIn('.paginacao{', html_text)

            # Funções e variáveis JS de paginação e filtragem
            self.assertIn("function mudarPaginaFin(novaPagina)", html_text)
            self.assertIn("function atualizarTabelaFinanceiroPaginada(", html_text)
            self.assertIn("var _porPaginaFin = 20;", html_text)
            self.assertIn("var _pagFinAtual = 1;", html_text)

    def test_barra_paginacao_fin_unitario(self):
        from api.painel import _barra_paginacao_fin

        # 1. Teste com 58 itens na página 0 (primeira página, 20 por página)
        params = {"view": "financeiro", "dias": "30"}
        html_p0 = _barra_paginacao_fin(pagina=0, total_itens=58, base_url="/painel", params=params, por_pagina=20)
        self.assertIn('id="paginacao-financeiro"', html_p0)
        self.assertIn("Mostrando <b>1–20</b> de <b>58</b> gerações · Página 1 de 3", html_p0)
        self.assertIn('<span class="pag-btn disabled">← Anterior</span>', html_p0)
        self.assertIn('<span class="pag-btn on">1</span>', html_p0)
        self.assertIn('onclick="mudarPaginaFin(2); return false;"', html_p0)
        self.assertIn('onclick="mudarPaginaFin(3); return false;"', html_p0)
        self.assertIn('onclick="mudarPaginaFin(2); return false;">Próxima →</a>', html_p0)

        # 2. Teste com página 1 (segunda página)
        html_p1 = _barra_paginacao_fin(pagina=1, total_itens=58, base_url="/painel", params=params, por_pagina=20)
        self.assertIn("Mostrando <b>21–40</b> de <b>58</b> gerações · Página 2 de 3", html_p1)
        self.assertIn('onclick="mudarPaginaFin(1); return false;">← Anterior</a>', html_p1)
        self.assertIn('<span class="pag-btn on">2</span>', html_p1)
        self.assertIn('onclick="mudarPaginaFin(3); return false;">Próxima →</a>', html_p1)

        # 3. Teste com <= 20 itens (apenas 1 página, sem poluir a tela com botões de paginação)
        html_peq = _barra_paginacao_fin(pagina=0, total_itens=14, base_url="/painel", params=params, por_pagina=20)
        self.assertEqual(html_peq, '<div id="paginacao-financeiro"></div>')

        # 4. Teste com 0 itens
        html_vazio = _barra_paginacao_fin(pagina=0, total_itens=0, base_url="/painel", params=params, por_pagina=20)
        self.assertEqual(html_vazio, '<div id="paginacao-financeiro"></div>')


if __name__ == "__main__":
    unittest.main()

