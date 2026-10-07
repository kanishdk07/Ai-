"""
Scheduler Service
Handles background job scheduling for repeat notifications
"""

from typing import Dict, Optional
from uuid import UUID
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.job import Job
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models import Incident, IncidentStatus
from app.services.incident_service import IncidentService
from app.services.notification_service import NotificationService
from app.services.hospital_service import HospitalService
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for managing notification scheduling"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.active_jobs: Dict[str, Job] = {}
        self._started = False

    def start(self):
        """Start the scheduler"""
        if not self._started:
            self.scheduler.start()
            self._started = True
            logger.info("Notification scheduler started")

    def shutdown(self):
        """Shutdown the scheduler"""
        if self._started:
            self.scheduler.shutdown()
            self._started = False
            logger.info("Notification scheduler shut down")

    async def schedule_incident_notifications(
        self,
        incident_id: UUID,
        interval_seconds: Optional[int] = None
    ) -> bool:
        """
        Schedule repeat notifications for an incident

        Args:
            incident_id: Incident UUID
            interval_seconds: Notification interval (defaults to settings)

        Returns:
            True if scheduled successfully
        """
        if not settings.AUTO_NOTIFICATION_ENABLED:
            logger.info("Auto notifications disabled, skipping scheduling")
            return False

        if interval_seconds is None:
            interval_seconds = settings.NOTIFICATION_INTERVAL_SECONDS

        # Validate interval
        if interval_seconds < settings.MIN_NOTIFICATION_INTERVAL:
            interval_seconds = settings.MIN_NOTIFICATION_INTERVAL
        elif interval_seconds > settings.MAX_NOTIFICATION_INTERVAL:
            interval_seconds = settings.MAX_NOTIFICATION_INTERVAL

        job_id = f"incident_{incident_id}"

        # Remove existing job if any
        if job_id in self.active_jobs:
            self.active_jobs[job_id].remove()
            del self.active_jobs[job_id]

        try:
            # Schedule repeat notifications
            job = self.scheduler.add_job(
                self._send_incident_notifications,
                trigger=IntervalTrigger(seconds=interval_seconds),
                args=[incident_id],
                id=job_id,
                replace_existing=True,
                max_instances=1,
                coalesce=True,  # Prevent overlapping executions
            )

            self.active_jobs[job_id] = job
            logger.info(f"Scheduled notifications for incident {incident_id} every {interval_seconds}s")
            return True

        except Exception as e:
            logger.error(f"Failed to schedule notifications for incident {incident_id}: {str(e)}")
            return False

    async def stop_incident_notifications(self, incident_id: UUID) -> bool:
        """
        Stop scheduled notifications for an incident

        Args:
            incident_id: Incident UUID

        Returns:
            True if stopped successfully
        """
        job_id = f"incident_{incident_id}"

        if job_id in self.active_jobs:
            try:
                self.active_jobs[job_id].remove()
                del self.active_jobs[job_id]
                logger.info(f"Stopped notifications for incident {incident_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to stop notifications for incident {incident_id}: {str(e)}")
                return False

        return False

    async def stop_all_notifications(self) -> int:
        """
        Stop all active notification jobs

        Returns:
            Number of jobs stopped
        """
        count = 0
        job_ids = list(self.active_jobs.keys())

        for job_id in job_ids:
            try:
                self.active_jobs[job_id].remove()
                del self.active_jobs[job_id]
                count += 1
            except Exception as e:
                logger.error(f"Failed to stop job {job_id}: {str(e)}")

        logger.info(f"Stopped {count} notification jobs")
        return count

    async def _send_incident_notifications(self, incident_id: UUID):
        """
        Background job to send notifications for an incident
        This is called repeatedly by the scheduler
        """
        async with AsyncSessionLocal() as db:
            try:
                # Get incident
                incident = await IncidentService.get_incident(db, incident_id)

                if not incident:
                    logger.warning(f"Incident {incident_id} not found, stopping notifications")
                    await self.stop_incident_notifications(incident_id)
                    return

                # Check if incident is still active
                if not incident.can_notify:
                    logger.info(f"Incident {incident_id} no longer active, stopping notifications")
                    await self.stop_incident_notifications(incident_id)
                    return

                # Check if acknowledged
                if incident.status == IncidentStatus.ACKNOWLEDGED:
                    logger.info(f"Incident {incident_id} acknowledged, stopping notifications")
                    await self.stop_incident_notifications(incident_id)
                    return

                # Check max retries
                if incident.notification_count >= settings.MAX_NOTIFICATION_RETRIES:
                    logger.warning(f"Incident {incident_id} reached max retries, stopping notifications")
                    await self.stop_incident_notifications(incident_id)
                    return

                # Check if in maintenance mode
                if settings.MAINTENANCE_MODE:
                    logger.info("System in maintenance mode, skipping notification")
                    return

                # Find nearby hospitals
                if not incident.latitude or not incident.longitude:
                    logger.error(f"Incident {incident_id} has no location, cannot find hospitals")
                    return

                nearby_hospitals = await HospitalService.find_nearby_hospitals(
                    db,
                    incident.latitude,
                    incident.longitude,
                    limit=settings.MAX_HOSPITALS_TO_NOTIFY
                )

                if not nearby_hospitals:
                    logger.warning(f"No hospitals found near incident {incident_id}")
                    return

                # Send notifications to hospitals
                repeat_sequence = incident.notification_count + 1

                for hospital_data in nearby_hospitals:
                    hospital_id = hospital_data['id']

                    # Create and send notification
                    notification = await NotificationService.create_notification(
                        db=db,
                        incident_id=incident_id,
                        hospital_id=hospital_id,
                        is_repeat=repeat_sequence > 1,
                        repeat_sequence=repeat_sequence,
                    )

                    await NotificationService.send_notification(db, notification.id)

                logger.info(f"Sent repeat notification #{repeat_sequence} for incident {incident_id} to {len(nearby_hospitals)} hospitals")

            except Exception as e:
                logger.error(f"Error sending notifications for incident {incident_id}: {str(e)}")

    def get_active_jobs_count(self) -> int:
        """Get count of active notification jobs"""
        return len(self.active_jobs)

    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self._started

    def get_job_info(self, incident_id: UUID) -> Optional[dict]:
        """Get information about a scheduled job"""
        job_id = f"incident_{incident_id}"
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            return {
                "job_id": job.id,
                "next_run_time": job.next_run_time,
                "trigger": str(job.trigger),
            }
        return None


# Global scheduler instance
scheduler_service = SchedulerService()


def get_scheduler() -> SchedulerService:
    """Get the global scheduler instance"""
    return scheduler_service
