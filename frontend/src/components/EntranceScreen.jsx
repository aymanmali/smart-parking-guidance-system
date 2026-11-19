import React from "react";
import { Radio, ShieldCheck } from "lucide-react";

function statusClass(status) {
  if (status === "FULL") return "led-red";
  if (status === "LIMITED") return "led-amber";
  return "led-green";
}

function badgeClass(status) {
  if (status === "FULL") return "bg-red-500/20 text-red-300 border-red-500/40";
  if (status === "LIMITED") return "bg-amber-500/20 text-amber-300 border-amber-500/40";
  return "bg-emerald-500/20 text-emerald-300 border-emerald-500/40";
}

export default function EntranceScreen({ entrance }) {
  return (
    <div className="sign-board rounded-2xl p-6 flex flex-col gap-5 border border-slate-800">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <p className="text-xs font-mono uppercase tracking-widest text-slate-400">
            {entrance.display_node_id} · RS-485 #{entrance.rs485_address}
          </p>
          <h3 className="text-xl font-bold text-white mt-0.5">{entrance.name}</h3>
        </div>
        <span
          className={`px-3 py-1 rounded-full text-xs font-bold tracking-wider border ${badgeClass(
            entrance.status
          )}`}
        >
          {entrance.status}
        </span>
      </div>

      {/* Main LED Counter */}
      <div className="bg-black/80 rounded-xl p-6 border border-slate-800/80 text-center">
        <p className="text-xs font-mono uppercase tracking-[0.25em] text-slate-400">
          Available Parking Spaces
        </p>
        <div className={`text-7xl font-mono font-black tracking-tight my-2 ${statusClass(entrance.status)}`}>
          {String(entrance.available_slots).padStart(3, "0")}
        </div>
        <p className="text-sm text-slate-400 font-mono">
          {entrance.occupied_slots} Occupied / {entrance.total_slots} Total
        </p>
        {entrance.recommended_zone && (
          <div className="mt-4 inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-medium">
            <ShieldCheck className="w-4 h-4" />
            Recommended: {entrance.recommended_zone}
          </div>
        )}
      </div>

      {/* Zone Breakdown */}
      <div className="grid grid-cols-2 gap-3">
        {entrance.zones.map((z) => (
          <div
            key={z.zone_id}
            className="bg-slate-900/90 border border-slate-800 rounded-xl px-4 py-3 flex items-center justify-between"
          >
            <div>
              <p className="text-xs font-mono text-slate-400">{z.zone_id}</p>
              <p className="text-sm font-semibold text-slate-200">Zone {z.code}</p>
            </div>
            <div className="text-right">
              <p className={`text-2xl font-mono font-bold ${statusClass(z.status)}`}>
                {z.available}
              </p>
              <p className="text-[11px] font-mono text-slate-500">/ {z.total}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Hardware Telemetry Footer */}
      <div className="text-[11px] font-mono text-slate-500 bg-slate-950/70 rounded-lg p-3 border border-slate-800/70 space-y-1">
        <div className="flex items-center gap-1.5 text-slate-400">
          <Radio className="w-3.5 h-3.5 text-sky-400" />
          <span>MQTT: {entrance.mqtt_topic}</span>
        </div>
        <div className="truncate">RS-485 TX: 0x{entrance.rs485_frame_hex}</div>
      </div>
    </div>
  );
}
