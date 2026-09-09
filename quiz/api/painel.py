# -*- coding: utf-8 -*-
"""GET /painel — o funil em números.

Protegido por senha porque concentra dado pessoal. A lista de leituras vem
MASCARADA por padrão: o pior cenário concreto não é invasão, é uma captura de
tela ou um olhar por cima do ombro sobre duzentos nomes completos com data de
nascimento e telefone.
"""
from __future__ import annotations

import csv
import html
import io
import json
import logging
import re
import secrets
import time
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import pytz

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials

import config
from servicos import eventos, registro
from servicos.agregador import MIN_PARA_PORCENTAGEM, agregar
from servicos.tempo_real import rastreador_presenca, ws_manager, ETAPAS_ROTULOS

router = APIRouter()
logger = logging.getLogger(__name__)
seguranca = HTTPBasic(auto_error=False)

_TOKENS_WS: set[str] = set()


def gerar_token_ws() -> str:
    token = secrets.token_urlsafe(24)
    _TOKENS_WS.add(token)
    if len(_TOKENS_WS) > 300:
        chaves = list(_TOKENS_WS)[:100]
        for k in chaves:
            _TOKENS_WS.discard(k)
    return token


def validar_token_ws(token: str) -> bool:
    return bool(token and token in _TOKENS_WS)


@router.websocket("/painel/ws")
async def ws_painel(websocket: WebSocket, token: Optional[str] = None):
    autorizado = False
    if token and validar_token_ws(token):
        autorizado = True
    else:
        auth_h = websocket.headers.get("authorization", "")
        if auth_h.startswith("Basic "):
            try:
                import base64
                u, p = base64.b64decode(auth_h[6:]).decode("utf-8").split(":", 1)
                if secrets.compare_digest(u, config.PAINEL_USUARIO) and secrets.compare_digest(p, config.PAINEL_SENHA):
                    autorizado = True
            except Exception:
                pass

    if not autorizado:
        await websocket.close(code=1008, reason="Não autorizado")
        return

    await ws_manager.conectar(websocket)
    try:
        ativos = rastreador_presenca.obter_ativos(90.0)
        await websocket.send_json({
            "tipo": "snapshot",
            "ao_vivo": ativos,
            "total_ao_vivo": len(ativos)
        })
        while True:
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning("Erro na conexão WebSocket do painel: %s", e)
    finally:
        await ws_manager.desconectar(websocket)


CABECALHOS = {"Cache-Control": "no-store, no-cache, must-revalidate",
              "X-Robots-Tag": "noindex, nofollow", "Referrer-Policy": "no-referrer"}


def exigir_senha(cred: Optional[HTTPBasicCredentials] = Depends(seguranca)) -> str:
    if not config.PAINEL_SENHA:
        raise HTTPException(503, "PAINEL_SENHA não definida no .env")
    if cred is None:
        raise HTTPException(401, "autenticação necessária",
                            headers={"WWW-Authenticate": "Basic"})
    ok_u = secrets.compare_digest(cred.username, config.PAINEL_USUARIO)
    ok_s = secrets.compare_digest(cred.password, config.PAINEL_SENHA)
    if not (ok_u and ok_s):
        time.sleep(0.3)          # atrito contra tentativa em rajada
        raise HTTPException(401, "senha incorreta",
                            headers={"WWW-Authenticate": "Basic"})
    return cred.username


# ---------------------------------------------------------------- mascaramento
def m_nome(n: str) -> str:
    partes = (n or "").split()
    if not partes:
        return "?"
    p = partes[0]
    resto = " ".join(x[0] + "." for x in partes[1:])
    return f"{p[:3]}{'*' * max(0, len(p) - 3)} {resto}".strip()


def m_data(nasc: dict) -> str:
    return f"{nasc.get('dia','?'):0>2}/{nasc.get('mes','?'):0>2}/19XX"


def m_fone(f: str) -> str:
    d = re.sub(r"\D", "", f or "")
    return f"…{d[-4:]}" if len(d) >= 4 else "—"


def f_data(nasc: dict) -> str:
    """Data de nascimento com dia, mês e ano de 2 dígitos (ex.: 09/03/98)."""
    if not nasc:
        return "—"
    dia = nasc.get("dia")
    mes = nasc.get("mes")
    ano = str(nasc.get("ano") or "")
    if dia is None or mes is None or not ano:
        return "—"
    ano_2d = ano[-2:] if len(ano) >= 2 else ano
    try:
        return f"{int(dia):0>2}/{int(mes):0>2}/{ano_2d}"
    except (ValueError, TypeError):
        return f"{dia}/{mes}/{ano_2d}"


def f_hora(nasc: dict, pr: Optional[dict] = None) -> str:
    """Horário e minuto de nascimento (ex.: 18h35), ou período/modo quando não houver hora exata."""
    if not nasc:
        return html.escape(str((pr or {}).get("modo_hora") or "—"))
    hora = nasc.get("hora")
    if hora is not None:
        minuto = nasc.get("minuto") or 0
        return f"{int(hora):0>2}h{int(minuto):0>2}"
    modo = nasc.get("periodo") or (pr or {}).get("modo_hora") or "desconhecida"
    return html.escape(str(modo))


def f_tempo(ms: Optional[float]) -> str:
    """Formata milissegundos em duração legível: ex.: 5s, 42s, 1m 15s."""
    if ms is None or ms < 0:
        return "—"
    seg = round(ms / 1000)
    if seg < 60:
        return f"{seg}s"
    m = seg // 60
    s = seg % 60
    return f"{m}m {s:0>2}s" if s else f"{m}m"


def f_wa(w: Optional[str]) -> str:
    """Formata número de WhatsApp com link direto wa.me se disponível."""
    if not w or w.strip() in ("", "—", "-"):
        return "—"
    w_str = w.strip()
    digitos = re.sub(r"\D", "", w_str)
    if len(digitos) >= 8:
        link_digitos = f"55{digitos}" if len(digitos) in (10, 11) and not w_str.startswith("+") else digitos
        return f'<a href="https://wa.me/{link_digitos}" target="_blank" rel="noopener" style="color:var(--green);text-decoration:underline;">{html.escape(w_str)}</a>'
    return html.escape(w_str)


FUSO_BSB = timezone(timedelta(hours=-3))
TZ_BRASILIA = FUSO_BSB


def hoje_bsb() -> date:
    """Retorna a data atual no horário oficial de Brasília (UTC-3)."""
    return datetime.now(FUSO_BSB).date()


def _formatar_data_hora_curta(val: datetime | str) -> str:
    """Formata datetime ou string existente para dd/mm/aa HH:MM (ano 2 dígitos, sem segundos)."""
    if isinstance(val, datetime):
        return val.strftime("%d/%m/%y %H:%M")
    if not val:
        return "—"
    s = str(val).strip()
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})\s+(\d{1,2}):(\d{1,2})(?::\d{1,2})?", s)
    if m:
        dia, mes, ano, hora, minuto = m.groups()
        ano_2d = ano[-2:] if len(ano) >= 2 else ano
        return f"{int(dia):0>2}/{int(mes):0>2}/{ano_2d} {int(hora):0>2}:{int(minuto):0>2}"
    try:
        dt = datetime.fromisoformat(s)
        return dt.strftime("%d/%m/%y %H:%M")
    except Exception:
        return s


def obter_datetimes_bsb(d: dict, arq_stem: str) -> tuple[Optional[datetime], Optional[datetime]]:
    """Calcula (dt_chegada_bsb, dt_gerada_bsb) no fuso de Brasília."""
    c_bsb = d.get("chegou_em_bsb")
    g_bsb = d.get("gravado_em_bsb")
    dt_c = None
    dt_g = None
    if c_bsb:
        if isinstance(c_bsb, datetime):
            dt_c = c_bsb
        else:
            s = str(c_bsb).strip()
            m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})\s+(\d{1,2}):(\d{1,2})(?::\d{1,2})?", s)
            if m:
                dia, mes, ano, hora, minuto = m.groups()
                ano_int = int(ano)
                if ano_int < 100:
                    ano_int += 2000
                try:
                    dt_c = datetime(ano_int, int(mes), int(dia), int(hora), int(minuto), tzinfo=TZ_BRASILIA)
                except Exception:
                    pass
            if not dt_c:
                try:
                    dt_c = datetime.fromisoformat(s)
                    if dt_c.tzinfo is None:
                        dt_c = dt_c.replace(tzinfo=TZ_BRASILIA)
                except Exception:
                    pass

    if g_bsb:
        if isinstance(g_bsb, datetime):
            dt_g = g_bsb
        else:
            s = str(g_bsb).strip()
            m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})\s+(\d{1,2}):(\d{1,2})(?::\d{1,2})?", s)
            if m:
                dia, mes, ano, hora, minuto = m.groups()
                ano_int = int(ano)
                if ano_int < 100:
                    ano_int += 2000
                try:
                    dt_g = datetime(ano_int, int(mes), int(dia), int(hora), int(minuto), tzinfo=TZ_BRASILIA)
                except Exception:
                    pass
            if not dt_g:
                try:
                    dt_g = datetime.fromisoformat(s)
                    if dt_g.tzinfo is None:
                        dt_g = dt_g.replace(tzinfo=TZ_BRASILIA)
                except Exception:
                    pass

    if dt_c and dt_g:
        return (dt_c, dt_g)

    dt_gerada_utc = None
    gravado_em = d.get("gravado_em")
    if gravado_em:
        try:
            dt_gerada_utc = datetime.fromisoformat(gravado_em)
            if dt_gerada_utc.tzinfo is None:
                dt_gerada_utc = dt_gerada_utc.replace(tzinfo=timezone.utc)
            else:
                dt_gerada_utc = dt_gerada_utc.astimezone(timezone.utc)
        except Exception:
            pass

    if not dt_gerada_utc and len(arq_stem) >= 15:
        try:
            dt_gerada_utc = datetime.strptime(arq_stem[:15], "%Y%m%d-%H%M%S").replace(tzinfo=timezone.utc)
        except Exception:
            pass

    if not dt_gerada_utc:
        dt_gerada_utc = datetime.now(timezone.utc)

    dt_gerada_bsb = dt_gerada_utc.astimezone(TZ_BRASILIA)
    tempo_quiz_ms = d.get("tempo_quiz_ms")
    if tempo_quiz_ms and tempo_quiz_ms > 0:
        dt_chegada_bsb = dt_gerada_bsb - timedelta(milliseconds=tempo_quiz_ms)
    else:
        dt_chegada_bsb = dt_gerada_bsb

    return (dt_c or dt_chegada_bsb, dt_g or dt_gerada_bsb)


def obter_data_chegada_leitura(d: dict, arq_stem: str) -> Optional[date]:
    """Retorna a data (date) em que o lead chegou ao quiz no horário de Brasília."""
    dt_c, _ = obter_datetimes_bsb(d, arq_stem)
    return dt_c.date() if dt_c else None


def f_chegada_bsb(d: dict, arq_stem: str) -> tuple[str, str]:
    """Retorna (chegou_em_bsb, gerado_em_bsb) formatados no horário de Brasília (UTC-3) como dd/mm/aa HH:MM."""
    if d.get("chegou_em_bsb") and d.get("gravado_em_bsb"):
        return (
            _formatar_data_hora_curta(d["chegou_em_bsb"]),
            _formatar_data_hora_curta(d["gravado_em_bsb"])
        )

    dt_c, dt_g = obter_datetimes_bsb(d, arq_stem)
    return (
        dt_c.strftime("%d/%m/%y %H:%M") if dt_c else "—",
        dt_g.strftime("%d/%m/%y %H:%M") if dt_g else "—"
    )


# --------------------------------------------------------------------- helpers
def _periodo(de: Optional[str], ate: Optional[str], dias: int = 7) -> tuple[date, date]:
    hoje = hoje_bsb()
    try:
        d1 = date.fromisoformat(de) if de else hoje - timedelta(days=dias - 1)
        d2 = date.fromisoformat(ate) if ate else hoje
    except ValueError:
        d1, d2 = hoje - timedelta(days=dias - 1), hoje
    return (d1, d2) if d1 <= d2 else (d2, d1)


def _n(v) -> str:
    return "—" if v is None else f"{v}%"


def _barra(v: Optional[float]) -> str:
    largura = 0 if v is None else max(1, min(100, v))
    return f'<i style="width:{largura}%"></i>'


