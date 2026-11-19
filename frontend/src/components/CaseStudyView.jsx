import React from "react";
import {
  Award,
  Building2,
  Cpu,
  Eye,
  Leaf,
  MapPin,
  ShieldAlert,
  Wrench,
} from "lucide-react";

const ENGINEERING_PILLARS = [
  {
    icon: Eye,
    title: "Multi-Camera Edge Vision",
    desc: "12 overhead cameras monitoring 300 individual stalls via YOLO vehicle detection, calibrated OpenCV ROI polygons, and temporal hysteresis to eliminate flicker from passing aisle traffic.",
  },
  {
    icon: Cpu,
    title: "Custom PCB & Embedded C Nodes",
    desc: "ESP32-based SPG-CTRL-v1 signage controller board with ESD-protected RS-485 industrial bus, CRC-16/MODBUS framing, 12V/24V MOSFET LED arrow drivers, and 15-second amber offline fallback.",
  },
  {
    icon: Leaf,
    title: "LEED Sustainability Alignment",
    desc: "Real-time entrance & intersection guidance cuts stall-search cruising time—reducing indoor CO/NOx emissions, lowering garage ventilation fan runtime, and eliminating peak-hour entry queues.",
  },
  {
    icon: Wrench,
    title: "Field-Hardened Reliability",
    desc: "Engineered for commercial retail uptime: wide-input 12–24V buck regulation with surge/reverse-polarity protection, camera heartbeat telemetry, and manual operator overrides.",
  },
];

export default function CaseStudyView({ facility }) {
  // Transparent engineering model illustrating daily LEED/cruising impact for a 300-slot commercial mall
  const dailyVehiclesEstimate = 1100; // ~3.6 turnovers/slot/day for a commercial mall/office hub
  const cruisingMinutesSavedPerCar = 2.5; // typical guided vs unguided search reduction
  const dailyMinutesSaved = Math.round(dailyVehiclesEstimate * cruisingMinutesSavedPerCar);
  const dailyCo2SavedKg = Math.round(dailyMinutesSaved * 0.045); // ~45g CO2/min low-speed idling/cruising

  return (
    <div className="space-y-6">
      {/* Hero Banner */}
      <section className="rounded-2xl border border-emerald-500/30 bg-gradient-to-br from-emerald-950/50 via-slate-900 to-slate-950 p-6 sm:p-8">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
            <Award className="w-3.5 h-3.5" />
            LEED Certified Commercial Complex
          </span>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono bg-slate-800 text-slate-300 border border-slate-700">
            <MapPin className="w-3.5 h-3.5 text-sky-400" />
            Galleria40 Mall · Sheikh Zayed, Egypt · Installed 2019
          </span>
        </div>

        <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          Field-Deployed Smart Parking Guidance System
        </h2>
        <p className="text-sm sm:text-base text-slate-300 mt-3 max-w-3xl leading-relaxed">
          Originally architected, engineered, and commissioned in <strong className="text-white">2019</strong> for{" "}
          <strong className="text-white">Galleria40</strong>—a LEED-certified commercial, retail, and
          office destination in Sheikh Zayed, Egypt. The system monitored <strong className="text-white">300 parking slots</strong>{" "}
          in real time from edge cameras to drive physical LED entrance counters and internal intersection
          directional guidance screens.
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6">
          <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5">
            <p className="text-[11px] font-mono uppercase text-slate-400">Deployment Year</p>
            <p className="text-2xl font-mono font-bold text-white mt-0.5">2019</p>
          </div>
          <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5">
            <p className="text-[11px] font-mono uppercase text-slate-400">Facility Capacity</p>
            <p className="text-2xl font-mono font-bold text-emerald-400 mt-0.5">
              {facility.total_slots} Slots
            </p>
          </div>
          <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5">
            <p className="text-[11px] font-mono uppercase text-slate-400">Building Standard</p>
            <p className="text-2xl font-mono font-bold text-emerald-300 mt-0.5">LEED</p>
          </div>
          <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5">
            <p className="text-[11px] font-mono uppercase text-slate-400">Scope Delivered</p>
            <p className="text-lg font-mono font-bold text-sky-300 mt-1.5">CV + API + C + PCB</p>
          </div>
        </div>
      </section>

      {/* Engineering Pillars */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {ENGINEERING_PILLARS.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.title}
              className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 flex gap-4"
            >
              <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-emerald-400 shrink-0">
                <Icon className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">{item.title}</h3>
                <p className="text-sm text-slate-400 mt-1.5 leading-relaxed">{item.desc}</p>
              </div>
            </div>
          );
        })}
      </section>

      {/* LEED Environmental Impact Model */}
      <section className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
          <div className="flex items-center gap-2.5">
            <Building2 className="w-5 h-5 text-emerald-400" />
            <h3 className="text-lg font-bold text-white">
              Why Parking Guidance Matters in LEED-Certified Facilities
            </h3>
          </div>
          <span className="text-[11px] font-mono text-slate-400 bg-slate-950 border border-slate-800 px-2.5 py-1 rounded">
            MODELED IMPACT · 300 SLOTS
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4">
            <p className="text-xs font-mono text-slate-400">Cruising Time Saved / Day</p>
            <p className="text-2xl font-mono font-bold text-emerald-400 mt-1">
              ~{(dailyMinutesSaved / 60).toFixed(0)} hrs
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Assuming ~{dailyVehiclesEstimate} daily visits &amp; {cruisingMinutesSavedPerCar} min
              faster stall discovery
            </p>
          </div>

          <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4">
            <p className="text-xs font-mono text-slate-400">Estimated CO₂ Avoided / Year</p>
            <p className="text-2xl font-mono font-bold text-sky-400 mt-1">
              ~{((dailyCo2SavedKg * 365) / 1000).toFixed(1)} tons
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Lower low-speed indoor idling across entrance ramps &amp; aisles
            </p>
          </div>

          <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4">
            <p className="text-xs font-mono text-slate-400">Indoor Air &amp; HVAC Benefit</p>
            <p className="text-2xl font-mono font-bold text-amber-300 mt-1">Lower Peak CO</p>
            <p className="text-xs text-slate-500 mt-1">
              Reduces demand-controlled exhaust fan spikes during mall rush hours
            </p>
          </div>
        </div>
      </section>

      {/* Open-Source Reference Note */}
      <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-4 flex items-start gap-3 text-xs text-slate-400">
        <ShieldAlert className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong className="text-slate-200">Reference Architecture Notice:</strong> This public
          repository and interactive web simulator present a modernized open-source architecture
          inspired by the 2019 Galleria40 production installation. All live counts, camera IDs, and
          scenarios shown here use synthetic simulation data—no proprietary client footage, network
          details, or confidential site assets are included.
        </p>
      </section>
    </div>
  );
}
