# -*- coding: utf-8 -*-
"""Configuração privada por variáveis de ambiente."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).parent
load_dotenv(RAIZ / ".env")

# ---- OpenAI ----
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()

# UM modelo, sem cascata de fallback. Cair para outro modelo em silencio troca a
# voz da carta sem ninguem perceber, e foi exatamente o que aconteceu quando o
# teto de tokens era apertado demais. Se o Luna falhar, entra a carta de reserva,
# que e deterministica e escrita na voz do Crassus.
MODELO = os.environ.get("MODELO_LEITURA", "gpt-5.6-luna").strip()
MODELOS = [MODELO]

# A bússola agora mostra etapas honestas enquanto espera, então dá para deixar o
# modelo terminar em vez de cortar em 20s e cair na carta de reserva. O navegador
# desiste em 150s; aqui a folga é bem menor que isso.
TIMEOUT_LLM = float(os.environ.get("TIMEOUT_LLM", "45"))
# Em modelo com raciocinio este teto cobre raciocinio E saida. A carta usa ~500
# tokens; o raciocinio em medium passa facil de 1000. Com teto apertado a API
# devolve 200 com conteudo VAZIO, e a cascata cai silenciosa para o gpt-4o.
MAX_TOKENS_SAIDA = int(os.environ.get("MAX_TOKENS_SAIDA", "4000"))

# ---- painel ----
# Sem senha o painel nao sobe: ele concentra nome, nascimento e telefone de
# pessoas reais.
PAINEL_SENHA = os.environ.get("PAINEL_SENHA", "").strip()
PAINEL_USUARIO = os.environ.get("PAINEL_USUARIO", "crassus").strip()
EVENTOS_RETENCAO_DIAS = int(os.environ.get("EVENTOS_RETENCAO_DIAS", "180"))
LEITURAS_RETENCAO_DIAS = int(os.environ.get("LEITURAS_RETENCAO_DIAS", "180"))

# ---- webhook ----
WEBHOOK_HOTMART_URL = os.environ.get(
    "WEBHOOK_HOTMART_URL",
    "https://zapvoicecrassos.aryaraj.shop/api/webhooks/bussula-hotmart",
).strip()

# ---- caminhos ----
# O projeto vive dentro do OneDrive. Pasta sincronizada trava arquivo durante a
# sincronizacao, e no Windows isso vira PermissionError no open() - com gravacao
# de lead sendo descartada em silencio. Aponte DIR_DADOS no .env para fora do
# OneDrive (ex.: C:ussola-dados).
DIR_DADOS = Path(os.environ.get("DIR_DADOS", RAIZ / "dados"))
DIR_CACHE = DIR_DADOS / "cache"
DIR_LEITURAS = DIR_DADOS / "leituras"
DIR_EVENTOS = DIR_DADOS / "eventos"
DIR_PUBLICO = RAIZ / "publico"
DIR_PROMPTS = RAIZ / "prompts"

for _d in (DIR_CACHE, DIR_LEITURAS, DIR_EVENTOS):
    _d.mkdir(parents=True, exist_ok=True)


def dentro_do_onedrive() -> bool:
    """Usado pelo /api/saude para avisar antes de virar perda de lead."""
    return "onedrive" in str(DIR_DADOS).lower()


def exigir_chave() -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY ausente. Copie .env.example para .env e coloque uma "
            "chave nova. A chave que circulou no chat esta comprometida e deve "
            "ser revogada em https://platform.openai.com/api-keys"
        )
    return OPENAI_API_KEY


def tem_chave() -> bool:
    return bool(OPENAI_API_KEY)
