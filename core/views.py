"""
Turnstil API views.
"""
import uuid

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Person, Event, Ticket, ScanLog
from .serializers import (
    RegisterSerializer, UserSerializer,
    PersonSerializer, PersonContactSerializer, ContactUpdateSerializer,
    EventSerializer, EventCreateSerializer,
    TicketSerializer, CheckInSerializer,
    ScanLogSerializer, StaffAssignSerializer,
)

User = get_user_model()


# ── Permissions ──────────────────────────────────────────────────

class IsStaffOrAbove(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff_or_above()


class IsOrganizerOrAbove(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_organizer_or_above()


class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class IsEventStaff(permissions.BasePermission):
    """Check if user is staff for the specific event."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role == 'admin':
            return True
        event_uuid = (
            request.data.get('event_uuid')
            or view.kwargs.get('uuid')
        )
        if not event_uuid:
            return False
        try:
            event = Event.objects.get(id=event_uuid)
        except Event.DoesNotExist:
            return False
        return (
            event.created_by == request.user
            or event.staff.filter(id=request.user.id).exists()
        )


# ── Auth ─────────────────────────────────────────────────────────

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'status': 'success',
            'data': {
                'user': UserSerializer(user).data,
                'person_uuid': str(user.person.id),
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
            }
        }, status=status.HTTP_201_CREATED)


class MeView(APIView):
    def get(self, request):
        return Response({
            'status': 'success',
            'data': UserSerializer(request.user).data,
        })


# ── Person ───────────────────────────────────────────────────────

class PersonDetailView(APIView):
    def get(self, request, uuid):
        person = get_object_or_404(Person, id=uuid)
        # Full details only for the owner
        if person.user == request.user:
            serializer = PersonSerializer(person)
        else:
            serializer = PersonSerializer(person)
        return Response({'status': 'success', 'data': serializer.data})


class PersonQRView(APIView):
    """Serve QR code image. Owner only."""
    def get(self, request, uuid):
        person = get_object_or_404(Person, id=uuid)
        if person.user != request.user and request.user.role != 'admin':
            return Response(
                {'status': 'error', 'message': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN,
            )
        from django.http import HttpResponse
        qr_bytes = person.generate_qr_code()
        return HttpResponse(qr_bytes, content_type='image/png')


class PersonContactView(APIView):
    """
    GET: Returns contact card respecting visibility.
    PATCH: Update contact fields (owner only).
    """
    def get(self, request, uuid):
        person = get_object_or_404(Person, id=uuid)
        if person.user == request.user:
            # Owner sees everything
            data = PersonSerializer(person).data
        else:
            data = person.get_visible_contact()
        return Response({'status': 'success', 'data': data})

    def patch(self, request, uuid):
        person = get_object_or_404(Person, id=uuid)
        if person.user != request.user:
            return Response(
                {'status': 'error', 'message': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = ContactUpdateSerializer(person, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'status': 'success',
            'data': PersonSerializer(person).data,
        })


# ── Events ───────────────────────────────────────────────────────

class EventListCreateView(APIView):
    def get(self, request):
        events = Event.objects.all()
        serializer = EventSerializer(events, many=True)
        return Response({'status': 'success', 'data': serializer.data})

    def post(self, request):
        if not request.user.is_organizer_or_above():
            return Response(
                {'status': 'error', 'message': 'Organizer role required'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = EventCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = serializer.save(created_by=request.user)
        # Auto-assign creator as staff
        event.staff.add(request.user)
        return Response({
            'status': 'success',
            'data': EventSerializer(event).data,
        }, status=status.HTTP_201_CREATED)


class EventDetailView(APIView):
    def get(self, request, uuid):
        event = get_object_or_404(Event, id=uuid)
        return Response({
            'status': 'success',
            'data': EventSerializer(event).data,
        })


class EventRegisterView(APIView):
    """Register the current user for an event."""
    def post(self, request, uuid):
        event = get_object_or_404(Event, id=uuid)

        if event.is_full:
            return Response({
                'status': 'error',
                'code': 'EVENT_FULL',
                'message': 'This event has reached capacity.',
            }, status=status.HTTP_409_CONFLICT)

        person = request.user.person

        ticket, created = Ticket.objects.get_or_create(
            person=person,
            event=event,
            defaults={'status': Ticket.Status.ISSUED},
        )

        if not created:
            if ticket.status == Ticket.Status.CANCELED:
                ticket.status = Ticket.Status.ISSUED
                ticket.save(update_fields=['status'])
                return Response({
                    'status': 'success',
                    'data': TicketSerializer(ticket).data,
                    'message': 'Registration reactivated.',
                })
            return Response({
                'status': 'error',
                'code': 'ALREADY_REGISTERED',
                'message': 'Already registered for this event.',
            }, status=status.HTTP_409_CONFLICT)

        return Response({
            'status': 'success',
            'data': TicketSerializer(ticket).data,
        }, status=status.HTTP_201_CREATED)


class EventStaffView(APIView):
    """Assign staff to an event."""
    permission_classes = [permissions.IsAuthenticated, IsOrganizerOrAbove]

    def post(self, request, uuid):
        event = get_object_or_404(Event, id=uuid)
        serializer = StaffAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = get_object_or_404(User, id=serializer.validated_data['user_id'])
        event.staff.add(user)
        return Response({
            'status': 'success',
            'message': f'{user.username} assigned as staff.',
        })

    def get(self, request, uuid):
        event = get_object_or_404(Event, id=uuid)
        staff = event.staff.all()
        return Response({
            'status': 'success',
            'data': UserSerializer(staff, many=True).data,
        })


class EventDashboardView(APIView):
    """Live stats for an event."""
    permission_classes = [permissions.IsAuthenticated, IsEventStaff]

    def get(self, request, uuid):
        event = get_object_or_404(Event, id=uuid)
        tickets = event.tickets.all()
        recent_scans = event.scan_logs.order_by('-timestamp')[:20]

        return Response({
            'status': 'success',
            'data': {
                'event': EventSerializer(event).data,
                'stats': {
                    'registered': tickets.exclude(
                        status=Ticket.Status.CANCELED
                    ).count(),
                    'checked_in': tickets.filter(
                        status=Ticket.Status.CHECKED_IN
                    ).count(),
                    'capacity': event.capacity,
                    'is_full': event.is_full,
                },
                'recent_scans': ScanLogSerializer(recent_scans, many=True).data,
            },
        })


# ── Check-in (the critical endpoint) ────────────────────────────

class CheckInView(APIView):
    """
    Process a QR code scan for event check-in.
    This is the most important endpoint in the system.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CheckInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        person_uuid = serializer.validated_data['person_uuid']
        event_uuid = serializer.validated_data['event_uuid']

        # --- Validate person ---
        try:
            person = Person.objects.get(id=person_uuid)
        except Person.DoesNotExist:
            self._log_scan(
                event_id=event_uuid, person=None, actor=request.user,
                result=ScanLog.Result.INVALID,
                scanned_value=str(person_uuid),
            )
            return Response({
                'status': 'error',
                'code': 'INVALID',
                'message': 'QR code not recognized.',
            }, status=status.HTTP_404_NOT_FOUND)

        # --- Validate event ---
        try:
            event = Event.objects.get(id=event_uuid)
        except Event.DoesNotExist:
            self._log_scan(
                event_id=None, person=person, actor=request.user,
                result=ScanLog.Result.INVALID,
                scanned_value=str(event_uuid),
                metadata={'reason': 'event_not_found'},
            )
            return Response({
                'status': 'error',
                'code': 'INVALID',
                'message': 'Event not found.',
            }, status=status.HTTP_404_NOT_FOUND)

        # --- Check staff authorization ---
        is_authorized = (
            request.user.role == 'admin'
            or event.created_by == request.user
            or event.staff.filter(id=request.user.id).exists()
        )
        if not is_authorized:
            return Response({
                'status': 'error',
                'code': 'UNAUTHORIZED',
                'message': 'You are not staff for this event.',
            }, status=status.HTTP_403_FORBIDDEN)

        # --- Check registration (or walk-in) ---
        try:
            ticket = Ticket.objects.get(person=person, event=event)
        except Ticket.DoesNotExist:
            if event.allow_walkins:
                # Auto-register walk-in
                if event.is_full:
                    self._log_scan(
                         event_id=event, person=person, actor=request.user,
                        result=ScanLog.Result.NOT_REGISTERED,
                        metadata={'reason': 'walkin_capacity_full'},
                    )
                    return Response({
                        'status': 'error',
                        'code': 'EVENT_FULL',
                        'message': f'Walk-in denied — event is at capacity.',
                    }, status=status.HTTP_409_CONFLICT)
                ticket = Ticket.objects.create(
                        person=person, event=event, status=Ticket.Status.ISSUED,
                    )
            else:
                self._log_scan(
                    event_id=event, person=person, actor=request.user,
                    result=ScanLog.Result.NOT_REGISTERED,
                )
                return Response({
                    'status': 'error',
                    'code': 'NOT_REGISTERED',
                    'message': f'{person.name} is not registered for this event.',
                }, status=status.HTTP_404_NOT_FOUND)
        # --- Check for duplicate ---
        if ticket.status == Ticket.Status.CHECKED_IN:
            self._log_scan(
                event_id=event, person=person, actor=request.user,
                result=ScanLog.Result.DUPLICATE,
                metadata={'checked_in_at': str(ticket.checked_in_at)},
            )
            return Response({
                'status': 'error',
                'code': 'DUPLICATE_CHECKIN',
                'message': f'{person.name} already checked in at {ticket.checked_in_at:%I:%M %p}.',
            }, status=status.HTTP_409_CONFLICT)

        # --- Check ticket status ---
        if ticket.status == Ticket.Status.CANCELED:
            self._log_scan(
                event_id=event, person=person, actor=request.user,
                result=ScanLog.Result.INVALID,
                metadata={'reason': 'ticket_canceled'},
            )
            return Response({
                'status': 'error',
                'code': 'TICKET_CANCELED',
                'message': f'{person.name}\'s registration was canceled.',
            }, status=status.HTTP_409_CONFLICT)

        # --- Success! Check them in ---
        ticket.check_in()
        self._log_scan(
            event_id=event, person=person, actor=request.user,
            result=ScanLog.Result.SUCCESS,
        )

        return Response({
            'status': 'success',
            'data': {
                'person_name': person.name,
                'checked_in_at': ticket.checked_in_at.isoformat(),
                'event_name': event.name,
            },
        })

    def _log_scan(self, event_id, person, actor, result, scanned_value='', metadata=None):
        """Log every scan attempt for audit trail."""
        ScanLog.objects.create(
            event=event_id if isinstance(event_id, Event) else None,
            person=person,
            actor=actor,
            result=result,
            scanned_value=scanned_value,
            metadata=metadata or {},
        )


# ── Scan Logs ────────────────────────────────────────────────────

class ScanLogListView(generics.ListAPIView):
    serializer_class = ScanLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def get_queryset(self):
        qs = ScanLog.objects.select_related('person', 'actor', 'event')
        event_id = self.request.query_params.get('event')
        if event_id:
            qs = qs.filter(event_id=event_id)
        result = self.request.query_params.get('result')
        if result:
            qs = qs.filter(result=result)
        return qs
