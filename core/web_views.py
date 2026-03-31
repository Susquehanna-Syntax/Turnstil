"""
Turnstil web views — server-rendered pages.
These handle the HTML interface; the API handles data operations.
"""
<<<<<<< HEAD
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import Person, Event, Ticket, ScanLog
from .serializers import RegisterSerializer
from .forms import EventForm
from datetime import datetime
from .serializers import EventCreateSerializer

=======
import logging
from datetime import datetime

from django.contrib import messages
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .forms import EventForm
from .models import Person, Event, Ticket, ScanLog
from .serializers import RegisterSerializer, EventCreateSerializer

logger = logging.getLogger(__name__)

User = get_user_model()
>>>>>>> 6489d758485c56fa294002f439ead7fee94f3161

def home(request):
    """Landing page with upcoming events."""
    events = Event.objects.filter(end_time__gte=timezone.now()).order_by('start_time')[:10]
    return render(request, 'public/home.html', {'events': events})


def register_page(request):
    if request.user.is_authenticated:
        return redirect('profile')

    errors = {}
    if request.method == 'POST':
        serializer = RegisterSerializer(data={
            'username': request.POST.get('username', ''),
            'email': request.POST.get('email', ''),
            'password': request.POST.get('password', ''),
            'name': request.POST.get('name', ''),
            'organization': request.POST.get('organization', ''),
        })
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)
            return redirect('profile')
        errors = serializer.errors

    return render(request, 'registration/register.html', {'errors': errors})


