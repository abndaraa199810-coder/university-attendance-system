from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
import hashlib, hmac, os
from cryptography.fernet import Fernet
from django.shortcuts import redirect



FERNET_KEY_RAW = os.environ.get("FERNET_KEY")
HMAC_SECRET_RAW = os.environ.get("HMAC_SECRET", "")

HMAC_SECRET = (HMAC_SECRET_RAW or "").encode("utf-8")


def get_fernet():

    if not FERNET_KEY_RAW:
        return None
    try:
        return Fernet(FERNET_KEY_RAW.encode("utf-8"))
    except Exception:
        return None



def encrypt_text(text: str):
    f = get_fernet()
    if not text or not f:
        return text
    return f.encrypt(text.encode()).decode()


def decrypt_text(token: str):
    f = get_fernet()
    if not token or not f:
        return token
    return f.decrypt(token.encode()).decode()


def hmac_signature(payload: str):
    return hmac.new(
        HMAC_SECRET,
        payload.encode(),
        hashlib.sha256
    ).hexdigest()


class User(AbstractUser):
    full_name = models.CharField(max_length=255, blank=True, null=True)

    role = models.CharField(
        max_length=20,
        choices=[
            ("student", "Student"),
            ("teacher", "Teacher"),
            ("admin", "Admin"),
        ],
        default="student",
    )

    def __str__(self):
        return self.username



class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=255)
    role = models.CharField(
        max_length=20,
        choices=[("admin", "Admin"), ("student", "Student")]
    )

    def __str__(self):
        return self.full_name




class Student(models.Model):
    student_id = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=255)

    photo = models.ImageField(upload_to="students/", null=True, blank=True)
    face_encoding = models.BinaryField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_id} - {self.full_name}"

    @property
    def has_face(self):
        return self.face_encoding is not None



class Room(models.Model):
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=60, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class RoomAccess(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    allowed = models.BooleanField(default=True)
    allowed_from = models.TimeField(null=True, blank=True)
    allowed_to = models.TimeField(null=True, blank=True)

    class Meta:
        unique_together = ("student", "room")



class Attendance(models.Model):
    STATUS_CHOICES = [
        ("IN", "Check In"),
        ("OUT", "Check Out"),
        ("FORBIDDEN", "Unauthorized"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES)
    device = models.CharField(max_length=150, default="laptop-camera")
    confidence = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)])
    signature = models.CharField(max_length=128, null=True, blank=True)

    def save(self, *args, **kwargs):
        room_id = self.room.id if self.room else "NONE"
        payload = f"{self.student.id}|{room_id}|{self.timestamp.isoformat()}|{self.status}|{self.confidence}"
        self.signature = hmac_signature(payload)
        super().save(*args, **kwargs)




class AuditLog(models.Model):
    action = models.CharField(max_length=150)
    username = models.CharField(max_length=150, null=True, blank=True)
    ip_address = models.CharField(max_length=100, null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    data = models.JSONField(null=True, blank=True)
    signature = models.CharField(max_length=128, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        payload = f"{self.action}|{self.username}|{self.ip_address}|{self.created_at}"
        self.signature = hmac_signature(payload)
        super().save(*args, **kwargs)




class AttendanceBackup(models.Model):
    original_attendance_id = models.IntegerField()
    student_id = models.CharField(max_length=50)
    status = models.CharField(max_length=10)
    confidence = models.FloatField()
    timestamp = models.DateTimeField()
    backup_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Backup Attendance {self.original_attendance_id}"






class Course(models.Model):
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.code} - {self.name}"



class CourseSession(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    room = models.ForeignKey("Room", on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.course.code} | {self.room.code}"


class Enrollment(models.Model):
    student = models.ForeignKey("Student", on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("student", "course")
