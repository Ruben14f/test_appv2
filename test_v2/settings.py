import os
from pathlib import Path
from dotenv import load_dotenv
from test_v2.config_helpers.google_cloud_utils import obtener_credenciales_google, descargar_y_extraer_wallet
from google.cloud import storage

# Cargar variables de entorno
load_dotenv()

# Directorio base de la aplicación y la ubicación del wallet
BASE_DIR = Path(__file__).resolve().parent.parent
local_wallet_path = BASE_DIR / 'wallet'

# Definir el TNS_ADMIN en las variables de entorno
os.environ['TNS_ADMIN'] = str(local_wallet_path)

# Determinar si estamos en el entorno de Render
is_render = 'RENDER' in os.environ

# Obtener las credenciales de Google Cloud
credentials = obtener_credenciales_google(is_render)

# Crear el cliente de Google Cloud Storage usando las credenciales
storage_client = storage.Client(credentials=credentials)

# Configuración para el wallet y descarga
bucket_name = 'credenciales-bd-bucket'
wallet_file = 'wallet.zip'
flag_file = local_wallet_path / 'download_complete.flag'

# Descargar y extraer el wallet si es necesario
descargar_y_extraer_wallet(storage_client, bucket_name, wallet_file, local_wallet_path, flag_file)

# Configuración de la ubicación del wallet para la base de datos Oracle
wallet_location = os.path.abspath(local_wallet_path)

# Configuración de la base de datos Oracle
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': 'djangodbtest_high',
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'OPTIONS': {
            'wallet_location': wallet_location,
            'wallet_password': os.getenv('WALLET_PASSWORD'),
        }
    },
}

# Configuración de Django
SECRET_KEY = os.environ.get('SECRET_KEY', default='hasdjdashjshajdhjshajdshdj')
DEBUG = not is_render
ALLOWED_HOSTS = ['*']

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'test_v2.core',
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

ROOT_URLCONF = 'test_v2.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'test_v2.wsgi.application'

LANGUAGE_CODE = 'es'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

if is_render:
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
