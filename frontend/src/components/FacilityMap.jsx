import React from "react";

export default function FacilityMap({ zones, slots, onToggleSlot }) {
  const slotsByZone = {};
  for (const s of slots) {
    if (!slotsByZone[s.zone_id]) slotsByZone[s.zone_id] = [];
    slotsByZone[s.zone_id].push(s);
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
      {zones.map((zone) => {
        const zSlots = (slotsByZone[zone.id] || []).slice().sort((a, b) => a.id.localeCompare(b.id));
        return (
          <div
            key={zone.id}
            className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 flex flex-col gap-4"
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white">{zone.name}</h3>
                <p className="text-xs text-slate-400 font-mono">
                  {zone.available_slots} free · {zone.occupied_slots} occupied ·{" "}
                  {Math.round(zone.occupancy_rate * 100)}% full
                </p>
              </div>
              <span
                className={`px-2.5 py-1 rounded-full text-xs font-bold border ${
                  zone.status === "FULL"
                    ? "bg-red-500/20 text-red-300 border-red-500/40"
                    : zone.status === "LIMITED"
                    ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                    : "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                }`}
              >
                {zone.status}
              </span>
            </div>

            {/* 75 slots rendered as 15 columns x 5 rows */}
            <div className="grid grid-cols-15 gap-1">
              {zSlots.map((slot) => {
                const isOcc = slot.occupied;
                return (
                  <button
                    key={slot.id}
                    type="button"
                    onClick={() => onToggleSlot(slot)}
                    title={`${slot.id} (${slot.slot_type}) — ${
                      isOcc ? `Occupied (${slot.vehicle_class || "car"})` : "Available"
                    } · Click to toggle`}
                    className={`h-7 rounded text-[9px] font-mono font-semibold transition-all cursor-pointer border ${
                      isOcc
                        ? "bg-red-500/30 border-red-500/60 text-red-200 hover:bg-red-500/50"
                        : slot.slot_type === "ev_charging"
                        ? "bg-sky-500/25 border-sky-400/50 text-sky-200 hover:bg-sky-500/45"
                        : slot.slot_type === "accessible"
                        ? "bg-indigo-500/25 border-indigo-400/50 text-indigo-200 hover:bg-indigo-500/45"
                        : "bg-emerald-500/25 border-emerald-500/50 text-emerald-200 hover:bg-emerald-500/45"
                    }`}
                  >
                    {slot.id.split("-")[1]}
                  </button>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
