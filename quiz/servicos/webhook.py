# -*- coding: utf-8 -*-
"""Disparo de webhook para ZapVoice / Hotmart com os dados da leitura gerada."""
from __future__ import annotations

import asyncio
import json
import logging
import re
import threading
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from typing import Optional

from config import WEBHOOK_HOTMART_URL, WEBHOOK_DELAY_SEGUNDOS

logger = logging.getLogger("bussola.webhook")
FUSO_BRASILIA = timezone(timedelta(hours=-3))

_LOCK_AGENDAMENTOS = threading.Lock()
_AGENDAMENTOS: dict[str, dict] = {}


def formatar_mensagem(nome: str, carta: dict) -> str:
    """Formata a mensagem completa da leitura para envio no WhatsApp."""
    partes = []
    primeiro_nome = (nome or "").strip().split()[0] if (nome or "").strip() else ""
    if primeiro_nome:
        partes.append(f"Olá, {primeiro_nome}! Aqui está a sua leitura da Bússola Astrológica:")
    else:
        partes.append("Aqui está a sua leitura da Bússola Astrológica:")

    if carta.get("selo"):
        partes.append(f"✦ {carta['selo']}")

    if carta.get("titulo"):
        partes.append(f"*{str(carta['titulo']).upper()}*")

    if carta.get("destaque"):
        partes.append(f"_{carta['destaque']}_")

    # A carta vem em duas partes. Se vier so no formato antigo - ou pela carta
    # de reserva -, `paragrafos` continua sendo a saida e nada aqui quebra.
    ident = carta.get("identificacao") or {}
    porta = carta.get("porta") or {}
    tem_partes = bool(ident.get("paragrafos") or porta.get("paragrafos"))

    if tem_partes:
        if ident.get("selo"):
            partes.append(f"✦ {ident['selo']}")
        if ident.get("abertura"):
            partes.append(f"*{ident['abertura']}*")
        partes.extend(ident.get("paragrafos") or [])

        if porta.get("selo"):
            partes.append(f"✦ A PORTA ABERTA AGORA\n{porta['selo']}")
        if porta.get("abertura"):
            partes.append(f"*{porta['abertura']}*")
        partes.extend(porta.get("paragrafos") or [])
        if porta.get("aproveitar"):
            partes.append("\n".join(f"• {x}" for x in porta["aproveitar"]))
        if porta.get("cuidado"):
            partes.append(f"⚠️ {porta['cuidado']}")
    elif carta.get("paragrafos") and isinstance(carta["paragrafos"], list):
        partes.extend(carta["paragrafos"])

    espera = carta.get("espera") or ""
    janela = carta.get("janela") or ""
    espera_janela = f"{espera} {janela}".strip()
    if espera_janela:
        partes.append(f"⏳ {espera_janela}")

    return "\n\n".join(partes)


