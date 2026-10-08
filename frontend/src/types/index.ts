export type UserRole = 'admin' | 'operator' | 'viewer' | 'hospital';

export interface User {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  phone_number?: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export type CameraType = 'system' | 'mobile' | 'ip_cctv';
export type CameraStatus = 'online' | 'offline' | 'monitoring' | 'error' | 'maintenance';

export interface Camera {
  id: string;
  camera_id: string;
  name: string;
  camera_type: CameraType;
  location_name?: string;
  latitude?: number;
  longitude?: number;
  description?: string;
  status: CameraStatus;
  is_monitoring: boolean;
  health_score?: number;
  last_active_at?: string;
  last_detection_at?: string;
  total_detections: number;
  uptime_percentage?: number;
  created_at: string;
  updated_at?: string;
  connection_config?: {
    rtsp_url?: string;
    stream_endpoint?: string;
    username?: string;
    deviceId?: string;
  };
}

export type SeverityLevel = 'high' | 'medium' | 'low';
export type IncidentStatus = 'detected' | 'active' | 'notified' | 'acknowledged' | 'resolved' | 'cancelled';

export interface VehicleDetails {
  type: string;
  color?: string;
  bbox?: [number, number, number, number] | number[];
  speed_kmh?: number;
  confidence?: number;
}

export interface Incident {
  id: string;
  incident_id: string;
  camera_id?: string;
  camera_external_id?: string;
  detected_at: string;
  accident_detected: boolean;
  severity: SeverityLevel;
  confidence_score: number;
  latitude?: number;
  longitude?: number;
  location_description?: string;
  accident_image_url?: string;
  status: IncidentStatus;
  vehicle_count?: number;
  vehicle_info?: {
    vehicles?: VehicleDetails[];
    total_vehicles?: number;
    estimated_impact_speed_kmh?: number;
  };
  ai_event_data?: {
    model_version?: string;
    processing_time_ms?: number;
    collision_type?: string;
    fire_detected?: boolean;
    road_blockage?: boolean;
  };
  notification_started_at?: string;
  notification_stopped_at?: string;
  notification_count: number;
  acknowledged_at?: string;
  acknowledged_by_hospital_id?: string;
  acknowledged_by_hospital_name?: string;
  acknowledged_responder?: string;
  acknowledged_notes?: string;
  resolved_at?: string;
  resolved_by?: string;
  resolution_notes?: string;
  notes?: string;
  created_at: string;
  updated_at?: string;
}

export interface Hospital {
  id: string;
  name: string;
  hospital_code?: string;
  phone_numbers: string[];
  email?: string;
  address: string;
  city?: string;
  state?: string;
  postal_code?: string;
  latitude: number;
  longitude: number;
  emergency_contact?: string;
  has_emergency_dept: boolean;
  has_trauma_center: boolean;
  has_ambulance: boolean;
  bed_capacity?: number;
  available_beds?: number;
  is_available: boolean;
  is_24_7: boolean;
  accepts_sms: boolean;
  accepts_email: boolean;
  accepts_call: boolean;
  average_response_time_minutes?: number;
  total_responses: number;
  successful_responses: number;
  description?: string;
  website?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at?: string;
  last_notified_at?: string;
}

export interface NearbyHospital extends Hospital {
  distance_km: number;
}

export type NotificationType = 'sms' | 'email' | 'call' | 'push' | 'webhook';
export type NotificationStatus = 'pending' | 'sent' | 'delivered' | 'failed' | 'acknowledged' | 'cancelled';
export type RecipientType = 'hospital' | 'manual' | 'emergency_service' | 'admin';

export interface Notification {
  id: string;
  notification_id: string;
  incident_id: string;
  recipient_type: RecipientType;
  hospital_id?: string;
  recipient_phone?: string;
  recipient_email?: string;
  recipient_name?: string;
  notification_type: NotificationType;
  status: NotificationStatus;
  message: string;
  sent_at?: string;
  delivered_at?: string;
  acknowledged_at?: string;
  retry_count: number;
  is_repeat: boolean;
  repeat_sequence: number;
  created_at: string;
}

export interface SystemSettings {
  auto_notification_enabled: boolean;
  notification_interval_seconds: number;
  hospital_search_radius_km: number;
  max_hospitals_to_notify: number;
  max_notification_retries: number;
  maintenance_mode: boolean;
  test_mode: boolean;
  updated_at?: string;
}

export interface SystemHealth {
  status: string;
  timestamp: string;
  database_connected: boolean;
  scheduler_running: boolean;
  active_incidents: number;
  pending_notifications: number;
  online_cameras: number;
  maintenance_mode: boolean;
  uptime_seconds: number;
}

export interface AuditLog {
  id: string;
  user_id?: string;
  username?: string;
  action: string;
  resource_type?: string;
  resource_id?: string;
  method?: string;
  endpoint?: string;
  ip_address?: string;
  success: boolean;
  error_message?: string;
  description?: string;
  created_at: string;
}

export type WebSocketEventType =
  | 'connected'
  | 'pong'
  | 'incident_created'
  | 'incident_updated'
  | 'incident_acknowledged'
  | 'incident_resolved'
  | 'notification_sent'
  | 'notifications_stopped'
  | 'camera_status_changed'
  | 'maintenance_mode_changed'
  | 'system_alert';

export interface WebSocketMessage<T = any> {
  type: WebSocketEventType;
  data: T;
  timestamp?: string | null;
}
