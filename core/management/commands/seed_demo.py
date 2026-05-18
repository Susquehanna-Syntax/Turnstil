"""
Seed the database with demo data for development/testing.
Usage: python manage.py seed_demo
"""
import base64
import io
import math
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import User, Person, Event, Ticket, ScannedContact, EventPhoto


# ── Pastel palette (matches CSS vars) ────────────────────────────────────────
COLORS = {
    'rose':     (242, 160, 184),
    'lavender': (186, 168, 232),
    'mint':     (126, 221, 181),
    'peach':    (240, 184, 136),
    'sky':      (130, 196, 238),
    'lemon':    (226, 212, 120),
}
BG_DARK = (28, 28, 33)


def _make_avatar(initial: str, color_name: str, size: int = 200) -> str:
    """Generate a square avatar PNG with a large initial on a pastel background."""
    from PIL import Image, ImageDraw, ImageFont

    bg = COLORS.get(color_name, COLORS['peach'])
    img = Image.new('RGB', (size, size), color=bg)
    draw = ImageDraw.Draw(img)

    # Subtle inner highlight
    for r in range(size // 2, 0, -20):
        alpha = int(30 * (r / (size / 2)))
        overlay = Image.new('RGBA', (size, size), (255, 255, 255, 0))
        od = ImageDraw.Draw(overlay)
        od.ellipse(
            (size // 2 - r, size // 4 - r, size // 2 + r, size // 4 + r),
            fill=(255, 255, 255, alpha)
        )
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)

    # Initial letter
    font_size = int(size * 0.52)
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', font_size)
    except OSError:
        font = ImageFont.load_default()

    text = initial.upper()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) // 2 - bbox[0]
    y = (size - th) // 2 - bbox[1]

    # Shadow
    draw.text((x + 3, y + 3), text, font=font, fill=(0, 0, 0, 40) if hasattr(Image, 'RGBA') else (20, 20, 20))
    # Letter in dark bg color
    draw.text((x, y), text, font=font, fill=BG_DARK)

    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=88)
    b64 = base64.b64encode(buf.getvalue()).decode('ascii')
    return f'data:image/jpeg;base64,{b64}'


