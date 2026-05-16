import React, { useEffect } from "react";
import { MapContainer, TileLayer, Circle, Polyline, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import type { DashboardState, TrafficView } from "../types";

// Fix Leaflet default icon paths broken by webpack
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl:       "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl:     "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const ISLAMABAD_CENTER: [number, number] = [33.6844, 73.0479];

const rescueIcon = L.divIcon({
  html: `<div style="background:#EA580C;width:14px;height:14px;border-radius:50%;border:2px solid white;"></div>`,
  className: "",
  iconSize: [14, 14],
  iconAnchor: [7, 7],
});

const hospitalIcon = L.divIcon({
  html: `<div style="background:#2563EB;width:14px;height:14px;border-radius:2px;border:2px solid white;font-size:9px;color:white;text-align:center;line-height:11px;">H</div>`,
  className: "",
  iconSize: [14, 14],
  iconAnchor: [7, 7],
});

function RecenterMap({ lat, lng }: { lat: number; lng: number }) {
  const map = useMap();
  useEffect(() => {
    map.setView([lat, lng], 14);
  }, [map, lat, lng]);
  return null;
}

interface Props {
  dashboardState: DashboardState | null;
  trafficView: TrafficView;
}

export default function MapView({ dashboardState, trafficView }: Props) {
  const crisis = dashboardState?.crisis;
  const ops = dashboardState?.operational_picture?.operational_picture;
  const simulation = dashboardState?.simulation?.simulation;

  const crisisLat = crisis?.location.lat ?? ISLAMABAD_CENTER[0];
  const crisisLng = crisis?.location.lng ?? ISLAMABAD_CENTER[1];
  const radiusM = (crisis?.location.affected_radius_km ?? 2.5) * 1000;

  return (
  <div style={{ position: "relative", width: "100%", height: "100%" }}>
    <MapContainer
      center={ISLAMABAD_CENTER}
      zoom={13}
      style={{ width: "100%", height: "100%" }}
      className="z-0"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {crisis && <RecenterMap lat={crisisLat} lng={crisisLng} />}

      {/* Crisis zone polygon */}
      {crisis && (
        <Circle
          center={[crisisLat, crisisLng]}
          radius={radiusM}
          pathOptions={{
            color: "#DC2626",
            fillColor: "#DC2626",
            fillOpacity: 0.15,
            weight: 2,
            dashArray: "6 4",
          }}
        >
          <Popup>
            <strong>{crisis.type.replace(/_/g, " ").toUpperCase()}</strong><br />
            {crisis.location.primary}<br />
            Severity: {crisis.severity}/5 &nbsp;|&nbsp; Confidence: {crisis.confidence}<br />
            <em style={{ fontSize: "11px" }}>{crisis.reasoning}</em>
          </Popup>
        </Circle>
      )}

      {/* Road closures */}
      {ops?.road_closures?.map((rc, i) => (
        rc.status !== "clear" && (
          <Circle
            key={i}
            center={[rc.lat, rc.lng]}
            radius={300}
            pathOptions={{
              color: "#DC2626",
              fillColor: "#DC2626",
              fillOpacity: 0.4,
              weight: 3,
            }}
          >
            <Popup>
              <strong>Road Closure</strong><br />{rc.road}<br />Status: {rc.status}
            </Popup>
          </Circle>
        )
      ))}

      {/* Facilities */}
      {ops?.nearby_facilities?.map((f, i) => (
        <Marker
          key={i}
          position={[f.lat, f.lng]}
          icon={f.type === "hospital" ? hospitalIcon : rescueIcon}
        >
          <Popup>
            <strong>{f.name}</strong><br />
            Type: {f.type}<br />
            Status: {f.status}<br />
            Distance: {f.distance_km} km
          </Popup>
        </Marker>
      ))}

      {/* Unit route (from simulation) */}
      {simulation?.routes?.map((r, i) => (
        r.route.waypoints.length > 1 && (
          <Polyline
            key={i}
            positions={r.route.waypoints}
            pathOptions={{
              color: "#16A34A",
              weight: 4,
              opacity: 0.8,
            }}
          >
            <Popup>
              <strong>{r.unit}</strong><br />
              Via: {r.route.via}<br />
              {r.route.distance_km} km &nbsp;|&nbsp; {r.route.duration_min} min<br />
              <em style={{ fontSize: "11px" }}>{r.route_reasoning}</em>
            </Popup>
          </Polyline>
        )
      ))}

      {/* Traffic state overlay indicator */}
      {simulation && (
        <Circle
          center={[33.6880, 73.0550]}
          radius={500}
          pathOptions={{
            color: trafficView === "before" ? "#DC2626" : "#D97706",
            fillColor: trafficView === "before" ? "#DC2626" : "#D97706",
            fillOpacity: 0.25,
            weight: 2,
          }}
        >
          <Popup>
            Srinagar Highway<br />
            {trafficView === "before"
              ? "BEFORE: Severe congestion"
              : `AFTER: Diverted (-${simulation.traffic_state.congestion_reduction_pct}% congestion)`}
          </Popup>
        </Circle>
      )}
    </MapContainer>

    {simulation?.routes && simulation.routes.length > 0 && (
      <div
        style={{
          position: "absolute",
          bottom: "16px",
          right: "16px",
          zIndex: 1000,
          background: "rgba(15,23,42,0.9)",
          border: "1px solid #334155",
          borderRadius: "6px",
          padding: "8px 12px",
          fontSize: "11px",
          color: "#94A3B8",
          pointerEvents: "none",
        }}
      >
        <div style={{ fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "4px" }}>
          Unit Routes
        </div>
        {simulation.routes.map((r, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: "6px", color: "#F8FAFC" }}>
            <div style={{ width: "16px", height: "3px", background: "#16A34A", borderRadius: "2px" }} />
            {r.unit}
          </div>
        ))}
      </div>
    )}
  </div>
  );
}
