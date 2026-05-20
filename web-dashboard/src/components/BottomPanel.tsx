import React from "react";
import ReactMarkdown from "react-markdown";
import type { DashboardState, BottomTab, AgentTraceSummary } from "../types";

interface Props {
  activeTab: BottomTab;
  onTabChange: (tab: BottomTab) => void;
  dashboardState: DashboardState | null;
}

const TABS: { id: BottomTab; label: string }[] = [
  { id: "trace",     label: "Agent Trace" },
  { id: "dispatch",  label: "Dispatch Orders" },
  { id: "resources", label: "Resource Status" },
  { id: "sitrep",    label: "SITREP" },
];

const STAGE_COLORS: Record<string, string> = {
  TOOL_CALL: "text-info",
  DECISION:  "text-warning",
  OUTPUT:    "text-safe",
  ACTION:    "text-high",
  START:     "text-text-secondary",
  END:       "text-text-secondary",
  PROCESS:   "text-text-secondary",
  RESULT:    "text-text-primary",
};

function TraceTab({ traces }: { traces: AgentTraceSummary[] }) {
  if (!traces || traces.length === 0) {
    return (
      <div className="text-text-secondary text-sm p-4">
        Waiting for agent pipeline to start...
      </div>
    );
  }
  return (
    <div className="font-mono text-xs space-y-0.5 p-2">
      {traces.map((t, i) => {
        const stage = t.key_decision.includes("|") ? t.key_decision.split("|")[1]?.trim() : "INFO";
        return (
          <div key={i} className="flex gap-2">
            <span className="text-text-secondary shrink-0">
              {new Date(t.timestamp).toLocaleTimeString("en-GB")}
            </span>
            <span className="text-info shrink-0">{t.agent}</span>
            <span className={STAGE_COLORS[stage] || "text-text-primary"}>▸ {t.key_decision}</span>
          </div>
        );
      })}
    </div>
  );
}

function DispatchTab({ dashboardState }: { dashboardState: DashboardState | null }) {
  const orders = dashboardState?.dispatch_plan?.dispatch_plan?.dispatch_orders ?? [];
  if (orders.length === 0) {
    return <div className="text-text-secondary text-sm p-4">No dispatch orders yet.</div>;
  }
  return (
    <table className="w-full text-xs">
      <thead>
        <tr className="border-b border-border text-text-secondary text-left">
          <th className="p-2 font-semibold">Unit</th>
          <th className="p-2 font-semibold">Type</th>
          <th className="p-2 font-semibold">Destination</th>
          <th className="p-2 font-semibold">ETA</th>
          <th className="p-2 font-semibold">Reason</th>
        </tr>
      </thead>
      <tbody>
        {orders.map((o) => (
          <tr key={o.order_id} className="border-b border-border hover:bg-bg">
            <td className="p-2 text-text-primary font-medium">{o.unit}</td>
            <td className="p-2 text-info">{o.unit_type.replace("_", " ")}</td>
            <td className="p-2 text-text-secondary">{o.destination}</td>
            <td className="p-2 text-warning">{o.eta_minutes} min</td>
            <td className="p-2 text-text-secondary max-w-xs truncate" title={o.reason}>{o.reason}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function ResourceTab({ dashboardState }: { dashboardState: DashboardState | null }) {
  const gaps = dashboardState?.dispatch_plan?.dispatch_plan?.resource_gaps ?? [];
  const orders = dashboardState?.dispatch_plan?.dispatch_plan?.dispatch_orders ?? [];

  return (
    <div className="p-3 space-y-4 text-xs">
      {orders.length > 0 && (
        <div>
          <div className="text-text-secondary font-semibold uppercase tracking-wider mb-1">Deployed Units</div>
          {orders.map((o) => (
            <div key={o.order_id} className="flex justify-between py-1 border-b border-border">
              <span className="text-text-primary">{o.unit}</span>
              <span className="text-warning font-medium">En Route → {o.destination}</span>
            </div>
          ))}
        </div>
      )}
      {gaps.length > 0 && (
        <div>
          <div className="text-text-secondary font-semibold uppercase tracking-wider mb-1">Resource Gaps</div>
          {gaps.map((g, i) => (
            <div key={i} className="flex justify-between py-1 border-b border-border">
              <span className="text-text-primary">{g.item}</span>
              <span className="text-critical">Required: {g.required} / Available: {g.available} (Gap: {g.gap})</span>
            </div>
          ))}
        </div>
      )}
      {orders.length === 0 && gaps.length === 0 && (
        <div className="text-text-secondary">No resource data yet.</div>
      )}
    </div>
  );
}

function SitrepTab({ sitrep }: { sitrep: string }) {
  if (!sitrep) {
    return <div className="text-text-secondary text-sm p-4">SITREP will appear here after Agent 6 completes.</div>;
  }
  return (
    <div className="p-4 text-xs text-text-primary leading-relaxed prose prose-invert prose-xs max-w-none
      [&_h1]:text-sm [&_h1]:font-bold [&_h1]:text-text-primary [&_h1]:mb-2 [&_h1]:mt-3
      [&_h2]:text-xs [&_h2]:font-bold [&_h2]:text-info [&_h2]:mb-1 [&_h2]:mt-2 [&_h2]:uppercase [&_h2]:tracking-wider
      [&_p]:mb-2 [&_p]:text-text-primary
      [&_ul]:pl-4 [&_ul]:mb-2 [&_li]:mb-0.5 [&_li]:text-text-secondary
      [&_strong]:text-text-primary [&_strong]:font-semibold
      [&_hr]:border-border [&_hr]:my-3
      [&_code]:text-warning [&_code]:bg-bg [&_code]:px-1 [&_code]:rounded">
      <ReactMarkdown>{sitrep}</ReactMarkdown>
    </div>
  );
}

export default function BottomPanel({ activeTab, onTabChange, dashboardState }: Props) {
  return (
    <div className="h-full flex flex-col bg-surface border-t border-border">
      {/* Tab bar */}
      <div className="flex border-b border-border shrink-0">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`px-4 py-2 text-xs font-semibold border-r border-border transition-colors ${
              activeTab === tab.id
                ? "text-text-primary bg-bg border-t-2 border-t-info"
                : "text-text-secondary hover:text-text-primary hover:bg-bg"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === "trace" && (
          <TraceTab traces={dashboardState?.agent_trace_summary ?? []} />
        )}
        {activeTab === "dispatch" && <DispatchTab dashboardState={dashboardState} />}
        {activeTab === "resources" && <ResourceTab dashboardState={dashboardState} />}
        {activeTab === "sitrep" && <SitrepTab sitrep={dashboardState?.sitrep_text ?? ""} />}
      </div>
    </div>
  );
}
