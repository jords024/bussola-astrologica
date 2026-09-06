"""Vista resumida das casas natais calculadas pelo Kerykeion.

Mantém as cúspides reais e a casa eleita; omite graus, planetas e linhas de
aspectos da roda técnica. Os cálculos usados pelo escritor não são alterados.
"""
from html import escape
from math import cos, sin, radians
from .regencia import CUSPIDE


def desenhar(natal, casa_aberta: int) -> str:
    cusps = [float(getattr(natal, CUSPIDE[n]).abs_pos) for n in range(1, 13)]
    asc = cusps[0]

    def point(degree, radius):
        # O Ascendente fica a esquerda (9h) e as casas correm no ANTI-horario:
        # 1 desce pela esquerda, 4 no fundo, 7 a direita, 10 no topo. Com o sinal
        # invertido a roda saia espelhada, com o Meio do Ceu desenhado embaixo.
        angle = radians(180 + (degree - asc))
        return (200 + radius * cos(angle), 200 - radius * sin(angle))

    def coord(p):
        return f'{p[0]:.3f},{p[1]:.3f}'

    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" role="img">',
             '<title>Casas do mapa de nascimento · vista simplificada</title>',
             '<desc>Cúspides calculadas pelo Kerykeion. A casa destacada é a eleita para esta leitura. Graus e aspectos omitidos nesta vista.</desc>',
             '<circle cx="200" cy="200" r="185" fill="none" stroke="#b99a60" stroke-opacity=".22"/>',
             '<circle cx="200" cy="200" r="151" fill="none" stroke="#b99a60" stroke-opacity=".45"/>']
    for index, start in enumerate(cusps):
        span = (cusps[(index + 1) % 12] - start) % 360
        end = start + span
        selected = index + 1 == casa_aberta
        if selected:
            parts.append(f'<path data-house="{index+1}" d="M {coord(point(start,148))} A 148 148 0 {int(span>180)} 0 {coord(point(end,148))} L {coord(point(end,98))} A 98 98 0 {int(span>180)} 1 {coord(point(start,98))} Z" fill="#dcb66c" fill-opacity=".15"/>')
        a, b = point(start, 98), point(start, 148)
        parts.append(f'<path d="M {coord(a)} L {coord(b)}" stroke="#c5a56c" stroke-opacity=".22" stroke-width=".8"/>')
        x, y = point(start + span / 2, 125)
        color = '#f2d18f' if selected else '#8a8171'
        parts.append(f'<text x="{x:.2f}" y="{y+4:.2f}" text-anchor="middle" fill="{color}" font-family="Arial,sans-serif" font-size="12">{index+1:02}</text>')
    parts.append('<circle cx="200" cy="200" r="97" fill="none" stroke="#b99a60" stroke-opacity=".35"/>')
    for index, glyph in enumerate('♈♉♊♋♌♍♎♏♐♑♒♓'):
        x, y = point(index * 30 + 15, 168)
        parts.append(f'<text x="{x:.2f}" y="{y+6:.2f}" text-anchor="middle" fill="#bfa77d" font-size="19" font-family="Segoe UI Symbol,serif">{glyph}</text>')
    name = escape((natal.name or '').split()[0][:24])
    size = max(16, min(32, 160 / max(len(name), 1) * 1.5))
    parts.extend([
        '<text x="200" y="174" text-anchor="middle" fill="#aa9572" font-size="8" letter-spacing="3" font-family="Arial,sans-serif">SEU MAPA</text>',
        f'<text x="200" y="210" text-anchor="middle" fill="#f3ead9" font-size="{size:.1f}" font-family="Georgia,serif">{name}</text>',
        '<path d="M 181 226 H 219" stroke="#c9a566" stroke-width="1"/>',
        f'<text x="200" y="249" text-anchor="middle" fill="#cbb58e" font-size="10" letter-spacing="2" font-family="Arial,sans-serif">CASA {casa_aberta:02}</text>',
        '</svg>'])
    return ''.join(parts)
