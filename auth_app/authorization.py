# auth_app/authorization.py

from django.utils import timezone
from .models import RoomAccess

def authorize_student(student, room):
    """
    Authorization based on Room Access Control (ACL):
    - Student must have RoomAccess.allowed=True for the given room.
    - Optional time window: allowed_from / allowed_to.
    """

    if not room:
        return False, "NO_ROOM"

    now = timezone.localtime().time()

    access = RoomAccess.objects.filter(student=student, room=room).first()

    if not access:
        return False, "NO_ROOM_ACCESS_RECORD"

    if not access.allowed:
        return False, "ROOM_ACCESS_DENIED"

    # Optional time window checks
    if access.allowed_from and now < access.allowed_from:
        return False, "BEFORE_ALLOWED_TIME"

    if access.allowed_to and now > access.allowed_to:
        return False, "AFTER_ALLOWED_TIME"

    return True, "AUTHORIZED"
