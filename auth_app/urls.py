# auth_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # صفحات
    path("", views.dashboard_page, name="dashboard"),
    path("dashboard/", views.dashboard_page, name="dashboard_page"),
    path("enroll-page/", views.enroll_page, name="enroll_page"),
    path("verify-page/", views.verify_page, name="verify_page"),
    path("attendance/", views.attendance_page, name="attendance_page"),
    path("attendance-result/", views.attendance_result, name="attendance_result"),

    # APIs (مهم: المسارات اللي تستخدمها صفحات HTML)
    path("auth/enroll-face/", views.enroll_face, name="enroll_face"),  # ✅ هنا التعديل
    path("auth/verify/", views.verify, name="verify"),
    path("auth/attendance/", views.attendance_api, name="attendance_api"),

    # Auth API (لو تستخدمينها)
    path("api/register/", views.RegisterView.as_view(), name="register"),
    path("api/login/", views.LoginView.as_view(), name="login"),
]
