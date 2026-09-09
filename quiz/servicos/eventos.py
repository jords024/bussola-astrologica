# -*- coding: utf-8 -*-
"""Coleta de eventos do funil.

Uma linha JSONL por evento, um arquivo por dia. Sem banco, seguindo o padrão de
arquivos simples que `registro.py` já usa.

**Nenhum dado pessoal entra aqui.** Nome, data e hora de nascimento, cidade,
coordenadas e telefone ficam só em `dados/leituras/`. Os eventos ligam a pessoas
apenas por `leitura_id`. Assim o arquivo que se abre todo dia para ver o funil
não é uma base de dados pessoais.

`(sid, seq)` é a chave de idempotência: o escritor não deduplica (precisaria de
estado), quem deduplica é o leitor, na mesma passada em que agrega.
"""
from __future__ import annotations

import json
import logging
import re
import threading
import time
from collections import defaultdict, deque
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator, Optional

from config import DIR_EVENTOS, EVENTOS_RETENCAO_DIAS

logger = logging.getLogger(__name__)

FUSO_BSB = timezone(timedelta(hours=-3))


def hoje_bsb() -> date:
    return datetime.now(FUSO_BSB).date()

VERSAO = 1

# Um unico processo hoje (iniciar.cmd nao passa --workers). Se um dia virar
# multi-worker, este lock e os contadores de limite param de proteger.
_LOCK = threading.Lock()

EVENTOS_VALIDOS = {
    "sessao_inicio", "tela", "escolha", "form_campo", "form_erro", "form_envio",
    "leitura_entregue", "leitura_falha", "oferta_clique", "contato_enviado", "saida",
}

RE_ID = re.compile(r"^[A-Za-z0-9-]{8,64}$")

MAX_EVENTOS_POR_LOTE = 20
MAX_PROPS_CHARS = 1000
MAX_EVENTOS_POR_SESSAO = 300

RE_BOT = re.compile(
    r"bot|crawl|spider|preview|facebookexternalhit|whatsapp|telegram|slackbot|"
    r"discordbot|bingbot|googlebot|yandex|baidu|python-requests|curl|wget|"
    r"headlesschrome|lighthouse|pingdom|monitor",
    re.I,
)

_por_sessao: dict[str, int] = defaultdict(int)
_por_ip: dict[str, deque] = defaultdict(deque)


def e_bot(user_agent: str) -> bool:
    return bool(user_agent and RE_BOT.search(user_agent))


def dispositivo(user_agent: str) -> str:
    """Só a família, nunca a UA crua."""
    ua = (user_agent or "").lower()
    if any(x in ua for x in ("iphone", "android", "ipad", "mobile")):
        return "movel"
    return "desktop"


def limite_ok(sid: str, ip: str) -> bool:
    agora = time.time()
    _por_sessao[sid] += 1
    if _por_sessao[sid] > MAX_EVENTOS_POR_SESSAO:
        return False
    janela = _por_ip[ip]
    while janela and agora - janela[0] > 60:
        janela.popleft()
    if len(janela) >= 120:
        return False
    janela.append(agora)
    return True


def _arquivo(d: date) -> Path:
    return DIR_EVENTOS / f"{d:%Y-%m-%d}.jsonl"


def gravar(linhas: list[dict]) -> int:
    """Anexa as linhas ao arquivo de hoje. Nunca levanta.

    O OneDrive trava o arquivo durante a sincronização e o Windows devolve
    PermissionError. Uma retentativa curta resolve a maioria dos casos; sem ela,
    o evento some em silêncio.
    """
    if not linhas:
        return 0
    caminho = _arquivo(hoje_bsb())
    blob = "".join(json.dumps(l, ensure_ascii=False) + "\n" for l in linhas)
    for tentativa in range(3):
        try:
            with _LOCK:
                with open(caminho, "a", encoding="utf-8", newline="\n") as f:
                    f.write(blob)
            return len(linhas)
        except PermissionError:
            time.sleep(0.05 * (tentativa + 1))
        except Exception as e:
            logger.warning("falha ao gravar eventos: %s", e)
            return 0
    logger.warning("arquivo de eventos travado (OneDrive?): %d eventos descartados",
                   len(linhas))
    return 0


