"use client";

import React, { useState, useEffect } from "react";
import {
  AirportSummary,
  AircraftProfile,
  RoutePlanResponse,
} from "@/types";
import { searchAirports, planFlightRoute, createFlightPlan, getBriefingDownloadUrl } from "@/lib/api";
import {
  Plane,
  ArrowRightLeft,
  Search,
  Fuel,
  Clock,
  Navigation,
  FileDown,
  Bookmark,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  RotateCcw,
} from "lucide-react";

interface FlightPlanPanelProps {
  airports: AirportSummary[];
  aircraftProfiles: AircraftProfile[];
  departureAirport: AirportSummary | null;
  destinationAirport: AirportSummary | null;
  onSetDeparture: (airport: AirportSummary | null) => void;
  onSetDestination: (airport: AirportSummary | null) => void;
  routePlan: RoutePlanResponse | null;
  onSetRoutePlan: (plan: RoutePlanResponse | null) => void;
  onZoomToAirport: (airport: AirportSummary) => void;
  onPlanSaved: () => void;
}

export default function FlightPlanPanel({
  aircraftProfiles,
  departureAirport,
  destinationAirport,
  onSetDeparture,
  onSetDestination,
  routePlan,
  onSetRoutePlan,
  onZoomToAirport,
  onPlanSaved,
}: FlightPlanPanelProps) {
  const [depQuery, setDepQuery] = useState("");
  const [destQuery, setDestQuery] = useState("");
  const [depSuggestions, setDepSuggestions] = useState<AirportSummary[]>([]);
  const [destSuggestions, setDestSuggestions] = useState<AirportSummary[]>([]);
  const [showDepDropdown, setShowDepDropdown] = useState(false);
  const [showDestDropdown, setShowDestDropdown] = useState(false);

  const [selectedAircraft, setSelectedAircraft] = useState<string>("A320");
  const [routingObjective, setRoutingObjective] = useState<string>("great_circle");
  const [cruiseAlt, setCruiseAlt] = useState<number>(36000);

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showAssumptions, setShowAssumptions] = useState(false);
  const [savedPlanCode, setSavedPlanCode] = useState<string | null>(null);

  // Sync inputs when departure or destination changes from external selection (e.g. clicking globe)
  useEffect(() => {
    if (departureAirport) {
      setDepQuery(`${departureAirport.ident} - ${departureAirport.name}`);
    }
  }, [departureAirport]);

  useEffect(() => {
    if (destinationAirport) {
      setDestQuery(`${destinationAirport.ident} - ${destinationAirport.name}`);
    }
  }, [destinationAirport]);

  // Debounced search for departure
  useEffect(() => {
    if (!depQuery || (departureAirport && depQuery.startsWith(departureAirport.ident))) {
      setDepSuggestions([]);
      return;
    }
    const timer = setTimeout(() => {
      searchAirports(depQuery, 6).then((res) => setDepSuggestions(res.items)).catch(() => {});
    }, 250);
    return () => clearTimeout(timer);
  }, [depQuery, departureAirport]);

  // Debounced search for destination
  useEffect(() => {
    if (!destQuery || (destinationAirport && destQuery.startsWith(destinationAirport.ident))) {
      setDestSuggestions([]);
      return;
    }
    const timer = setTimeout(() => {
      searchAirports(destQuery, 6).then((res) => setDestSuggestions(res.items)).catch(() => {});
    }, 250);
    return () => clearTimeout(timer);
  }, [destQuery, destinationAirport]);

  const handleSwapAirports = () => {
    const temp = departureAirport;
    onSetDeparture(destinationAirport);
    onSetDestination(temp);
  };

  const handleCalculateRoute = async () => {
    if (!departureAirport || !destinationAirport) {
      setErrorMessage("Please select both a departure and destination airport.");
      return;
    }
    if (departureAirport.ident === destinationAirport.ident) {
      setErrorMessage("Departure and destination airports cannot be identical.");
      return;
    }

    setLoading(true);
    setErrorMessage(null);
    setSavedPlanCode(null);

    try {
      const planRes = await planFlightRoute({
        departure_ident: departureAirport.ident,
        destination_ident: destinationAirport.ident,
        aircraft_profile_ident: selectedAircraft,
        routing_objective: routingObjective,
      });
      onSetRoutePlan(planRes);
    } catch (err: any) {
      setErrorMessage(err.message || "Route calculation failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleSavePlan = async () => {
    if (!departureAirport || !destinationAirport || !routePlan) return;
    setSaving(true);
    try {
      const res = await createFlightPlan({
        departure_ident: departureAirport.ident,
        destination_ident: destinationAirport.ident,
        aircraft_id: selectedAircraft,
        routing_objective: routingObjective,
        cruise_altitude_ft: cruiseAlt,
      });
      setSavedPlanCode(res.plan_code);
      onPlanSaved();
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to save flight plan.");
    } finally {
      setSaving(false);
    }
  };

  const handleClear = () => {
    onSetDeparture(null);
    onSetDestination(null);
    onSetRoutePlan(null);
    setDepQuery("");
    setDestQuery("");
    setErrorMessage(null);
    setSavedPlanCode(null);
  };

  return (
    <div className="flex flex-col h-full bg-aviation-panel/95 backdrop-blur-md border-r border-aviation-border text-aviation-text w-96 p-4 shadow-2xl overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-aviation-border">
        <div className="flex items-center space-x-2">
          <Plane className="w-5 h-5 text-aviation-accent" />
          <h2 className="font-semibold text-sm tracking-wide uppercase">Flight Dispatch & Planning</h2>
        </div>
        {(departureAirport || destinationAirport || routePlan) && (
          <button
            onClick={handleClear}
            className="text-xs text-aviation-muted hover:text-aviation-text flex items-center space-x-1"
            title="Reset form"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>
        )}
      </div>

      {/* Error Alert */}
      {errorMessage && (
        <div className="mt-3 p-2.5 rounded bg-aviation-danger/15 border border-aviation-danger/40 text-xs text-red-300 flex items-start space-x-2">
          <AlertCircle className="w-4 h-4 text-aviation-danger shrink-0 mt-0.5" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Airport Selection Section */}
      <div className="mt-4 space-y-3">
        {/* Departure Input */}
        <div className="relative">
          <label className="text-xs font-medium text-aviation-muted mb-1 block">Departure Airport (Origin)</label>
          <div className="relative flex items-center">
            <input
              type="text"
              placeholder="Search ICAO, IATA, or City..."
              value={depQuery}
              onChange={(e) => {
                setDepQuery(e.target.value);
                setShowDepDropdown(true);
              }}
              onFocus={() => setShowDepDropdown(true)}
              className="w-full bg-slate-900/90 border border-aviation-border rounded px-3 py-2 text-xs focus:outline-none focus:border-aviation-accent text-white placeholder-slate-500"
            />
            <Search className="w-4 h-4 text-slate-500 absolute right-3 pointer-events-none" />
          </div>

          {/* Autocomplete Dropdown */}
          {showDepDropdown && depSuggestions.length > 0 && (
            <div className="absolute z-50 left-0 right-0 mt-1 bg-slate-900 border border-aviation-border rounded shadow-xl max-h-48 overflow-y-auto">
              {depSuggestions.map((a) => (
                <div
                  key={a.id}
                  onClick={() => {
                    onSetDeparture(a);
                    setDepQuery(`${a.ident} - ${a.name}`);
                    setShowDepDropdown(false);
                    onZoomToAirport(a);
                  }}
                  className="px-3 py-2 text-xs hover:bg-aviation-accent/20 cursor-pointer border-b border-slate-800/60 last:border-0"
                >
                  <div className="font-semibold text-white flex justify-between">
                    <span>{a.ident} {a.iata ? `(${a.iata})` : ""}</span>
                    <span className="text-[10px] text-slate-400">{a.iso_country}</span>
                  </div>
                  <div className="text-slate-400 truncate">{a.name}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Swap Airports Button */}
        <div className="flex justify-center -my-1">
          <button
            onClick={handleSwapAirports}
            disabled={!departureAirport && !destinationAirport}
            className="p-1.5 rounded-full bg-slate-800 hover:bg-slate-700 text-aviation-muted hover:text-white transition disabled:opacity-30"
            title="Swap Origin and Destination"
          >
            <ArrowRightLeft className="w-3.5 h-3.5 rotate-90" />
          </button>
        </div>

        {/* Destination Input */}
        <div className="relative">
          <label className="text-xs font-medium text-aviation-muted mb-1 block">Destination Airport</label>
          <div className="relative flex items-center">
            <input
              type="text"
              placeholder="Search ICAO, IATA, or City..."
              value={destQuery}
              onChange={(e) => {
                setDestQuery(e.target.value);
                setShowDestDropdown(true);
              }}
              onFocus={() => setShowDestDropdown(true)}
              className="w-full bg-slate-900/90 border border-aviation-border rounded px-3 py-2 text-xs focus:outline-none focus:border-aviation-accent text-white placeholder-slate-500"
            />
            <Search className="w-4 h-4 text-slate-500 absolute right-3 pointer-events-none" />
          </div>

          {/* Autocomplete Dropdown */}
          {showDestDropdown && destSuggestions.length > 0 && (
            <div className="absolute z-50 left-0 right-0 mt-1 bg-slate-900 border border-aviation-border rounded shadow-xl max-h-48 overflow-y-auto">
              {destSuggestions.map((a) => (
                <div
                  key={a.id}
                  onClick={() => {
                    onSetDestination(a);
                    setDestQuery(`${a.ident} - ${a.name}`);
                    setShowDestDropdown(false);
                    onZoomToAirport(a);
                  }}
                  className="px-3 py-2 text-xs hover:bg-aviation-accent/20 cursor-pointer border-b border-slate-800/60 last:border-0"
                >
                  <div className="font-semibold text-white flex justify-between">
                    <span>{a.ident} {a.iata ? `(${a.iata})` : ""}</span>
                    <span className="text-[10px] text-slate-400">{a.iso_country}</span>
                  </div>
                  <div className="text-slate-400 truncate">{a.name}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Aircraft and Parameters */}
      <div className="mt-4 pt-3 border-t border-aviation-border space-y-3">
        <div>
          <label className="text-xs font-medium text-aviation-muted mb-1 block">Aircraft Profile</label>
          <select
            value={selectedAircraft}
            onChange={(e) => setSelectedAircraft(e.target.value)}
            className="w-full bg-slate-900 border border-aviation-border rounded px-2.5 py-2 text-xs text-white focus:outline-none focus:border-aviation-accent"
          >
            {aircraftProfiles.map((ac) => (
              <option key={ac.id} value={ac.identifier}>
                {ac.identifier} — {ac.name} ({ac.cruise_speed_kts} kts)
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="text-xs font-medium text-aviation-muted mb-1 block">Routing Objective</label>
            <select
              value={routingObjective}
              onChange={(e) => setRoutingObjective(e.target.value)}
              className="w-full bg-slate-900 border border-aviation-border rounded px-2 py-1.5 text-xs text-white focus:outline-none focus:border-aviation-accent"
            >
              <option value="great_circle">Direct (Great Circle)</option>
              <option value="shortest_distance">Shortest Distance</option>
              <option value="lowest_time">Lowest Flight Time</option>
              <option value="lowest_fuel">Lowest Fuel Burn</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-medium text-aviation-muted mb-1 block">Cruise Altitude</label>
            <select
              value={cruiseAlt}
              onChange={(e) => setCruiseAlt(Number(e.target.value))}
              className="w-full bg-slate-900 border border-aviation-border rounded px-2 py-1.5 text-xs text-white focus:outline-none focus:border-aviation-accent"
            >
              <option value={10000}>FL100 (10,000 ft)</option>
              <option value={24000}>FL240 (24,000 ft)</option>
              <option value={32000}>FL320 (32,000 ft)</option>
              <option value={36000}>FL360 (36,000 ft)</option>
              <option value={40000}>FL400 (40,000 ft)</option>
            </select>
          </div>
        </div>

        {/* Calculate Route CTA */}
        <button
          onClick={handleCalculateRoute}
          disabled={loading || !departureAirport || !destinationAirport}
          className="w-full py-2.5 rounded font-medium text-xs bg-aviation-accent hover:bg-aviation-accentHover text-white transition flex items-center justify-center space-x-2 disabled:opacity-50 shadow-lg shadow-sky-900/30"
        >
          {loading ? (
            <span>Computing Navigation Arc...</span>
          ) : (
            <>
              <Navigation className="w-4 h-4" />
              <span>Compute Flight Plan</span>
            </>
          )}
        </button>
      </div>

      {/* Route Calculation Summary & Results */}
      {routePlan && (
        <div className="mt-4 pt-4 border-t border-aviation-border space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-sky-400 uppercase tracking-wider">
              {routePlan.algorithm}
            </span>
            <span className="text-[11px] text-slate-400">
              {routePlan.waypoints.length} Fixes
            </span>
          </div>

          {/* Quick Metrics Cards */}
          <div className="grid grid-cols-3 gap-2">
            <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
              <div className="text-[10px] text-aviation-muted flex items-center space-x-1">
                <Navigation className="w-3 h-3 text-sky-400" />
                <span>Distance</span>
              </div>
              <div className="text-sm font-bold text-white mt-1">
                {Math.round(routePlan.total_distance_nm)} <span className="text-[10px] font-normal text-slate-400">NM</span>
              </div>
              <div className="text-[9px] text-slate-500">
                {Math.round(routePlan.total_distance_km)} km
              </div>
            </div>

            <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
              <div className="text-[10px] text-aviation-muted flex items-center space-x-1">
                <Clock className="w-3 h-3 text-amber-400" />
                <span>ETE Time</span>
              </div>
              <div className="text-sm font-bold text-white mt-1">
                {routePlan.performance.flight_time_formatted}
              </div>
              <div className="text-[9px] text-slate-500">
                {Math.round(routePlan.performance.groundspeed_kts)} KTAS
              </div>
            </div>

            <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
              <div className="text-[10px] text-aviation-muted flex items-center space-x-1">
                <Fuel className="w-3 h-3 text-emerald-400" />
                <span>Trip Fuel</span>
              </div>
              <div className="text-sm font-bold text-white mt-1">
                {Math.round(routePlan.performance.trip_fuel_kg)} <span className="text-[10px] font-normal text-slate-400">kg</span>
              </div>
              <div className="text-[9px] text-slate-500">
                {Math.round(routePlan.performance.total_fuel_required_kg)} kg ramp
              </div>
            </div>
          </div>

          {/* Calculation Assumptions Toggle */}
          <div className="bg-slate-900/60 rounded border border-slate-800/80 text-xs">
            <button
              onClick={() => setShowAssumptions(!showAssumptions)}
              className="w-full px-3 py-2 flex items-center justify-between text-slate-400 hover:text-white"
            >
              <span>Performance Assumptions</span>
              {showAssumptions ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
            {showAssumptions && (
              <div className="px-3 pb-3 pt-1 text-[11px] text-slate-300 space-y-1.5 border-t border-slate-800/60">
                <p><b>Condition:</b> {routePlan.performance.assumptions}</p>
                <p className="text-slate-400"><b>Disclaimer:</b> {routePlan.performance.limitations}</p>
              </div>
            )}
          </div>

          {/* Waypoint Log Snippet */}
          <div className="border border-slate-800 rounded bg-slate-950/60 p-2">
            <div className="text-[11px] font-medium text-slate-300 mb-1 flex justify-between">
              <span>Nav Route Leg Log</span>
              <span className="text-[10px] text-slate-500">{routePlan.departure.ident} DCT {routePlan.destination.ident}</span>
            </div>
            <div className="space-y-1 max-h-24 overflow-y-auto text-[10px] font-mono">
              {routePlan.waypoints.map((wp, i) => (
                <div key={i} className="flex justify-between text-slate-400 hover:text-white">
                  <span>{i + 1}. {wp.ident}</span>
                  <span>{wp.bearing_deg}°</span>
                  <span>{wp.cumulative_distance_nm} NM</span>
                </div>
              ))}
            </div>
          </div>

          {/* Save Plan and Download PDF Actions */}
          <div className="flex space-x-2 pt-2">
            <button
              onClick={handleSavePlan}
              disabled={saving}
              className="flex-1 py-2 rounded bg-slate-800 hover:bg-slate-700 text-white text-xs font-medium flex items-center justify-center space-x-1.5 border border-slate-700 transition"
            >
              <Bookmark className="w-3.5 h-3.5 text-amber-400" />
              <span>{savedPlanCode ? "Saved!" : "Save Plan"}</span>
            </button>

            {savedPlanCode && (
              <a
                href={getBriefingDownloadUrl(savedPlanCode)}
                target="_blank"
                rel="noreferrer"
                className="flex-1 py-2 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium flex items-center justify-center space-x-1.5 transition text-center"
              >
                <FileDown className="w-3.5 h-3.5" />
                <span>OFP Briefing</span>
              </a>
            )}
          </div>

          {savedPlanCode && (
            <div className="p-2 bg-emerald-950/40 border border-emerald-800/50 rounded text-center text-[11px] text-emerald-300">
              Plan saved as <b>{savedPlanCode}</b>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