def disparar_webhook_leitura(
    nome_completo: str,
    whatsapp: str,
    carta: dict,
    leitura_id: str = "",
    meta: Optional[dict] = None,
    url: Optional[str] = None,
    estrelas: Optional[int] = None,
    pulou: bool = False,
) -> bool:
    """Dispara webhook POST para a URL configurada com nome, numero, mensagem e estrelas."""
    destino = WEBHOOK_HOTMART_URL if url is None else url
    if not destino:
        logger.warning("Webhook não configurado; pulando disparo.")
        return False

    agora_brasilia = datetime.now(FUSO_BRASILIA)
    data_hora_fmt = agora_brasilia.strftime("%d/%m/%Y, %H:%M:%S")

    clean_digits = re.sub(r"\D", "", whatsapp or "")
    mensagem_formatada = formatar_mensagem(nome_completo, carta)

    # Se não foram passadas estrelas diretamente, tenta ler do arquivo da leitura caso já exista
    if leitura_id and (estrelas is None and not pulou):
        try:
            from config import DIR_LEITURAS
            arq_leitura = DIR_LEITURAS / f"{leitura_id}.json"
            if arq_leitura.exists():
                d_disco = json.loads(arq_leitura.read_text(encoding="utf-8"))
                if d_disco.get("feedback_estrelas") is not None:
                    estrelas = d_disco.get("feedback_estrelas")
                if d_disco.get("feedback_pulou"):
                    pulou = True
        except Exception:
            pass

    meta_dados = meta or {}
    nascimento = meta_dados.get("nascimento") or {}
    cidade = meta_dados.get("cidade") or {}
    quiz = meta_dados.get("quiz") or {}

    payload = {
        "event": "PURCHASE_OUT_OF_SHOPPING_CART",
        "tipo": "leitura_concluida",
        "origem": "quiz_bussola",
        "leitura_id": leitura_id,
        "data_hora_brasilia": data_hora_fmt,
        # Dados do usuário preenchidos:
        "nome_completo": nome_completo,
        "nome": nome_completo,
        "name": nome_completo,
        "numero": whatsapp,
        "whatsapp": whatsapp,
        "telefone": whatsapp,
        "phone": clean_digits or whatsapp,
        "nascimento": nascimento,
        "cidade": cidade,
        "quiz": quiz,
        # Avaliação / Estrelas informadas pelo usuário:
        "feedback_estrelas": estrelas,
        "estrelas": estrelas,
        "stars": estrelas,
        "nota": estrelas,
        "feedback_pulou": pulou,
        "pulou": pulou,
        "pulou_avaliacao": pulou,
        # Leitura e mensagem secreta completa:
        "mensagem": mensagem_formatada,
        "message": mensagem_formatada,
        "texto": mensagem_formatada,
        "carta": carta,
        "data": {
            "product": {
                "name": "Bússola Astrológica",
            },
            "buyer": {
                "name": nome_completo,
                "phone": whatsapp,
                "checkout_phone": clean_digits,
            },
            "purchase": {
                "order_date": int(agora_brasilia.timestamp() * 1000),
                "order_date_brasilia": data_hora_fmt,
            },
            "reading": {
                "leitura_id": leitura_id,
                "mensagem": mensagem_formatada,
                "titulo": carta.get("titulo", ""),
                "destaque": carta.get("destaque", ""),
                "estrelas": estrelas,
                "feedback_estrelas": estrelas,
                "feedback_pulou": pulou,
                **meta_dados,
            },
            "custom_fields": {
                "nome_completo": nome_completo,
                "numero": whatsapp,
                "mensagem": mensagem_formatada,
                "leitura_id": leitura_id,
                "nascimento": nascimento,
                "cidade": cidade,
                "quiz": quiz,
                "estrelas": estrelas if estrelas is not None else "",
                "feedback_estrelas": estrelas if estrelas is not None else "",
                "stars": estrelas if estrelas is not None else "",
                "nota": estrelas if estrelas is not None else "",
                "feedback_pulou": "Sim" if pulou else "Não",
                "pulou": "Sim" if pulou else "Não",
            },
        },
    }

    try:
        corpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            destino,
            data=corpo,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": "BussolaQuiz/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as res:
            codigo = res.getcode()
            resposta_texto = res.read().decode("utf-8", errors="replace")
            logger.info("Webhook disparado com sucesso (%s) para %s (estrelas=%s, pulou=%s): %s",
                        codigo, destino, estrelas, pulou, resposta_texto[:200])

            # Registra no arquivo da leitura que o webhook já foi disparado
            if 200 <= codigo < 300 and leitura_id:
                try:
                    from config import DIR_LEITURAS
                    arq_lead = DIR_LEITURAS / f"{leitura_id}.json"
                    if arq_lead.exists():
                        d_lead = json.loads(arq_lead.read_text(encoding="utf-8"))
                        d_lead["webhook_disparado"] = True
                        d_lead["webhook_disparado_em"] = agora_brasilia.isoformat()
                        arq_lead.write_text(json.dumps(d_lead, ensure_ascii=False, indent=1), encoding="utf-8")
                except Exception:
                    pass

            return 200 <= codigo < 300
    except urllib.error.HTTPError as e:
        corpo_erro = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
        logger.warning("Erro HTTP ao disparar webhook (%s): %s | %s", e.code, e.reason, corpo_erro[:200])
        return False
    except Exception as e:
        logger.error("Falha ao disparar webhook para %s: %s", destino, e)
        return False


