# -*- coding: utf-8 -*-
"""POST /api/leitura — o endpoint que gera a carta."""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import date, datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator
import pytz

from servicos import astro, eventos, fatos as mod_fatos, llm, registro, mandala
from servicos.heuristica import eleger
from servicos.nomes import MES_PT, PLANETA_PT
from servicos.regencia import regente_da_casa
from servicos.veredito import AREA_CASA, CASA_NOME, Veredito, classificar

router = APIRouter()
logger = logging.getLogger(__name__)

AREAS = ("dinheiro", "amor", "carreira", "casa", "corpo", "caminhos")

QUEBRA_TEXTO = {
    "sim": "Sim, mais de uma vez",
    "muitas": "Muitas vezes. É quase um padrão",
    "nao": "Não sei dizer",
}


class Quiz(BaseModel):
    area: Literal["dinheiro", "amor", "carreira", "casa", "corpo", "caminhos"]
    espelho: str = ""
    espelho_idx: int = 0
    quebra: Literal["sim", "muitas", "nao"] = "nao"


class Nascimento(BaseModel):
    ano: int = Field(ge=1900, le=2030)
    mes: int = Field(ge=1, le=12)
    dia: int = Field(ge=1, le=31)
    hora: Optional[int] = Field(default=None, ge=0, le=23)
    minuto: Optional[int] = Field(default=0, ge=0, le=59)
    precisao: Literal["exata", "periodo", "desconhecida"] = "exata"
    periodo: Optional[str] = None
    is_dst: Optional[bool] = None

    @model_validator(mode="after")
    def validar(self):
        if date(self.ano, self.mes, self.dia) > date.today():
            raise ValueError("Data de nascimento futura")
        if self.precisao == "exata" and self.hora is None:
            raise ValueError("Informe a hora ou escolha horário desconhecido")
        if self.precisao == "periodo" and self.periodo not in astro.PERIODO_HORA:
            raise ValueError("Escolha um período válido")
        return self


class Cidade(BaseModel):
    nome: str
    uf: str = ""
    pais: str = ""
    cc: str = "BR"
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    tz: str = "America/Sao_Paulo"

    @field_validator("tz")
    @classmethod
    def validar_fuso(cls, value):
        if value not in pytz.all_timezones_set:
            raise ValueError("Fuso horário desconhecido")
        return value


class Pedido(BaseModel):
    cliente_id: str = ""
    nome_completo: str = Field(min_length=1, max_length=120)
    quiz: Quiz
    nascimento: Nascimento
    cidade: Cidade
    ms_ate_gerar: Optional[int] = None


class Contato(BaseModel):
    leitura_id: str
    whatsapp: str


def _pipeline(p: Pedido, agora: datetime):
    """Tudo que é síncrono e pesado, para rodar em to_thread."""
    mapa = astro.calcular(
        p.nascimento.model_dump(), p.cidade.model_dump(), p.nome_completo, agora)

    placar = eleger(mapa.aspectos, mapa.presencas, mapa.casas_confiaveis)
    alvo = AREA_CASA[p.quiz.area]
    casa_demanda = alvo["principal"]

    # Casa sem trânsito nenhum não é casa vazia: quem responde é o regente dela.
    via_regente, regente = False, None
    if mapa.casas_confiaveis:
        tem_transito = any(x.casa == casa_demanda for x in mapa.presencas) or any(
            casa_demanda in (a.casa_transito, a.casa_natal) for a in mapa.aspectos)
        if not tem_transito:
            regente = regente_da_casa(mapa.natal, casa_demanda)
            via_regente = bool(regente)

    # SEM "or casa_demanda". Quando nao ha placar de casas, casa_aberta fica None
    # e o cenario vira SEM_CASAS. O "or" antigo herdava a casa da resposta do
    # quiz e classificar() a comparava com ela mesma, marcando CONFIRMACAO em
    # toda leitura sem hora confiavel: a carta afirmava uma coincidencia que o
    # calculo nunca constatou.
    casa_aberta = placar.casa_aberta
    veredito = Veredito(
        cenario=classificar(p.quiz.area, casa_aberta),
        casa_demanda=casa_demanda,
        casa_aberta=casa_aberta,
        casa_fechada=placar.casa_fechada,
        via_regente=via_regente,
        regente=regente,
        empate_tecnico=placar.empate_tecnico,
    )

    precisao = {
        "modo_hora": p.nascimento.precisao,
        "casas_confiaveis": mapa.casas_confiaveis,
        "lua_confiavel": mapa.lua_confiavel,
        "aviso": mapa.aviso,
    }

    quiz = p.quiz.model_dump()
    quiz["primeiro_nome"] = _primeiro_nome(p.nome_completo)
    quiz["quebra_texto"] = QUEBRA_TEXTO.get(p.quiz.quebra, "")

    bloco = mod_fatos.montar(placar, veredito, mapa.presencas, quiz,
                             precisao, agora.date())
    # Uma roda de casas calculadas com hora presumida sugere precisão inexistente.
    svg = mandala.desenhar(mapa.natal, veredito.casa_aberta) if mapa.casas_confiaveis else ""
    return mapa, placar, veredito, precisao, quiz, bloco, svg


