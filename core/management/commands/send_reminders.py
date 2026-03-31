"""
Send periodic reminder emails to registered attendees before events begin.

Usage:
    python manage.py send_reminders          # run once
    python manage.py send_reminders --loop   # run every 15 minutes (for Docker)
"""
import time
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Event, EventReminder

User = get_user_model()
logger = logging.getLogger(__name__)

LOOP_INTERVAL = 15 * 60  # 15 minutes


class Command(BaseCommand):
    help = 'Send reminder emails for upcoming events'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loop',
            action='store_true',
            help='Run continuously every 15 minutes (for Docker/daemon use)',
        )

    def handle(self, *args, **options):
        if options['loop']:
            self.stdout.write('Reminder worker started (every 15 min)')
            while True:
                self._send_reminders()
                time.sleep(LOOP_INTERVAL)
        else:
            self._send_reminders()

    def _send_reminders(self):
        now = timezone.now()
        windows = getattr(settings, 'REMINDER_WINDOWS', [24, 1])
        sent_count = 0

        for hours in windows:
            cutoff = now + timezone.timedelta(hours=hours)
            events = Event.objects.filter(
                start_time__gt=now,
                start_time__lte=cutoff,
            ).exclude(
                reminders__hours_before=hours,
            )

            for event in events:
                attendees = User.objects.filter(
                    person__tickets__event=event,
                ).distinct()
                recipient_list = [u.email for u in attendees if u.email]

                if not recipient_list:
                    EventReminder.objects.create(event=event, hours_before=hours)
                    continue

                if hours >= 24:
                    time_label = f"{hours // 24} day{'s' if hours >= 48 else ''}"
                else:
                    time_label = f"{hours} hour{'s' if hours != 1 else ''}"

                subject = f"Reminder: {event.name} starts in {time_label}"
                message = (
                    f"This is a reminder that {event.name} starts in {time_label}.\n\n"
                    f"When: {event.start_time.strftime('%A, %b %d at %I:%M %p')}\n"
                    f"Where: {event.location or 'TBD'}\n\n"
                    f"See you there!"
                )

                try:
                    send_mail(subject, message, None, recipient_list)
                    EventReminder.objects.create(event=event, hours_before=hours)
                    sent_count += 1
                    self.stdout.write(f"  Sent {hours}h reminder for {event.name} to {len(recipient_list)} attendees")
                except Exception:
                    logger.exception("Failed to send %dh reminder for %s", hours, event.name)

        if sent_count:
            self.stdout.write(self.style.SUCCESS(f"Sent {sent_count} reminder(s)"))