import os
import json
from pathlib import Path
from dotenv import load_dotenv
from google.cloud import storage
from google.oauth2 import service_account
import zipfile

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
local_wallet_path = BASE_DIR / 'wallet'

os.environ['TNS_ADMIN'] = str(local_wallet_path)

# Determinar si estamos en el entorno de Render
is_render = 'RENDER' in os.environ

if is_render:
    # En Render usamos la variable de entorno que contiene el JSON de credenciales
    credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    if not credentials_json:
        raise ValueError("La variable de entorno GOOGLE_APPLICATION_CREDENTIALS_JSON no está definida.")
    # Crear las credenciales desde el JSON
    credentials = service_account.Credentials.from_service_account_info(json.loads(credentials_json))
else:
    # En local usamos el archivo de credenciales
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not credentials_path:
        raise ValueError("La variable de entorno GOOGLE_APPLICATION_CREDENTIALS no está definida.")
    # Crear credenciales desde el archivo
    credentials = service_account.Credentials.from_service_account_file(credentials_path)

# Crear el cliente de Google Cloud Storage usando las credenciales
storage_client = storage.Client(credentials=credentials)

bucket_name = 'credenciales-bd-bucket'
wallet_file = 'wallet.zip'
flag_file = local_wallet_path / 'download_complete.flag'  # Archivo de bandera para indicar que ya se descargó

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', default='hasdjdashjshajdhjshajdshdj')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = not is_render

ALLOWED_HOSTS = ['*']

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Application definition

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

# Configuración para evitar descargas y descompresiones redundantes del wallet
tnsnames_path = local_wallet_path / 'tnsnames.ora'

# Solo descargar y descomprimir si el archivo de bandera no existe
if not flag_file.exists():
    # Crear el directorio local para el wallet si no existe
    if not local_wallet_path.exists():
        local_wallet_path.mkdir(parents=True)

    # Descargar el archivo ZIP del bucket
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(wallet_file)
        zip_path = local_wallet_path / wallet_file
        blob.download_to_filename(str(zip_path))

        # Descomprimir el archivo, evitando crear subcarpetas adicionales
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for member in zip_ref.namelist():
                # Extraer solo el nombre del archivo, ignorando las subcarpetas
                filename = Path(member).name
                if filename:  # Evitar carpetas vacías
                    target_path = local_wallet_path / filename
                    with zip_ref.open(member) as source, open(target_path, "wb") as target:
                        target.write(source.read())

        # Eliminar el archivo ZIP después de la descompresión si lo deseas
        os.remove(zip_path)

        # Crear un archivo de bandera para evitar descargar en el futuro
        flag_file.touch()

    except Exception as e:
        print(f"Error configurando Google Cloud Storage: {e}")

# Configuración de la ubicación del wallet
wallet_location = os.path.abspath(local_wallet_path)

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

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'es'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

if is_render:
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
