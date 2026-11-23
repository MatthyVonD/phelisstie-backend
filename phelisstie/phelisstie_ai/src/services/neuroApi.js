// En desarrollo, Vite reenvía /api al backend FastAPI.
const BASE = import.meta.env.VITE_NEURO_API ?? "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail ?? `Error ${res.status}`);
  return data;
}

const post = (path, body) => request(path, { method: "POST", body: JSON.stringify(body) });

export const health = () => request("/health");
export const startTraining = (dataset, opts = {}) => post("/train", { ...dataset, ...opts });
export const startAutoML = (dataset, opts = {}) => post("/automl", { ...dataset, ...opts });
export const getJob = (id) => request(`/jobs/${id}`);
export const stopJob = (id) => post(`/jobs/${id}/stop`, {});
export const getModel = () => request("/model");
export const predict = (X) => post("/predict", { X });
export const chat = (messages) => post("/chat", { messages });

// Espera a que un trabajo termine, avisando del progreso.
export async function waitForJob(id, onProgress, intervalMs = 1000) {
  for (;;) {
    const job = await getJob(id);
    onProgress?.(job);
    if (job.status !== "running") return job;
    await new Promise((r) => setTimeout(r, intervalMs));
  }
}
