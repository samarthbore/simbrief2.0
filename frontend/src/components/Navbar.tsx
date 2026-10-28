"use client";

import React from "react";
import { Globe, Bookmark, Compass, Info } from "lucide-react";

interface NavbarProps {
  appTitle?: string;
  onResetGlobal: () => void;
  onOpenSavedPlans: () => void;
  backendOnline: boolean;
}

export default function Navbar({
  appTitle = "Aviation Flight Planner",
  onResetGlobal,
  onOpenSavedPlans,
  backendOnline,
}: NavbarProps) {
  return (
    <header className="h-12 bg-slate-950/95 border-b border-aviation-border px-4 flex items-center justify-between z-30 select-none">
      {/* Brand title */}
      <div className="flex items-center space-x-3">
        <div className="w-7 h-7 rounded bg-sky-600/20 border border-sky-500/30 flex items-center justify-center">
          <Compass className="w-4 h-4 text-sky-400" />
        </div>
        <div>
          <h1 className="text-sm font-semibold tracking-wide text-white uppercase">{appTitle}</h1>
          <div className="text-[10px] text-slate-400 -mt-0.5">Global 3D Flight Operations & Dispatch</div>
        </div>
      </div>

      {/* Center status badge */}
      <div className="hidden md:flex items-center space-x-2 text-xs">
        <div className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-slate-900 border border-slate-800">
          <span className={`w-2 h-2 rounded-full ${backendOnline ? "bg-emerald-500 animate-pulse" : "bg-red-500"}`} />
          <span className="text-[11px] text-slate-300">
            {backendOnline ? "Engine Online" : "Backend Offline"}
          </span>
        </div>
        <div className="text-[11px] text-slate-500">
          Open Datasets: OurAirports (CC0) • Natural Earth (Public Domain)
        </div>
      </div>

      {/* Right controls */}
      <div className="flex items-center space-x-2">
        <button
          onClick={onResetGlobal}
          className="px-2.5 py-1.5 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 text-xs font-medium flex items-center space-x-1.5 transition"
          title="Return to global 3D Earth view"
        >
          <Globe className="w-3.5 h-3.5 text-sky-400" />
          <span className="hidden sm:inline">Global View</span>
        </button>

        <button
          onClick={onOpenSavedPlans}
          className="px-2.5 py-1.5 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 text-xs font-medium flex items-center space-x-1.5 transition"
        >
          <Bookmark className="w-3.5 h-3.5 text-amber-400" />
          <span>Saved Plans</span>
        </button>
      </div>
    </header>
  );
}
