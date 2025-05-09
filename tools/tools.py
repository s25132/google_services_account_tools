import io
import os
from datetime import datetime
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
import pandas as pd

def get_or_create_folder_id_by_name(folder_name, drive_service):
    query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}'"
    
    response = drive_service.files().list(
        q=query,
        spaces='drive',
        fields="files(id, name)",
        pageSize=10
    ).execute()

    folders = response.get('files', [])
    
    if folders:
        folder = folders[0]
        print(f"Found folder: {folder['name']}, ID: {folder['id']}")
        return folder['id']

    # Folder nie istnieje – tworzymy nowy
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }

    folder = drive_service.files().create(
        body=folder_metadata,
        fields='id'
    ).execute()

    print(f"Created folder: {folder_name}, ID: {folder['id']}")
    return folder['id']


def get_latest_file_id(suffix, folder_name, drive_service):
    
    folder_id = get_or_create_folder_id_by_name(folder_name, drive_service)

    conditions = [f"'{folder_id}' in parents"]
    if suffix:
        conditions.append(f"name contains '{suffix}'")
    
    query = " and ".join(conditions)

    response = drive_service.files().list(
        q=query,
        fields="files(id, name, modifiedTime)",
        orderBy="modifiedTime desc"
    ).execute()

    files = response.get('files', [])

    if not files:
        print("No files {suffix} found in the specified folder.")
        return None

    latest_file = files[0]
    print(f"Latest file ID: {latest_file['id']}, Name: {latest_file['name']}, Modified Time: {latest_file['modifiedTime']}")
    return latest_file['id']



def download_file(suffix, folder_name, destination_path, drive_service):

    file_id = get_latest_file_id(suffix, folder_name, drive_service)

    if not file_id:
        return None

    request = drive_service.files().get_media(fileId=file_id)
    fh = io.FileIO(destination_path, mode='wb')
    
    downloader = MediaIoBaseDownload(fh, request)
    
    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f"Download {int(status.progress() * 100)}%.")

    return pd.read_csv(destination_path)

def upload_file(dataset, name, folder_name, drive_service):
    try:
        
        folder_id = get_or_create_folder_id_by_name(folder_name, drive_service)

        # Konwersja DataFrame do CSV
        csv_string = dataset.to_csv(index=False)
        csv_bytes = io.BytesIO(csv_string.encode('utf-8'))
        csv_bytes.seek(0)

        # Metadane pliku
        file_metadata = {
            'name': name + "_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
            'mimeType': 'text/csv'
        }


        file_metadata['parents'] = [folder_id]

        # Przygotuj plik do przesłania
        media = MediaIoBaseUpload(csv_bytes, mimetype='text/csv', resumable=True)

        # Prześlij plik
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        print(f"Plik został przesłany. ID: {file.get('id')}")
        return file.get('id')

    except Exception as e:
        print(f"Wystąpił błąd: {e}")
        return None

def upload_zip_file(zip_path, name, folder_name, drive_service):
    try:
        # Sprawdź, czy plik istnieje
        if not os.path.exists(zip_path):
            print(f"Plik {zip_path} nie istnieje.")
            return None

        # Pobierz lub utwórz folder na dysku Google
        folder_id = get_or_create_folder_id_by_name(folder_name, drive_service)

        # Otwórz plik ZIP jako strumień binarny
        with open(zip_path, "rb") as f:
            media = MediaIoBaseUpload(f, mimetype='application/zip', resumable=True)

            # Metadane pliku
            file_metadata = {
                'name': name + "_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".zip",
                'parents': [folder_id],
                'mimeType': 'application/zip'
            }

            # Prześlij plik
            file = drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

        print(f"Plik ZIP został przesłany. ID: {file.get('id')}")
        return file.get('id')

    except Exception as e:
        print(f"Wystąpił błąd: {e}")
        return None
    

def download_zip_file(suffix, folder_name, destination_path, drive_service):
    try:
        file_id = get_latest_file_id(suffix, folder_name, drive_service)

        if not file_id:
            print("Nie znaleziono pliku ZIP do pobrania.")
            return None

        request = drive_service.files().get_media(fileId=file_id)
        fh = io.FileIO(destination_path, mode='wb')

        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Pobrano {int(status.progress() * 100)}%.")

        print(f"Plik ZIP zapisany w: {destination_path}")
        return destination_path

    except Exception as e:
        print(f"Wystąpił błąd podczas pobierania ZIP: {e}")
        return None