def agendar_webhook_leitura(
    leitura_id: str,
    nome_completo: str,
    whatsapp: str,
    carta: dict,
    meta: Optional[dict] = None,
    delay_segundos: Optional[float] = None,
) -> bool:
    """Inicia contagem regressiva (padrão: 5 minutos / 300s) para envio ao ZapVoice/zapjords.

    Se o usuário preencher ou pular a nota antes dos 5 minutos, a contagem é desconsiderada
    e o webhook é enviado imediatamente via notificar_feedback_leitura().
    Caso o usuário permaneça apenas na tela da mensagem e não avalie, ao término dos 5 min
    as informações são enviadas automaticamente.
    """
    if not whatsapp or not leitura_id:
        return False

    tempo_espera = float(delay_segundos if delay_segundos is not None else WEBHOOK_DELAY_SEGUNDOS)
    cancelar_agendamento(leitura_id)

    async def _timer_worker():
        try:
            await asyncio.sleep(tempo_espera)
        except asyncio.CancelledError:
            return

        with _LOCK_AGENDAMENTOS:
            item = _AGENDAMENTOS.pop(leitura_id, None)
        if not item or item.get("disparado"):
            return
        item["disparado"] = True

        # Verifica se alguma nota chegou ao arquivo em disco antes de disparar
        estrelas = item.get("estrelas")
        pulou = item.get("pulou", False)
        try:
            from config import DIR_LEITURAS
            arq = DIR_LEITURAS / f"{leitura_id}.json"
            if arq.exists():
                d_l = json.loads(arq.read_text(encoding="utf-8"))
                if estrelas is None:
                    estrelas = d_l.get("feedback_estrelas")
                if not pulou:
                    pulou = bool(d_l.get("feedback_pulou"))
        except Exception:
            pass

        logger.info("Cronômetro de %ss expirou para leitura %s. Enviando webhook ao ZapVoice.", tempo_espera, leitura_id)
        threading.Thread(
            target=disparar_webhook_leitura,
            kwargs=dict(
                nome_completo=item["nome_completo"],
                whatsapp=item["whatsapp"],
                carta=item["carta"],
                leitura_id=leitura_id,
                meta=item.get("meta"),
                estrelas=estrelas,
                pulou=pulou,
            ),
            daemon=True,
        ).start()

    task = None
    timer = None
    try:
        loop = asyncio.get_running_loop()
        task = loop.create_task(_timer_worker())
    except RuntimeError:
        # Modo síncrono / sem event loop rodando na thread atual
        def _sync_worker():
            with _LOCK_AGENDAMENTOS:
                item = _AGENDAMENTOS.pop(leitura_id, None)
            if not item or item.get("disparado"):
                return
            item["disparado"] = True
            disparar_webhook_leitura(
                nome_completo=nome_completo,
                whatsapp=whatsapp,
                carta=carta,
                leitura_id=leitura_id,
                meta=meta,
            )
        timer = threading.Timer(tempo_espera, _sync_worker)
        timer.daemon = True
        timer.start()

    with _LOCK_AGENDAMENTOS:
        _AGENDAMENTOS[leitura_id] = {
            "nome_completo": nome_completo,
            "whatsapp": whatsapp,
            "carta": carta,
            "meta": meta or {},
            "estrelas": None,
            "pulou": False,
            "disparado": False,
            "task": task,
            "timer": timer,
        }
    logger.info("Cronômetro de 5min iniciado para leitura %s (espera de %ss).", leitura_id, tempo_espera)
    return True


def notificar_feedback_leitura(
    leitura_id: str,
    estrelas: Optional[int] = None,
    pulou: bool = False,
) -> bool:
    """Cancela o cronômetro de 5 minutos e envia o webhook imediatamente com as estrelas."""
    if not leitura_id:
        return False

    with _LOCK_AGENDAMENTOS:
        item = _AGENDAMENTOS.pop(leitura_id, None)

    if item:
        task = item.get("task")
        if task and not task.done():
            task.cancel()
        timer = item.get("timer")
        if timer and timer.is_alive():
            timer.cancel()

        if item.get("disparado"):
            return False

        item["disparado"] = True
        logger.info("Avaliação recebida para %s (estrelas=%s, pulou=%s). Cancelando cronômetro e disparando webhook.",
                    leitura_id, estrelas, pulou)

        threading.Thread(
            target=disparar_webhook_leitura,
            kwargs=dict(
                nome_completo=item["nome_completo"],
                whatsapp=item["whatsapp"],
                carta=item["carta"],
                leitura_id=leitura_id,
                meta=item.get("meta"),
                estrelas=estrelas,
                pulou=pulou,
            ),
            daemon=True,
        ).start()
        return True
    else:
        # Se não estava em memória, tenta recuperar do disco se ainda não tiver disparado
        try:
            from config import DIR_LEITURAS
            arq = DIR_LEITURAS / f"{leitura_id}.json"
            if arq.exists():
                d_l = json.loads(arq.read_text(encoding="utf-8"))
                wa = d_l.get("whatsapp")
                if wa and not d_l.get("webhook_disparado"):
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(asyncio.to_thread(
                            disparar_webhook_leitura,
                            nome_completo=d_l.get("nome_completo", ""),
                            whatsapp=wa,
                            carta=d_l.get("carta", {}),
                            leitura_id=leitura_id,
                            meta={
                                "nascimento": d_l.get("nascimento"),
                                "cidade": d_l.get("cidade"),
                                "quiz": d_l.get("quiz"),
                            },
                            estrelas=estrelas,
                            pulou=pulou,
                        ))
                    except RuntimeError:
                        disparar_webhook_leitura(
                            nome_completo=d_l.get("nome_completo", ""),
                            whatsapp=wa,
                            carta=d_l.get("carta", {}),
                            leitura_id=leitura_id,
                            meta={
                                "nascimento": d_l.get("nascimento"),
                                "cidade": d_l.get("cidade"),
                                "quiz": d_l.get("quiz"),
                            },
                            estrelas=estrelas,
                            pulou=pulou,
                        )
                    return True
        except Exception as e:
            logger.warning("Falha ao recuperar leitura %s no feedback: %s", leitura_id, e)
        return False


