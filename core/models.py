"""
Turnstil core models.

Person-centric identity: each user gets ONE persistent UUID/QR code
that works across all events for both check-in and networking.
"""
import uuid
import io

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """Extended user with role-based access."""

    class Role(models.TextChoices):
        ATTENDEE = 'attendee', 'Attendee'
        STAFF = 'staff', 'Staff'
        ORGANIZER = 'organizer', 'Organizer'
        ADMIN = 'admin', 'Admin'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ATTENDEE,
    )

    def is_staff_or_above(self):
        return self.role in (self.Role.STAFF, self.Role.ORGANIZER, self.Role.ADMIN)

    def is_organizer_or_above(self):
        return self.role in (self.Role.ORGANIZER, self.Role.ADMIN)


class Person(models.Model):
    """
    Identity/profile model. The UUID here IS the QR code payload.
    Separated from User so auth concerns stay separate from identity.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='person',
    )
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    organization = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    links = models.JSONField(
        default=dict, blank=True,
        help_text='Social/web links, e.g. {"linkedin": "...", "github": "..."}'
    )
    visibility = models.JSONField(
        default=dict, blank=True,
        help_text='Which fields are public, e.g. {"email": true, "phone": false}'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'people'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.id})"

    def get_visible_contact(self):
        """Return only the fields the user has marked as visible."""
        contact = {'name': self.name}  # Name always visible
        field_map = {
            'email': self.email,
            'organization': self.organization,
            'phone': self.phone,
            'links': self.links,
        }
        for field, value in field_map.items():
            if self.visibility.get(field, False) and value:
                contact[field] = value
        return contact

    @property
    def default_visibility(self):
        return {
            'email': True,
            'organization': True,
            'phone': False,
            'links': True,
        }

    def generate_qr_code(self):
        """Generate QR code PNG as bytes. QR contains ONLY the UUID."""
        import qrcode
        from qrcode.image.styledpil import StyledPilImage
        from qrcode.image.styles.moduledrawers import RoundedModuleDrawer

        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(str(self.id))
        qr.make(fit=True)

        img = qr.make_image(fill_color='black', back_color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer.getvalue()


class Event(models.Model):
    """An event that people can register for and check into."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=300, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    capacity = models.PositiveIntegerField(default=0, help_text='0 = unlimited')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_events',
    )
    staff = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='staffed_events',
        help_text='Users who can scan for this event',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.name} ({self.start_time.strftime('%Y-%m-%d')})"

    @property
    def is_active(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time

    @property
    def is_upcoming(self):
        return timezone.now() < self.start_time

    @property
    def registration_count(self):
        return self.tickets.exclude(status=Ticket.Status.CANCELED).count()

    @property
    def checkin_count(self):
        return self.tickets.filter(status=Ticket.Status.CHECKED_IN).count()

    @property
    def is_full(self):
        if self.capacity == 0:
            return False
        return self.registration_count >= self.capacity


class Ticket(models.Model):
    """Links a Person to an Event. Tracks registration and check-in status."""

    class Status(models.TextChoices):
        ISSUED = 'issued', 'Issued'
        CHECKED_IN = 'checked_in', 'Checked In'
        CANCELED = 'canceled', 'Canceled'
        EXPIRED = 'expired', 'Expired'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='tickets')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tickets')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ISSUED,
    )
    issued_at = models.DateTimeField(auto_now_add=True)
    checked_in_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['person', 'event']
        ordering = ['-issued_at']

    def __str__(self):
        return f"{self.person.name} → {self.event.name} [{self.status}]"

    def check_in(self):
        """Mark ticket as checked in."""
        self.status = self.Status.CHECKED_IN
        self.checked_in_at = timezone.now()
        self.save(update_fields=['status', 'checked_in_at'])


class ScanLog(models.Model):
    """Audit trail for every scan attempt, successful or not."""

    class Result(models.TextChoices):
        SUCCESS = 'success', 'Success'
        DUPLICATE = 'duplicate', 'Duplicate Check-in'
        NOT_REGISTERED = 'not_registered', 'Not Registered'
        WRONG_EVENT = 'wrong_event', 'Wrong Event'
        INVALID = 'invalid', 'Invalid QR'
        EVENT_INACTIVE = 'event_inactive', 'Event Not Active'

    id = models.BigAutoField(primary_key=True)
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE,
        related_name='scan_logs', null=True,
    )
    person = models.ForeignKey(
        Person, on_delete=models.SET_NULL,
        null=True, related_name='scan_logs',
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='performed_scans',
        help_text='Staff member who performed the scan',
    )
    result = models.CharField(max_length=20, choices=Result.choices)
    scanned_value = models.CharField(
        max_length=200, blank=True,
        help_text='Raw value from QR code (for debugging invalid scans)',
    )
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        person_name = self.person.name if self.person else 'Unknown'
        return f"[{self.result}] {person_name} @ {self.timestamp:%H:%M:%S}"