ESTILO = """
:root{--bg:#131313;--card:#1B1917;--line:#332E27;--sand:#F2EFE9;--sand2:rgba(242,239,233,.62);
--amber:#E5A93C;--red:#C4564A;--green:#4E9D6E}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--sand);
font:14px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;padding:26px 18px 70px}
.w{max-width:1000px;margin:0 auto}
h1{font-size:20px;margin:0 0 3px;letter-spacing:-.01em}
h2{font-size:13px;text-transform:uppercase;letter-spacing:.13em;color:var(--amber);
margin:34px 0 12px;font-weight:600}
.sub{color:var(--sand2);font-size:12.5px;margin:0 0 20px}
.filtros{display:flex;gap:7px;flex-wrap:wrap;margin:14px 0 10px;align-items:center}
.filtros a{padding:6px 12px;border:1px solid var(--line);border-radius:999px;
color:var(--sand2);text-decoration:none;font-size:12px;transition:all .15s ease}
.filtros a:hover{border-color:var(--amber);color:var(--amber);background:rgba(229,169,60,.08)}
.filtros a.on{border-color:var(--amber);color:var(--amber);background:rgba(229,169,60,.12);font-weight:700}
.form-filtro-datas{display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,.03);border:1px solid var(--line);border-radius:999px;padding:3px 10px;font-size:12px;margin-left:auto}
.form-filtro-datas .lbl-datas{color:var(--amber);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.05em}
.form-filtro-datas .lbl-campo{display:inline-flex;align-items:center;gap:4px;color:var(--sand2);font-size:11.5px}
.form-filtro-datas input[type="date"]{background:#1B1917;color:var(--sand);border:1px solid var(--line);border-radius:6px;padding:2px 6px;font-size:11.5px;font-family:inherit;color-scheme:dark;outline:none}
.form-filtro-datas input[type="date"]:focus{border-color:var(--amber)}
.btn-filtrar-datas{background:var(--amber);color:#131313;border:none;border-radius:999px;padding:3px 12px;font-size:11.5px;font-weight:700;cursor:pointer;transition:all .15s ease}
.btn-filtrar-datas:hover{background:#F6C467;transform:translateY(-1px)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));gap:10px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:13px 14px}
.card b{display:block;font-size:23px;line-height:1.15;font-weight:700}
.card span{display:block;font-size:11px;color:var(--sand2);margin-top:3px}
table{width:100%;border-collapse:collapse;background:var(--card);
border:1px solid var(--line);border-radius:12px;overflow:hidden}
th,td{padding:9px 12px;text-align:left;border-bottom:1px solid var(--line);font-size:13px}
th{font-size:10.5px;text-transform:uppercase;letter-spacing:.09em;color:var(--sand2);font-weight:600}
tr:last-child td{border-bottom:none}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.bar{position:relative;height:6px;background:#272320;border-radius:4px;overflow:hidden;min-width:70px}
.bar i{position:absolute;left:0;top:0;bottom:0;background:var(--amber);border-radius:4px}
.alerta{background:rgba(196,86,74,.12);border:1px solid rgba(196,86,74,.45);
border-radius:10px;padding:11px 13px;margin:10px 0;font-size:12.5px}
.nota{color:var(--sand2);font-size:11.5px;margin:8px 0 0;line-height:1.6}
a{color:var(--amber)}
.vazio{color:var(--sand2);padding:16px 0;font-size:13px}
.abas{display:flex;gap:8px;border-bottom:1px solid var(--line);margin:26px 0 20px;padding-bottom:1px;overflow-x:auto;-webkit-overflow-scrolling:touch}
.aba-btn{background:none;border:none;color:var(--sand2);font:inherit;font-size:13px;font-weight:600;padding:10px 18px;cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px;transition:all .15s ease;display:inline-flex;align-items:center;gap:7px;white-space:nowrap;border-radius:6px 6px 0 0;user-select:none;-webkit-user-select:none}
.aba-btn:hover{color:var(--sand);background:rgba(255,255,255,.03)}
.aba-btn.on{color:var(--amber);border-bottom-color:var(--amber);background:rgba(229,169,60,.08)}
.aba-painel{display:none !important}
.aba-painel.on{display:block !important;animation:fadein .2s ease}
.tbl-wrap{width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch;margin-bottom:12px;cursor:default}
#aba-leituras .tbl-wrap, .tbl-wrap-leituras{cursor:grab}
#aba-leituras .tbl-wrap:active, .tbl-wrap-leituras:active{cursor:grabbing}
#aba-leituras .tbl-wrap.arrastando, .tbl-wrap-leituras.arrastando{cursor:grabbing !important;user-select:none !important;-webkit-user-select:none !important}
#aba-leituras .tbl-wrap.arrastando *, .tbl-wrap-leituras.arrastando *{cursor:grabbing !important;user-select:none !important;-webkit-user-select:none !important}
.tbl-wrap a, .tbl-wrap button, .tbl-wrap input{cursor:pointer}
.paginacao{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin:16px 0 8px;padding:12px 0;border-top:1px solid var(--line)}
.pag-info{font-size:12.5px;color:var(--sand2)}
.pag-links{display:flex;align-items:center;gap:6px}
.pag-btn{display:inline-flex;align-items:center;justify-content:center;padding:6px 12px;border:1px solid var(--line);border-radius:6px;color:var(--sand);text-decoration:none;font-size:12px;min-width:32px;transition:all .15s ease}
.pag-btn:hover{border-color:var(--amber);color:var(--amber);background:rgba(229,169,60,.08)}
.pag-btn.on{border-color:var(--amber);background:var(--amber);color:#12100C;font-weight:700}
.pag-btn.disabled{opacity:.35;pointer-events:none;cursor:default;color:var(--sand2)}
.tag-etapa{display:inline-block;padding:2px 8px;border-radius:6px;font-size:11.5px;font-weight:600;background:rgba(229,169,60,.12);color:var(--amber);border:1px solid rgba(229,169,60,.3);white-space:nowrap}
.tag-etapa.oferta{background:rgba(229,169,60,.25);border-color:var(--amber);color:#F6C467}
.tag-checkout{display:inline-flex;align-items:center;justify-content:center;padding:2px 8px;border-radius:6px;font-size:11.5px;font-weight:700;white-space:nowrap}
.tag-checkout.sim{background:rgba(62,145,102,.22);color:#58B982;border:1px solid rgba(62,145,102,.5)}
.tag-checkout.nao{background:rgba(255,255,255,.04);color:var(--sand2);border:1px solid var(--line)}
.tag-rep{display:inline-block;padding:1px 6px;border-radius:4px;font-size:11px;font-weight:700;background:rgba(229,169,60,.18);color:var(--amber);border:1px solid rgba(229,169,60,.35);margin-left:6px;vertical-align:middle}
.filtros-leituras{display:flex;gap:8px;margin:12px 0 16px;flex-wrap:wrap;align-items:center}
.btn-filtro-leituras{display:inline-flex;align-items:center;gap:6px;padding:6px 14px;border:1px solid var(--line);border-radius:999px;color:var(--sand2);text-decoration:none;font-size:12px;font-weight:600;background:rgba(255,255,255,.02);cursor:pointer;transition:all .15s ease}
.btn-filtro-leituras:hover{border-color:var(--amber);color:var(--amber);background:rgba(229,169,60,.08)}
.btn-filtro-leituras.on{border-color:var(--amber);background:rgba(229,169,60,.12);color:var(--amber);font-weight:700}
.btn-filtro-leituras.chk:hover{border-color:var(--green);color:#58B982;background:rgba(78,157,110,.08)}
.btn-filtro-leituras.chk.on{border-color:var(--green);background:rgba(78,157,110,.18);color:#58B982;font-weight:700}
.btn-filtro-leituras .badge-count{display:inline-block;padding:1px 6px;border-radius:999px;font-size:11px;background:rgba(255,255,255,.06);margin-left:2px}
.btn-filtro-leituras.on .badge-count{background:rgba(229,169,60,.22);color:var(--amber)}
.btn-filtro-leituras.chk.on .badge-count{background:rgba(78,157,110,.25);color:#58B982}
.btn-del{background:rgba(196,86,74,.12);color:#E57373;border:1px solid rgba(196,86,74,.35);border-radius:6px;padding:3px 9px;font-size:11.5px;font-weight:600;cursor:pointer;transition:all .15s ease;display:inline-flex;align-items:center;gap:4px;white-space:nowrap}
.btn-del:hover{background:rgba(196,86,74,.3);border-color:#E57373;color:#FFF}
.btn-acordeao{background:rgba(229,169,60,.12);color:var(--amber);border:1px solid rgba(229,169,60,.35);border-radius:6px;padding:2px 7px;font-size:11px;font-weight:700;cursor:pointer;display:inline-flex;align-items:center;gap:5px;margin-left:6px;vertical-align:middle;transition:all .15s ease}
.btn-acordeao:hover{background:rgba(229,169,60,.22);border-color:var(--amber)}
.btn-acordeao.aberto{background:rgba(229,169,60,.28);border-color:var(--amber);color:#FFF}
.btn-acordeao .seta{display:inline-block;transition:transform .18s ease;font-size:8.5px}
.btn-acordeao.aberto .seta{transform:rotate(90deg)}
.tr-subleitura{background:rgba(255,255,255,.02);border-left:3px solid rgba(229,169,60,.4)}
.tr-subleitura td{padding:6px 12px;font-size:12px;color:var(--sand2);border-bottom:1px dashed rgba(255,255,255,.06)}
.modal-backdrop{position:fixed;inset:0;background:rgba(0,0,0,.78);backdrop-filter:blur(4px);z-index:99999;display:flex;align-items:center;justify-content:center;opacity:0;pointer-events:none;transition:opacity .2s ease}
.modal-backdrop.on{opacity:1;pointer-events:auto}
.modal-card{background:#1B1917;border:1px solid rgba(196,86,74,.5);border-radius:14px;padding:26px 24px;max-width:460px;width:90%;box-shadow:0 20px 45px rgba(0,0,0,.85);text-align:center;transform:translateY(10px) scale(.98);transition:transform .2s ease}
.modal-backdrop.on .modal-card{transform:translateY(0) scale(1)}
.modal-icone{font-size:36px;margin-bottom:12px;line-height:1}
.modal-titulo{font-size:18px;font-weight:700;color:var(--sand);margin:0 0 8px}
.modal-texto{font-size:13.5px;color:var(--sand2);margin:0 0 12px;line-height:1.55}
.modal-id{display:inline-block;font-size:11.5px;font-family:monospace;background:rgba(255,255,255,.05);padding:2px 7px;border-radius:4px;color:var(--amber);margin-top:4px}
.modal-opcoes-excluir{text-align:left;background:rgba(255,255,255,.04);border:1px solid var(--line);border-radius:8px;padding:10px 14px;margin:12px 0;font-size:12.5px}
.modal-opcoes-excluir label{display:flex;align-items:center;gap:8px;margin:7px 0;cursor:pointer;color:var(--sand)}
.modal-opcoes-excluir input[type="radio"]{accent-color:var(--amber);cursor:pointer}
.modal-aviso{display:block;margin-top:10px;font-size:12px;color:#E57373;font-weight:600}
.modal-erro{background:rgba(196,86,74,.18);border:1px solid rgba(196,86,74,.4);color:#FFA49E;padding:8px 12px;border-radius:6px;font-size:12px;margin-bottom:14px;text-align:left}
.modal-acoes{display:flex;gap:10px;justify-content:center;margin-top:20px}
.btn-modal-cancelar{background:rgba(255,255,255,.06);color:var(--sand);border:1px solid var(--line);border-radius:8px;padding:9px 18px;font-size:13px;font-weight:600;cursor:pointer;transition:all .15s ease}
.btn-modal-cancelar:hover{background:rgba(255,255,255,.12);border-color:var(--sand2)}
.btn-modal-confirmar{background:#C4564A;color:#FFF;border:none;border-radius:8px;padding:9px 20px;font-size:13px;font-weight:700;cursor:pointer;transition:background .15s ease}
.btn-modal-confirmar:hover{background:#D96558}
.btn-modal-confirmar:disabled{opacity:.5;cursor:not-allowed}
.tag-ao-vivo{display:inline-flex;align-items:center;gap:4px;padding:2px 7px;border-radius:6px;font-size:11px;font-weight:700;background:rgba(78,157,110,.2);color:#58B982;border:1px solid rgba(78,157,110,.45);margin-left:5px;animation:pulse-live 2s infinite}
@keyframes pulse-live{0%{opacity:.85}50%{opacity:1;box-shadow:0 0 8px rgba(88,185,130,.4)}100%{opacity:.85}}
.tr-flash{animation:tr-flash 2.5s ease}
@keyframes tr-flash{0%{background:rgba(229,169,60,.38)}50%{background:rgba(229,169,60,.18)}100%{background:transparent}}
.btn-filtro-leituras.vivo:hover{border-color:var(--green);color:#58B982;background:rgba(78,157,110,.08)}
.btn-filtro-leituras.vivo.on{border-color:var(--green);background:rgba(78,157,110,.18);color:#58B982;font-weight:700}
.btn-filtro-leituras.vivo.on .badge-count{background:rgba(78,157,110,.25);color:#58B982}
.ws-status{display:inline-flex;align-items:center;gap:6px;font-size:11.5px;padding:3px 10px;border-radius:999px;border:1px solid var(--line);background:rgba(255,255,255,.02);color:var(--sand2);margin-left:auto}
.ws-status.conectado{color:#58B982;border-color:rgba(78,157,110,.4);background:rgba(78,157,110,.1)}
.ws-status.desconectado{color:#E5A93C;border-color:rgba(229,169,60,.4);background:rgba(229,169,60,.1)}
.btn-compra{background:rgba(255,255,255,.05);color:var(--sand2);border:1px solid var(--line);border-radius:6px;padding:3px 8px;font-size:11.5px;font-weight:600;cursor:pointer;transition:all .15s ease;display:inline-flex;align-items:center;gap:4px;white-space:nowrap}
.btn-compra:hover{background:rgba(229,169,60,.12);border-color:var(--amber);color:var(--amber)}
.btn-compra.comprou{background:rgba(78,157,110,.2);color:#58B982;border:1px solid rgba(78,157,110,.5);font-weight:700}
.btn-compra.comprou:hover{background:rgba(78,157,110,.3);border-color:#58B982;color:#FFF}
.tag-comprou{display:inline-flex;align-items:center;gap:3px;padding:2px 7px;border-radius:6px;font-size:11px;font-weight:700;background:rgba(78,157,110,.22);color:#58B982;border:1px solid rgba(78,157,110,.5);margin-left:6px;vertical-align:middle}
.btn-filtro-leituras.comprou:hover{border-color:var(--green);color:#58B982;background:rgba(78,157,110,.08)}
.btn-filtro-leituras.comprou.on{border-color:var(--green);background:rgba(78,157,110,.18);color:#58B982;font-weight:700}
.btn-filtro-leituras.comprou.on .badge-count{background:rgba(78,157,110,.25);color:#58B982}
.modal-card-compra{border-color:rgba(78,157,110,.4);max-width:460px;background:linear-gradient(180deg,#1F1C19 0%,#151412 100%);position:relative}
.modal-card-compra.desmarcar{border-color:rgba(229,169,60,.4)}
.modal-icone-wrap{width:62px;height:62px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 14px;font-size:30px;background:rgba(78,157,110,.14);border:1px solid rgba(78,157,110,.35);box-shadow:0 0 20px rgba(78,157,110,.15)}
.modal-card-compra.desmarcar .modal-icone-wrap{background:rgba(229,169,60,.14);border-color:rgba(229,169,60,.35);box-shadow:0 0 20px rgba(229,169,60,.15)}
.modal-fechar-btn{position:absolute;top:12px;right:14px;background:none;border:none;color:var(--sand2);font-size:16px;cursor:pointer;padding:4px 8px;border-radius:4px;line-height:1;transition:all .15s ease}
.modal-fechar-btn:hover{color:var(--sand);background:rgba(255,255,255,.08)}
.modal-info-box{background:rgba(255,255,255,.03);border:1px solid var(--line);border-radius:10px;padding:12px 16px;margin:14px 0 16px;text-align:center}
.modal-subtexto{font-size:12.5px;color:var(--sand2);margin-top:6px;line-height:1.5}
.btn-modal-confirmar-compra{background:linear-gradient(135deg,#3E9166 0%,#2E724F 100%);color:#FFF;border:none;border-radius:8px;padding:9px 20px;font-size:13px;font-weight:700;cursor:pointer;transition:all .15s ease;box-shadow:0 4px 14px rgba(62,145,102,.35)}
.btn-modal-confirmar-compra:hover{background:linear-gradient(135deg,#4E9D6E 0%,#35825A 100%);box-shadow:0 6px 18px rgba(62,145,102,.5)}
.btn-modal-confirmar-compra:disabled{opacity:.5;cursor:not-allowed}
.btn-modal-confirmar-compra.desmarcar{background:linear-gradient(135deg,#C4564A 0%,#A33C31 100%);box-shadow:0 4px 14px rgba(196,86,74,.35)}
.btn-modal-confirmar-compra.desmarcar:hover{background:linear-gradient(135deg,#D96558 0%,#B84A3E 100%);box-shadow:0 6px 18px rgba(196,86,74,.5)}
.painel-toast{position:fixed;bottom:24px;right:24px;background:#24201D;border:1px solid var(--amber);color:var(--sand);padding:12px 20px;border-radius:8px;font-size:13px;box-shadow:0 10px 25px rgba(0,0,0,.6);z-index:999999;opacity:0;transform:translateY(10px);transition:all .25s ease;pointer-events:none}
.th-chk{width:36px;text-align:center !important;padding:9px 6px 9px 12px !important}
.td-chk{width:36px;text-align:center !important;padding:9px 6px 9px 12px !important}
.chk-selecao{width:16px;height:16px;accent-color:var(--amber);cursor:pointer;vertical-align:middle;margin:0}
.barra-acoes-leituras{display:flex;justify-content:space-between;align-items:center;background:rgba(255,255,255,.02);border:1px solid var(--line);border-radius:10px;padding:10px 14px;margin:10px 0 14px;flex-wrap:wrap;gap:10px}
.acoes-leituras-esquerda{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.acoes-leituras-direita{display:flex;align-items:center;gap:8px}
.chk-label-todos{display:inline-flex;align-items:center;gap:8px;font-size:12.5px;color:var(--sand);cursor:pointer;user-select:none;-webkit-user-select:none}
.chk-label-todos:hover{color:var(--amber)}
.contador-selecao-wrap{display:inline-flex;align-items:center;gap:5px;font-size:12px;color:var(--amber);background:rgba(229,169,60,.12);border:1px solid rgba(229,169,60,.3);border-radius:6px;padding:2px 8px;font-weight:600}
.badge-sel-check{font-size:11px}
.btn-sel-todos-filtro{display:inline-flex;align-items:center;gap:6px;background:rgba(229,169,60,.08);border:1px solid rgba(229,169,60,.35);color:var(--sand);font-size:12px;font-weight:600;border-radius:6px;padding:3px 10px;cursor:pointer;transition:all .15s ease;user-select:none}
.btn-sel-todos-filtro:hover{background:rgba(229,169,60,.18);border-color:var(--amber);color:#FFF}
.btn-sel-todos-filtro.ativo{background:linear-gradient(135deg,rgba(229,169,60,.32) 0%,rgba(229,169,60,.15) 100%);border-color:var(--amber);color:var(--amber);font-weight:700;box-shadow:0 0 10px rgba(229,169,60,.25)}
.btn-limpar-selecao{background:none;border:none;color:var(--sand2);font-size:11.5px;cursor:pointer;padding:3px 8px;border-radius:4px;transition:all .15s ease}
.btn-limpar-selecao:hover{color:#D96558;background:rgba(196,86,74,.12)}
.banner-selecao-global{background:rgba(229,169,60,.1);border:1px solid rgba(229,169,60,.3);border-radius:8px;padding:8px 14px;margin:-4px 0 12px;font-size:12.5px;color:var(--sand);display:flex;align-items:center;justify-content:center;gap:10px;text-align:center;animation:fadein .2s ease}
.btn-link-banner{background:none;border:none;color:var(--amber);font-weight:700;text-decoration:underline;cursor:pointer;font-size:12.5px;padding:0;transition:color .15s ease}
.btn-link-banner:hover{color:#FFF}
.btn-exportar-csv{display:inline-flex;align-items:center;gap:6px;background:linear-gradient(135deg,rgba(229,169,60,.18) 0%,rgba(229,169,60,.06) 100%);border:1px solid var(--amber);color:var(--sand);font-size:12px;font-weight:600;border-radius:8px;padding:6px 14px;cursor:pointer;transition:all .15s ease}
.btn-exportar-csv:hover{background:var(--amber);color:#12100C;font-weight:700;box-shadow:0 3px 10px rgba(229,169,60,.25)}
.btn-importar-csv{display:inline-flex;align-items:center;gap:6px;background:linear-gradient(135deg,rgba(229,169,60,.12) 0%,rgba(229,169,60,.04) 100%);border:1px solid rgba(229,169,60,.4);color:var(--sand);font-size:12px;font-weight:600;border-radius:8px;padding:6px 14px;cursor:pointer;transition:all .15s ease}
.btn-importar-csv:hover{background:var(--amber);color:#12100C;font-weight:700;box-shadow:0 3px 10px rgba(229,169,60,.25)}
.dropzone-csv{border:2px dashed rgba(229,169,60,.4);border-radius:10px;padding:22px 16px;text-align:center;background:rgba(255,255,255,.015);cursor:pointer;transition:all .2s ease}
.dropzone-csv:hover,.dropzone-csv.dragover{border-color:var(--amber);background:rgba(229,169,60,.08);transform:translateY(-1px)}
.dropzone-icone{font-size:28px;margin-bottom:6px}
.dropzone-texto{font-size:13px;font-weight:600;color:var(--sand)}
.dropzone-detalhe{font-size:11px;color:rgba(235,230,222,.55);margin-top:4px}
.dropzone-csv.selecionado{border-style:solid;border-color:var(--green);background:rgba(78,157,110,.1)}
.dropzone-csv.selecionado .dropzone-texto{color:#58B982}
.modal-importar-status{font-size:12.5px;padding:10px 14px;border-radius:8px;text-align:left;line-height:1.5}
.modal-importar-status.sucesso{background:rgba(78,157,110,.15);border:1px solid var(--green);color:#58B982}
.modal-importar-status.processando{background:rgba(229,169,60,.12);border:1px solid var(--amber);color:var(--amber)}
.btn-filtro-leituras.wa:hover{border-color:var(--green);color:#58B982;background:rgba(78,157,110,.08)}
.btn-filtro-leituras.wa.on{border-color:var(--green);background:rgba(78,157,110,.18);color:#58B982;font-weight:700}
.btn-filtro-leituras.wa.on .badge-count{background:rgba(78,157,110,.25);color:#58B982}
.filtro-uf-wrap{display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,.03);border:1px solid var(--line);border-radius:8px;padding:3px 10px;margin-left:4px}
.lbl-filtro-uf{font-size:11.5px;color:var(--sand2);font-weight:600;display:inline-flex;align-items:center;white-space:nowrap}
.select-filtro-uf{background:#1B1815;border:1px solid rgba(229,169,60,.3);color:var(--sand);border-radius:6px;padding:4px 10px;font-size:12px;font-weight:600;cursor:pointer;outline:none;transition:all .15s ease}
.select-filtro-uf:hover,.select-filtro-uf:focus{border-color:var(--amber);color:#FFF;box-shadow:0 0 8px rgba(229,169,60,.25)}
.select-filtro-uf option{background:#1B1815;color:var(--sand);padding:4px}
@keyframes fadein{from{opacity:0;transform:translateY(3px)}to{opacity:1;transform:none}}
"""

