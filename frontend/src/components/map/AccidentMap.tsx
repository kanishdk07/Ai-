import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { Incident, Camera, Hospital } from '../../types';
import { useIncidents } from '../../context/IncidentContext';
import { useCameras } from '../../context/CameraContext';
import { hospitalApi } from '../../api/hospitalApi';
import { Eye, MapPin, Layers, RefreshCw, AlertTriangle, Building2, Cctv } from 'lucide-react';

interface AccidentMapProps {
  onSelectIncident?: (id: string) => void;
  height?: string;
  focusIncidentId?: string;
}

export const AccidentMap: React.FC<AccidentMapProps> = ({
  onSelectIncident,
  height = '600px',
  focusIncidentId,
}) => {
  const { incidents } = useIncidents();
  const { cameras } = useCameras();
  const [hospitals, setHospitals] = useState<Hospital[]>([]);

  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersLayerRef = useRef<L.LayerGroup | null>(null);

  const [showCameras, setShowCameras] = useState<boolean>(true);
  const [showIncidents, setShowIncidents] = useState<boolean>(true);
  const [showHospitals, setShowHospitals] = useState<boolean>(true);

  // Load hospitals
  useEffect(() => {
    const fetchHospitals = async () => {
      try {
        const res = await hospitalApi.getHospitals();
        setHospitals(res.hospitals);
      } catch {}
    };
    fetchHospitals();
  }, []);

  // Initialize map instance
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // Default center around Northern Highway Corridor (Delhi-Jaipur / Panipat)
    const map = L.map(mapContainerRef.current, {
      center: [28.6139, 77.2090],
      zoom: 9,
      zoomControl: false,
    });

    L.control.zoom({ position: 'bottomright' }).addTo(map);

    // Dark tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://carto.com/">CARTO</a> SafeWay AI',
      maxZoom: 19,
    }).addTo(map);

    const layerGroup = L.layerGroup().addTo(map);
    markersLayerRef.current = layerGroup;
    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Render markers and polyline links
  useEffect(() => {
    if (!mapInstanceRef.current || !markersLayerRef.current) return;

    const layerGroup = markersLayerRef.current;
    layerGroup.clearLayers();

    const bounds: L.LatLngExpression[] = [];

    // 1. Render Registered Cameras
    if (showCameras) {
      cameras.forEach((cam) => {
        if (cam.latitude && cam.longitude) {
          const isMonitoring = cam.is_monitoring;
          const colorClass = isMonitoring ? '#10B981' : '#6B7280';

          const cameraIcon = L.divIcon({
            className: 'custom-camera-marker',
            html: `
              <div style="
                background: #111827;
                border: 2px solid ${colorClass};
                border-radius: 50%;
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.5);
              ">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="${colorClass}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"></path>
                  <circle cx="12" cy="13" r="3"></circle>
                </svg>
              </div>
            `,
            iconSize: [32, 32],
            iconAnchor: [16, 16],
          });

          const marker = L.marker([cam.latitude, cam.longitude], { icon: cameraIcon });
          marker.bindPopup(`
            <div style="padding: 4px; font-family: Inter, sans-serif;">
              <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 4px;">
                <span style="font-size: 11px; font-weight: bold; color: ${colorClass}; text-transform: uppercase;">● Camera Feed</span>
                <span style="font-size: 10px; font-family: monospace; color: #9CA3AF;">${cam.camera_id}</span>
              </div>
              <p style="font-size: 13px; font-weight: bold; color: #FFFFFF; margin: 0 0 4px 0;">${cam.name}</p>
              <p style="font-size: 11px; color: #D1D5DB; margin: 0 0 6px 0;">${cam.location_name || 'Highway Corridor'}</p>
              <div style="font-size: 10px; font-family: monospace; color: #9CA3AF;">
                Status: <strong style="color: ${colorClass}; text-transform: uppercase;">${cam.status}</strong>
              </div>
            </div>
          `);
          layerGroup.addLayer(marker);
          bounds.push([cam.latitude, cam.longitude]);
        }
      });
    }

    // 2. Render Nearby Hospitals
    if (showHospitals) {
      hospitals.forEach((hosp) => {
        if (hosp.latitude && hosp.longitude) {
          const hospIcon = L.divIcon({
            className: 'custom-hospital-marker',
            html: `
              <div style="
                background: #064E3B;
                border: 2px solid #34D399;
                border-radius: 8px;
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 4px 12px rgba(6,78,59,0.5);
              ">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#34D399" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 6v12"></path>
                  <path d="M6 12h12"></path>
                </svg>
              </div>
            `,
            iconSize: [32, 32],
            iconAnchor: [16, 16],
          });

          const marker = L.marker([hosp.latitude, hosp.longitude], { icon: hospIcon });
          marker.bindPopup(`
            <div style="padding: 4px; font-family: Inter, sans-serif;">
              <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 4px;">
                <span style="font-size: 11px; font-weight: bold; color: #34D399; text-transform: uppercase;">🚑 Emergency Trauma Center</span>
              </div>
              <p style="font-size: 13px; font-weight: bold; color: #FFFFFF; margin: 0 0 4px 0;">${hosp.name}</p>
              <p style="font-size: 11px; color: #D1D5DB; margin: 0 0 6px 0;">${hosp.address}</p>
              <div style="font-size: 10px; font-family: monospace; color: #9CA3AF; margin-bottom: 4px;">
                Contact: <strong style="color: #60A5FA;">${hosp.phone_numbers[0]}</strong>
              </div>
              <div style="font-size: 10px; color: #34D399;">
                Available Beds: ${hosp.available_beds || 24} • 24/7 ALS Ambulance
              </div>
            </div>
          `);
          layerGroup.addLayer(marker);
          bounds.push([hosp.latitude, hosp.longitude]);
        }
      });
    }

    // 3. Render Accident Incidents
    if (showIncidents) {
      incidents.forEach((inc) => {
        if (inc.latitude && inc.longitude) {
          const isHigh = inc.severity === 'high';
          const isResolved = inc.status === 'resolved';
          const markerColor = isResolved ? '#10B981' : isHigh ? '#EF4444' : '#F59E0B';

          const incidentIcon = L.divIcon({
            className: 'custom-incident-marker',
            html: `
              <div style="
                position: relative;
                width: 36px;
                height: 36px;
                display: flex;
                align-items: center;
                justify-content: center;
              ">
                ${
                  !isResolved && isHigh
                    ? `<div style="
                        position: absolute;
                        width: 100%;
                        height: 100%;
                        border-radius: 50%;
                        background: rgba(239, 68, 68, 0.4);
                        animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;
                      "></div>`
                    : ''
                }
                <div style="
                  position: relative;
                  background: #111827;
                  border: 2.5px solid ${markerColor};
                  border-radius: 50%;
                  width: 32px;
                  height: 32px;
                  display: flex;
                  align-items: center;
                  justify-content: center;
                  box-shadow: 0 4px 16px ${markerColor}66;
                ">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="${markerColor}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path>
                    <line x1="12" y1="9" x2="12" y2="13"></line>
                    <line x1="12" y1="17" x2="12.01" y2="17"></line>
                  </svg>
                </div>
              </div>
            `,
            iconSize: [36, 36],
            iconAnchor: [18, 18],
          });

          const marker = L.marker([inc.latitude, inc.longitude], { icon: incidentIcon });
          marker.bindPopup(`
            <div style="padding: 6px; font-family: Inter, sans-serif; min-width: 220px;">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                <span style="font-size: 11px; font-weight: bold; color: ${markerColor}; text-transform: uppercase;">
                  ● ${inc.severity} Severity Crash
                </span>
                <span style="font-size: 10px; font-family: monospace; color: #9CA3AF;">${Math.round(inc.confidence_score * 100)}% AI</span>
              </div>
              <p style="font-size: 13px; font-weight: bold; color: #FFFFFF; margin: 0 0 4px 0; font-family: monospace;">${inc.incident_id}</p>
              <p style="font-size: 11px; color: #D1D5DB; margin: 0 0 6px 0;">${inc.location_description || 'Highway Corridor'}</p>
              <div style="font-size: 10px; font-family: monospace; color: #9CA3AF; margin-bottom: 6px;">
                Status: <strong style="color: #F3F4F6; text-transform: uppercase;">${inc.status}</strong>
              </div>
              <div style="font-size: 10px; color: #9CA3AF;">
                Time: ${new Date(inc.detected_at).toLocaleTimeString()}
              </div>
            </div>
          `);

          marker.on('click', () => {
            if (onSelectIncident) onSelectIncident(inc.id);
          });

          layerGroup.addLayer(marker);
          bounds.push([inc.latitude, inc.longitude]);

          // Add radius search circle around active accidents
          if (!isResolved) {
            const circle = L.circle([inc.latitude, inc.longitude], {
              radius: 15000, // 15 km inner radius visual
              color: markerColor,
              fillColor: markerColor,
              fillOpacity: 0.08,
              weight: 1,
              dashArray: '4, 8',
            });
            layerGroup.addLayer(circle);
          }
        }
      });
    }

    // Auto fit map bounds if items exist
    if (bounds.length > 0 && !focusIncidentId) {
      mapInstanceRef.current.fitBounds(L.latLngBounds(bounds), { padding: [50, 50], maxZoom: 12 });
    }
  }, [cameras, hospitals, incidents, showCameras, showHospitals, showIncidents, focusIncidentId, onSelectIncident]);

  return (
    <div className="relative w-full rounded-2xl overflow-hidden border border-gray-800 shadow-2xl bg-gray-950">
      {/* Map Filter Controls Bar */}
      <div className="absolute top-4 left-4 z-10 flex items-center gap-2 p-2 bg-gray-900/90 backdrop-blur-md border border-gray-800 rounded-xl shadow-xl">
        <span className="text-xs font-bold text-gray-400 uppercase tracking-wider px-2 font-mono flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5" />
          Layers
        </span>

        <button
          onClick={() => setShowIncidents(!showIncidents)}
          className={`px-2.5 py-1 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${
            showIncidents
              ? 'bg-red-600 text-white shadow-sm shadow-red-600/30'
              : 'bg-gray-800 text-gray-400 hover:text-white'
          }`}
        >
          <AlertTriangle className="w-3 h-3" />
          Accidents ({incidents.length})
        </button>

        <button
          onClick={() => setShowCameras(!showCameras)}
          className={`px-2.5 py-1 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${
            showCameras
              ? 'bg-blue-600 text-white shadow-sm shadow-blue-600/30'
              : 'bg-gray-800 text-gray-400 hover:text-white'
          }`}
        >
          <Cctv className="w-3 h-3" />
          Cameras ({cameras.length})
        </button>

        <button
          onClick={() => setShowHospitals(!showHospitals)}
          className={`px-2.5 py-1 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${
            showHospitals
              ? 'bg-emerald-600 text-white shadow-sm shadow-emerald-600/30'
              : 'bg-gray-800 text-gray-400 hover:text-white'
          }`}
        >
          <Building2 className="w-3 h-3" />
          Hospitals ({hospitals.length})
        </button>
      </div>

      {/* Map Canvas Container */}
      <div ref={mapContainerRef} style={{ height }} className="w-full" />

      {/* Map Legend Overlay */}
      <div className="absolute bottom-4 left-4 z-10 p-3 bg-gray-900/90 backdrop-blur-md border border-gray-800 rounded-xl shadow-xl text-xs space-y-1.5 pointer-events-none">
        <p className="font-bold text-white uppercase tracking-wider text-[10px] mb-1 font-mono">Legend</p>
        <div className="flex items-center gap-2 text-gray-300">
          <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />
          <span>High Severity Crash</span>
        </div>
        <div className="flex items-center gap-2 text-gray-300">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
          <span>Medium Severity Crash</span>
        </div>
        <div className="flex items-center gap-2 text-gray-300">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
          <span>Highway CCTV Camera</span>
        </div>
        <div className="flex items-center gap-2 text-gray-300">
          <span className="w-2.5 h-2.5 rounded bg-emerald-800 border border-emerald-400" />
          <span>Emergency Hospital / Trauma Center</span>
        </div>
      </div>
    </div>
  );
};