def _make_event_photo(title: str, color_name: str, width: int = 800, height: int = 500) -> str:
    """Generate a banner-style event photo with a gradient and title text."""
    from PIL import Image, ImageDraw, ImageFont

    base = COLORS.get(color_name, COLORS['peach'])

    # Horizontal gradient: base color → slightly darker
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)

    r0, g0, b0 = base
    r1, g1, b1 = max(0, r0 - 60), max(0, g0 - 60), max(0, b0 - 60)

    for x in range(width):
        t = x / width
        r = int(r0 + (r1 - r0) * t)
        g = int(g0 + (g1 - g0) * t)
        b = int(b0 + (b1 - b0) * t)
        draw.line([(x, 0), (x, height)], fill=(r, g, b))

    # Decorative circles
    import random
    rng = random.Random(hash(title))
    for _ in range(8):
        cx = rng.randint(0, width)
        cy = rng.randint(0, height)
        rad = rng.randint(40, 160)
        alpha_val = rng.randint(15, 40)
        overlay = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        od = ImageDraw.Draw(overlay)
        od.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=(255, 255, 255, alpha_val))
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)

    # Title text
    try:
        font_lg = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 52)
        font_sm = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 24)
    except OSError:
        font_lg = ImageFont.load_default()
        font_sm = font_lg

    # Semi-transparent dark band at bottom
    band = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    bd.rectangle([(0, height - 120), (width, height)], fill=(0, 0, 0, 120))
    img = Image.alpha_composite(img.convert('RGBA'), band).convert('RGB')
    draw = ImageDraw.Draw(img)

    bbox = draw.textbbox((0, 0), title, font=font_lg)
    tw = bbox[2] - bbox[0]
    draw.text(((width - tw) // 2, height - 100), title, font=font_lg, fill=(255, 255, 255))
    sub = 'Susquehanna Syntax'
    bbox2 = draw.textbbox((0, 0), sub, font=font_sm)
    tw2 = bbox2[2] - bbox2[0]
    draw.text(((width - tw2) // 2, height - 40), sub, font=font_sm, fill=(255, 255, 255, 180))

    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode('ascii')
    return f'data:image/jpeg;base64,{b64}'


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
                'event_limit': 0,  # unlimited
            }
        )
        if created:
            admin.set_password('admin1234')
            admin.save()
            Person.objects.create(
                user=admin, name='Admin User',
                email='admin@turnstil.dev',
                card_color='lavender',
                avatar=_make_avatar('A', 'lavender'),
                visibility={'email': True, 'organization': True, 'phone': False, 'links': True},
            )
            self.stdout.write(self.style.SUCCESS('  Created admin (admin / admin1234)'))

        # ── Organizer ──
        organizer, created = User.objects.get_or_create(
            username='organizer',
            defaults={
                'email': 'org@turnstil.dev',
                'role': 'organizer',
                'event_limit': 25,
            }
        )
        if created:
            organizer.set_password('organize1234')
            organizer.save()
            Person.objects.create(
                user=organizer, name='Event Organizer',
                email='org@turnstil.dev', organization='Susquehanna Syntax',
                card_color='mint',
                avatar=_make_avatar('E', 'mint'),
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
                card_color='sky',
                avatar=_make_avatar('D', 'sky'),
                visibility={'email': True, 'organization': True, 'phone': False, 'links': True},
            )
            self.stdout.write(self.style.SUCCESS('  Created staff (staff / staff1234)'))

        # ── Demo Attendees ──
        attendees = []
        demo_people = [
            ('alice', 'Alice Johnson',   'alice@example.com', 'Penn State',      'rose'),
            ('bob',   'Bob Smith',       'bob@example.com',   'Acme Corp',        'peach'),
            ('carol', 'Carol Williams',  'carol@example.com', 'TechStart Inc',    'lavender'),
            ('dave',  'Dave Brown',      'dave@example.com',  'Penn State',       'mint'),
            ('eve',   'Eve Davis',       'eve@example.com',   'DataFlow Labs',    'lemon'),
        ]
        for username, name, email, org, color in demo_people:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': email, 'role': 'attendee'}
            )
            if created:
                user.set_password('attendee1234')
                user.save()
                Person.objects.create(
                    user=user, name=name, email=email, organization=org,
                    card_color=color,
                    avatar=_make_avatar(name[0], color),
                    visibility={'email': True, 'organization': True, 'phone': False, 'links': True},
                )
                self.stdout.write(f'  Created attendee: {username}')
            attendees.append(user)

        # ── Demo Events ──
        now = timezone.now()

        event1, e1_created = Event.objects.get_or_create(
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

        event2, e2_created = Event.objects.get_or_create(
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

        event3, e3_created = Event.objects.get_or_create(
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

        # ── Event photos ──
        photo_specs = [
            (event1, e1_created, [
                ('Spring Tech Meetup', 'mint',     'Opening night'),
                ('Spring Tech Meetup', 'sky',      'Lightning talks'),
                ('Spring Tech Meetup', 'lavender', 'Networking session'),
            ]),
            (event2, e2_created, [
                ('Hackathon Kickoff', 'peach',  'Kickoff presentation'),
                ('Hackathon Kickoff', 'rose',   'Team formation'),
                ('Hackathon Kickoff', 'lemon',  'Hacking in progress'),
                ('Hackathon Kickoff', 'mint',   'Demo day'),
            ]),
            (event3, e3_created, [
                ('Career Fair 2026', 'sky',      'Employer booths'),
                ('Career Fair 2026', 'lavender', 'Resume reviews'),
            ]),
        ]
        for event, was_created, specs in photo_specs:
            if was_created and not event.photos.exists():
                for i, (title, color, caption) in enumerate(specs):
                    self.stdout.write(f'  Generating photo: {caption}...')
                    EventPhoto.objects.create(
                        event=event,
                        image_data=_make_event_photo(title, color),
                        caption=caption,
                        uploaded_by=organizer,
                        order=i,
                    )

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

        # ── Demo scanned contacts ──
        alice = attendees[0].person
        bob   = attendees[1].person
        carol = attendees[2].person
        dave  = attendees[3].person
        eve   = attendees[4].person

        for scanner, scanned in [
            (alice, bob), (alice, carol), (alice, eve),
            (bob, alice), (bob, dave),
            (carol, alice), (carol, eve),
            (dave, bob), (dave, carol),
            (eve, alice),
        ]:
            ScannedContact.objects.get_or_create(scanner=scanner, scanned=scanned)

        self.stdout.write(self.style.SUCCESS('\nDemo data seeded successfully!'))
        self.stdout.write('\nAccounts:')
        self.stdout.write('  admin     / admin1234     (admin, unlimited events)')
        self.stdout.write('  organizer / organize1234  (organizer, 25 event limit)')
        self.stdout.write('  staff     / staff1234     (staff)')
        self.stdout.write('  alice..eve / attendee1234 (attendees)')
