import base64
import json
import logging

import cv2
import numpy as np

from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model
from rest_framework.decorators import api_view, permission_classes

from .models import Student, Room, Attendance
from .serializers import RegisterSerializer, LoginSerializer
from .authorization import authorize_student
from .accounting import log_attempt

try:
    from face_service.engine_onnx import ArcFaceONNX, cosine_similarity
except Exception:
    ArcFaceONNX = None
    cosine_similarity = None

logger = logging.getLogger(__name__)
User = get_user_model()



MODEL_PATH = getattr(settings, "ARCFACE_MODEL_PATH", "")
_ARCFACE = None

def get_arcface():
    global _ARCFACE

    if _ARCFACE is not None:
        return _ARCFACE

    if not ArcFaceONNX:
        logger.warning("ArcFaceONNX not available (import failed).")
        return None

    if not MODEL_PATH:
        logger.warning("ARCFACE_MODEL_PATH not set.")
        return None

    try:
        _ARCFACE = ArcFaceONNX(MODEL_PATH)
        logger.info("ArcFace model loaded from %s", MODEL_PATH)
        return _ARCFACE
    except Exception as e:
        logger.error("ArcFace load failed: %s", repr(e))
        return None



def require_device_key(request, action_name="DEVICE_CHECK"):
 
    required_key = getattr(settings, "DEVICE_KEY", "")
    if not required_key:
        return True   

    sent_key = request.headers.get("X-DEVICE-KEY") or request.META.get("HTTP_X_DEVICE_KEY") or ""
    if sent_key.strip() != str(required_key).strip():
        log_attempt(request, f"{action_name}_FAILED", {"reason": "BAD_DEVICE_KEY"})
        return False

    return True



class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            log_attempt(request, "REGISTER_SUCCESS", {"username": user.username})
            return Response(serializer.data, status=201)

        log_attempt(request, "REGISTER_FAILED", serializer.errors)
        return Response(serializer.errors, status=400)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if not user:
            log_attempt(request, "LOGIN_FAILED", {"username": username})
            return Response({"error": "Invalid credentials"}, status=401)

        token, _ = Token.objects.get_or_create(user=user)
        log_attempt(request, "LOGIN_SUCCESS", {"username": username})
        return Response({"token": token.key})



