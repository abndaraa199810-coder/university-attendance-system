from django.core.management.base import BaseCommand
from django.core import serializers
from auth_app.models import Attendance
from django.utils import timezone
import os

class Command(BaseCommand):
    help = "Create automatic backup for Attendance table"

    def handle(self, *args, **kwargs):
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = "backups"

        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        file_path = f"{backup_dir}/attendance_backup_{timestamp}.json"

        data = serializers.serialize("json", Attendance.objects.all())

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(data)

        self.stdout.write(
            self.style.SUCCESS(f"Attendance backup created successfully: {file_path}")
        )
