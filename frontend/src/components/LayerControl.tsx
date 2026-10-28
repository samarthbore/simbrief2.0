"use client";

import React, { useState } from "react";
import { Layers, Check } from "lucide-react";

interface LayerControlProps {
  layers: {
    airports: boolean;
    route: boolean;
    waypoints: boolean;
    atmosphere: boolean;
  };
  onToggleLayer: (layerKey: keyof LayerControlProps["layers"]) => void;
}

export default function LayerControl({ layers, onToggleLayer }: LayerControlProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="absolute top-16 left-[25rem] z-30">
      <button
        onClick={() => setOpen(!open)}
        className="p-2 bg-slate-900/90 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 rounded-lg shadow-lg flex items-center space-x-1.5 text-xs font-medium backdrop-blur-md transition"
        title="Toggle Map Layers"
      >
        <Layers className="w-4 h-4 text-sky-400" />
        <span>Layers</span>
      </button>

      {open && (
        <div className="absolute left-0 mt-2 w-48 bg-slate-900/95 border border-slate-800 rounded-lg shadow-2xl p-2 text-xs text-slate-200 backdrop-blur-md space-y-1 animate-in fade-in duration-100">
          <div className="text-[10px] uppercase font-bold text-slate-500 px-2 py-1">Map Overlays</div>

          <button
            onClick={() => onToggleLayer("airports")}
            className="w-full flex items-center justify-between px-2 py-1.5 rounded hover:bg-slate-800 transition"
          >
            <span>Airport Markers</span>
            <div className={`w-4 h-4 rounded border flex items-center justify-center ${layers.airports ? "bg-sky-600 border-sky-500" : "border-slate-700"}`}>
              {layers.airports && <Check className="w-3 h-3 text-white" />}
            </div>
          </button>

          <button
            onClick={() => onToggleLayer("route")}
            className="w-full flex items-center justify-between px-2 py-1.5 rounded hover:bg-slate-800 transition"
          >
            <span>Flight Route Arc</span>
            <div className={`w-4 h-4 rounded border flex items-center justify-center ${layers.route ? "bg-sky-600 border-sky-500" : "border-slate-700"}`}>
              {layers.route && <Check className="w-3 h-3 text-white" />}
            </div>
          </button>

          <button
            onClick={() => onToggleLayer("waypoints")}
            className="w-full flex items-center justify-between px-2 py-1.5 rounded hover:bg-slate-800 transition"
          >
            <span>Waypoints & Fixes</span>
            <div className={`w-4 h-4 rounded border flex items-center justify-center ${layers.waypoints ? "bg-sky-600 border-sky-500" : "border-slate-700"}`}>
              {layers.waypoints && <Check className="w-3 h-3 text-white" />}
            </div>
          </button>

          <button
            onClick={() => onToggleLayer("atmosphere")}
            className="w-full flex items-center justify-between px-2 py-1.5 rounded hover:bg-slate-800 transition"
          >
            <span>Day / Night Atmosphere</span>
            <div className={`w-4 h-4 rounded border flex items-center justify-center ${layers.atmosphere ? "bg-sky-600 border-sky-500" : "border-slate-700"}`}>
              {layers.atmosphere && <Check className="w-3 h-3 text-white" />}
            </div>
          </button>
        </div>
      )}
    </div>
  );
}
