"""
Django settings for safedeal project.

Generated by 'django-admin startproject' using Django 5.2.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

from pathlib import Path
# import dj_database_url

import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
from decouple import config

MPESA_CONSUMER_KEY = config("MPESA_CONSUMER_KEY")
MPESA_CONSUMER_SECRET = config("MPESA_CONSUMER_SECRET")
MPESA_SHORTCODE = config("MPESA_SHORTCODE")
MPESA_PASSKEY = config("MPESA_PASSKEY")
MPESA_CALLBACK_URL = config("MPESA_CALLBACK_URL")
MPESA_RESULT_CALLBACK = config("MPESA_RESULT_CALLBACK")
MPESA_TIMEOUT_CALLBACK = config("MPESA_TIMEOUT_CALLBACK")
MPESA_INITIATOR_NAME = config("MPESA_INITIATOR_NAME")
MPESA_SECURITY_CREDENTIAL = config("MPESA_SECURITY_CREDENTIAL")

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.safedeal.co.ke'
EMAIL_PORT = 465
EMAIL_USE_TLS=False
EMAIL_USE_SSL=True
EMAIL_HOST_USER = 'noreply@safedeal.co.ke'
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = "SafeDeal <noreply@safedeal.co.ke>"



CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config("CLOUDINARY_CLOUD_NAME"),
    'API_KEY': config("CLOUDINARY_API_KEY"),
    'API_SECRET': config("CLOUDINARY_API_SECRET"),
}

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['safedeal.onrender.com', '127.0.0.1', 'localhost',]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'core',
    'rest_framework',
    'dj_rest_auth', # For RESTful authentication
    'dj_rest_auth.registration',  # For registration functionality
    'rest_framework.authtoken', # For token authentication
    'django.contrib.sites',  # Required by allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',  # Optional if you want social login
    'widget_tweaks',
    'django.contrib.humanize',
    
    'mpesa',
    'messaging',
]
INSTALLED_APPS += ['cloudinary', 'cloudinary_storage']

MIDDLEWARE = [
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

ROOT_URLCONF = 'safedeal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'safedeal.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {'ENGINE': 'django.db.backends.sqlite3','NAME': BASE_DIR / 'db.sqlite3',}
}



# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}



DEFAULT_FILE_STORAGE = config("DEFAULT_FILE_STORAGE", default='cloudinary_storage.storage.MediaCloudinaryStorage')

# Simple JWT settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=180),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': 'your_secret_key',
}
SITE_ID = 1
AUTH_USER_MODEL = 'core.CustomUser'
LOGIN_URL = 'login'
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)
ACCOUNT_LOGIN_METHOD = 'username'                        # Login by username
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username', 'password1', 'password2']  # email required + verified
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'                # Enforce verification
ACCOUNT_AUTHENTICATED_LOGIN_REDIRECTS = True
LOGIN_REDIRECT_URL = '/dashboard/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/login/'



LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Mpesa settings
# https://developer.safaricom.co.ke/daraja/apis/postman


log_dir = os.path.join(BASE_DIR, 'logs')
os.makedirs(log_dir, exist_ok=True)


log_file_path = os.path.join(log_dir, 'mpesa.log')
open(log_file_path, 'a').close()
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'handlers': {
        'mpesa_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'mpesa.log'),
            'formatter': 'verbose',
        },
    },

    'formatters': {
        'verbose': {
            'format': '{asctime} [{levelname}] {name}: {message}',
            'style': '{',
        },
    },

    'loggers': {
        'mpesa': {
            'handlers': ['mpesa_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]  # For dev
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')    # For prod

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
