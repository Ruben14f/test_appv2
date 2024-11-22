
import os
import json
from pathlib import Path
from google.cloud import storage
from google.oauth2 import service_account
import zipfile


def obtener_credenciales_google(is_render):
    """
    Obtener credenciales de Google Cloud dependiendo del entorno (local o Render).

    Args:
        is_render (bool): Indica si se está ejecutando en el entorno de Render.

    Returns:
        google.oauth2.service_account.Credentials: Credenciales para usar Google Cloud.
    """
    if is_render:
        # En Render, se usa un JSON almacenado en la variable de entorno
        credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        if not credentials_json:
            raise ValueError("La variable de entorno GOOGLE_APPLICATION_CREDENTIALS_JSON no está definida.")
        return service_account.Credentials.from_service_account_info(json.loads(credentials_json))
    else:
        # En local, se usa un archivo físico de credenciales
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not credentials_path:
            raise ValueError("La variable de entorno GOOGLE_APPLICATION_CREDENTIALS no está definida.")
        return service_account.Credentials.from_service_account_file(credentials_path)


def descargar_y_extraer_wallet(storage_client, bucket_name, wallet_file, local_wallet_path, flag_file):
    """
    Descargar y extraer el archivo ZIP del wallet desde Google Cloud Storage si aún no se ha descargado.

    Args:
        storage_client (google.cloud.storage.Client): Cliente de Google Cloud Storage.
        bucket_name (str): Nombre del bucket donde está almacenado el wallet.
        wallet_file (str): Nombre del archivo ZIP del wallet en el bucket.
        local_wallet_path (Path): Ruta local donde se extraerá el wallet.
        flag_file (Path): Archivo de bandera para indicar que el wallet ya se descargó y extrajo.
    """
    # Solo descargar y extraer si no existe el archivo de bandera
    if not flag_file.exists():
        if not local_wallet_path.exists():
            # Crear el directorio si no existe
            local_wallet_path.mkdir(parents=True)

        # Descargar el archivo ZIP del wallet desde el bucket
        try:
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(wallet_file)
            zip_path = local_wallet_path / wallet_file
            blob.download_to_filename(str(zip_path))

            # Descomprimir el archivo ZIP, evitando subcarpetas
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for member in zip_ref.namelist():
                    filename = Path(member).name
                    if filename:  # Evitar carpetas vacías
                        target_path = local_wallet_path / filename
                        with zip_ref.open(member) as source, open(target_path, "wb") as target:
                            target.write(source.read())

            # Eliminar el archivo ZIP después de la descompresión para liberar espacio
            os.remove(zip_path)

            # Crear un archivo de bandera para evitar futuras descargas
            flag_file.touch()

        except Exception as e:
            print(f"Error configurando Google Cloud Storage: {e}")