def cancelar_agendamento(leitura_id: str) -> bool:
    """Cancela o cronômetro pendente de uma leitura."""
    with _LOCK_AGENDAMENTOS:
        item = _AGENDAMENTOS.pop(leitura_id, None)
    if item:
        task = item.get("task")
        if task and not task.done():
            task.cancel()
        timer = item.get("timer")
        if timer and timer.is_alive():
            timer.cancel()
        return True
    return False


def obter_agendamento(leitura_id: str) -> Optional[dict]:
    """Retorna os dados do agendamento pendente se houver (para testes/inspeção)."""
    with _LOCK_AGENDAMENTOS:
        return _AGENDAMENTOS.get(leitura_id)


def disparar_webhook_vsl_play(
    nome: str = "",
    whatsapp: str = "",
    video_id: str = "",
    video_tipo: str = "oferta",
    leitura_id: str = "",
    url: Optional[str] = None,
) -> bool:
    """Dispara webhook POST para a ferramenta de gerenciamento de VSL quando o visitante aperta o play."""
    destino = url
    if not destino:
        try:
            from servicos.config_oferta import obter_config_oferta
            cfg = obter_config_oferta()
            destino = cfg.get("webhook_vsl_play_url", "").strip()
        except Exception:
            destino = ""
    if not destino:
        import config
        destino = getattr(config, "WEBHOOK_VSL_PLAY_URL", "").strip()

    if not destino:
        logger.info("Webhook de VSL Play não configurado; pulando disparo.")
        return False

    agora_brasilia = datetime.now(FUSO_BRASILIA)
    data_hora_fmt = agora_brasilia.strftime("%d/%m/%Y, %H:%M:%S")
    clean_digits = re.sub(r"\D", "", whatsapp or "")

    # Se nome ou whatsapp não vieram diretamente, tenta buscar no arquivo da leitura
    if leitura_id and (not nome or not whatsapp):
        try:
            from config import DIR_LEITURAS
            arq = DIR_LEITURAS / f"{leitura_id}.json"
            if arq.exists():
                d_l = json.loads(arq.read_text(encoding="utf-8"))
                if not nome:
                    nome = d_l.get("nome_completo", "")
                if not whatsapp:
                    whatsapp = d_l.get("whatsapp", "")
                    clean_digits = re.sub(r"\D", "", whatsapp or "")
        except Exception:
            pass

    payload = {
        "event": "vsl_play",
        "video_id": video_id,
        "video_tipo": video_tipo,
        "name": nome,
        "nome_completo": nome,
        "nome": nome,
        "phone": clean_digits or whatsapp,
        "numero": whatsapp,
        "whatsapp": whatsapp,
        "telefone": whatsapp,
        "lead_id": leitura_id,
        "leitura_id": leitura_id,
        "data_hora_brasilia": data_hora_fmt,
        "timestamp": int(agora_brasilia.timestamp() * 1000),
        "data": {
            "lead": {
                "name": nome,
                "phone": whatsapp,
                "clean_phone": clean_digits,
                "lead_id": leitura_id,
            },
            "video": {
                "video_id": video_id,
                "tipo": video_tipo,
            },
            "occurred_at": agora_brasilia.isoformat(),
        },
    }

    try:
        corpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            destino,
            data=corpo,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": "BussolaQuiz/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=6) as res:
            codigo = res.getcode()
            logger.info("Webhook VSL Play disparado com sucesso (%s) para %s (video_id=%s, lead=%s)",
                        codigo, destino, video_id, nome)

            if 200 <= codigo < 300 and leitura_id:
                try:
                    from config import DIR_LEITURAS
                    arq_lead = DIR_LEITURAS / f"{leitura_id}.json"
                    if arq_lead.exists():
                        d_lead = json.loads(arq_lead.read_text(encoding="utf-8"))
                        d_lead["vsl_play"] = True
                        d_lead["vsl_play_em"] = agora_brasilia.isoformat()
                        d_lead["vsl_play_video_id"] = video_id
                        arq_lead.write_text(json.dumps(d_lead, ensure_ascii=False, indent=1), encoding="utf-8")
                except Exception:
                    pass

            return 200 <= codigo < 300
    except Exception as e:
        logger.warning("Falha ao disparar webhook VSL Play para %s: %s", destino, e)
        return False

