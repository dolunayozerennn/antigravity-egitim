import os
import sys
from googleapiclient.http import MediaFileUpload

# ── Merkezi Google Auth ──────────────────────────────────────────────────────
# Kök dizinde barınan google_auth.py üzerinden Token JSON okur (Railway Uyumlu)
from core.google_auth import get_drive_service

def authenticate_google_drive():
    """Merkezi google_auth modülü üzerinden Drive service döndür."""
    return get_drive_service("outreach")

def _extract_folder_id(folder_url: str):
    folder_id = None
    if "folders/" in folder_url:
         folder_id = folder_url.split("folders/")[1].split("?")[0]
    elif "id=" in folder_url:
         folder_id = folder_url.split("id=")[1].split("&")[0]
    return folder_id

def get_or_create_subfolder(service, parent_id: str, folder_name: str) -> str:
    """
    Checks if a subfolder exists within the parent_id. If not, creates it.
    Returns the subfolder's Drive ID.
    """
    try:
        query = f"'{parent_id}' in parents and name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        
        if len(files) > 0:
            return files[0]['id']
            
        print(f"Creating new '{folder_name}' folder in Drive...")
        file_metadata = {
            'name': folder_name,
            'parents': [parent_id],
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')
    except Exception as e:
        print(f"Error creating/fetching subfolder: {e}")
        return parent_id

def check_covers_exist(folder_url: str) -> bool:
    """
    Checks if YouTube thumbnail covers already exist in the given Google Drive folder.
    Looks for files containing 'THUMBNAIL' or 'KAPAK' in their names.
    """
    if not folder_url:
        return False
        
    service = authenticate_google_drive()
    if not service:
        return False
        
    folder_id = _extract_folder_id(folder_url)
    if not folder_id:
        return False
        
    try:
        # Search for files with THUMBNAIL or KAPAK in the name
        query = f"'{folder_id}' in parents and (name contains 'THUMBNAIL' or name contains 'KAPAK') and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)", pageSize=1).execute()
        files = results.get('files', [])
        return len(files) > 0
    except Exception as e:
        print(f"Error checking existing covers in Drive: {e}")
        return False

def count_existing_covers(folder_url: str) -> int:
    """
    THUMBNAIL alt klasörünün içindeki kapak dosyalarını sayar.
    Not: Kapaklar upload_cover_to_drive() tarafından THUMBNAIL alt klasörüne yüklenir.
    Bu fonksiyon da aynı yerde arar — tutarlılık garantisi.
    """
    if not folder_url:
        return 0
    service = authenticate_google_drive()
    if not service:
        return 0
    folder_id = _extract_folder_id(folder_url)
    if not folder_id:
        return 0
    try:
        # 1) THUMBNAIL alt klasörünü bul
        subfolder_query = (
            f"'{folder_id}' in parents and name = 'THUMBNAIL' "
            f"and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        )
        subfolder_results = service.files().list(
            q=subfolder_query, fields="files(id)"
        ).execute()
        subfolders = subfolder_results.get('files', [])
        if not subfolders:
            return 0
        # 2) Alt klasörün içindeki dosyaları say (klasörleri hariç tut)
        thumbnail_folder_id = subfolders[0]['id']
        count_query = (
            f"'{thumbnail_folder_id}' in parents "
            f"and mimeType != 'application/vnd.google-apps.folder' and trashed = false"
        )
        count_results = service.files().list(
            q=count_query, fields="files(id)", pageSize=20
        ).execute()
        return len(count_results.get('files', []))
    except Exception as e:
        print(f"Error counting existing covers in Drive: {e}")
        return 0

def upload_cover_to_drive(file_path: str, folder_url: str, file_name: str = None):
    """
    Uploads a YouTube thumbnail to a specific Google Drive folder.
    Creates a 'THUMBNAIL' subfolder within the video folder.
    """
    if not os.path.exists(file_path):
         print(f"File not found: {file_path}")
         return False
         
    service = authenticate_google_drive()
    if not service:
         return False
         
    folder_id = _extract_folder_id(folder_url)
         
    if not folder_id:
         print(f"Could not extract folder ID from URL: {folder_url}")
         return False

    print(f"Preparing to upload {file_path}...")
    target_folder_id = get_or_create_subfolder(service, folder_id, 'THUMBNAIL')
    print(f"Uploading to THUMBNAIL Subfolder ID: {target_folder_id}...")
    
    file_metadata = {
        'name': file_name if file_name else os.path.basename(file_path),
        'parents': [target_folder_id]
    }
    media = MediaFileUpload(file_path, mimetype='image/png')
    
    try:
         file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
         print(f"Successfully uploaded! Drive File ID: {file.get('id')}")
         return True
    except Exception as e:
         print(f"Failed to upload to Google Drive: {e}")
         return False

if __name__ == '__main__':
    pass
