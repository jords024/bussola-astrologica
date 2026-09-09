# -*- coding: utf-8 -*-
"""Agregação dos eventos em números de funil.

Função pura sobre uma lista de eventos: sem FastAPI aqui dentro, para poder
testar com listas sintéticas.

As decisões que impedem o painel de mentir estão todas neste arquivo, e cada
uma tem um comentário dizendo o que aconteceria sem ela.
"""
from __future__ import annotations

import statistics
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Iterable, Optional

FUSO_BSB = timezone(timedelta(hours=-3))

TELAS = [
    (0, "O chamado"), (1, "O mecanismo"), (2, "A área"), (3, "O espelho"),
    (4, "A quebra"), (5, "Os dados"), (6, "O cálculo"), (7, "A leitura"),
    (8, "As 12 portas"), (9, "A ponte"), (10, "A oferta"),
]

# Abaixo disto, porcentagem engana mais do que informa: "33%" a partir de três
# sessões move decisão que não deveria ser movida.
MIN_PARA_PORCENTAGEM = 20

# Quem ainda está lendo a carta no momento em que o painel abre não é desistente.
MINUTOS_SESSAO_ABERTA = 30


def _ts(ev: dict) -> Optional[datetime]:
    try:
        dt = datetime.fromisoformat(ev["ts"])
        if dt.tzinfo is None:
            return dt.replace(tzinfo=FUSO_BSB)
        return dt.astimezone(FUSO_BSB)
    except Exception:
        return None


def _mediana(valores: Iterable[float]) -> Optional[float]:
    v = [x for x in valores if x is not None and x >= 0]
    return round(statistics.median(v), 1) if v else None


def _chave_pessoa(s: dict) -> str:
    aid = str(s.get("aid") or "").strip()
    if aid:
        return f"aid:{aid}"
    sid = str(s.get("sid") or "").strip()
    return f"sid:{sid}" if sid else ""


