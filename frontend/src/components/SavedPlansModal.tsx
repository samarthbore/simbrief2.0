"use client";

import React, { useEffect, useState } from "react";
import { FlightPlan, AirportSummary } from "@/types";
import { listFlightPlans, getBriefingDownloadUrl, planFlightRoute } from "@/lib/api";
import { X, FileDown, Bookmark, Calendar, Plane, History } from "lucide-react";

interface SavedPlansModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLoadPlan: (plan: FlightPlan) => void;
}

export default function SavedPlansModal({
  isOpen,
  onClose,
  onLoadPlan,
}: SavedPlansModalProps) {
  const [plans, setPlans] = useState<FlightPlan[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    setError(null);
    listFlightPlans()
      .then((data) => setPlans(data))
      .catch((err) => setError(err.message || "Failed to load saved plans"))
      .finally(() => setLoading(false));
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-aviation-border rounded-xl shadow-2xl w-full max-w-2xl max-h-[85vh] flex flex-col text-aviation-text animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
          <div className="flex items-center space-x-2.5">
            <Bookmark className="w-5 h-5 text-amber-400" />
            <h2 className="text-base font-semibold text-white">Saved Flight Plans & OFP Briefings</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content list */}
        <div className="p-6 overflow-y-auto space-y-3 flex-1">
          {loading ? (
            <div className="text-center py-12 text-slate-400 text-sm">Loading saved flight plans...</div>
          ) : error ? (
            <div className="text-center py-12 text-red-400 text-sm">{error}</div>
          ) : plans.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-sm">
              No saved flight plans found. Create and save a flight plan from the planning panel.
            </div>
          ) : (
            plans.map((p) => (
              <div
                key={p.id}
                className="bg-slate-950/70 border border-slate-800 rounded-lg p-4 hover:border-slate-700 transition flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-mono font-bold text-sm text-sky-400">{p.plan_code}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {p.departure_ident} ➔ {p.destination_ident}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded bg-slate-800/80 text-amber-300 font-mono">
                      {p.aircraft_profile?.identifier || "A320"}
                    </span>
                  </div>

                  <h4 className="text-sm font-medium text-white mt-1">{p.title}</h4>

                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-xs text-slate-400">
                    <span><b>{Math.round(p.total_distance_nm)}</b> NM</span>
                    <span><b>{Math.round(p.estimated_flight_time_min)}</b> min ETE</span>
                    <span><b>{Math.round(p.estimated_fuel_burn_kg)}</b> kg fuel</span>
                    <span className="flex items-center space-x-1">
                      <History className="w-3 h-3 text-slate-500" />
                      <span>Rev {p.revisions?.length ?? 1}</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <Calendar className="w-3 h-3 text-slate-500" />
                      <span>{new Date(p.created_at).toLocaleDateString()}</span>
                    </span>
                  </div>
                </div>

                <div className="flex items-center space-x-2 shrink-0">
                  <button
                    onClick={() => {
                      onLoadPlan(p);
                      onClose();
                    }}
                    className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-xs font-medium text-white transition"
                  >
                    Load Route
                  </button>
                  <a
                    href={getBriefingDownloadUrl(p.plan_code)}
                    target="_blank"
                    rel="noreferrer"
                    className="px-3 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 text-xs font-medium text-white transition flex items-center space-x-1"
                  >
                    <FileDown className="w-3.5 h-3.5" />
                    <span>PDF</span>
                  </a>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
