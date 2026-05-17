import React, { useState, useCallback, useEffect, useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import CrisisPanel from "./components/CrisisPanel";
import MapView from "./components/MapView";
import BottomPanel from "./components/BottomPanel";
import { fetchActiveCrises, fetchFullCrisis, triggerDemo } from "./lib/api";
import { useCommandWebSocket } from "./hooks/useWebSocket";
import type { ActiveCrisisSummary, BottomTab, DashboardState, TrafficView } from "./types";

export default function App() {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<BottomTab>("trace");
  const [trafficView, setTrafficView] = useState<TrafficView>("after");
  const [wsStatus, setWsStatus] = useState<"connecting" | "live" | "offline">("connecting");
  const [triggerStatus, setTriggerStatus] = useState<"idle" | "loading" | "ok" | "error">("idle");
  const [triggerError, setTriggerError] = useState<string | null>(null);
  const triggerTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const { data: crises = [], isError: crisesError } = useQuery<ActiveCrisisSummary[]>({
    queryKey: ["activeCrises"],
    queryFn: fetchActiveCrises,
    refetchInterval: 30000,
    retry: false,
  });

  useEffect(() => {
    if (crisesError) setWsStatus("offline");
  }, [crisesError]);

  const { data: dashboardState = null } = useQuery<DashboardState | null>({
    queryKey: ["crisis", selectedId],
    queryFn: () => (selectedId ? fetchFullCrisis(selectedId) : Promise.resolve(null)),
    enabled: !!selectedId,
  });

  const handleWsMessage = useCallback(
    (data: unknown) => {
      setWsStatus("live");
      const msg = data as { crisis_id?: string; stage?: string };
      if (msg.crisis_id) {
        queryClient.invalidateQueries({ queryKey: ["activeCrises"] });
        queryClient.invalidateQueries({ queryKey: ["crisis", msg.crisis_id] });
        if (!selectedId) setSelectedId(msg.crisis_id);
      }
    },
    [queryClient, selectedId]
  );

  useCommandWebSocket(handleWsMessage, useCallback(() => setWsStatus("live"), []));

  const handleTriggerDemo = useCallback(async () => {
    if (triggerStatus === "loading") return;
    if (triggerTimer.current) clearTimeout(triggerTimer.current);
    setTriggerStatus("loading");
    setTriggerError(null);
    try {
      await triggerDemo();
      setTriggerStatus("ok");
      triggerTimer.current = setTimeout(() => setTriggerStatus("idle"), 3000);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setTriggerStatus("error");
      setTriggerError(msg);
      triggerTimer.current = setTimeout(() => setTriggerStatus("idle"), 5000);
    }
  }, [triggerStatus]);

  const handleSelectCrisis = useCallback((id: string) => {
    setSelectedId(id);
    setActiveTab("trace");
  }, []);

  return (
    <div className="h-screen w-screen bg-bg text-text-primary flex flex-col overflow-hidden">
      {/* Top bar */}
      <header className="h-10 bg-surface border-b border-border flex items-center px-4 shrink-0 z-10">
        <span className="font-bold text-sm tracking-wide mr-4">CIRO</span>
        <span className="text-text-secondary text-xs mr-4">Crisis Command Dashboard</span>
        <div className="ml-auto flex items-center gap-3 text-xs">
          {selectedId && (
            <div className="flex items-center gap-2 bg-bg rounded px-2 py-1">
              <span className="text-text-secondary">Traffic:</span>
              <button
                onClick={() => setTrafficView("before")}
                className={`px-2 py-0.5 rounded text-xs ${trafficView === "before" ? "bg-critical text-white" : "text-text-secondary hover:text-text-primary"}`}
              >
                Before
              </button>
              <button
                onClick={() => setTrafficView("after")}
                className={`px-2 py-0.5 rounded text-xs ${trafficView === "after" ? "bg-safe text-white" : "text-text-secondary hover:text-text-primary"}`}
              >
                After
              </button>
            </div>
          )}
          <span
            className={`flex items-center gap-1 font-semibold ${
              wsStatus === "live" ? "text-safe" : wsStatus === "offline" ? "text-critical" : "text-warning"
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                wsStatus === "live" ? "bg-safe animate-pulse" : wsStatus === "offline" ? "bg-critical" : "bg-warning animate-pulse"
              }`}
            />
            {wsStatus === "live" ? "LIVE" : wsStatus === "offline" ? "OFFLINE" : "CONNECTING"}
          </span>
        </div>
      </header>

      {/* Main: sidebar + map + bottom panel */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: crisis list */}
        <CrisisPanel
          crises={crises}
          selectedId={selectedId}
          onSelect={handleSelectCrisis}
          onTriggerDemo={handleTriggerDemo}
          triggerStatus={triggerStatus}
          triggerError={triggerError}
        />

        {/* Center + bottom */}
        <div className="flex flex-col flex-1 overflow-hidden">
          {/* Map */}
          <div className="flex-1 relative">
            <MapView dashboardState={dashboardState} trafficView={trafficView} />

            {/* Backend offline banner */}
            {wsStatus === "offline" && (
              <div className="absolute top-2 left-1/2 -translate-x-1/2 bg-critical text-white text-xs px-3 py-1.5 rounded shadow-lg z-10">
                Backend offline — check connection
              </div>
            )}
          </div>

          {/* Bottom panel */}
          <div className="h-48 shrink-0">
            <BottomPanel
              activeTab={activeTab}
              onTabChange={setActiveTab}
              dashboardState={dashboardState}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