def agregar(eventos: Iterable[dict], de: date, ate: date,
            incluir_bots: bool = False, incluir_teste: bool = False,
            agora: Optional[datetime] = None) -> dict:
    """Recebe eventos de um período JÁ ACOLCHOADO (um dia a mais de cada lado).

    Sem o acolchoamento, uma sessão que começa 23h57 aparece cortada em duas:
    uma que "começa na tela 6" e outra que "abandona na tela 5".
    """
    vistos: set[tuple] = set()
    ses: dict[str, dict] = {}

    for ev in eventos:
        sid = ev.get("sid")
        if not sid:
            continue
        if ev.get("bot") and not incluir_bots:
            continue
        if ev.get("teste") and not incluir_teste:
            continue

        # (sid, seq) e a chave de idempotencia. O escritor nao deduplica; quem
        # deduplica e o leitor, aqui, na mesma passada que agrega. Sem isto, o
        # reenvio da fila apos um fechamento no meio do voo conta duas vezes.
        chave = (sid, ev.get("seq"), ev.get("evt"))
        if ev.get("seq", -1) >= 0:
            if chave in vistos:
                continue
            vistos.add(chave)

        s = ses.get(sid)
        if s is None:
            s = ses[sid] = {
                "sid": sid,
                "telas": set(), "primeiro": None, "ultimo": None,
                "area": None, "modo_hora": None, "ultimo_campo": None,
                "campos": set(), "form_envio": False, "form_erros": [],
                "leitura": None, "oferta": False, "disp": ev.get("disp"),
                "contato": False, "falha": None,
                "duracoes_tela": defaultdict(list),
                "cronometro_tela": {0: 0.0},
                "tempo_checkout": None,
                "aid": str(ev.get("aid") or "").strip(),
            }
        elif not s.get("aid"):
            novo_aid = str(ev.get("aid") or (ev.get("props") or {}).get("aid") or (ev.get("props") or {}).get("cliente_id") or "").strip()
            if novo_aid:
                s["aid"] = novo_aid
        t = _ts(ev)
        if t:
            if s["primeiro"] is None or t < s["primeiro"]:
                s["primeiro"] = t
            if s["ultimo"] is None or t > s["ultimo"]:
                s["ultimo"] = t

        evt, props = ev.get("evt"), (ev.get("props") or {})
        if evt == "tela":
            for k in ("de", "para"):
                v = props.get(k)
                if isinstance(v, int) and 0 <= v <= 10:
                    s["telas"].add(v)
            de_tela = props.get("de")
            para_tela = props.get("para")
            ms_ant = props.get("ms_na_anterior")
            if isinstance(de_tela, int) and 0 <= de_tela <= 10 and isinstance(ms_ant, (int, float)) and 0 <= ms_ant < 1800000:
                s["duracoes_tela"][de_tela].append(float(ms_ant))
            ms_acum = props.get("ms_acumulado")
            if isinstance(para_tela, int) and 0 <= para_tela <= 10 and para_tela not in s["cronometro_tela"]:
                if isinstance(ms_acum, (int, float)) and ms_acum >= 0:
                    s["cronometro_tela"][para_tela] = float(ms_acum)
                elif t and s["primeiro"] and t >= s["primeiro"]:
                    s["cronometro_tela"][para_tela] = (t - s["primeiro"]).total_seconds() * 1000
        elif evt == "escolha":
            # a ULTIMA escolha vale: quem clica em tres opcoes antes de decidir
            # nao pode virar tres pessoas na distribuicao de areas
            if props.get("campo") == "area":
                s["area"] = props.get("valor")
        elif evt == "form_campo":
            if props.get("estado") == "preenchido":
                s["campos"].add(props.get("campo"))
                s["ultimo_campo"] = props.get("campo")
        elif evt == "form_erro":
            s["form_erros"].extend(props.get("faltando") or [])
        elif evt == "form_envio":
            s["form_envio"] = True
            s["modo_hora"] = props.get("modo_hora")
            ms_tela5 = props.get("ms_na_tela5")
            if isinstance(ms_tela5, (int, float)) and 0 <= ms_tela5 < 1800000:
                s["duracoes_tela"][5].append(float(ms_tela5))
        elif evt == "leitura_entregue":
            s["leitura"] = props
            s["modo_hora"] = s["modo_hora"] or props.get("modo_hora")
            s["area"] = s["area"] or props.get("area")
        elif evt == "leitura_falha":
            s["falha"] = props.get("motivo")
        elif evt == "oferta_clique":
            s["oferta"] = True
            ms_tela = props.get("ms_na_tela")
            if isinstance(ms_tela, (int, float)) and 0 <= ms_tela < 1800000:
                s["duracoes_tela"][10].append(float(ms_tela))
            ms_acum = props.get("ms_acumulado")
            if isinstance(ms_acum, (int, float)) and ms_acum >= 0:
                s["tempo_checkout"] = float(ms_acum)
            elif t and s["primeiro"] and t >= s["primeiro"]:
                s["tempo_checkout"] = (t - s["primeiro"]).total_seconds() * 1000
        elif evt == "saida":
            tela_s = props.get("tela")
            ms_tela = props.get("ms_na_tela")
            if isinstance(tela_s, int) and 0 <= tela_s <= 10 and isinstance(ms_tela, (int, float)) and 0 <= ms_tela < 1800000:
                s["duracoes_tela"][tela_s].append(float(ms_tela))
        elif evt == "contato_enviado":
            s["contato"] = True

    # o dia de uma sessao e o dia em que ela COMECOU, nao o dia de cada evento
    agora = agora or datetime.now(FUSO_BSB)
    sessoes = []
    for sid, s in ses.items():
        if s["primeiro"] is None:
            continue
        if not (de <= s["primeiro"].date() <= ate):
            continue
        s["sid"] = sid
        s["max_tela"] = max(s["telas"]) if s["telas"] else 0
        try:
            aberta = (agora - s["ultimo"]) < timedelta(minutes=MINUTOS_SESSAO_ABERTA)
        except Exception:
            aberta = False
        s["aberta"] = aberta
        sessoes.append(s)

    duracoes_sessoes = []
    for s in sessoes:
        if s["primeiro"] and s["ultimo"]:
            delta_ms = (s["ultimo"] - s["primeiro"]).total_seconds() * 1000
            if 0 < delta_ms < 1800000:
                duracoes_sessoes.append(delta_ms)

    tempos = {
        "mediana_sessao_ms": _mediana(duracoes_sessoes),
        "mediana_ate_oferta_ms": _mediana([s["cronometro_tela"][10] for s in sessoes if 10 in s.get("cronometro_tela", {})]),
        "mediana_ate_checkout_ms": _mediana([s["tempo_checkout"] for s in sessoes if s.get("tempo_checkout") is not None]),
    }

    pessoas_unicas = len({_chave_pessoa(s) for s in sessoes if _chave_pessoa(s)})

    return {
        "periodo": {"de": de.isoformat(), "ate": ate.isoformat()},
        "sessoes": len(sessoes),
        "pessoas_unicas": pessoas_unicas,
        "abertas": sum(1 for s in sessoes if s["aberta"]),
        "funil": _funil(sessoes),
        "checkout": {
            "cliques": sum(1 for s in sessoes if s["oferta"]),
            "pct_da_oferta": pct(sum(1 for s in sessoes if s["oferta"]), sum(1 for s in sessoes if 10 in s["telas"])),
        },
        "tempos": tempos,
        "formulario": _formulario(sessoes),
        "areas": _contagem(s["area"] for s in sessoes if s["area"]),
        "cenarios": _cenarios(sessoes),
        "casas": _casas(sessoes),
        "horario": _horario(sessoes),
        "geracao": _geracao(sessoes),
        "dispositivos": _contagem(s["disp"] for s in sessoes if s["disp"]),
    }


