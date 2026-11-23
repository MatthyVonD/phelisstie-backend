import React, { useState, useEffect, useRef } from "react";
import { Mic, MessageSquare, History, Settings, Send, ChevronRight, BrainCircuit } from "lucide-react";
import NeuroPanel from "../phelisstie_ai/src/components/NeuroPanel.jsx";
import { chat } from "../phelisstie_ai/src/services/neuroApi.js";

/* ------------------------------------------------------------------ */
/*  PHELLISSTIE — front-end de asistente multi-agente IA               */
/*  Paleta: negro vacío (#07070a), rojo sangre (#e0142d),               */
/*  rojo profundo (#5c0d16), brasa (#ff3b4e), texto ceniza (#c98d92)   */
/* ------------------------------------------------------------------ */

const AGENTS = [
  { id: "nucleo", label: "Núcleo", color: "#ff3b4e" },
  { id: "analista", label: "Analista", color: "#ff8a3d" },
  { id: "creativo", label: "Creativo", color: "#c13bff" },
  { id: "codigo", label: "Código", color: "#3bd6ff" },
];

const SEED_MESSAGES = [
  {
    id: 1,
    from: "agent",
    agent: "nucleo",
    text: "Hola, soy Phellisstie. Escribe tu mensaje para conversar conmigo.",
  },
];

