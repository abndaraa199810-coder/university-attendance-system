# project/settings.py (مُنقّح)
from pathlib import Path
from datetime import timedelta
import os
import environ

# ---------------------------
# Base / Env
# ---------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    # تعريف أنواع المتغيرات الافتراضية (اختياري)
    DEBUG=(bool, False),
)
# اقرأ .env مرة واحدة
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))
DEVICE_KEY = env("DEVICE_KEY", default="")
FACE_MATCH_THRESHOLD = float(env("FACE_MATCH_THRESHOLD", default=0.35))  # cosine similarity
ARCFACE_MODEL_PATH = env(
    "ARCFACE_MODEL_PATH",
    default=str(BASE_DIR / "face_service" / "arcface.onnx")
)


# ---------------------------
# Security / Secrets
# ---------------------------
SECRET_KEY = env("SECRET_KEY", default="django-insecure-dev-key")  # ضع في .env لقيم حقيقية
DEBUG = env("DEBUG")  # سيأخذ القيمة من .env أو False افتراضياً
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])

# التشفير / المفاتيح
FERNET_KEY_RAW = env("FERNET_KEY", default=None)  # حافظ على السلسلة في .env
FERNET_KEY = FERNET_KEY_RAW.encode("utf-8") if FERNET_KEY_RAW else None
HMAC_SECRET = env("HMAC_SECRET", default="")  # استخدم قيمة قوية في .env
SIEM_ENDPOINT = env("SIEM_ENDPOINT", default="")

# ---------------------------
# Installed apps / auth
# ---------------------------
INSTALLED_APPS = [
    # django builtins
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",


    # third-party
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt",

    # your apps
    "auth_app.apps.AuthAppConfig",
    "face_service",   # folder for face logic (إن وُجد)
]

AUTH_USER_MODEL = "auth_app.User"

# ---------------------------
# Middleware / Security flags
# ---------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# أثناء التطوير لا نفرِض HTTPS لأن runserver لا يدعم HTTPS محليًا
# نفعّل قواعد الأمان فقط في وضع الإنتاج (DEBUG=False)
if not DEBUG:
    # development safe defaults (temporary)
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
else:
    # مفاتح افتراضية أثناء التطوير
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
    SECURE_BROWSER_XSS_FILTER = False
    SECURE_CONTENT_TYPE_NOSNIFF = False

# ---------------------------
# URLs, templates, WSGI
# ---------------------------
ROOT_URLCONF = "project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # إذا لديك مجلد frontend/templates، أضفه هنا لسهولة التطوير
        "DIRS": [BASE_DIR / "frontend" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "project.wsgi.application"

# ---------------------------
# Database (use .env for credentials)
# ---------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
# ---------------------------
# REST Framework / JWT
# ---------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
}

# ---------------------------
# Media / Static
# ---------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "frontend" / "static", BASE_DIR / "auth_app" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"  # استخدم هذا عند deploy وجلب الملفات عبر collectstatic

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------
# Other settings
# ---------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LANGUAGE_CODE = "en-us"
TIME_ZONE = env("TIME_ZONE", default="UTC")
USE_I18N = True
USE_TZ = True

# Face recognition threshold (قابلة للتعديل)
FACE_MATCH_THRESHOLD = float(env("FACE_MATCH_THRESHOLD", default=0.6))

# ---------------------------
# Logging (مبدئي - ضع SIEM أو ملف إن احتجت)
# ---------------------------
LOG_LEVEL = env("LOG_LEVEL", default="INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
        # يمكنك إضافة FileHandler هنا لتخزين Audit logs في ملف
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
}

# ---------------------------
# Warnings / Notes for developer
# ---------------------------
# 1) ضع القيم الحقيقية في ملف .env في BASE_DIR:
#    SECRET_KEY=...
#    FERNET_KEY=...   (مثال: Fernet.generate_key().decode())
#    HMAC_SECRET=...
#    DB_NAME=...
#    DB_USER=...
#    DB_PASSWORD=...
#    DB_HOST=...
#    DB_PORT=...
#    DEBUG=True  (أثناء التطوير فقط)
#
# 2) أثناء التطوير استخدم runserver (http). تفعيل HTTPS مطلوب فقط عند النشر.
# 3) لا تنس تشغيل:
#    python manage.py migrate
#    python manage.py collectstatic  (عند النشر)
#
