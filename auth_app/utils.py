# auth_app/utils.py
import base64
import os
from django.conf import settings
from cryptography.fernet import Fernet, InvalidToken
import hmac, hashlib, json

# استخدم متغير بيئة أو إعداد في settings.py
# إذا لم يكن موجودًا نولّد مفتاح مؤقت (غير مناسب للإنتاج)
FERNET_KEY = getattr(settings, "FERNET_KEY", None)
if not FERNET_KEY:
    # لا تنشئ هذا في production — احفظ FERNET_KEY في env أو .env
    FERNET_KEY = base64.urlsafe_b64encode(hashlib.sha256(str(settings.SECRET_KEY).encode()).digest())

fernet = Fernet(FERNET_KEY)

def encrypt_text(plain: str) -> str:
    if plain is None:
        return None
    token = fernet.encrypt(plain.encode("utf-8"))
    return token.decode("utf-8")

def decrypt_text(token: str) -> str:
    if token is None:
        return None
    try:
        return fernet.decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return None

# HMAC signing for attendance/audit
AUDIT_SECRET = getattr(settings, "AUDIT_SECRET_KEY", None)
if AUDIT_SECRET and isinstance(AUDIT_SECRET, str):
    AUDIT_SECRET = AUDIT_SECRET.encode("utf-8")

def hmac_signature(msg: str) -> str:
    key = AUDIT_SECRET or str(settings.SECRET_KEY).encode("utf-8")
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).hexdigest()

def sign_dict(d: dict) -> str:
    s = json.dumps(d, sort_keys=True, default=str)
    return hmac_signature(s)
