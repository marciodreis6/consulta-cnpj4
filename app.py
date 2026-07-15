from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

from consulta_sintegra import ConsultaSintegraBA, limpar_cnpj


app = FastAPI(
    title="API CNPJ BA - Versao 4",
    description="Consulta situacao cadastral de CNPJs no portal publico da Sefaz-BA.",
    version="4.0.0",
)


class ConsultaRequest(BaseModel):
    cnpj: str = Field(..., examples=["12345678000100"])
    tentativas: int = Field(2, ge=1, le=5)
    delay_min: float = Field(1.5, ge=0.5, le=10)
    delay_max: float = Field(3.0, ge=0.5, le=15)


class LoteRequest(BaseModel):
    cnpjs: list[str] = Field(..., min_length=1, max_length=500)
    tentativas: int = Field(2, ge=1, le=5)
    delay_min: float = Field(1.5, ge=0.5, le=10)
    delay_max: float = Field(3.0, ge=0.5, le=15)
    modo: Literal["seguro", "rapido"] = "seguro"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/consultar")
def consultar_cnpj(payload: ConsultaRequest):
    delay_min, delay_max = _normalizar_delays(payload.delay_min, payload.delay_max)
    with ConsultaSintegraBA(delay_min=delay_min, delay_max=delay_max) as consulta:
        return consulta.consultar(payload.cnpj, tentativas=payload.tentativas)


@app.post("/consultar-lote")
def consultar_lote(payload: LoteRequest):
    delay_min, delay_max = _normalizar_delays(payload.delay_min, payload.delay_max)

    if payload.modo == "rapido":
        delay_min = max(0.8, min(delay_min, 1.2))
        delay_max = max(1.2, min(delay_max, 2.0))

    cnpjs_limpos = [limpar_cnpj(cnpj) for cnpj in payload.cnpjs]
    with ConsultaSintegraBA(delay_min=delay_min, delay_max=delay_max) as consulta:
        resultados = consulta.consultar_lote(cnpjs_limpos, tentativas=payload.tentativas)

    return {
        "total_recebido": len(payload.cnpjs),
        "total_unico": len(set(cnpjs_limpos)),
        "delay_min": delay_min,
        "delay_max": delay_max,
        "resultados": resultados,
    }


def _normalizar_delays(delay_min: float, delay_max: float) -> tuple[float, float]:
    if delay_max < delay_min:
        return delay_max, delay_min
    return delay_min, delay_max
