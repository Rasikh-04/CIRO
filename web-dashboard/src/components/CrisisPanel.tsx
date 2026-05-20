import React from "react";
import type { ActiveCrisisSummary, CrisisStage } from "../types";

interface Props {
  crises: ActiveCrisisSummary[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onTriggerDemo: () => void;
  triggerStatus: "idle" | "loading" | "ok" | "error";
  triggerError: string | null;
}

const STAGE_LABELS: Record<CrisisStage, string> = {
  detected:   "Detected",
  analyzed:   "Analyzed",
  dispatched: "Dispatched",
  simulated:  "Simulated",
  resolved:   "Resolved",
};

const STAGE_DOT: Record<CrisisStage, string> = {
  detected:   "bg-critical animate-pulse",
  analyzed:   "bg-high animate-pulse",
  dispatched: "bg-warning animate-pulse",
  simulated:  "bg-info",
  resolved:   "bg-safe",
};

const SEVERITY_COLOR: Record<number, string> = {
  1: "bg-safe text-white",
  2: "bg-info text-white",
  3: "bg-warning text-white",
  4: "bg-high text-white",
  5: "bg-critical text-white",
};

function timeAgo(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

export default function CrisisPanel({ crises, selectedId, onSelect, onTriggerDemo, triggerStatus, triggerError }: Props) {
  const buttonLabel =
    triggerStatus === "loading" ? "Triggering…" :
    triggerStatus === "ok"      ? "✓ Triggered" :
    triggerStatus === "error"   ? "✗ Failed" :
    "▶ Trigger Demo";

  const buttonClass =
    triggerStatus === "loading" ? "bg-warning cursor-not-allowed opacity-70" :
    triggerStatus === "ok"      ? "bg-safe" :
    triggerStatus === "error"   ? "bg-critical" :
    "bg-critical hover:bg-red-700";

  return (
    <aside className="w-64 min-w-[16rem] bg-surface border-r border-border flex flex-col h-full">
      <div className="p-3 border-b border-border flex items-center justify-between">
        <span className="text-text-secondary text-xs font-semibold uppercase tracking-widest">
          Active Crises
        </span>
        <span className="text-xs bg-critical text-white rounded-full px-2 py-0.5 font-bold">
          {crises.length}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto">
        {crises.length === 0 ? (
          <div className="p-4 text-text-secondary text-sm text-center mt-4">
            No active crises.<br />
            <span className="text-xs">Waiting for signal ingestion.</span>
          </div>
        ) : (
          crises.map((c) => (
            <button
              key={c.crisis_id}
              onClick={() => onSelect(c.crisis_id)}
              className={`w-full text-left p-3 border-b border-border hover:bg-bg transition-colors ${
                selectedId === c.crisis_id ? "bg-bg border-l-2 border-l-critical" : ""
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-text-primary text-sm font-semibold truncate">
                  {c.type.replace("_", " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                </span>
                <span className={`text-xs rounded px-1.5 py-0.5 font-bold ${SEVERITY_COLOR[c.severity] || "bg-surface"}`}>
                  {c.severity}/5
                </span>
              </div>
              <div className="text-text-secondary text-xs mb-1.5">{c.location_name}</div>
              <div className="flex items-center gap-1.5">
                <span className={`inline-block w-2 h-2 rounded-full ${STAGE_DOT[c.stage]}`} />
                <span className="text-text-secondary text-xs">{STAGE_LABELS[c.stage]}</span>
                <span className="text-text-secondary text-xs ml-auto">{timeAgo(c.detected_at)}</span>
              </div>
            </button>
          ))
        )}
      </div>

      <div className="p-3 border-t border-border">
        <button
          onClick={onTriggerDemo}
          disabled={triggerStatus === "loading"}
          className={`w-full py-2 px-3 text-white text-sm font-semibold rounded transition-colors ${buttonClass}`}
        >
          {buttonLabel}
        </button>
        {triggerStatus === "error" && triggerError && (
          <p className="text-critical text-xs text-center mt-1.5 break-all">{triggerError}</p>
        )}
        {triggerStatus !== "error" && (
          <p className="text-text-secondary text-xs text-center mt-1.5">
            Runs G-10 flood scenario
          </p>
        )}
      </div>
    </aside>
  );
}
