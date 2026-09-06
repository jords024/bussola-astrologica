# -*- coding: utf-8 -*-
"""Sonda: confere a API real da Kerykeion instalada, antes de construir em cima.

O fonte já respondeu quase tudo, mas validar contra a instalação do venv pega
divergência de wheel e de versão. O ponto que mais importa aqui é a orientação
p1/p2: se estiver invertida, todo veredito sai errado e continua parecendo
plausível.
"""
import inspect
from datetime import datetime

from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer

PONTOS = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
          "Uranus", "Neptune", "Pluto", "Ascendant", "Medium_Coeli"]

NOME_NATAL = "Sonda"
NOME_TRANSITO = "Transito_2026-09-05"

natal = AstrologicalSubjectFactory.from_birth_data(
    name=NOME_NATAL, year=1991, month=3, day=14, hour=4, minute=20,
    lat=-28.2628, lng=-52.4067, tz_str="America/Sao_Paulo",
    city="Passo Fundo", nation="BR", online=False,
    zodiac_type="Tropical", houses_system_identifier="P",
)

agora = datetime(2026, 9, 5, 15, 0)
transito = AstrologicalSubjectFactory.from_birth_data(
    name=NOME_TRANSITO, year=agora.year, month=agora.month, day=agora.day,
    hour=agora.hour, minute=agora.minute,
    lat=-28.2628, lng=-52.4067, tz_str="America/Sao_Paulo",
    city="Passo Fundo", nation="BR", online=False,
    zodiac_type="Tropical", houses_system_identifier="P",
)

chart = ChartDataFactory.create_transit_chart_data(
    natal, transito, active_points=PONTOS, include_house_comparison=True,
)

print("tipo:", type(chart).__name__)
print("active_points:", chart.active_points)
print("active_aspects:", chart.active_aspects)
print("n aspectos:", len(chart.aspects))

a = chart.aspects[0]
print("\nprimeiro aspecto:")
for k, v in a.model_dump().items():
    print(f"   {k} = {v!r}")

movimentos = {x.aspect_movement for x in chart.aspects}
print("\nmovimentos vistos:", movimentos)

hc = chart.house_comparison
print("\nhouse_comparison campos:", list(hc.model_dump().keys()))
p = hc.second_points_in_first_houses[0]
print("primeiro ponto em casa:")
for k, v in p.model_dump().items():
    print(f"   {k} = {v!r}")

# ---- as asserções que importam ----
donos_p1 = {x.p1_owner for x in chart.aspects}
donos_p2 = {x.p2_owner for x in chart.aspects}
assert donos_p1 == {NOME_NATAL}, f"p1_owner inesperado: {donos_p1}"
assert donos_p2 == {NOME_TRANSITO}, f"p2_owner inesperado: {donos_p2}"
print("\nOK  p1 = natal, p2 = transito  (confirmado na instalacao real)")

assert movimentos <= {"Applying", "Separating", "Static"}, movimentos
print("OK  aspect_movement com os tres valores esperados")

assert all(1 <= x.projected_house_number <= 12 for x in hc.second_points_in_first_houses)
print("OK  projected_house_number dentro de 1..12")

velocidades_natal = {x.p1_speed for x in chart.aspects}
print("OK  p1_speed (lado natal, deve ser 0):", velocidades_natal)

# ---- o desenho ----
metodos = [m for m in dir(ChartDrawer) if "svg" in m.lower()]
print("\nmetodos de SVG:", metodos)
drawer = ChartDrawer(chart_data=chart, theme="dark", chart_language="PT")
print("assinatura wheel-only:",
      inspect.signature(drawer.generate_wheel_only_svg_string))

svg = drawer.generate_wheel_only_svg_string(remove_css_variables=True)
print("svg len:", len(svg))
print("tem var(--):", "var(--" in svg)
print("usa aspas simples:", svg.count("'") > svg.count('"'))
print("inicio:", svg[:120].replace("\n", " "))
