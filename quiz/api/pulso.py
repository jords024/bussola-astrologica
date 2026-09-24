# -*- coding: utf-8 -*-
"""GET /api/pulso — quem passou por aqui há pouco.

Alimenta o aviso que aparece no canto da tela de oferta. A regra que define
este arquivo inteiro: **só sai daqui o que de fato aconteceu**. Cada linha
devolvida corresponde a uma leitura real gravada em disco, com a cidade que a
própria pessoa informou.

O que NUNCA sai: sobrenome, WhatsApp, data ou hora de nascimento, id da leitura
e qualquer coisa do texto da carta. Primeiro nome e cidade, e só. São dados de
pessoas reais sendo mostrados a terceiros, então o corte é pelo mínimo
necessário para a frase fazer sentido.
"""
from __future__ import annotations

import json
import logging
import re
import threading
import time
import unicodedata
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

import config

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_ITENS = 20
# varrer o diretorio a cada visita seria desperdicio: a lista muda devagar e
# todo mundo que chega na tela 10 pede a mesma coisa
CACHE_SEGUNDOS = 60
# leituras mais velhas que isto nao entram: "acabou de" precisa ser verdade
JANELA_HORAS = 72

RE_ID = re.compile(r"^\d{8}-\d{6}-[a-f0-9]{8}$")

# o cadastro guarda o estado por extenso; a sigla cabe melhor no aviso
SIGLA_UF = {
    "acre": "AC", "alagoas": "AL", "amapa": "AP", "amazonas": "AM",
    "bahia": "BA", "ceara": "CE", "distrito federal": "DF",
    "espirito santo": "ES", "goias": "GO", "maranhao": "MA",
    "mato grosso": "MT", "mato grosso do sul": "MS", "minas gerais": "MG",
    "para": "PA", "paraiba": "PB", "parana": "PR", "pernambuco": "PE",
    "piaui": "PI", "rio de janeiro": "RJ", "rio grande do norte": "RN",
    "rio grande do sul": "RS", "rondonia": "RO", "roraima": "RR",
    "santa catarina": "SC", "sao paulo": "SP", "sergipe": "SE",
    "tocantins": "TO",
}


def _sigla(uf: str) -> str:
    bruto = str(uf or "").strip()
    if not bruto:
        return ""
    if len(bruto) == 2:
        return bruto.upper()
    return SIGLA_UF.get(_sem_acento(bruto), "")

_cache: list[dict] = []
_cache_em: float = 0.0
_lock = threading.Lock()


def _primeiro_nome(completo: str) -> Optional[str]:
    """Só o primeiro nome, capitalizado. Nada de sobrenome."""
    partes = [p for p in str(completo or "").strip().split() if p]
    if not partes:
        return None
    nome = partes[0]
    if len(nome) < 2 or len(nome) > 20 or not nome.replace("-", "").isalpha():
        return None
    return nome[:1].upper() + nome[1:].lower()


def _sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").lower()


def _e_teste(dados: dict, nome: Optional[str]) -> bool:
    cid = str(dados.get("cliente_id") or "")
    if cid.startswith("teste-") or cid in ("ling", "acentos", "sem-hora"):
        return True
    if dados.get("teste"):
        return True
    sem = _sem_acento(str(dados.get("nome_completo") or ""))
    return "teste" in sem or (nome or "").lower() == "teste"


def _ha_minutos(dados: dict, agora: datetime) -> Optional[int]:
    bruto = dados.get("gravado_em")
    if not bruto:
        return None
    try:
        quando = datetime.fromisoformat(str(bruto))
    except ValueError:
        return None
    if quando.tzinfo is None:
        quando = quando.replace(tzinfo=timezone.utc)
    minutos = int((agora - quando).total_seconds() // 60)
    return minutos if 0 <= minutos <= JANELA_HORAS * 60 else None


def _coletar() -> list[dict]:
    """Os arquivos mais recentes primeiro. O nome do arquivo já é a ordem."""
    pasta = config.DIR_LEITURAS
    try:
        arquivos = sorted((p for p in pasta.glob("*.json") if RE_ID.match(p.stem)),
                          key=lambda p: p.stem, reverse=True)
    except Exception as e:
        logger.warning("pulso: nao consegui listar %s: %s", pasta, e)
        return []

    agora = datetime.now(timezone.utc)
    saida: list[dict] = []
    # a mesma pessoa refazendo o quiz nao pode aparecer duas vezes no rodizio
    vistos: set = set()
    # o teto de leitura e maior que MAX_ITENS porque parte sera descartada
    for caminho in arquivos[:MAX_ITENS * 6]:
        if len(saida) >= MAX_ITENS:
            break
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except Exception:
            continue  # arquivo truncado nao derruba a lista inteira
        if not isinstance(dados, dict):
            continue
        nome = _primeiro_nome(dados.get("nome_completo"))
        if not nome or _e_teste(dados, nome):
            continue
        cidade = (dados.get("cidade") or {})
        if not isinstance(cidade, dict) or not cidade.get("nome"):
            continue
        minutos = _ha_minutos(dados, agora)
        if minutos is None:
            continue
        cidade_nome = str(cidade.get("nome"))[:40]
        chave = (_sem_acento(nome), _sem_acento(cidade_nome))
        if chave in vistos:
            continue
        vistos.add(chave)
        saida.append({
            "nome": nome,
            "cidade": cidade_nome,
            "uf": _sigla(cidade.get("uf")),
            "ha_minutos": minutos,
        })
    return saida


@router.get("/api/pulso")
async def pulso() -> JSONResponse:
    global _cache, _cache_em
    itens: list[dict] = []
    try:
        agora = time.time()
        with _lock:
            if agora - _cache_em > CACHE_SEGUNDOS or not _cache:
                _cache = _coletar()
                _cache_em = agora
            itens = list(_cache)
    except Exception as e:
        logger.warning("pulso: falhou, devolvendo vazio: %s", e)
        itens = []
    # lista vazia e resposta valida: o cliente simplesmente nao mostra nada
    return JSONResponse({"itens": itens},
                        headers={"Cache-Control": "public, max-age=60"})
