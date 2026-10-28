"use client";

import React, { useEffect, useRef } from "react";
import { AirportSummary, RoutePlanResponse } from "@/types";

interface GlobeViewProps {
  airports: AirportSummary[];
  selectedAirport: AirportSummary | null;
  departureAirport: AirportSummary | null;
  destinationAirport: AirportSummary | null;
  routePlan: RoutePlanResponse | null;
  layers: {
    airports: boolean;
    route: boolean;
    waypoints: boolean;
    atmosphere: boolean;
  };
  onSelectAirport: (airport: AirportSummary) => void;
  flyToAirport: AirportSummary | null;
  resetGlobalTrigger: number;
}

export default function GlobeView({
  airports,
  selectedAirport,
  departureAirport,
  destinationAirport,
  routePlan,
  layers,
  onSelectAirport,
  flyToAirport,
  resetGlobalTrigger,
}: GlobeViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<any>(null);
  const airportEntitiesRef = useRef<any[]>([]);
  const routeEntitiesRef = useRef<any[]>([]);

  // Initialize Cesium Viewer
  useEffect(() => {
    if (!containerRef.current) return;

    let viewer: any = null;

    // Dynamically import Cesium on client side
    import("cesium").then((Cesium) => {
      // Ensure zero-cost offline setup: clear ion access token
      Cesium.Ion.defaultAccessToken = "";
      (window as any).CESIUM_BASE_URL = "/cesium";

      try {
        viewer = new Cesium.Viewer(containerRef.current!, {
          baseLayerPicker: false,
          geocoder: false,
          homeButton: false,
          infoBox: false,
          sceneModePicker: false,
          selectionIndicator: false,
          timeline: false,
          navigationHelpButton: false,
          animation: false,
          fullscreenButton: false,
          vrButton: false,
          baseLayer: false,
          skyAtmosphere: new Cesium.SkyAtmosphere(),
        });

        // Load offline NaturalEarthII imagery asynchronously without paid tokens
        Cesium.TileMapServiceImageryProvider.fromUrl("/cesium/Assets/Textures/NaturalEarthII", {
          fileExtension: "jpg",
        })
          .then((provider: any) => {
            if (viewer && !viewer.isDestroyed()) {
              viewer.imageryLayers.addImageryProvider(provider);
            }
          })
          .catch((err: any) => {
            console.warn("Could not load local NaturalEarthII texture, using ellipsoid base:", err);
          });
      } catch (e) {
        // Ultimate fallback to clean ellipsoid globe if texture directory is not served
        console.warn("Falling back to standard ellipsoid globe:", e);
        viewer = new Cesium.Viewer(containerRef.current!, {
          baseLayerPicker: false,
          geocoder: false,
          homeButton: false,
          infoBox: false,
          sceneModePicker: false,
          selectionIndicator: false,
          timeline: false,
          navigationHelpButton: false,
          animation: false,
          fullscreenButton: false,
          vrButton: false,
          baseLayer: false,
          skyAtmosphere: false,
        });
      }

      viewerRef.current = viewer;

      // Dark aerospace aesthetic background
      viewer.scene.backgroundColor = Cesium.Color.fromCssColorString("#050811");
      viewer.scene.globe.baseColor = Cesium.Color.fromCssColorString("#0f172a");
      viewer.scene.globe.enableLighting = true;

      // Set initial global camera view (viewing Europe / Africa / Atlantic)
      viewer.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(10.0, 30.0, 18000000.0),
        duration: 1.5,
      });

      // Handle screen space clicks for selecting airport pins
      const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
      handler.setInputAction((movement: any) => {
        const pickedObject = viewer.scene.pick(movement.position);
        if (Cesium.defined(pickedObject) && pickedObject.id && pickedObject.id.airportData) {
          onSelectAirport(pickedObject.id.airportData);
        }
      }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

      (viewer as any)._clickHandler = handler;
    });

    return () => {
      if (viewerRef.current) {
        if (viewerRef.current._clickHandler) {
          viewerRef.current._clickHandler.destroy();
        }
        viewerRef.current.destroy();
        viewerRef.current = null;
      }
    };
  }, []);

  // Update Atmosphere and Lighting layer
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) return;
    if (viewer.scene.skyAtmosphere) {
      viewer.scene.skyAtmosphere.show = layers.atmosphere;
    }
    viewer.scene.globe.enableLighting = layers.atmosphere;
  }, [layers.atmosphere]);

  // Update Airport Entities on globe
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) return;

    import("cesium").then((Cesium) => {
      // Clear previous airport entities
      airportEntitiesRef.current.forEach((e) => viewer.entities.remove(e));
      airportEntitiesRef.current = [];

      if (!layers.airports) return;

      airports.forEach((airport) => {
        const isDep = departureAirport?.ident === airport.ident;
        const isDest = destinationAirport?.ident === airport.ident;
        const isSelected = selectedAirport?.ident === airport.ident;

        let pinColor = Cesium.Color.fromCssColorString("#38bdf8"); // Cyan default
        let pinSize = 7;

        if (isDep) {
          pinColor = Cesium.Color.fromCssColorString("#10b981"); // Green for departure
          pinSize = 12;
        } else if (isDest) {
          pinColor = Cesium.Color.fromCssColorString("#ef4444"); // Red for destination
          pinSize = 12;
        } else if (isSelected) {
          pinColor = Cesium.Color.fromCssColorString("#f59e0b"); // Amber for selected
          pinSize = 10;
        }

        const entity = viewer.entities.add({
          position: Cesium.Cartesian3.fromDegrees(airport.longitude, airport.latitude, 500),
          point: {
            pixelSize: pinSize,
            color: pinColor,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 1.5,
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
          },
          label: {
            text: isDep
              ? `DEP: ${airport.ident}`
              : isDest
              ? `DEST: ${airport.ident}`
              : airport.ident,
            font: isDep || isDest ? "bold 12px sans-serif" : "10px sans-serif",
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            fillColor: isDep
              ? Cesium.Color.fromCssColorString("#10b981")
              : isDest
              ? Cesium.Color.fromCssColorString("#ef4444")
              : Cesium.Color.WHITE,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
            pixelOffset: new Cesium.Cartesian2(0, -10),
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
            // Only show labels when camera is reasonably close or for origin/dest
            distanceDisplayCondition:
              isDep || isDest
                ? undefined
                : new Cesium.DistanceDisplayCondition(0.0, 7000000.0),
          },
        });

        entity.airportData = airport;
        airportEntitiesRef.current.push(entity);
      });
    });
  }, [
    airports,
    departureAirport,
    destinationAirport,
    selectedAirport,
    layers.airports,
  ]);

  // Update Flight Route Arc and Waypoints
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) return;

    import("cesium").then((Cesium) => {
      // Clear previous route entities
      routeEntitiesRef.current.forEach((e) => viewer.entities.remove(e));
      routeEntitiesRef.current = [];

      if (!routePlan || !layers.route) return;

      // Extract Great Circle interpolated path
      const coords = routePlan.great_circle_path.flatMap((pt) => [
        pt.longitude,
        pt.latitude,
        10000, // Elevated 10km for 3D flight corridor aesthetic
      ]);

      const routeLine = viewer.entities.add({
        name: `${routePlan.departure.ident} -> ${routePlan.destination.ident}`,
        polyline: {
          positions: Cesium.Cartesian3.fromDegreesArrayHeights(coords),
          width: 3.5,
          material: new Cesium.PolylineGlowMaterialProperty({
            glowPower: 0.25,
            color: Cesium.Color.fromCssColorString("#0284c7"), // Cyan/blue aviation arc
          }),
        },
      });
      routeEntitiesRef.current.push(routeLine);

      // Render Waypoints along the path if enabled
      if (layers.waypoints && routePlan.waypoints) {
        routePlan.waypoints.forEach((wp, idx) => {
          if (idx === 0 || idx === routePlan.waypoints.length - 1) return; // Origin & Dest already have pins

          const wpEntity = viewer.entities.add({
            position: Cesium.Cartesian3.fromDegrees(wp.longitude, wp.latitude, 10000),
            point: {
              pixelSize: 5,
              color: Cesium.Color.fromCssColorString("#93c5fd"),
              outlineColor: Cesium.Color.BLACK,
              outlineWidth: 1,
              disableDepthTestDistance: Number.POSITIVE_INFINITY,
            },
            label: {
              text: wp.ident,
              font: "9px monospace",
              fillColor: Cesium.Color.fromCssColorString("#e0f2fe"),
              outlineColor: Cesium.Color.BLACK,
              outlineWidth: 2,
              verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
              pixelOffset: new Cesium.Cartesian2(0, -6),
              disableDepthTestDistance: Number.POSITIVE_INFINITY,
              distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0.0, 5000000.0),
            },
          });
          routeEntitiesRef.current.push(wpEntity);
        });
      }

      // Smoothly zoom camera to route bounding view
      const allLats = routePlan.great_circle_path.map((p) => p.latitude);
      const allLons = routePlan.great_circle_path.map((p) => p.longitude);
      const minLat = Math.min(...allLats);
      const maxLat = Math.max(...allLats);
      const minLon = Math.min(...allLons);
      const maxLon = Math.max(...allLons);

      viewer.camera.flyTo({
        destination: Cesium.Rectangle.fromDegrees(
          Math.max(minLon - 5, -180),
          Math.max(minLat - 5, -85),
          Math.min(maxLon + 5, 180),
          Math.min(maxLat + 5, 85)
        ),
        duration: 2.0,
      });
    });
  }, [routePlan, layers.route, layers.waypoints]);

  // Fly to selected airport when triggered
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || !flyToAirport) return;

    import("cesium").then((Cesium) => {
      viewer.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(
          flyToAirport.longitude,
          flyToAirport.latitude,
          35000.0 // 35 km altitude for terminal / airport view
        ),
        duration: 1.8,
      });
    });
  }, [flyToAirport]);

  // Reset to global view when triggered
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || resetGlobalTrigger === 0) return;

    import("cesium").then((Cesium) => {
      viewer.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(10.0, 25.0, 18000000.0),
        duration: 1.5,
      });
    });
  }, [resetGlobalTrigger]);

  return (
    <div className="relative w-full h-full">
      <div ref={containerRef} className="w-full h-full" />
    </div>
  );
}
