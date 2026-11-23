"""API web de Phelisstie AI (FastAPI).

Arranque:  uvicorn api:app --reload --port 8000
Docs interactivas: http://127.0.0.1:8000/docs
"""
from __future__ import annotations

import json
import os
import socket
import threading
import uuid
from typing import Any, Literal, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import neuro

MODEL_PATH = os.getenv("PHELISSTIE_MODEL_PATH", "phelisstie_model.pt")
ORIGINS = os.getenv("PHELISSTIE_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(",")
OLLAMA_URL = os.getenv("PHELISSTIE_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("PHELISSTIE_LLM_MODEL", "qwen2.5:3b")

app = FastAPI(title="Phelisstie AI", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estado en memoria (suficiente para desarrollo local; en producción usa Redis/DB).
_lock = threading.Lock()
_model: Optional[neuro.Trained] = None
_jobs: dict[str, dict[str, Any]] = {}

if os.path.exists(MODEL_PATH):
    try:
        _model = neuro.load_model(MODEL_PATH)
    except Exception:  # modelo corrupto o de otra versión: se ignora
        _model = None


class Dataset(BaseModel):
    X: list[list[float]] = Field(..., description="Filas x características")
    y: list[float | int | str] = Field(..., description="Objetivo por fila")
    task: Literal["regression", "classification"] = "regression"


class TrainRequest(Dataset):
    hidden_layers: list[int] = [64, 32]
    dropout: float = 0.1
    activation: Literal["relu", "gelu", "silu", "tanh"] = "relu"
    lr: float = 1e-3
    epochs: int = Field(200, ge=1, le=2000)


class AutoMLRequest(Dataset):
    n_trials: int = Field(20, ge=1, le=200)
    max_epochs: int = Field(150, ge=5, le=1000)


class PredictRequest(BaseModel):
    X: list[list[float]]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1, max_length=20)


def _summary(t: neuro.Trained) -> dict:
    return {
        "task": t.task,
        "metrics": t.metrics,
        "config": {k: v for k, v in neuro.asdict(t.cfg).items()},
        "history": t.history,
        "n_features": t.model.net[0].in_features,
    }


def _set_model(t: neuro.Trained) -> None:
    global _model
    with _lock:
        _model = t
        neuro.save_model(t, MODEL_PATH)


def _run_job(job_id: str, fn) -> None:
    job = _jobs[job_id]
    try:
        job["result"] = fn(job)
        job["status"] = "stopped" if job.get("stop") else "done"
    except Exception as e:  # el error llega al front por /jobs/{id}
        job["status"], job["error"] = "error", str(e)


def _start(fn) -> str:
    job_id = uuid.uuid4().hex[:12]
    _jobs[job_id] = {"status": "running", "progress": [], "result": None, "error": None, "stop": False}
    threading.Thread(target=_run_job, args=(job_id, fn), daemon=True).start()
    return job_id


@app.get("/health")
def health():
    return {"status": "ok", "device": str(neuro.DEVICE), "model_loaded": _model is not None}


@app.post("/chat")
def chat(req: ChatRequest):
    """Genera una respuesta conversacional mediante el modelo local de Ollama."""
    if req.messages[-1].role != "user":
        raise HTTPException(422, "El último mensaje debe ser del usuario")
    if any(not message.content.strip() for message in req.messages):
        raise HTTPException(422, "Los mensajes no pueden estar vacíos")

    messages = [
        {
            "role": "system",
            "content": "Eres Phellisstie, un asistente útil. Responde en el idioma del usuario con claridad y honestidad. Solo puedes usar la conversación actual: no tienes acceso a internet, archivos, herramientas externas ni memoria fuera de estos mensajes. No afirmes que puedes hacer búsquedas, recordar citas o realizar acciones externas.",
        },
        *[message.model_dump() for message in req.messages],
    ]
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {"num_predict": 512},
    }).encode("utf-8")
    upstream = Request(
        f"{OLLAMA_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(upstream, timeout=180) as response:
            result = json.loads(response.read())
    except HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise HTTPException(502, f"Error de Ollama ({e.code}): {detail}") from e
    except (URLError, ConnectionError) as e:
        raise HTTPException(
            503,
            "Ollama no está disponible. Inícialo y descarga el modelo "
            f"{OLLAMA_MODEL}.",
        ) from e
    except (TimeoutError, socket.timeout) as e:
        raise HTTPException(504, "Ollama tardó demasiado en generar la respuesta.") from e
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise HTTPException(502, "Ollama devolvió una respuesta no válida.") from e

    try:
        content = result["message"]["content"].strip()
    except (KeyError, TypeError, AttributeError) as e:
        raise HTTPException(502, "Ollama devolvió una respuesta sin texto.") from e
    if not content:
        raise HTTPException(502, "Ollama devolvió una respuesta vacía.")
    return {"response": content, "model": OLLAMA_MODEL}


@app.post("/train")
def train(req: TrainRequest):
    """Entrenamiento de Deep Learning con la arquitectura indicada."""
    cfg = neuro.Config(hidden_layers=req.hidden_layers, dropout=req.dropout,
                       activation=req.activation, lr=req.lr, epochs=req.epochs)

    def work(job):
        def on_epoch(ep, tr, va):
            job["progress"].append({"epoch": ep, "train_loss": tr, "val_loss": va})
            return job["stop"]

        t = neuro.train_model(req.X, req.y, req.task, cfg, on_epoch=on_epoch)
        _set_model(t)
        return _summary(t)

    try:
        return {"job_id": _start(work)}
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.post("/automl")
def automl(req: AutoMLRequest):
    """AutoML: Optuna busca la mejor arquitectura e hiperparámetros."""

    def work(job):
        def on_trial(n, val, params):
            job["progress"].append({"trial": n, "val_loss": val, "params": params})

        t, log = neuro.run_automl(req.X, req.y, req.task, req.n_trials, req.max_epochs,
                                  on_trial=on_trial, should_stop=lambda: job["stop"])
        _set_model(t)
        return {**_summary(t), "top_trials": log[:5]}

    return {"job_id": _start(work)}


@app.get("/jobs/{job_id}")
def job_status(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Trabajo no encontrado")
    return {"status": job["status"], "progress": job["progress"][-200:],
            "result": job["result"], "error": job["error"]}


@app.post("/jobs/{job_id}/stop")
def job_stop(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Trabajo no encontrado")
    job["stop"] = True
    return {"status": "stopping"}


@app.get("/model")
def model_info():
    if _model is None:
        raise HTTPException(404, "Aún no hay un modelo entrenado")
    return _summary(_model)


@app.post("/predict")
def predict(req: PredictRequest):
    if _model is None:
        raise HTTPException(409, "Entrena un modelo primero (/train o /automl)")
    n = _model.model.net[0].in_features
    if any(len(r) != n for r in req.X):
        raise HTTPException(422, f"Cada fila debe tener {n} características")
    return neuro.predict(_model, req.X)
