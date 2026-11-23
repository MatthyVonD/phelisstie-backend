import { useEffect, useState } from "react";
import { health, startAutoML, startTraining, waitForJob, predict } from "../services/neuroApi";

// Datos de ejemplo: y = 3*x1 - 2*x2 + ruido. Sustituye por los datos de tus empresas/campañas.
function demoDataset(n = 300) {
  const X = Array.from({ length: n }, () => [Math.random() * 10 - 5, Math.random() * 10 - 5]);
  const y = X.map(([a, b]) => 3 * a - 2 * b + (Math.random() - 0.5) * 0.6);
  return { X, y, task: "regression" };
}

export default function NeuroPanel() {
  const [status, setStatus] = useState("Listo");
  const [job, setJob] = useState(null);
  const [result, setResult] = useState(null);
  const [input, setInput] = useState("1, 2");
  const [pred, setPred] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    health()
      .then(() => {
        if (active) setStatus("API conectada. Entrena el modelo para empezar.");
      })
      .catch((e) => {
        if (active) {
          setStatus("API no disponible");
          setError(`No se pudo conectar con Phelisstie AI: ${e.message}`);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  async function run(kind) {
    setError(null);
    setResult(null);
    setPred(null);
    setJob(null);
    setBusy(true);
    try {
      setStatus(kind === "automl" ? "Buscando la mejor red (AutoML)…" : "Entrenando…");
      const data = demoDataset();
      const { job_id } =
        kind === "automl"
          ? await startAutoML(data, { n_trials: 15, max_epochs: 100 })
          : await startTraining(data, { hidden_layers: [64, 32], epochs: 200 });
      const final = await waitForJob(job_id, setJob);
      if (final.status === "error") throw new Error(final.error);
      setResult(final.result);
      setStatus("Entrenamiento completado");
    } catch (e) {
      setError(e.message);
      setStatus("Error");
    } finally {
      setBusy(false);
    }
  }

  async function onPredict() {
    setError(null);
    setPred(null);
    try {
      const row = input.split(",").map(Number);
      if (row.length !== result.n_features || row.some((value) => !Number.isFinite(value))) {
        throw new Error(`Escribe ${result.n_features} valores numéricos separados por comas.`);
      }
      const { predictions } = await predict([row]);
      setPred(predictions[0]);
    } catch (e) {
      setError(e.message);
    }
  }

  const last = job?.progress?.at(-1);

  return (
    <section className="ph-neuro">
      <h2>Red neuronal</h2>
      <p>Entrena el modelo numérico de Phelisstie AI y prueba sus predicciones. Esta red no genera texto de chat.</p>
      <p>{status}</p>
      <button onClick={() => run("train")} disabled={busy}>Entrenar red profunda</button>{" "}
      <button onClick={() => run("automl")} disabled={busy}>Ejecutar AutoML</button>

      {last && job.status === "running" && (
        <p>{last.epoch ? `Época ${last.epoch} · val_loss ${last.val_loss.toFixed(4)}` : `Prueba ${last.trial + 1} · val_loss ${last.val_loss.toFixed(4)}`}</p>
      )}
      {error && <p style={{ color: "crimson" }}>{error}</p>}

      {result && (
        <>
          <h3>Resultado</h3>
          <pre>{JSON.stringify({ metricas: result.metrics, arquitectura: result.config.hidden_layers }, null, 2)}</pre>
          <label htmlFor="neuro-input">Valores de entrada (separados por comas)</label>
          <input id="neuro-input" value={input} onChange={(e) => setInput(e.target.value)} />{" "}
          <button onClick={onPredict} disabled={busy}>Predecir</button>
          {pred !== null && <p>Predicción: <b>{typeof pred === "number" ? pred.toFixed(3) : pred}</b></p>}
        </>
      )}
    </section>
  );
}
