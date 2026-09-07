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
from datetime import date, datetime, timedelta
from typing import Optional

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
    return f'<table class="{classes}"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>'


@router.get("/painel", response_class=HTMLResponse)
def painel(request: Request, _=Depends(exigir_senha),
           de: Optional[str] = None, ate: Optional[str] = None,
           dias: int = Query(7, ge=1, le=365),
           bots: int = 0, teste: int = 0):
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
    p.append('<div class="cards">')
    for valor, rot in [
        (d["sessoes"], "sessões"),
        (d["funil"][5]["sessoes"], "chegaram aos dados"),
        (g["total"], "cartas entregues"),
        (sum(1 for _ in []) or d["funil"][9]["sessoes"], "chegaram à oferta"),
        (f'{g["mediana_ms"]/1000:.1f}s', "mediana do agente"),
        (g["reserva"], "cartas de reserva"),
    ]:
        p.append(f'<div class="card"><b>{valor}</b><span>{rot}</span></div>')
    p.append("</div>")

    # ---- navegação de abas ----
    p.append('<nav class="abas">'
             '<button type="button" class="aba-btn on" data-tab="aba-funil" onclick="abrirAba(\'aba-funil\')">📊 Funil por Tela</button>'
             '<button type="button" class="aba-btn" data-tab="aba-formulario" onclick="abrirAba(\'aba-formulario\')">📝 Formulário & Horário</button>'
             '<button type="button" class="aba-btn" data-tab="aba-astrologia" onclick="abrirAba(\'aba-astrologia\')">🔮 Áreas & Casas</button>'
             '<button type="button" class="aba-btn" data-tab="aba-agente" onclick="abrirAba(\'aba-agente\')">⚡ Saúde do Agente</button>'
             '</nav>')

    # ==================== ABA 1: FUNIL ====================
    p.append('<section class="aba-painel on" id="aba-funil">')
    p.append("<h2>Funil por tela</h2>")
    linhas = []
    for f in d["funil"]:
        linhas.append([
            f'{f["tela"]} · {html.escape(f["nome"])}',
            f'<div class="bar">{_barra(f["pct_do_topo"])}</div>',
            str(f["sessoes"]), _n(f["pct_do_topo"]),
            "—" if f["queda"] in (None, 0) else f'−{f["queda"]}',
            str(f["parou_aqui"]),
        ])
    p.append(_tabela(["tela", "", "#sessões", "#% do topo", "#queda", "#pararam aqui"], linhas))
    p.append('<p class="nota">Conta quem <b>chegou pelo menos uma vez</b> em cada tela, não a tela '
             'atual: com o botão voltar, quem chegou na leitura e voltou aos dados não pode contar '
             'como abandono nos dados. A tela 6 não é conteúdo, é a espera do cálculo — a queda ali '
             'mede a paciência com a demora do agente, não a copy.</p>')
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
    p.append(_tabela(["modo", "#sessões", "#chegaram à carta", "#chegaram à oferta"],
                     [[html.escape(str(h["modo"])), str(h["n"]),
                       f'{h["leitura"]} ({_n(h["pct_leitura"])})',
                       f'{h["oferta"]} ({_n(h["pct_oferta"])})'] for h in d["horario"]]))
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
             f'<a href="/painel/leituras">ver a lista de leituras geradas</a> — dados mascarados.</p>')
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
    # o id comeca com AAAAMMDD-HHMMSS, entao ordem alfabetica e ordem cronologica
    arquivos = sorted(config.DIR_LEITURAS.glob("*.json"), reverse=True)
    recorte = arquivos[pagina * 50:(pagina + 1) * 50]

    linhas = []
    for arq in recorte:
        try:
            d = json.loads(arq.read_text(encoding="utf-8"))
        except Exception:
            continue
        if (d.get("nome_completo") or "").strip().lower() == "pessoa de teste":
            continue          # fixtures da suite de testes
        v, pr = d.get("veredito") or {}, d.get("precisao") or {}
        linhas.append([
            f'<a href="/painel/leitura/{html.escape(arq.stem)}">{html.escape(arq.stem[:15])}</a>',
            html.escape(m_nome(d.get("nome_completo", ""))),
            m_data(d.get("nascimento") or {}),
            html.escape((d.get("cidade") or {}).get("uf") or "—"),
            html.escape(str((d.get("quiz") or {}).get("area") or "—")),
            html.escape(str(v.get("tipo") or "—")),
            "—" if not v.get("casa_eleita_real") else f'Casa {v.get("casa_aberta")}',
            html.escape(str(pr.get("modo_hora") or "—")),
            m_fone(d.get("whatsapp", "")),
        ])
    corpo = _tabela(["id", "nome", "nascimento", "uf", "área", "cenário",
                     "casa", "hora", "whatsapp"], linhas)
    nav = ""
    if pagina:
        nav += f'<a href="/painel/leituras?pagina={pagina-1}">← anteriores</a> '
    if len(arquivos) > (pagina + 1) * 50:
        nav += f'<a href="/painel/leituras?pagina={pagina+1}">próximas →</a>'
    return HTMLResponse(
        f"<style>{ESTILO}</style><title>Leituras</title><div class=w>"
        f'<h1>Leituras</h1><p class="sub">{len(arquivos)} no total · '
        f'<a href="/painel">voltar ao painel</a></p>{corpo}'
        f'<p class="nota">Nome, data de nascimento e telefone aparecem mascarados. '
        f'O conteúdo completo fica na página de cada leitura.</p><p class="nota">{nav}</p></div>',
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

    if revelar:
        ident = (f'{html.escape(d.get("nome_completo",""))} · '
                 f'{n.get("dia")}/{n.get("mes")}/{n.get("ano")} '
                 f'{n.get("hora","?")}h{n.get("minuto",0):0>2} · '
                 f'{html.escape(cid.get("nome",""))} · {html.escape(d.get("whatsapp","—"))}')
    else:
        ident = (f'{html.escape(m_nome(d.get("nome_completo","")))} · {m_data(n)} · '
                 f'{html.escape(cid.get("uf","—"))} · {m_fone(d.get("whatsapp",""))} '
                 f'· <a href="?revelar=1">revelar</a>')

    ps = "".join(f"<p>{html.escape(x)}</p>" for x in (c.get("paragrafos") or []))
    notas = "".join(f"<li>{html.escape(x)}</li>" for x in (c.get("notas") or []))
    return HTMLResponse(
        f"<style>{ESTILO}</style><title>{html.escape(leitura_id)}</title><div class=w>"
        f'<h1>{html.escape(leitura_id)}</h1><p class="sub">{ident} · '
        f'<a href="/painel/leituras">voltar</a></p>'
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
