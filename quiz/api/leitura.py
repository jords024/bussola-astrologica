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

from servicos import astro, eventos, fatos as mod_fatos, llm, registro, mandala, webhook
from servicos.lentos import eleger_identificacao
from servicos.porta import eleger_porta
from servicos.heuristica import eleger
from servicos.nomes import MES_PT, PLANETA_PT
from servicos.regencia import regente_da_casa
from servicos.veredito import AREA_CASA, CASA_NOME, Veredito, classificar
from servicos.tempo_real import rastreador_presenca, ws_manager

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
    whatsapp: Optional[str] = None
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

    # AS DUAS PARTES DA LEITURA.
    # A Parte 1 nao consulta a area escolhida no quiz - ela fala da vida
    # inteira. A Parte 2 elege a porta pelos rapidos, e NAO e comparada com a
    # escolha dela: e isso que remove a deflacao do veredito antigo.
    ident = eleger_identificacao(mapa.aspectos, mapa.presencas, mapa.perfil)
    porta = eleger_porta(mapa.presencas)

    precisao = {
        "modo_hora": p.nascimento.precisao,
        "casas_confiaveis": mapa.casas_confiaveis,
        "casas_solares": mapa.casas_solares,
        "lua_confiavel": mapa.lua_confiavel,
        "aviso": mapa.aviso,
    }

    quiz = p.quiz.model_dump()
    quiz["primeiro_nome"] = _primeiro_nome(p.nome_completo)
    quiz["quebra_texto"] = QUEBRA_TEXTO.get(p.quiz.quebra, "")

    bloco = mod_fatos.montar(placar, veredito, mapa.presencas, quiz,
                             precisao, agora.date(), ident, porta)
    # A roda destaca a PORTA ABERTA, que e o que a carta aponta agora.
    # Uma roda de casas calculadas com hora presumida sugere precisão inexistente.
    destaque = porta.casa if porta else None
    svg = mandala.desenhar(mapa.natal, destaque) if mapa.casas_confiaveis else ""

    # ident e porta seguem DENTRO do bloco, como valores simples. A tupla fica
    # com sete posicoes, que e como o resto do codigo a desempacota; e
    # chave_cache() serializa `bloco` em JSON, entao dataclass ali dentro
    # quebraria o cache inteiro.
    bloco["porta_casa"] = porta.casa if porta else None
    bloco["porta_planetas"] = list(porta.planetas) if porta else []
    bloco["porta_empate"] = bool(porta.empate) if porta else False
    bloco["identificacao_criterio"] = ident.criterio if ident else 0
    bloco["identificacao_planeta"] = ident.planeta if ident else None
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
    """O selo principal da carta: a PORTA ABERTA.

    Antes vinha da casa eleita pela heuristica. Isso passou a CONTRADIZER a
    propria carta: numa leitura real o selo dizia "Casa 8, recursos
    compartilhados" enquanto o texto apontava a casa 3. O selo tem que ser a
    mesma coisa que a leitura aponta.
    """
    porta = bloco.get("selo_porta")
    if porta:
        return porta
    ident = bloco.get("selo_identificacao")
    return ident or "leitura por signo e aspecto"


def _parte_identificacao(carta: dict, bloco: dict) -> dict:
    """Parte 1 pronta para a tela: o texto do modelo com o selo do codigo."""
    d = carta.get("identificacao") or {}
    return {
        "selo": bloco.get("selo_identificacao") or "",
        "abertura": d.get("abertura") or "",
        "paragrafos": d.get("paragrafos") or [],
    }


def _parte_porta(carta: dict, bloco: dict) -> dict:
    d = carta.get("porta") or {}
    return {
        "selo": bloco.get("selo_porta") or "",
        "abertura": d.get("abertura") or "",
        "paragrafos": d.get("paragrafos") or [],
        "aproveitar": d.get("aproveitar") or [],
        "cuidado": d.get("cuidado"),
    }


