# -*- coding: utf-8 -*-
"""Cache e registro de leads.

Cache: a porta muda devagar, então leituras com a mesma casa, mesmo aspecto
principal e mesma semana podem ser reaproveitadas. A chave inclui a área e o
índice da frase do espelho, senão duas pessoas com o mesmo trânsito receberiam
literalmente o mesmo texto. O nome nunca entra no corpo cacheado, só na
renderização.

Registro: o lead é gravado no instante em que a leitura é gerada, antes de
qualquer tela de oferta. Quem abandonar no meio continua registrado.
"""
from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import date, datetime
from typing import Optional

from config import DIR_CACHE, DIR_LEITURAS
from .pesos import PESOS_V

logger = logging.getLogger(__name__)


def chave_cache(veredito, fatos: dict, quiz: dict, hoje: date) -> str:
    ap = fatos.get("aspecto_principal") or {}
    semana = hoje.isocalendar()
    bruto = "|".join(str(x) for x in [
        PESOS_V, semana[0], semana[1],
        veredito.cenario, veredito.casa_aberta, veredito.casa_fechada,
        ap.get("transito"), ap.get("natal"), ap.get("aspecto"), ap.get("movimento"),
        round(float(ap.get("orbe") or 0)),
        quiz.get("area"), quiz.get("espelho_idx"), quiz.get("quebra"),
        fatos["permitido"]["casas"] and 1 or 0,
    ])
    # Toda a entrada do escritor entra na chave: nenhum mapa pode receber
    # uma carta de outro mapa só porque compartilham o aspecto principal.
    from config import DIR_PROMPTS, MODELOS
    contexto = {"versao": bruto, "fatos": fatos, "quiz": {
        k: v for k, v in quiz.items() if k != "primeiro_nome"},
        "prompt": (DIR_PROMPTS / "carta.txt").read_text(encoding="utf-8"),
        "modelos": MODELOS, "dia": hoje.isoformat()}
    return hashlib.sha256(json.dumps(contexto, ensure_ascii=False,
                                    sort_keys=True).encode("utf-8")).hexdigest()


def ler_cache(chave: str) -> Optional[dict]:
    caminho = DIR_CACHE / f"{chave}.json"
    if not caminho.exists():
        return None
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("cache ilegivel em %s: %s", caminho.name, e)
        return None


def gravar_cache(chave: str, carta: dict) -> None:
    try:
        (DIR_CACHE / f"{chave}.json").write_text(
            json.dumps(carta, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception as e:
        logger.warning("falha ao gravar cache: %s", e)


def novo_id() -> str:
    from datetime import timezone
    return f"{datetime.now(timezone.utc):%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:8]}"


def gravar_lead(leitura_id: str, dados: dict) -> None:
    """Nome completo, nascimento, respostas, veredito e a carta inteira.

    Sem banco nesta fase: um JSON por leitura basta para não perder contato de
    quem completou o percurso.
    """
    try:
        from datetime import timezone, timedelta
        import pytz
        agora_utc = datetime.now(timezone.utc)
        tz_bsb = pytz.timezone("America/Sao_Paulo")
        agora_bsb = agora_utc.astimezone(tz_bsb)
        tempo_quiz_ms = dados.get("tempo_quiz_ms") or 0
        chegou_bsb = (agora_utc - timedelta(milliseconds=tempo_quiz_ms)).astimezone(tz_bsb)

        dados = dict(
            dados,
            gravado_em=agora_utc.isoformat(timespec="seconds"),
            gravado_em_bsb=agora_bsb.strftime("%d/%m/%Y %H:%M:%S"),
            chegou_em_bsb=chegou_bsb.strftime("%d/%m/%Y %H:%M:%S"),
            pesos_v=PESOS_V,
        )
        (DIR_LEITURAS / f"{leitura_id}.json").write_text(
            json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception as e:
        logger.error("FALHA AO GRAVAR LEAD %s: %s", leitura_id, e)


def anexar_contato(leitura_id: str, whatsapp: str) -> bool:
    import re
    if not re.fullmatch(r"\d{8}-\d{6}-[a-f0-9]{8}", leitura_id):
        return False
    """O WhatsApp chega depois, no fim da carta. Enriquece o lead já gravado."""
    caminho = DIR_LEITURAS / f"{leitura_id}.json"
    if not caminho.exists():
        return False
    try:
        d = json.loads(caminho.read_text(encoding="utf-8"))
        d["whatsapp"] = whatsapp
        d["whatsapp_em"] = datetime.now().isoformat(timespec="seconds")
        caminho.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        return True
    except Exception as e:
        logger.error("falha ao anexar contato em %s: %s", leitura_id, e)
        return False
