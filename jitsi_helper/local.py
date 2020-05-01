from .settings import *
DATABASES = {
    "default": {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'jitsi_db',
        'USER': 'jitsi_user',
        'PASSWORD': 'jitsi_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
