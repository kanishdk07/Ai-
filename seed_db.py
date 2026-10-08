"""
Database Seed Script
Populates the SQLite database with initial data for testing and demonstration
"""
import asyncio
import sys
import os
import uuid
from datetime import datetime, timedelta

# Make sure app is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from sqlalchemy import select

from app.config import settings
from app.database import Base
from app.models.user import User, UserRole
from app.models.camera import Camera, CameraType, CameraStatus
from app.models.hospital import Hospital
from app.models.incident import Incident, IncidentStatus, SeverityLevel
from app.models.notification import Notification, NotificationStatus, NotificationType, RecipientType
from app.models.audit_log import AuditLog
from app.models.admin_setting import AdminSetting
from app.models.hospital_response import HospitalResponse
from app.models.accident_image import AccidentImage
from app.utils.security import get_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_database():
    """Seed the database with initial data"""
    
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # ─── Check if already seeded ───
        result = await session.execute(select(User).where(User.username == "admin"))
        if result.scalar_one_or_none():
            logger.info("Database already seeded. Skipping.")
            print("✓ Database already contains data. Nothing to seed.")
            await engine.dispose()
            return

        now = datetime.utcnow()
        
        # ─── Users ───
        admin_id = str(uuid.uuid4())
        operator_id = str(uuid.uuid4())
        viewer_id = str(uuid.uuid4())
        
        users = [
            User(
                id=admin_id,
                email=settings.DEFAULT_ADMIN_EMAIL,
                username="admin",
                hashed_password=get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
                full_name="Chief Control Officer (Admin)",
                role=UserRole.ADMIN,
                phone_number="+919876543210",
                is_active=True,
                is_verified=True,
            ),
            User(
                id=operator_id,
                email="operator@safeway.gov.in",
                username="operator",
                hashed_password=get_password_hash("Operator123!"),
                full_name="Highway Patrol Operator",
                role=UserRole.OPERATOR,
                phone_number="+919876543211",
                is_active=True,
                is_verified=True,
            ),
            User(
                id=viewer_id,
                email="viewer@safeway.gov.in",
                username="viewer",
                hashed_password=get_password_hash("Viewer123!"),
                full_name="Traffic Analyst Viewer",
                role=UserRole.VIEWER,
                phone_number="+919876543212",
                is_active=True,
                is_verified=True,
            ),
        ]
        session.add_all(users)
        await session.flush()
        logger.info("Users created")
        
        # ─── Admin Settings ───
        admin_setting = AdminSetting(
            id=str(uuid.uuid4()),
            auto_notification_enabled=False,
            notification_repeat_interval=60,
            maintenance_mode=False,
            monitoring_status="active",
            default_hospital_search_radius=50.0,
            system_configuration_version=1,
            last_updated_by=admin_id,
        )
        session.add(admin_setting)
        
        # ─── Cameras ───
        cam1_id = str(uuid.uuid4())
        cam2_id = str(uuid.uuid4())
        cam3_id = str(uuid.uuid4())
        cam4_id = str(uuid.uuid4())
        cam5_id = str(uuid.uuid4())
        cam6_id = str(uuid.uuid4())
        
        cameras = [
            Camera(
                id=cam1_id, camera_id="CAM-NH48-KM245",
                name="NH-48 KM 245 Toll Plaza North", camera_type=CameraType.IP_CCTV,
                location_name="NH-48 KM 245 (Delhi-Jaipur Express Corridor)",
                latitude=28.4595, longitude=77.0266,
                description="High-definition 4K PTZ CCTV overlooking north toll junction",
                status=CameraStatus.MONITORING, is_monitoring=True, health_score=98,
                total_detections=14, uptime_percentage=99.8,
                connection_config={"stream_endpoint": "https://images.unsplash.com/photo-1545178803-4056771d60a3?auto=format&fit=crop&w=1200&q=80", "rtsp_url": "rtsp://nhai-camera-hub.internal/live/cam-01"},
                created_by=admin_id,
            ),
            Camera(
                id=cam2_id, camera_id="CAM-NH44-KM112",
                name="NH-44 KM 112 Flyover Overpass", camera_type=CameraType.IP_CCTV,
                location_name="NH-44 KM 112 (Panipat Highway Section)",
                latitude=28.7041, longitude=77.1025,
                description="Wide-angle surveillance camera monitoring fast lane merging zone",
                status=CameraStatus.MONITORING, is_monitoring=True, health_score=95,
                total_detections=28, uptime_percentage=99.4,
                connection_config={"stream_endpoint": "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?auto=format&fit=crop&w=1200&q=80", "rtsp_url": "rtsp://nhai-camera-hub.internal/live/cam-02"},
                created_by=admin_id,
            ),
            Camera(
                id=cam3_id, camera_id="CAM-MEW-KM088",
                name="Mumbai-Pune Expressway KM 88 Ghats", camera_type=CameraType.IP_CCTV,
                location_name="Mumbai-Pune Expressway Khandala Slope",
                latitude=18.7562, longitude=73.3429,
                description="Weather-hardened IR thermal and optical dual feed for mountain highway",
                status=CameraStatus.MONITORING, is_monitoring=True, health_score=92,
                total_detections=9, uptime_percentage=98.9,
                connection_config={"stream_endpoint": "https://images.unsplash.com/photo-1506521781263-d8422e82f27a?auto=format&fit=crop&w=1200&q=80", "rtsp_url": "rtsp://nhai-camera-hub.internal/live/cam-03"},
                created_by=admin_id,
            ),
            Camera(
                id=cam4_id, camera_id="CAM-SYS-WEBCAM",
                name="Local Operations Workstation USB Cam", camera_type=CameraType.SYSTEM,
                location_name="Control Room Hub 04 Desk",
                latitude=28.6139, longitude=77.2090,
                description="Direct browser-connected USB / Integrated webcam feed for live AI edge inference",
                status=CameraStatus.ONLINE, is_monitoring=False, health_score=100,
                total_detections=3, uptime_percentage=100.0,
                created_by=admin_id,
            ),
            Camera(
                id=cam5_id, camera_id="CAM-MOB-PATROL1",
                name="Highway Patrol Mobile Unit 09", camera_type=CameraType.MOBILE,
                location_name="Mobile Patrol Unit Van (En route NH-48)",
                latitude=28.5200, longitude=77.0800,
                description="Smartphone / Tablet field browser stream via WebRTC/transcode uplink",
                status=CameraStatus.ONLINE, is_monitoring=False, health_score=88,
                total_detections=6, uptime_percentage=94.2,
                created_by=admin_id,
            ),
            Camera(
                id=cam6_id, camera_id="CAM-NH24-KM054",
                name="NH-24 Bridge Sector 62 Underpass", camera_type=CameraType.IP_CCTV,
                location_name="NH-24 KM 54 Ghaziabad Link",
                latitude=28.6280, longitude=77.3649,
                description="Optical CCTV camera (Network cable maintenance scheduled)",
                status=CameraStatus.OFFLINE, is_monitoring=False, health_score=0,
                total_detections=19, uptime_percentage=82.5,
                created_by=admin_id,
            ),
        ]
        session.add_all(cameras)
        await session.flush()
        logger.info("Cameras created")
        
        # ─── Hospitals ───
        hosp1_id = str(uuid.uuid4())
        hosp2_id = str(uuid.uuid4())
        hosp3_id = str(uuid.uuid4())
        hosp4_id = str(uuid.uuid4())
        
        hospitals = [
            Hospital(
                id=hosp1_id, name="Apex Trauma & Multi-Specialty Hospital",
                hospital_code="HOSP-APEX-01",
                phone_numbers=["+919876543201", "+911145678901"],
                email="emergency@apextrauma.org",
                address="Sector 44, Near NH-48 Expressway Interchange",
                city="Gurugram", state="Haryana", postal_code="122003",
                latitude=28.4550, longitude=77.0320,
                emergency_contact="Dr. R. Sharma (Head of Trauma - 24/7)",
                has_emergency_dept=True, has_trauma_center=True, has_ambulance=True,
                bed_capacity=450, available_beds=34,
                is_available=True, is_24_7=True,
                accepts_sms=True, accepts_email=True, accepts_call=True,
                average_response_time_minutes=3.2,
                total_responses=142, successful_responses=139,
                description="Level 1 Trauma Center with 12 Advanced Life Support (ALS) Ambulances and Helipad.",
                is_active=True, is_verified=True,
            ),
            Hospital(
                id=hosp2_id, name="Metro City Government Emergency Hospital",
                hospital_code="HOSP-METRO-02",
                phone_numbers=["+919876543202", "+911123456789"],
                email="casualty@metrohospital.gov.in",
                address="Main Ring Road, Civil Lines",
                city="New Delhi", state="Delhi", postal_code="110054",
                latitude=28.6850, longitude=77.2100,
                emergency_contact="Casualty Medical Officer (On Duty)",
                has_emergency_dept=True, has_trauma_center=True, has_ambulance=True,
                bed_capacity=800, available_beds=58,
                is_available=True, is_24_7=True,
                accepts_sms=True, accepts_email=True, accepts_call=True,
                average_response_time_minutes=4.5,
                total_responses=285, successful_responses=278,
                description="Central Government Multi-Specialty Hospital equipped with emergency triage and ICU burn ward.",
                is_active=True, is_verified=True,
            ),
            Hospital(
                id=hosp3_id, name="Sanjivani Highway Emergency Care Clinic",
                hospital_code="HOSP-SANJ-03",
                phone_numbers=["+919876543203"],
                email="dispatch@sanjivanicare.in",
                address="NH-44 Toll Plaza Adjacent Complex, KM 110",
                city="Panipat", state="Haryana", postal_code="132103",
                latitude=28.7120, longitude=77.0950,
                emergency_contact="Emergency Dispatch Desk",
                has_emergency_dept=True, has_trauma_center=False, has_ambulance=True,
                bed_capacity=120, available_beds=15,
                is_available=True, is_24_7=True,
                accepts_sms=True, accepts_email=False, accepts_call=True,
                average_response_time_minutes=5.1,
                total_responses=67, successful_responses=65,
                description="Dedicated Highway Rapid-Response stabilization clinic with 4 GPS-tracked ambulances.",
                is_active=True, is_verified=True,
            ),
            Hospital(
                id=hosp4_id, name="LifeCare Critical Care Center",
                hospital_code="HOSP-LIFE-04",
                phone_numbers=["+919876543204"],
                email="er@lifecarecritical.com",
                address="Sector 62, Expressway Bypass Rd",
                city="Noida", state="Uttar Pradesh", postal_code="201301",
                latitude=28.6250, longitude=77.3700,
                emergency_contact="Chief of Critical Care",
                has_emergency_dept=True, has_trauma_center=True, has_ambulance=True,
                bed_capacity=300, available_beds=22,
                is_available=True, is_24_7=True,
                accepts_sms=True, accepts_email=True, accepts_call=True,
                average_response_time_minutes=3.8,
                total_responses=94, successful_responses=92,
                description="Specialized neuro-trauma and surgical emergency center on eastern expressway access corridor.",
                is_active=True, is_verified=True,
            ),
        ]
        session.add_all(hospitals)
        await session.flush()
        logger.info("Hospitals created")
        
        # ─── Incidents ───
        inc1_id = str(uuid.uuid4())
        inc2_id = str(uuid.uuid4())
        inc3_id = str(uuid.uuid4())
        inc4_id = str(uuid.uuid4())
        
        incidents = [
            Incident(
                id=inc1_id, incident_id="ACC-2026-10-08-001",
                camera_id=cam1_id, camera_external_id="CAM-NH48-KM245",
                detected_at=now - timedelta(minutes=4),
                accident_detected=True, severity=SeverityLevel.HIGH, confidence_score=0.94,
                latitude=28.4595, longitude=77.0266,
                location_description="NH-48 KM 245 Northbound Fast Lane Merging Zone",
                accident_image_url="https://images.unsplash.com/photo-1545178803-4056771d60a3?auto=format&fit=crop&w=1200&q=80",
                status=IncidentStatus.NOTIFIED, vehicle_count=2,
                vehicle_info={"vehicles": [{"type": "Heavy Commercial Truck", "color": "White", "speed_kmh": 68, "confidence": 0.96}, {"type": "SUV (Sedan Impact)", "color": "Silver", "speed_kmh": 82, "confidence": 0.93}], "total_vehicles": 2, "estimated_impact_speed_kmh": 75},
                ai_event_data={"model_version": "YOLO-v9-Accident-X", "processing_time_ms": 138, "collision_type": "Rear-End High Speed Collision", "fire_detected": False, "road_blockage": True},
                notification_started_at=now - timedelta(minutes=3),
                notification_count=3,
                notes="High severity crash detected. Fast lanes 1 and 2 blocked. Rapid response ambulance notification triggered.",
            ),
            Incident(
                id=inc2_id, incident_id="ACC-2026-10-08-002",
                camera_id=cam2_id, camera_external_id="CAM-NH44-KM112",
                detected_at=now - timedelta(minutes=20),
                accident_detected=True, severity=SeverityLevel.MEDIUM, confidence_score=0.88,
                latitude=28.7041, longitude=77.1025,
                location_description="NH-44 KM 112 Flyover Exit Ramp",
                accident_image_url="https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?auto=format&fit=crop&w=1200&q=80",
                status=IncidentStatus.ACKNOWLEDGED, vehicle_count=2,
                vehicle_info={"vehicles": [{"type": "Compact Car", "color": "Red", "speed_kmh": 45}, {"type": "Motorcycle", "color": "Black", "speed_kmh": 30}], "total_vehicles": 2},
                ai_event_data={"model_version": "YOLO-v9-Accident-X", "processing_time_ms": 142, "collision_type": "Side Swipe during ramp merge", "fire_detected": False, "road_blockage": False},
                notification_started_at=now - timedelta(minutes=18),
                notification_stopped_at=now - timedelta(minutes=12),
                notification_count=2,
                acknowledged_at=now - timedelta(minutes=12),
                acknowledged_by_hospital_id=hosp1_id,
                acknowledgment_details={"notes": "ALS Ambulance #04 Dispatched. ETA 6 minutes.", "responder_name": "Dr. Vivek Mehra (Chief EMT)"},
                notes="Hospital acknowledged and en route. Notifications automatically halted.",
            ),
            Incident(
                id=inc3_id, incident_id="ACC-2026-10-08-003",
                camera_id=cam3_id, camera_external_id="CAM-MEW-KM088",
                detected_at=now - timedelta(hours=1),
                accident_detected=True, severity=SeverityLevel.LOW, confidence_score=0.74,
                latitude=18.7562, longitude=73.3429,
                location_description="Mumbai-Pune Expressway Khandala Slope Curve 4",
                accident_image_url="https://images.unsplash.com/photo-1506521781263-d8422e82f27a?auto=format&fit=crop&w=1200&q=80",
                status=IncidentStatus.DETECTED, vehicle_count=1,
                vehicle_info={"vehicles": [{"type": "Commercial Van", "color": "White", "speed_kmh": 0}], "total_vehicles": 1},
                ai_event_data={"model_version": "YOLO-v9-Accident-X", "processing_time_ms": 155, "collision_type": "Shoulder Barrier Scraping / Stalled Vehicle", "fire_detected": False, "road_blockage": False},
                notification_count=0,
                notes="Potential low severity incident / stalled vehicle against guardrail. Requires operator visual verification.",
            ),
            Incident(
                id=inc4_id, incident_id="ACC-2026-10-07-009",
                camera_id=cam1_id, camera_external_id="CAM-NH48-KM245",
                detected_at=now - timedelta(days=1),
                accident_detected=True, severity=SeverityLevel.HIGH, confidence_score=0.96,
                latitude=28.4595, longitude=77.0266,
                location_description="NH-48 KM 245 Southbound Toll Corridor",
                accident_image_url="https://images.unsplash.com/photo-1545178803-4056771d60a3?auto=format&fit=crop&w=1200&q=80",
                status=IncidentStatus.RESOLVED, vehicle_count=3,
                vehicle_info={"vehicles": [{"type": "Bus", "color": "Blue"}, {"type": "Car", "color": "White"}], "total_vehicles": 3},
                ai_event_data={"collision_type": "Multi-vehicle pileup"},
                notification_count=4,
                acknowledged_at=now - timedelta(hours=23, minutes=37),
                acknowledged_by_hospital_id=hosp1_id,
                acknowledgment_details={"responder_name": "Dr. EMT On-Duty"},
                resolved_at=now - timedelta(hours=22, minutes=46),
                resolved_by=admin_id,
                resolution_notes="All 4 injured passengers stabilized and evacuated to Apex Trauma. Wreck cleared from highway by NHAI cranes. Normal traffic resumed.",
                notes="Incident successfully resolved with zero fatalities.",
            ),
        ]
        session.add_all(incidents)
        await session.flush()
        logger.info("Incidents created")
        
        # ─── Notifications ───
        notifications = [
            Notification(
                id=str(uuid.uuid4()),
                notification_id="NOTIF-2026-001-A",
                incident_id=inc1_id, hospital_id=hosp1_id,
                recipient_type=RecipientType.HOSPITAL,
                recipient_phone="+919876543201",
                recipient_email="emergency@apextrauma.org",
                recipient_name="Apex Trauma Emergency Desk",
                notification_type=NotificationType.SMS,
                status=NotificationStatus.DELIVERED,
                message="[EMERGENCY ALERT] Severe Accident detected at NH-48 KM 245 Northbound. 2 vehicles involved. Coordinates: 28.4595, 77.0266. Please dispatch emergency response.",
                sent_at=now - timedelta(minutes=3),
                delivered_at=now - timedelta(minutes=2, seconds=56),
                retry_count=0, is_repeat=False, repeat_sequence=1,
                created_by=None,
            ),
            Notification(
                id=str(uuid.uuid4()),
                notification_id="NOTIF-2026-001-B",
                incident_id=inc1_id, hospital_id=hosp1_id,
                recipient_type=RecipientType.HOSPITAL,
                recipient_phone="+919876543201",
                recipient_name="Apex Trauma Emergency Desk",
                notification_type=NotificationType.SMS,
                status=NotificationStatus.DELIVERED,
                message="[REPEAT ALERT 2/10] Severe Accident awaiting acknowledgment at NH-48 KM 245. High Priority.",
                sent_at=now - timedelta(minutes=2),
                delivered_at=now - timedelta(minutes=1, seconds=57),
                retry_count=1, is_repeat=True, repeat_sequence=2,
                created_by=None,
            ),
            Notification(
                id=str(uuid.uuid4()),
                notification_id="NOTIF-2026-001-C",
                incident_id=inc1_id, hospital_id=hosp2_id,
                recipient_type=RecipientType.HOSPITAL,
                recipient_phone="+919876543202",
                recipient_name="Metro City Government Emergency",
                notification_type=NotificationType.SMS,
                status=NotificationStatus.SENT,
                message="[EMERGENCY ALERT 3/10] High severity accident NH-48 KM 245. Response required immediately.",
                sent_at=now - timedelta(minutes=1),
                retry_count=2, is_repeat=True, repeat_sequence=3,
                created_by=None,
            ),
        ]
        session.add_all(notifications)
        await session.flush()
        logger.info("Notifications created")
        
        # ─── Audit Logs ───
        audit_logs = [
            AuditLog(
                id=str(uuid.uuid4()), user_id=admin_id, username="admin",
                action="UPDATE_SETTINGS", resource_type="admin_setting",
                endpoint="/api/v1/admin/settings", method="PATCH",
                ip_address="192.168.1.10", success="true",
                description="Updated notification repeat interval to 60 seconds",
            ),
            AuditLog(
                id=str(uuid.uuid4()), user_id=operator_id, username="operator",
                action="INCIDENT_VERIFIED", resource_type="incident",
                resource_id=inc1_id, endpoint=f"/api/v1/incidents/{inc1_id}/verify",
                method="POST", ip_address="192.168.1.15", success="true",
                description="Confirmed high severity collision on NH-48 KM 245",
            ),
            AuditLog(
                id=str(uuid.uuid4()), user_id=None, username="system",
                action="NOTIFICATION_DISPATCH", resource_type="notification",
                endpoint="/api/v1/notifications/manual",
                method="POST", ip_address="127.0.0.1", success="true",
                description="Automated SMS dispatched to Apex Trauma Hospital (+919876543201)",
            ),
        ]
        session.add_all(audit_logs)
        
        await session.commit()
        logger.info("All seed data committed successfully")
    
    await engine.dispose()
    
    print("\n" + "="*60)
    print("SUCCESS: DATABASE SEEDED SUCCESSFULLY!")
    print("="*60)
    print(f"  Users:         3  (admin, operator, viewer)")
    print(f"  Cameras:       6  (3 monitoring, 2 online, 1 offline)")
    print(f"  Hospitals:     4  (all active)")
    print(f"  Incidents:     4  (high/medium/low severity, various states)")
    print(f"  Notifications: 3  (delivered/sent)")
    print(f"  Audit Logs:    3")
    print("="*60)
    print(f"\nAdmin credentials:")
    print(f"  Username: admin")
    print(f"  Password: {settings.DEFAULT_ADMIN_PASSWORD}")
    print(f"\nOther users:")
    print(f"  operator / Operator123!")
    print(f"  viewer   / Viewer123!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(seed_database())