JS_PAINEL = r"""
function abrirAba(id){
  if(!id) return;
  document.querySelectorAll(".aba-btn").forEach(function(b){
    b.classList.toggle("on", b.getAttribute("data-tab") === id);
  });
  document.querySelectorAll(".aba-painel").forEach(function(s){
    s.classList.toggle("on", s.id === id);
  });
  try{
    history.replaceState(null, "", "#" + id);
    localStorage.setItem("painel_aba_ativa", id);
  }catch(e){}
  atualizarLinksPresetsAba();
  iniciarArrastoScroll();
}
window.abrirAba = abrirAba;

function atualizarLinksPresetsAba(){
  var aba = (location.hash || "").replace("#", "") || "";
  try{ if(!aba) aba = localStorage.getItem("painel_aba_ativa") || ""; }catch(e){}
  if(!aba) return;
  document.querySelectorAll(".filtros a").forEach(function(el){
    var href = el.getAttribute("href") || "";
    if(href){
      el.setAttribute("href", href.split("#")[0] + "#" + aba);
    }
  });
  var formDatas = document.querySelector(".form-filtro-datas");
  if(formDatas){
    formDatas.action = "/painel#" + aba;
  }
}

function vincularAbas(){
  document.querySelectorAll(".aba-btn").forEach(function(btn){
    if(btn._vinculado) return;
    btn._vinculado = true;
    btn.addEventListener("click", function(e){
      e.preventDefault();
      var id = this.getAttribute("data-tab");
      if(id){
        window.abrirAba(id);
      }
    });
  });
}

var _activeWrap = null;
var _startX = 0;
var _scrollLeft = 0;
var _hasMoved = false;

function iniciarArrastoScroll(){
  // Ativa a mãozinha e o arrasto horizontal com o botão esquerdo EXCLUSIVAMENTE na tabela de Leituras
  var wraps = document.querySelectorAll("#aba-leituras .tbl-wrap, .tbl-wrap-leituras");
  if(wraps.length === 0 && window.location.pathname.indexOf("/painel/leituras") === 0){
    wraps = document.querySelectorAll(".tbl-wrap");
  }
  wraps.forEach(function(wrap){
    if(wrap._dragIniciado) return;
    wrap._dragIniciado = true;

    wrap.addEventListener("mousedown", function(e){
      if(e.button !== 0) return;
      _activeWrap = wrap;
      _hasMoved = false;
      _startX = e.pageX - wrap.offsetLeft;
      _scrollLeft = wrap.scrollLeft;
      wrap.classList.add("arrastando");
    });

    wrap.addEventListener("click", function(e){
      if(_hasMoved){
        e.preventDefault();
        e.stopPropagation();
        _hasMoved = false;
      }
    }, true);
  });
}

window.addEventListener("mousemove", function(e){
  if(!_activeWrap) return;
  var x = e.pageX - _activeWrap.offsetLeft;
  var walk = (x - _startX);
  if(Math.abs(walk) > 4){
    _hasMoved = true;
    try{ window.getSelection().removeAllRanges(); }catch(err){}
    e.preventDefault();
  }
  _activeWrap.scrollLeft = _scrollLeft - walk;
});

window.addEventListener("mouseup", function(){
  if(_activeWrap){
    _activeWrap.classList.remove("arrastando");
    _activeWrap = null;
    setTimeout(function(){ _hasMoved = false; }, 60);
  }
});
function toggleAcordeao(grupoId, btn){
  var subRows = document.querySelectorAll(".grupo-" + grupoId);
  var estaAberto = btn.classList.contains("aberto");
  if(estaAberto){
    subRows.forEach(function(r){ r.style.display = "none"; });
    btn.classList.remove("aberto");
    var seta = btn.querySelector(".seta");
    if(seta){ seta.textContent = "▶"; }
  } else {
    subRows.forEach(function(r){ r.style.display = ""; });
    btn.classList.add("aberto");
    var seta = btn.querySelector(".seta");
    if(seta){ seta.textContent = "▼"; }
  }
}
function filtrarTabelaClient(filtro, btn, evt){
  var tbody = document.getElementById("tbody-leituras");
  if(!tbody){ return true; }
  var rows = tbody.querySelectorAll("tr.tr-pessoa");
  var totalRows = rows.length;
  if(totalRows > 0 && totalRows <= 20){
    if(evt && evt.preventDefault){ evt.preventDefault(); }
    var selUF = document.getElementById("select-filtro-uf");
    var ufNorm = (selUF && selUF.value) ? selUF.value.trim().toLowerCase() : "";
    var visiveis = 0;
    rows.forEach(function(r){
      var chk = r.getAttribute("data-checkout") === "1";
      var vivo = r.getAttribute("data-ao-vivo") === "1";
      var comprou = r.getAttribute("data-comprou") === "1";
      var wa = r.getAttribute("data-whatsapp") === "1";
      var rowUF = (r.getAttribute("data-uf") || "").trim().toLowerCase();
      var idGrupo = r.id.replace("row-pessoa-", "");
      var subRows = document.querySelectorAll(".grupo-" + idGrupo);
      var mostrarModo = true;
      if(filtro === "checkout"){
        mostrarModo = chk;
      } else if(filtro === "ao_vivo"){
        mostrarModo = vivo;
      } else if(filtro === "comprou"){
        mostrarModo = comprou;
      } else if(filtro === "whatsapp"){
        mostrarModo = wa;
      }
      var mostrarUF = (!ufNorm || rowUF === ufNorm);
      var mostrar = mostrarModo && mostrarUF;
      if(!mostrar){
        r.style.display = "none";
        subRows.forEach(function(sr){ sr.style.display = "none"; });
      } else {
        r.style.display = "";
        visiveis++;
      }
    });
    document.querySelectorAll(".btn-filtro-leituras").forEach(function(b){
      var bFiltro = b.getAttribute("data-filtro") || (b.getAttribute("data-so-checkout") === "1" ? "checkout" : "todos");
      b.classList.toggle("on", bFiltro === filtro);
    });
    var sub = document.getElementById("sub-leituras-info");
    if(sub){
      var tipo = "pessoas no total";
      if(filtro === "checkout") tipo = "pessoas com checkout";
      else if(filtro === "ao_vivo") tipo = "pessoas ativas navegando agora";
      else if(filtro === "comprou") tipo = "pessoas que compraram o produto";
      else if(filtro === "whatsapp") tipo = "pessoas que deixaram WhatsApp";
      var ufTxt = (selUF && selUF.value) ? (" (UF: " + selUF.value + ")") : "";
      sub.innerHTML = "<b>" + visiveis + "</b> " + tipo + ufTxt + " · mostrando até 20 por página · clique no ID para ver o mapa astrológico e o detalhe completo.";
    }
    _selecionarTodosFiltro = false;
    atualizarContadorSelecao();
    try{
      var href = btn ? btn.getAttribute("href") : null;
      if(href){
        var u = new URL(href, window.location.href);
        if(selUF && selUF.value){ u.searchParams.set("uf", selUF.value); }
        else { u.searchParams.delete("uf"); }
        history.replaceState(null, "", u.toString());
      }
    }catch(e){}
    return false;
  }
  return true;
}

function filtrarPorUFClient(ufValor){
  var ufNorm = (ufValor || "").trim().toLowerCase();
  var tbody = document.getElementById("tbody-leituras");
  if(!tbody){ return; }
  var rows = tbody.querySelectorAll("tr.tr-pessoa");
  var totalRows = rows.length;

  if(totalRows > 20){
    try{
      var u = new URL(window.location.href);
      if(ufValor){ u.searchParams.set("uf", ufValor); }
      else { u.searchParams.delete("uf"); }
      u.searchParams.delete("pag_leituras");
      window.location.href = u.toString();
    }catch(e){
      window.location.search = (ufValor ? ("?uf=" + encodeURIComponent(ufValor)) : "");
    }
    return;
  }

  var bAtivo = document.querySelector(".btn-filtro-leituras.on");
  var modo = bAtivo ? (bAtivo.getAttribute("data-filtro") || "todos") : "todos";
  var visiveis = 0;

  rows.forEach(function(r){
    var chk = r.getAttribute("data-checkout") === "1";
    var vivo = r.getAttribute("data-ao-vivo") === "1";
    var comprou = r.getAttribute("data-comprou") === "1";
    var wa = r.getAttribute("data-whatsapp") === "1";
    var rowUF = (r.getAttribute("data-uf") || "").trim().toLowerCase();
    var idGrupo = r.id.replace("row-pessoa-", "");
    var subRows = document.querySelectorAll(".grupo-" + idGrupo);

    var atendeModo = true;
    if(modo === "checkout") atendeModo = chk;
    else if(modo === "ao_vivo") atendeModo = vivo;
    else if(modo === "comprou") atendeModo = comprou;
    else if(modo === "whatsapp") atendeModo = wa;

    var atendeUF = (!ufNorm || rowUF === ufNorm);
    var mostrar = atendeModo && atendeUF;

    if(!mostrar){
      r.style.display = "none";
      subRows.forEach(function(sr){ sr.style.display = "none"; });
    } else {
      r.style.display = "";
      visiveis++;
    }
  });

  var sub = document.getElementById("sub-leituras-info");
  if(sub){
    var tipo = "pessoas exibidas";
    if(modo === "checkout") tipo = "pessoas com checkout";
    else if(modo === "ao_vivo") tipo = "pessoas ativas navegando agora";
    else if(modo === "comprou") tipo = "pessoas que compraram o produto";
    else if(modo === "whatsapp") tipo = "pessoas que deixaram WhatsApp";
    var ufTxt = ufValor ? (" (UF: " + ufValor + ")") : "";
    sub.innerHTML = "<b>" + visiveis + "</b> " + tipo + ufTxt + " · mostrando até 20 por página · clique no ID para ver o mapa astrológico e o detalhe completo.";
  }

  _selecionarTodosFiltro = false;
  atualizarContadorSelecao();

  try{
    var u = new URL(window.location.href);
    if(ufValor){ u.searchParams.set("uf", ufValor); }
    else { u.searchParams.delete("uf"); }
    history.replaceState(null, "", u.toString());
  }catch(e){}
}
function filtrarCheckoutClient(soChk, btn, evt){
  return filtrarTabelaClient(soChk === 1 ? "checkout" : "todos", btn, evt);
}

var _selecionarTodosFiltro = false;
var _idsSelecionados = new Set();

function obterAssinaturaFiltro(){
  try{
    var u = new URL(window.location.href);
    var partes = [];
    var temDatas = (u.searchParams.get("de") || u.searchParams.get("ate"));
    var diasVal = u.searchParams.get("dias") || (temDatas ? "" : "7");
    if(diasVal) partes.push("dias=" + diasVal);
    ["de", "ate", "bots", "teste", "so_checkout", "so_ao_vivo", "so_comprou", "so_whatsapp", "uf"].sort().forEach(function(k){
      var v = u.searchParams.get(k);
      if(v !== null && v !== "") partes.push(k + "=" + v);
    });
    return partes.join("&");
  }catch(e){
    return "";
  }
}

function salvarEstadoSelecao(){
  try{
    var sig = obterAssinaturaFiltro();
    sessionStorage.setItem("painel_sel_sig", sig);
    sessionStorage.setItem("painel_sel_todos", _selecionarTodosFiltro ? "1" : "0");
    sessionStorage.setItem("painel_sel_ids", JSON.stringify(Array.from(_idsSelecionados)));
  }catch(e){}
}

function carregarEstadoSelecao(){
  try{
    var sigAtual = obterAssinaturaFiltro();
    var sigSalva = sessionStorage.getItem("painel_sel_sig");
    if(sigSalva !== null && sigSalva !== sigAtual){
      sessionStorage.removeItem("painel_sel_todos");
      sessionStorage.removeItem("painel_sel_ids");
      sessionStorage.setItem("painel_sel_sig", sigAtual);
      _selecionarTodosFiltro = false;
      _idsSelecionados.clear();
      return;
    }
    _selecionarTodosFiltro = (sessionStorage.getItem("painel_sel_todos") === "1");
    var idsRaw = sessionStorage.getItem("painel_sel_ids");
    if(idsRaw){
      var lista = JSON.parse(idsRaw);
      _idsSelecionados = new Set(lista);
    } else {
      _idsSelecionados = new Set();
    }
  }catch(e){
    _selecionarTodosFiltro = false;
    _idsSelecionados = new Set();
  }
}

function aplicarSelecaoNoDOM(){
  carregarEstadoSelecao();
  var rows = document.querySelectorAll("tr.tr-pessoa:not([style*='display: none'])");
  rows.forEach(function(r){
    var c = r.querySelector(".chk-contato");
    if(!c) return;
    var id = c.getAttribute("data-id");
    if(_selecionarTodosFiltro || (id && _idsSelecionados.has(id))){
      c.checked = true;
    } else {
      c.checked = false;
    }
  });
  atualizarContadorSelecao();
}

function toggleContatoIndividual(chk){
  var id = chk.getAttribute("data-id");
  if(!id) return;
  if(chk.checked){
    _idsSelecionados.add(id);
  } else {
    _idsSelecionados.delete(id);
    _selecionarTodosFiltro = false;
  }
  salvarEstadoSelecao();
  atualizarContadorSelecao();
}

function obterTotalFiltro(){
  if(typeof window._totalLeiturasFiltro === "number") return window._totalLeiturasFiltro;
  var barra = document.getElementById("barra-acoes-leituras");
  if(barra){
    var tf = parseInt(barra.getAttribute("data-total-filtro"), 10);
    if(!isNaN(tf)) return tf;
  }
  return 0;
}

function obterTotalPagina(){
  if(typeof window._totalLeiturasPagina === "number") return window._totalLeiturasPagina;
  var chks = document.querySelectorAll("tr.tr-pessoa:not([style*='display: none']) .chk-contato");
  return chks.length;
}

function toggleSelecionarTodosFiltro(){
  if(_selecionarTodosFiltro){
    limparSelecao();
  } else {
    selecionarTodosFiltro();
  }
}

function selecionarTodosFiltro(){
  _selecionarTodosFiltro = true;
  _idsSelecionados.clear();
  var chkTopo = document.getElementById("chk-selecionar-todos-topo");
  var chkBarra = document.getElementById("chk-selecionar-todos-barra");
  if(chkTopo) chkTopo.checked = true;
  if(chkBarra) chkBarra.checked = true;
  var rows = document.querySelectorAll("tr.tr-pessoa:not([style*='display: none'])");
  rows.forEach(function(r){
    var c = r.querySelector(".chk-contato");
    if(c){ c.checked = true; }
  });
  salvarEstadoSelecao();
  atualizarContadorSelecao();
  mostrarToastPainel("Todos os contatos do período foram selecionados!");
}

function limparSelecao(){
  _selecionarTodosFiltro = false;
  _idsSelecionados.clear();
  try{
    sessionStorage.removeItem("painel_sel_todos");
    sessionStorage.removeItem("painel_sel_ids");
  }catch(e){}
  var chkTopo = document.getElementById("chk-selecionar-todos-topo");
  var chkBarra = document.getElementById("chk-selecionar-todos-barra");
  if(chkTopo) chkTopo.checked = false;
  if(chkBarra) chkBarra.checked = false;
  var chks = document.querySelectorAll("tr.tr-pessoa .chk-contato");
  chks.forEach(function(c){ c.checked = false; });
  atualizarContadorSelecao();
}

function toggleSelecionarTodos(chkMaster){
  var marcado = !!chkMaster.checked;
  var chkTopo = document.getElementById("chk-selecionar-todos-topo");
  var chkBarra = document.getElementById("chk-selecionar-todos-barra");
  if(chkTopo && chkTopo !== chkMaster) chkTopo.checked = marcado;
  if(chkBarra && chkBarra !== chkMaster) chkBarra.checked = marcado;

  var rows = document.querySelectorAll("tr.tr-pessoa");
  rows.forEach(function(r){
    if(r.style.display !== "none"){
      var c = r.querySelector(".chk-contato");
      if(c){
        c.checked = marcado;
        var id = c.getAttribute("data-id");
        if(id){
          if(marcado) _idsSelecionados.add(id);
          else _idsSelecionados.delete(id);
        }
      }
    }
  });

  if(!marcado){
    _selecionarTodosFiltro = false;
  }
  salvarEstadoSelecao();
  atualizarContadorSelecao();
}

function atualizarContadorSelecao(){
  var chks = document.querySelectorAll("tr.tr-pessoa:not([style*='display: none']) .chk-contato");
  var totalPagina = chks.length;
  var selecionadosPagina = 0;
  chks.forEach(function(c){
    if(c.checked) selecionadosPagina++;
  });

  var totalFiltro = obterTotalFiltro() || totalPagina;
  if(totalFiltro < totalPagina) totalFiltro = totalPagina;

  var chkTopo = document.getElementById("chk-selecionar-todos-topo");
  var chkBarra = document.getElementById("chk-selecionar-todos-barra");
  var todosPaginaMarcados = (totalPagina > 0 && selecionadosPagina === totalPagina);
  if(chkTopo) chkTopo.checked = (_selecionarTodosFiltro || todosPaginaMarcados);
  if(chkBarra) chkBarra.checked = (_selecionarTodosFiltro || todosPaginaMarcados);

  var wrap = document.getElementById("contador-selecao-wrap");
  var btnTxt = document.getElementById("btn-exportar-contagem");
  var btnSelFiltro = document.getElementById("btn-sel-todos-filtro");
  var btnLimpar = document.getElementById("btn-limpar-selecao");
  var banner = document.getElementById("banner-selecao-global");
  var txtBanner = document.getElementById("txt-banner-selecao");
  var btnBannerAcao = document.getElementById("btn-banner-acao");

  if(btnSelFiltro){
    btnSelFiltro.classList.toggle("ativo", !!_selecionarTodosFiltro);
    if(_selecionarTodosFiltro){
      btnSelFiltro.innerHTML = '✓ Todos os <b>' + totalFiltro + '</b> selecionados';
      btnSelFiltro.title = "Clique para desmarcar a seleção global de contatos";
    } else {
      btnSelFiltro.innerHTML = '📋 Selecionar todos os <span class="num-total-filtro">' + totalFiltro + '</span> contatos';
      btnSelFiltro.title = "Selecionar todos os " + totalFiltro + " contatos deste filtro em todas as páginas";
    }
  }

  if(_selecionarTodosFiltro){
    if(wrap){
      wrap.style.display = "inline-flex";
      wrap.innerHTML = '<span class="badge-sel-check">✓</span> Todos os <b id="contador-selecao-num">' + totalFiltro + '</b> selecionados (todas as páginas)';
    }
    if(btnTxt){
      btnTxt.textContent = "(todos os " + totalFiltro + " contatos)";
    }
    if(btnLimpar){
      btnLimpar.style.display = "inline-flex";
    }
    if(banner){
      banner.style.display = "flex";
      if(txtBanner) txtBanner.innerHTML = "✓ Todos os <b>" + totalFiltro + "</b> contatos deste filtro estão selecionados (incluindo todas as páginas).";
      if(btnBannerAcao){
        btnBannerAcao.textContent = "Desmarcar seleção";
        btnBannerAcao.onclick = limparSelecao;
      }
    }
  } else {
    var totalSelGeral = _idsSelecionados.size;
    if(wrap){
      if(totalSelGeral > 0){
        wrap.style.display = "inline-flex";
        wrap.innerHTML = '<span class="badge-sel-check">✓</span> <b id="contador-selecao-num">' + totalSelGeral + '</b> selecionado' + (totalSelGeral > 1 ? "s" : "");
      } else {
        wrap.style.display = "none";
      }
    }
    if(btnLimpar){
      btnLimpar.style.display = (totalSelGeral > 0) ? "inline-flex" : "none";
    }
    if(btnTxt){
      if(totalSelGeral > 0){
        btnTxt.textContent = "(" + totalSelGeral + " selecionado" + (totalSelGeral > 1 ? "s" : "") + ")";
      } else {
        btnTxt.textContent = "(todos: " + totalFiltro + ")";
      }
    }
    if(banner){
      if(todosPaginaMarcados && totalFiltro > totalPagina){
        banner.style.display = "flex";
        if(txtBanner) txtBanner.innerHTML = "Todos os <b>" + totalPagina + "</b> contatos desta página estão selecionados.";
        if(btnBannerAcao){
          btnBannerAcao.innerHTML = "👉 Selecionar todos os <b>" + totalFiltro + "</b> contatos deste filtro";
          btnBannerAcao.onclick = selecionarTodosFiltro;
        }
      } else {
        banner.style.display = "none";
      }
    }
  }
}

function exportarTodosViaServidor(){
  var u = new URL(window.location.href);
  var exportUrl = new URL("/painel/exportar-csv", window.location.origin);
  ["de", "ate", "dias", "bots", "teste", "so_checkout", "so_ao_vivo", "so_comprou", "so_whatsapp", "uf"].forEach(function(param){
    var val = u.searchParams.get(param);
    if(val !== null && val !== "") {
      exportUrl.searchParams.set(param, val);
    }
  });
  var selUF = document.getElementById("select-filtro-uf");
  if(selUF && selUF.value){
    exportUrl.searchParams.set("uf", selUF.value);
  }
  var bAtivo = document.querySelector(".btn-filtro-leituras.on");
  if(bAtivo){
    var modo = bAtivo.getAttribute("data-filtro");
    if(modo === "checkout") exportUrl.searchParams.set("so_checkout", "1");
    else if(modo === "ao_vivo") exportUrl.searchParams.set("so_ao_vivo", "1");
    else if(modo === "comprou") exportUrl.searchParams.set("so_comprou", "1");
    else if(modo === "whatsapp") exportUrl.searchParams.set("so_whatsapp", "1");
    else if(modo === "todos"){
      exportUrl.searchParams.delete("so_checkout");
      exportUrl.searchParams.delete("so_ao_vivo");
      exportUrl.searchParams.delete("so_comprou");
      exportUrl.searchParams.delete("so_whatsapp");
    }
  }

  var a = document.createElement("a");
  a.href = exportUrl.toString();
  a.setAttribute("download", "");
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  mostrarToastPainel("Baixando planilha CSV com todos os contatos do período...");
}

function exportarSelecionadosViaServidor(idsList){
  if(!idsList || idsList.length === 0){
    alert("Nenhum contato selecionado para exportar.");
    return;
  }
  var exportUrl = new URL("/painel/exportar-csv", window.location.origin);
  exportUrl.searchParams.set("ids", idsList.join(","));
  var a = document.createElement("a");
  a.href = exportUrl.toString();
  a.setAttribute("download", "");
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  mostrarToastPainel("Baixando " + idsList.length + " contato(s) selecionado(s)...");
}

function exportarContatosCSV(){
  var totalFiltro = obterTotalFiltro();
  if(_selecionarTodosFiltro || (_idsSelecionados.size === 0 && totalFiltro > 0)){
    exportarTodosViaServidor();
    return;
  }

  if(_idsSelecionados.size === 0){
    alert("Nenhum contato selecionado para exportar.");
    return;
  }

  var mapa = window._contatosExportacao || {};
  var selecionados = Array.from(_idsSelecionados);
  var todosNoMapa = selecionados.every(function(id){ return !!mapa[id]; });

  if(!todosNoMapa){
    exportarSelecionadosViaServidor(selecionados);
    return;
  }

  var colunas = [
    "ID da Leitura",
    "Chegou ao Quiz (BSB)",
    "Preencheu Dados (BSB)",
    "Etapa Alcançada",
    "Fez Checkout",
    "Comprou",
    "Nome Completo",
    "WhatsApp",
    "Data de Nascimento",
    "Hora de Nascimento",
    "Cidade",
    "UF",
    "País",
    "Área do Quiz",
    "Cenário Astrológico",
    "Casa Astrológica",
    "Tempo no Quiz",
    "Total de Envios"
  ];

  function esc(val){
    if(val === null || val === undefined) return '""';
    return '"' + String(val).replace(/"/g, '""') + '"';
  }

  var linhas = [];
  linhas.push(colunas.map(esc).join(";"));

  selecionados.forEach(function(id){
    var d = mapa[id] || {};
    linhas.push([
      esc(d.id || id),
      esc(d.chegou_em_bsb || "—"),
      esc(d.gravado_em_bsb || "—"),
      esc(d.etapa || "—"),
      esc(d.checkout || "NÃO"),
      esc(d.comprou || "NÃO"),
      esc(d.nome || "—"),
      esc(d.whatsapp || "—"),
      esc(d.nascimento || "—"),
      esc(d.hora_nasc || "—"),
      esc(d.cidade || "—"),
      esc(d.uf || "—"),
      esc(d.pais || "Brasil"),
      esc(d.area || "—"),
      esc(d.cenario || "—"),
      esc(d.casa || "—"),
      esc(d.tempo_quiz || "—"),
      esc(d.total_envios || 1)
    ].join(";"));
  });

  var csvConteudo = "\uFEFF" + linhas.join("\r\n");
  var blob = new Blob([csvConteudo], { type: "text/csv;charset=utf-8;" });
  var link = document.createElement("a");
  var url = URL.createObjectURL(blob);
  var hoje = new Date().toISOString().slice(0, 10);
  link.setAttribute("href", url);
  link.setAttribute("download", "leituras_bussola_" + hoje + ".csv");
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
  mostrarToastPainel(selecionados.length + " contato(s) exportado(s) com sucesso!");
}

var _arquivoCSVParaImportar = null;

function abrirModalImportarCSV(){
  _arquivoCSVParaImportar = null;
  var input = document.getElementById("input-arquivo-csv");
  if(input) input.value = "";
  var dropzone = document.getElementById("dropzone-csv");
  if(dropzone) dropzone.classList.remove("selecionado", "dragover");
  var dropTexto = document.getElementById("dropzone-texto");
  if(dropTexto) dropTexto.textContent = "Clique ou arraste o arquivo CSV aqui";
  var dropDet = document.getElementById("dropzone-detalhe");
  if(dropDet) dropDet.textContent = "Compatível com Excel, Google Sheets e CRM (UTF-8, Latin-1, sep: ; ou ,)";
  var st = document.getElementById("modal-importar-status");
  if(st){ st.style.display = "none"; st.textContent = ""; st.className = "modal-importar-status"; }
  var er = document.getElementById("modal-importar-erro");
  if(er){ er.style.display = "none"; er.textContent = ""; }
  var btn = document.getElementById("btn-modal-enviar-csv");
  if(btn){ btn.disabled = true; btn.textContent = "Iniciar Importação"; }
  var modal = document.getElementById("modal-importar-csv-backdrop");
  if(modal) modal.classList.add("on");
  inicializarDropzoneCSV();
}

function fecharModalImportarCSV(){
  _arquivoCSVParaImportar = null;
  var modal = document.getElementById("modal-importar-csv-backdrop");
  if(modal) modal.classList.remove("on");
}

function arquivoCSVSelecionado(input){
  if(!input || !input.files || input.files.length === 0) return;
  definirArquivoCSV(input.files[0]);
}

function definirArquivoCSV(file){
  if(!file) return;
  if(!file.name.toLowerCase().endsWith(".csv")){
    var er = document.getElementById("modal-importar-erro");
    if(er){
      er.textContent = "Por favor, selecione um arquivo válido com extensão .csv";
      er.style.display = "block";
    }
    return;
  }
  _arquivoCSVParaImportar = file;
  var er = document.getElementById("modal-importar-erro");
  if(er){ er.style.display = "none"; }
  var dropzone = document.getElementById("dropzone-csv");
  if(dropzone) dropzone.classList.add("selecionado");
  var dropTexto = document.getElementById("dropzone-texto");
  if(dropTexto) dropTexto.textContent = "📄 " + file.name;
  var dropDet = document.getElementById("dropzone-detalhe");
  if(dropDet){
    var tamKb = (file.size / 1024).toFixed(1);
    dropDet.textContent = "Tamanho: " + tamKb + " KB · Arquivo pronto para envio";
  }
  var btn = document.getElementById("btn-modal-enviar-csv");
  if(btn) btn.disabled = false;
}

function inicializarDropzoneCSV(){
  var drop = document.getElementById("dropzone-csv");
  if(!drop || drop._inicializado) return;
  drop._inicializado = true;
  ["dragenter", "dragover"].forEach(function(evt){
    drop.addEventListener(evt, function(e){
      e.preventDefault();
      e.stopPropagation();
      drop.classList.add("dragover");
    }, false);
  });
  ["dragleave", "drop"].forEach(function(evt){
    drop.addEventListener(evt, function(e){
      e.preventDefault();
      e.stopPropagation();
      drop.classList.remove("dragover");
    }, false);
  });
  drop.addEventListener("drop", function(e){
    if(e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0){
      definirArquivoCSV(e.dataTransfer.files[0]);
    }
  }, false);
}

function executarImportacaoCSV(){
  if(!_arquivoCSVParaImportar){
    alert("Selecione um arquivo CSV para importar.");
    return;
  }
  var btn = document.getElementById("btn-modal-enviar-csv");
  var st = document.getElementById("modal-importar-status");
  var er = document.getElementById("modal-importar-erro");
  var chkAtualizar = document.getElementById("chk-importar-atualizar");
  var atualizar = (chkAtualizar && !chkAtualizar.checked) ? "0" : "1";

  if(btn){ btn.disabled = true; btn.textContent = "Importando..."; }
  if(er){ er.style.display = "none"; er.textContent = ""; }
  if(st){
    st.style.display = "block";
    st.className = "modal-importar-status processando";
    st.textContent = "Processando arquivo e atualizando contatos...";
  }

  var formData = new FormData();
  formData.append("arquivo", _arquivoCSVParaImportar);
  formData.append("atualizar", atualizar);

  fetch("/painel/importar-csv", {
    method: "POST",
    body: formData,
    headers: { "Accept": "application/json" }
  }).then(function(res){
    if(!res.ok){
      return res.json().then(function(j){ throw new Error(j.detail || ("Erro HTTP " + res.status)); })
             .catch(function(e){ throw new Error(e.message || ("Erro HTTP " + res.status)); });
    }
    return res.json();
  }).then(function(res){
    if(btn){ btn.disabled = false; btn.textContent = "Iniciar Importação"; }
    if(st){
      st.className = "modal-importar-status sucesso";
      var msg = "✓ Sucesso! Total de " + res.total + " contato(s) processado(s): " +
                res.criados + " novo(s) contato(s) criado(s), " +
                res.atualizados + " atualizado(s).";
      if(res.erros && res.erros.length > 0){
        msg += " (" + res.erros.length + " inconsistência(s))";
      }
      st.innerHTML = "<b>" + msg + "</b><div style='margin-top:6px;font-size:11.5px;'>Atualizando visualização...</div>";
    }
    if(typeof mostrarToast === "function"){
      mostrarToast("Importação concluída: " + res.criados + " criados, " + res.atualizados + " atualizados.");
    }
    setTimeout(function(){
      fecharModalImportarCSV();
      if(typeof recarregarTabelaLeiturasViaWS === "function"){
        recarregarTabelaLeiturasViaWS();
      } else {
        window.location.reload();
      }
    }, 1200);
  }).catch(function(err){
    if(btn){ btn.disabled = false; btn.textContent = "Tentar Novamente"; }
    if(st) st.style.display = "none";
    if(er){
      er.style.display = "block";
      er.textContent = "Falha na importação: " + err.message;
    }
  });
}

var _leituraCompraAlvo = null;
var _novoStatusCompra = false;
var _btnCompraAlvo = null;

function abrirModalCompra(id, nome, btnOuStatus, btnExtra){
  if(!id) return;
  _leituraCompraAlvo = id;

  var btn = null;
  if(btnOuStatus && typeof btnOuStatus === "object" && btnOuStatus.nodeType){
    btn = btnOuStatus;
  } else if(btnExtra && typeof btnExtra === "object" && btnExtra.nodeType){
    btn = btnExtra;
  }
  _btnCompraAlvo = btn || document.getElementById("btn-compra-" + id);

  var estaComprou = false;
  if(_btnCompraAlvo){
    estaComprou = _btnCompraAlvo.classList.contains("comprou");
  } else {
    var r = document.getElementById("row-pessoa-" + id) || document.getElementById("row-leitura-" + id);
    if(r){
      estaComprou = (r.getAttribute("data-comprou") === "1");
    } else if(typeof btnOuStatus === "boolean" || typeof btnOuStatus === "number"){
      estaComprou = !!btnOuStatus;
    }
  }

  _novoStatusCompra = !estaComprou;

  if(!nome){
    var rPessoa = document.getElementById("row-pessoa-" + id);
    if(rPessoa){
      var tdNome = rPessoa.querySelector("td:nth-child(6)");
      if(tdNome){
        nome = tdNome.childNodes[0] ? tdNome.childNodes[0].textContent.trim() : tdNome.textContent.trim();
      }
    }
  }

  var elCard = document.getElementById("modal-compra-card");
  var elIcone = document.getElementById("modal-compra-icone");
  var elTitulo = document.getElementById("modal-compra-titulo");
  var elPergunta = document.getElementById("modal-compra-pergunta");
  var elNome = document.getElementById("modal-compra-nome");
  var elId = document.getElementById("modal-compra-id");
  var elDesc = document.getElementById("modal-compra-desc");
  var elErro = document.getElementById("modal-compra-erro");
  var btnConfirmar = document.getElementById("btn-modal-confirmar-compra");

  if(elNome) elNome.textContent = nome || "Contato (" + id + ")";
  if(elId) elId.textContent = "ID: " + id;
  if(elErro){ elErro.style.display = "none"; elErro.textContent = ""; }

  if(_novoStatusCompra){
    if(elCard) elCard.classList.remove("desmarcar");
    if(elIcone) elIcone.textContent = "💰";
    if(elTitulo) elTitulo.textContent = "Confirmar Compra do Produto";
    if(elPergunta) elPergunta.textContent = "Deseja marcar que este contato comprou o produto?";
    if(elDesc) elDesc.textContent = "Ao confirmar, o contato receberá o selo ✅ Comprou e será contabilizado no filtro de compradores.";
    if(btnConfirmar){
      btnConfirmar.className = "btn-modal-confirmar-compra";
      btnConfirmar.textContent = "Sim, Marcar Compra";
      btnConfirmar.disabled = false;
    }
  } else {
    if(elCard) elCard.classList.add("desmarcar");
    if(elIcone) elIcone.textContent = "↩️";
    if(elTitulo) elTitulo.textContent = "Desmarcar Compra";
    if(elPergunta) elPergunta.textContent = "Deseja realmente desmarcar a compra deste contato?";
    if(elDesc) elDesc.textContent = "O selo ✅ Comprou será removido deste contato e as métricas do painel serão atualizadas.";
    if(btnConfirmar){
      btnConfirmar.className = "btn-modal-confirmar-compra desmarcar";
      btnConfirmar.textContent = "Sim, Desmarcar";
      btnConfirmar.disabled = false;
    }
  }

  var modal = document.getElementById("modal-compra-backdrop");
  if(modal){ modal.classList.add("on"); }
}

function fecharModalCompra(){
  _leituraCompraAlvo = null;
  _btnCompraAlvo = null;
  var modal = document.getElementById("modal-compra-backdrop");
  if(modal){ modal.classList.remove("on"); }
}

function executarConfirmacaoCompra(){
  if(!_leituraCompraAlvo) return;
  var id = _leituraCompraAlvo;
  var novoStatus = _novoStatusCompra;
  var btnConfirmar = document.getElementById("btn-modal-confirmar-compra");
  var elErro = document.getElementById("modal-compra-erro");
  var elBtnOrig = _btnCompraAlvo || document.getElementById("btn-compra-" + id);

  if(btnConfirmar){
    btnConfirmar.disabled = true;
    btnConfirmar.textContent = "Salvando...";
  }
  if(elBtnOrig){
    elBtnOrig.disabled = true;
    elBtnOrig._textoOriginal = elBtnOrig.textContent;
    elBtnOrig.textContent = "...";
  }

  fetch("/painel/leitura/" + encodeURIComponent(id) + "/status-compra?comprou=" + (novoStatus ? "true" : "false"), {
    method: "POST",
    headers: { "Accept": "application/json" }
  }).then(function(res){
    if(!res.ok){
      return res.json().then(function(j){ throw new Error(j.detail || ("Erro " + res.status)); })
             .catch(function(e){ throw new Error(e.message || ("Erro " + res.status)); });
    }
    return res.json();
  }).then(function(data){
    if(elBtnOrig) elBtnOrig.disabled = false;
    fecharModalCompra();
    aplicarStatusCompraNoDOM(id, novoStatus, data.total_comprou);
    mostrarToast(novoStatus ? "Contato marcado como comprou!" : "Status de compra desmarcado.");
  }).catch(function(err){
    if(btnConfirmar){
      btnConfirmar.disabled = false;
      btnConfirmar.textContent = novoStatus ? "Sim, Marcar Compra" : "Sim, Desmarcar";
    }
    if(elBtnOrig){
      elBtnOrig.disabled = false;
      elBtnOrig.textContent = elBtnOrig._textoOriginal || (novoStatus ? "💰 Comprou" : "✅ Comprou");
    }
    if(elErro){
      elErro.textContent = "Erro ao salvar: " + err.message;
      elErro.style.display = "block";
    } else {
      alert("Erro ao alterar status de compra: " + err.message);
    }
  });
}

function alternarCompra(id, btn, nome){
  abrirModalCompra(id, nome, undefined, btn);
}

function aplicarStatusCompraNoDOM(id, comprou, totalComprou){
  var row = document.getElementById("row-pessoa-" + id) || document.getElementById("row-leitura-" + id);
  if(row){
    row.setAttribute("data-comprou", comprou ? "1" : "0");
    var btn = document.getElementById("btn-compra-" + id) || row.querySelector(".btn-compra");
    if(btn){
      btn.classList.toggle("comprou", comprou);
      btn.textContent = comprou ? "✅ Comprou" : "💰 Comprou";
      btn.title = comprou ? "Compra confirmada. Clique para desmarcar." : "Clique para marcar que este contato comprou o produto.";
    }
    var tag = document.getElementById("tag-comprou-" + id);
    if(tag){
      tag.style.display = comprou ? "inline-flex" : "none";
    }
    flashElemento(row);
  }

  var btnDetalhe = document.getElementById("btn-compra-" + id);
  if(btnDetalhe && !row){
    btnDetalhe.classList.toggle("comprou", comprou);
    btnDetalhe.textContent = comprou ? "✅ Comprou" : "💰 Marcar Compra";
  }

  var bComprou = document.getElementById("badge-count-comprou");
  if(bComprou){
    if(totalComprou !== undefined && totalComprou !== null){
      bComprou.textContent = totalComprou;
    } else {
      var cur = parseInt(bComprou.textContent || "0", 10);
      bComprou.textContent = Math.max(0, cur + (comprou ? 1 : -1));
    }
  }
}
var _leituraParaExcluir = null;
var _leituraEhSub = false;
var _grupoTodosIds = [];
function abrirModalExcluir(id, nome, totalEnvios, todosIdsJson, ehSub){
  _leituraParaExcluir = id;
  _leituraEhSub = !!ehSub;
  try{
    _grupoTodosIds = todosIdsJson ? JSON.parse(todosIdsJson) : [id];
  }catch(e){
    _grupoTodosIds = [id];
  }
  var elNome = document.getElementById("modal-del-nome");
  var elId = document.getElementById("modal-del-id");
  var elErro = document.getElementById("modal-del-erro");
  var btnConf = document.getElementById("btn-modal-confirmar");
  var opcoes = document.getElementById("modal-del-opcoes");
  var spanTotal = document.getElementById("modal-del-total-envios");
  var spanCurto = document.getElementById("modal-del-id-curto");

  if(elNome) elNome.textContent = nome || "Sem nome";
  if(elId) elId.textContent = "ID: " + id;
  if(elErro){ elErro.style.display = "none"; elErro.textContent = ""; }
  if(btnConf){ btnConf.disabled = false; btnConf.textContent = "Sim, Excluir"; }

  if(!_leituraEhSub && totalEnvios && totalEnvios > 1 && opcoes){
    opcoes.style.display = "block";
    if(spanTotal) spanTotal.textContent = totalEnvios;
    if(spanCurto) spanCurto.textContent = id.substring(0, 15);
    var radios = document.getElementsByName("modo_exclusao");
    if(radios.length > 0) radios[0].checked = true;
  } else if(opcoes){
    opcoes.style.display = "none";
  }

  var modal = document.getElementById("modal-excluir-backdrop");
  if(modal){ modal.classList.add("on"); }
}
function fecharModalExcluir(){
  _leituraParaExcluir = null;
  var modal = document.getElementById("modal-excluir-backdrop");
  if(modal){ modal.classList.remove("on"); }
}
document.addEventListener("keydown", function(e){
  if(e.key === "Escape"){
    fecharModalExcluir();
    fecharModalCompra();
    fecharModalImportarCSV();
  }
});
function executarExclusao(){
  if(!_leituraParaExcluir) return;
  var id = _leituraParaExcluir;
  var btnConf = document.getElementById("btn-modal-confirmar");
  var elErro = document.getElementById("modal-del-erro");
  if(btnConf){ btnConf.disabled = true; btnConf.textContent = "Excluindo..."; }

  var modo = "individual";
  var opcoes = document.getElementById("modal-del-opcoes");
  if(!_leituraEhSub && opcoes && opcoes.style.display !== "none"){
    var radios = document.getElementsByName("modo_exclusao");
    for(var i = 0; i < radios.length; i++){
      if(radios[i].checked){ modo = radios[i].value; break; }
    }
  }

  fetch("/painel/leitura/" + encodeURIComponent(id) + "/deletar?modo=" + encodeURIComponent(modo), {
    method: "POST",
    headers: { "Accept": "application/json" }
  }).then(function(res){
    if(!res.ok){
      return res.json().then(function(j){ throw new Error(j.detail || ("Erro " + res.status)); })
             .catch(function(e){ throw new Error(e.message || ("Erro ao excluir (" + res.status + ")")); });
    }
    return res.json();
  }).then(function(data){
    fecharModalExcluir();
    if(window.location.pathname.indexOf("/painel/leitura/") === 0){
      window.location.href = "/painel#aba-leituras";
      return;
    }

    if(modo === "todos"){
      var mainRow = document.getElementById("row-pessoa-" + id);
      var subRows = document.querySelectorAll(".grupo-" + id);
      if(mainRow){
        mainRow.style.transition = "opacity 0.25s ease, transform 0.25s ease";
        mainRow.style.opacity = "0";
        mainRow.style.transform = "translateX(20px)";
        setTimeout(function(){ if(mainRow.parentNode) mainRow.parentNode.removeChild(mainRow); }, 260);
      }
      subRows.forEach(function(sr){
        sr.style.transition = "opacity 0.25s ease, transform 0.25s ease";
        sr.style.opacity = "0";
        setTimeout(function(){ if(sr.parentNode) sr.parentNode.removeChild(sr); }, 260);
      });
      atualizarAposExclusaoGrupo(data.removidos ? data.removidos.length : 1, true);
    } else {
      var row = document.getElementById("row-leitura-" + id) || document.getElementById("row-pessoa-" + id);
      if(row){
        row.style.transition = "opacity 0.25s ease, transform 0.25s ease";
        row.style.opacity = "0";
        setTimeout(function(){ if(row.parentNode) row.parentNode.removeChild(row); }, 260);
      }
      atualizarAposExclusaoGrupo(1, !_leituraEhSub);
    }
    mostrarToast("Registro(s) excluído(s) com sucesso!");
  }).catch(function(err){
    if(btnConf){ btnConf.disabled = false; btnConf.textContent = "Sim, Excluir"; }
    if(elErro){
      elErro.style.display = "block";
      elErro.textContent = err.message || "Não foi possível excluir o registro.";
    }
  });
}
function atualizarAposExclusaoGrupo(qtdRemovida, ehPessoaInteira){
  var badges = document.querySelectorAll(".btn-filtro-leituras .badge-count");
  if(badges.length >= 2){
    var bTodos = badges[0];
    var nTodos = Math.max(0, parseInt(bTodos.textContent || "0", 10) - (ehPessoaInteira ? 1 : 0));
    bTodos.textContent = nTodos;
  }
  var sub = document.getElementById("sub-leituras-info");
  if(sub){
    var b = sub.querySelector("b");
    if(b && ehPessoaInteira){
      var cur = Math.max(0, parseInt(b.textContent || "0", 10) - 1);
      b.textContent = cur;
    }
  }
}
function mostrarToast(msg){
  var t = document.getElementById("painel-toast");
  if(!t){
    t = document.createElement("div");
    t.id = "painel-toast";
    t.className = "painel-toast";
    document.body.appendChild(t);
  }
  t.textContent = msg;
  t.classList.add("on");
  setTimeout(function(){ t.classList.remove("on"); }, 3200);
}

var _ws = null;
var _wsRetryTimer = null;

function conectarWebSocketPainel(){
  if(typeof WebSocket === "undefined") return;
  if(_ws && (_ws.readyState === WebSocket.OPEN || _ws.readyState === WebSocket.CONNECTING)) return;
  var loc = window.location;
  var proto = loc.protocol === "https:" ? "wss:" : "ws:";
  var url = proto + "//" + loc.host + "/painel/ws";
  if(window._wsToken){
    url += "?token=" + encodeURIComponent(window._wsToken);
  }
  try{
    _ws = new WebSocket(url);
  }catch(e){
    atualizarStatusWS(false);
    reagendarWS();
    return;
  }

  _ws.onopen = function(){
    atualizarStatusWS(true);
    if(_ws._pingTimer) clearInterval(_ws._pingTimer);
    _ws._pingTimer = setInterval(function(){
      if(_ws && _ws.readyState === WebSocket.OPEN){
        try{ _ws.send("ping"); }catch(e){}
      }
    }, 25000);
  };

  _ws.onmessage = function(evt){
    try{
      if(evt.data === "pong") return;
      var msg = JSON.parse(evt.data);
      processarMensagemTempoReal(msg);
    }catch(e){}
  };

  _ws.onclose = function(){
    atualizarStatusWS(false);
    if(_ws && _ws._pingTimer) clearInterval(_ws._pingTimer);
    _ws = null;
    reagendarWS();
  };

  _ws.onerror = function(){
    atualizarStatusWS(false);
  };
}

function reagendarWS(){
  if(_wsRetryTimer) clearTimeout(_wsRetryTimer);
  _wsRetryTimer = setTimeout(conectarWebSocketPainel, 4000);
}

function atualizarStatusWS(conectado){
  var el = document.getElementById("ws-status");
  if(!el) return;
  if(conectado){
    el.className = "ws-status conectado";
    el.textContent = "● Ao vivo conectado";
    el.title = "WebSocket conectado: atualizações de leads em tempo real ativas";
  }else{
    el.className = "ws-status desconectado";
    el.textContent = "○ Reconectando...";
    el.title = "Tentando reconectar ao servidor para atualizações em tempo real";
  }
}

function flashElemento(el){
  if(!el) return;
  el.classList.remove("tr-flash");
  void el.offsetWidth;
  el.classList.add("tr-flash");
  setTimeout(function(){ el.classList.remove("tr-flash"); }, 2600);
}

function processarMensagemTempoReal(msg){
  if(!msg || !msg.tipo) return;

  if(msg.tipo === "status_compra"){
    aplicarStatusCompraNoDOM(msg.leitura_id, msg.comprou, msg.total_comprou);
    return;
  }

  var bVivo = document.getElementById("badge-count-vivo");
  if(bVivo && msg.total_ao_vivo !== undefined){
    bVivo.textContent = msg.total_ao_vivo;
  }

  if(msg.tipo === "snapshot"){
    if(Array.isArray(msg.ao_vivo)){
      var lidsAtivos = {};
      var sidsAtivos = {};
      msg.ao_vivo.forEach(function(item){
        if(item.leitura_id) lidsAtivos[item.leitura_id] = item;
        if(item.sid) sidsAtivos[item.sid] = item;
      });
      document.querySelectorAll("tr.tr-pessoa").forEach(function(row){
        var id = row.id.replace("row-pessoa-", "");
        var sid = row.getAttribute("data-sid") || "";
        var atv = lidsAtivos[id] || sidsAtivos[sid];
        if(atv && atv.ativo !== false){
          row.setAttribute("data-ao-vivo", "1");
          var liveTag = document.getElementById("live-tag-" + id);
          if(liveTag){ liveTag.style.display = "inline-flex"; }
          if(atv.rotulo){
            var tagEtapa = document.getElementById("tag-etapa-" + id);
            if(tagEtapa){
              tagEtapa.textContent = atv.rotulo;
              if(atv.tela === 10) tagEtapa.classList.add("oferta");
            }
          }
          if(atv.checkout){
            row.setAttribute("data-checkout", "1");
            var tagChk = document.getElementById("tag-checkout-" + id);
            if(tagChk){
              tagChk.className = "tag-checkout sim";
              tagChk.textContent = "✦ SIM";
            }
          }
        }
      });
    }
    return;
  }

  var lid = msg.leitura_id;
  var sid = msg.sid;
  var row = null;
  if(lid){
    row = document.getElementById("row-pessoa-" + lid) || document.getElementById("row-leitura-" + lid);
  }
  if(!row && sid){
    row = document.querySelector('tr.tr-pessoa[data-sid="' + sid + '"]');
  }

  if(msg.tipo === "progresso" || msg.tipo === "checkout" || msg.tipo === "presenca"){
    if(row){
      var rowId = row.id.replace("row-pessoa-", "").replace("row-leitura-", "");
      if(msg.rotulo){
        var tagEtapa = document.getElementById("tag-etapa-" + rowId);
        if(tagEtapa){
          tagEtapa.textContent = msg.rotulo;
          if(msg.tela === 10) tagEtapa.classList.add("oferta");
        }
      }
      if(msg.checkout){
        row.setAttribute("data-checkout", "1");
        var tagChk = document.getElementById("tag-checkout-" + rowId);
        if(tagChk){
          tagChk.className = "tag-checkout sim";
          tagChk.textContent = "✦ SIM";
        }
        var bChk = document.getElementById("badge-count-checkout");
        if(bChk && !row._jaContadoChk){
          row._jaContadoChk = true;
          var cur = parseInt(bChk.textContent || "0", 10);
          bChk.textContent = cur + 1;
        }
      }
      var liveTag = document.getElementById("live-tag-" + rowId);
      if(msg.ativo !== false){
        row.setAttribute("data-ao-vivo", "1");
        if(liveTag) liveTag.style.display = "inline-flex";
      }else{
        row.setAttribute("data-ao-vivo", "0");
        if(liveTag) liveTag.style.display = "none";
      }
      flashElemento(row);
    }
  } else if(msg.tipo === "contato_atualizado"){
    if(row && msg.whatsapp){
      var tdWa = row.querySelector("td:nth-child(7)");
      if(tdWa){
        var limpo = (msg.whatsapp || "").replace(/\D/g, "");
        var linkW = (limpo.length === 10 || limpo.length === 11) ? ("55" + limpo) : limpo;
        tdWa.innerHTML = '<a href="https://wa.me/' + linkW + '" target="_blank" rel="noopener" style="color:var(--green);text-decoration:underline;">' + msg.whatsapp + '</a>';
        flashElemento(row);
      }
    }
  } else if(msg.tipo === "nova_leitura"){
    var d = msg.dados || {};
    var newLid = msg.leitura_id || d.id;
    var existingRow = document.getElementById("row-pessoa-" + newLid);
    if(!existingRow){
      var bTodos = document.getElementById("badge-count-todos");
      if(bTodos){
        var curT = parseInt(bTodos.textContent || "0", 10);
        bTodos.textContent = curT + 1;
      }
      var tbody = document.getElementById("tbody-leituras");
      if(tbody){
        var tr = document.createElement("tr");
        tr.id = "row-pessoa-" + newLid;
        tr.className = "tr-pessoa";
        tr.setAttribute("data-checkout", "0");
        tr.setAttribute("data-ao-vivo", "1");
        if(msg.sid){ tr.setAttribute("data-sid", msg.sid); }
        var temWaLive = (d.whatsapp && d.whatsapp !== "—" && (d.whatsapp || "").replace(/\D/g, "").length >= 8);
        tr.setAttribute("data-whatsapp", temWaLive ? "1" : "0");
        var cidLive = d.cidade || {};
        var ufLive = (cidLive.uf || cidLive.nome || "").trim().toLowerCase();
        tr.setAttribute("data-uf", ufLive);

        var agoraStr = new Date().toLocaleTimeString("pt-BR", {hour:"2-digit", minute:"2-digit"});
        var waHtml = "—";
        if(d.whatsapp && d.whatsapp !== "—"){
          var waL = (d.whatsapp || "").replace(/\D/g, "");
          var waLink = (waL.length === 10 || waL.length === 11) ? ("55" + waL) : waL;
          waHtml = '<a href="https://wa.me/' + waLink + '" target="_blank" rel="noopener" style="color:var(--green);text-decoration:underline;">' + d.whatsapp + '</a>';
        }
        var veredito = d.veredito || {};
        var nasc = d.nascimento || {};
        var cid = d.cidade || {};
        var nascStr = (nasc.dia && nasc.mes) ? (String(nasc.dia).padStart(2,"0") + "/" + String(nasc.mes).padStart(2,"0") + "/" + String(nasc.ano || "").slice(-2)) : "—";
        var horaStr = nasc.hora !== undefined ? (String(nasc.hora).padStart(2,"0") + "h" + String(nasc.minuto || 0).padStart(2,"0")) : "desconhecida";

        var nomeEsc = (d.nome_completo || "—").replace(/</g, "&lt;");
        var nomeJs = nomeEsc.replace(/'/g, "\\'");

        tr.innerHTML = '<td class="td-chk"><input type="checkbox" class="chk-selecao chk-contato" data-id="' + newLid + '" data-nome="' + nomeJs + '" onchange="toggleContatoIndividual(this)" title="Selecionar ' + nomeJs + '"></td>'
          + '<td><a href="/painel/leitura/' + newLid + '">' + newLid.substring(0, 15) + '</a></td>'
          + '<td><span style="white-space:nowrap;">' + agoraStr + '</span></td>'
          + '<td><span style="white-space:nowrap;">' + agoraStr + '</span></td>'
          + '<td><span class="tag-etapa" id="tag-etapa-' + newLid + '">Tela 7 (Leitura)</span> <span class="tag-ao-vivo" id="live-tag-' + newLid + '">🟢 Ao vivo</span></td>'
          + '<td><span class="tag-checkout nao" id="tag-checkout-' + newLid + '">Não</span></td>'
          + '<td>' + nomeEsc + '</td>'
          + '<td>' + waHtml + '</td>'
          + '<td>' + nascStr + '</td>'
          + '<td>' + (cid.uf || cid.nome || "—") + '</td>'
          + '<td>' + ((d.quiz && d.quiz.area) || "—") + '</td>'
          + '<td>' + (veredito.tipo || "—") + '</td>'
          + '<td>' + (veredito.casa_eleita_real ? ("Casa " + veredito.casa_aberta) : "—") + '</td>'
          + '<td>' + horaStr + '</td>'
          + '<td>' + (d.tempo_quiz_ms ? Math.round(d.tempo_quiz_ms/1000) + 's' : '—') + '</td>'
          + '<td><button type="button" class="btn-del" onclick="abrirModalExcluir(\'' + newLid + '\', \'' + nomeJs + '\', 1, \'[]\', false);" title="Excluir">🗑️ Excluir</button></td>';

        if(window._contatosExportacao){
          window._contatosExportacao[newLid] = {
            id: newLid,
            chegou_em_bsb: agoraStr,
            gravado_em_bsb: agoraStr,
            etapa: "Tela 7 (Leitura)",
            checkout: "NÃO",
            comprou: "NÃO",
            nome: d.nome_completo || "—",
            whatsapp: d.whatsapp || "—",
            nascimento: nascStr,
            hora_nasc: horaStr,
            cidade: cid.nome || "—",
            uf: cid.uf || "—",
            pais: cid.pais || "Brasil",
            area: (d.quiz && d.quiz.area) || "—",
            cenario: veredito.tipo || "—",
            casa: veredito.casa_eleita_real ? ("Casa " + veredito.casa_aberta) : "—",
            tempo_quiz: d.tempo_quiz_ms ? Math.round(d.tempo_quiz_ms/1000) + 's' : '—',
            total_envios: 1
          };
        }

        tbody.insertBefore(tr, tbody.firstChild);
        flashElemento(tr);
        atualizarContadorSelecao();
        mostrarToast("Nova leitura recebida: " + (d.nome_completo || "Novo visitante"));
      }
    }
  }
}

(function(){
  vincularAbas();
  var hash=(location.hash||"").replace("#","");
  var salva="";try{salva=localStorage.getItem("painel_aba_ativa");}catch(e){}
  var alvo=hash||salva;
  if(alvo&&document.getElementById(alvo)){window.abrirAba(alvo);}
  atualizarLinksPresetsAba();
  iniciarArrastoScroll();
  inicializarDropzoneCSV();
  conectarWebSocketPainel();
  aplicarSelecaoNoDOM();
})();
"""


