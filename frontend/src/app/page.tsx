"use client";

import React, { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import Navbar from "@/components/Navbar";
import FlightPlanPanel from "@/components/FlightPlanPanel";
import AirportDetailPanel from "@/components/AirportDetailPanel";
import SavedPlansModal from "@/components/SavedPlansModal";
import LayerControl from "@/components/LayerControl";
import {
  AirportSummary,
  AircraftProfile,
  RoutePlanResponse,
  FlightPlan,
} from "@/types";
import {
  searchAirports,
  fetchAircraftProfiles,
  fetchHealth,
  planFlightRoute,
} from "@/lib/api";

// Dynamically import GlobeView with SSR disabled for WebGL browser execution
const GlobeView = dynamic(() => import("@/components/GlobeView"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex flex-col items-center justify-center bg-slate-950 text-slate-400">
      <div className="w-10 h-10 border-2 border-sky-500 border-t-transparent rounded-full animate-spin mb-4" />
      <p className="text-sm tracking-wide">Initializing 3D Aerospace Globe Engine...</p>
      <p className="text-xs text-slate-500 mt-1">Loading offline Natural Earth terrain & atmosphere</p>
    </div>
  ),
});

export default function Home() {
  const [airports, setAirports] = useState<AirportSummary[]>([]);
  const [aircraftProfiles, setAircraftProfiles] = useState<AircraftProfile[]>([]);
  const [backendOnline, setBackendOnline] = useState<boolean>(false);

  const [selectedAirport, setSelectedAirport] = useState<AirportSummary | null>(null);
  const [departureAirport, setDepartureAirport] = useState<AirportSummary | null>(null);
  const [destinationAirport, setDestinationAirport] = useState<AirportSummary | null>(null);
  const [routePlan, setRoutePlan] = useState<RoutePlanResponse | null>(null);

  const [flyToAirport, setFlyToAirport] = useState<AirportSummary | null>(null);
  const [resetGlobalTrigger, setResetGlobalTrigger] = useState<number>(0);
  const [isSavedPlansOpen, setIsSavedPlansOpen] = useState<boolean>(false);

  const [layers, setLayers] = useState({
    airports: true,
    route: true,
    waypoints: true,
    atmosphere: true,
  });

  // Load initial data and health check on mount
  useEffect(() => {
    fetchHealth().then((h) => {
      setBackendOnline(h.status === "ok");
    });

    searchAirports("", 100)
      .then((res) => setAirports(res.items))
      .catch((err) => console.warn("Could not load initial airports:", err));

    fetchAircraftProfiles()
      .then((profiles) => setAircraftProfiles(profiles))
      .catch((err) => console.warn("Could not load aircraft profiles:", err));
  }, []);

  const handleToggleLayer = (key: keyof typeof layers) => {
    setLayers((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleZoomToAirport = (airport: AirportSummary) => {
    setSelectedAirport(airport);
    setFlyToAirport(airport);
  };

  const handleResetGlobal = () => {
    setResetGlobalTrigger((prev) => prev + 1);
  };

  const handleLoadSavedPlan = async (plan: FlightPlan) => {
    // Locate departure and destination from airports list or search
    try {
      const dep = airports.find((a) => a.ident === plan.departure_ident) || {
        id: plan.departure_ident,
        ident: plan.departure_ident,
        name: plan.departure?.name || plan.departure_ident,
        latitude: plan.route_waypoints[0]?.latitude || 0,
        longitude: plan.route_waypoints[0]?.longitude || 0,
      };
      const dest = airports.find((a) => a.ident === plan.destination_ident) || {
        id: plan.destination_ident,
        ident: plan.destination_ident,
        name: plan.destination?.name || plan.destination_ident,
        latitude: plan.route_waypoints[plan.route_waypoints.length - 1]?.latitude || 0,
        longitude: plan.route_waypoints[plan.route_waypoints.length - 1]?.longitude || 0,
      };

      setDepartureAirport(dep);
      setDestinationAirport(dest);

      // Re-calculate plan route visualization
      const res = await planFlightRoute({
        departure_ident: plan.departure_ident,
        destination_ident: plan.destination_ident,
        aircraft_id: plan.aircraft_profile_id,
        routing_objective: plan.routing_objective,
      });
      setRoutePlan(res);
    } catch (err) {
      console.error("Error loading saved plan:", err);
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-aviation-bg select-none">
      {/* Top Navigation */}
      <Navbar
        onResetGlobal={handleResetGlobal}
        onOpenSavedPlans={() => setIsSavedPlansOpen(true)}
        backendOnline={backendOnline}
      />

      {/* Main Workspace */}
      <div className="relative flex-1 flex overflow-hidden">
        {/* Left Flight Planning Panel */}
        <FlightPlanPanel
          airports={airports}
          aircraftProfiles={aircraftProfiles}
          departureAirport={departureAirport}
          destinationAirport={destinationAirport}
          onSetDeparture={(airport) => {
            setDepartureAirport(airport);
            if (airport) handleZoomToAirport(airport);
          }}
          onSetDestination={(airport) => {
            setDestinationAirport(airport);
            if (airport) handleZoomToAirport(airport);
          }}
          routePlan={routePlan}
          onSetRoutePlan={setRoutePlan}
          onZoomToAirport={handleZoomToAirport}
          onPlanSaved={() => {}}
        />

        {/* 3D Earth Globe Viewport */}
        <div className="relative flex-1 h-full">
          <GlobeView
            airports={airports}
            selectedAirport={selectedAirport}
            departureAirport={departureAirport}
            destinationAirport={destinationAirport}
            routePlan={routePlan}
            layers={layers}
            onSelectAirport={(a) => {
              setSelectedAirport(a);
            }}
            flyToAirport={flyToAirport}
            resetGlobalTrigger={resetGlobalTrigger}
          />

          {/* Map Layer Overlay Control */}
          <LayerControl layers={layers} onToggleLayer={handleToggleLayer} />

          {/* Contextual Airport Detail Panel */}
          <AirportDetailPanel
            airport={selectedAirport}
            onClose={() => setSelectedAirport(null)}
            onSetDeparture={(a) => {
              setDepartureAirport(a);
              setSelectedAirport(null);
            }}
            onSetDestination={(a) => {
              setDestinationAirport(a);
              setSelectedAirport(null);
            }}
            onZoom={(a) => handleZoomToAirport(a)}
          />
        </div>
      </div>

      {/* Saved Flight Plans & Briefings Modal */}
      <SavedPlansModal
        isOpen={isSavedPlansOpen}
        onClose={() => setIsSavedPlansOpen(false)}
        onLoadPlan={handleLoadSavedPlan}
      />
    </div>
  );
}