def pct(parte: int, total: int) -> Optional[float]:
    """None abaixo do mínimo: o painel imprime '—' em vez de um número que mente."""
    if total < MIN_PARA_PORCENTAGEM or not total:
        return None
    return round(parte * 100 / total, 1)


def _funil(sessoes: list[dict]) -> list[dict]:
    """Conta quem CHEGOU pelo menos uma vez em cada tela.

    Nunca "tela atual": com o botão voltar, o conjunto de telas de uma sessão
    não é um prefixo, e quem chegou na 7 e voltou para a 5 apareceria como
    abandono na 5.
    """
    base = sum(1 for s in sessoes if 0 in s["telas"]) or len(sessoes)
    linhas = []
    anterior = None
    for n, nome in TELAS:
        alcanceou = sum(1 for s in sessoes if n in s["telas"])
        alcanceou_pessoas = len({_chave_pessoa(s) for s in sessoes if n in s["telas"] and _chave_pessoa(s)})
        # quem parou aqui: nunca passou desta tela e nao esta com a sessao aberta
        if n == 10:
            parou = sum(1 for s in sessoes if s["max_tela"] == 10 and not s["oferta"] and not s["aberta"])
        else:
            parou = sum(1 for s in sessoes if s["max_tela"] == n and not s["aberta"])
        duracoes = [d for s in sessoes for d in s.get("duracoes_tela", {}).get(n, [])]
        cronos = [s["cronometro_tela"][n] for s in sessoes if n in s.get("cronometro_tela", {})]

        linhas.append({
            "tela": n, "nome": nome,
            "sessoes": alcanceou,
            "pessoas": alcanceou_pessoas,
            "tempo_na_tela_ms": _mediana(duracoes),
            "cronometro_ms": _mediana(cronos),
            "pct_do_topo": pct(alcanceou, base),
            "parou_aqui": parou,
            "queda": (anterior - alcanceou) if anterior is not None else None,
        })
        anterior = alcanceou

    # Etapa de conversão final: clique no botão da oferta direcionando ao checkout da Hotmart
    clicou_checkout = sum(1 for s in sessoes if s["oferta"])
    clicou_checkout_pessoas = len({_chave_pessoa(s) for s in sessoes if s["oferta"] and _chave_pessoa(s)})
    duracoes_checkout = [d for s in sessoes if s.get("oferta") for d in s.get("duracoes_tela", {}).get(10, [])]
    cronos_checkout = [s["tempo_checkout"] for s in sessoes if s.get("tempo_checkout") is not None]
    linhas.append({
        "tela": "✦",
        "nome": "Clique no Checkout",
        "sessoes": clicou_checkout,
        "pessoas": clicou_checkout_pessoas,
        "tempo_na_tela_ms": _mediana(duracoes_checkout),
        "cronometro_ms": _mediana(cronos_checkout),
        "pct_do_topo": pct(clicou_checkout, base),
        "parou_aqui": clicou_checkout,
        "queda": (anterior - clicou_checkout) if anterior is not None else None,
    })
    return linhas


def _formulario(sessoes: list[dict]) -> dict:
    """Onde a tela 5 trava."""
    chegou = [s for s in sessoes if 5 in s["telas"]]
    travou = [s for s in chegou if not s["form_envio"] and not s["aberta"]]
    # "chegou e nao tocou em nada" e um problema diferente de "preencheu 4 de 5":
    # o primeiro e a tela assustando, o segundo e a tela derrotando
    intacto = sum(1 for s in travou if not s["campos"])
    erros = Counter()
    for s in chegou:
        erros.update(s["form_erros"])
    return {
        "chegaram": len(chegou),
        "chegaram_pessoas": len({_chave_pessoa(s) for s in chegou if _chave_pessoa(s)}),
        "enviaram": sum(1 for s in chegou if s["form_envio"]),
        "enviaram_pessoas": len({_chave_pessoa(s) for s in chegou if s["form_envio"] and _chave_pessoa(s)}),
        "travaram": len(travou),
        "travaram_pessoas": len({_chave_pessoa(s) for s in travou if _chave_pessoa(s)}),
        "sem_tocar": intacto,
        "ultimo_campo": _contagem(s["ultimo_campo"] for s in travou if s["ultimo_campo"]),
        "faltou": erros.most_common(6),
    }