def _primeiro_nome(completo: str) -> str:
    partes = (completo or "").strip().split()
    return partes[0] if partes else ""


def _assinatura(p: Pedido, hoje: date) -> str:
    """A carta que estava na garrafa.

    O céu do dia em que ela nasceu foi a garrafa jogada ao mar. Chega hoje.
    Literalmente verdadeiro: o mapa natal é o céu do nascimento e os trânsitos
    são o céu de hoje encostando naquele.
    """
    n = p.nascimento
    quando = f"{n.dia} de {MES_PT[n.mes - 1]} de {n.ano}"
    if n.precisao == "exata" and n.hora is not None:
        quando += f", às {n.hora:02d}h{(n.minuto or 0):02d}"
    return (f"Escrita no céu de {p.cidade.nome}, {quando}.\n"
            f"Chegou em {hoje.day} de {MES_PT[hoje.month - 1]} de {hoje.year}.")


def _selo(bloco: dict, veredito: Veredito, casas_ok: bool) -> str:
    ap = bloco.get("aspecto_principal") or {}
    planeta = ap.get("transito_pt") or ""
    if casas_ok and veredito.casa_aberta:
        base = f"Casa {veredito.casa_aberta} · {CASA_NOME.get(veredito.casa_aberta, '')}"
    else:
        base = "leitura por signo e aspecto"
    return f"{base} · {planeta} em trânsito" if planeta else base


def _ressalva(precisao: dict) -> Optional[str]:
    if precisao["modo_hora"] == "desconhecida":
        return ("Sem a hora exata eu leio os trânsitos, mas não monto as suas doze "
                "casas com precisão. Esta carta sai pelo planeta, pelo signo e pelo "
                "aspecto. Com o horário da certidão, ela fica bem mais fechada.")
    if precisao["modo_hora"] == "periodo" and not precisao["casas_confiaveis"]:
        return ("O período que você indicou ainda deixa as casas em aberto, então "
                "esta carta segue pelo planeta e pelo aspecto. Com o horário exato, "
                "ela fecha mais.")
    if precisao.get("aviso"):
        return f"Uma observação sobre o horário: {precisao['aviso']}."
    return None


def _evento(sid: str, evt: str, props: dict) -> None:
    """Emissao best-effort: uma falha aqui nunca pode derrubar a leitura."""
    try:
        eventos.registrar_servidor(sid, evt, props)
    except Exception as e:
        logger.warning("evento %s nao gravado: %s", evt, str(e)[:120])


