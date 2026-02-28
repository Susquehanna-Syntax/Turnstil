"""
Turnstil web views — server-rendered pages.
These handle the HTML interface; the API handles data operations.
"""
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import Person, Event, Ticket
from .serializers import RegisterSerializer
from .forms import EventForm
from datetime import datetime
from .serializers import EventCreateSerializer


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
    return render(request, 'admin_portal/dashboard.html', {'events': events})


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

    # Handle registration from web
    if request.method == 'POST' and 'register' in request.POST:
        person = request.user.person
        Ticket.objects.get_or_create(
            person=person, event=event,
            defaults={'status': Ticket.Status.ISSUED},
        )
        return redirect('event-detail', uuid=uuid)

    return render(request, 'admin_portal/event_detail.html', {
        'event': event,
        'tickets': tickets,
    })


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
            return redirect('organizer-event-list')
    else:
        form = EventForm(instance=event)

    return render(request, 'organizer_event_create/event_edit.html', {
        'form': form,
        'event': event
    })