def _paragrafos_planos(carta: dict) -> list:
    """As duas partes em lista unica, para quem le a carta como texto corrido.

    Montada por CODIGO. O modelo nao escreve `paragrafos` no esquema novo, e
    tres consumidores dependem dela: o guard do cliente, a mensagem da
    ZapVoice e o painel. Sem isto o deploy derruba os tres de uma vez.
    """
    ident = carta.get("identificacao") or {}
    porta = carta.get("porta") or {}
    fora = []
    if ident.get("abertura"):
        fora.append(ident["abertura"])
    fora += list(ident.get("paragrafos") or [])
    if porta.get("abertura"):
        fora.append(porta["abertura"])
    fora += list(porta.get("paragrafos") or [])
    if porta.get("aproveitar"):
        fora.append(" ".join(porta["aproveitar"]))
    if porta.get("cuidado"):
        fora.append(porta["cuidado"])
    # a reserva ainda entrega `paragrafos` pronto; nesse caso, respeita
    return fora or list(carta.get("paragrafos") or [])


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
            # AS DUAS PARTES, cada uma com o selo gerado por codigo
            "identificacao": _parte_identificacao(carta, bloco),
            "porta": _parte_porta(carta, bloco),
            # `paragrafos` continua existindo e e a CONCATENACAO das duas
            # partes. O cliente trava com "carta incompleta" se esta lista
            # vier vazia, e a mensagem da ZapVoice sai dela.
            "paragrafos": _paragrafos_planos(carta),
            "espera": carta.get("espera"),
            "janela": carta.get("janela") or bloco.get("janela"),
            "assinatura": _assinatura(p, agora.date()),
            "ressalva": _ressalva(precisao),
        },
        "bussola": {
            # a roda aponta a PORTA ABERTA, que e o que a carta indica agora
            "slot": ((bloco["porta_casa"] - 1) % 12)
                    if (casas_ok and bloco.get("porta_casa")) else None,
            "porta_casa": bloco.get("porta_casa"),
            "porta_planetas": bloco.get("porta_planetas") or [],
            "criterio_identificacao": bloco.get("identificacao_criterio"),
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
        # a leitura em duas partes: por qual criterio a Parte 1 entrou, e que
        # porta a Parte 2 abriu. Sem isto o painel continua medindo o cenario
        # antigo, que a carta nao usa mais.
        "criterio_identificacao": bloco.get("identificacao_criterio"),
        "planeta_identificacao": bloco.get("identificacao_planeta"),
        "porta_casa": bloco.get("porta_casa"),
        "porta_empate": bloco.get("porta_empate"),
        "casas_solares": precisao.get("casas_solares", False),
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
        "whatsapp": p.whatsapp,
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

    # Atualiza presença em tempo real e transmite nova leitura via WebSocket
    rastreador_presenca.vincular_leitura(leitura_id, p.cliente_id, p.nome_completo)
    rastreador_presenca.registrar_atividade(
        sid=p.cliente_id,
        tela=7,
        leitura_id=leitura_id,
        nome=p.nome_completo
    )
    ws_manager.broadcast_sync({
        "tipo": "nova_leitura",
        "leitura_id": leitura_id,
        "sid": p.cliente_id,
        "dados": {
            "id": leitura_id,
            "nome_completo": p.nome_completo,
            "whatsapp": p.whatsapp or "—",
            "nascimento": p.nascimento.model_dump(),
            "cidade": p.cidade.model_dump(),
            "quiz": p.quiz.model_dump(),
            "etapa_max": 7,
            "rotulo_etapa": "Tela 7 (Leitura)",
            "checkout": False,
            "veredito": resposta["veredito"],
            "precisao": precisao,
            "tempo_quiz_ms": p.ms_ate_gerar,
            "ao_vivo": True,
        },
        "total_ao_vivo": len(rastreador_presenca.obter_ativos(90.0))
    })

    # Disparo assíncrono do webhook para ZapVoice (nome completo, número e mensagem da leitura)
    if p.whatsapp:
        asyncio.create_task(asyncio.to_thread(
            webhook.disparar_webhook_leitura,
            p.nome_completo,
            p.whatsapp,
            resposta["carta"],
            leitura_id,
            {"casa_aberta": veredito.casa_aberta, "area": p.quiz.area},
        ))

    return resposta


@router.post("/api/contato")
async def contato(c: Contato):
    ok = await asyncio.to_thread(registro.anexar_contato, c.leitura_id, c.whatsapp)
    # so o fato, nunca o numero
    await asyncio.to_thread(_evento, "", "contato_enviado",
                            {"leitura_id": c.leitura_id, "ok": ok})
    if ok and c.whatsapp:
        ws_manager.broadcast_sync({
            "tipo": "contato_atualizado",
            "leitura_id": c.leitura_id,
            "whatsapp": c.whatsapp
        })
        try:
            import json
            arq = registro.DIR_LEITURAS / f"{c.leitura_id}.json"
            if arq.exists():
                d = json.loads(arq.read_text(encoding="utf-8"))
                asyncio.create_task(asyncio.to_thread(
                    webhook.disparar_webhook_leitura,
                    d.get("nome_completo", ""),
                    c.whatsapp,
                    d.get("carta", {}),
                    c.leitura_id,
                ))
        except Exception:
            pass
    return {"ok": ok}
