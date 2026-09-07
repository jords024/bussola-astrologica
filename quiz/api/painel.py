# -*- coding: utf-8 -*-
"""GET /painel — o funil em números.

Protegido por senha porque concentra dado pessoal. A lista de leituras vem
MASCARADA por padrão: o pior cenário concreto não é invasão, é uma captura de
tela ou um olhar por cima do ombro sobre duzentos nomes completos com data de
nascimento e telefone.
"""
from __future__ import annotations

import html
import json
import logging
import re
import secrets
import time
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import pytz

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

import config
from servicos import eventos, registro
from servicos.agregador import MIN_PARA_PORCENTAGEM, agregar

router = APIRouter()
logger = logging.getLogger(__name__)
seguranca = HTTPBasic(auto_error=False)

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


TZ_BRASILIA = pytz.timezone("America/Sao_Paulo")


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


def f_chegada_bsb(d: dict, arq_stem: str) -> tuple[str, str]:
    """Retorna (chegou_em_bsb, gerado_em_bsb) formatados no horário de Brasília (UTC-3) como dd/mm/aa HH:MM."""
    if d.get("chegou_em_bsb") and d.get("gravado_em_bsb"):
        return (
            _formatar_data_hora_curta(d["chegou_em_bsb"]),
            _formatar_data_hora_curta(d["gravado_em_bsb"])
        )

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

    return (
        dt_chegada_bsb.strftime("%d/%m/%y %H:%M"),
        dt_gerada_bsb.strftime("%d/%m/%y %H:%M")
    )


