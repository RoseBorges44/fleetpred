from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

app.include_router(veiculos_router)
app.include_router(ocorrencias_router)
app.include_router(manutencoes_router)
app.include_router(relatorios_router)
app.include_router(alertas_router)


@app.on_event("startup")
def startup():
    init_db()
    seed()


@app.get("/")
def root():
    return {
        "app": "FleetPred",
        "versao": "0.1.0",
        "descricao": "Sistema de manutenção preditiva de frota de caminhões",
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}
