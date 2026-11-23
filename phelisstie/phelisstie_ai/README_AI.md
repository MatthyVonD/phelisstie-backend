# Phelisstie AI

## Desarrollo local

El chat usa Ollama con un modelo de lenguaje local; la sección **IA** conserva
la red numérica de PyTorch para entrenar y predecir. Desde la raíz del proyecto:

1. Instala Ollama si aún no está instalado y descarga el modelo:

   ```powershell
   winget install --id Ollama.Ollama -e
   ollama pull qwen2.5:3b
   ```

2. Instala las dependencias y arranca la API:

   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r phelisstie_ai\requirements.txt
   .\.venv\Scripts\python.exe -m uvicorn api:app --app-dir phelisstie_ai --reload --port 8000
   ```

3. En otra terminal, arranca el front-end:

   ```powershell
   npm install
   npm run dev
   ```

Escribe un mensaje libre en **Chat**: se enviará al backend, que conserva el
historial de la conversación y solicita una respuesta a Ollama en `127.0.0.1:11434`.
Vite reenvía `/api` al backend en `127.0.0.1:8000`; la documentación está en
`/docs`. Puedes cambiar el modelo con `PHELISSTIE_LLM_MODEL` o la URL de Ollama
con `PHELISSTIE_OLLAMA_URL`.

En la sección **IA** puedes entrenar la red numérica de ejemplo, ejecutar AutoML
y probar predicciones. Para producción, configura `VITE_NEURO_API` con la URL
desplegada de la API.

## Endpoints
GET /health · POST /chat · POST /train · POST /automl · GET /jobs/{id} · POST /jobs/{id}/stop · GET /model · POST /predict
