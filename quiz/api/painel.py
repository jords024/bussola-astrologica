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
from servicos import eventos
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
    """Data de nascimento completa com dia, mês e ano de 4 dígitos."""
    if not nasc:
        return "—"
    return f"{nasc.get('dia', '?'):0>2}/{nasc.get('mes', '?'):0>2}/{nasc.get('ano', '????')}"


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


def f_chegada_bsb(d: dict, arq_stem: str) -> tuple[str, str]:
    """Retorna (chegou_em_bsb, gerado_em_bsb) formatados no horário de Brasília (UTC-3)."""
    if d.get("chegou_em_bsb") and d.get("gravado_em_bsb"):
        return str(d["chegou_em_bsb"]), str(d["gravado_em_bsb"])

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
        dt_chegada_bsb.strftime("%d/%m/%Y %H:%M:%S"),
        dt_gerada_bsb.strftime("%d/%m/%Y %H:%M:%S")
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
.tbl-wrap{width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch;margin-bottom:12px}
.paginacao{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin:16px 0 8px;padding:12px 0;border-top:1px solid var(--line)}
.pag-info{font-size:12.5px;color:var(--sand2)}
.pag-links{display:flex;align-items:center;gap:6px}
.pag-btn{display:inline-flex;align-items:center;justify-content:center;padding:6px 12px;border:1px solid var(--line);border-radius:6px;color:var(--sand);text-decoration:none;font-size:12px;min-width:32px;transition:all .15s ease}
.pag-btn:hover{border-color:var(--amber);color:var(--amber);background:rgba(229,169,60,.08)}
.pag-btn.on{border-color:var(--amber);background:var(--amber);color:#12100C;font-weight:700}
.pag-btn.disabled{opacity:.35;pointer-events:none;cursor:default;color:var(--sand2)}
@keyframes fadein{from{opacity:0;transform:translateY(3px)}to{opacity:1;transform:none}}
"""


def _tabela(cabecalhos: list[str], linhas: list[list[str]], classes: str = "") -> str:
    if not linhas:
        return '<p class="vazio">Ainda sem dados neste período.</p>'
    th = "".join(f'<th class="{"n" if h.startswith("#") else ""}">{html.escape(h.lstrip("#"))}</th>'
                 for h in cabecalhos)
    tr = ""
    for l in linhas:
        tds = "".join(f'<td class="{"n" if h.startswith("#") else ""}">{c}</td>'
                      for h, c in zip(cabecalhos, l))
        tr += f"<tr>{tds}</tr>"
    return f'<div class="tbl-wrap"><table class="{classes}"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'


def _tabela_leituras(pagina: int = 0, por_pagina: int = 20) -> tuple[str, int, int]:
    arquivos = sorted(config.DIR_LEITURAS.glob("*.json"), reverse=True)
    total_arquivos = len(arquivos)
    total_paginas = max(1, (total_arquivos + por_pagina - 1) // por_pagina)
    pagina_ajustada = min(max(0, pagina), total_paginas - 1) if total_arquivos > 0 else 0
    recorte = arquivos[pagina_ajustada * por_pagina:(pagina_ajustada + 1) * por_pagina]

    linhas = []
    for arq in recorte:
        try:
            d = json.loads(arq.read_text(encoding="utf-8"))
        except Exception:
            continue
        if (d.get("nome_completo") or "").strip().lower() == "pessoa de teste":
            continue          # fixtures da suite de testes
        v, pr = d.get("veredito") or {}, d.get("precisao") or {}
        nasc = d.get("nascimento") or {}
        cid = d.get("cidade") or {}
        chegada_bsb, gerada_bsb = f_chegada_bsb(d, arq.stem)
        linhas.append([
            f'<a href="/painel/leitura/{html.escape(arq.stem)}">{html.escape(arq.stem[:15])}</a>',
            f'<span style="white-space:nowrap;" title="Gerada às {html.escape(gerada_bsb)} (BSB)">{html.escape(chegada_bsb)}</span>',
            html.escape(d.get("nome_completo") or "—"),
            f_data(nasc),
            html.escape(cid.get("uf") or cid.get("nome") or "—"),
            html.escape(str((d.get("quiz") or {}).get("area") or "—")),
            html.escape(str(v.get("tipo") or "—")),
            "—" if not v.get("casa_eleita_real") else f'Casa {v.get("casa_aberta")}',
            f_hora(nasc, pr),
            f_tempo(d.get("tempo_quiz_ms")),
            f_wa(d.get("whatsapp")),
        ])
    corpo = _tabela(["id", "chegou ao quiz (bsb)", "nome", "nascimento", "uf", "área", "cenário",
                     "casa", "hora nasc.", "tempo no quiz", "whatsapp"], linhas)
    return corpo, total_arquivos, total_paginas


def _barra_paginacao(pagina: int, total_arquivos: int, base_url: str, params: dict,
                     por_pagina: int = 20, param_nome: str = "pag_leituras",
                     hash_tab: str = "") -> str:
    if total_arquivos == 0:
        return ""
    total_paginas = max(1, (total_arquivos + por_pagina - 1) // por_pagina)
    pagina = min(max(0, pagina), total_paginas - 1)

    inicio = pagina * por_pagina + 1
    fim = min((pagina + 1) * por_pagina, total_arquivos)
    info = f"Mostrando <b>{inicio}–{fim}</b> de <b>{total_arquivos}</b> leituras · Página {pagina + 1} de {total_paginas}"

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
           pag_leituras: int = Query(0, ge=0)):
    d1, d2 = _periodo(de, ate, dias)
    # acolchoa um dia de cada lado: sessao que comeca 23h57 e continua depois da
    # meia-noite tem que ser lida inteira, senao aparece cortada em duas
    brutos = eventos.ler_dias(d1 - timedelta(days=1), d2 + timedelta(days=1))
    d = agregar(brutos, d1, d2, incluir_bots=bool(bots), incluir_teste=bool(teste))

    def link(rot, **kw):
        q = {"dias": kw.get("dias", dias)}
        if bots:
            q["bots"] = 1
        if teste:
            q["teste"] = 1
        if pag_leituras:
            q["pag_leituras"] = pag_leituras
        qs = "&".join(f"{k}={v}" for k, v in q.items())
        on = " on" if kw.get("dias") == dias else ""
        return f'<a class="f{on}" href="/painel?{qs}">{rot}</a>'

    p = [f"<style>{ESTILO}</style><title>Painel · Bússola</title><div class=w>"]
    p.append(f"<h1>Bússola Astrológica</h1>")
    p.append(f'<p class="sub">{d1:%d/%m/%Y} a {d2:%d/%m/%Y} · '
             f'{d["sessoes"]} sessões, {d["abertas"]} ainda em andamento</p>')
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
    chegaram_oferta = oferta_item["sessoes"] if oferta_item else 0
    checkout_item = next((f for f in d["funil"] if f["tela"] == "✦"), None)
    clicaram_checkout = checkout_item["sessoes"] if checkout_item else d.get("checkout", {}).get("cliques", 0)

    tempos = d.get("tempos") or {}
    p.append('<div class="cards">')
    for valor, rot in [
        (d["sessoes"], "sessões"),
        (f_tempo(tempos.get("mediana_sessao_ms")), "tempo médio no funil"),
        (f_tempo(tempos.get("mediana_ate_oferta_ms")), "tempo até a oferta"),
        (d["funil"][5]["sessoes"], "chegaram aos dados"),
        (g["total"], "cartas entregues"),
        (chegaram_oferta, "chegaram à oferta"),
        (clicaram_checkout, "foram ao checkout"),
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
            str(f["sessoes"]),
            f_tempo(f.get("tempo_na_tela_ms")),
            f_tempo(f.get("cronometro_ms")),
            _n(f["pct_do_topo"]),
            "—" if f["queda"] in (None, 0) else f'−{f["queda"]}',
            str(f["parou_aqui"]),
        ])
    p.append(_tabela(["etapa / tela", "", "#sessões", "tempo na tela", "cronômetro", "#% do topo", "#queda", "#pararam aqui"], linhas))
    p.append('<p class="nota">Conta quem <b>chegou pelo menos uma vez</b> em cada tela. '
             '<b>Tempo na tela:</b> mediana do tempo de permanência nesta etapa específica. '
             '<b>Cronômetro:</b> tempo acumulado desde o momento em que o visitante entrou na página até atingir a tela. '
             'A linha <b>✦ Clique no Checkout</b> registra quem apertou o botão de compra na oferta.</p>')
    p.append('</section>')

    # ==================== ABA 2: LEITURAS ====================
    p.append('<section class="aba-painel" id="aba-leituras">')
    p.append("<h2>Leituras Geradas</h2>")
    corpo_leituras, total_leituras, total_pags = _tabela_leituras(pag_leituras, por_pagina=20)
    p_params = {"dias": dias, "bots": bots if bots else None, "teste": teste if teste else None}
    barra_pag = _barra_paginacao(pag_leituras, total_leituras, "/painel", p_params,
                                 por_pagina=20, param_nome="pag_leituras", hash_tab="#aba-leituras")
    p.append(f'<p class="sub">{total_leituras} leitura(s) no total · mostrando 20 por página · clique no ID para ver o mapa astrológico e o detalhe completo.</p>')
    p.append(corpo_leituras)
    p.append(barra_pag)
    p.append('</section>')

    # ==================== ABA 2: FORMULÁRIO & HORÁRIO ====================
    p.append('<section class="aba-painel" id="aba-formulario">')
    fo = d["formulario"]
    p.append("<h2>Onde a tela dos dados trava</h2>")
    p.append(f'<div class="cards"><div class="card"><b>{fo["chegaram"]}</b><span>chegaram</span></div>'
             f'<div class="card"><b>{fo["enviaram"]}</b><span>enviaram</span></div>'
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

    p.append('<script>'
             'function abrirAba(id){'
             'document.querySelectorAll(".aba-btn").forEach(function(b){b.classList.toggle("on",b.getAttribute("data-tab")===id);});'
             'document.querySelectorAll(".aba-painel").forEach(function(s){s.classList.toggle("on",s.id===id);});'
             'try{history.replaceState(null,"","#"+id);localStorage.setItem("painel_aba_ativa",id);}catch(e){}'
             '}'
             '(function(){'
             'var hash=(location.hash||"").replace("#","");'
             'var salva="";try{salva=localStorage.getItem("painel_aba_ativa");}catch(e){}'
             'var alvo=hash||salva;'
             'if(alvo&&document.getElementById(alvo)){abrirAba(alvo);}'
             '})();'
             '</script>')
    p.append("</div>")
    return HTMLResponse("".join(p), headers=CABECALHOS)


@router.get("/painel/leituras", response_class=HTMLResponse)
def lista(_=Depends(exigir_senha), pagina: int = Query(0, ge=0)):
    corpo, total_arquivos, total_pags = _tabela_leituras(pagina, por_pagina=20)
    barra_pag = _barra_paginacao(pagina, total_arquivos, "/painel/leituras", {},
                                 por_pagina=20, param_nome="pagina")
    return HTMLResponse(
        f"<style>{ESTILO}</style><title>Leituras</title><div class=w>"
        f'<h1>Leituras</h1><p class="sub">{total_arquivos} no total · mostrando 20 por página · '
        f'<a href="/painel#aba-leituras">voltar ao painel</a></p>{corpo}'
        f'{barra_pag}'
        f'<p class="nota">Clique no ID para ver o detalhe e o mapa astrológico completo de cada leitura.</p></div>',
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
    h_str = f_hora(n, pr)
    uf_str = f' ({html.escape(cid.get("uf"))})' if cid.get("uf") else ''
    t_quiz_str = f' · tempo no quiz: {f_tempo(d.get("tempo_quiz_ms"))}' if d.get("tempo_quiz_ms") else ''
    ident = (f'{html.escape(d.get("nome_completo") or "—")} · '
             f'chegou ao quiz: <b style="color:var(--amber);">{html.escape(chegada_bsb)} (BSB)</b> · '
             f'gerada em: {html.escape(gerada_bsb)} (BSB) · '
             f'{f_data(n)} ({h_str}) · '
             f'{html.escape(cid.get("nome") or "—")}{uf_str} · '
             f'{f_wa(d.get("whatsapp"))}'
             f'{t_quiz_str}')

    ps = "".join(f"<p>{html.escape(x)}</p>" for x in (c.get("paragrafos") or []))
    notas = "".join(f"<li>{html.escape(x)}</li>" for x in (c.get("notas") or []))
    return HTMLResponse(
        f"<style>{ESTILO}</style><title>{html.escape(leitura_id)}</title><div class=w>"
        f'<h1>{html.escape(leitura_id)}</h1><p class="sub">{ident} · '
        f'<a href="/painel#aba-leituras">voltar ao painel</a></p>'
        f'<h2>{html.escape(c.get("selo",""))}</h2>'
        f'<p><b>{html.escape(c.get("titulo",""))}</b></p>'
        f'<p style="color:var(--amber)">{html.escape(c.get("destaque",""))}</p>'
        f'{ps}<p class="nota">{html.escape(c.get("espera") or "")} '
        f'{html.escape(c.get("janela") or "")}</p>'
        f'<h2>cálculo</h2><ul class="nota">{notas}</ul>'
        f'<h2>veredito</h2><pre class="nota">'
        f'{html.escape(json.dumps(d.get("veredito"), ensure_ascii=False, indent=1))}</pre>'
        f'<h2>meta</h2><pre class="nota">'
        f'{html.escape(json.dumps(d.get("meta"), ensure_ascii=False, indent=1))}</pre></div>',
        headers=CABECALHOS)
