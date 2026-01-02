from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Attendance, AttendanceBackup, AuditLog


@receiver(post_save, sender=Attendance)
def backup_and_audit_attendance(sender, instance, created, **kwargs):
    if not created:
        return

  
    AttendanceBackup.objects.create(
        original_attendance_id=instance.id,
        student_id=instance.student.student_id,
        status=instance.status,
        confidence=instance.confidence,
        timestamp=instance.timestamp
    )

   
    AuditLog.objects.create(
        action="ATTENDANCE_BACKUP_CREATED",
        username=instance.student.student_id,
        ip_address="127.0.0.1",
        user_agent="FACE_SYSTEM",
        data={
            "attendance_id": instance.id,
            "backup_time": timezone.now().isoformat()
        }
    )
