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
# Em "high" o modelo pensa mais antes de escrever, e demora mais. Medido aqui:
# medium entregava em 16-30s, high fica na casa dos 30-60s. O navegador desiste
# em 150s, entao ainda ha folga - mas o teto precisou subir junto, senao um
# estouro de tempo derruba a leitura para a carta de reserva, que e o pior
# resultado possivel.
TIMEOUT_LLM = float(os.environ.get("TIMEOUT_LLM", "45"))

# Quanto o modelo pensa antes de escrever. A carta tem muita regra simultanea -
# registro, ancora concreta, elo entre as partes, proporcao de incentivo - e em
# "medium" ele cumpria umas e esquecia outras.
# O TEMPO AQUI E O TAMANHO DO VIDEO, E NAO UMA PREFERENCIA.
#
# O botao de avancar so aparece quando a carta fica pronta, e a VSL que segura
# a espera tem 22 segundos. Carta mais lenta que isso = tela parada depois do
# video acabar = gente saindo do funil na ultima tela antes da oferta.
#
# Medido no mesmo mapa, quatro rodadas cada:
#   high     43 a 92s
#   medium   27 a 31s
#   minimal  24 a 28s   (nao e o mais rapido, por incrivel que pareca)
#   low       6 a  9s   <-- cabe no video com folga para uma regeneracao
#
# "low" nao reprovou nenhuma vez na auditoria dura - nao inventa astrologia.
# O que ele perde e acabamento de estilo, e para isso existe a regeneracao,
# que em "low" custa mais 8s em vez de mais 50.
RACIOCINIO = os.environ.get("RACIOCINIO_LEITURA", "low").strip()

# O ORCAMENTO TOTAL da geracao, somando todas as tentativas. O TIMEOUT_LLM
# acima limita UMA chamada; este limita a soma - e e ele que importa, porque
# quem desiste e o navegador, em 150s, e nao a API.
#
# Medido: uma carta em "high" leva ~65s e uma regeneracao em "medium" ~50s.
# Somadas, 117s, contra 150s do navegador. Margem de menos para o calculo do
# mapa, a rede e a tela. Passando deste orcamento, a leitura para de tentar de
# novo e entrega a melhor carta que ja tem - o que quase sempre significa uma
# carta boa com um problema de tom, em vez de um erro de conexao.
ORCAMENTO_LLM = float(os.environ.get("ORCAMENTO_LLM", "40"))

# Quanto reservar para a regeneracao caber dentro do orcamento. A primeira
# versao desta conta olhava so o tempo JA gasto: aos 65s a segunda tentativa
# era autorizada por estar abaixo do limite, gastava mais 50s e terminava em
# 115s. O teste certo nao e "ja estourei?", e "a proxima cabe?".
# Em "low" a regeneracao custa ~9s. Com 12 de reserva e 40 de orcamento, o
# pior caso realista fica em torno de 20s, que e o tamanho do video.
RESERVA_REGENERACAO = float(os.environ.get("RESERVA_REGENERACAO", "12"))
# Em modelo com raciocinio este teto cobre raciocinio E saida. A carta usa ~600
# tokens; o raciocinio em "high" passa de 3000 com folga. Com teto apertado a
# API devolve 200 com conteudo VAZIO - e como isso vira excecao, a leitura cai
# para a carta de reserva sem ninguem entender por que. Por isso o teto subiu
# junto com o esforco. Medido em quatro mapas: o raciocinio ficou entre 7,7k e
# 8,9k tokens. Com teto em 12000 o pior caso usava 79%, apertado demais; 16000
# deixa quase o dobro do observado. Subir nao custa: o teto e um limite, e a
# cobranca e pelo que foi usado.
MAX_TOKENS_SAIDA = int(os.environ.get("MAX_TOKENS_SAIDA", "16000"))

# ---- painel ----
# Sem senha o painel nao sobe: ele concentra nome, nascimento e telefone de
# pessoas reais.
PAINEL_SENHA = os.environ.get("PAINEL_SENHA", "").strip()
PAINEL_USUARIO = os.environ.get("PAINEL_USUARIO", "crassus").strip()
EVENTOS_RETENCAO_DIAS = int(os.environ.get("EVENTOS_RETENCAO_DIAS", "180"))
LEITURAS_RETENCAO_DIAS = int(os.environ.get("LEITURAS_RETENCAO_DIAS", "180"))

# ---- webhook ----
WEBHOOK_LEITURA_URL = os.environ.get(
    "WEBHOOK_LEITURA_URL",
    os.environ.get(
        "WEBHOOK_HOTMART_URL",
        "https://zapvoicecrassos.aryaraj.shop/api/webhooks/bussula-hotmart",
    ),
).strip()
WEBHOOK_HOTMART_URL = WEBHOOK_LEITURA_URL

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
