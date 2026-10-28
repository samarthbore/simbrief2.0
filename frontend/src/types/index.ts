export interface Runway {
  id: string;
  airport_ident: string;
  length_ft?: number;
  width_ft?: number;
  surface?: string;
  lighted: boolean;
  closed: boolean;
  le_ident?: string;
  le_latitude?: number;
  le_longitude?: number;
  le_elevation_ft?: number;
  he_ident?: string;
  he_latitude?: number;
  he_longitude?: number;
  he_elevation_ft?: number;
}

export interface AirportSummary {
  id: string;
  ident: string;
  icao?: string;
  iata?: string;
  name: string;
  airport_type?: string;
  latitude: number;
  longitude: number;
  elevation_ft?: number;
  municipality?: string;
  iso_country?: string;
}

export interface AirportDetail extends AirportSummary {
  continent?: string;
  iso_region?: string;
  scheduled_service: boolean;
  gps_code?: string;
  local_code?: string;
  home_link?: string;
  wikipedia_link?: string;
  runways: Runway[];
}

export interface AirportListResponse {
  total: number;
  items: AirportSummary[];
}

export interface AircraftProfile {
  id: string;
  identifier: string;
  name: string;
  category: string;
  cruise_speed_kts: number;
  fuel_flow_kg_hr: number;
  climb_rate_fpm: number;
  descent_rate_fpm: number;
  service_ceiling_ft: number;
  max_range_nm: number;
  description?: string;
  model_source?: string;
}

export interface RouteWaypoint {
  id?: string;
  ident: string;
  name?: string;
  node_type: string;
  latitude: number;
  longitude: number;
  airway?: string;
  leg_distance_nm: number;
  bearing_deg: number;
  cumulative_distance_nm: number;
}

export interface RoutePerformance {
  distance_nm: number;
  groundspeed_kts: number;
  flight_time_hours: number;
  flight_time_minutes: number;
  flight_time_formatted: string;
  trip_fuel_kg: number;
  reserve_fuel_kg: number;
  taxi_fuel_kg: number;
  total_fuel_required_kg: number;
  fuel_flow_kg_hr: number;
  assumptions: string;
  limitations: string;
}

export interface RoutePlanResponse {
  departure: AirportSummary;
  destination: AirportSummary;
  aircraft: AircraftProfile;
  routing_objective: string;
  algorithm: string;
  total_distance_nm: number;
  total_distance_km: number;
  estimated_flight_time_min: number;
  estimated_fuel_burn_kg: number;
  performance: RoutePerformance;
  waypoints: RouteWaypoint[];
  great_circle_path: { latitude: number; longitude: number }[];
  visited_nodes_count: number;
}

export interface FlightPlanRevision {
  id: string;
  revision_number: number;
  changes_summary?: string;
  route_summary: string;
  total_distance_nm: number;
  estimated_flight_time_min: number;
  estimated_fuel_burn_kg: number;
  created_at: string;
}

export interface FlightPlan {
  id: string;
  plan_code: string;
  title?: string;
  departure_ident: string;
  destination_ident: string;
  departure?: AirportSummary;
  destination?: AirportSummary;
  aircraft_profile_id: string;
  aircraft_profile?: AircraftProfile;
  routing_objective: string;
  total_distance_nm: number;
  estimated_flight_time_min: number;
  estimated_fuel_burn_kg: number;
  cruise_altitude_ft: number;
  route_waypoints: RouteWaypoint[];
  calculation_assumptions?: string;
  status: string;
  created_at: string;
  updated_at: string;
  revisions: FlightPlanRevision[];
}
