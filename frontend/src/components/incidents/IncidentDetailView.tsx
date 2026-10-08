import React, { useState, useEffect } from 'react';
import { Incident, NearbyHospital, Notification } from '../../types';
import { SeverityBadge } from '../common/SeverityBadge';
import { StatusBadge } from '../common/StatusBadge';
import { BoundingBoxCanvas } from '../monitoring/BoundingBoxCanvas';
import { VerifyIncidentModal } from './VerifyIncidentModal';
import { CancelIncidentModal } from './CancelIncidentModal';
import { ResolveIncidentModal } from './ResolveIncidentModal';
import { hospitalApi } from '../../api/hospitalApi';
import { notificationApi } from '../../api/notificationApi';
import { useIncidents } from '../../context/IncidentContext';
import { useAuth } from '../../context/AuthContext';
import {
  MapPin,
  Clock,
  Car,
  CheckCircle,
  XCircle,
  CheckCircle2,
  AlertOctagon,
  Building2,
  Phone,
  Send,
  Bell,
  Layers,
  ArrowLeft,
  ShieldAlert,
  AlertTriangle,
  FileText,
} from 'lucide-react';

interface IncidentDetailViewProps {
  incident: Incident;
  onBack: () => void;
  onOpenMap?: () => void;
}

export const IncidentDetailView: React.FC<IncidentDetailViewProps> = ({
  incident,
  onBack,
  onOpenMap,
}) => {
  const { canVerifyIncidents, canTriggerNotifications } = useAuth();
  const { stopIncidentNotifications, sendManualAlert, acknowledgeIncident } = useIncidents();

  const [nearbyHospitals, setNearbyHospitals] = useState<NearbyHospital[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoadingHospitals, setIsLoadingHospitals] = useState<boolean>(true);
  const [showAnnotations, setShowAnnotations] = useState<boolean>(true);

  // Modals
  const [isVerifyOpen, setIsVerifyOpen] = useState<boolean>(false);
  const [isCancelOpen, setIsCancelOpen] = useState<boolean>(false);
  const [isResolveOpen, setIsResolveOpen] = useState<boolean>(false);

  // Manual Contact quick form state
  const [manualPhone, setManualPhone] = useState<string>('');
  const [manualName, setManualName] = useState<string>('');
  const [isDispatching, setIsDispatching] = useState<boolean>(false);

  useEffect(() => {
    const loadDetails = async () => {
      setIsLoadingHospitals(true);
      try {
        if (incident.latitude && incident.longitude) {
          const hosps = await hospitalApi.getNearbyHospitals({
            latitude: incident.latitude,
            longitude: incident.longitude,
            radius_km: 50,
            limit: 4,
          });
          setNearbyHospitals(hosps);
        }
        const notifs = await notificationApi.getIncidentNotifications(incident.id);
        setNotifications(notifs);
      } finally {
        setIsLoadingHospitals(false);
      }
    };

    loadDetails();
  }, [incident]);

  const handleManualDispatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualPhone.trim()) return;
    setIsDispatching(true);
    try {
      const notif = await sendManualAlert(
        incident.id,
        manualPhone,
        manualName || 'Highway Emergency Contact'
      );
      setNotifications((prev) => [notif, ...prev]);
      setManualPhone('');
      setManualName('');
    } finally {
      setIsDispatching(false);
    }
  };

  const handleQuickDispatchToHospital = async (hosp: NearbyHospital) => {
    const phone = hosp.phone_numbers[0] || '+919876543200';
    setIsDispatching(true);
    try {
      const notif = await sendManualAlert(
        incident.id,
        phone,
        hosp.name,
        `[URGENT EMERGENCY] Accident at ${incident.location_description || 'Highway'}. Dispatch ALS ambulance to ${incident.latitude}, ${incident.longitude}.`
      );
      setNotifications((prev) => [notif, ...prev]);
    } finally {
      setIsDispatching(false);
    }
  };

  const handleSimulateAck = async () => {
    if (nearbyHospitals.length > 0) {
      await acknowledgeIncident(
        incident.id,
        nearbyHospitals[0].id,
        'Dr. Rajesh Verma (Trauma Lead)',
        'ALS Ambulance #02 dispatched with paramedics. ETA 5 minutes.'
      );
    } else {
      await acknowledgeIncident(
        incident.id,
        undefined,
        'Dr. On-Duty EMT',
        'Emergency response team dispatched.'
      );
    }
  };

  const vehicles = incident.vehicle_info?.vehicles || [
    { type: 'Commercial Vehicle', color: 'White', bbox: [0.15, 0.25, 0.45, 0.55], speed_kmh: 70, confidence: 0.95 },
    { type: 'Sedan', color: 'Silver', bbox: [0.45, 0.35, 0.35, 0.45], speed_kmh: 80, confidence: 0.92 },
  ];

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Top Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 bg-gray-900/90 border border-gray-800 rounded-2xl shadow-xl backdrop-blur-md">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-xl transition border border-gray-700"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-2.5 flex-wrap">
              <h2 className="text-lg font-bold text-white font-mono">{incident.incident_id}</h2>
              <SeverityBadge severity={incident.severity} pulse={incident.status !== 'resolved'} />
              <StatusBadge status={incident.status} />
            </div>
            <p className="text-xs text-gray-400 mt-0.5">
              Detected: {new Date(incident.detected_at).toLocaleString()} • Camera:{' '}
              {incident.camera_external_id || 'CAM-HWY-01'}
            </p>
          </div>
        </div>

        {/* Operational Lifecycle Buttons */}
        <div className="flex items-center gap-2 flex-wrap">
          {incident.status === 'detected' && canVerifyIncidents && (
            <>
              <button
                onClick={() => setIsVerifyOpen(true)}
                className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold uppercase tracking-wider shadow-lg shadow-emerald-600/30 flex items-center gap-1.5 transition"
              >
                <CheckCircle className="w-4 h-4" />
                Verify Event
              </button>
              <button
                onClick={() => setIsCancelOpen(true)}
                className="px-3 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition border border-gray-700"
              >
                <XCircle className="w-4 h-4" />
                False Positive
              </button>
            </>
          )}

          {['detected', 'active', 'notified'].includes(incident.status) && (
            <button
              onClick={() => stopIncidentNotifications(incident.id)}
              className="px-3 py-2 bg-amber-950/80 hover:bg-amber-900 border border-amber-700/60 text-amber-300 rounded-xl text-xs font-bold flex items-center gap-1.5 transition"
            >
              <AlertOctagon className="w-4 h-4" />
              Stop Messaging
            </button>
          )}

          {incident.status !== 'resolved' && incident.status !== 'cancelled' && (
            <button
              onClick={() => setIsResolveOpen(true)}
              className="px-3.5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold uppercase tracking-wider shadow-lg shadow-blue-600/30 flex items-center gap-1.5 transition"
            >
              <CheckCircle2 className="w-4 h-4" />
              Resolve Incident
            </button>
          )}
        </div>
      </div>

      {/* Main Grid: Left (Media & AI Metadata) / Right (Hospitals & Notifications) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Annotated Camera Preview Frame */}
          <div className="p-5 bg-gray-900/80 border border-gray-800 rounded-2xl shadow-xl backdrop-blur-md">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold uppercase tracking-wider text-gray-300 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-red-500" />
                Accident Frame Capture & AI Detection
              </h3>
              <button
                onClick={() => setShowAnnotations(!showAnnotations)}
                className={`px-2.5 py-1 rounded-lg border text-xs font-semibold flex items-center gap-1.5 transition ${
                  showAnnotations
                    ? 'bg-emerald-950/80 border-emerald-500/50 text-emerald-400'
                    : 'bg-gray-800 border-gray-700 text-gray-400'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                {showAnnotations ? 'Bounding Boxes: ON' : 'Bounding Boxes: OFF'}
              </button>
            </div>

            <div className="aspect-video w-full rounded-xl overflow-hidden bg-gray-950 border border-gray-800 relative">
              {showAnnotations ? (
                <BoundingBoxCanvas
                  imageSrc={incident.accident_image_url}
                  vehicles={vehicles}
                  hasAccident={incident.accident_detected}
                  severity={incident.severity}
                  confidenceScore={incident.confidence_score}
                />
              ) : (
                <img
                  src={incident.accident_image_url || 'https://images.unsplash.com/photo-1545178803-4056771d60a3?auto=format&fit=crop&w=1200&q=80'}
                  alt="Accident snapshot"
                  className="w-full h-full object-cover"
                />
              )}
            </div>

            {/* AI Telemetry Strip */}
            <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
              <div className="p-3 bg-gray-950/80 rounded-xl border border-gray-800">
                <p className="text-[10px] text-gray-400 uppercase">AI Confidence</p>
                <p className="text-sm font-bold text-emerald-400 mt-0.5">
                  {Math.round(incident.confidence_score * 100)}%
                </p>
              </div>
              <div className="p-3 bg-gray-950/80 rounded-xl border border-gray-800">
                <p className="text-[10px] text-gray-400 uppercase">Vehicles Detected</p>
                <p className="text-sm font-bold text-white mt-0.5">{incident.vehicle_count || 2}</p>
              </div>
              <div className="p-3 bg-gray-950/80 rounded-xl border border-gray-800">
                <p className="text-[10px] text-gray-400 uppercase">Collision Type</p>
                <p className="text-xs font-bold text-amber-400 mt-0.5 truncate">
                  {incident.ai_event_data?.collision_type || 'Multi-Vehicle'}
                </p>
              </div>
              <div className="p-3 bg-gray-950/80 rounded-xl border border-gray-800">
                <p className="text-[10px] text-gray-400 uppercase">Inference Time</p>
                <p className="text-sm font-bold text-blue-400 mt-0.5">
                  {incident.ai_event_data?.processing_time_ms || 135}ms
                </p>
              </div>
            </div>
          </div>

          {/* Location & GPS Info */}
          <div className="p-5 bg-gray-900/80 border border-gray-800 rounded-2xl shadow-xl backdrop-blur-md space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold uppercase tracking-wider text-gray-300 flex items-center gap-2">
                <MapPin className="w-4 h-4 text-red-500" />
                Geographical Coordinates & Location
              </h3>
              {onOpenMap && (
                <button
                  onClick={onOpenMap}
                  className="text-xs font-bold text-red-400 hover:text-red-300 underline"
                >
                  View on Full Map →
                </button>
              )}
            </div>

            <p className="text-sm text-gray-200">{incident.location_description || 'Highway Corridor'}</p>

            <div className="flex items-center gap-4 text-xs font-mono text-gray-400">
              <span>Latitude: {incident.latitude ? incident.latitude.toFixed(5) : 'Unavailable'}</span>
              <span>Longitude: {incident.longitude ? incident.longitude.toFixed(5) : 'Unavailable'}</span>
            </div>

            {incident.notes && (
              <div className="p-3.5 bg-gray-950/80 rounded-xl border border-gray-800 text-xs text-gray-300 flex items-start gap-2">
                <FileText className="w-4 h-4 text-gray-400 flex-shrink-0 mt-0.5" />
                <p className="leading-relaxed">{incident.notes}</p>
              </div>
            )}
          </div>
        </div>

        {/* Right Column (5 cols) - Hospital Response & Notifications */}
        <div className="lg:col-span-5 space-y-6">
          {/* Hospital Acknowledgment Status Card */}
          {incident.acknowledged_at && (
            <div className="p-5 bg-gradient-to-br from-blue-950/50 to-gray-900 border-2 border-blue-500/60 rounded-2xl shadow-xl backdrop-blur-md">
              <div className="flex items-center gap-2.5 text-blue-400 font-bold text-sm uppercase tracking-wide mb-2">
                <CheckCircle2 className="w-5 h-5" />
                <span>Verified Hospital Response</span>
              </div>
              <p className="text-base font-extrabold text-white">
                {incident.acknowledged_by_hospital_name || 'Apex Trauma Emergency Center'}
              </p>
              <div className="text-xs text-gray-300 mt-2 space-y-1 font-mono">
                <p>Responder: {incident.acknowledged_responder || 'Chief Medical Officer'}</p>
                <p>Acknowledged At: {new Date(incident.acknowledged_at).toLocaleTimeString()}</p>
                {incident.acknowledged_notes && (
                  <p className="mt-2 p-2.5 bg-blue-950/80 rounded-lg text-blue-200 border border-blue-800/40">
                    &quot;{incident.acknowledged_notes}&quot;
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Quick Simulation Button if awaiting ack */}
          {!incident.acknowledged_at && incident.status !== 'resolved' && incident.status !== 'cancelled' && (
            <div className="p-4 bg-purple-950/30 border border-purple-800/50 rounded-2xl flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-bold text-purple-300">Hospital Response Simulation</p>
                <p className="text-[11px] text-gray-400">Simulate incoming hospital ambulance acknowledgment</p>
              </div>
              <button
                onClick={handleSimulateAck}
                className="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-bold uppercase transition whitespace-nowrap shadow-md shadow-purple-600/20"
              >
                Simulate Ack
              </button>
            </div>
          )}

          {/* Nearby Emergency Hospitals */}
          <div className="p-5 bg-gray-900/80 border border-gray-800 rounded-2xl shadow-xl backdrop-blur-md">
            <h3 className="text-sm font-bold uppercase tracking-wider text-gray-300 mb-3 flex items-center gap-2">
              <Building2 className="w-4 h-4 text-emerald-400" />
              Nearby Trauma Centers ({nearbyHospitals.length})
            </h3>

            {isLoadingHospitals ? (
              <p className="text-xs text-gray-400">Calculating hospital distances...</p>
            ) : nearbyHospitals.length === 0 ? (
              <p className="text-xs text-gray-500">No registered hospitals within 50km radius.</p>
            ) : (
              <div className="space-y-3">
                {nearbyHospitals.map((hosp) => (
                  <div
                    key={hosp.id}
                    className="p-3 rounded-xl bg-gray-950/80 border border-gray-800 hover:border-gray-700 transition flex items-center justify-between gap-2"
                  >
                    <div className="min-w-0">
                      <h4 className="text-xs font-bold text-white truncate">{hosp.name}</h4>
                      <p className="text-[11px] text-gray-400 truncate">{hosp.address}</p>
                      <div className="flex items-center gap-2 text-[10px] text-emerald-400 font-mono mt-1">
                        <span>{hosp.distance_km} km away</span>
                        <span>• {hosp.phone_numbers[0]}</span>
                      </div>
                    </div>

                    <button
                      onClick={() => handleQuickDispatchToHospital(hosp)}
                      disabled={isDispatching}
                      className="px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white rounded-lg text-xs font-bold flex items-center gap-1 transition shadow-sm flex-shrink-0 disabled:opacity-50"
                      title="Dispatch Emergency SMS directly to this hospital"
                    >
                      <Send className="w-3 h-3" />
                      Dispatch
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Manual Emergency Contact Number Dispatch */}
          {canTriggerNotifications && (
            <div className="p-5 bg-gray-900/80 border border-gray-800 rounded-2xl shadow-xl backdrop-blur-md">
              <h3 className="text-sm font-bold uppercase tracking-wider text-gray-300 mb-2 flex items-center gap-2">
                <Phone className="w-4 h-4 text-blue-400" />
                Manual Emergency Dispatch
              </h3>
              <p className="text-xs text-gray-400 mb-3">
                Enter an on-call emergency doctor or external unit number in E.164 format (+91...).
              </p>

              <form onSubmit={handleManualDispatch} className="space-y-3">
                <div>
                  <input
                    type="tel"
                    required
                    placeholder="+919876543210"
                    value={manualPhone}
                    onChange={(e) => setManualPhone(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-xs font-mono focus:outline-none focus:border-red-500"
                  />
                </div>
                <div>
                  <input
                    type="text"
                    placeholder="Recipient Name / Unit (e.g. Dr. Verma)"
                    value={manualName}
                    onChange={(e) => setManualName(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-xs focus:outline-none focus:border-red-500"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isDispatching || !manualPhone}
                  className="w-full py-2 bg-red-600 hover:bg-red-500 text-white rounded-xl text-xs font-bold uppercase tracking-wider shadow-lg shadow-red-600/30 transition disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  <Send className="w-3.5 h-3.5" />
                  {isDispatching ? 'Transmitting...' : 'Send Emergency Alert'}
                </button>
              </form>
            </div>
          )}

          {/* Notification History Timeline */}
          <div className="p-5 bg-gray-900/80 border border-gray-800 rounded-2xl shadow-xl backdrop-blur-md">
            <h3 className="text-sm font-bold uppercase tracking-wider text-gray-300 mb-3 flex items-center gap-2">
              <Bell className="w-4 h-4 text-purple-400" />
              Notification Dispatch History ({notifications.length})
            </h3>

            {notifications.length === 0 ? (
              <p className="text-xs text-gray-500">No emergency notifications sent yet for this incident.</p>
            ) : (
              <div className="space-y-2.5 max-h-56 overflow-y-auto pr-1 font-mono text-xs">
                {notifications.map((n) => (
                  <div key={n.id} className="p-2.5 rounded-lg bg-gray-950 border border-gray-800 text-gray-300">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-bold text-white">{n.recipient_name || n.recipient_phone}</span>
                      <span className="text-emerald-400 uppercase font-bold">{n.status}</span>
                    </div>
                    <p className="text-[10px] text-gray-400 mt-1 line-clamp-1">{n.message}</p>
                    <p className="text-[9px] text-gray-500 mt-1">
                      Cycle #{n.repeat_sequence} • {new Date(n.created_at).toLocaleTimeString()}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modal Dialogs */}
      <VerifyIncidentModal
        incident={incident}
        isOpen={isVerifyOpen}
        onClose={() => setIsVerifyOpen(false)}
      />
      <CancelIncidentModal
        incident={incident}
        isOpen={isCancelOpen}
        onClose={() => setIsCancelOpen(false)}
      />
      <ResolveIncidentModal
        incident={incident}
        isOpen={isResolveOpen}
        onClose={() => setIsResolveOpen(false)}
      />
    </div>
  );
};
