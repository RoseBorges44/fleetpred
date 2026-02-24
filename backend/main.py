import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import init_db
from seed_data import seed
from routes.veiculos import router as veiculos_router
from routes.ocorrencias import router as ocorrencias_router
from routes.manutencoes import router as manutencoes_router
from routes.relatorios import router as relatorios_router
from routes.alertas import router as alertas_router

app = FastAPI(
    title="FleetPred",
    description="Sistema de manutenção preditiva de frota de caminhões",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routes (registrar ANTES dos arquivos estáticos) ──────────────────

app.include_router(veiculos_router)
app.include_router(ocorrencias_router)
app.include_router(manutencoes_router)
app.include_router(relatorios_router)
app.include_router(alertas_router)


@app.on_event("startup")
def startup():
    init_db()
    seed()


@app.get("/api/health")
def health():
    return {"status": "ok"}


# ── Frontend estático (SPA) ─────────────────────────────────────────────

_dist_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
_assets_dir = os.path.join(_dist_dir, "assets")

if os.path.isdir(_assets_dir):
    app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    index = os.path.join(_dist_dir, "index.html")
    if os.path.isfile(index):
        return FileResponse(index)
    return {"app": "FleetPred", "versao": "0.1.0", "nota": "frontend não buildado — rode npm run build"}
