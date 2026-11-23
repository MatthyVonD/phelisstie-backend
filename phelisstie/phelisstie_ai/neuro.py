"""Phelisstie Neural Network: Deep Learning + AutoML.

- PhelisstieNet: red densa (MLP) configurable (capas, neuronas, dropout, BatchNorm).
- train_model: entrenamiento con AdamW, early stopping y scheduler.
- run_automl: búsqueda automática de hiperparámetros con Optuna (TPE + pruning).
- save_model / load_model: persistencia en disco.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, asdict, field
from typing import Callable, Optional

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

ACTIVATIONS = {
    "relu": nn.ReLU,
    "gelu": nn.GELU,
    "silu": nn.SiLU,
    "tanh": nn.Tanh,
}


@dataclass
class Config:
    """Hiperparámetros de la red (esto es lo que AutoML optimiza)."""
    hidden_layers: list[int] = field(default_factory=lambda: [64, 32])
    dropout: float = 0.1
    activation: str = "relu"
    batch_norm: bool = True
    lr: float = 1e-3
    weight_decay: float = 1e-4
    batch_size: int = 32
    epochs: int = 200
    patience: int = 20
    val_split: float = 0.2
    seed: int = 42


class PhelisstieNet(nn.Module):
    """MLP profunda. Con hidden_layers=[] equivale a tu red original (1 capa lineal)."""

    def __init__(self, in_dim: int, out_dim: int = 1, cfg: Optional[Config] = None):
        super().__init__()
        cfg = cfg or Config()
        layers: list[nn.Module] = []
        prev = in_dim
        for units in cfg.hidden_layers:
            layers.append(nn.Linear(prev, units))
            if cfg.batch_norm:
                layers.append(nn.BatchNorm1d(units))
            layers.append(ACTIVATIONS[cfg.activation]())
            if cfg.dropout > 0:
                layers.append(nn.Dropout(cfg.dropout))
            prev = units
        layers.append(nn.Linear(prev, out_dim))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class Scaler:
    """Estandarización (media 0, desviación 1). Se guarda junto al modelo."""

    def __init__(self, mean=None, std=None):
        self.mean, self.std = mean, std

    def fit(self, a: np.ndarray) -> "Scaler":
        self.mean = a.mean(axis=0)
        self.std = a.std(axis=0)
        self.std[self.std < 1e-8] = 1.0
        return self

    def transform(self, a: np.ndarray) -> np.ndarray:
        return (a - self.mean) / self.std

    def inverse(self, a: np.ndarray) -> np.ndarray:
        return a * self.std + self.mean


@dataclass
class Trained:
    """Modelo entrenado + todo lo necesario para predecir."""
    model: PhelisstieNet
    cfg: Config
    task: str
    x_scaler: Scaler
    y_scaler: Optional[Scaler]
    classes: Optional[list]
    history: dict
    metrics: dict


def _prepare(X, y, task: str, cfg: Config):
    X = np.asarray(X, dtype=np.float32)
    y = np.asarray(y)
    if X.ndim != 2:
        raise ValueError("X debe ser una matriz 2D: filas x características.")
    if len(X) != len(y):
        raise ValueError("X e y deben tener el mismo número de filas.")
    if len(X) < 10:
        raise ValueError("Se necesitan al menos 10 filas para entrenar.")

    rng = np.random.default_rng(cfg.seed)
    idx = rng.permutation(len(X))
    n_val = max(2, int(len(X) * cfg.val_split))
    val_i, tr_i = idx[:n_val], idx[n_val:]

    x_scaler = Scaler().fit(X[tr_i])
    Xs = x_scaler.transform(X).astype(np.float32)

    y_scaler, classes = None, None
    if task == "regression":
        yf = y.astype(np.float32).reshape(-1, 1)
        y_scaler = Scaler().fit(yf[tr_i])
        ys = y_scaler.transform(yf).astype(np.float32)
        out_dim = 1
    elif task == "classification":
        classes = sorted(set(y.tolist()))
        lookup = {c: i for i, c in enumerate(classes)}
        ys = np.array([lookup[v] for v in y.tolist()], dtype=np.int64)
        out_dim = len(classes)
    else:
        raise ValueError("task debe ser 'regression' o 'classification'.")
    return Xs, ys, tr_i, val_i, x_scaler, y_scaler, classes, out_dim


def train_model(
    X,
    y,
    task: str = "regression",
    cfg: Optional[Config] = None,
    on_epoch: Optional[Callable[[int, float, float], bool]] = None,
) -> Trained:
    """Entrena una PhelisstieNet. on_epoch(epoch, train_loss, val_loss) -> True para parar."""
    cfg = cfg or Config()
    torch.manual_seed(cfg.seed)
    Xs, ys, tr_i, val_i, x_sc, y_sc, classes, out_dim = _prepare(X, y, task, cfg)

    model = PhelisstieNet(Xs.shape[1], out_dim, cfg).to(DEVICE)
    loss_fn = nn.MSELoss() if task == "regression" else nn.CrossEntropyLoss()
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, factor=0.5, patience=max(3, cfg.patience // 3))

    def tens(a, idx):
        return torch.from_numpy(a[idx]).to(DEVICE)

    xt, yt, xv, yv = tens(Xs, tr_i), tens(ys, tr_i), tens(Xs, val_i), tens(ys, val_i)
    loader = DataLoader(TensorDataset(xt, yt), batch_size=cfg.batch_size, shuffle=True, drop_last=len(xt) > cfg.batch_size)

    best, best_state, bad = float("inf"), None, 0
    history = {"train_loss": [], "val_loss": []}

    for epoch in range(1, cfg.epochs + 1):
        model.train()
        total = 0.0
        for xb, yb in loader:
            opt.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step()
            total += loss.item() * len(xb)
        tr_loss = total / len(loader.dataset)

        model.eval()
        with torch.no_grad():
            val_loss = loss_fn(model(xv), yv).item()
        sched.step(val_loss)
        history["train_loss"].append(tr_loss)
        history["val_loss"].append(val_loss)

        if val_loss < best - 1e-6:
            best, best_state, bad = val_loss, copy.deepcopy(model.state_dict()), 0
        else:
            bad += 1
        if on_epoch and on_epoch(epoch, tr_loss, val_loss):
            break
        if bad >= cfg.patience:
            break

    if best_state is not None:
        model.load_state_dict(best_state)
    model.eval()

    metrics = _evaluate(model, xv, yv, task, y_sc)
    metrics["best_val_loss"] = best
    metrics["epochs_run"] = len(history["val_loss"])
    return Trained(model, cfg, task, x_sc, y_sc, classes, history, metrics)


def _evaluate(model, xv, yv, task, y_sc) -> dict:
    with torch.no_grad():
        out = model(xv)
    if task == "regression":
        pred = y_sc.inverse(out.cpu().numpy()).ravel()
        true = y_sc.inverse(yv.cpu().numpy()).ravel()
        mse = float(np.mean((pred - true) ** 2))
        ss_tot = float(np.sum((true - true.mean()) ** 2)) or 1.0
        return {"rmse": mse ** 0.5, "mae": float(np.mean(np.abs(pred - true))),
                "r2": 1.0 - float(np.sum((pred - true) ** 2)) / ss_tot}
    acc = (out.argmax(1) == yv).float().mean().item()
    return {"accuracy": acc}


def predict(t: Trained, X) -> dict:
    X = np.asarray(X, dtype=np.float32)
    xs = torch.from_numpy(t.x_scaler.transform(X).astype(np.float32)).to(DEVICE)
    t.model.eval()
    with torch.no_grad():
        out = t.model(xs)
    if t.task == "regression":
        return {"predictions": t.y_scaler.inverse(out.cpu().numpy()).ravel().tolist()}
    prob = torch.softmax(out, dim=1).cpu().numpy()
    return {
        "predictions": [t.classes[i] for i in prob.argmax(1)],
        "probabilities": prob.tolist(),
        "classes": t.classes,
    }


# ------------------------------------------------------------------ AutoML
def run_automl(
    X,
    y,
    task: str = "regression",
    n_trials: int = 20,
    max_epochs: int = 150,
    on_trial: Optional[Callable[[int, float, dict], None]] = None,
    should_stop: Optional[Callable[[], bool]] = None,
) -> tuple[Trained, list[dict]]:
    """Busca la mejor arquitectura/hiperparámetros con Optuna y reentrena la ganadora."""
    import optuna

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    trials_log: list[dict] = []

    def config_from(trial: "optuna.Trial") -> Config:
        n_layers = trial.suggest_int("n_layers", 1, 4)
        units = [trial.suggest_categorical(f"units_{i}", [16, 32, 64, 128, 256]) for i in range(n_layers)]
        return Config(
            hidden_layers=units,
            dropout=trial.suggest_float("dropout", 0.0, 0.5),
            activation=trial.suggest_categorical("activation", list(ACTIVATIONS)),
            batch_norm=trial.suggest_categorical("batch_norm", [True, False]),
            lr=trial.suggest_float("lr", 1e-4, 3e-2, log=True),
            weight_decay=trial.suggest_float("weight_decay", 1e-6, 1e-2, log=True),
            batch_size=trial.suggest_categorical("batch_size", [16, 32, 64, 128]),
            epochs=max_epochs,
            patience=12,
        )

    def objective(trial: "optuna.Trial") -> float:
        cfg = config_from(trial)

        def on_epoch(ep, tr, va):
            trial.report(va, ep)
            return trial.should_prune()

        res = train_model(X, y, task, cfg, on_epoch=on_epoch)
        val = res.metrics["best_val_loss"]
        entry = {"trial": trial.number, "val_loss": val, "params": dict(trial.params)}
        trials_log.append(entry)
        if on_trial:
            on_trial(trial.number, val, trial.params)
        return val

    def stopper(study, _trial):
        if should_stop and should_stop():
            study.stop()

    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=42),
        pruner=optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=10),
    )
    study.optimize(objective, n_trials=n_trials, callbacks=[stopper], catch=(optuna.TrialPruned,))

    best = study.best_trial
    best_cfg = Config(
        hidden_layers=[best.params[f"units_{i}"] for i in range(best.params["n_layers"])],
        dropout=best.params["dropout"],
        activation=best.params["activation"],
        batch_norm=best.params["batch_norm"],
        lr=best.params["lr"],
        weight_decay=best.params["weight_decay"],
        batch_size=best.params["batch_size"],
        epochs=max_epochs * 2,
        patience=25,
    )
    final = train_model(X, y, task, best_cfg)
    trials_log.sort(key=lambda t: t["val_loss"])
    return final, trials_log


# ------------------------------------------------------------- persistencia
def save_model(t: Trained, path: str) -> None:
    torch.save({
        "state": t.model.state_dict(),
        "cfg": asdict(t.cfg),
        "task": t.task,
        "in_dim": t.model.net[0].in_features,
        "out_dim": t.model.net[-1].out_features,
        "x_mean": t.x_scaler.mean, "x_std": t.x_scaler.std,
        "y_mean": None if t.y_scaler is None else t.y_scaler.mean,
        "y_std": None if t.y_scaler is None else t.y_scaler.std,
        "classes": t.classes, "history": t.history, "metrics": t.metrics,
    }, path)


def load_model(path: str) -> Trained:
    d = torch.load(path, map_location=DEVICE, weights_only=False)
    cfg = Config(**d["cfg"])
    model = PhelisstieNet(d["in_dim"], d["out_dim"], cfg).to(DEVICE)
    model.load_state_dict(d["state"])
    model.eval()
    y_sc = None if d["y_mean"] is None else Scaler(d["y_mean"], d["y_std"])
    return Trained(model, cfg, d["task"], Scaler(d["x_mean"], d["x_std"]), y_sc,
                   d["classes"], d["history"], d["metrics"])


if __name__ == "__main__":
    # Demo rápida: aprende y = 3*x1 - 2*x2 + ruido (tu ejemplo original, pero con más datos)
    rng = np.random.default_rng(0)
    X = rng.uniform(-5, 5, size=(500, 2))
    y = 3 * X[:, 0] - 2 * X[:, 1] + rng.normal(0, 0.3, 500)
    t = train_model(X, y, "regression")
    print("Métricas:", t.metrics)
    print("Predicción [1,2]:", predict(t, [[1.0, 2.0]]), "(esperado ≈ -1)")