@csrf_exempt
def enroll_face(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST only"}, status=405)

    if not require_device_key(request, "ENROLL"):
        return JsonResponse({"success": False, "error": "Unauthorized device"}, status=401)

    arc = get_arcface()
    if arc is None:
        return JsonResponse({"success": False, "error": "ArcFace model not loaded"}, status=500)

    try:
        data = json.loads(request.body.decode("utf-8"))
        image_data = data.get("image")
        student_id = data.get("student_id")
        full_name = data.get("full_name")
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    if not image_data or not student_id or not full_name:
        return JsonResponse({"success": False, "error": "Missing data"}, status=400)

   
    try:
        header, encoded = image_data.split(",", 1)
        img_bytes = base64.b64decode(encoded)
        np_img = np.frombuffer(img_bytes, np.uint8)
        bgr = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError("Invalid image")
    except Exception:
        return JsonResponse({"success": False, "error": "Bad image format"}, status=400)

   
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

   
    try:
        embedding = arc.embed_from_rgb(rgb)
    except Exception as e:
        log_attempt(request, "ENROLL_FAILED", {"reason": "NO_FACE", "error": repr(e)})
        return JsonResponse({"success": False, "error": "No face detected"}, status=200)

    student, created = Student.objects.update_or_create(
        student_id=student_id,
        defaults={
            "full_name": full_name,
            "face_encoding": embedding.tobytes(),
        }
    )

    log_attempt(request, "ENROLL_SUCCESS", {
        "student_id": student.student_id,
        "name": student.full_name,
        "created": created
    })

    return JsonResponse({
        "success": True,
        "student_id": student.student_id,
        "full_name": student.full_name,
        "message": "Student enrolled successfully"
    })


@csrf_exempt
def verify(request):
    if request.method != "POST":
        return JsonResponse({"matched": False, "error": "POST only"}, status=405)

    if not require_device_key(request, "VERIFY"):
        return JsonResponse({"matched": False, "error": "Unauthorized device"}, status=401)

    arc = get_arcface()
    if arc is None:
        return JsonResponse({"matched": False, "error": "ArcFace model not loaded"}, status=500)

    try:
        data = json.loads(request.body.decode("utf-8"))
        image_data = data.get("image")
        room_code = (data.get("room_code") or "").strip()
    except Exception:
        return JsonResponse({"matched": False, "error": "Invalid JSON"}, status=400)

    if not image_data:
        log_attempt(request, "VERIFY_FAILED", {"reason": "NO_IMAGE"})
        return JsonResponse({"matched": False, "error": "No image"}, status=400)

    if not room_code:
        log_attempt(request, "VERIFY_FAILED", {"reason": "NO_ROOM_CODE"})
        return JsonResponse({"matched": False, "error": "room_code required"}, status=400)

    room = Room.objects.filter(code=room_code).first()
    if not room:
        log_attempt(request, "VERIFY_FAILED", {"reason": "INVALID_ROOM", "room_code": room_code})
        return JsonResponse({"matched": False, "error": "Invalid room"}, status=400)

    # decode image
    try:
        header, encoded = image_data.split(",", 1)
        img_bytes = base64.b64decode(encoded)
        np_img = np.frombuffer(img_bytes, np.uint8)
        bgr = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
        if bgr is None:
            return JsonResponse({"matched": False, "error": "Invalid image"}, status=400)
    except Exception:
        return JsonResponse({"matched": False, "error": "Bad image format"}, status=400)

    # probe embedding
    try:
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)   # مهم جداً
        probe = arc.embed_from_rgb(rgb)              # الدالة الصحيحة داخل ArcFaceONNX
    except Exception as e:
       log_attempt(request, "VERIFY_EMBED_FAIL", {"error": repr(e)})
       return JsonResponse({"matched": False, "error": f"Embedding failed: {repr(e)}"}, status=200)

    if probe is None:
        log_attempt(request, "AUTH_FAILED", {"reason": "NO_FACE"})
        return JsonResponse({"matched": False, "error": "No face detected"}, status=200)


    best_student = None
    best_score = -1.0

    for student in Student.objects.exclude(face_encoding__isnull=True):
        known = np.frombuffer(student.face_encoding, dtype=np.float32)
        if known.size == 0:
            continue

        if cosine_similarity:
            score = float(cosine_similarity(probe, known))
        else:
            # fallback بسيط
            score = float(np.dot(probe, known))

        if score > best_score:
            best_score = score
            best_student = student

    threshold = float(getattr(settings, "FACE_MATCH_THRESHOLD", 0.35))

    if best_student and best_score >= threshold:
        is_allowed, reason = authorize_student(best_student, room)
        status_att = "IN" if is_allowed else "FORBIDDEN"

        Attendance.objects.create(
            student=best_student,
            room=room,
            status=status_att,
            confidence=float(best_score),
        )

        log_attempt(request, "FACE_VERIFICATION", {
            "student_id": best_student.student_id,
            "student_name": best_student.full_name,
            "room": room.code,
            "authorized": is_allowed,
            "authorization_reason": reason,
            "confidence": float(best_score),
            "threshold": threshold,
        })

        return JsonResponse({
            "matched": True,
            "authorized": is_allowed,
            "student_id": best_student.student_id,
            "full_name": best_student.full_name,
            "room": room.code,
            "time": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            "confidence": round(float(best_score), 3),
            "status": status_att,
            "reason": reason,
        })

    log_attempt(request, "AUTHENTICATION_FAILED", {
        "reason": "FACE_NOT_MATCHED",
        "room": room_code,
        "best_score": float(best_score),
        "threshold": threshold
    })
    return JsonResponse({"matched": False, "error": "Face not matched"}, status=200)


@api_view(["GET"])
@permission_classes([AllowAny])
def attendance_api(request):
    qname = request.GET.get("q", "").strip()
    status_q = request.GET.get("status", "").strip()

    logs = Attendance.objects.all().select_related("student", "room")

    if qname:
        logs = logs.filter(
            Q(student__full_name__icontains=qname) |
            Q(student__student_id__icontains=qname)
        )

    if status_q:
        logs = logs.filter(status=status_q)

    data = [
        {
            "timestamp": log.timestamp,
            "student_name": log.student.full_name if log.student else None,
            "student_id": log.student.student_id if log.student else None,
            "room_code": log.room.code if log.room else None,
            "room_name": log.room.name if log.room else None,
            "status": log.status,
            "confidence": float(log.confidence),
        }
        for log in logs.order_by("-timestamp")[:200]
    ]
    return JsonResponse(data, safe=False)


def face_page(request):
    return render(request, "auth_app/face.html")


def attendance_page(request):
    return render(request, "auth_app/attendance.html")


def dashboard_page(request):
    return render(request, "auth_app/dashboard.html")


def enroll_page(request):
    return render(request, "auth_app/enroll.html", {
        "DEVICE_KEY": getattr(settings, "DEVICE_KEY", "")
    })


def verify_page(request):
    rooms = Room.objects.all()
    return render(request, "auth_app/verify.html", {
        "rooms": rooms,
        "DEVICE_KEY": getattr(settings, "DEVICE_KEY", "")
    })


def attendance_result(request):
    context = {
        "student_id": request.GET.get("student_id"),
        "full_name": request.GET.get("full_name"),
        "time": request.GET.get("time"),
    }
    return render(request, "auth_app/attendance_result.html", context)