def _tabela(cabecalhos: list[str], linhas: list[list[str]], classes: str = "",
            tr_attrs: Optional[list[str]] = None, tbody_id: str = "",
            wrap_class: str = "tbl-wrap") -> str:
    if not linhas:
        return '<p class="vazio">Ainda sem dados neste período.</p>'
    ths = []
    for h in cabecalhos:
        if h == "[sel]":
            ths.append('<th class="th-chk"><input type="checkbox" id="chk-selecionar-todos-topo" class="chk-selecao" onchange="toggleSelecionarTodos(this)" title="Selecionar todos os contatos visíveis"></th>')
        else:
            cls_n = "n" if h.startswith("#") else ""
            ths.append(f'<th class="{cls_n}">{html.escape(h.lstrip("#"))}</th>')
    th = "".join(ths)
    tr = ""
    for idx, l in enumerate(linhas):
        extra = f" {tr_attrs[idx]}" if tr_attrs and idx < len(tr_attrs) else ""
        tds_list = []
        for h_idx, (h, c) in enumerate(zip(cabecalhos, l)):
            cls_td = "td-chk" if h == "[sel]" else ("n" if h.startswith("#") else "")
            td_class_attr = f' class="{cls_td}"' if cls_td else ""
            tds_list.append(f'<td{td_class_attr}>{c}</td>')
        tds = "".join(tds_list)
        tr += f"<tr{extra}>{tds}</tr>"
    tbody_attr = f' id="{tbody_id}"' if tbody_id else ""
    return f'<div class="{wrap_class}"><table class="{classes}"><thead><tr>{th}</tr></thead><tbody{tbody_attr}>{tr}</tbody></table></div>'