def _cenarios(sessoes: list[dict]) -> dict:
    """Só onde a casa saiu do cálculo.

    Sem hora confiável não há placar de casas. Misturar esses casos aqui faria
    um cenário dominar por motivo que nada tem a ver com os pesos.
    """
    reais = [s["leitura"] for s in sessoes
             if s["leitura"] and s["leitura"].get("casa_eleita_real")]
    fora = sum(1 for s in sessoes
               if s["leitura"] and not s["leitura"].get("casa_eleita_real"))
    c = Counter(l.get("cenario") for l in reais)
    total = sum(c.values())
    return {
        "total": total, "excluidas_sem_casa": fora,
        "itens": [{"nome": k, "n": v, "pct": pct(v, total)}
                  for k, v in c.most_common()],
    }


def _casas(sessoes: list[dict]) -> dict:
    reais = [s["leitura"] for s in sessoes
             if s["leitura"] and s["leitura"].get("casa_eleita_real")]
    c = Counter(l.get("casa_aberta") for l in reais if l.get("casa_aberta"))
    total = sum(c.values())
    empates = sum(1 for l in reais if l.get("empate_tecnico"))
    itens = [{"casa": k, "n": v, "pct": pct(v, total)} for k, v in c.most_common()]
    # se uma casa domina, os pesos precisam de revisao - mas so vale ler o
    # alarme com amostra suficiente
    alarme = bool(itens and total >= MIN_PARA_PORCENTAGEM
                  and itens[0]["n"] * 100 / total > 40)
    return {"total": total, "itens": itens, "empates": empates, "alarme": alarme}


def _horario(sessoes: list[dict]) -> list[dict]:
    """Distribuição e conclusão por modo de horário.

    Atenção ao ler: os três grupos atravessam quantidades diferentes de atrito
    para chegar ao fim, então isto compara caminhos, não tipos de pessoa.
    """
    grupos = defaultdict(lambda: {"n": 0, "leitura": 0, "oferta": 0, "checkout": 0})
    for s in sessoes:
        m = s["modo_hora"]
        if not m:
            continue
        g = grupos[m]
        g["n"] += 1
        if s["leitura"] or 7 in s["telas"]:
            g["leitura"] += 1
        if 10 in s["telas"] or s["oferta"]:
            g["oferta"] += 1
        if s["oferta"]:
            g["checkout"] += 1
    return [{"modo": k, **v,
             "pct_leitura": pct(v["leitura"], v["n"]),
             "pct_oferta": pct(v["oferta"], v["n"]),
             "pct_checkout": pct(v["checkout"], v["n"])}
            for k, v in sorted(grupos.items(), key=lambda x: -x[1]["n"])]


def _geracao(sessoes: list[dict]) -> dict:
    """Saúde do agente.

    Cacheadas ficam FORA das estatísticas de tempo: ms_llm 0 puxaria a mediana
    para baixo e esconderia lentidão real.
    """
    todas = [s["leitura"] for s in sessoes if s["leitura"]]
    novas = [l for l in todas if not l.get("cached")]
    tempos = sorted(l.get("ms_llm") or 0 for l in novas if (l.get("ms_llm") or 0) > 0)
    p95 = tempos[int(len(tempos) * 0.95)] if tempos else 0
    return {
        "total": len(todas),
        "cacheadas": sum(1 for l in todas if l.get("cached")),
        "reserva": sum(1 for l in todas if l.get("validacao") == "reserva"),
        "regeneradas": sum(1 for l in todas if l.get("tentativas", 1) and l.get("validacao") == "regenerado"),
        "mediana_ms": int(statistics.median(tempos)) if tempos else 0,
        "p95_ms": int(p95),
        "amostra_tempo": len(tempos),
        "falhas": sum(1 for s in sessoes if s["falha"]),
        "modelos": _contagem(l.get("modelo") for l in todas if l.get("modelo")),
    }


def _contagem(valores: Iterable) -> list[tuple]:
    return Counter(v for v in valores if v is not None).most_common()
