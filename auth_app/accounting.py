from django.utils import timezone
from .models import AuditLog

def log_attempt(request, action, data=None):
    ip = request.META.get("REMOTE_ADDR")
    ua = request.META.get("HTTP_USER_AGENT", "")
    username = request.user.username if request.user.is_authenticated else None

    payload = {
        "action": action,
        "username": username,
        "ip": ip,
        "ua": ua,
        "time": timezone.now().isoformat(),
        "data": data or {}
    }

    # IMPORTANT: أنت عندك signature داخل AuditLog.save()
    # لكن created_at يتولد بعد الحفظ -> الأفضل نمرر time ونستخدمه في signature
    # الحل الأسهل: خزّن الوقت داخل data واستخدمه في payload (كما هنا)
    # واعتبر signature مجرد Tamper-evident على مستوى الـ action/log

    AuditLog.objects.create(
        action=action,
        username=username,
        ip_address=ip,
        user_agent=ua,
        data=payload
    )
