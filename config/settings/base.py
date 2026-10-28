import os
from pathlib import Path
from datetime import timedelta
BASE_DIR=Path(__file__).resolve().parents[2]
SECRET_KEY=os.environ.get('DJANGO_SECRET_KEY','dev-only-insecure-change-me')
DEBUG=False
ALLOWED_HOSTS=os.environ.get('ALLOWED_HOSTS','localhost,127.0.0.1').split(',')
INSTALLED_APPS=['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','rest_framework','rest_framework_simplejwt','django_filters','drf_spectacular','corsheaders','channels','apps.identity','apps.accounts','apps.ledger','apps.transfers','apps.risk','apps.audit','apps.notifications.apps.NotificationsConfig','apps.loans','apps.cards','apps.billing','apps.investments','apps.operations','apps.portal']
MIDDLEWARE=['django.middleware.security.SecurityMiddleware','whitenoise.middleware.WhiteNoiseMiddleware','corsheaders.middleware.CorsMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF='config.urls'
TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.debug','django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages','apps.portal.context_processors.banking_notifications']}}]
WSGI_APPLICATION='config.wsgi.application'
ASGI_APPLICATION='config.asgi.application'
DATABASES={'default':{'ENGINE':'django.db.backends.postgresql','NAME':os.environ.get('POSTGRES_DB','banking'),'USER':os.environ.get('POSTGRES_USER','banking'),'PASSWORD':os.environ.get('POSTGRES_PASSWORD','banking'),'HOST':os.environ.get('POSTGRES_HOST','localhost'),'PORT':os.environ.get('POSTGRES_PORT','5432'),'CONN_MAX_AGE':60,'OPTIONS':{'connect_timeout':5}}}
AUTH_USER_MODEL='identity.User'
AUTH_PASSWORD_VALIDATORS=[{'NAME':'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},{'NAME':'django.contrib.auth.password_validation.MinimumLengthValidator','OPTIONS':{'min_length':10}},{'NAME':'django.contrib.auth.password_validation.CommonPasswordValidator'},{'NAME':'django.contrib.auth.password_validation.NumericPasswordValidator'}]
REST_FRAMEWORK={'DEFAULT_AUTHENTICATION_CLASSES':['rest_framework_simplejwt.authentication.JWTAuthentication'],'DEFAULT_PERMISSION_CLASSES':['rest_framework.permissions.IsAuthenticated'],'DEFAULT_FILTER_BACKENDS':['django_filters.rest_framework.DjangoFilterBackend','rest_framework.filters.OrderingFilter','rest_framework.filters.SearchFilter'],'DEFAULT_PAGINATION_CLASS':'rest_framework.pagination.PageNumberPagination','PAGE_SIZE':20,'DEFAULT_SCHEMA_CLASS':'drf_spectacular.openapi.AutoSchema','DEFAULT_THROTTLE_CLASSES':['rest_framework.throttling.AnonRateThrottle','rest_framework.throttling.UserRateThrottle'],'DEFAULT_THROTTLE_RATES':{'anon':'30/min','user':'120/min'}}
SIMPLE_JWT={'ACCESS_TOKEN_LIFETIME':timedelta(minutes=15),'REFRESH_TOKEN_LIFETIME':timedelta(days=1),'AUTH_HEADER_TYPES':('Bearer',)}
SPECTACULAR_SETTINGS={'TITLE':'Banking & Transaction Management API','DESCRIPTION':'Educational banking simulator; not licensed banking infrastructure','VERSION':'1.0.0'}
CORS_ALLOWED_ORIGINS=os.environ.get('CORS_ALLOWED_ORIGINS','http://localhost:5173').split(',')
CELERY_BROKER_URL=os.environ.get('REDIS_URL','redis://localhost:6379/0')
CELERY_RESULT_BACKEND=CELERY_BROKER_URL
CHANNEL_LAYERS={'default':{'BACKEND':'channels_redis.core.RedisChannelLayer','CONFIG':{'hosts':[CELERY_BROKER_URL]}}}
LANGUAGE_CODE='en-us';TIME_ZONE='UTC';USE_TZ=True
STATIC_URL='static/';STATIC_ROOT=BASE_DIR/'staticfiles'
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
SECURE_CONTENT_TYPE_NOSNIFF=True
SESSION_COOKIE_HTTPONLY=True
CSRF_COOKIE_HTTPONLY=True
X_FRAME_OPTIONS='DENY'

LOGIN_URL="portal-login"
LOGIN_REDIRECT_URL="portal-dashboard"
LOGOUT_REDIRECT_URL="portal-login"

STORAGES={'staticfiles':{'BACKEND':'whitenoise.storage.CompressedManifestStaticFilesStorage'}}
