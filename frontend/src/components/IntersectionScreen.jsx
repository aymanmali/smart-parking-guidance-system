import React from "react";
import { ArrowLeft, ArrowRight, ArrowUp, Radio } from "lucide-react";

function DirectionIcon({ direction, status }) {
  const color =
    status === "FULL"
      ? "text-red-400"
      : status === "LIMITED"
      ? "text-amber-400"
      : "text-emerald-400";
  const cls = `w-10 h-10 ${color}`;
  if (direction === "left") return <ArrowLeft className={cls} strokeWidth={2.75} />;
  if (direction === "right") return <ArrowRight className={cls} strokeWidth={2.75} />;
  return <ArrowUp className={cls} strokeWidth={2.75} />;
}

function ledClass(status) {
  if (status === "FULL") return "led-red";
  if (status === "LIMITED") return "led-amber";
  return "led-green";
}

export default function IntersectionScreen({ intersection }) {
  return (
    <div className="sign-board rounded-2xl p-5 border border-slate-800 flex flex-col gap-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <p className="text-xs font-mono uppercase tracking-widest text-slate-400">
            {intersection.display_node_id} · RS-485 #{intersection.rs485_address}
          </p>
          <h3 className="text-lg font-bold text-white">{intersection.id} — {intersection.name}</h3>
        </div>
        <span className="px-2.5 py-1 rounded bg-sky-500/15 text-sky-300 border border-sky-500/30 text-[11px] font-mono">
          LIVE GUIDANCE
        </span>
      </div>

      {/* 3 Directional LED Panels */}
      <div className="grid grid-cols-3 gap-3">
        {intersection.branches.map((br) => (
          <div
            key={br.direction}
            className={`rounded-xl p-4 bg-black/85 border flex flex-col items-center text-center gap-2 ${
              br.status === "FULL"
                ? "border-red-500/40"
                : br.status === "LIMITED"
                ? "border-amber-500/40"
                : "border-emerald-500/35"
            }`}
          >
            <DirectionIcon direction={br.direction} status={br.status} />
            <div className={`text-4xl font-mono font-black ${ledClass(br.status)}`}>
              {br.status === "FULL" ? "FULL" : br.available}
            </div>
            <p className="text-xs font-medium text-slate-200 leading-tight">{br.label}</p>
            <p className="text-[11px] font-mono text-slate-500">
              {br.available} / {br.total} free
            </p>
          </div>
        ))}
      </div>

      {/* Hardware Wire Frame */}
      <div className="text-[11px] font-mono text-slate-500 bg-slate-950/70 rounded-lg p-2.5 border border-slate-800/70 space-y-1">
        <div className="flex items-center gap-1.5 text-slate-400">
          <Radio className="w-3.5 h-3.5 text-sky-400" />
          <span className="truncate">{intersection.mqtt_topic}</span>
        </div>
        <div className="truncate">RS-485 TX: 0x{intersection.rs485_frame_hex}</div>
      </div>
    </div>
  );
}
