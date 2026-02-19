from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Person, Event, Ticket, ScanLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'is_active']
    list_filter = ['role', 'is_active']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Turnstil', {'fields': ('role',)}),
    )


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'organization', 'user', 'created_at']
    search_fields = ['name', 'email', 'organization']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'start_time', 'end_time', 'capacity', 'created_by']
    list_filter = ['start_time']
    search_fields = ['name', 'location']
    readonly_fields = ['id', 'created_at']
    filter_horizontal = ['staff']


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['person', 'event', 'status', 'issued_at', 'checked_in_at']
    list_filter = ['status', 'event']
    search_fields = ['person__name']
    readonly_fields = ['id', 'issued_at']


@admin.register(ScanLog)
class ScanLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'result', 'person', 'event', 'actor']
    list_filter = ['result', 'event']
    readonly_fields = ['id', 'timestamp']
    ordering = ['-timestamp']