def _modal_confirmar_exclusao() -> str:
    return (
        '<div id="modal-excluir-backdrop" class="modal-backdrop">'
        '  <div class="modal-card" role="dialog" aria-modal="true" aria-labelledby="modal-del-titulo">'
        '    <div class="modal-icone">⚠️</div>'
        '    <h3 id="modal-del-titulo" class="modal-titulo">Confirmar Exclusão</h3>'
        '    <p class="modal-texto">'
        '      Deseja realmente excluir dados de <b id="modal-del-nome">—</b>?'
        '      <br><span id="modal-del-id" class="modal-id">ID: —</span>'
        '    </p>'
        '    <div id="modal-del-opcoes" class="modal-opcoes-excluir" style="display:none;">'
        '      <label><input type="radio" name="modo_exclusao" value="todos" checked> <span>Excluir <b>todos os <span id="modal-del-total-envios"></span> envios</b> desta pessoa</span></label>'
        '      <label><input type="radio" name="modo_exclusao" value="individual"> <span>Excluir apenas o <b>envio mais recente</b> (<span id="modal-del-id-curto"></span>)</span></label>'
        '    </div>'
        '    <span class="modal-aviso">Esta ação é irreversível e removerá os dados selecionados do sistema.</span>'
        '    <div id="modal-del-erro" class="modal-erro" style="display:none;"></div>'
        '    <div class="modal-acoes">'
        '      <button type="button" class="btn-modal-cancelar" onclick="fecharModalExcluir()">Cancelar</button>'
        '      <button type="button" id="btn-modal-confirmar" class="btn-modal-confirmar" onclick="executarExclusao()">Sim, Excluir</button>'
        '    </div>'
        '  </div>'
        '</div>'
    )


def _modal_confirmar_compra() -> str:
    return (
        '<div id="modal-compra-backdrop" class="modal-backdrop">'
        '  <div id="modal-compra-card" class="modal-card modal-card-compra" role="dialog" aria-modal="true" aria-labelledby="modal-compra-titulo">'
        '    <button type="button" class="modal-fechar-btn" onclick="fecharModalCompra()" title="Fechar">✕</button>'
        '    <div id="modal-compra-icone-wrap" class="modal-icone-wrap">'
        '      <span id="modal-compra-icone">💰</span>'
        '    </div>'
        '    <h3 id="modal-compra-titulo" class="modal-titulo">Confirmar Compra do Produto</h3>'
        '    <p class="modal-texto">'
        '      <span id="modal-compra-pergunta">Deseja marcar que este contato comprou o produto?</span>'
        '      <br><b id="modal-compra-nome" style="color:var(--amber);font-size:15px;display:inline-block;margin-top:6px;">—</b>'
        '    </p>'
        '    <div class="modal-info-box">'
        '      <span id="modal-compra-id" class="modal-id">ID: —</span>'
        '      <div id="modal-compra-desc" class="modal-subtexto">Ao confirmar, o contato receberá o selo ✅ Comprou e será contabilizado no filtro de compradores.</div>'
        '    </div>'
        '    <div id="modal-compra-erro" class="modal-erro" style="display:none;"></div>'
        '    <div class="modal-acoes">'
        '      <button type="button" class="btn-modal-cancelar" onclick="fecharModalCompra()">Cancelar</button>'
        '      <button type="button" id="btn-modal-confirmar-compra" class="btn-modal-confirmar-compra" onclick="executarConfirmacaoCompra()">Sim, Marcar Compra</button>'
        '    </div>'
        '  </div>'
        '</div>'
    )


def _modal_importar_csv() -> str:
    return (
        '<div id="modal-importar-csv-backdrop" class="modal-backdrop">'
        '  <div id="modal-importar-csv-card" class="modal-card modal-card-compra" role="dialog" aria-modal="true" aria-labelledby="modal-importar-titulo">'
        '    <button type="button" class="modal-fechar-btn" onclick="fecharModalImportarCSV()" title="Fechar">✕</button>'
        '    <div class="modal-icone-wrap">'
        '      <span id="modal-importar-icone">📤</span>'
        '    </div>'
        '    <h3 id="modal-importar-titulo" class="modal-titulo">Importar Contatos via CSV</h3>'
        '    <p class="modal-texto">'
        '      Selecione uma planilha <b>.csv</b> para importar novos leads ou atualizar contatos existentes.'
        '    </p>'
        '    <div class="importar-csv-area" style="margin-top:14px;">'
        '      <input type="file" id="input-arquivo-csv" accept=".csv,text/csv" style="display:none;" onchange="arquivoCSVSelecionado(this)">'
        '      <div id="dropzone-csv" class="dropzone-csv" onclick="document.getElementById(\'input-arquivo-csv\').click()">'
        '        <div class="dropzone-icone">📁</div>'
        '        <div class="dropzone-texto" id="dropzone-texto">Clique ou arraste o arquivo CSV aqui</div>'
        '        <div class="dropzone-detalhe" id="dropzone-detalhe">Compatível com Excel, Google Sheets e CRM (UTF-8, Latin-1, sep: ; ou ,)</div>'
        '      </div>'
        '      <div class="importar-opcoes" style="margin-top:14px;text-align:left;">'
        '        <label style="display:flex;align-items:center;gap:8px;font-size:12.5px;color:var(--sand);cursor:pointer;">'
        '          <input type="checkbox" id="chk-importar-atualizar" checked style="accent-color:var(--amber);width:16px;height:16px;">'
        '          <span>Atualizar contatos existentes caso o ID já exista</span>'
        '        </label>'
        '      </div>'
        '      <div id="modal-importar-status" class="modal-importar-status" style="display:none;margin-top:14px;"></div>'
        '      <div id="modal-importar-erro" class="modal-erro" style="display:none;margin-top:14px;"></div>'
        '    </div>'
        '    <div class="modal-acoes" style="margin-top:18px;">'
        '      <button type="button" class="btn-modal-cancelar" onclick="fecharModalImportarCSV()">Cancelar</button>'
        '      <button type="button" id="btn-modal-enviar-csv" class="btn-modal-confirmar-compra" onclick="executarImportacaoCSV()" disabled>Iniciar Importação</button>'
        '    </div>'
        '  </div>'
        '</div>'
    )




def obter_progresso_leituras(itens: list[tuple[str, dict]]) -> dict[str, dict]:
    """Mapeia cada leitura para (max_tela, rotulo, checkout).

    Combina os dados salvos no próprio JSON da leitura com os eventos registrados
    em DIR_EVENTOS para as datas correspondentes.
    """
    progresso: dict[str, dict] = {}
    sids_map: dict[str, list[str]] = {}
    datas_pesquisa: set[date] = set()

    for leitura_id, d in itens:
        etapa_salva = int(d.get("etapa_max") or 7)
        checkout_salvo = bool(d.get("checkout") or False)
        sid = str(d.get("cliente_id") or "").strip()

        progresso[leitura_id] = {
            "max_tela": etapa_salva,
            "rotulo": d.get("etapa_nome") or registro.ETAPAS_ROTULOS.get(etapa_salva, f"Tela {etapa_salva}"),
            "checkout": checkout_salvo,
            "sid": sid,
        }
        if sid:
            sids_map.setdefault(sid, []).append(leitura_id)

        dt_leitura = None
        gravado_em = d.get("gravado_em")
        if gravado_em:
            try:
                dt_leitura = datetime.fromisoformat(gravado_em).date()
            except Exception:
                pass
        if not dt_leitura and len(leitura_id) >= 8 and leitura_id[:8].isdigit():
            try:
                dt_leitura = datetime.strptime(leitura_id[:8], "%Y%m%d").date()
            except Exception:
                pass
        if not dt_leitura:
            dt_leitura = hoje_bsb()

        datas_pesquisa.add(dt_leitura)
        datas_pesquisa.add(dt_leitura - timedelta(days=1))
        datas_pesquisa.add(dt_leitura + timedelta(days=1))

    lids_set = set(progresso.keys())
    if not lids_set and not sids_map:
        return progresso

    for d_pesq in sorted(datas_pesquisa):
        arq_ev = config.DIR_EVENTOS / f"{d_pesq:%Y-%m-%d}.jsonl"
        if not arq_ev.exists():
            continue
        try:
            with open(arq_ev, encoding="utf-8") as f:
                for linha in f:
                    linha = linha.strip()
                    if not linha:
                        continue
                    try:
                        ev = json.loads(linha)
                    except Exception:
                        continue
                    ev_sid = str(ev.get("sid") or "").strip()
                    props = ev.get("props") or {}
                    ev_lid = str(props.get("leitura_id") or "").strip()
                    evt = ev.get("evt")

                    alvos: list[str] = []
                    if ev_lid and ev_lid in lids_set:
                        alvos.append(ev_lid)
                        if ev_sid and ev_sid not in sids_map:
                            sids_map.setdefault(ev_sid, []).append(ev_lid)
                    elif ev_sid and ev_sid in sids_map:
                        alvos.extend(sids_map[ev_sid])
                    elif evt == "leitura_entregue":
                        lid_entregue = str(props.get("leitura_id") or "").strip()
                        if lid_entregue in lids_set:
                            alvos.append(lid_entregue)
                            if ev_sid:
                                sids_map.setdefault(ev_sid, []).append(lid_entregue)

                    if not alvos:
                        continue

                    for alvo_lid in alvos:
                        info = progresso[alvo_lid]
                        if evt == "tela":
                            for k in ("para", "de"):
                                val = props.get(k)
                                if isinstance(val, int) and 0 <= val <= 10:
                                    if val > info["max_tela"]:
                                        info["max_tela"] = val
                        elif evt == "oferta_clique":
                            info["checkout"] = True
                            if info["max_tela"] < 10:
                                info["max_tela"] = 10
                        elif evt == "saida":
                            t_saida = props.get("tela")
                            if isinstance(t_saida, int) and 0 <= t_saida <= 10:
                                if t_saida > info["max_tela"]:
                                    info["max_tela"] = t_saida
                        elif evt == "leitura_entregue":
                            if info["max_tela"] < 7:
                                info["max_tela"] = 7
        except Exception as err:
            logger.warning("Erro ao ler eventos em %s: %s", arq_ev.name, err)

    for lid, info in progresso.items():
        m = info["max_tela"]
        info["rotulo"] = registro.ETAPAS_ROTULOS.get(m, f"Tela {m}")

    return progresso


def _agrupar_leituras_por_pessoa(todos_dados: list[tuple[str, dict]],
                                 progresso_map: dict[str, dict]) -> list[dict]:
    """Agrupa submissões da mesma pessoa em grupos ordenados cronologicamente."""
    leads = []
    mapa_dados = {}
    for stem, d in todos_dados:
        mapa_dados[stem] = d
        if (d.get("nome_completo") or "").strip().lower() == "pessoa de teste":
            continue
        nome = " ".join((d.get("nome_completo") or "").strip().lower().split())
        n = d.get("nascimento") or {}
        dia, mes, ano = n.get("dia"), n.get("mes"), n.get("ano")
        dn = f"{dia}/{mes}/{ano}" if dia and mes and ano else ""
        wa = re.sub(r"\D", "", str(d.get("whatsapp") or ""))
        if len(wa) >= 10 and wa.startswith("55"):
            wa = wa[2:]
        cid = str(d.get("cliente_id") or "").strip()
        leads.append({
            "stem": stem,
            "nome_norm": nome,
            "dn": dn,
            "wa": wa if len(wa) >= 8 else "",
            "cid": cid,
        })

    n_leads = len(leads)
    if n_leads == 0:
        return []

    parent = list(range(n_leads))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    for i in range(n_leads):
        for j in range(i + 1, n_leads):
            l1, l2 = leads[i], leads[j]
            if l1["wa"] and l2["wa"] and l1["wa"] == l2["wa"]:
                union(i, j)
            elif l1["cid"] and l2["cid"] and l1["cid"] == l2["cid"]:
                union(i, j)
            elif (l1["nome_norm"] and l2["nome_norm"] and l1["dn"] and l2["dn"]
                  and l1["nome_norm"] == l2["nome_norm"] and l1["dn"] == l2["dn"]):
                union(i, j)

    clusters: dict[int, list[str]] = {}
    for i in range(n_leads):
        r = find(i)
        clusters.setdefault(r, []).append(leads[i]["stem"])

    grupos: list[dict] = []
    for stems in clusters.values():
        stems_ordenados = sorted(stems, reverse=True)
        principal_stem = stems_ordenados[0]
        d_principal = mapa_dados[principal_stem]

        teve_checkout = any(progresso_map.get(s, {}).get("checkout") for s in stems_ordenados)
        comprou = any(bool(mapa_dados[s].get("comprou")) for s in stems_ordenados)
        max_tela = max((progresso_map.get(s, {}).get("max_tela", 7) for s in stems_ordenados), default=7)
        rotulo_etapa = registro.ETAPAS_ROTULOS.get(max_tela, f"Tela {max_tela}")

        # WhatsApp consolidado
        wa_consolidado = d_principal.get("whatsapp")
        if not wa_consolidado or wa_consolidado == "—":
            for s in stems_ordenados[1:]:
                w_alt = mapa_dados[s].get("whatsapp")
                if w_alt and w_alt != "—":
                    wa_consolidado = w_alt
                    break

        wa_digitos = re.sub(r"\D", "", str(wa_consolidado or ""))
        tem_wa = bool(wa_consolidado and str(wa_consolidado).strip() not in ("", "—", "-") and len(wa_digitos) >= 8)

        # Nome consolidado
        nome_consolidado = d_principal.get("nome_completo") or "—"
        if nome_consolidado in ("—", ""):
            for s in stems_ordenados[1:]:
                n_alt = mapa_dados[s].get("nome_completo")
                if n_alt and n_alt not in ("—", ""):
                    nome_consolidado = n_alt
                    break

        grupos.append({
            "id_grupo": principal_stem,
            "stem_principal": principal_stem,
            "d_principal": d_principal,
            "nome_completo": nome_consolidado,
            "whatsapp": wa_consolidado,
            "tem_whatsapp": tem_wa,
            "nascimento": d_principal.get("nascimento") or {},
            "cidade": d_principal.get("cidade") or {},
            "teve_checkout": teve_checkout,
            "comprou": comprou,
            "max_tela": max_tela,
            "rotulo_etapa": rotulo_etapa,
            "total_envios": len(stems_ordenados),
            "todos_ids": stems_ordenados,
            "outras_leituras": [(s, mapa_dados[s]) for s in stems_ordenados[1:]],
        })

    grupos.sort(key=lambda g: g["stem_principal"], reverse=True)
    return grupos


def _contagens_leituras_dados(dados: list[tuple[str, dict]]) -> tuple[dict[str, int], int]:
    grupos = _agrupar_leituras_por_pessoa(dados, {})
    mapa_contagens = {}
    for g in grupos:
        for s in g["todos_ids"]:
            mapa_contagens[s] = g["total_envios"]
    return mapa_contagens, len(grupos)


def _contagens_leituras(arquivos: list[Path]) -> tuple[dict[str, int], int]:
    dados = []
    for arq in arquivos:
        try:
            dados.append((arq.stem, json.loads(arq.read_text(encoding="utf-8"))))
        except Exception:
            continue
    return _contagens_leituras_dados(dados)


class ResultadoTabela(tuple):
    def __new__(cls, corpo, total_exibidos, total_pags, total_pessoas, total_chk, total_geral, total_ao_vivo=0, total_comprou=0, total_whatsapp=0, lista_ufs=None):
        return super().__new__(cls, (corpo, total_exibidos, total_pags, total_pessoas, total_chk, total_geral))

    def __init__(self, corpo, total_exibidos, total_pags, total_pessoas, total_chk, total_geral, total_ao_vivo=0, total_comprou=0, total_whatsapp=0, lista_ufs=None):
        self.total_ao_vivo = total_ao_vivo
        self.total_comprou = total_comprou
        self.total_whatsapp = total_whatsapp
        self.lista_ufs = lista_ufs or []


