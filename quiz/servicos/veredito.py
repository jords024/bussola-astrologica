"""Onde a escolha dela entra.

Numa consulta de verdade o astrologo faz tres movimentos: acolhe a demanda,
olha o mapa para aquela area, e percebe se o que grita mais alto esta em outro
lugar. Quando esta, ele conecta as duas coisas.

Por isso o calculo produz dois vereditos, nao um: a casa da demanda (que ela
escolheu) e a casa mais forte (que saiu da pontuacao, sem saber a escolha dela).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# cada area do quiz aponta para uma casa principal e uma vizinha
AREA_CASA = {
    "dinheiro": {"principal": 2,  "vizinha": 8},
    "amor":     {"principal": 7,  "vizinha": 5},
    "carreira": {"principal": 10, "vizinha": 6},
    "casa":     {"principal": 4,  "vizinha": 3},
    "corpo":    {"principal": 6,  "vizinha": 1},
    "caminhos": {"principal": 9,  "vizinha": 12},
}

# Aparecem no selo da carta e no bloco de fatos. Vao para a tela em portugues,
# entao sao acentuados.
CASA_NOME = {
    1: "corpo e presença", 2: "valores e recursos", 3: "comunicação e trocas curtas",
    4: "raízes e família", 5: "criação e prazer", 6: "rotina e saúde",
    7: "vínculos e parcerias", 8: "recursos compartilhados", 9: "direção e sentido",
    10: "vocação e reconhecimento", 11: "grupos e futuro", 12: "silêncio e bastidor",
}

CONFIRMACAO = "CONFIRMACAO"
DESLOCAMENTO = "DESLOCAMENTO"
CAUSA_OCULTA = "CAUSA_OCULTA"
# Sem hora confiavel nao ha placar de casas, entao NAO EXISTE veredito de casa.
# Sem este quarto estado, casa_aberta cairia na casa que veio da resposta do quiz
# e classificar() a compararia com ela mesma, devolvendo CONFIRMACAO sempre - ou
# seja, a carta afirmaria que o ceu confirmou a escolha dela sem nenhum calculo
# por tras.
SEM_CASAS = "SEM_CASAS"


@dataclass
class Veredito:
    cenario: str
    casa_demanda: int
    casa_aberta: Optional[int]
    casa_fechada: Optional[int]
    via_regente: bool
    regente: Optional[dict]
    empate_tecnico: bool


def classificar(area: str, casa_forte: Optional[int]) -> str:
    if not casa_forte:
        return SEM_CASAS
    alvo = AREA_CASA.get(area) or AREA_CASA["caminhos"]
    if casa_forte == alvo["principal"]:
        return CONFIRMACAO   # ela olhou onde o ceu esta mexendo
    if casa_forte == alvo["vizinha"]:
        return DESLOCAMENTO  # a resposta esta na sala ao lado
    return CAUSA_OCULTA      # o barulho vem de outro comodo


def casa_label(n: Optional[int]) -> Optional[str]:
    if not n:
        return None
    return f"Casa {n} - {CASA_NOME.get(n, '')}".strip(" -")
