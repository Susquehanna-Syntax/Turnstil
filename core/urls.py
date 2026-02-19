"""
Turnstil web interface URL configuration.
Server-rendered pages for registration, profile, scanner, and admin.
"""
from django.urls import path
from . import web_views

urlpatterns = [
    path('', web_views.home, name='home'),
    path('register/', web_views.register_page, name='register'),
    path('login/', web_views.login_page, name='login'),
    path('logout/', web_views.logout_view, name='logout'),
    path('profile/', web_views.profile_page, name='profile'),
    path('profile/qr/', web_views.qr_display, name='qr-display'),
    path('scanner/', web_views.scanner_page, name='scanner'),
    path('dashboard/', web_views.dashboard_page, name='dashboard'),
    path('events/create/', web_views.event_create_page, name='event-create'),
    path('events/<uuid:uuid>/', web_views.event_detail_page, name='event-detail'),
    path('contact/<uuid:uuid>/', web_views.contact_page, name='contact-view'),
]