@router.post("/api/leitura")
async def gerar(p: Pedido):
    t0 = time.time()
    agora = datetime.now(timezone.utc).astimezone(pytz.timezone(p.cidade.tz))

    try:
        mapa, placar, veredito, precisao, quiz, bloco, svg = await asyncio.to_thread(
            _pipeline, p, agora)
    except Exception as exc:
        # NAO acrescentar p.model_dump() aqui: jogaria nome e nascimento no log
        logger.exception("Falha ao calcular leitura")
        _evento(p.cliente_id, "leitura_falha",
                {"onde": "servidor", "motivo": type(exc).__name__,
                 "ms": int((time.time() - t0) * 1000)})
        raise HTTPException(503, "Não consegui calcular sua leitura. Confira os dados e tente novamente.")
    t_astro = int((time.time() - t0) * 1000)

    chave = registro.chave_cache(veredito, bloco, quiz, agora.date())
    cacheado = registro.ler_cache(chave)
    if cacheado:
        carta, meta = cacheado, {"modelo": "cache", "tentativas": 0,
                                 "validacao": "cache", "ms_llm": 0}
    else:
        r = await llm.escrever(bloco, veredito, quiz, precisao)
        carta, meta = r["carta"], r["meta"]
        if meta["validacao"] in ("ok", "regenerado"):
            registro.gravar_cache(chave, carta)

    primeiro = quiz["primeiro_nome"]
    leitura_id = registro.novo_id()
    casas_ok = precisao["casas_confiaveis"]

    resposta = {
        "ok": True,
        "leitura_id": leitura_id,
        "cached": bool(cacheado),
        "svg": svg,
        "carta": {
            "titulo": carta.get("titulo") or "",
            "direcao": carta.get("titulo") or "",
            "destaque": carta.get("destaque") or "",
            # a prova ao pe da carta: montada por codigo, nunca pelo modelo
            "notas": bloco.get("notas") or [],
            "selo": _selo(bloco, veredito, casas_ok),
            "saudacao": f"{primeiro}," if primeiro else "",
            "paragrafos": carta.get("paragrafos") or [],
            "espera": carta.get("espera"),
            "janela": carta.get("janela") or bloco.get("janela"),
            "assinatura": _assinatura(p, agora.date()),
            "ressalva": _ressalva(precisao),
        },
        "bussola": {
            "slot": ((veredito.casa_aberta - 1) % 12)
                    if (casas_ok and veredito.casa_aberta) else None,
            "casa_aberta": veredito.casa_aberta if casas_ok else None,
            "casa_fechada": veredito.casa_fechada if casas_ok else None,
        },
        "veredito": {
            "tipo": veredito.cenario,
            # distingue casa que saiu do calculo de casa que nao existe
            "casa_eleita_real": bool(veredito.casa_aberta),
            "casa_demanda": veredito.casa_demanda,
            "casa_aberta": veredito.casa_aberta,
            "casa_fechada": veredito.casa_fechada,
            "via_regente": veredito.via_regente,
            "regente": veredito.regente,
            "empate_tecnico": veredito.empate_tecnico,
        },
        "precisao": precisao,
        "meta": {**meta, "ms": {"astro": t_astro,
                                "total": int((time.time() - t0) * 1000)}},
    }

    # Sem nenhum dado pessoal: o evento liga a pessoa so por leitura_id.
    await asyncio.to_thread(_evento, p.cliente_id, "leitura_entregue", {
        "leitura_id": leitura_id,
        "area": p.quiz.area,
        "modo_hora": precisao["modo_hora"],
        "cenario": veredito.cenario,
        "casa_demanda": veredito.casa_demanda,
        "casa_aberta": veredito.casa_aberta,
        "casa_fechada": veredito.casa_fechada,
        "casas_confiaveis": casas_ok,
        "casa_eleita_real": bool(veredito.casa_aberta),
        "via_regente": veredito.via_regente,
        "empate_tecnico": veredito.empate_tecnico,
        "cached": bool(cacheado),
        "validacao": meta.get("validacao"),
        "tentativas": meta.get("tentativas"),
        "modelo": meta.get("modelo"),
        "ms_llm": meta.get("ms_llm", 0),
        "ms_astro": t_astro,
        "ms_total": resposta["meta"]["ms"]["total"],
    })

    # o lead é gravado agora, antes de qualquer tela de oferta
    await asyncio.to_thread(registro.gravar_lead, leitura_id, {
        "cliente_id": p.cliente_id,
        "nome_completo": p.nome_completo,
        "nascimento": p.nascimento.model_dump(),
        "cidade": p.cidade.model_dump(),
        "quiz": p.quiz.model_dump(),
        "tempo_quiz_ms": p.ms_ate_gerar,
        "veredito": resposta["veredito"],
        "precisao": precisao,
        "placar": {str(k): round(v, 1) for k, v in placar.casas.items()},
        "carta": resposta["carta"],
        "meta": resposta["meta"],
    })

    return resposta


@router.post("/api/contato")
async def contato(c: Contato):
    ok = await asyncio.to_thread(registro.anexar_contato, c.leitura_id, c.whatsapp)
    # so o fato, nunca o numero
    await asyncio.to_thread(_evento, "", "contato_enviado",
                            {"leitura_id": c.leitura_id, "ok": ok})
    return {"ok": ok}