def normalizar(lote: dict, ip: str, user_agent: str) -> list[dict]:
    """Valida e carimba. Devolve as linhas prontas, descartando o que não presta.

    O carimbo de tempo oficial é o do SERVIDOR: o relógio do navegador pode estar
    errado, e a linha do tempo do painel não pode depender dele.
    """
    sid = str(lote.get("sid") or "")
    aid = str(lote.get("aid") or "")
    if not RE_ID.match(sid) or not RE_ID.match(aid):
        return []
    if not limite_ok(sid, ip):
        return []

    agora = datetime.now(FUSO_BSB)
    bot = e_bot(user_agent)
    disp = dispositivo(user_agent)
    teste = bool(lote.get("teste"))

    saida: list[dict] = []
    for ev in (lote.get("eventos") or [])[:MAX_EVENTOS_POR_LOTE]:
        if not isinstance(ev, dict):
            continue
        nome = ev.get("evt")
        if nome not in EVENTOS_VALIDOS:
            continue
        props = ev.get("props")
        if not isinstance(props, dict):
            props = {}
        if len(json.dumps(props, ensure_ascii=False)) > MAX_PROPS_CHARS:
            props = {"_truncado": True}
        try:
            seq = int(ev.get("seq", 0))
        except (TypeError, ValueError):
            continue
        saida.append({
            "v": VERSAO,
            "ts": agora.isoformat(timespec="seconds"),
            "ts_cli": ev.get("ts_cli"),
            "seq": seq,
            "sid": sid,
            "aid": aid,
            "evt": nome,
            "props": props,
            "disp": disp,
            "bot": bot,
            "teste": teste,
        })
    return saida


def registrar_servidor(sid: str, evt: str, props: dict) -> None:
    """Eventos emitidos pelo próprio servidor, que sabe mais que o navegador."""
    if not sid or not RE_ID.match(str(sid)):
        sid = "servidor-sem-sessao"
    gravar([{
        "v": VERSAO,
        "ts": datetime.now(FUSO_BSB).isoformat(timespec="seconds"),
        "ts_cli": None,
        "seq": -1,                 # -1 = servidor; nunca colide com o cliente
        "sid": str(sid),
        "aid": "",
        "evt": evt,
        "props": props,
        "disp": "servidor",
        "bot": False,
        "teste": False,
    }])


def ler_dias(inicio: date, fim: date) -> Iterator[dict]:
    """Percorre os arquivos do período, pulando linha corrompida sem levantar.

    Uma linha meio escrita por queda de energia no meio do append não pode
    derrubar o painel inteiro.
    """
    ruins = 0
    d = inicio
    while d <= fim:
        caminho = _arquivo(d)
        if caminho.exists():
            try:
                with open(caminho, encoding="utf-8") as f:
                    for linha in f:
                        linha = linha.strip()
                        if not linha:
                            continue
                        try:
                            yield json.loads(linha)
                        except Exception:
                            ruins += 1
            except Exception as e:
                logger.warning("falha ao ler %s: %s", caminho.name, e)
        d += timedelta(days=1)
    if ruins:
        logger.warning("%d linhas de evento ilegiveis foram puladas", ruins)


def limpar_antigos() -> int:
    """Retenção. Política que ninguém roda não é política, então roda no startup."""
    if EVENTOS_RETENCAO_DIAS <= 0:
        return 0
    limite = hoje_bsb() - timedelta(days=EVENTOS_RETENCAO_DIAS)
    apagados = 0
    for arq in DIR_EVENTOS.glob("*.jsonl"):
        try:
            d = datetime.strptime(arq.stem, "%Y-%m-%d").date()
        except ValueError:
            continue
        if d < limite:
            try:
                arq.unlink()
                apagados += 1
            except Exception as e:
                logger.warning("nao consegui apagar %s: %s", arq.name, e)
    if apagados:
        logger.info("retencao: %d arquivos de evento apagados", apagados)
    return apagados
