"use client";

import "leaflet/dist/leaflet.css";

import { useEffect, useRef } from "react";
import type { Map as LeafletMap, Circle, Marker } from "leaflet";

interface MapPickerProps {
  latitude: number;
  longitude: number;
  radiusKm: number;
  onCenterChange: (lat: number, lng: number) => void;
}

// A colored-dot DivIcon instead of Leaflet's default marker: the default
// icon references image files at a path that doesn't survive bundling
// (a well-known Leaflet+webpack papercut), and a plain signal-colored dot
// fits this app's instrument-panel language better than a generic pin.
function buildCenterIcon(L: typeof import("leaflet")) {
  return L.divIcon({
    className: "",
    html: `<span style="
      display:block;width:14px;height:14px;border-radius:9999px;
      background:hsl(42 100% 50%);border:2px solid hsl(220 26% 6%);
      box-shadow:0 0 0 4px hsl(42 100% 50% / 0.25);
    "></span>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
}

export function MapPicker({ latitude, longitude, radiusKm, onCenterChange }: MapPickerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<LeafletMap | null>(null);
  const markerRef = useRef<Marker | null>(null);
  const circleRef = useRef<Circle | null>(null);
  const onCenterChangeRef = useRef(onCenterChange);
  onCenterChangeRef.current = onCenterChange;

  // Init once.
  useEffect(() => {
    let cancelled = false;

    (async () => {
      const L = (await import("leaflet")).default;
      if (cancelled || !containerRef.current || mapRef.current) return;

      const map = L.map(containerRef.current, {
        center: [latitude, longitude],
        zoom: 11,
        scrollWheelZoom: true,
      });
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
      }).addTo(map);

      const icon = buildCenterIcon(L);
      const marker = L.marker([latitude, longitude], { icon, draggable: true }).addTo(map);
      const circle = L.circle([latitude, longitude], {
        radius: radiusKm * 1000,
        color: "#FFB300",
        weight: 1.5,
        fillColor: "#FFB300",
        fillOpacity: 0.08,
      }).addTo(map);

      const moveTo = (lat: number, lng: number) => {
        marker.setLatLng([lat, lng]);
        circle.setLatLng([lat, lng]);
        onCenterChangeRef.current(lat, lng);
      };

      map.on("click", (e) => moveTo(e.latlng.lat, e.latlng.lng));
      marker.on("dragend", () => {
        const pos = marker.getLatLng();
        moveTo(pos.lat, pos.lng);
      });

      mapRef.current = map;
      markerRef.current = marker;
      circleRef.current = circle;
    })();

    return () => {
      cancelled = true;
      mapRef.current?.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Keep marker/circle/view in sync when center or radius changes from
  // outside the map (typed recenter search, radius slider).
  useEffect(() => {
    const map = mapRef.current;
    const marker = markerRef.current;
    const circle = circleRef.current;
    if (!map || !marker || !circle) return;
    marker.setLatLng([latitude, longitude]);
    circle.setLatLng([latitude, longitude]);
    if (map.getCenter().distanceTo([latitude, longitude]) > 50) {
      map.setView([latitude, longitude]);
    }
  }, [latitude, longitude]);

  useEffect(() => {
    circleRef.current?.setRadius(radiusKm * 1000);
  }, [radiusKm]);

  return <div ref={containerRef} className="h-full w-full" />;
}
