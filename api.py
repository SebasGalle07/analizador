from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from extraccion_datos import DEFAULT_SYMBOLS, construir_dataset_maestro, guardar_en_csv
from ordenamiento import (
    ALGORITMOS,
    cargar_dataset,
    ejecutar_benchmark,
    obtener_top_n_volumen_y_ordenar,
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DATASET_CANDIDATES = ("dataset_maerstro.csv", "dataset_maestro.csv")

app = FastAPI(
    title="Analisis de Algoritmos API",
    description="API para extraccion, benchmark y visualizacion de datasets financieros.",
    version="2.0.0",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class BuildDatasetRequest(BaseModel):
    simbolos: List[str] = Field(default_factory=lambda: DEFAULT_SYMBOLS.copy())
    years: int = 5
    interval: str = "1d"
    timeout: int = 10
    pausa_segundos: float = 2.0
    guardar_csv: bool = True
    nombre_archivo: str = "dataset_maestro.csv"


class AnalyzeDatasetRequest(BaseModel):
    ruta_archivo: Optional[str] = None
    simbolo: str = "VOO"
    top_n: int = 15
    algoritmos: Optional[List[str]] = None


class SaveDatasetRequest(BaseModel):
    ruta_archivo: str = "dataset_maestro.csv"
    simbolos: List[str] = Field(default_factory=lambda: DEFAULT_SYMBOLS.copy())


def resolve_dataset_path(ruta_archivo: Optional[str] = None) -> Path:
    if ruta_archivo:
        path = Path(ruta_archivo)
        if not path.is_absolute():
            path = BASE_DIR / ruta_archivo
        if path.exists():
            return path

        nombre = Path(ruta_archivo).name
        if nombre in DATASET_CANDIDATES:
            for candidate in DATASET_CANDIDATES:
                candidate_path = BASE_DIR / candidate
                if candidate_path.exists():
                    return candidate_path

        raise HTTPException(
            status_code=404,
            detail=f"No se encontro el archivo: {ruta_archivo}",
        )

    for candidate in DATASET_CANDIDATES:
        candidate_path = BASE_DIR / candidate
        if candidate_path.exists():
            return candidate_path

    raise HTTPException(
        status_code=404,
        detail="No se encontro dataset_maestro.csv ni dataset_maerstro.csv en la carpeta.",
    )


def extract_symbols(dataset):
    if not dataset:
        return []
    return sorted(
        column[:-6]
        for column in dataset[0].keys()
        if column.endswith("_Close")
    )


def build_dataset_overview(dataset, dataset_path: Path, preview_rows=5):
    symbols = extract_symbols(dataset)
    fechas = [row["Fecha"] for row in dataset if row.get("Fecha")]

    return {
        "source_file": dataset_path.name,
        "source_path": str(dataset_path),
        "rows": len(dataset),
        "columns": len(dataset[0].keys()) if dataset else 0,
        "symbols": symbols,
        "symbol_count": len(symbols),
        "date_min": min(fechas) if fechas else None,
        "date_max": max(fechas) if fechas else None,
        "preview": dataset[:preview_rows],
    }


@app.get("/", response_class=FileResponse)
def home():
    return STATIC_DIR / "index.html"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/algorithms")
def list_algorithms():
    return {"algorithms": list(ALGORITMOS.keys())}


@app.get("/dataset/overview")
def dataset_overview(ruta_archivo: Optional[str] = Query(default=None)):
    dataset_path = resolve_dataset_path(ruta_archivo)
    dataset = cargar_dataset(str(dataset_path))
    if not dataset:
        raise HTTPException(status_code=404, detail="No se pudo cargar el dataset.")
    return build_dataset_overview(dataset, dataset_path)


@app.post("/dataset/build")
def build_dataset(payload: BuildDatasetRequest):
    dataset = construir_dataset_maestro(
        simbolos=payload.simbolos,
        years=payload.years,
        interval=payload.interval,
        timeout=payload.timeout,
        pausa_segundos=payload.pausa_segundos,
        guardar_csv=payload.guardar_csv,
        nombre_archivo=payload.nombre_archivo,
    )

    if not dataset:
        raise HTTPException(status_code=502, detail="No se pudo construir el dataset.")

    return {
        "rows": len(dataset),
        "symbols": payload.simbolos,
        "saved_to": payload.nombre_archivo if payload.guardar_csv else None,
        "preview": dataset[:3],
    }


@app.post("/dataset/analyze")
def analyze_dataset(payload: AnalyzeDatasetRequest):
    dataset_path = resolve_dataset_path(payload.ruta_archivo)
    dataset = cargar_dataset(str(dataset_path))
    if not dataset:
        raise HTTPException(status_code=404, detail="No se pudo cargar el dataset.")

    available_symbols = extract_symbols(dataset)
    if payload.simbolo not in available_symbols:
        raise HTTPException(
            status_code=400,
            detail=(
                f"El simbolo {payload.simbolo} no existe en el dataset. "
                f"Disponibles: {', '.join(available_symbols)}"
            ),
        )

    if payload.algoritmos:
        desconocidos = [nombre for nombre in payload.algoritmos if nombre not in ALGORITMOS]
        if desconocidos:
            raise HTTPException(
                status_code=400,
                detail=f"Algoritmos no validos: {', '.join(desconocidos)}",
            )

    benchmark = ejecutar_benchmark(
        dataset,
        simbolo=payload.simbolo,
        algoritmos=payload.algoritmos,
    )
    top_n, tiempo_top_n = obtener_top_n_volumen_y_ordenar(
        dataset,
        simbolo=payload.simbolo,
        limite=payload.top_n,
    )

    return {
        "source_file": dataset_path.name,
        "rows": len(dataset),
        "symbol": payload.simbolo,
        "benchmark": benchmark,
        "top_n_time_ms": round(tiempo_top_n, 4),
        "top_n": top_n,
    }


@app.post("/dataset/rebuild-and-save")
def rebuild_and_save(payload: SaveDatasetRequest):
    dataset = construir_dataset_maestro(
        simbolos=payload.simbolos,
        guardar_csv=False,
    )
    if not dataset:
        raise HTTPException(status_code=502, detail="No se pudo reconstruir el dataset.")

    guardar_en_csv(dataset, nombre_archivo=payload.ruta_archivo)
    return {
        "rows": len(dataset),
        "saved_to": payload.ruta_archivo,
        "symbols": payload.simbolos,
    }
