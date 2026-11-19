import React, { useEffect, useRef, useState } from "react";
import {
  Activity,
  Award,
  Camera,
  Car,
  Cpu,
  LayoutGrid,
  Monitor,
  Navigation,
  Pause,
  Play,
  Wifi,
  WifiOff,
} from "lucide-react";
import EntranceScreen from "./components/EntranceScreen.jsx";
import IntersectionScreen from "./components/IntersectionScreen.jsx";
import FacilityMap from "./components/FacilityMap.jsx";
import CaseStudyView from "./components/CaseStudyView.jsx";
import { DemoParkingEngine } from "./lib/demoEngine.js";

const API_BASE = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

const TABS = [
  { id: "dashboard", label: "300-Slot Dashboard", icon: LayoutGrid },
  { id: "entrances", label: "Entrance Screens (2)", icon: Monitor },
  { id: "intersections", label: "Intersection Signs (4)", icon: Navigation },
  { id: "cameras", label: "Edge Cameras (12)", icon: Camera },
  { id: "casestudy", label: "Galleria40 Case Study", icon: Award },
];

const SCENARIOS = [
  { id: "empty", label: "Empty" },
  { id: "balanced", label: "Balanced" },
  { id: "morning_rush", label: "Morning Rush" },
  { id: "zone_a_full", label: "Zone A Full" },
  { id: "peak_full", label: "Peak Full" },
];

