"""
Turnstil web interface URL configuration.
Server-rendered pages for registration, profile, scanner, and admin.
"""
from django.urls import path
from . import web_views

urlpatterns = [
<<<<<<< HEAD
=======
    # Public
>>>>>>> 6489d758485c56fa294002f439ead7fee94f3161
    path('', web_views.home, name='home'),
    path('register/', web_views.register_page, name='register'),
    path('login/', web_views.login_page, name='login'),
    path('logout/', web_views.logout_view, name='logout'),
<<<<<<< HEAD
=======
    path('contact/<uuid:uuid>/', web_views.contact_page, name='contact-view'),

    # Authenticated
>>>>>>> 6489d758485c56fa294002f439ead7fee94f3161
    path('profile/', web_views.profile_page, name='profile'),
    path('profile/qr/', web_views.qr_display, name='qr-display'),
    path('profile/notifications/', web_views.save_notification_preferences, name='save-notifications'),
    path('scanner/', web_views.scanner_page, name='scanner'),
    path('scanner/select-event', web_views.select_event, name='select-event'),
<<<<<<< HEAD
    path('dashboard/', web_views.dashboard_page, name='dashboard'),
    path('events/create/', web_views.event_create_page, name='event-create'),
    path('events/<uuid:uuid>/', web_views.event_detail_page, name='event-detail'),
    path('contact/<uuid:uuid>/', web_views.contact_page, name='contact-view'),
    path('events/<uuid:uuid>/walkins/', web_views.toggle_walkins, name='toggle-walkins'),
    path('organizer_event_create/', web_views.organizer_event_list, name='organizer-event-list'),
    path('organizer_event_create/', web_views.event_edit_page, name='event-edit'),

    path('', web_views.home, name='home'),
    path('register/', web_views.register_page, name='register'),
    path('login/', web_views.login_page, name='login'),
    path('logout/', web_views.logout_view, name='logout'),
    path('profile/', web_views.profile_page, name='profile'),
    path('profile/qr/', web_views.qr_display, name='qr-display'),
    path('scanner/', web_views.scanner_page, name='scanner'),
    path('dashboard/', web_views.dashboard_page, name='dashboard'),
    path('organizer_event_create/', web_views.organizer_event_list, name='organizer-event-list'),
    path('organizer_event_create/create/', web_views.event_create_page, name='organizer-event-create'),
    path('organizer_event_create/<uuid:uuid>/edit/', web_views.event_edit_page, name='event-edit'),
=======

    # Events
>>>>>>> 6489d758485c56fa294002f439ead7fee94f3161
    path('events/create/', web_views.event_create_page, name='event-create'),
    path('events/<uuid:uuid>/', web_views.event_detail_page, name='event-detail'),
    path('events/<uuid:uuid>/walkins/', web_views.toggle_walkins, name='toggle-walkins'),
    path('events/<uuid:uuid>/staff/', web_views.manage_event_staff, name='manage-event-staff'),
<<<<<<< HEAD
    path('contact/<uuid:uuid>/', web_views.contact_page, name='contact-view'),
=======

    # Organizer
    path('organizer_event_create/', web_views.organizer_event_list, name='organizer-event-list'),
    path('organizer_event_create/create/', web_views.event_create_page, name='organizer-event-create'),
    path('organizer_event_create/<uuid:uuid>/edit/', web_views.event_edit_page, name='event-edit'),

    # Dashboard & admin
    path('dashboard/', web_views.dashboard_page, name='dashboard'),
    path('dashboard/users/create/', web_views.admin_create_user, name='admin-create-user'),
    path('dashboard/users/<int:user_id>/delete/', web_views.admin_delete_user, name='admin-delete-user'),
    path('dashboard/users/<int:user_id>/role/', web_views.admin_change_role, name='admin-change-role'),
    path('dashboard/users/<int:user_id>/register/', web_views.admin_register_user_for_event, name='admin-register-user'),
>>>>>>> 6489d758485c56fa294002f439ead7fee94f3161
]
