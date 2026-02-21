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


@login_required
def scanner_page(request):
    """Scanner interface for staff."""
    events = Event.objects.filter(
        end_time__gte=timezone.now()
    ).order_by('start_time')
    return render(request, 'scanner/index.html', {'events': events})


@login_required
def dashboard_page(request):
    """Admin dashboard — list of events with stats."""
    if not request.user.is_staff_or_above():
        return redirect('home')
    events = Event.objects.all()
    return render(request, 'admin_portal/dashboard.html', {'events': events})


@login_required
def event_create_page(request):
    if not request.user.is_organizer_or_above():
        return redirect('home')

    if request.method == 'POST':
        from .serializers import EventCreateSerializer
        serializer = EventCreateSerializer(data={
            'name': request.POST.get('name', ''),
            'description': request.POST.get('description', ''),
            'location': request.POST.get('location', ''),
            'start_time': request.POST.get('start_time', ''),
            'end_time': request.POST.get('end_time', ''),
            'capacity': request.POST.get('capacity', 0) or 0,
        })
        if serializer.is_valid():
            event = serializer.save(created_by=request.user)
            event.staff.add(request.user)
            return redirect('event-detail', uuid=event.id)

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
