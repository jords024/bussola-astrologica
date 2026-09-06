# -*- coding: utf-8 -*-
"""Bússola Astrológica — backend do funil.

Serve o próprio HTML, então frontend e API compartilham origem e não há CORS.
O estático é montado em /estatico e não na raiz de propósito: montado na raiz,
o StaticFiles engole as rotas de API dependendo da ordem de registro.
"""
from __future__ import annotations

import logging
import mimetypes

# Este Python no Windows nao conhece .webp e o StaticFiles serviria a foto
# como text/plain, que o navegador recusa a desenhar.
mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("image/svg+xml", ".svg")

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import config
from api.evento import router as router_evento
from api.leitura import router as router_leitura
from api.painel import router as router_painel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("bussola")

app = FastAPI(title="Bússola Astrológica", docs_url="/api/docs")
app.include_router(router_leitura)
app.include_router(router_evento)
app.include_router(router_painel)

if config.DIR_PUBLICO.exists():
    app.mount("/estatico", StaticFiles(directory=str(config.DIR_PUBLICO)), name="estatico")


@app.get("/")
def home():
    index = config.DIR_PUBLICO / "index.html"
    if not index.exists():
        return JSONResponse({"erro": "publico/index.html nao encontrado"}, status_code=404)
    return FileResponse(index, media_type="text/html",
                        headers={"Cache-Control": "no-store"})


@app.get("/api/saude")
def saude():
    componentes = {}

    try:
        from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
        s = AstrologicalSubjectFactory.from_birth_data(
            name="Saude", year=1990, month=1, day=1, hour=12, minute=0,
            lat=-23.55, lng=-46.63, tz_str="America/Sao_Paulo",
            city="Sao Paulo", nation="BR", online=False,
            active_points=["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"])
        ChartDataFactory.create_natal_chart_data(s)
        componentes["kerykeion"] = "ok"
    except Exception as e:
        componentes["kerykeion"] = f"falha: {str(e)[:120]}"

    componentes["openai_key"] = "presente" if config.tem_chave() else "AUSENTE"
    componentes["painel_senha"] = "presente" if config.PAINEL_SENHA else "AUSENTE"
    componentes["eventos"] = "ok" if config.DIR_EVENTOS.exists() else "falha: sem diretorio"
    if config.dentro_do_onedrive():
        componentes["onedrive"] = ("falha: DIR_DADOS esta dentro do OneDrive. A sincronizacao "
                                   "trava arquivo e pode descartar leads. Aponte DIR_DADOS "
                                   "no .env para fora do OneDrive.")
    componentes["modelos"] = config.MODELOS
    componentes["publico"] = "ok" if (config.DIR_PUBLICO / "index.html").exists() else "sem index.html"

    try:
        (config.DIR_LEITURAS / ".probe").write_text("ok", encoding="utf-8")
        (config.DIR_LEITURAS / ".probe").unlink()
        componentes["disco"] = "ok"
    except Exception as e:
        componentes["disco"] = f"falha: {str(e)[:120]}"

    degradado = any(
        isinstance(v, str) and (v.startswith("falha") or v in ("AUSENTE", "sem index.html"))
        for v in componentes.values()
    )
    return {"status": "degradado" if degradado else "operacional",
            "componentes": componentes}


@app.on_event("startup")
def retencao():
    from servicos import eventos
    try:
        eventos.limpar_antigos()
    except Exception as e:
        logger.warning("retencao de eventos falhou: %s", e)


@app.on_event("startup")
def aviso_chave():
    if not config.tem_chave():
        logger.warning(
            "OPENAI_API_KEY ausente. O funil roda, mas toda leitura vai sair com a "
            "carta de reserva. Copie .env.example para .env e ponha uma chave nova."
        )