export default function App() {
  const [snapshot, setSnapshot] = useState(null);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [mode, setMode] = useState("connecting"); // "live" | "demo" | "connecting"
  const [wsConnected, setWsConnected] = useState(false);
  const [simRunning, setSimRunning] = useState(false);

  const demoEngineRef = useRef(null);
  const demoTimerRef = useRef(null);

  const getDemoEngine = () => {
    if (!demoEngineRef.current) {
      demoEngineRef.current = new DemoParkingEngine();
    }
    return demoEngineRef.current;
  };

  useEffect(() => {
    let ws;
    let retryTimer;
    let cancelled = false;

    const activateDemoMode = () => {
      if (cancelled) return;
      setMode("demo");
      setWsConnected(false);
      setSnapshot(getDemoEngine().getSnapshot());
    };

    const connectWs = () => {
      if (cancelled) return;
      let wsUrl;
      if (API_BASE) {
        wsUrl = API_BASE.replace(/^http/, "ws") + "/ws/live";
      } else {
        const proto = window.location.protocol === "https:" ? "wss" : "ws";
        wsUrl = `${proto}://${window.location.host}/ws/live`;
      }

      ws = new WebSocket(wsUrl);
      ws.onopen = () => {
        if (cancelled) return;
        setMode("live");
        setWsConnected(true);
      };
      ws.onclose = () => {
        if (cancelled) return;
        setWsConnected(false);
        retryTimer = setTimeout(connectWs, 3000);
      };
      ws.onmessage = (evt) => {
        try {
          setSnapshot(JSON.parse(evt.data));
        } catch {
          // ignore malformed frames
        }
      };
    };

    // Probe backend first with a short timeout; fall back cleanly to Demo Engine on static hosts (e.g., Vercel)
    const controller = new AbortController();
    const probeTimeout = setTimeout(() => controller.abort(), 1600);

    fetch(`${API_BASE}/api/v1/snapshot`, { signal: controller.signal })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        clearTimeout(probeTimeout);
        if (cancelled) return;
        setMode("live");
        setSnapshot(data);
        connectWs();
      })
      .catch(() => {
        clearTimeout(probeTimeout);
        activateDemoMode();
      });

    return () => {
      cancelled = true;
      clearTimeout(probeTimeout);
      clearTimeout(retryTimer);
      clearInterval(demoTimerRef.current);
      if (ws) ws.close();
    };
  }, []);

  // Browser simulation timer when in Demo Mode
  useEffect(() => {
    clearInterval(demoTimerRef.current);
    if (mode === "demo" && simRunning) {
      demoTimerRef.current = setInterval(() => {
        setSnapshot(getDemoEngine().stepTraffic(3));
      }, 2000);
    }
    return () => clearInterval(demoTimerRef.current);
  }, [mode, simRunning]);

  const handleToggleSim = async () => {
    const next = !simRunning;
    if (mode === "demo") {
      setSimRunning(next);
      if (next) {
        setSnapshot(getDemoEngine().stepTraffic(3));
      }
      return;
    }

    const res = await fetch(`${API_BASE}/api/v1/simulation/toggle?running=${next}`, {
      method: "POST",
    });
    if (res.ok) {
      const data = await res.json();
      setSimRunning(data.simulator_running);
    }
  };

  const handleScenario = async (scenario) => {
    if (mode === "demo") {
      setSnapshot(getDemoEngine().applyScenario(scenario));
      return;
    }

    await fetch(`${API_BASE}/api/v1/simulation/scenario`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario }),
    });
  };

  const handleToggleSlot = async (slot) => {
    if (mode === "demo") {
      setSnapshot(getDemoEngine().toggleSlot(slot.id));
      return;
    }

    await fetch(`${API_BASE}/api/v1/slots/${slot.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ occupied: !slot.occupied }),
    });
  };

  if (!snapshot) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-300 font-mono">
        Initializing SmartPark 300 Guidance Engine...
      </div>
    );
  }

  const { facility, zones, entrances, intersections, cameras, slots } = snapshot;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navigation */}
      <header className="border-b border-slate-800 bg-slate-900/70 backdrop-blur sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
              <Car className="w-5 h-5" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-base font-bold tracking-tight text-white">{facility.name}</h1>
                <button
                  type="button"
                  onClick={() => setActiveTab("casestudy")}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/35 hover:bg-emerald-500/25 cursor-pointer transition"
                  title="Read the 2019 Galleria40 Mall (LEED Certified) deployment case study"
                >
                  <Award className="w-3 h-3" />
                  Galleria40 · LEED (2019)
                </button>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                300 Slots · 12 Edge Cameras · 2 Entrances · 4 Intersections
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleToggleSim}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer border transition ${
                simRunning
                  ? "bg-amber-500/20 text-amber-300 border-amber-500/40 hover:bg-amber-500/30"
                  : "bg-emerald-500/20 text-emerald-300 border-emerald-500/40 hover:bg-emerald-500/30"
              }`}
            >
              {simRunning ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
              {simRunning ? "Pause Live Traffic" : "Start Live Traffic"}
            </button>

            {mode === "demo" ? (
              <span
                className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-mono border bg-sky-500/10 text-sky-300 border-sky-500/30"
                title="Running standalone in-browser 300-slot simulation engine (FastAPI backend not connected)"
              >
                <Cpu className="w-3.5 h-3.5" />
                DEMO ENGINE
              </span>
            ) : (
              <span
                className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-mono border ${
                  wsConnected
                    ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/30"
                    : "bg-red-500/10 text-red-300 border-red-500/30"
                }`}
              >
                {wsConnected ? <Wifi className="w-3.5 h-3.5" /> : <WifiOff className="w-3.5 h-3.5" />}
                {wsConnected ? "WS LIVE" : "OFFLINE"}
              </span>
            )}
          </div>
        </div>

        {/* Sub-nav Tabs */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center gap-1 overflow-x-auto pb-2">
          {TABS.map((t) => {
            const Icon = t.icon;
            const active = activeTab === t.id;
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => setActiveTab(t.id)}
                className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-medium cursor-pointer transition whitespace-nowrap ${
                  active
                    ? "bg-slate-800 text-white border border-slate-700"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
                }`}
              >
                <Icon className="w-4 h-4" />
                {t.label}
              </button>
            );
          })}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 flex-1 space-y-6">
        {/* KPI Summary Strip */}
        {activeTab !== "casestudy" && (
          <>
            <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
                <p className="text-xs font-mono text-slate-400 uppercase">Available Spaces</p>
                <p className="text-3xl font-mono font-bold text-emerald-400 mt-1">
                  {facility.available_slots}
                  <span className="text-sm text-slate-500 font-normal">
                    {" "}
                    / {facility.total_slots}
                  </span>
                </p>
              </div>
              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
                <p className="text-xs font-mono text-slate-400 uppercase">Occupied Spaces</p>
                <p className="text-3xl font-mono font-bold text-red-400 mt-1">
                  {facility.occupied_slots}
                </p>
              </div>
              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
                <p className="text-xs font-mono text-slate-400 uppercase">Occupancy Rate</p>
                <p className="text-3xl font-mono font-bold text-sky-400 mt-1">
                  {Math.round(facility.occupancy_rate * 100)}%
                </p>
              </div>
              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
                <p className="text-xs font-mono text-slate-400 uppercase">Edge Cameras Online</p>
                <p className="text-3xl font-mono font-bold text-white mt-1 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-emerald-400" />
                  {facility.cameras_online}/{facility.cameras_total}
                </p>
              </div>
            </section>

            {/* Scenario Bar */}
            <section className="flex flex-wrap items-center gap-2 bg-slate-900/50 border border-slate-800/80 rounded-xl px-4 py-3">
              <span className="text-xs font-mono text-slate-400 mr-2">TEST SCENARIOS:</span>
              {SCENARIOS.map((sc) => (
                <button
                  key={sc.id}
                  type="button"
                  onClick={() => handleScenario(sc.id)}
                  className="px-3 py-1 rounded-md text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 cursor-pointer transition"
                >
                  {sc.label}
                </button>
              ))}
              <span className="ml-auto text-[11px] text-slate-500 hidden sm:inline">
                Tip: Click any slot on the map to manually toggle occupancy
              </span>
            </section>
          </>
        )}

        {/* Tab Views */}
        {activeTab === "dashboard" && (
          <FacilityMap zones={zones} slots={slots} onToggleSlot={handleToggleSlot} />
        )}

        {activeTab === "entrances" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {entrances.map((ent) => (
              <EntranceScreen key={ent.id} entrance={ent} />
            ))}
          </div>
        )}

        {activeTab === "intersections" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {intersections.map((inter) => (
              <IntersectionScreen key={inter.id} intersection={inter} />
            ))}
          </div>
        )}

        {activeTab === "cameras" && (
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-900 text-xs font-mono uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">Camera</th>
                  <th className="px-4 py-3">Zone</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Slots Occupied</th>
                  <th className="px-4 py-3">FPS</th>
                  <th className="px-4 py-3">Inference</th>
                  <th className="px-4 py-3">RTSP Stream</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70 font-mono text-xs">
                {cameras.map((cam) => (
                  <tr key={cam.id} className="hover:bg-slate-800/40">
                    <td className="px-4 py-3 font-semibold text-white">{cam.id}</td>
                    <td className="px-4 py-3 text-slate-300">{cam.zone_id}</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300">
                        {cam.online ? "ONLINE" : "OFFLINE"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-200">
                      {cam.occupied_count} / {cam.slot_count}
                    </td>
                    <td className="px-4 py-3 text-slate-300">{cam.fps.toFixed(1)}</td>
                    <td className="px-4 py-3 text-sky-300">{cam.inference_ms.toFixed(1)} ms</td>
                    <td className="px-4 py-3 text-slate-500">{cam.rtsp_url}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === "casestudy" && <CaseStudyView facility={facility} />}
      </main>
    </div>
  );
}
