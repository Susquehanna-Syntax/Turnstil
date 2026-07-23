from django.urls import path

from . import views

urlpatterns = [
    path("accounts/civil/login/", views.login_start, name="civil-login"),
    path("accounts/civil/callback", views.callback, name="civil-callback"),
    path("api/v1/civil/settings/", views.civil_settings_api, name="civil-settings"),
    path("accounts/civil/config/", views.civil_settings_page, name="civil-settings-page"),
]