def _tabela_leituras(pagina: int = 0, por_pagina: int = 20,
                     so_checkout: bool = False,
                     so_ao_vivo: bool = False,
                     so_comprou: bool = False,
                     so_whatsapp: bool = False,
                     uf: Optional[str] = None,
                     de: Optional[date] = None,
                     ate: Optional[date] = None) -> ResultadoTabela:
    arquivos = sorted(config.DIR_LEITURAS.glob("*.json"), reverse=True)

    todos_dados: list[tuple[str, dict]] = []
    for arq in arquivos:
        try:
            d = json.loads(arq.read_text(encoding="utf-8"))
        except Exception:
            continue
        if (d.get("nome_completo") or "").strip().lower() == "pessoa de teste":
            continue          # fixtures da suite de testes

        if de and ate:
            dt_ch = obter_data_chegada_leitura(d, arq.stem)
            if dt_ch and not (de <= dt_ch <= ate):
                continue

        todos_dados.append((arq.stem, d))

    total_leituras_geral = len(todos_dados)

    # Identifica progresso e checkout de todas as leituras
    progresso_map = obter_progresso_leituras(todos_dados)
    total_leituras_checkout = sum(1 for stem, _ in todos_dados if progresso_map.get(stem, {}).get("checkout"))

    # Agrupa por pessoa única
    todos_grupos = _agrupar_leituras_por_pessoa(todos_dados, progresso_map)
    total_pessoas_geral = len(todos_grupos)
    total_pessoas_checkout = sum(1 for g in todos_grupos if g["teve_checkout"])

    # Coleta todas as UFs/Cidades preenchidas nos dados do período
    mapa_ufs: dict[str, int] = {}
    for g in todos_grupos:
        cid_g = g.get("cidade") or {}
        val_uf = str(cid_g.get("uf") or cid_g.get("nome") or "").strip()
        if val_uf and val_uf != "—":
            mapa_ufs[val_uf] = mapa_ufs.get(val_uf, 0) + 1
    lista_ufs = sorted(mapa_ufs.items(), key=lambda x: x[0].lower())

    # Identifica quem está ativo no momento (últimos 90 segundos)
    ativos = rastreador_presenca.obter_ativos(90.0)
    ids_ao_vivo = {str(a["leitura_id"]).strip() for a in ativos if a.get("leitura_id")}
    sids_ao_vivo = {str(a["sid"]).strip() for a in ativos if a.get("sid")}

    for g in todos_grupos:
        cid = str(g["d_principal"].get("cliente_id") or "").strip()
        g_cids = {cid} if cid else set()
        for _, sub_d in g["outras_leituras"]:
            sc = str(sub_d.get("cliente_id") or "").strip()
            if sc:
                g_cids.add(sc)
        g["ao_vivo"] = bool(set(g["todos_ids"]) & ids_ao_vivo or g_cids & sids_ao_vivo)

    total_pessoas_ao_vivo = sum(1 for g in todos_grupos if g["ao_vivo"])
    total_pessoas_comprou = sum(1 for g in todos_grupos if g.get("comprou"))
    total_pessoas_whatsapp = sum(1 for g in todos_grupos if g.get("tem_whatsapp"))

    if so_whatsapp:
        grupos_filtrados = [g for g in todos_grupos if g.get("tem_whatsapp")]
    elif so_comprou:
        grupos_filtrados = [g for g in todos_grupos if g.get("comprou")]
    elif so_ao_vivo:
        grupos_filtrados = [g for g in todos_grupos if g["ao_vivo"]]
    elif so_checkout:
        grupos_filtrados = [g for g in todos_grupos if g["teve_checkout"]]
    else:
        grupos_filtrados = todos_grupos

    if uf and uf.strip():
        uf_norm = uf.strip().lower()
        grupos_filtrados = [
            g for g in grupos_filtrados
            if str((g.get("cidade") or {}).get("uf") or (g.get("cidade") or {}).get("nome") or "").strip().lower() == uf_norm
        ]

    total_pessoas_exibidas = len(grupos_filtrados)
    total_leituras_exibidas = sum(g["total_envios"] for g in grupos_filtrados)

    total_paginas = max(1, (total_pessoas_exibidas + por_pagina - 1) // por_pagina)
    pagina_int = pagina.default if hasattr(pagina, "default") else int(pagina)
    pagina_ajustada = min(max(0, pagina_int), total_paginas - 1) if total_pessoas_exibidas > 0 else 0
    recorte_grupos = grupos_filtrados[pagina_ajustada * por_pagina:(pagina_ajustada + 1) * por_pagina]

    linhas = []
    tr_attrs = []
    dados_exportacao_map = {}

    for g in recorte_grupos:
        stem = g["stem_principal"]
        d = g["d_principal"]
        v, pr = d.get("veredito") or {}, d.get("precisao") or {}
        nasc = g["nascimento"]
        cid = g["cidade"]
        chegada_bsb, gerada_bsb = f_chegada_bsb(d, stem)
        rotulo_etapa = g["rotulo_etapa"]
        etapa_cls = "tag-etapa oferta" if g["max_tela"] == 10 else "tag-etapa"
        tag_live = f'<span class="tag-ao-vivo" id="live-tag-{stem}">🟢 Ao vivo</span>' if g["ao_vivo"] else f'<span class="tag-ao-vivo" id="live-tag-{stem}" style="display:none;">🟢 Ao vivo</span>'
        tag_etapa = f'<span class="{etapa_cls}" id="tag-etapa-{stem}">{html.escape(rotulo_etapa)}</span> {tag_live}'
        tag_chk = f'<span class="tag-checkout sim" id="tag-checkout-{stem}">✦ SIM</span>' if g["teve_checkout"] else f'<span class="tag-checkout nao" id="tag-checkout-{stem}">Não</span>'

        btn_acordeao = ""
        if g["total_envios"] > 1:
            btn_acordeao = (
                f' <button type="button" class="btn-acordeao" '
                f'onclick="toggleAcordeao(\'{html.escape(g["id_grupo"])}\', this);" '
                f'title="Ver todas as {g["total_envios"]} tentativas desta pessoa">'
                f'<span class="seta">▶</span> <span class="tag-rep" title="Preencheu o formulário {g["total_envios"]} vezes">{g["total_envios"]}x</span></button>'
            )

        g_comprou = bool(g.get("comprou"))
        tag_comprou = f'<span class="tag-comprou" id="tag-comprou-{stem}">✅ Comprou</span>' if g_comprou else f'<span class="tag-comprou" id="tag-comprou-{stem}" style="display:none;">✅ Comprou</span>'
        nome_cell = html.escape(g["nome_completo"]) + tag_comprou + btn_acordeao

        todos_ids_json = html.escape(json.dumps(g["todos_ids"])).replace("'", "&#39;")
        nome_js = html.escape(g["nome_completo"]).replace("'", "\\'")
        btn_del_principal = (
            f'<button type="button" class="btn-del" '
            f'onclick="abrirModalExcluir(\'{html.escape(stem)}\', \'{nome_js}\', {g["total_envios"]}, \'{todos_ids_json}\', false);" '
            f'title="Excluir dados desta pessoa">🗑️ Excluir</button>'
        )

        btn_compra_cls = "btn-compra comprou" if g_comprou else "btn-compra"
        btn_compra_txt = "✅ Comprou" if g_comprou else "💰 Comprou"
        btn_compra_title = "Compra confirmada. Clique para desmarcar." if g_comprou else "Clique para marcar que este contato comprou o produto."
        btn_compra_principal = (
            f'<button type="button" id="btn-compra-{stem}" class="{btn_compra_cls}" '
            f'onclick="abrirModalCompra(\'{html.escape(stem)}\', \'{nome_js}\', {1 if g_comprou else 0}, this);" '
            f'title="{btn_compra_title}">{btn_compra_txt}</button>'
        )
        acoes_principal = f'<div style="display:flex;gap:5px;align-items:center;">{btn_compra_principal}{btn_del_principal}</div>'

        cid_str = html.escape(str(g["d_principal"].get("cliente_id") or ""))
        uf_attr = html.escape(str(cid.get("uf") or cid.get("nome") or "").strip().lower())
        tr_attrs.append(f'id="row-pessoa-{stem}" class="tr-pessoa" data-checkout="{"1" if g["teve_checkout"] else "0"}" data-uf="{uf_attr}" data-ao-vivo="{"1" if g["ao_vivo"] else "0"}" data-comprou="{"1" if g_comprou else "0"}" data-whatsapp="{"1" if g.get("tem_whatsapp") else "0"}" data-sid="{cid_str}"')
        
        chk_principal = f'<input type="checkbox" class="chk-selecao chk-contato" data-id="{html.escape(stem)}" data-nome="{nome_js}" onchange="toggleContatoIndividual(this)" title="Selecionar {nome_js}">'
        linhas.append([
            chk_principal,
            f'<a href="/painel/leitura/{html.escape(stem)}">{html.escape(stem[:15])}</a>',
            f'<span style="white-space:nowrap;">{html.escape(chegada_bsb)}</span>',
            f'<span style="white-space:nowrap;">{html.escape(gerada_bsb)}</span>',
            tag_etapa,
            tag_chk,
            nome_cell,
            f_wa(g["whatsapp"]),
            f_data(nasc),
            html.escape(cid.get("uf") or cid.get("nome") or "—"),
            html.escape(str((d.get("quiz") or {}).get("area") or "—")),
            html.escape(str(v.get("tipo") or "—")),
            "—" if not v.get("casa_eleita_real") else f'Casa {v.get("casa_aberta")}',
            f_hora(nasc, pr),
            f_tempo(d.get("tempo_quiz_ms")),
            acoes_principal,
        ])

        dados_exportacao_map[stem] = {
            "id": stem,
            "chegou_em_bsb": chegada_bsb,
            "gravado_em_bsb": gerada_bsb,
            "etapa": rotulo_etapa,
            "checkout": "SIM" if g["teve_checkout"] else "NÃO",
            "comprou": "SIM" if g_comprou else "NÃO",
            "nome": g["nome_completo"],
            "whatsapp": g["whatsapp"] or "—",
            "nascimento": f_data(nasc),
            "hora_nasc": f_hora(nasc, pr),
            "cidade": cid.get("nome") or "—",
            "uf": cid.get("uf") or "—",
            "pais": cid.get("pais") or "Brasil",
            "area": str((d.get("quiz") or {}).get("area") or "—"),
            "cenario": str(v.get("tipo") or "—"),
            "casa": "—" if not v.get("casa_eleita_real") else f'Casa {v.get("casa_aberta")}',
            "tempo_quiz": f_tempo(d.get("tempo_quiz_ms")),
            "total_envios": g["total_envios"]
        }

        # Sub-linhas para tentativas anteriores do acordeão
        for sub_stem, sub_d in g["outras_leituras"]:
            sub_v, sub_pr = sub_d.get("veredito") or {}, sub_d.get("precisao") or {}
            sub_nasc = sub_d.get("nascimento") or {}
            sub_cid = sub_d.get("cidade") or {}
            sub_chegada_bsb, sub_gerada_bsb = f_chegada_bsb(sub_d, sub_stem)
            sub_prog = progresso_map.get(sub_stem, {"max_tela": 7, "rotulo": "Tela 7 (Leitura)", "checkout": False})
            sub_rotulo_etapa = sub_prog["rotulo"]
            sub_etapa_cls = "tag-etapa oferta" if sub_prog["max_tela"] == 10 else "tag-etapa"
            sub_cid_str = html.escape(str(sub_d.get("cliente_id") or ""))
            sub_ao_vivo = (sub_stem in ids_ao_vivo or (sub_cid_str and sub_cid_str in sids_ao_vivo))
            sub_tag_live = f'<span class="tag-ao-vivo" id="live-tag-{sub_stem}">🟢 Ao vivo</span>' if sub_ao_vivo else f'<span class="tag-ao-vivo" id="live-tag-{sub_stem}" style="display:none;">🟢 Ao vivo</span>'
            sub_tag_etapa = f'<span class="{sub_etapa_cls}" id="tag-etapa-{sub_stem}">{html.escape(sub_rotulo_etapa)}</span> {sub_tag_live}'
            sub_tag_chk = f'<span class="tag-checkout sim" id="tag-checkout-{sub_stem}">✦ SIM</span>' if sub_prog["checkout"] else f'<span class="tag-checkout nao" id="tag-checkout-{sub_stem}">Não</span>'

            sub_comprou = bool(sub_d.get("comprou"))
            btn_compra_sub_cls = "btn-compra comprou" if sub_comprou else "btn-compra"
            btn_compra_sub_txt = "✅" if sub_comprou else "💰"
            btn_compra_sub = (
                f'<button type="button" id="btn-compra-{sub_stem}" class="{btn_compra_sub_cls}" '
                f'onclick="abrirModalCompra(\'{html.escape(sub_stem)}\', \'{nome_js}\', {1 if sub_comprou else 0}, this);" '
                f'title="Marcar ou desmarcar compra">{btn_compra_sub_txt}</button>'
            )

            btn_del_sub = (
                f'<button type="button" class="btn-del" '
                f'onclick="abrirModalExcluir(\'{html.escape(sub_stem)}\', \'{nome_js}\', 1, \'[]\', true);" '
                f'title="Excluir apenas esta tentativa anterior">🗑️</button>'
            )
            acoes_sub = f'<div style="display:flex;gap:4px;align-items:center;">{btn_compra_sub}{btn_del_sub}</div>'

            sub_wa_digitos = re.sub(r"\D", "", str(sub_d.get("whatsapp") or ""))
            sub_tem_wa = bool(sub_d.get("whatsapp") and len(sub_wa_digitos) >= 8)

            sub_uf_attr = html.escape(str(sub_cid.get("uf") or sub_cid.get("nome") or "").strip().lower())
            tr_attrs.append(f'id="row-leitura-{sub_stem}" class="tr-subleitura grupo-{g["id_grupo"]}" data-uf="{sub_uf_attr}" style="display:none;" data-checkout="{"1" if sub_prog["checkout"] else "0"}" data-ao-vivo="{"1" if sub_ao_vivo else "0"}" data-comprou="{"1" if sub_comprou else "0"}" data-whatsapp="{"1" if sub_tem_wa else "0"}" data-sid="{sub_cid_str}"')
            linhas.append([
                '<span style="opacity:0.25;font-size:11px;display:inline-block;padding-left:4px;">↳</span>',
                f'<span style="padding-left:14px;"><a href="/painel/leitura/{html.escape(sub_stem)}" style="color:var(--sand2);">↳ {html.escape(sub_stem[:15])}</a></span>',
                f'<span style="white-space:nowrap;color:var(--sand2);">{html.escape(sub_chegada_bsb)}</span>',
                f'<span style="white-space:nowrap;color:var(--sand2);">{html.escape(sub_gerada_bsb)}</span>',
                sub_tag_etapa,
                sub_tag_chk,
                '<span style="color:var(--sand2);font-size:11.5px;padding-left:8px;">↳ tentativa anterior</span>',
                f_wa(sub_d.get("whatsapp")),
                f_data(sub_nasc),
                "—",
                html.escape(str((sub_d.get("quiz") or {}).get("area") or "—")),
                html.escape(str(sub_v.get("tipo") or "—")),
                "—" if not sub_v.get("casa_eleita_real") else f'Casa {sub_v.get("casa_aberta")}',
                f_hora(sub_nasc, sub_pr),
                f_tempo(sub_d.get("tempo_quiz_ms")),
                acoes_sub,
            ])

    btn_importar_html = (
        '    <button type="button" id="btn-importar-csv" class="btn-importar-csv" onclick="abrirModalImportarCSV()"'
        '      title="Importar contatos de uma planilha CSV">'
        '      📤 Importar CSV'
        '    </button>'
    )

    if not linhas:
        barra_vazio = (
            '<div class="barra-acoes-leituras" id="barra-acoes-leituras">'
            '  <div class="acoes-leituras-esquerda"></div>'
            '  <div class="acoes-leituras-direita">'
            f'  {btn_importar_html}'
            '  </div>'
            '</div>'
        )
        if so_whatsapp:
            corpo = barra_vazio + '<p class="vazio">Nenhum contato com WhatsApp registrado neste período.</p>'
        elif so_comprou:
            corpo = barra_vazio + '<p class="vazio">Nenhum comprador registrado neste período.</p>'
        elif so_ao_vivo:
            corpo = barra_vazio + '<p class="vazio">Nenhum visitante ativo navegando nas telas neste momento.</p>'
        elif so_checkout:
            corpo = barra_vazio + '<p class="vazio">Nenhum visitante foi ao checkout neste período.</p>'
        else:
            corpo = barra_vazio + '<p class="vazio">Nenhuma leitura encontrada neste período.</p>'
    else:
        btn_todos_filtro_html = ""
        if total_pessoas_exibidas > len(recorte_grupos):
            btn_todos_filtro_html = (
                f'    <button type="button" id="btn-sel-todos-filtro" class="btn-sel-todos-filtro" '
                f'      onclick="toggleSelecionarTodosFiltro()" '
                f'      title="Selecionar todos os {total_pessoas_exibidas} contatos deste filtro em todas as páginas">'
                f'      📋 Selecionar todos os <span class="num-total-filtro">{total_pessoas_exibidas}</span> contatos'
                f'    </button>'
            )

        banner_selecao_html = (
            f'<div id="banner-selecao-global" class="banner-selecao-global" style="display:none;" '
            f'  data-total-filtro="{total_pessoas_exibidas}" data-total-pagina="{len(recorte_grupos)}">'
            f'  <span id="txt-banner-selecao">Todos os <b>{len(recorte_grupos)}</b> contatos desta página estão selecionados.</span>'
            f'  <button type="button" id="btn-banner-acao" class="btn-link-banner" onclick="selecionarTodosFiltro()">'
            f'    👉 Selecionar todos os <b>{total_pessoas_exibidas}</b> contatos deste filtro'
            f'  </button>'
            f'</div>'
        )

        barra_acoes = (
            f'<div class="barra-acoes-leituras" id="barra-acoes-leituras" '
            f'  data-total-filtro="{total_pessoas_exibidas}" data-total-pagina="{len(recorte_grupos)}">'
            '  <div class="acoes-leituras-esquerda">'
            '    <label class="chk-label-todos">'
            '      <input type="checkbox" id="chk-selecionar-todos-barra" class="chk-selecao" onchange="toggleSelecionarTodos(this)">'
            '      <span id="txt-selecionar-todos">Selecionar todos da página</span>'
            '    </label>'
            f'  {btn_todos_filtro_html}'
            '    <span id="contador-selecao-wrap" class="contador-selecao-wrap" style="display:none;">'
            '      <span class="badge-sel-check">✓</span> <b id="contador-selecao-num">0</b> selecionados'
            '    </span>'
            '    <button type="button" id="btn-limpar-selecao" class="btn-limpar-selecao" style="display:none;" onclick="limparSelecao()" title="Limpar seleção de contatos">'
            '      ✕ Limpar'
            '    </button>'
            '  </div>'
            '  <div class="acoes-leituras-direita">'
            f'  {btn_importar_html}'
            '    <button type="button" id="btn-exportar-csv" class="btn-exportar-csv" onclick="exportarContatosCSV()"'
            '      title="Exportar contatos para planilha CSV compatível com Excel">'
            f'      📥 Exportar CSV <span id="btn-exportar-contagem">(todos: {total_pessoas_exibidas})</span>'
            '    </button>'
            '  </div>'
            '</div>'
            + banner_selecao_html
        )
        json_export = json.dumps(dados_exportacao_map)
        script_export = (
            f'<script>'
            f'window._contatosExportacao = Object.assign(window._contatosExportacao || {{}}, {json_export});'
            f'window._totalLeiturasFiltro = {total_pessoas_exibidas};'
            f'window._totalLeiturasPagina = {len(recorte_grupos)};'
            f'setTimeout(aplicarSelecaoNoDOM, 30);'
            f'</script>'
        )
        corpo = barra_acoes + _tabela([
            "[sel]", "id", "chegou ao quiz (bsb)", "preencheu dados (bsb)", "etapa alcançada", "checkout",
            "nome", "whatsapp", "nascimento", "uf", "área", "cenário", "casa", "hora nasc.", "tempo no quiz", "ações"
        ], linhas, tr_attrs=tr_attrs, tbody_id="tbody-leituras", wrap_class="tbl-wrap tbl-wrap-leituras") + script_export

    return ResultadoTabela(corpo, total_leituras_exibidas, total_paginas, total_pessoas_exibidas, total_pessoas_checkout, total_leituras_geral, total_pessoas_ao_vivo, total_pessoas_comprou, total_pessoas_whatsapp, lista_ufs)


def _dropdown_filtro_uf(lista_ufs: list[tuple[str, int]], uf_selecionado: Optional[str] = None) -> str:
    """Renderiza o dropdown de filtro por UF / Cidade para a aba de leituras."""
    if not lista_ufs:
        return ""
    options = ['<option value="">Todos os estados / UFs</option>']
    uf_sel_norm = (uf_selecionado or "").strip().lower()
    for nome_uf, count in lista_ufs:
        sel = ' selected' if nome_uf.strip().lower() == uf_sel_norm else ''
        options.append(f'<option value="{html.escape(nome_uf)}"{sel}>{html.escape(nome_uf)} ({count})</option>')

    return (
        '<div class="filtro-uf-wrap" title="Filtrar contatos pelo estado ou cidade preenchida">'
        '  <label for="select-filtro-uf" class="lbl-filtro-uf">📍 UF:</label>'
        '  <select id="select-filtro-uf" class="select-filtro-uf" onchange="filtrarPorUFClient(this.value)">'
        + "".join(options) +
        '  </select>'
        '</div>'
    )


def _barra_paginacao(pagina: int, total_arquivos: int, base_url: str, params: dict,
                     por_pagina: int = 20, param_nome: str = "pag_leituras",
                     hash_tab: str = "", rotulo_item: str = "leituras") -> str:
    if total_arquivos == 0:
        return ""
    total_paginas = max(1, (total_arquivos + por_pagina - 1) // por_pagina)
    pagina_int = pagina.default if hasattr(pagina, "default") else int(pagina)
    pagina = min(max(0, pagina_int), total_paginas - 1)

    inicio = pagina * por_pagina + 1
    fim = min((pagina + 1) * por_pagina, total_arquivos)
    info = f"Mostrando <b>{inicio}–{fim}</b> de <b>{total_arquivos}</b> {rotulo_item} · Página {pagina + 1} de {total_paginas}"

    def make_url(p: int) -> str:
        q = {k: v for k, v in params.items() if v is not None}
        q[param_nome] = p
        qs = "&".join(f"{k}={v}" for k, v in q.items())
        sep = "&" if "?" in base_url else "?"
        url = f"{base_url}{sep}{qs}" if qs else base_url
        if hash_tab and not url.endswith(hash_tab):
            url += hash_tab
        return url

    botoes = []
    # Botão Anterior
    if pagina > 0:
        botoes.append(f'<a class="pag-btn" href="{make_url(pagina - 1)}">← Anterior</a>')
    else:
        botoes.append('<span class="pag-btn disabled">← Anterior</span>')

    # Janela de até 5 páginas adjacentes
    p_ini = max(0, pagina - 2)
    p_fim = min(total_paginas, p_ini + 5)
    if p_fim - p_ini < 5:
        p_ini = max(0, p_fim - 5)

    if p_ini > 0:
        botoes.append(f'<a class="pag-btn" href="{make_url(0)}">1</a>')
        if p_ini > 1:
            botoes.append('<span class="pag-btn disabled">…</span>')

    for p_idx in range(p_ini, p_fim):
        if p_idx == pagina:
            botoes.append(f'<span class="pag-btn on">{p_idx + 1}</span>')
        else:
            botoes.append(f'<a class="pag-btn" href="{make_url(p_idx)}">{p_idx + 1}</a>')

    if p_fim < total_paginas:
        if p_fim < total_paginas - 1:
            botoes.append('<span class="pag-btn disabled">…</span>')
        botoes.append(f'<a class="pag-btn" href="{make_url(total_paginas - 1)}">{total_paginas}</a>')

    # Botão Próxima
    if pagina < total_paginas - 1:
        botoes.append(f'<a class="pag-btn" href="{make_url(pagina + 1)}">Próxima →</a>')
    else:
        botoes.append('<span class="pag-btn disabled">Próxima →</span>')

    return (f'<div class="paginacao">'
            f'<span class="pag-info">{info}</span>'
            f'<div class="pag-links">{"".join(botoes)}</div>'
            f'</div>')


@router.get("/painel", response_class=HTMLResponse)
def painel(request: Request, _=Depends(exigir_senha),
           de: Optional[str] = None, ate: Optional[str] = None,
           dias: int = Query(7, ge=1, le=365),
           bots: int = 0, teste: int = 0,
           pag_leituras: int = Query(0, ge=0),
           so_checkout: int = 0,
           so_ao_vivo: int = 0,
           so_comprou: int = 0,
           so_whatsapp: int = 0,
           uf: Optional[str] = None):
    dias_int = dias.default if hasattr(dias, "default") else int(dias)
    pag_leituras_int = pag_leituras.default if hasattr(pag_leituras, "default") else int(pag_leituras)
    d1, d2 = _periodo(de, ate, dias_int)
    # acolchoa um dia de cada lado: sessao que comeca 23h57 e continua depois da
    # meia-noite tem que ser lida inteira, senao aparece cortada em duas
    brutos = eventos.ler_dias(d1 - timedelta(days=1), d2 + timedelta(days=1))
    d = agregar(brutos, d1, d2, incluir_bots=bool(bots), incluir_teste=bool(teste))

    hoje = hoje_bsb()
    ontem = hoje - timedelta(days=1)
    segunda_esta_semana = hoje - timedelta(days=hoje.weekday())
    segunda_passada = segunda_esta_semana - timedelta(days=7)
    domingo_passado = segunda_esta_semana - timedelta(days=1)

    is_hoje = (d1 == hoje and d2 == hoje)
    is_ontem = (d1 == ontem and d2 == ontem)
    is_esta_semana = (d1 == segunda_esta_semana and d2 == hoje)
    is_semana_passada = (d1 == segunda_passada and d2 == domingo_passado)
    is_7dias = (d1 == hoje - timedelta(days=6) and d2 == hoje and not de and not ate)
    is_30dias = (d1 == hoje - timedelta(days=29) and d2 == hoje and not de and not ate)
    is_90dias = (d1 == hoje - timedelta(days=89) and d2 == hoje and not de and not ate)

    def link_preset(rot: str, p_de: Optional[str] = None, p_ate: Optional[str] = None, p_dias: Optional[int] = None, ativo: bool = False) -> str:
        q = {}
        if p_de and p_ate:
            q["de"] = p_de
            q["ate"] = p_ate
        elif p_dias:
            q["dias"] = p_dias
        if bots:
            q["bots"] = 1
        if teste:
            q["teste"] = 1
        if pag_leituras_int:
            q["pag_leituras"] = pag_leituras_int
        if so_checkout:
            q["so_checkout"] = 1
        if so_ao_vivo:
            q["so_ao_vivo"] = 1
        if so_comprou:
            q["so_comprou"] = 1
        if so_whatsapp:
            q["so_whatsapp"] = 1
        if uf:
            q["uf"] = uf
        qs = "&".join(f"{k}={v}" for k, v in q.items())
        on = " on" if ativo else ""
        return f'<a class="f{on}" href="/painel?{qs}">{rot}</a>'

    def link_toggle(rot: str, novo_bots: int, novo_teste: int) -> str:
        q = {}
        if de:
            q["de"] = de
        if ate:
            q["ate"] = ate
        if not de and not ate:
            q["dias"] = dias_int
        if novo_bots:
            q["bots"] = 1
        if novo_teste:
            q["teste"] = 1
        if pag_leituras_int:
            q["pag_leituras"] = pag_leituras_int
        if so_checkout:
            q["so_checkout"] = 1
        if so_ao_vivo:
            q["so_ao_vivo"] = 1
        if so_comprou:
            q["so_comprou"] = 1
        if so_whatsapp:
            q["so_whatsapp"] = 1
        if uf:
            q["uf"] = uf
        qs = "&".join(f"{k}={v}" for k, v in q.items())
        return f'<a href="/painel?{qs}">{rot}</a>'

    form_datas = (
        '<form method="GET" action="/painel" class="form-filtro-datas">'
        + (f'<input type="hidden" name="bots" value="1">' if bots else '')
        + (f'<input type="hidden" name="teste" value="1">' if teste else '')
        + (f'<input type="hidden" name="so_checkout" value="1">' if so_checkout else '')
        + (f'<input type="hidden" name="so_ao_vivo" value="1">' if so_ao_vivo else '')
        + (f'<input type="hidden" name="so_comprou" value="1">' if so_comprou else '')
        + (f'<input type="hidden" name="so_whatsapp" value="1">' if so_whatsapp else '')
        + (f'<input type="hidden" name="uf" value="{html.escape(uf)}">' if uf else '')
        + '<span class="lbl-datas">📅 Personalizado:</span>'
        + f'<label class="lbl-campo">De <input type="date" name="de" value="{d1:%Y-%m-%d}" max="{hoje:%Y-%m-%d}"></label>'
        + f'<label class="lbl-campo">Até <input type="date" name="ate" value="{d2:%Y-%m-%d}" max="{hoje:%Y-%m-%d}"></label>'
        + '<button type="submit" class="btn-filtrar-datas">Filtrar</button>'
        + '</form>'
    )

    p = [f"<style>{ESTILO}</style><title>Painel · Bússola</title><div class=w>"]
    p.append(f"<h1>Bússola Astrológica</h1>")
    p.append(f'<p class="sub">{d1:%d/%m/%Y} a {d2:%d/%m/%Y} · '
             f'<b>{d.get("pessoas_unicas", d["sessoes"])}</b> pessoas únicas, '
             f'{d["sessoes"]} sessões no total ({d["abertas"]} ainda em andamento)</p>')
    p.append('<div class="filtros">'
             + link_preset("hoje", p_de=hoje.isoformat(), p_ate=hoje.isoformat(), ativo=is_hoje)
             + link_preset("ontem", p_de=ontem.isoformat(), p_ate=ontem.isoformat(), ativo=is_ontem)
             + link_preset("esta semana", p_de=segunda_esta_semana.isoformat(), p_ate=hoje.isoformat(), ativo=is_esta_semana)
             + link_preset("semana passada", p_de=segunda_passada.isoformat(), p_ate=domingo_passado.isoformat(), ativo=is_semana_passada)
             + link_preset("7 dias", p_dias=7, ativo=is_7dias)
             + link_preset("30 dias", p_dias=30, ativo=is_30dias)
             + link_preset("90 dias", p_dias=90, ativo=is_90dias)
             + link_toggle("ocultar bots" if bots else "mostrar bots", novo_bots=0 if bots else 1, novo_teste=teste)
             + link_toggle("ocultar meus testes" if teste else "mostrar meus testes", novo_bots=bots, novo_teste=0 if teste else 1)
             + form_datas
             + '</div>')

    if d["sessoes"] < MIN_PARA_PORCENTAGEM:
        p.append(f'<div class="alerta">Menos de {MIN_PARA_PORCENTAGEM} sessões no período. '
                 'As porcentagens estão ocultas de propósito: com amostra pequena elas '
                 'movem decisão que não deveria ser movida. Os números absolutos valem.</div>')

    g = d["geracao"]
    oferta_item = next((f for f in d["funil"] if f["tela"] == 10), None)
    chegaram_oferta_sessoes = oferta_item["sessoes"] if oferta_item else 0
    chegaram_oferta_pessoas = oferta_item.get("pessoas", chegaram_oferta_sessoes) if oferta_item else 0

    checkout_item = next((f for f in d["funil"] if f["tela"] == "✦"), None)
    clicaram_checkout_sessoes = checkout_item["sessoes"] if checkout_item else d.get("checkout", {}).get("cliques", 0)
    clicaram_checkout_pessoas = checkout_item.get("pessoas", clicaram_checkout_sessoes) if checkout_item else clicaram_checkout

    dados_item = next((f for f in d["funil"] if f["tela"] == 5), None)
    chegaram_dados_sessoes = dados_item["sessoes"] if dados_item else 0
    chegaram_dados_pessoas = dados_item.get("pessoas", chegaram_dados_sessoes) if dados_item else 0

    tempos = d.get("tempos") or {}
    p.append('<div class="cards">')
    for valor, rot in [
        (d.get("pessoas_unicas", d["sessoes"]), "pessoas únicas"),
        (d["sessoes"], "sessões totais"),
        (f_tempo(tempos.get("mediana_sessao_ms")), "tempo médio no funil"),
        (f_tempo(tempos.get("mediana_ate_oferta_ms")), "tempo até a oferta"),
        (chegaram_dados_pessoas,
         f"chegaram aos dados ({chegaram_dados_sessoes} sessões)" if chegaram_dados_pessoas != chegaram_dados_sessoes else "chegaram aos dados"),
        (g["total"], "cartas entregues"),
        (chegaram_oferta_pessoas,
         f"chegaram à oferta ({chegaram_oferta_sessoes} sessões)" if chegaram_oferta_pessoas != chegaram_oferta_sessoes else "chegaram à oferta"),
        (clicaram_checkout_pessoas,
         f"foram ao checkout ({clicaram_checkout_sessoes} sessões)" if clicaram_checkout_pessoas != clicaram_checkout_sessoes else "foram ao checkout"),
        (f'{g["mediana_ms"]/1000:.1f}s', "mediana do agente"),
        (g["reserva"], "cartas de reserva"),
    ]:
        p.append(f'<div class="card"><b>{valor}</b><span>{rot}</span></div>')
    p.append("</div>")

    # ---- navegação de abas ----
    p.append('<nav class="abas">'
             '<button type="button" class="aba-btn on" data-tab="aba-funil" onclick="window.abrirAba(\'aba-funil\');return false;">📊 Funil por Tela</button>'
             '<button type="button" class="aba-btn" data-tab="aba-leituras" onclick="window.abrirAba(\'aba-leituras\');return false;">📖 Leituras</button>'
             '<button type="button" class="aba-btn" data-tab="aba-formulario" onclick="window.abrirAba(\'aba-formulario\');return false;">📝 Formulário & Horário</button>'
             '<button type="button" class="aba-btn" data-tab="aba-astrologia" onclick="window.abrirAba(\'aba-astrologia\');return false;">🔮 Áreas & Casas</button>'
             '</nav>')

    # ==================== ABA 1: FUNIL ====================
    p.append('<section class="aba-painel on" id="aba-funil">')
    p.append("<h2>Funil por tela</h2>")
    linhas = []
    for f in d["funil"]:
        rotulo = f'{f["tela"]} · {html.escape(f["nome"])}' if f["tela"] != "✦" else f'✦ {html.escape(f["nome"])}'
        linhas.append([
            rotulo,
            f'<div class="bar">{_barra(f["pct_do_topo"])}</div>',
            str(f.get("pessoas", f["sessoes"])),
            str(f["sessoes"]),
            f_tempo(f.get("tempo_na_tela_ms")),
            f_tempo(f.get("cronometro_ms")),
            _n(f["pct_do_topo"]),
            "—" if f["queda"] in (None, 0) else f'−{f["queda"]}',
            str(f["parou_aqui"]),
        ])
    p.append(_tabela(["etapa / tela", "", "#pessoas únicas", "#sessões", "tempo na tela", "cronômetro", "#% do topo", "#queda", "#pararam aqui"], linhas))
    p.append('<p class="nota"><b>#Pessoas únicas:</b> visitantes únicos que alcançaram a tela. '
             '<b>#Sessões:</b> total de acessos contabilizados. '
             '<b>Tempo na tela:</b> mediana do tempo de permanência nesta etapa específica. '
             '<b>Cronômetro:</b> tempo acumulado desde o momento em que o visitante entrou na página até atingir a tela. '
             'A linha <b>✦ Clique no Checkout</b> registra quem apertou o botão de compra na oferta.</p>')
    p.append('</section>')

    # ==================== ABA 2: LEITURAS ====================
    p.append('<section class="aba-painel" id="aba-leituras">')
    p.append("<h2>Leituras Geradas</h2>")
    res_leituras = _tabela_leituras(
        pag_leituras_int, por_pagina=20,
        so_checkout=bool(so_checkout),
        so_ao_vivo=bool(so_ao_vivo),
        so_comprou=bool(so_comprou),
        so_whatsapp=bool(so_whatsapp),
        uf=uf,
        de=d1, ate=d2
    )
    corpo_leituras, total_exibidos, total_pags, total_pessoas, total_chk, total_geral = res_leituras
    total_ao_vivo = getattr(res_leituras, "total_ao_vivo", 0)
    total_comprou = getattr(res_leituras, "total_comprou", 0)
    total_whatsapp = getattr(res_leituras, "total_whatsapp", 0)

    def link_filtro_leituras(modo: str) -> str:
        q = {"dias": dias_int}
        if de:
            q["de"] = de
        if ate:
            q["ate"] = ate
        if bots:
            q["bots"] = 1
        if teste:
            q["teste"] = 1
        if modo == "checkout":
            q["so_checkout"] = 1
        elif modo == "ao_vivo":
            q["so_ao_vivo"] = 1
        elif modo == "comprou":
            q["so_comprou"] = 1
        elif modo == "whatsapp":
            q["so_whatsapp"] = 1
        if uf:
            q["uf"] = uf
        qs = "&".join(f"{k}={v}" for k, v in q.items())
        url = f"/painel?{qs}#aba-leituras"
        if modo == "checkout":
            cls = " chk"
            on = " on" if so_checkout else ""
            rotulo = "✦ Só quem foi pro checkout"
            badge_id = "badge-count-checkout"
            cnt = total_chk
        elif modo == "ao_vivo":
            cls = " vivo"
            on = " on" if so_ao_vivo else ""
            rotulo = "🟢 Ao vivo agora"
            badge_id = "badge-count-vivo"
            cnt = total_ao_vivo
        elif modo == "comprou":
            cls = " comprou"
            on = " on" if so_comprou else ""
            rotulo = "💰 Só quem comprou"
            badge_id = "badge-count-comprou"
            cnt = total_comprou
        elif modo == "whatsapp":
            cls = " wa"
            on = " on" if so_whatsapp else ""
            rotulo = "📱 Só com WhatsApp"
            badge_id = "badge-count-wa"
            cnt = total_whatsapp
        else:
            cls = ""
            on = " on" if (not so_checkout and not so_ao_vivo and not so_comprou and not so_whatsapp) else ""
            rotulo = "Todas as leituras"
            badge_id = "badge-count-todos"
            cnt = total_geral

        return (f'<a href="{url}" class="btn-filtro-leituras{cls}{on}" '
                f'data-filtro="{modo}" onclick="return filtrarTabelaClient(\'{modo}\', this, event);">'
                f'{rotulo} <span id="{badge_id}" class="badge-count">{cnt}</span></a>')

    dropdown_uf = _dropdown_filtro_uf(getattr(res_leituras, "lista_ufs", []), uf_selecionado=uf)

    p.append('<div class="filtros-leituras">'
             + link_filtro_leituras("todos")
             + link_filtro_leituras("whatsapp")
             + link_filtro_leituras("checkout")
             + link_filtro_leituras("ao_vivo")
             + link_filtro_leituras("comprou")
             + dropdown_uf
             + '<span id="ws-status" class="ws-status desconectado" title="Status da conexão em tempo real">○ Conectando...</span>'
             + '</div>')

    p_params = {
        "dias": dias_int,
        "de": de if de else None,
        "ate": ate if ate else None,
        "bots": bots if bots else None,
        "teste": teste if teste else None,
        "so_checkout": 1 if so_checkout else None,
        "so_ao_vivo": 1 if so_ao_vivo else None,
        "so_comprou": 1 if so_comprou else None,
        "so_whatsapp": 1 if so_whatsapp else None,
        "uf": uf if uf else None,
    }
    if so_whatsapp:
        rotulo_pag = "contatos com WhatsApp"
    elif so_comprou:
        rotulo_pag = "compradores"
    elif so_ao_vivo:
        rotulo_pag = "pessoas ativas ao vivo"
    elif so_checkout:
        rotulo_pag = "pessoas com checkout"
    else:
        rotulo_pag = "pessoas únicas"

    barra_pag = _barra_paginacao(pag_leituras_int, total_pessoas, "/painel", p_params,
                                 por_pagina=20, param_nome="pag_leituras", hash_tab="#aba-leituras",
                                 rotulo_item=rotulo_pag)
    if so_whatsapp:
        sub_tipo = "que deixaram WhatsApp"
    elif so_comprou:
        sub_tipo = "que compraram o produto"
    elif so_ao_vivo:
        sub_tipo = "ativas navegando agora"
    elif so_checkout:
        sub_tipo = "com checkout"
    else:
        sub_tipo = "no total"

    txt_pessoas = f"{total_pessoas} pessoa única" if total_pessoas == 1 else f"{total_pessoas} pessoas únicas"
    txt_envios = f"{total_exibidos} envio" if total_exibidos == 1 else f"{total_exibidos} envios"
    p.append(f'<p class="sub" id="sub-leituras-info"><b>{total_pessoas}</b> {txt_pessoas} {sub_tipo} ({txt_envios} no total) · mostrando 20 por página · clique no ID para ver o mapa astrológico e o detalhe completo.</p>')
    p.append(corpo_leituras)
    p.append(barra_pag)
    p.append('</section>')

    # ==================== ABA 2: FORMULÁRIO & HORÁRIO ====================
    p.append('<section class="aba-painel" id="aba-formulario">')
    fo = d["formulario"]
    cheg_rot = f'chegaram ({fo["chegaram"]} sessões)' if fo.get("chegaram_pessoas", fo["chegaram"]) != fo["chegaram"] else 'chegaram'
    env_rot = f'enviaram ({fo["enviaram"]} sessões)' if fo.get("enviaram_pessoas", fo["enviaram"]) != fo["enviaram"] else 'enviaram'
    p.append("<h2>Onde a tela dos dados trava</h2>")
    p.append(f'<div class="cards">'
             f'<div class="card"><b>{fo.get("chegaram_pessoas", fo["chegaram"])}</b><span>{cheg_rot}</span></div>'
             f'<div class="card"><b>{fo.get("enviaram_pessoas", fo["enviaram"])}</b><span>{env_rot}</span></div>'
             f'<div class="card"><b>{fo["travaram"]}</b><span>travaram</span></div>'
             f'<div class="card"><b>{fo["sem_tocar"]}</b><span>não tocaram em nada</span></div></div>')
    p.append(_tabela(["último campo preenchido antes de desistir", "#sessões"],
                     [[html.escape(str(k)), str(v)] for k, v in fo["ultimo_campo"]]))
    if fo["faltou"]:
        p.append('<p class="nota">O que mais faltou ao clicar em calcular: '
                 + ", ".join(f"{html.escape(str(k))} ({v})" for k, v in fo["faltou"]) + ".</p>")

    # ---- horário ----
    p.append("<h2>Hora de nascimento</h2>")
    p.append(_tabela(["modo", "#sessões", "#chegaram à carta", "#chegaram à oferta", "#foram ao checkout"],
                     [[html.escape(str(h["modo"])), str(h["n"]),
                       f'{h["leitura"]} ({_n(h["pct_leitura"])})',
                       f'{h["oferta"]} ({_n(h["pct_oferta"])})',
                       f'{h.get("checkout", 0)} ({_n(h.get("pct_checkout"))})'] for h in d["horario"]]))
    p.append('<p class="nota">Cuidado ao comparar: quem não sabe a hora atravessa mais cliques até '
             'o fim do que quem digita dois números. Isto compara caminhos com atritos diferentes, '
             'não tipos de pessoa.</p>')
    p.append('</section>')

    # ==================== ABA 3: ÁREAS & CASAS ====================
    p.append('<section class="aba-painel" id="aba-astrologia">')
    # ---- áreas ----
    p.append("<h2>Áreas escolhidas</h2>")
    tot_a = sum(v for _, v in d["areas"]) or 1
    p.append(_tabela(["área", "", "#sessões", "#%"],
                     [[html.escape(str(k)), f'<div class="bar">{_barra(v*100/tot_a)}</div>',
                       str(v), _n(pct_ := (round(v*100/tot_a, 1) if tot_a >= MIN_PARA_PORCENTAGEM else None))]
                      for k, v in d["areas"]]))

    # ---- cenários e casas ----
    ce, ca = d["cenarios"], d["casas"]
    p.append("<h2>Cenários e casas eleitas</h2>")
    if ce["excluidas_sem_casa"]:
        p.append(f'<div class="alerta">{ce["excluidas_sem_casa"]} leitura(s) fora desta contagem '
                 'por não terem hora de nascimento confiável. Sem hora não há placar de casas, '
                 'então não existe cenário a comparar. Incluí-las faria um cenário dominar por '
                 'um motivo que nada tem a ver com os pesos do cálculo.</div>')
    if ca["alarme"]:
        p.append('<div class="alerta"><b>Uma casa passou de 40% das leituras.</b> '
                 'Isso costuma indicar que os pesos em <code>servicos/pesos.py</code> precisam '
                 'de rebalanceamento. Veja também a taxa de empate técnico abaixo antes de mexer.</div>')
    p.append(_tabela(["cenário", "#leituras", "#%"],
                     [[html.escape(str(i["nome"])), str(i["n"]), _n(i["pct"])] for i in ce["itens"]]))
    p.append(_tabela(["casa eleita", "", "#leituras", "#%"],
                     [[f'Casa {i["casa"]}', f'<div class="bar">{_barra(i["pct"])}</div>',
                       str(i["n"]), _n(i["pct"])] for i in ca["itens"]]))
    if ca["total"]:
        p.append(f'<p class="nota">{ca["empates"]} de {ca["total"]} leituras tiveram '
                 '<b>empate técnico</b>: a primeira e a segunda casa ficaram a menos de 8% uma da '
                 'outra, então o vencedor foi quase arbitrário. Se essa fração for alta, a tabela '
                 'acima é mais ruído que sinal.</p>')
    p.append('</section>')

    p.append(_modal_confirmar_exclusao())
    p.append(_modal_confirmar_compra())
    p.append(_modal_importar_csv())
    token_ws = gerar_token_ws()
    p.append(f'<script>window._wsToken = "{token_ws}";</script>')
    p.append(f'<script>{JS_PAINEL}</script>')
    p.append("</div>")
    return HTMLResponse("".join(p), headers=CABECALHOS)


@router.get("/painel/leituras", response_class=HTMLResponse)
def lista(_=Depends(exigir_senha), pagina: int = Query(0, ge=0),
          de: Optional[str] = None, ate: Optional[str] = None, dias: int = 7,
          so_checkout: int = 0, so_ao_vivo: int = 0, so_comprou: int = 0, so_whatsapp: int = 0,
          uf: Optional[str] = None):
    d1, d2 = _periodo(de, ate, dias) if (de or ate or dias) else (None, None)
    res_leituras = _tabela_leituras(
        pagina, por_pagina=20,
        so_checkout=bool(so_checkout),
        so_ao_vivo=bool(so_ao_vivo),
        so_comprou=bool(so_comprou),
        so_whatsapp=bool(so_whatsapp),
        uf=uf,
        de=d1, ate=d2
    )
    corpo, total_exibidos, total_pags, total_pessoas, total_chk, total_geral = res_leituras
    total_ao_vivo = getattr(res_leituras, "total_ao_vivo", 0)
    total_comprou = getattr(res_leituras, "total_comprou", 0)
    total_whatsapp = getattr(res_leituras, "total_whatsapp", 0)

    p_params = {
        "dias": dias,
        "de": de if de else None,
        "ate": ate if ate else None,
        "so_checkout": 1 if so_checkout else None,
        "so_ao_vivo": 1 if so_ao_vivo else None,
        "so_comprou": 1 if so_comprou else None,
        "so_whatsapp": 1 if so_whatsapp else None,
        "uf": uf if uf else None,
    }
    if so_whatsapp:
        rotulo_pag = "contatos com WhatsApp"
    elif so_comprou:
        rotulo_pag = "pessoas que compraram"
    elif so_ao_vivo:
        rotulo_pag = "pessoas ativas ao vivo"
    elif so_checkout:
        rotulo_pag = "pessoas com checkout"
    else:
        rotulo_pag = "pessoas únicas"

    barra_pag = _barra_paginacao(pagina, total_pessoas, "/painel/leituras", p_params,
                                 por_pagina=20, param_nome="pagina", rotulo_item=rotulo_pag)

    def link_filtro_lista(modo: str) -> str:
        q = {}
        if dias != 7:
            q["dias"] = dias
        if de:
            q["de"] = de
        if ate:
            q["ate"] = ate
        if modo == "checkout":
            q["so_checkout"] = 1
        elif modo == "ao_vivo":
            q["so_ao_vivo"] = 1
        elif modo == "comprou":
            q["so_comprou"] = 1
        elif modo == "whatsapp":
            q["so_whatsapp"] = 1
        if uf:
            q["uf"] = uf
        qs = ("?" + "&".join(f"{k}={v}" for k, v in q.items())) if q else ""
        url = f"/painel/leituras{qs}"
        if modo == "checkout":
            cls = " chk"
            on = " on" if so_checkout else ""
            rotulo = "✦ Só quem foi pro checkout"
            badge_id = "badge-count-checkout"
            cnt = total_chk
        elif modo == "ao_vivo":
            cls = " vivo"
            on = " on" if so_ao_vivo else ""
            rotulo = "🟢 Ao vivo agora"
            badge_id = "badge-count-vivo"
            cnt = total_ao_vivo
        elif modo == "comprou":
            cls = " comprou"
            on = " on" if so_comprou else ""
            rotulo = "💰 Só quem comprou"
            badge_id = "badge-count-comprou"
            cnt = total_comprou
        elif modo == "whatsapp":
            cls = " wa"
            on = " on" if so_whatsapp else ""
            rotulo = "📱 Só com WhatsApp"
            badge_id = "badge-count-wa"
            cnt = total_whatsapp
        else:
            cls = ""
            on = " on" if (not so_checkout and not so_ao_vivo and not so_comprou and not so_whatsapp) else ""
            rotulo = "Todas as leituras"
            badge_id = "badge-count-todos"
            cnt = total_geral

        return (f'<a href="{url}" class="btn-filtro-leituras{cls}{on}" '
                f'data-filtro="{modo}" onclick="return filtrarTabelaClient(\'{modo}\', this, event);">'
                f'{rotulo} <span id="{badge_id}" class="badge-count">{cnt}</span></a>')

    dropdown_uf = _dropdown_filtro_uf(getattr(res_leituras, "lista_ufs", []), uf_selecionado=uf)

    botoes_filtro = ('<div class="filtros-leituras">'
                     + link_filtro_lista("todos")
                     + link_filtro_lista("whatsapp")
                     + link_filtro_lista("checkout")
                     + link_filtro_lista("ao_vivo")
                     + link_filtro_lista("comprou")
                     + dropdown_uf
                     + '<span id="ws-status" class="ws-status desconectado" title="Status da conexão em tempo real">○ Conectando...</span>'
                     + '</div>')

    if so_whatsapp:
        sub_tipo = "que deixaram WhatsApp"
    elif so_comprou:
        sub_tipo = "que compraram o produto"
    elif so_ao_vivo:
        sub_tipo = "ativas navegando agora"
    elif so_checkout:
        sub_tipo = "com checkout"
    else:
        sub_tipo = "no total"

    txt_pessoas = f"{total_pessoas} pessoa única" if total_pessoas == 1 else f"{total_pessoas} pessoas únicas"
    txt_envios = f"{total_exibidos} envio" if total_exibidos == 1 else f"{total_exibidos} envios"
    token_ws = gerar_token_ws()
    return HTMLResponse(
        f"<style>{ESTILO}</style><title>Leituras</title><div class=w>"
        f'<h1>Leituras</h1><p class="sub" id="sub-leituras-info"><b>{total_pessoas}</b> {txt_pessoas} {sub_tipo} ({txt_envios} no total) · mostrando 20 por página · '
        f'<a href="/painel#aba-leituras">voltar ao painel</a></p>'
        f'{botoes_filtro}'
        f'{corpo}'
        f'{barra_pag}'
        f'{_modal_confirmar_exclusao()}'
        f'{_modal_confirmar_compra()}'
        f'{_modal_importar_csv()}'
        f'<p class="nota">Clique no ID para ver o detalhe e o mapa astrológico completo de cada leitura.</p></div>'
        f'<script>window._wsToken = "{token_ws}";</script>'
        f'<script>{JS_PAINEL}</script>',
        headers=CABECALHOS)


def _normalizar_nome_coluna(col: str) -> str:
    """Normaliza o cabeçalho de coluna do CSV para facilitar o mapeamento."""
    c = col.strip().lower()
    for o, d in [("á", "a"), ("à", "a"), ("ã", "a"), ("â", "a"),
                 ("é", "e"), ("ê", "e"), ("í", "i"), ("ó", "o"),
                 ("õ", "o"), ("ô", "o"), ("ú", "u"), ("ç", "c")]:
        c = c.replace(o, d)
    c = re.sub(r"[^\w\s]", "", c)
    return re.sub(r"\s+", "_", c)


def _parsear_data_nasc(s: str) -> dict:
    """Extrai dia, mês e ano de nascimento a partir de formatos comuns."""
    if not s or s.strip() in ("", "—", "-"):
        return {}
    s = s.strip()
    m = re.match(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})$", s)
    if m:
        dia, mes, ano = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if ano < 100:
            ano += 1900 if ano > 40 else 2000
        return {"dia": dia, "mes": mes, "ano": ano}
    m2 = re.match(r"^(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})$", s)
    if m2:
        ano, mes, dia = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
        return {"dia": dia, "mes": mes, "ano": ano}
    return {}


def _parsear_hora_nasc(s: str) -> dict:
    """Extrai hora e minuto ou período de nascimento."""
    if not s or s.strip() in ("", "—", "-"):
        return {}
    s = s.strip().lower()
    m = re.match(r"^(\d{1,2})[h:](\d{1,2})?$", s)
    if m:
        hora = int(m.group(1))
        minuto = int(m.group(2)) if m.group(2) is not None else 0
        return {"hora": hora, "minuto": minuto}
    return {"periodo": s}


def _parsear_booleano(s: Optional[str]) -> Optional[bool]:
    """Converte valores textuais comuns para booleano."""
    if s is None:
        return None
    val = str(s).strip().upper()
    if val in ("SIM", "S", "1", "TRUE", "VERDADEIRO", "COMPROU", "CHECKOUT"):
        return True
    if val in ("NÃO", "NAO", "N", "0", "FALSE", "FALSO"):
        return False
    return None


def processar_csv_leituras(conteudo_bytes: bytes, atualizar: bool = True) -> dict:
    """Processa o conteúdo binário de um arquivo CSV e cria ou atualiza leituras."""
    texto = None
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            texto = conteudo_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if texto is None:
        texto = conteudo_bytes.decode("latin-1", errors="replace")

    linhas_puras = [l for l in texto.splitlines() if l.strip()]
    if not linhas_puras:
        return {"sucesso": False, "erro": "O arquivo CSV está vazio.", "total": 0, "criados": 0, "atualizados": 0, "erros": []}

    primeira_linha = linhas_puras[0]
    if primeira_linha.count(";") >= primeira_linha.count(","):
        delim = ";"
    elif "," in primeira_linha:
        delim = ","
    elif "\t" in primeira_linha:
        delim = "\t"
    else:
        delim = ";"

    leitor = csv.reader(io.StringIO(texto), delimiter=delim)
    try:
        cabecalho_bruto = next(leitor)
    except StopIteration:
        return {"sucesso": False, "erro": "Cabeçalho não encontrado no CSV.", "total": 0, "criados": 0, "atualizados": 0, "erros": []}

    col_map = {}
    for idx, c in enumerate(cabecalho_bruto):
        norm = _normalizar_nome_coluna(c)
        if norm in ("id", "id_da_leitura", "leitura_id", "stem"):
            col_map["id"] = idx
        elif norm in ("nome", "nome_completo", "cliente", "lead", "nome_do_cliente"):
            col_map["nome"] = idx
        elif norm in ("whatsapp", "telefone", "celular", "fone", "tel", "zap", "contato"):
            col_map["whatsapp"] = idx
        elif norm in ("data_de_nascimento", "data_nasc", "nascimento", "data_nascimento", "dt_nasc"):
            col_map["nascimento"] = idx
        elif norm in ("hora_de_nascimento", "hora_nasc", "hora_nascimento", "hora"):
            col_map["hora_nasc"] = idx
        elif norm in ("cidade", "municipio"):
            col_map["cidade"] = idx
        elif norm in ("uf", "estado"):
            col_map["uf"] = idx
        elif norm in ("pais", "pais_de_residencia"):
            col_map["pais"] = idx
        elif norm in ("etapa", "etapa_alcancada", "etapa_max"):
            col_map["etapa"] = idx
        elif norm in ("checkout", "fez_checkout"):
            col_map["checkout"] = idx
        elif norm in ("comprou", "compra", "comprador"):
            col_map["comprou"] = idx
        elif norm in ("area", "area_do_quiz"):
            col_map["area"] = idx
        elif norm in ("cenario", "cenario_astrologico"):
            col_map["cenario"] = idx
        elif norm in ("casa", "casa_astrologica"):
            col_map["casa"] = idx
        elif norm in ("chegou_ao_quiz_bsb", "chegou_ao_quiz", "chegou_em_bsb", "chegou_bsb"):
            col_map["chegou_bsb"] = idx
        elif norm in ("preencheu_dados_bsb", "preencheu_dados", "gravado_em_bsb", "gravado_bsb"):
            col_map["gravado_bsb"] = idx
        elif norm in ("tempo_no_quiz", "tempo_quiz"):
            col_map["tempo_quiz"] = idx

    if "nome" not in col_map and "whatsapp" not in col_map and "id" not in col_map:
        return {
            "sucesso": False,
            "erro": "Não foi possível identificar colunas mínimas (Nome, WhatsApp ou ID) no cabeçalho do CSV.",
            "total": 0, "criados": 0, "atualizados": 0, "erros": []
        }

    total = 0
    criados = 0
    atualizados = 0
    erros = []

    def get_v(row: list, key: str) -> str:
        idx = col_map.get(key)
        if idx is not None and idx < len(row):
            return row[idx].strip()
        return ""

    agora_bsb_dt = datetime.now(FUSO_BSB)
    agora_bsb_str = agora_bsb_dt.strftime("%d/%m/%y %H:%M")

    for num_linha, row in enumerate(leitor, start=2):
        if not row or not any(x.strip() for x in row):
            continue
        total += 1
        try:
            val_id = get_v(row, "id")
            val_nome = get_v(row, "nome")
            val_wa = get_v(row, "whatsapp")
            val_nasc = get_v(row, "nascimento")
            val_hora = get_v(row, "hora_nasc")
            val_cidade = get_v(row, "cidade")
            val_uf = get_v(row, "uf")
            val_pais = get_v(row, "pais")
            val_etapa = get_v(row, "etapa")
            val_checkout = get_v(row, "checkout")
            val_comprou = get_v(row, "comprou")
            val_area = get_v(row, "area")
            val_cenario = get_v(row, "cenario")
            val_casa = get_v(row, "casa")
            val_chegou = get_v(row, "chegou_bsb")
            val_gravado = get_v(row, "gravado_bsb")

            def limpa_traco(v: str) -> str:
                return "" if v in ("—", "-") else v

            val_id = limpa_traco(val_id)
            val_nome = limpa_traco(val_nome)
            val_wa = limpa_traco(val_wa)
            val_cidade = limpa_traco(val_cidade)
            val_uf = limpa_traco(val_uf)
            val_pais = limpa_traco(val_pais) or "Brasil"
            val_area = limpa_traco(val_area)
            val_cenario = limpa_traco(val_cenario)
            val_casa = limpa_traco(val_casa)
            val_chegou = limpa_traco(val_chegou)
            val_gravado = limpa_traco(val_gravado)

            b_comprou = _parsear_booleano(val_comprou)
            b_checkout = _parsear_booleano(val_checkout)

            arq_existente = None
            if val_id:
                candidato = config.DIR_LEITURAS / f"{val_id}.json"
                if candidato.exists():
                    arq_existente = candidato

            if arq_existente and atualizar:
                try:
                    d = json.loads(arq_existente.read_text(encoding="utf-8"))
                except Exception:
                    d = {}

                if val_nome:
                    d["nome_completo"] = val_nome
                    quiz_dict = d.setdefault("quiz", {})
                    if not quiz_dict.get("primeiro_nome"):
                        quiz_dict["primeiro_nome"] = val_nome.split()[0]
                if val_wa:
                    d["whatsapp"] = val_wa
                if b_comprou is not None:
                    d["comprou"] = b_comprou
                    if b_comprou and not d.get("comprado_em"):
                        d["comprado_em"] = datetime.now().isoformat(timespec="seconds")
                if b_checkout is not None:
                    d["checkout"] = b_checkout
                if val_nasc:
                    parsed_nasc = _parsear_data_nasc(val_nasc)
                    if parsed_nasc:
                        d_nasc = d.setdefault("nascimento", {})
                        d_nasc.update(parsed_nasc)
                if val_hora:
                    parsed_hora = _parsear_hora_nasc(val_hora)
                    if parsed_hora:
                        d_nasc = d.setdefault("nascimento", {})
                        d_nasc.update(parsed_hora)
                if val_cidade or val_uf or val_pais:
                    d_cid = d.setdefault("cidade", {})
                    if val_cidade: d_cid["nome"] = val_cidade
                    if val_uf: d_cid["uf"] = val_uf
                    if val_pais: d_cid["pais"] = val_pais
                if val_area:
                    d.setdefault("quiz", {})["area"] = val_area
                if val_cenario:
                    d.setdefault("veredito", {})["tipo"] = val_cenario
                if val_casa:
                    m_c = re.search(r"\d+", val_casa)
                    if m_c:
                        c_num = int(m_c.group(0))
                        d.setdefault("veredito", {})["casa_aberta"] = c_num
                        d["veredito"]["casa_eleita_real"] = True
                if val_chegou:
                    d["chegou_em_bsb"] = val_chegou
                if val_gravado:
                    d["gravado_em_bsb"] = val_gravado

                arq_existente.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
                atualizados += 1

            elif not arq_existente:
                novo_lid = val_id if (val_id and re.fullmatch(r"[\w-]+", val_id)) else registro.novo_id()
                agora_utc = datetime.now(timezone.utc)
                parsed_nasc = _parsear_data_nasc(val_nasc) if val_nasc else {}
                parsed_hora = _parsear_hora_nasc(val_hora) if val_hora else {}
                nasc_obj = dict(parsed_nasc, **parsed_hora)

                casa_num = 0
                if val_casa:
                    m_c = re.search(r"\d+", val_casa)
                    if m_c:
                        casa_num = int(m_c.group(0))

                etapa_num = 7
                etapa_nome = val_etapa or "Tela 7 (Leitura)"
                if val_etapa:
                    m_et = re.search(r"\d+", val_etapa)
                    if m_et:
                        etapa_num = int(m_et.group(0))

                d_novo = {
                    "leitura_id": novo_lid,
                    "nome_completo": val_nome or "—",
                    "whatsapp": val_wa or "",
                    "quiz": {
                        "primeiro_nome": val_nome.split()[0] if val_nome else "",
                        "area": val_area or "geral",
                    },
                    "nascimento": nasc_obj,
                    "cidade": {
                        "nome": val_cidade or "—",
                        "uf": val_uf or "—",
                        "pais": val_pais or "Brasil",
                    },
                    "veredito": {
                        "tipo": val_cenario or "—",
                        "casa_aberta": casa_num,
                        "casa_eleita_real": bool(casa_num > 0),
                    },
                    "etapa_max": etapa_num,
                    "etapa_nome": etapa_nome,
                    "checkout": bool(b_checkout) if b_checkout is not None else False,
                    "comprou": bool(b_comprou) if b_comprou is not None else False,
                    "gravado_em": agora_utc.isoformat(timespec="seconds"),
                    "gravado_em_bsb": val_gravado or agora_bsb_str,
                    "chegou_em_bsb": val_chegou or agora_bsb_str,
                    "pesos_v": 1,
                }
                if b_comprou:
                    d_novo["comprado_em"] = agora_utc.isoformat(timespec="seconds")

                caminho_novo = config.DIR_LEITURAS / f"{novo_lid}.json"
                caminho_novo.write_text(json.dumps(d_novo, ensure_ascii=False, indent=1), encoding="utf-8")
                criados += 1

        except Exception as ex:
            logger.warning("Erro ao processar linha %d do CSV: %s", num_linha, ex)
            erros.append(f"Linha {num_linha}: {str(ex)}")

    return {
        "sucesso": True,
        "total": total,
        "criados": criados,
        "atualizados": atualizados,
        "erros": erros
    }


@router.post("/painel/importar-csv")
async def importar_csv(
    arquivo: UploadFile = File(...),
    atualizar: int = Form(1),
    _=Depends(exigir_senha)
):
    """Recebe planilha CSV enviada e cadastra ou atualiza leituras."""
    nome = arquivo.filename or ""
    if not nome.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="O arquivo enviado deve ter extensão .csv")

    try:
        conteudo = await arquivo.read()
    except Exception as e:
        logger.error("Falha ao ler arquivo CSV enviado: %s", e)
        raise HTTPException(status_code=400, detail="Não foi possível ler o arquivo enviado.")

    if not conteudo or not conteudo.strip():
        raise HTTPException(status_code=400, detail="O arquivo CSV enviado está vazio.")

    resultado = processar_csv_leituras(conteudo, atualizar=bool(atualizar))
    if not resultado.get("sucesso"):
        raise HTTPException(status_code=400, detail=resultado.get("erro", "Erro ao processar CSV."))

    return resultado


