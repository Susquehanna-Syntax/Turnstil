"""
Seed the database with demo data for development/testing.
Usage: python manage.py seed_demo
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import User, Person, Event, Ticket


class Command(BaseCommand):
    help = 'Seed database with demo users, events, and registrations'

    def handle(self, *args, **options):
        self.stdout.write('Seeding demo data...')

        # ── Admin User ──
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@turnstil.dev',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('admin1234')
            admin.save()
            Person.objects.create(
                user=admin, name='Admin User',
                email='admin@turnstil.dev',
                visibility={'email': True, 'organization': True, 'phone': False, 'links': True},
            )
            self.stdout.write(self.style.SUCCESS('  Created admin (admin / admin1234)'))

        # ── Organizer ──
        organizer, created = User.objects.get_or_create(
            username='organizer',
            defaults={
                'email': 'org@turnstil.dev',
                'role': 'organizer',
            }
        )
        if created:
            organizer.set_password('organize1234')
            organizer.save()
            Person.objects.create(
                user=organizer, name='Event Organizer',
                email='org@turnstil.dev', organization='Susquehanna Syntax',
                visibility={'email': True, 'organization': True, 'phone': False, 'links': True},
            )
            self.stdout.write(self.style.SUCCESS('  Created organizer (organizer / organize1234)'))

        # ── Staff ──
        staff, created = User.objects.get_or_create(
            username='staff',
            defaults={
                'email': 'staff@turnstil.dev',
                'role': 'staff',
            }
        )
        if created:
            staff.set_password('staff1234')
            staff.save()
            Person.objects.create(
                user=staff, name='Door Staff',
                email='staff@turnstil.dev',
                visibility={'email': True, 'organization': True, 'phone': False, 'links': True},
            )
            self.stdout.write(self.style.SUCCESS('  Created staff (staff / staff1234)'))

        # ── Demo Attendees ──
        attendees = []
        demo_people = [
            ('alice', 'Alice Johnson', 'alice@example.com', 'Penn State'),
            ('bob', 'Bob Smith', 'bob@example.com', 'Acme Corp'),
            ('carol', 'Carol Williams', 'carol@example.com', 'TechStart Inc'),
            ('dave', 'Dave Brown', 'dave@example.com', 'Penn State'),
            ('eve', 'Eve Davis', 'eve@example.com', 'DataFlow Labs'),
        ]
        for username, name, email, org in demo_people:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': email, 'role': 'attendee'}
            )
            if created:
                user.set_password('attendee1234')
                user.save()
                Person.objects.create(
                    user=user, name=name, email=email, organization=org,
                    visibility={'email': True, 'organization': True, 'phone': False, 'links': True},
                )
                self.stdout.write(f'  Created attendee: {username}')
            attendees.append(user)

        # ── Demo Events ──
        now = timezone.now()

        event1, _ = Event.objects.get_or_create(
            name='Spring Tech Meetup',
            defaults={
                'description': 'Monthly technology networking event featuring lightning talks and demos.',
                'location': 'Room 201, Science Building',
                'start_time': now + timedelta(hours=2),
                'end_time': now + timedelta(hours=5),
                'capacity': 50,
                'created_by': organizer,
            }
        )
        event1.staff.add(organizer, staff)

        event2, _ = Event.objects.get_or_create(
            name='Hackathon Kickoff',
            defaults={
                'description': '24-hour hackathon with prizes for best project.',
                'location': 'Innovation Hub',
                'start_time': now + timedelta(days=3),
                'end_time': now + timedelta(days=4),
                'capacity': 100,
                'created_by': organizer,
            }
        )
        event2.staff.add(organizer, staff)

        event3, _ = Event.objects.get_or_create(
            name='Career Fair 2026',
            defaults={
                'description': 'Annual career fair with 30+ employers.',
                'location': 'Gymnasium',
                'start_time': now + timedelta(days=14),
                'end_time': now + timedelta(days=14, hours=6),
                'capacity': 0,  # unlimited
                'created_by': organizer,
            }
        )
        event3.staff.add(organizer)

        # ── Register attendees ──
        for user in attendees:
            Ticket.objects.get_or_create(
                person=user.person, event=event1,
                defaults={'status': 'issued'}
            )
            Ticket.objects.get_or_create(
                person=user.person, event=event2,
                defaults={'status': 'issued'}
            )

        self.stdout.write(self.style.SUCCESS('\nDemo data seeded successfully!'))
        self.stdout.write('\nAccounts:')
        self.stdout.write('  admin     / admin1234     (admin)')
        self.stdout.write('  organizer / organize1234  (organizer)')
        self.stdout.write('  staff     / staff1234     (staff)')
        self.stdout.write('  alice..eve / attendee1234 (attendees)')