# --------------------------------------------------------------------- helpers
def _periodo(de: Optional[str], ate: Optional[str], dias: int) -> tuple[date, date]:
    hoje = date.today()
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
.filtros{display:flex;gap:7px;flex-wrap:wrap;margin:14px 0 6px}
.filtros a{padding:6px 12px;border:1px solid var(--line);border-radius:999px;
color:var(--sand2);text-decoration:none;font-size:12px}
.filtros a.on{border-color:var(--amber);color:var(--amber)}
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
.aba-btn{background:none;border:none;color:var(--sand2);font:inherit;font-size:13px;font-weight:600;padding:10px 18px;cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px;transition:all .15s ease;display:inline-flex;align-items:center;gap:7px;white-space:nowrap;border-radius:6px 6px 0 0}
.aba-btn:hover{color:var(--sand);background:rgba(255,255,255,.03)}
.aba-btn.on{color:var(--amber);border-bottom-color:var(--amber);background:rgba(229,169,60,.08)}
.aba-painel{display:none}
.aba-painel.on{display:block;animation:fadein .2s ease}
.tbl-wrap{width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch;margin-bottom:12px;cursor:grab}
.tbl-wrap:active{cursor:grabbing}
.tbl-wrap.arrastando{cursor:grabbing !important;user-select:none !important;-webkit-user-select:none !important}
.tbl-wrap.arrastando *{cursor:grabbing !important;user-select:none !important;-webkit-user-select:none !important}
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
.painel-toast{position:fixed;bottom:24px;right:24px;background:#24201D;border:1px solid var(--amber);color:var(--sand);padding:12px 20px;border-radius:8px;font-size:13px;box-shadow:0 10px 25px rgba(0,0,0,.6);z-index:999999;opacity:0;transform:translateY(10px);transition:all .25s ease;pointer-events:none}
.painel-toast.on{opacity:1;transform:translateY(0);pointer-events:auto}
@keyframes fadein{from{opacity:0;transform:translateY(3px)}to{opacity:1;transform:none}}
"""

JS_PAINEL = """
var _activeWrap = null;
var _startX = 0;
var _scrollLeft = 0;
var _hasMoved = false;

function iniciarArrastoScroll(){
  document.querySelectorAll(".tbl-wrap").forEach(function(wrap){
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

function abrirAba(id){
  document.querySelectorAll(".aba-btn").forEach(function(b){b.classList.toggle("on",b.getAttribute("data-tab")===id);});
  document.querySelectorAll(".aba-painel").forEach(function(s){s.classList.toggle("on",s.id===id);});
  try{history.replaceState(null,"","#"+id);localStorage.setItem("painel_aba_ativa",id);}catch(e){}
  iniciarArrastoScroll();
}
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
function filtrarCheckoutClient(soChk, btn, evt){
  var tbody = document.getElementById("tbody-leituras");
  if(!tbody){ return true; }
  var rows = tbody.querySelectorAll("tr.tr-pessoa[data-checkout]");
  var totalRows = rows.length;
  if(totalRows > 0 && totalRows <= 20){
    if(evt && evt.preventDefault){ evt.preventDefault(); }
    var visiveis = 0;
    rows.forEach(function(r){
      var chk = r.getAttribute("data-checkout") === "1";
      var idGrupo = r.id.replace("row-pessoa-", "");
      var subRows = document.querySelectorAll(".grupo-" + idGrupo);
      if(soChk === 1 && !chk){
        r.style.display = "none";
        subRows.forEach(function(sr){ sr.style.display = "none"; });
      } else {
        r.style.display = "";
        visiveis++;
      }
    });
    document.querySelectorAll(".btn-filtro-leituras").forEach(function(b){
      var bSoChk = parseInt(b.getAttribute("data-so-checkout") || "0", 10);
      b.classList.toggle("on", bSoChk === soChk);
    });
    var sub = document.getElementById("sub-leituras-info");
    if(sub){
      var tipo = soChk === 1 ? "pessoas com checkout" : "pessoas no total";
      sub.innerHTML = "<b>" + visiveis + "</b> " + tipo + " · mostrando 20 por página · clique no ID para ver o mapa astrológico e o detalhe completo.";
    }
    try{
      var href = btn.getAttribute("href");
      if(href){ history.replaceState(null, "", href); }
    }catch(e){}
    return false;
  }
  return true;
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
  if(e.key === "Escape"){ fecharModalExcluir(); }
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
(function(){
  var hash=(location.hash||"").replace("#","");
  var salva="";try{salva=localStorage.getItem("painel_aba_ativa");}catch(e){}
  var alvo=hash||salva;
  if(alvo&&document.getElementById(alvo)){abrirAba(alvo);}
  iniciarArrastoScroll();
})();
"""


def _tabela(cabecalhos: list[str], linhas: list[list[str]], classes: str = "",
            tr_attrs: Optional[list[str]] = None, tbody_id: str = "") -> str:
    if not linhas:
        return '<p class="vazio">Ainda sem dados neste período.</p>'
    th = "".join(f'<th class="{"n" if h.startswith("#") else ""}">{html.escape(h.lstrip("#"))}</th>'
                 for h in cabecalhos)
    tr = ""
    for idx, l in enumerate(linhas):
        extra = f" {tr_attrs[idx]}" if tr_attrs and idx < len(tr_attrs) else ""
        tds = "".join(f'<td class="{"n" if h.startswith("#") else ""}">{c}</td>'
                      for h, c in zip(cabecalhos, l))
        tr += f"<tr{extra}>{tds}</tr>"
    tbody_attr = f' id="{tbody_id}"' if tbody_id else ""
    return f'<div class="tbl-wrap"><table class="{classes}"><thead><tr>{th}</tr></thead><tbody{tbody_attr}>{tr}</tbody></table></div>'


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
            dt_leitura = date.today()

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
            "nascimento": d_principal.get("nascimento") or {},
            "cidade": d_principal.get("cidade") or {},
            "teve_checkout": teve_checkout,
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


def _tabela_leituras(pagina: int = 0, por_pagina: int = 20,
                     so_checkout: bool = False) -> tuple[str, int, int, int, int, int]:
    arquivos = sorted(config.DIR_LEITURAS.glob("*.json"), reverse=True)

    todos_dados: list[tuple[str, dict]] = []
    for arq in arquivos:
        try:
            d = json.loads(arq.read_text(encoding="utf-8"))
        except Exception:
            continue
        if (d.get("nome_completo") or "").strip().lower() == "pessoa de teste":
            continue          # fixtures da suite de testes
        todos_dados.append((arq.stem, d))

    total_leituras_geral = len(todos_dados)

    # Identifica progresso e checkout de todas as leituras
    progresso_map = obter_progresso_leituras(todos_dados)
    total_leituras_checkout = sum(1 for stem, _ in todos_dados if progresso_map.get(stem, {}).get("checkout"))

    # Agrupa por pessoa única
    todos_grupos = _agrupar_leituras_por_pessoa(todos_dados, progresso_map)
    total_pessoas_geral = len(todos_grupos)
    total_pessoas_checkout = sum(1 for g in todos_grupos if g["teve_checkout"])

    if so_checkout:
        grupos_filtrados = [g for g in todos_grupos if g["teve_checkout"]]
    else:
        grupos_filtrados = todos_grupos

    total_pessoas_exibidas = len(grupos_filtrados)
    total_leituras_exibidas = sum(g["total_envios"] for g in grupos_filtrados)

    total_paginas = max(1, (total_pessoas_exibidas + por_pagina - 1) // por_pagina)
    pagina_int = pagina.default if hasattr(pagina, "default") else int(pagina)
    pagina_ajustada = min(max(0, pagina_int), total_paginas - 1) if total_pessoas_exibidas > 0 else 0
    recorte_grupos = grupos_filtrados[pagina_ajustada * por_pagina:(pagina_ajustada + 1) * por_pagina]

    linhas = []
    tr_attrs = []
    for g in recorte_grupos:
        stem = g["stem_principal"]
        d = g["d_principal"]
        v, pr = d.get("veredito") or {}, d.get("precisao") or {}
        nasc = g["nascimento"]
        cid = g["cidade"]
        chegada_bsb, gerada_bsb = f_chegada_bsb(d, stem)
        rotulo_etapa = g["rotulo_etapa"]
        etapa_cls = "tag-etapa oferta" if g["max_tela"] == 10 else "tag-etapa"
        tag_etapa = f'<span class="{etapa_cls}">{html.escape(rotulo_etapa)}</span>'
        tag_chk = '<span class="tag-checkout sim">✦ SIM</span>' if g["teve_checkout"] else '<span class="tag-checkout nao">Não</span>'

        btn_acordeao = ""
        if g["total_envios"] > 1:
            btn_acordeao = (
                f' <button type="button" class="btn-acordeao" '
                f'onclick="toggleAcordeao(\'{html.escape(g["id_grupo"])}\', this);" '
                f'title="Ver todas as {g["total_envios"]} tentativas desta pessoa">'
                f'<span class="seta">▶</span> <span class="tag-rep" title="Preencheu o formulário {g["total_envios"]} vezes">{g["total_envios"]}x</span></button>'
            )

        nome_cell = html.escape(g["nome_completo"]) + btn_acordeao

        todos_ids_json = html.escape(json.dumps(g["todos_ids"])).replace("'", "&#39;")
        nome_js = html.escape(g["nome_completo"]).replace("'", "\\'")
        btn_del_principal = (
            f'<button type="button" class="btn-del" '
            f'onclick="abrirModalExcluir(\'{html.escape(stem)}\', \'{nome_js}\', {g["total_envios"]}, \'{todos_ids_json}\', false);" '
            f'title="Excluir dados desta pessoa">🗑️ Excluir</button>'
        )

        tr_attrs.append(f'id="row-pessoa-{stem}" class="tr-pessoa" data-checkout="{"1" if g["teve_checkout"] else "0"}"')
        linhas.append([
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
            btn_del_principal,
        ])

        # Sub-linhas para tentativas anteriores do acordeão
        for sub_stem, sub_d in g["outras_leituras"]:
            sub_v, sub_pr = sub_d.get("veredito") or {}, sub_d.get("precisao") or {}
            sub_nasc = sub_d.get("nascimento") or {}
            sub_chegada_bsb, sub_gerada_bsb = f_chegada_bsb(sub_d, sub_stem)
            sub_prog = progresso_map.get(sub_stem, {"max_tela": 7, "rotulo": "Tela 7 (Leitura)", "checkout": False})
            sub_rotulo_etapa = sub_prog["rotulo"]
            sub_etapa_cls = "tag-etapa oferta" if sub_prog["max_tela"] == 10 else "tag-etapa"
            sub_tag_etapa = f'<span class="{sub_etapa_cls}">{html.escape(sub_rotulo_etapa)}</span>'
            sub_tag_chk = '<span class="tag-checkout sim">✦ SIM</span>' if sub_prog["checkout"] else '<span class="tag-checkout nao">Não</span>'

            btn_del_sub = (
                f'<button type="button" class="btn-del" '
                f'onclick="abrirModalExcluir(\'{html.escape(sub_stem)}\', \'{nome_js}\', 1, \'[]\', true);" '
                f'title="Excluir apenas esta tentativa anterior">🗑️</button>'
            )

            tr_attrs.append(f'id="row-leitura-{sub_stem}" class="tr-subleitura grupo-{g["id_grupo"]}" style="display:none;" data-checkout="{"1" if sub_prog["checkout"] else "0"}"')
            linhas.append([
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
                btn_del_sub,
            ])

    if not linhas and so_checkout:
        corpo = '<p class="vazio">Nenhum visitante foi ao checkout neste período.</p>'
    elif not linhas:
        corpo = '<p class="vazio">Nenhuma leitura encontrada.</p>'
    else:
        corpo = _tabela([
            "id", "chegou ao quiz (bsb)", "preencheu dados (bsb)", "etapa alcançada", "checkout",
            "nome", "whatsapp", "nascimento", "uf", "área", "cenário", "casa", "hora nasc.", "tempo no quiz", "ações"
        ], linhas, tr_attrs=tr_attrs, tbody_id="tbody-leituras")

    return corpo, total_leituras_exibidas, total_paginas, total_pessoas_exibidas, total_pessoas_checkout, total_leituras_geral


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
           so_checkout: int = 0):
    dias_int = dias.default if hasattr(dias, "default") else int(dias)
    pag_leituras_int = pag_leituras.default if hasattr(pag_leituras, "default") else int(pag_leituras)
    d1, d2 = _periodo(de, ate, dias_int)
    # acolchoa um dia de cada lado: sessao que comeca 23h57 e continua depois da
    # meia-noite tem que ser lida inteira, senao aparece cortada em duas
    brutos = eventos.ler_dias(d1 - timedelta(days=1), d2 + timedelta(days=1))
    d = agregar(brutos, d1, d2, incluir_bots=bool(bots), incluir_teste=bool(teste))

    def link(rot, **kw):
        q = {"dias": kw.get("dias", dias_int)}
        if bots:
            q["bots"] = 1
        if teste:
            q["teste"] = 1
        if pag_leituras:
            q["pag_leituras"] = pag_leituras
        if so_checkout:
            q["so_checkout"] = 1
        qs = "&".join(f"{k}={v}" for k, v in q.items())
        on = " on" if kw.get("dias") == dias_int else ""
        return f'<a class="f{on}" href="/painel?{qs}">{rot}</a>'

    p = [f"<style>{ESTILO}</style><title>Painel · Bússola</title><div class=w>"]
    p.append(f"<h1>Bússola Astrológica</h1>")
    p.append(f'<p class="sub">{d1:%d/%m/%Y} a {d2:%d/%m/%Y} · '
             f'<b>{d.get("pessoas_unicas", d["sessoes"])}</b> pessoas únicas, '
             f'{d["sessoes"]} sessões no total ({d["abertas"]} ainda em andamento)</p>')
    p.append('<div class="filtros">' + link("hoje", dias=1) + link("7 dias", dias=7)
             + link("30 dias", dias=30) + link("90 dias", dias=90)
             + f'<a href="/painel?dias={dias}&bots={0 if bots else 1}&teste={teste}">'
             f'{"ocultar" if bots else "mostrar"} bots</a>'
             + f'<a href="/painel?dias={dias}&bots={bots}&teste={0 if teste else 1}">'
             f'{"ocultar" if teste else "mostrar"} meus testes</a></div>')

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
             '<button type="button" class="aba-btn on" data-tab="aba-funil" onclick="abrirAba(\'aba-funil\')">📊 Funil por Tela</button>'
             '<button type="button" class="aba-btn" data-tab="aba-leituras" onclick="abrirAba(\'aba-leituras\')">📖 Leituras</button>'
             '<button type="button" class="aba-btn" data-tab="aba-formulario" onclick="abrirAba(\'aba-formulario\')">📝 Formulário & Horário</button>'
             '<button type="button" class="aba-btn" data-tab="aba-astrologia" onclick="abrirAba(\'aba-astrologia\')">🔮 Áreas & Casas</button>'
             '<button type="button" class="aba-btn" data-tab="aba-agente" onclick="abrirAba(\'aba-agente\')">⚡ Saúde do Agente</button>'
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
    corpo_leituras, total_exibidos, total_pags, total_pessoas, total_chk, total_geral = _tabela_leituras(
        pag_leituras_int, por_pagina=20, so_checkout=bool(so_checkout)
    )

    def link_filtro_leituras(so_chk: int) -> str:
        q = {"dias": dias_int}
        if bots:
            q["bots"] = 1
        if teste:
            q["teste"] = 1
        if so_chk:
            q["so_checkout"] = 1
        qs = "&".join(f"{k}={v}" for k, v in q.items())
        url = f"/painel?{qs}#aba-leituras"
        cls_chk = " chk" if so_chk else ""
        cls_on = " on" if (bool(so_chk) == bool(so_checkout)) else ""
        rotulo = "✦ Só quem foi pro checkout" if so_chk else "Todas as leituras"
        cnt = total_chk if so_chk else total_geral
        return (f'<a href="{url}" class="btn-filtro-leituras{cls_chk}{cls_on}" '
                f'data-so-checkout="{so_chk}" onclick="return filtrarCheckoutClient({so_chk}, this, event);">'
                f'{rotulo} <span class="badge-count">{cnt}</span></a>')

    p.append('<div class="filtros-leituras">'
             + link_filtro_leituras(0)
             + link_filtro_leituras(1)
             + '</div>')

    p_params = {
        "dias": dias_int,
        "bots": bots if bots else None,
        "teste": teste if teste else None,
        "so_checkout": 1 if so_checkout else None,
    }
    rotulo_pag = "pessoas com checkout" if so_checkout else "pessoas únicas"
    barra_pag = _barra_paginacao(pag_leituras_int, total_pessoas, "/painel", p_params,
                                 por_pagina=20, param_nome="pag_leituras", hash_tab="#aba-leituras",
                                 rotulo_item=rotulo_pag)
    sub_tipo = "com checkout" if so_checkout else "no total"
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

    # ==================== ABA 4: SAÚDE DO AGENTE ====================
    p.append('<section class="aba-painel" id="aba-agente">')
    # ---- geração ----
    p.append("<h2>Saúde do agente</h2>")
    p.append(f'<div class="cards">'
             f'<div class="card"><b>{g["mediana_ms"]/1000:.1f}s</b><span>mediana</span></div>'
             f'<div class="card"><b>{g["p95_ms"]/1000:.1f}s</b><span>p95</span></div>'
             f'<div class="card"><b>{g["cacheadas"]}</b><span>vieram do cache</span></div>'
             f'<div class="card"><b>{g["reserva"]}</b><span>carta de reserva</span></div>'
             f'<div class="card"><b>{g["falhas"]}</b><span>falhas de cálculo</span></div></div>')
    p.append(f'<p class="nota">Tempo medido sobre {g["amostra_tempo"]} leitura(s) realmente geradas. '
             'As que vieram do cache ficam de fora: elas respondem em milissegundos e puxariam a '
             'mediana para baixo, escondendo lentidão real. Modelos usados: '
             + (", ".join(f"{html.escape(str(k))} ({v})" for k, v in g["modelos"]) or "—") + ".</p>")

    p.append(f'<h2>Leituras</h2><p class="nota">'
             f'<a href="#aba-leituras" onclick="abrirAba(\'aba-leituras\');return false;">ver a lista na aba Leituras</a>.</p>')
    p.append('</section>')

    p.append(_modal_confirmar_exclusao())
    p.append(f'<script>{JS_PAINEL}</script>')
    p.append("</div>")
    return HTMLResponse("".join(p), headers=CABECALHOS)


@router.get("/painel/leituras", response_class=HTMLResponse)
def lista(_=Depends(exigir_senha), pagina: int = Query(0, ge=0), so_checkout: int = 0):
    corpo, total_exibidos, total_pags, total_pessoas, total_chk, total_geral = _tabela_leituras(
        pagina, por_pagina=20, so_checkout=bool(so_checkout)
    )
    p_params = {"so_checkout": 1 if so_checkout else None}
    rotulo_pag = "pessoas com checkout" if so_checkout else "pessoas únicas"
    barra_pag = _barra_paginacao(pagina, total_pessoas, "/painel/leituras", p_params,
                                 por_pagina=20, param_nome="pagina", rotulo_item=rotulo_pag)

    def link_filtro_lista(so_chk: int) -> str:
        q = {}
        if so_chk:
            q["so_checkout"] = 1
        qs = ("?" + "&".join(f"{k}={v}" for k, v in q.items())) if q else ""
        url = f"/painel/leituras{qs}"
        cls_chk = " chk" if so_chk else ""
        cls_on = " on" if (bool(so_chk) == bool(so_checkout)) else ""
        rotulo = "✦ Só quem foi pro checkout" if so_chk else "Todas as leituras"
        cnt = total_chk if so_chk else total_geral
        return (f'<a href="{url}" class="btn-filtro-leituras{cls_chk}{cls_on}" '
                f'data-so-checkout="{so_chk}" onclick="return filtrarCheckoutClient({so_chk}, this, event);">'
                f'{rotulo} <span class="badge-count">{cnt}</span></a>')

    botoes_filtro = ('<div class="filtros-leituras">'
                     + link_filtro_lista(0)
                     + link_filtro_lista(1)
                     + '</div>')

    sub_tipo = "com checkout" if so_checkout else "no total"
    txt_pessoas = f"{total_pessoas} pessoa única" if total_pessoas == 1 else f"{total_pessoas} pessoas únicas"
    txt_envios = f"{total_exibidos} envio" if total_exibidos == 1 else f"{total_exibidos} envios"
    return HTMLResponse(
        f"<style>{ESTILO}</style><title>Leituras</title><div class=w>"
        f'<h1>Leituras</h1><p class="sub" id="sub-leituras-info"><b>{total_pessoas}</b> {txt_pessoas} {sub_tipo} ({txt_envios} no total) · mostrando 20 por página · '
        f'<a href="/painel#aba-leituras">voltar ao painel</a></p>'
        f'{botoes_filtro}'
        f'{corpo}'
        f'{barra_pag}'
        f'{_modal_confirmar_exclusao()}'
        f'<p class="nota">Clique no ID para ver o detalhe e o mapa astrológico completo de cada leitura.</p></div>'
        f'<script>{JS_PAINEL}</script>',
        headers=CABECALHOS)


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
    btn_del = (f'<button type="button" class="btn-del" style="margin-left:8px;" '
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
        f'<a href="/painel#aba-leituras">voltar ao painel</a> {btn_del}</p>'
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