@router.get("/painel/exportar-csv")
def exportar_csv(_=Depends(exigir_senha),
                 de: Optional[str] = None, ate: Optional[str] = None, dias: int = 7,
                 so_checkout: int = 0, so_ao_vivo: int = 0, so_comprou: int = 0, so_whatsapp: int = 0,
                 uf: Optional[str] = None,
                 ids: Optional[str] = None):
    """Gera planilha CSV estruturada com as leituras filtradas ou selecionadas."""
    d1, d2 = _periodo(de, ate, dias) if not ids else (None, None)
    arquivos = sorted(config.DIR_LEITURAS.glob("*.json"), reverse=True)

    ids_alvo = set(x.strip() for x in ids.split(",") if x.strip()) if ids else None

    todos_dados: list[tuple[str, dict]] = []
    for arq in arquivos:
        if ids_alvo and arq.stem not in ids_alvo:
            continue
        try:
            d = json.loads(arq.read_text(encoding="utf-8"))
        except Exception:
            continue
        if (d.get("nome_completo") or "").strip().lower() == "pessoa de teste":
            continue
        if not ids_alvo and d1 and d2:
            dt_ch = obter_data_chegada_leitura(d, arq.stem)
            if dt_ch and not (d1 <= dt_ch <= d2):
                continue
        todos_dados.append((arq.stem, d))

    progresso_map = obter_progresso_leituras(todos_dados)
    todos_grupos = _agrupar_leituras_por_pessoa(todos_dados, progresso_map)

    ativos = rastreador_presenca.obter_ativos(90.0)
    ids_ao_vivo = {str(a["leitura_id"]).strip() for a in ativos if a.get("leitura_id")}
    sids_ao_vivo = {str(a["sid"]).strip() for a in ativos if a.get("sid")}

    for g in todos_grupos:
        cid = str(g["d_principal"].get("cliente_id") or "").strip()
        g_cids = {cid} if cid else set()
        for _, sub_d in g["outras_leituras"]:
            sc = str(sub_d.get("cliente_id") or "").strip()
            if sc:
                g_cids.add(sc)
        g["ao_vivo"] = bool(set(g["todos_ids"]) & ids_ao_vivo or g_cids & sids_ao_vivo)

    if not ids_alvo:
        if so_whatsapp:
            todos_grupos = [g for g in todos_grupos if g.get("tem_whatsapp")]
        elif so_comprou:
            todos_grupos = [g for g in todos_grupos if g.get("comprou")]
        elif so_ao_vivo:
            todos_grupos = [g for g in todos_grupos if g["ao_vivo"]]
        elif so_checkout:
            todos_grupos = [g for g in todos_grupos if g["teve_checkout"]]

        if uf and uf.strip():
            uf_norm = uf.strip().lower()
            todos_grupos = [
                g for g in todos_grupos
                if str((g.get("cidade") or {}).get("uf") or (g.get("cidade") or {}).get("nome") or "").strip().lower() == uf_norm
            ]

    out = io.StringIO()
    out.write("\ufeff")
    writer = csv.writer(out, delimiter=";", quoting=csv.QUOTE_ALL)
    writer.writerow([
        "ID da Leitura",
        "Chegou ao Quiz (BSB)",
        "Preencheu Dados (BSB)",
        "Etapa Alcançada",
        "Fez Checkout",
        "Comprou",
        "Nome Completo",
        "WhatsApp",
        "Data de Nascimento",
        "Hora de Nascimento",
        "Cidade",
        "UF",
        "País",
        "Área do Quiz",
        "Cenário Astrológico",
        "Casa Astrológica",
        "Tempo no Quiz",
        "Total de Envios"
    ])

    for g in todos_grupos:
        stem = g["stem_principal"]
        d = g["d_principal"]
        v, pr = d.get("veredito") or {}, d.get("precisao") or {}
        nasc = g["nascimento"]
        cid = g["cidade"]
        chegada_bsb, gerada_bsb = f_chegada_bsb(d, stem)
        writer.writerow([
            stem,
            chegada_bsb,
            gerada_bsb,
            g["rotulo_etapa"],
            "SIM" if g["teve_checkout"] else "NÃO",
            "SIM" if g.get("comprou") else "NÃO",
            g["nome_completo"],
            g["whatsapp"] or "—",
            f_data(nasc),
            f_hora(nasc, pr),
            cid.get("nome") or "—",
            cid.get("uf") or "—",
            cid.get("pais") or "Brasil",
            str((d.get("quiz") or {}).get("area") or "—"),
            str(v.get("tipo") or "—"),
            "—" if not v.get("casa_eleita_real") else f'Casa {v.get("casa_aberta")}',
            f_tempo(d.get("tempo_quiz_ms")),
            g["total_envios"]
        ])

    csv_data = out.getvalue().encode("utf-8")
    nome_arquivo = f"leituras_bussola_{hoje_bsb().strftime('%Y-%m-%d')}.csv"
    return Response(
        content=csv_data,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{nome_arquivo}"',
            "Cache-Control": "no-store, no-cache, must-revalidate",
        }
    )