def login_page(request):
    if request.user.is_authenticated:
        return redirect('profile')

    error = None
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username', ''),
            password=request.POST.get('password', ''),
        )
        if user:
            login(request, user)
            if user.is_staff_or_above():
                return redirect('scanner')
            next_url = request.GET.get('next', 'profile')
            return redirect(next_url)
        error = 'Invalid username or password.'

    return render(request, 'registration/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def profile_page(request):
    person = request.user.person
    tickets = Ticket.objects.filter(person=person).select_related('event')

    if request.method == 'POST':
        # Handle profile updates
        person.name = request.POST.get('name', person.name)
        person.email = request.POST.get('email', person.email)
        person.organization = request.POST.get('organization', person.organization)
        person.phone = request.POST.get('phone', person.phone)
        person.links = request.POST.get('links', person.links)

        # Handle visibility toggles
        visibility = {}
        for field in ['email', 'organization', 'phone', 'links']:
            visibility[field] = request.POST.get(f'vis_{field}') == 'on'
        person.visibility = visibility
        person.save()

    return render(request, 'public/profile.html', {
        'person': person,
        'tickets': tickets,
    })


@login_required
def qr_display(request):
    person = request.user.person
    return render(request, 'public/qr_display.html', {'person': person})


def _get_active_event(request):
    """Helper function for scanner page"""
    event_uuid = request.session.get('active_event_uuid')
    if not event_uuid:
        return None

    try:
        event = Event.objects.get(id=event_uuid)
    except Event.DoesNotExist:
        # Event was deleted — clean up
        _clear_active_event(request)
        return None

    # Re-check authorization on every request (staff list may have changed)
    if not (
        request.user.role == 'admin'
        or event.created_by == request.user
        or event.staff.filter(id=request.user.id).exists()
    ):
        _clear_active_event(request)
        return None

    return event


def _clear_active_event(request):
    request.session.pop('active_event_uuid', None)
    request.session.pop('active_event_name', None)


@login_required
def scanner_page(request):
    """Scanner interface for staff."""

    user = request.user
    is_staff = user.is_staff_or_above()

    active_event = _get_active_event(request) if is_staff else None

    events = []
    if is_staff:
        events = Event.objects.filter(
            end_time__gte=timezone.now()
        ).order_by('start_time')

        if user.role != 'admin':
            events = (
                    events.filter(staff__id=user.id) |
                    events.filter(created_by_id=user.id)
            ).distinct()

    return render(request, 'scanner/index.html', {
        'events': events,
        'active_event': active_event,
        'is_staff': is_staff,
    })


@login_required
def select_event(request):
    if not request.user.is_staff_or_above():
        return redirect('home')

    if request.method == 'POST':
        event_uuid = request.POST.get('event_uuid', '').strip()

        if not event_uuid:
            # "Change event" / deselect
            _clear_active_event(request)
            return redirect('scanner')

        event = get_object_or_404(Event, id=event_uuid)

        if not (
            request.user.role == 'admin'
            or event.created_by == request.user
            or event.staff.filter(id=request.user.id).exists()
        ):
            # Re-render event list with an error rather than a bare 403
            events = Event.objects.filter(
                end_time__gte=timezone.now()
            ).order_by('start_time')
            if request.user.role != 'admin':
                events = events.filter(staff__id=request.user.id) | events.filter(created_by_id=request.user.id)
            return render(request, 'scanner/index.html', {
                'events': events,
                'active_event': None,
                'error': 'You are not assigned as staff for that event.',
            })

        request.session['active_event_uuid'] = str(event.id)
        request.session['active_event_name'] = event.name

    return redirect('scanner')


@login_required
def dashboard_page(request):
    """Admin dashboard — list of events with stats."""

    if request.user.role not in ('staff', 'admin', 'organizer'):
        return redirect('home')
    events = Event.objects.all()
<<<<<<< HEAD
    return render(request, 'admin_portal/dashboard.html', {'events': events})
=======
    context = {'events': events}

    if request.user.role == 'admin':
        context['users'] = User.objects.select_related('person').order_by('username')
        context['all_events'] = Event.objects.filter(end_time__gte=timezone.now()).order_by('start_time')
        context['role_choices'] = User.Role.choices

    return render(request, 'admin_portal/dashboard.html', context)
>>>>>>> 6489d758485c56fa294002f439ead7fee94f3161


@login_required
def event_create_page(request):
    if not request.user.is_organizer_or_above():
        return redirect('home')

    if request.method == 'POST':
        data = request.POST.copy()

        # Convert reg_open and reg_close to datetime if they exist
        for field in ['reg_open', 'reg_close']:
            if field in data and data[field]:
                try:
                    data[field] = datetime.fromisoformat(data[field])
                except ValueError:
                    data[field] = None  # or handle invalid format

        serializer = EventCreateSerializer(data=data)
        if serializer.is_valid():
            # Save the event, passing created_by separately
            event = serializer.save(created_by=request.user)
            event.staff.add(request.user)
<<<<<<< HEAD
=======

            users = User.objects.all()

            subject = f"New Event: {event.name}"
            message = (
                f"A new event has been created!\n\n"
                f"Event: {event.name}\n"
                f"Start: {event.start_time}\n"
                f"Location: {event.location}\n\n"
                f"Register now in the app."
            )

            recipient_list = [user.email for user in users if user.email]

            try:
                send_mail(subject, message, None, recipient_list)
            except Exception:
                logger.exception("Failed to send event creation email for %s", event.name)

>>>>>>> 6489d758485c56fa294002f439ead7fee94f3161
            return redirect('event-detail', uuid=event.id)

        # If serializer invalid, show errors
        return render(request, 'admin_portal/event_create.html', {
            'errors': serializer.errors,
            'data': data
        })

    # GET request: show empty form
    return render(request, 'admin_portal/event_create.html')


@login_required
def event_detail_page(request, uuid):
    event = get_object_or_404(Event, id=uuid)
    tickets = event.tickets.select_related('person').order_by('-issued_at')

    # check if user is registered
    is_registered = False
    if request.user.is_authenticated:
        try:
            person = request.user.person
            is_registered = Ticket.objects.filter(
                person=person,
                event=event,
            ).exists()
<<<<<<< HEAD
        except:
=======
        except Person.DoesNotExist:
>>>>>>> 6489d758485c56fa294002f439ead7fee94f3161
            pass

    # Handle registration from web (with added cancel feature)
    if request.method == 'POST':
        person = request.user.person

        if 'register' in request.POST:
            Ticket.objects.get_or_create(
                person=person,
                event=event,
                defaults={'status': Ticket.Status.ISSUED},
            )

        elif 'unregister' in request.POST:
            Ticket.objects.filter(
                person=person,
                event=event,
            ).delete()

        return redirect('event-detail', uuid=uuid)

    logs = ScanLog.objects.filter(event=event).select_related('person', 'actor').order_by('-timestamp')

<<<<<<< HEAD
    User = get_user_model()
=======
>>>>>>> 6489d758485c56fa294002f439ead7fee94f3161
    event_staff = event.staff.all()
    available_staff = User.objects.filter(
        role__in=['staff', 'organizer', 'admin']
    ).exclude(id__in=event_staff.values_list('id', flat=True))

    return render(request, 'admin_portal/event_detail.html', {
        'event': event,
        'tickets': tickets,
        'logs': logs,
        'event_staff': event_staff,
        'available_staff': available_staff,
        'is_registered': is_registered,
    })


@login_required
def manage_event_staff(request, uuid):
    event = get_object_or_404(Event, id=uuid)
    if not (request.user.role == 'admin' or event.created_by == request.user or request.user.is_organizer_or_above()):
        return redirect('event-detail', uuid=uuid)

    if request.method == 'POST':
<<<<<<< HEAD
        User = get_user_model()
=======
>>>>>>> 6489d758485c56fa294002f439ead7fee94f3161
        action = request.POST.get('action')
        user_id = request.POST.get('user_id', '').strip()
        if not user_id:
            return redirect('event-detail', uuid=uuid)
        user = get_object_or_404(User, id=user_id)
        if action == 'add':
            event.staff.add(user)
        elif action == 'remove':
            event.staff.remove(user)

    return redirect('event-detail', uuid=uuid)


def contact_page(request, uuid):
    """Public contact card view (respects visibility)."""
    person = get_object_or_404(Person, id=uuid)
    contact = person.get_visible_contact()
    return render(request, 'public/contact.html', {
        'person': person,
        'contact': contact,
    })

@login_required
def toggle_walkins(request, uuid):
    """Toggle walk-in mode for an event."""
    event = get_object_or_404(Event, id=uuid)
    # Only event creator, staff, or admin can toggle
    if not (
        request.user.role == 'admin'
        or event.created_by == request.user
        or request.user.is_organizer_or_above()
    ):
        return redirect('event-detail', uuid=uuid)

    if request.method == 'POST':
        event.allow_walkins = not event.allow_walkins
        event.save(update_fields=['allow_walkins'])

    return redirect('event-detail', uuid=uuid)


@login_required
def organizer_event_list(request):
    if not request.user.is_organizer_or_above():
        return redirect('dashboard')

    events = Event.objects.filter(created_by=request.user)
    return render(request, 'organizer_event_create/organizer_event_list.html', {
        'events': events
    })


@login_required
def event_edit_page(request, uuid):
    if not request.user.is_organizer_or_above():
        return redirect('dashboard')

    event = get_object_or_404(Event, id=uuid)

    if event.created_by != request.user:
        return redirect('organizer-event-list')

    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
<<<<<<< HEAD
=======

            attendees = User.objects.filter(
                person__tickets__event=event
            ).distinct()

            subject = f"Update for {event.name}"
            message = (
                f'The event "{event.name}" has been updated.\n\n'
                f"Start: {event.start_time}\n"
                f"Location: {event.location}\n\n"
                f"Please check the app for details."
            )

            recipient_list = [user.email for user in attendees if user.email]

            try:
                send_mail(subject, message, None, recipient_list)
            except Exception:
                logger.exception("Failed to send event update email for %s", event.name)

>>>>>>> 6489d758485c56fa294002f439ead7fee94f3161
            return redirect('organizer-event-list')
    else:
        form = EventForm(instance=event)

    return render(request, 'organizer_event_create/event_edit.html', {
        'form': form,
        'event': event
    })

<<<<<<< HEAD
=======

# ── Admin user management ──────────────────────────────────────

def _is_admin(request):
    return request.user.is_authenticated and request.user.role == 'admin'


@login_required
def admin_create_user(request):
    if not _is_admin(request):
        return redirect('home')
    if request.method != 'POST':
        return redirect('dashboard')

    username = request.POST.get('username', '').strip()
    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '').strip()
    name = request.POST.get('name', '').strip()
    role = request.POST.get('role', 'attendee')

    if not username or not password:

        messages.error(request, 'Username and password are required.')
        return redirect('dashboard')

    if User.objects.filter(username=username).exists():

        messages.error(request, f'Username "{username}" already exists.')
        return redirect('dashboard')

    user = User.objects.create_user(username=username, email=email, password=password, role=role)
    Person.objects.create(user=user, name=name or username, email=email)


    messages.success(request, f'User "{username}" created.')
    return redirect('dashboard')


