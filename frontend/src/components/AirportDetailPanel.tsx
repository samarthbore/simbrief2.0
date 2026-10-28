"use client";

import React, { useEffect, useState } from "react";
import { AirportSummary, AirportDetail } from "@/types";
import { getAirportDetail } from "@/lib/api";
import { X, Navigation, Building2, MapPin, Compass, ArrowUpRight } from "lucide-react";

interface AirportDetailPanelProps {
  airport: AirportSummary | null;
  onClose: () => void;
  onSetDeparture: (airport: AirportSummary) => void;
  onSetDestination: (airport: AirportSummary) => void;
  onZoom: (airport: AirportSummary) => void;
}

export default function AirportDetailPanel({
  airport,
  onClose,
  onSetDeparture,
  onSetDestination,
  onZoom,
}: AirportDetailPanelProps) {
  const [detail, setDetail] = useState<AirportDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!airport) {
      setDetail(null);
      return;
    }
    setLoading(true);
    getAirportDetail(airport.ident)
      .then((data) => setDetail(data))
      .catch(() => setDetail(null))
      .finally(() => setLoading(false));
  }, [airport]);

  if (!airport) return null;

  return (
    <div className="absolute top-16 right-4 z-40 w-80 bg-slate-900/95 backdrop-blur-md border border-aviation-border rounded-lg shadow-2xl p-4 text-aviation-text animate-in fade-in slide-in-from-right-4 duration-200">
      {/* Header */}
      <div className="flex items-start justify-between pb-3 border-b border-slate-800">
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-bold text-lg text-white font-mono">{airport.ident}</span>
            {airport.iata && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-slate-800 text-sky-400 font-mono font-medium">
                {airport.iata}
              </span>
            )}
            {airport.icao && airport.icao !== airport.ident && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                {airport.icao}
              </span>
            )}
          </div>
          <h3 className="text-xs text-slate-300 font-medium mt-0.5 line-clamp-1">{airport.name}</h3>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Core Location Metrics */}
      <div className="py-3 space-y-2 text-xs border-b border-slate-800">
        <div className="flex items-center space-x-2 text-slate-300">
          <MapPin className="w-3.5 h-3.5 text-sky-400 shrink-0" />
          <span>{airport.municipality || "Unknown Municipality"}, {airport.iso_country}</span>
        </div>
        <div className="flex items-center space-x-2 text-slate-300">
          <Compass className="w-3.5 h-3.5 text-amber-400 shrink-0" />
          <span className="font-mono">
            {airport.latitude.toFixed(4)}°, {airport.longitude.toFixed(4)}°
          </span>
        </div>
        <div className="flex items-center space-x-2 text-slate-300">
          <Building2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
          <span>Elevation: <b>{airport.elevation_ft ?? "N/A"} ft</b> MSL</span>
        </div>
      </div>

      {/* Runways Section */}
      <div className="py-3 border-b border-slate-800">
        <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
          Runways ({detail?.runways?.length ?? 0})
        </div>

        {loading ? (
          <div className="text-xs text-slate-500 py-2">Loading runway geometry...</div>
        ) : detail?.runways && detail.runways.length > 0 ? (
          <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
            {detail.runways.map((r) => (
              <div
                key={r.id}
                className="bg-slate-950/70 p-2 rounded border border-slate-800/80 text-[11px] flex justify-between items-center"
              >
                <div>
                  <span className="font-bold text-white font-mono">
                    RWY {r.le_ident || "??"} / {r.he_ident || "??"}
                  </span>
                  <div className="text-[10px] text-slate-400">
                    {r.surface || "Paved"} {r.lighted ? "• Lighted" : ""}
                  </div>
                </div>
                <div className="text-right font-mono text-[11px] text-sky-300">
                  {r.length_ft ? `${Math.round(r.length_ft)} ft` : ""}
                  {r.width_ft ? ` × ${Math.round(r.width_ft)}` : ""}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-xs text-slate-500">No runway details recorded</div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="pt-3 grid grid-cols-2 gap-2">
        <button
          onClick={() => onSetDeparture(airport)}
          className="py-1.5 px-2 rounded bg-emerald-700/80 hover:bg-emerald-600 text-white text-xs font-medium transition text-center"
        >
          Set Departure
        </button>
        <button
          onClick={() => onSetDestination(airport)}
          className="py-1.5 px-2 rounded bg-sky-700/80 hover:bg-sky-600 text-white text-xs font-medium transition text-center"
        >
          Set Destination
        </button>
        <button
          onClick={() => onZoom(airport)}
          className="col-span-2 py-1.5 px-2 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-medium transition flex items-center justify-center space-x-1"
        >
          <Navigation className="w-3.5 h-3.5 text-sky-400" />
          <span>Center Camera on Airport</span>
        </button>
      </div>
    </div>
  );
}