@router.get("/painel/leitura/{leitura_id}", response_class=HTMLResponse)
def detalhe(leitura_id: str, _=Depends(exigir_senha), revelar: int = 0):
    if not re.fullmatch(r"[0-9]{8}-[0-9]{6}-[0-9a-f]{8}", leitura_id):
        raise HTTPException(404, "não encontrada")
    arq = config.DIR_LEITURAS / f"{leitura_id}.json"
    if not arq.exists():
        raise HTTPException(404, "não encontrada")
    d = json.loads(arq.read_text(encoding="utf-8"))
    c = d.get("carta") or {}
    n = d.get("nascimento") or {}
    cid = d.get("cidade") or {}
    pr = d.get("precisao") or {}

    chegada_bsb, gerada_bsb = f_chegada_bsb(d, leitura_id)
    prog = obter_progresso_leituras([(leitura_id, d)]).get(leitura_id, {"max_tela": 7, "rotulo": "Tela 7 (Leitura)", "checkout": False})
    h_str = f_hora(n, pr)
    uf_str = f' ({html.escape(cid.get("uf"))})' if cid.get("uf") else ''
    t_quiz_str = f' · tempo no quiz: {f_tempo(d.get("tempo_quiz_ms"))}' if d.get("tempo_quiz_ms") else ''
    chk_str = '<b style="color:var(--green);">✦ SIM</b>' if prog["checkout"] else '<span style="color:var(--sand2);">Não</span>'

    # Verifica se a pessoa enviou mais de uma vez
    contagens_map, _ = _contagens_leituras(list(config.DIR_LEITURAS.glob("*.json")))
    qtd_submissoes = contagens_map.get(leitura_id, 1)
    tag_rep_detalhe = f' · <span class="tag-rep">{qtd_submissoes} envios desta pessoa</span>' if qtd_submissoes > 1 else ''

    nome_puro = d.get("nome_completo") or "—"
    nome_js = html.escape(nome_puro).replace("'", "\\'")
    comprou = bool(d.get("comprou"))
    btn_compra_cls = "btn-compra comprou" if comprou else "btn-compra"
    btn_compra_txt = "✅ Comprou" if comprou else "💰 Marcar Compra"
    btn_compra = (f'<button type="button" id="btn-compra-{html.escape(leitura_id)}" class="{btn_compra_cls}" style="margin-left:8px;" '
                  f'onclick="abrirModalCompra(\'{html.escape(leitura_id)}\', \'{nome_js}\', {1 if comprou else 0}, this);" '
                  f'title="Marcar ou desmarcar se comprou o produto">{btn_compra_txt}</button>')
    btn_del = (f'<button type="button" class="btn-del" style="margin-left:6px;" '
               f'onclick="abrirModalExcluir(\'{html.escape(leitura_id)}\', \'{nome_js}\');">'
               f'🗑️ Excluir Leitura</button>')

    ident = (f'{html.escape(nome_puro)}{tag_rep_detalhe} · '
             f'chegou ao quiz: <b style="color:var(--amber);">{html.escape(chegada_bsb)} (BSB)</b> · '
             f'preencheu dados: <b style="color:var(--amber);">{html.escape(gerada_bsb)} (BSB)</b> · '
             f'etapa: <b style="color:var(--amber);">{html.escape(prog["rotulo"])}</b> · '
             f'checkout: {chk_str} · '
             f'{f_data(n)} ({h_str}) · '
             f'{html.escape(cid.get("nome") or "—")}{uf_str} · '
             f'{f_wa(d.get("whatsapp"))}'
             f'{t_quiz_str}')

    ps = "".join(f"<p>{html.escape(x)}</p>" for x in (c.get("paragrafos") or []))
    notas = "".join(f"<li>{html.escape(x)}</li>" for x in (c.get("notas") or []))
    return HTMLResponse(
        f"<style>{ESTILO}</style><title>{html.escape(leitura_id)}</title><div class=w>"
        f'<h1>{html.escape(leitura_id)}</h1><p class="sub">{ident} · '
        f'<a href="/painel#aba-leituras">voltar ao painel</a> {btn_compra} {btn_del}</p>'
        f'<h2>{html.escape(c.get("selo",""))}</h2>'
        f'<p><b>{html.escape(c.get("titulo",""))}</b></p>'
        f'<p style="color:var(--amber)">{html.escape(c.get("destaque",""))}</p>'
        f'{ps}<p class="nota">{html.escape(c.get("espera") or "")} '
        f'{html.escape(c.get("janela") or "")}</p>'
        f'<h2>cálculo</h2><ul class="nota">{notas}</ul>'
        f'<h2>veredito</h2><pre class="nota">'
        f'{html.escape(json.dumps(d.get("veredito"), ensure_ascii=False, indent=1))}</pre>'
        f'<h2>meta</h2><pre class="nota">'
        f'{html.escape(json.dumps(d.get("meta"), ensure_ascii=False, indent=1))}</pre>'
        f'{_modal_confirmar_exclusao()}'
        f'{_modal_confirmar_compra()}'
        f'<script>{JS_PAINEL}</script></div>',
        headers=CABECALHOS)


@router.post("/painel/leitura/{leitura_id}/deletar")
def deletar_leitura(leitura_id: str, modo: str = Query("individual"), _=Depends(exigir_senha)):
    """Exclui permanentemente o arquivo de uma leitura individual ou todos os envios de uma pessoa."""
    if not re.fullmatch(r"[0-9]{8}-[0-9]{6}-[0-9a-f]{8}", leitura_id):
        raise HTTPException(400, "identificador de leitura inválido")

    if modo == "todos":
        # Carrega todas as leituras e agrupa para encontrar todos os IDs associados a essa pessoa
        arquivos = list(config.DIR_LEITURAS.glob("*.json"))
        todos_dados: list[tuple[str, dict]] = []
        for arq in arquivos:
            try:
                todos_dados.append((arq.stem, json.loads(arq.read_text(encoding="utf-8"))))
            except Exception:
                continue

        grupos = _agrupar_leituras_por_pessoa(todos_dados, {})
        ids_para_excluir = [leitura_id]
        for g in grupos:
            if leitura_id in g["todos_ids"]:
                ids_para_excluir = g["todos_ids"]
                break

        removidos = []
        erros = []
        for lid in ids_para_excluir:
            arq = config.DIR_LEITURAS / f"{lid}.json"
            if arq.exists():
                try:
                    arq.unlink()
                    removidos.append(lid)
                except Exception as e:
                    logger.error("Erro ao excluir arquivo de leitura %s: %s", lid, e)
                    erros.append(lid)

        if not removidos and erros:
            raise HTTPException(500, f"falha ao excluir leituras: {erros}")
        if not removidos:
            raise HTTPException(404, "nenhuma leitura encontrada para exclusão")

        logger.info("Grupo de leituras %s excluído com sucesso (%d arquivos removidos).", leitura_id, len(removidos))
        return {
            "ok": True,
            "leitura_id": leitura_id,
            "modo": "todos",
            "removidos": removidos,
            "mensagem": f"{len(removidos)} envio(s) excluído(s) com sucesso"
        }

    # modo == "individual"
    arq = config.DIR_LEITURAS / f"{leitura_id}.json"
    if not arq.exists():
        raise HTTPException(404, "leitura não encontrada")
    try:
        arq.unlink()
        logger.info("Leitura %s excluída com sucesso.", leitura_id)
    except Exception as e:
        logger.error("Erro ao excluir arquivo de leitura %s: %s", leitura_id, e)
        raise HTTPException(500, f"falha ao excluir leitura: {e}")
    return {
        "ok": True,
        "leitura_id": leitura_id,
        "modo": "individual",
        "removidos": [leitura_id],
        "mensagem": "Leitura excluída com sucesso"
    }


@router.post("/painel/leitura/{leitura_id}/status-compra")
def alterar_status_compra(leitura_id: str, comprou: bool = Query(...), _=Depends(exigir_senha)):
    """Atualiza o status de compra (comprou: true/false) de uma leitura e notifica via WebSocket."""
    if not re.fullmatch(r"[0-9]{8}-[0-9]{6}-[0-9a-f]{8}", leitura_id):
        raise HTTPException(400, "identificador de leitura inválido")

    sucesso = registro.atualizar_status_compra(leitura_id, comprou)
    if not sucesso:
        raise HTTPException(404, "leitura não encontrada")

    # Calcula o total atualizado de compradores únicos
    arquivos = list(config.DIR_LEITURAS.glob("*.json"))
    todos_dados: list[tuple[str, dict]] = []
    for arq in arquivos:
        try:
            todos_dados.append((arq.stem, json.loads(arq.read_text(encoding="utf-8"))))
        except Exception:
            continue
    grupos = _agrupar_leituras_por_pessoa(todos_dados, {})
    total_comprou = sum(1 for g in grupos if g.get("comprou"))

    # Notifica clientes conectados no WebSocket
    ws_manager.broadcast_sync({
        "tipo": "status_compra",
        "leitura_id": leitura_id,
        "comprou": comprou,
        "total_comprou": total_comprou,
    })

    logger.info("Status de compra atualizado para leitura %s: comprou=%s", leitura_id, comprou)
    return {
        "ok": True,
        "leitura_id": leitura_id,
        "comprou": comprou,
        "total_comprou": total_comprou,
    }


