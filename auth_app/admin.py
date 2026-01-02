# auth_app/admin.py
from django.contrib import admin
from .models import (
    User,
    Profile,
    Student,
    Room,
    RoomAccess,
    Attendance,
    AttendanceBackup,
    AuditLog,
    Course,
    CourseSession,
    Enrollment,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "full_name", "role", "is_staff")
    search_fields = ("username", "full_name")
    list_filter = ("role",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "role")
    search_fields = ("full_name",)



@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "full_name", "has_face", "created_at")
    search_fields = ("student_id", "full_name")
    list_filter = ("created_at",)



@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


@admin.register(RoomAccess)
class RoomAccessAdmin(admin.ModelAdmin):
    list_display = ("student", "room", "allowed", "allowed_from", "allowed_to")
    list_filter = ("allowed",)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("student", "room", "status", "confidence", "timestamp")
    list_filter = ("status", "room")
    search_fields = ("student__student_id", "student__full_name")
    readonly_fields = ("signature",)


@admin.register(AttendanceBackup)
class AttendanceBackupAdmin(admin.ModelAdmin):
    list_display = ("original_attendance_id", "student_id", "status", "backup_time")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "username", "ip_address", "created_at")
    search_fields = ("action", "username")
    readonly_fields = ("signature",)



@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


@admin.register(CourseSession)
class CourseSessionAdmin(admin.ModelAdmin):
    list_display = ("course", "room", "start_time", "end_time")
    list_filter = ("room",)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course")
