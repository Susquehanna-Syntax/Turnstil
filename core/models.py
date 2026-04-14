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
from django.core.exceptions import ValidationError


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
    notification_preferences = models.JSONField(
        default=dict, blank=True,
        help_text='Notification settings, e.g. {"event_reminders": true, "event_updates": true, "new_events": true}'
    )
    avatar = models.TextField(blank=True, default='', help_text='Base64-encoded profile image data URI')

    CARD_COLORS = [
        ('rose', 'Rose'),
        ('lavender', 'Lavender'),
        ('mint', 'Mint'),
        ('peach', 'Peach'),
        ('sky', 'Sky'),
        ('lemon', 'Lemon'),
    ]
    card_color = models.CharField(max_length=20, choices=CARD_COLORS, default='peach', blank=True)

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
        # Normalise links — may be stored as a plain URL string or a dict
        links_value = self.links
        if isinstance(links_value, dict) and not links_value:
            links_value = ''  # treat empty dict as blank
        field_map = {
            'email': self.email,
            'organization': self.organization,
            'phone': self.phone,
            'links': links_value,
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

    @property
    def default_notification_preferences(self):
        return {
            'event_reminders': True,
            'event_updates': True,
            'new_events': True,
        }

    def get_notification_preferences(self):
        """Return notification preferences with defaults for any missing keys."""
        defaults = self.default_notification_preferences
        defaults.update(self.notification_preferences)
        return defaults

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
    reg_open = models.DateTimeField()
    reg_close = models.DateTimeField()
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
    allow_walkins = models.BooleanField(
        default=False,
        help_text='Allow check-in for people not pre-registered',
    )
    disable_gui_registration = models.BooleanField(
        default=False,
        help_text='Hide web registration button; only API/external registration allowed',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    external_link = models.URLField(blank=True, null=True)

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

    def save(self, *args, **kwargs):
        if self.reg_open is None:
            self.reg_open = timezone.now()
        if self.reg_close is None:
            self.reg_close = self.start_time

        self.full_clean()  # now validation sees proper values
        super().save(*args, **kwargs)

    def clean(self):
        errors = {}

        if self.reg_open and self.reg_close:
            if self.reg_open >= self.reg_close:
                errors['reg_close'] = 'Registration close must be after registration open.'

        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                errors['end_time'] = 'Event end time must be after start time.'

        if self.reg_close and self.start_time:
            if self.reg_close > self.start_time:
                errors['reg_close'] = 'Registration close must be on or before event start time.'

        if self.reg_open and self.end_time:
            if self.reg_open >= self.end_time:
                errors['reg_open'] = 'Registration open must be before event end time.'

        if errors:
            raise ValidationError(errors)

    def registration_is_open(self):
        now = timezone.now()
        return self.reg_open <= now <= self.reg_close


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


class EventReminder(models.Model):
    """Tracks which reminder emails have been sent for each event."""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reminders')
    hours_before = models.PositiveIntegerField(help_text='Reminder window in hours before start')
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['event', 'hours_before']

    def __str__(self):
        return f"{self.event.name} — {self.hours_before}h reminder"


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
    
    @property
    def result_display(self):
        labels = {
            self.Result.SUCCESS: 'Success',
            self.Result.DUPLICATE: 'Duplicate',
            self.Result.NOT_REGISTERED: 'Not Registered',
            self.Result.INVALID: 'Invalid',
            self.Result.WRONG_EVENT: 'Wrong Event',
            self.Result.EVENT_INACTIVE: 'Event Inactive',
        }
        return labels.get(self.result, self.result)


class EventPhoto(models.Model):
    """Up to 10 organizer-uploaded photos per event, stored as base64."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='photos')
    image_data = models.TextField(help_text='Base64-encoded image data URI')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_photos',
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'uploaded_at']

    def __str__(self):
        return f"Photo for {self.event.name} by {self.uploaded_by}"

    def clean(self):
        if not self.pk and self.event_id:
            count = EventPhoto.objects.filter(event_id=self.event_id).count()
            if count >= 10:
                raise ValidationError('An event may have at most 10 photos.')


class ScanConfirmation(models.Model):
    """
    Attendee-facing confirmation for a successful check-in scan.
    Shown as a popup on the attendee's device to prevent screenshot fraud.
    """

    class Response(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed — attendee said yes'
        DENIED = 'denied', 'Denied — attendee said no'
        EXPIRED = 'expired', 'Expired'

    scan_log = models.OneToOneField(
        ScanLog, on_delete=models.CASCADE, related_name='confirmation'
    )
    response = models.CharField(
        max_length=20, choices=Response.choices, default=Response.PENDING
    )
    responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Confirmation for {self.scan_log} — {self.response}"


class ScannedContact(models.Model):
    """Records when a person scans another person's QR in Discovery mode."""
    scanner = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name='scanned_contacts'
    )
    scanned = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name='scanned_by'
    )
    scanned_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['scanner', 'scanned']
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.scanner.name} → {self.scanned.name}"
