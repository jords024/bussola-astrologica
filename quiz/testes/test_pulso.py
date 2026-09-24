# -*- coding: utf-8 -*-
"""Testes do /api/pulso — o aviso de atividade no canto da oferta.

O risco aqui não é a rota cair: é ela vazar dado de gente real. Cada leitura
no disco tem nome completo, WhatsApp, data e hora de nascimento e o texto da
carta. Sai daqui primeiro nome e cidade, e mais nada. Os testes abaixo existem
principalmente para que isso continue verdade.
"""
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from fastapi.testclient import TestClient

import config
import main
from api import pulso


def leitura(nome="Marina Duarte Silva", cidade="Belo Horizonte", uf="Minas Gerais",
            minutos=12, **extra):
    quando = datetime.now(timezone.utc) - timedelta(minutes=minutos)
    d = {
        "cliente_id": "sid-real",
        "nome_completo": nome,
        "whatsapp": "5531999998888",
        "nascimento": {"ano": 1990, "mes": 4, "dia": 2, "hora": 14, "minuto": 30},
        "cidade": {"nome": cidade, "uf": uf, "lat": -19.9, "lng": -43.9},
        "carta": {"destaque": "uma frase que nunca deve sair daqui"},
        "gravado_em": quando.isoformat(timespec="seconds"),
    }
    d.update(extra)
    return d


class Pulso(unittest.TestCase):
    def setUp(self):
        pulso._cache, pulso._cache_em = [], 0.0
        self.addCleanup(lambda: (setattr(pulso, "_cache", []),
                                 setattr(pulso, "_cache_em", 0.0)))

    def pedir(self, arquivos):
        """Escreve as leituras num diretório temporário e chama a rota."""
        with TemporaryDirectory() as tmp:
            pasta = Path(tmp)
            for i, dados in enumerate(arquivos):
                nome = f"2026092{i%9}-1200{i:02d}-aaaaaaa{i%10}.json"
                alvo = pasta / nome
                if isinstance(dados, str):
                    alvo.write_text(dados, encoding="utf-8")
                else:
                    alvo.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
            with mock.patch.object(config, "DIR_LEITURAS", pasta):
                pulso._cache, pulso._cache_em = [], 0.0
                r = TestClient(main.app).get("/api/pulso")
                self.assertEqual(r.status_code, 200)
                return r.json()["itens"], r.text

    def test_devolve_primeiro_nome_e_cidade(self):
        itens, _ = self.pedir([leitura()])
        self.assertEqual(len(itens), 1)
        self.assertEqual(itens[0]["nome"], "Marina")
        self.assertEqual(itens[0]["cidade"], "Belo Horizonte")
        self.assertEqual(itens[0]["uf"], "MG")
        self.assertIsInstance(itens[0]["ha_minutos"], int)

    def test_nao_vaza_dado_pessoal(self):
        """O teste mais importante deste arquivo."""
        _, corpo = self.pedir([leitura()])
        for proibido in ("Duarte", "Silva", "5531999998888", "1990",
                         "nascimento", "whatsapp", "carta", "nunca deve sair",
                         "-19.9", "cliente_id"):
            self.assertNotIn(proibido, corpo, f"vazou: {proibido}")

    def test_ignora_leitura_de_teste(self):
        itens, _ = self.pedir([
            leitura(cliente_id="teste-porta-amor"),
            leitura(nome="Bruno Teste"),
            leitura(nome="Aline Souza", cidade="Recife", uf="Pernambuco"),
        ])
        self.assertEqual([i["nome"] for i in itens], ["Aline"])

    def test_nao_repete_a_mesma_pessoa(self):
        """Quem refaz o quiz não pode ocupar o rodízio inteiro."""
        itens, _ = self.pedir([leitura(), leitura(), leitura()])
        self.assertEqual(len(itens), 1)

    def test_leitura_velha_fica_de_fora(self):
        """'Acabou de' precisa ser verdade: 72h é o limite."""
        itens, _ = self.pedir([leitura(minutos=60 * 24 * 5)])
        self.assertEqual(itens, [])

    def test_arquivo_corrompido_nao_derruba_a_lista(self):
        itens, _ = self.pedir([
            "{ isto nao e json",
            leitura(nome="Carla Nunes", cidade="Curitiba", uf="Paraná"),
        ])
        self.assertEqual([i["nome"] for i in itens], ["Carla"])

    def test_sem_cidade_nao_entra(self):
        sem = leitura()
        sem["cidade"] = {}
        itens, _ = self.pedir([sem])
        self.assertEqual(itens, [])

    def test_diretorio_vazio_responde_lista_vazia(self):
        itens, _ = self.pedir([])
        self.assertEqual(itens, [])

    def test_respeita_o_teto_de_itens(self):
        muitas = [leitura(nome=f"Pessoa{i}", cidade=f"Cidade{i}")
                  for i in range(pulso.MAX_ITENS + 8)]
        itens, _ = self.pedir(muitas)
        self.assertLessEqual(len(itens), pulso.MAX_ITENS)

    def test_sigla_do_estado(self):
        self.assertEqual(pulso._sigla("São Paulo"), "SP")
        self.assertEqual(pulso._sigla("mg"), "MG")
        self.assertEqual(pulso._sigla("Rio Grande do Sul"), "RS")
        self.assertEqual(pulso._sigla(""), "")
        self.assertEqual(pulso._sigla("Pais Inventado"), "")
