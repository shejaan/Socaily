"""
Django settings for Socaily.

Production-ready configuration:
  - Environment variable driven (SECRET_KEY, DATABASE_URL, CLOUDINARY_URL, DEBUG, ALLOWED_HOSTS)
  - Cloudinary SDK native config (no fragile string parsing)
  - Cloudinary for media storage in production
  - WhiteNoise for static files (CompressedManifestStaticFilesStorage)
  - Security headers gated behind DEBUG=False
  - PostgreSQL via DATABASE_URL on Render; SQLite locally
  - ALLOWED_HOSTS raises ImproperlyConfigured when empty in production
  - Critical warning when CLOUDINARY_URL is missing in production
"""

from pathlib import Path
import os
import logging
import dj_database_url
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  CORE
# ─────────────────────────────────────────────

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG      = os.environ.get('DEBUG', 'False') == 'True'

# ─────────────────────────────────────────────
#  ALLOWED_HOSTS  (raises in production if not set)
# ─────────────────────────────────────────────

_raw_hosts = os.environ.get('ALLOWED_HOSTS', '').strip()

if _raw_hosts:
    ALLOWED_HOSTS = [h.strip() for h in _raw_hosts.split(',') if h.strip()]
elif DEBUG:
    # Local development — allow all
    ALLOWED_HOSTS = ['*']
else:
    raise ImproperlyConfigured(
        "ALLOWED_HOSTS environment variable must be set in production.\n"
        "Example: ALLOWED_HOSTS=yourapp.onrender.com"
    )

# Allow Render's SSL domain and any custom domain in CSRF
CSRF_TRUSTED_ORIGINS = [
    f"https://{h}" for h in ALLOWED_HOSTS if not h.startswith('*')
]

# Extra security headers (only in production)
if not DEBUG:
    SECURE_PROXY_SSL_HEADER       = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT           = True
    SESSION_COOKIE_SECURE         = True
    CSRF_COOKIE_SECURE            = True
    SECURE_HSTS_SECONDS           = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD           = True
    SECURE_CONTENT_TYPE_NOSNIFF   = True


# ─────────────────────────────────────────────
#  APPS
# ─────────────────────────────────────────────

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cloudinary',
    'cloudinary_storage',
    'core',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

MIDDLEWARE = [
    'core.middleware.AdminDebugMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS':    [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.utils.context_processors.notifications_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ─────────────────────────────────────────────
#  DATABASE
#  Set DATABASE_URL env var on Render.
#  Falls back to PostgreSQL locally.
# ─────────────────────────────────────────────

_db_url = os.environ.get('DATABASE_URL')
if _db_url:
    DATABASES = {
        'default': dj_database_url.config(
            default=_db_url,
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'socaily',
            'USER': 'postgres',
            'PASSWORD': '2512',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ─────────────────────────────────────────────
#  AUTH
# ─────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL           = '/login/'
LOGIN_REDIRECT_URL  = '/'
LOGOUT_REDIRECT_URL = '/login/'

SESSION_COOKIE_AGE = 1209600  # 2 weeks


# ─────────────────────────────────────────────
#  INTERNATIONALIZATION
# ─────────────────────────────────────────────

LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'UTC'
USE_I18N      = True
USE_TZ        = True


# ─────────────────────────────────────────────
#  STATIC FILES  (WhiteNoise)
# ─────────────────────────────────────────────

STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []


# ─────────────────────────────────────────────
#  MEDIA FILES  (Cloudinary in production, local in dev)
# ─────────────────────────────────────────────

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL', '')
WHITENOISE_MANIFEST_STRICT = False

if CLOUDINARY_URL:
    import cloudinary
    cloudinary.config()

    _cfg = cloudinary.config()
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': _cfg.cloud_name,
        'API_KEY':    _cfg.api_key,
        'API_SECRET': _cfg.api_secret,
    }

    STORAGES = {
        'default':     {'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage'},
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
        },
    }
else:
    if not DEBUG:
        logging.getLogger('django').critical(
            "CLOUDINARY_URL is not set in production! "
            "Media uploads will vanish on Render redeploy."
        )

    STORAGES = {
        'default':     {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
        },
    }


# ─────────────────────────────────────────────
#  EMAIL
# ─────────────────────────────────────────────

if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# ─────────────────────────────────────────────
#  LOGGING
# ─────────────────────────────────────────────

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style':  '{',
        },
    },
    'handlers': {
        'console': {
            'class':     'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level':    'WARNING',
    },
    'loggers': {
        'django': {
            'handlers':  ['console'],
            'level':     'INFO' if DEBUG else 'WARNING',
            'propagate': False,
        },
    },
}

# ─────────────────────────────────────────────
#  ASGI / CHANNELS (WebSocket)
# ─────────────────────────────────────────────

ASGI_APPLICATION = 'config.asgi.application'

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')

if 'channels' in INSTALLED_APPS or True:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [REDIS_URL],
            },
        },
    }

# ─────────────────────────────────────────────
#  CELERY (Background Tasks)
# ─────────────────────────────────────────────

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# ─────────────────────────────────────────────
#  ALLAUTH / GOOGLE LOGIN
# ─────────────────────────────────────────────

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.environ.get('GOOGLE_CLIENT_ID', '123'),
            'secret': os.environ.get('GOOGLE_CLIENT_SECRET', '456'),
            'key': ''
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}

ACCOUNT_LOGIN_METHODS = {'email', 'username'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'none'

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'
SOCIALACCOUNT_LOGIN_ON_GET = True
