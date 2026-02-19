"""
Turnstil API serializers.
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Person, Event, Ticket, ScanLog

User = get_user_model()


# ── Auth ──────────────────────────────────────────────────────────

class RegisterSerializer(serializers.Serializer):
    """Creates User + Person in one shot."""
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    name = serializers.CharField(max_length=200)
    organization = serializers.CharField(max_length=200, required=False, default='')

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Username already taken.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already registered.')
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        person = Person.objects.create(
            user=user,
            name=validated_data['name'],
            email=validated_data['email'],
            organization=validated_data.get('organization', ''),
            visibility=Person().default_visibility,
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    person_uuid = serializers.UUIDField(source='person.id', read_only=True)
    person_name = serializers.CharField(source='person.name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'person_uuid', 'person_name']
        read_only_fields = ['id', 'role']


# ── Person ────────────────────────────────────────────────────────

class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = [
            'id', 'name', 'email', 'organization', 'phone',
            'links', 'visibility', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PersonContactSerializer(serializers.Serializer):
    """Read-only serializer that respects visibility settings."""
    name = serializers.CharField()
    email = serializers.EmailField(required=False)
    organization = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    links = serializers.JSONField(required=False)


class ContactUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ['name', 'email', 'organization', 'phone', 'links', 'visibility']


# ── Event ─────────────────────────────────────────────────────────

class EventSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(
        source='created_by.username', read_only=True
    )
    registration_count = serializers.IntegerField(read_only=True)
    checkin_count = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'name', 'description', 'location',
            'start_time', 'end_time', 'capacity',
            'created_by', 'created_by_name',
            'registration_count', 'checkin_count', 'is_full',
            'created_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at']


class EventCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['name', 'description', 'location', 'start_time', 'end_time', 'capacity']


# ── Ticket ────────────────────────────────────────────────────────

class TicketSerializer(serializers.ModelSerializer):
    person_name = serializers.CharField(source='person.name', read_only=True)
    event_name = serializers.CharField(source='event.name', read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id', 'person', 'event', 'status',
            'person_name', 'event_name',
            'issued_at', 'checked_in_at',
        ]
        read_only_fields = ['id', 'status', 'issued_at', 'checked_in_at']


# ── Check-in ─────────────────────────────────────────────────────

class CheckInSerializer(serializers.Serializer):
    person_uuid = serializers.UUIDField()
    event_uuid = serializers.UUIDField()


class CheckInResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    person_name = serializers.CharField(required=False)
    checked_in_at = serializers.DateTimeField(required=False)
    event_name = serializers.CharField(required=False)
    code = serializers.CharField(required=False)
    message = serializers.CharField(required=False)


# ── ScanLog ──────────────────────────────────────────────────────

class ScanLogSerializer(serializers.ModelSerializer):
    person_name = serializers.CharField(source='person.name', read_only=True)
    actor_name = serializers.CharField(source='actor.username', read_only=True)

    class Meta:
        model = ScanLog
        fields = [
            'id', 'event', 'person', 'person_name',
            'actor', 'actor_name', 'result',
            'scanned_value', 'metadata', 'timestamp',
        ]


# ── Staff Assignment ─────────────────────────────────────────────

class StaffAssignSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
