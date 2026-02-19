"""
Turnstil API URL configuration.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path('auth/register', views.RegisterView.as_view(), name='api-register'),
    path('auth/login', TokenObtainPairView.as_view(), name='api-login'),
    path('auth/refresh', TokenRefreshView.as_view(), name='api-refresh'),
    path('auth/me', views.MeView.as_view(), name='api-me'),

    # People
    path('people/<uuid:uuid>', views.PersonDetailView.as_view(), name='api-person-detail'),
    path('people/<uuid:uuid>/qr', views.PersonQRView.as_view(), name='api-person-qr'),
    path('people/<uuid:uuid>/contact', views.PersonContactView.as_view(), name='api-person-contact'),

    # Events
    path('events', views.EventListCreateView.as_view(), name='api-events'),
    path('events/<uuid:uuid>', views.EventDetailView.as_view(), name='api-event-detail'),
    path('events/<uuid:uuid>/register', views.EventRegisterView.as_view(), name='api-event-register'),
    path('events/<uuid:uuid>/staff', views.EventStaffView.as_view(), name='api-event-staff'),
    path('events/<uuid:uuid>/dashboard', views.EventDashboardView.as_view(), name='api-event-dashboard'),

    # Check-in
    path('checkin', views.CheckInView.as_view(), name='api-checkin'),

    # Logs
    path('logs', views.ScanLogListView.as_view(), name='api-logs'),
]