export default function PhellisstieApp() {
  const [navActive, setNavActive] = useState("chat");
  const [listening, setListening] = useState(false);
  const [messages, setMessages] = useState(SEED_MESSAGES);
  const [chatHistory, setChatHistory] = useState([]);
  const [draft, setDraft] = useState("");
  const [activeAgent, setActiveAgent] = useState("nucleo");
  const [isSending, setIsSending] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, navActive]);

  useEffect(() => {
    if (!listening) return;
    const t = setTimeout(() => {
      setListening(false);
      setMessages((m) => [
        ...m,
        { id: Date.now(), from: "user", text: "( mensaje de voz transcrito )" },
        {
          id: Date.now() + 1,
          from: "agent",
          agent: activeAgent,
          text: "Te escucho. Estoy coordinando con el resto de los agentes para darte una respuesta.",
        },
      ]);
    }, 2600);
    return () => clearTimeout(t);
  }, [listening, activeAgent]);

  async function sendDraft() {
    const text = draft.trim();
    if (!text || isSending) return;
    setMessages((m) => [...m, { id: Date.now(), from: "user", text }]);
    setDraft("");
    setIsSending(true);
    const userMessage = { role: "user", content: text };
    try {
      const { response } = await chat([...chatHistory, userMessage]);
      setChatHistory((history) => [...history, userMessage, { role: "assistant", content: response }].slice(-20));
      setMessages((m) => [
        ...m,
        {
          id: Date.now() + 1,
          from: "agent",
          agent: activeAgent,
          text: response,
        },
      ]);
    } catch (error) {
      setMessages((m) => [
        ...m,
        {
          id: Date.now() + 1,
          from: "agent",
          agent: activeAgent,
          text: `No pude generar una respuesta: ${error.message}`,
        },
      ]);
    } finally {
      setIsSending(false);
    }
  }

  return (
    <div className="ph-root">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@400;500;600;700&display=swap');

        .ph-root{
          --void:#07070a;
          --panel:#0d0d11;
          --panel-2:#131317;
          --red:#e0142d;
          --red-deep:#5c0d16;
          --ember:#ff3b4e;
          --ash:#c98d92;
          --ash-dim:#7a5459;
          --line:#2a1114;
          font-family:'Rajdhani',sans-serif;
          background:
            radial-gradient(1200px 600px at 50% -10%, rgba(224,20,45,0.10), transparent 60%),
            var(--void);
          color:#f2dfe0;
          min-height:100vh;
          width:100%;
          display:flex;
          overflow:hidden;
          position:relative;
        }
        .ph-root *{box-sizing:border-box;}
        .ph-bg-circuit{
          position:absolute; inset:0; opacity:0.35; pointer-events:none;
          background-image:
            linear-gradient(var(--line) 1px, transparent 1px),
            linear-gradient(90deg, var(--line) 1px, transparent 1px);
          background-size: 46px 46px;
          mask-image: radial-gradient(circle at 50% 40%, black 0%, transparent 72%);
        }

        /* ---------- Sidebar ---------- */
        .ph-sidebar{
          width:64px; flex-shrink:0; z-index:5;
          background: linear-gradient(180deg, var(--panel), var(--void));
          border-right:1px solid var(--line);
          display:flex; flex-direction:column; align-items:center;
          padding:24px 0; gap:36px;
        }
        .ph-nav-item{
          display:flex; flex-direction:column; align-items:center; gap:10px;
          background:none; border:none; cursor:pointer; padding:0;
          color: var(--ash-dim);
          transition: color .2s ease, transform .2s ease;
        }
        .ph-nav-item:hover{ color:var(--ash); transform: translateY(-1px); }
        .ph-nav-item.active{ color: var(--ember); }
        .ph-nav-item.active .ph-nav-dot{ background: var(--ember); box-shadow:0 0 8px var(--ember); }
        .ph-nav-label{
          writing-mode: vertical-rl; transform: rotate(180deg);
          font-size:11px; letter-spacing:.18em; text-transform:uppercase; font-weight:600;
        }
        .ph-nav-icon-wrap{
          width:34px; height:34px; border-radius:10px; display:flex; align-items:center; justify-content:center;
          border:1px solid var(--line); background: rgba(224,20,45,0.04);
        }
        .ph-nav-item.active .ph-nav-icon-wrap{
          border-color: rgba(255,59,78,0.5); background: rgba(224,20,45,0.12);
          box-shadow: inset 0 0 12px rgba(255,59,78,0.25);
        }

        /* ---------- Main ---------- */
        .ph-main{
          flex:1; display:flex; flex-direction:column; position:relative; z-index:2;
          min-width:0;
        }
        .ph-topbar{
          display:flex; align-items:center; justify-content:center; flex-direction:column;
          padding: 22px 20px 8px;
        }
        .ph-brand{ display:flex; align-items:center; gap:8px; }
        .ph-brand-mark{ width:26px; height:26px; }
        .ph-brand-text{
          font-family:'Orbitron', sans-serif; font-size:11px; letter-spacing:.32em;
          color: var(--ash); text-transform:uppercase;
        }
        .ph-title{
          margin-top:10px;
          font-family:'Orbitron', sans-serif; font-weight:700; letter-spacing:.12em;
          font-size: clamp(22px, 3vw, 30px);
          color:#fff2f2;
          text-shadow: 0 0 18px rgba(255,59,78,0.55), 0 0 2px rgba(255,59,78,0.9);
        }

        /* ---------- Orb (signature element) ---------- */
        .ph-orb-stage{
          flex-shrink:0;
          display:flex; flex-direction:column; align-items:center; justify-content:center;
          padding: 18px 20px 10px; position:relative;
        }
        .ph-orb-ring{
          position:relative; width:190px; height:190px; display:flex; align-items:center; justify-content:center;
        }
        .ph-orb-ring::before{
          content:''; position:absolute; inset:-18px; border-radius:50%;
          border:1px dashed rgba(255,59,78,0.25);
          animation: ph-spin 22s linear infinite;
        }
        .ph-orb{
          width:170px; height:170px; border-radius:50%; position:relative; overflow:hidden;
          background:
            radial-gradient(circle at 32% 28%, #3a1015 0%, #0c0407 55%, #000 100%);
          box-shadow:
            0 0 40px rgba(224,20,45,0.45),
            0 0 90px rgba(224,20,45,0.18),
            inset 0 0 40px rgba(0,0,0,0.8);
          animation: ph-heartbeat 2.6s ease-in-out infinite;
        }
        .ph-orb.listening{ animation: ph-heartbeat 1s ease-in-out infinite; }
        .ph-orb svg{ position:absolute; inset:0; width:100%; height:100%; opacity:0.9; }
        .ph-orb-pulse{
          position:absolute; inset:0; border-radius:50%;
          box-shadow: 0 0 0 0 rgba(255,59,78,0.5);
          animation: ph-pulse-ring 2.6s ease-out infinite;
        }
        .ph-orb.listening ~ .ph-orb-pulse,
        .ph-orb-pulse.fast{ animation-duration: 1.1s; }

        @keyframes ph-heartbeat{
          0%,100%{ transform: scale(1); }
          15%{ transform: scale(1.05); }
          30%{ transform: scale(0.99); }
          45%{ transform: scale(1.03); }
        }
        @keyframes ph-spin{ to{ transform: rotate(360deg); } }
        @keyframes ph-pulse-ring{
          0%{ box-shadow:0 0 0 0 rgba(255,59,78,0.45); }
          100%{ box-shadow:0 0 0 30px rgba(255,59,78,0); }
        }

        .ph-status{
          margin-top:18px; font-size:15px; letter-spacing:.06em; color: var(--ash);
          min-height: 20px;
        }
        .ph-status.live{ color: var(--ember); text-shadow: 0 0 10px rgba(255,59,78,0.6); }

        .ph-mic-btn{
          margin-top:16px; width:58px; height:58px; border-radius:50%; border:none; cursor:pointer;
          display:flex; align-items:center; justify-content:center;
          background: radial-gradient(circle at 35% 30%, #ff5064, var(--red) 60%, var(--red-deep) 100%);
          box-shadow: 0 0 22px rgba(224,20,45,0.65), 0 4px 12px rgba(0,0,0,0.6);
          color:#fff; transition: transform .15s ease;
        }
        .ph-mic-btn:hover{ transform: scale(1.05); }
        .ph-mic-btn:active{ transform: scale(0.96); }
        .ph-mic-btn.on{ animation: ph-mic-glow 1s ease-in-out infinite; }
        @keyframes ph-mic-glow{
          0%,100%{ box-shadow: 0 0 18px rgba(224,20,45,0.6), 0 4px 12px rgba(0,0,0,0.6); }
          50%{ box-shadow: 0 0 34px rgba(255,59,78,0.95), 0 4px 12px rgba(0,0,0,0.6); }
        }

        /* ---------- Agent selector ---------- */
        .ph-agent-row{
          display:flex; gap:8px; justify-content:center; flex-wrap:wrap;
          padding: 14px 20px 4px;
        }
        .ph-agent-chip{
          font-size:12px; font-weight:600; letter-spacing:.04em;
          padding:6px 12px; border-radius:999px; cursor:pointer;
          background: var(--panel-2); border:1px solid var(--line); color: var(--ash-dim);
          transition: all .15s ease; display:flex; align-items:center; gap:6px;
        }
        .ph-agent-chip .dot{ width:7px; height:7px; border-radius:50%; }
        .ph-agent-chip.active{ color:#fff; border-color: transparent; }

        /* ---------- Chat ---------- */
        .ph-chat{
          flex:1; min-height:0; margin: 8px 16px 0;
          background: linear-gradient(180deg, rgba(19,19,23,0.7), rgba(10,10,12,0.7));
          border:1px solid var(--line); border-radius:16px 16px 0 0;
          display:flex; flex-direction:column; overflow:hidden;
        }
        .ph-chat-scroll{ flex:1; overflow-y:auto; padding:16px; display:flex; flex-direction:column; gap:12px; }
        .ph-msg{ max-width:78%; display:flex; flex-direction:column; gap:4px; }
        .ph-msg.user{ align-self:flex-end; align-items:flex-end; }
        .ph-msg.agent{ align-self:flex-start; align-items:flex-start; }
        .ph-msg-tag{ font-size:11px; letter-spacing:.08em; font-weight:700; text-transform:uppercase; }
        .ph-bubble{
          padding:10px 14px; border-radius:14px; font-size:14.5px; line-height:1.4;
        }
        .ph-msg.user .ph-bubble{
          background: linear-gradient(135deg, var(--red), var(--red-deep));
          color:#fff; border-bottom-right-radius:4px;
        }
        .ph-msg.agent .ph-bubble{
          background: var(--panel-2); border:1px solid var(--line); color:#f0dcdd;
          border-bottom-left-radius:4px;
        }

        .ph-composer{
          display:flex; gap:8px; padding:12px 16px; border-top:1px solid var(--line);
          background: var(--panel);
        }
        .ph-composer input{
          flex:1; background: var(--panel-2); border:1px solid var(--line); border-radius:10px;
          padding:10px 14px; color:#f2dfe0; font-family:'Rajdhani',sans-serif; font-size:14.5px; outline:none;
        }
        .ph-composer input:focus{ border-color: rgba(255,59,78,0.6); }
        .ph-composer input::placeholder{ color: var(--ash-dim); }
        .ph-send-btn{
          width:42px; height:42px; border-radius:10px; border:none; cursor:pointer; flex-shrink:0;
          background: linear-gradient(135deg, var(--ember), var(--red-deep)); color:#fff;
          display:flex; align-items:center; justify-content:center;
        }

        /* ---------- History / Settings panels ---------- */
        .ph-panel-alt{
          flex:1; margin:8px 16px 16px; border:1px solid var(--line); border-radius:16px;
          background: linear-gradient(180deg, rgba(19,19,23,0.7), rgba(10,10,12,0.7));
          padding:20px; overflow-y:auto;
        }
        .ph-panel-alt h3{
          font-family:'Orbitron',sans-serif; font-size:14px; letter-spacing:.12em;
          color:#fff2f2; margin: 0 0 14px; text-transform:uppercase;
        }
        .ph-neuro h2{
          font-family:'Orbitron',sans-serif; font-size:16px; letter-spacing:.12em;
          color:#fff2f2; margin:0 0 10px; text-transform:uppercase;
        }
        .ph-neuro p, .ph-neuro label{ color:var(--ash); }
        .ph-neuro button, .ph-neuro input{
          font:inherit; color:#f2dfe0; background:var(--panel-2);
          border:1px solid var(--line); border-radius:8px; padding:9px 12px;
        }
        .ph-neuro button{ cursor:pointer; }
        .ph-neuro button:disabled{ cursor:wait; opacity:.6; }
        .ph-neuro input{ margin:8px 0; }
        .ph-neuro pre{
          overflow:auto; padding:12px; border-radius:8px;
          background:var(--panel-2); color:#f2dfe0;
        }
        .ph-hist-item{
          display:flex; align-items:center; justify-content:space-between;
          padding:12px 4px; border-bottom:1px solid var(--line); cursor:pointer;
        }
        .ph-hist-item:hover{ color: var(--ember); }
        .ph-hist-item small{ color: var(--ash-dim); display:block; margin-top:2px; }
        .ph-setting-row{
          display:flex; align-items:center; justify-content:space-between;
          padding:14px 4px; border-bottom:1px solid var(--line); font-size:14.5px; color:var(--ash);
        }
        .ph-toggle{
          width:40px; height:22px; border-radius:999px; background: var(--panel-2); border:1px solid var(--line);
          position:relative; cursor:pointer; flex-shrink:0;
        }
        .ph-toggle.on{ background: var(--red); border-color: var(--ember); }
        .ph-toggle::after{
          content:''; position:absolute; top:2px; left:2px; width:16px; height:16px; border-radius:50%;
          background:#fff; transition: left .15s ease;
        }
        .ph-toggle.on::after{ left:20px; }

        @media (max-width: 640px){
          .ph-orb-ring{ width:150px; height:150px; }
          .ph-orb{ width:132px; height:132px; }
          .ph-title{ font-size:22px; }
        }
      `}</style>

      <div className="ph-bg-circuit" />

      {/* SIDEBAR */}
      <nav className="ph-sidebar" aria-label="Navegación principal">
        <button
          className={`ph-nav-item ${navActive === "chat" ? "active" : ""}`}
          onClick={() => setNavActive("chat")}
        >
          <span className="ph-nav-icon-wrap"><MessageSquare size={16} /></span>
          <span className="ph-nav-label">Chat</span>
        </button>
        <button
          className={`ph-nav-item ${navActive === "neuronal" ? "active" : ""}`}
          onClick={() => setNavActive("neuronal")}
        >
          <span className="ph-nav-icon-wrap"><BrainCircuit size={16} /></span>
          <span className="ph-nav-label">IA</span>
        </button>
        <button
          className={`ph-nav-item ${navActive === "historial" ? "active" : ""}`}
          onClick={() => setNavActive("historial")}
        >
          <span className="ph-nav-icon-wrap"><History size={16} /></span>
          <span className="ph-nav-label">Historial</span>
        </button>
        <button
          className={`ph-nav-item ${navActive === "ajustes" ? "active" : ""}`}
          onClick={() => setNavActive("ajustes")}
        >
          <span className="ph-nav-icon-wrap"><Settings size={16} /></span>
          <span className="ph-nav-label">Ajustes</span>
        </button>
      </nav>

      {/* MAIN */}
      <div className="ph-main">
        <div className="ph-topbar">
          <div className="ph-brand">
            <DragonMark />
            <span className="ph-brand-text">IT-SELEPH</span>
          </div>
          <div className="ph-title">PHELLISSTIE</div>
        </div>

        <div className="ph-orb-stage">
          <div className="ph-orb-ring">
            <div className={`ph-orb ${listening ? "listening" : ""}`}>
              <CircuitHeart />
            </div>
            <div className={`ph-orb-pulse ${listening ? "fast" : ""}`} />
          </div>
          <div className={`ph-status ${listening ? "live" : ""}`}>
            {listening ? "Escuchando…" : "Toca para hablar con Phellisstie"}
          </div>
          <button
            className={`ph-mic-btn ${listening ? "on" : ""}`}
            onClick={() => setListening((v) => !v)}
            aria-pressed={listening}
            aria-label={listening ? "Detener escucha" : "Activar micrófono"}
          >
            <Mic size={22} />
          </button>
        </div>

        <div className="ph-agent-row">
          {AGENTS.map((a) => (
            <button
              key={a.id}
              className={`ph-agent-chip ${activeAgent === a.id ? "active" : ""}`}
              style={activeAgent === a.id ? { background: a.color, boxShadow: `0 0 14px ${a.color}66` } : {}}
              onClick={() => setActiveAgent(a.id)}
            >
              <span className="dot" style={{ background: a.color }} />
              {a.label}
            </button>
          ))}
        </div>

        {navActive === "chat" && (
          <div className="ph-chat">
            <div className="ph-chat-scroll" ref={scrollRef}>
              {messages.map((m) => {
                const agentInfo = AGENTS.find((a) => a.id === m.agent);
                return (
                  <div key={m.id} className={`ph-msg ${m.from}`}>
                    {m.from === "agent" && (
                      <span className="ph-msg-tag" style={{ color: agentInfo?.color || "#ff3b4e" }}>
                        {agentInfo?.label || "Phellisstie"}
                      </span>
                    )}
                    <div className="ph-bubble">{m.text}</div>
                  </div>
                );
              })}
            </div>
            <div className="ph-composer">
              <input
                placeholder="Escribe un mensaje…"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !isSending && sendDraft()}
                disabled={isSending}
              />
              <button className="ph-send-btn" onClick={sendDraft} aria-label="Enviar" disabled={isSending}>
                {isSending ? "…" : <Send size={18} />}
              </button>
            </div>
          </div>
        )}

        {navActive === "historial" && (
          <div className="ph-panel-alt">
            <h3>Historial de conversaciones</h3>
            {[
              { t: "Resumen de métricas semanales", d: "Hoy · 09:12" },
              { t: "Plan de contenido para redes", d: "Ayer · 18:40" },
              { t: "Revisión de bug en checkout", d: "Ayer · 11:05" },
              { t: "Borrador de propuesta comercial", d: "Lun · 16:22" },
            ].map((h, i) => (
              <div className="ph-hist-item" key={i}>
                <div>
                  {h.t}
                  <small>{h.d}</small>
                </div>
                <ChevronRight size={16} color="#7a5459" />
              </div>
            ))}
          </div>
        )}

        {navActive === "neuronal" && (
          <div className="ph-panel-alt">
            <NeuroPanel />
          </div>
        )}

        {navActive === "ajustes" && <AjustesPanel />}
      </div>
    </div>
  );
}

function AjustesPanel() {
  const [voice, setVoice] = useState(true);
  const [autoAgents, setAutoAgents] = useState(true);
  const [notifs, setNotifs] = useState(false);
  return (
    <div className="ph-panel-alt">
      <h3>Ajustes</h3>
      <div className="ph-setting-row">
        <span>Respuesta por voz</span>
        <div className={`ph-toggle ${voice ? "on" : ""}`} onClick={() => setVoice((v) => !v)} />
      </div>
      <div className="ph-setting-row">
        <span>Enrutamiento automático de agentes</span>
        <div className={`ph-toggle ${autoAgents ? "on" : ""}`} onClick={() => setAutoAgents((v) => !v)} />
      </div>
      <div className="ph-setting-row">
        <span>Notificaciones</span>
        <div className={`ph-toggle ${notifs ? "on" : ""}`} onClick={() => setNotifs((v) => !v)} />
      </div>
      <div className="ph-setting-row" style={{ borderBottom: "none" }}>
        <span>Versión</span>
        <span style={{ color: "#7a5459" }}>Phellisstie-1.0 · IT-SELEPH</span>
      </div>
    </div>
  );
}

/* Logo ouroboros-dragón simplificado en SVG */
function DragonMark() {
  return (
    <svg className="ph-brand-mark" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <circle cx="50" cy="50" r="46" fill="none" stroke="#e0142d" strokeWidth="6" strokeDasharray="4 3" opacity="0.85" />
      <circle cx="50" cy="50" r="34" fill="#0c0407" stroke="#5c0d16" strokeWidth="2" />
      <path
        d="M50 30 L54 40 L50 46 L46 40 Z M50 46 Q58 50 54 60 Q50 68 50 68 Q50 68 46 60 Q42 50 50 46 Z"
        fill="#e0142d"
      />
    </svg>
  );
}

/* Esfera corazón-circuito — elemento firma del diseño */
function CircuitHeart() {
  return (
    <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="heartGlow" cx="50%" cy="45%" r="60%">
          <stop offset="0%" stopColor="#ff5064" />
          <stop offset="55%" stopColor="#e0142d" />
          <stop offset="100%" stopColor="#3a0a10" />
        </radialGradient>
      </defs>
      {Array.from({ length: 10 }).map((_, i) => {
        const angle = (i / 10) * Math.PI * 2;
        const x1 = 100 + Math.cos(angle) * 20;
        const y1 = 100 + Math.sin(angle) * 20;
        const x2 = 100 + Math.cos(angle) * 78;
        const y2 = 100 + Math.sin(angle) * 78;
        return (
          <g key={i} opacity="0.55">
            <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#ff3b4e" strokeWidth="1" />
            <circle cx={x2} cy={y2} r="2.4" fill="#ff3b4e" />
          </g>
        );
      })}
      <path
        d="M100 120
           C 78 100, 62 86, 62 68
           C 62 54, 74 46, 86 52
           C 92 55, 97 61, 100 68
           C 103 61, 108 55, 114 52
           C 126 46, 138 54, 138 68
           C 138 86, 122 100, 100 120 Z"
        fill="url(#heartGlow)"
        stroke="#ff8a90"
        strokeWidth="1"
      />
    </svg>
  );
}
