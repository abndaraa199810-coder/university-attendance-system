from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Student, Room, RoomAccess, Attendance

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ["username", "email", "full_name", "role", "password"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = "__all__"
        read_only_fields = ["face_embedding"]


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = "__all__"


class RoomAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomAccess
        fields = "__all__"


class AttendanceSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    room = RoomSerializer(read_only=True)
    class Meta:
        model = Attendance
        fields = "__all__"
        read_only_fields = ["id", "timestamp"]