@login_required
def admin_delete_user(request, user_id):
    if not _is_admin(request):
        return redirect('home')
    if request.method != 'POST':
        return redirect('dashboard')

    target = get_object_or_404(User, id=user_id)
    if target == request.user:

        messages.error(request, "You can't delete your own account.")
        return redirect('dashboard')

    username = target.username
    target.delete()

    messages.success(request, f'User "{username}" deleted.')
    return redirect('dashboard')


@login_required
def admin_change_role(request, user_id):
    if not _is_admin(request):
        return redirect('home')
    if request.method != 'POST':
        return redirect('dashboard')

    target = get_object_or_404(User, id=user_id)
    new_role = request.POST.get('role', '').strip()
    valid_roles = [r[0] for r in User.Role.choices]
    if new_role not in valid_roles:
        return redirect('dashboard')

    target.role = new_role
    target.save(update_fields=['role'])

    messages.success(request, f'Changed {target.username} to {new_role}.')
    return redirect('dashboard')


@login_required
def admin_register_user_for_event(request, user_id):
    if not _is_admin(request):
        return redirect('home')
    if request.method != 'POST':
        return redirect('dashboard')

    target = get_object_or_404(User, id=user_id)
    event_uuid = request.POST.get('event_uuid', '').strip()
    if not event_uuid:
        return redirect('dashboard')

    event = get_object_or_404(Event, id=event_uuid)
    person = target.person
    Ticket.objects.get_or_create(
        person=person,
        event=event,
        defaults={'status': Ticket.Status.ISSUED},
    )

    messages.success(request, f'Registered {target.username} for {event.name}.')
    return redirect('dashboard')

>>>>>>> 6489d758485c56fa294002f439ead7fee94f3161
