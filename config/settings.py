""" Turnstil - Event Management System Django settings for development. """
import os
from pathlib import Path
from datetime import timedelta
BASE_DIR = Path(__file__).resolve().parent.parent
# --- Security ---
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-CHANGE-ME-IN-'
     'PRODUCTION-turnstil-dev-key-2024'
    )
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS','localhost,127.0.0.1,10.0.0.204').split(',')

# CSRF trusted origins (required for HTTPS proxies)
CSRF_TRUSTED_ORIGINS = os.environ.get(
    'CSRF_TRUSTED_ORIGINS',
    'http://localhost:8000,http://127.0.0.1:8000' ).split(',')
# --- Application ---
INSTALLED_APPS = [ 'django.contrib.admin',
                   'django.contrib.auth',
                   'django.contrib.contenttypes',
                   'django.contrib.sessions',
                   'django.contrib.messages',
                   'django.contrib.staticfiles',
                   # Third-party
                   'rest_framework',
                   'rest_framework_simplejwt',
                   # Local
                   'core',
                   ]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ]
ROOT_URLCONF = 'config.urls'
TEMPLATES = [
    {
        'BACKEND':
            'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                ],
            },
    },
]
WSGI_APPLICATION = 'config.wsgi.application'
# --- Database ---
# Default: SQLite for quick prototyping. Swap to PostgreSQL for production.
DATABASE_URL = os.environ.get('DATABASE_URL', '')
if DATABASE_URL.startswith('postgresql'):
    DATABASES = { 'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'turnstil'),
        'USER': os.environ.get('DB_USER', 'turnstil'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'turnstil'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
# --- Auth ---
AUTH_USER_MODEL = 'core.User'
AUTH_PASSWORD_VALIDATORS = [
    {'NAME':
         'django.contrib.auth.password_validation.MinimumLengthValidator'},
]
# --- DRF ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS':
        'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
}
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
# --- i18n ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/New_York'
USE_I18N = True
USE_TZ = True
# --- Static / Media ---
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# --- QR Code ---
QR_CODE_DIR = MEDIA_ROOT / 'qrcodes'
# --- Email ---
# Set EMAIL_HOST_PASSWORD to a Gmail App Password to enable SMTP delivery.
# Generate one at https://myaccount.google.com/apppasswords — revoke it there to cancel.
# When unset, emails print to the console (safe for dev/test).
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_BACKEND = (
    'django.core.mail.backends.smtp.EmailBackend'
    if EMAIL_HOST_PASSWORD
    else 'django.core.mail.backends.console.EmailBackend'
)

EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')

EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'turnstilreminders@gmail.com')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Reminder windows (hours before event start) for periodic email reminders
REMINDER_WINDOWS = [24, 1]

>>>>>>> 6489d758485c56fa294002f439ead7fee94f3161
