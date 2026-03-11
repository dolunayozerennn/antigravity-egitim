import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def authenticate_google_drive():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        except Exception as e:
            print(f"Warning: Failed to load existing token.json: {e}")
            os.remove('token.json')
            creds = None
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                 print("Error: credentials.json not found! Please provide Google Drive OAuth credentials.")
                 return None
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080, prompt='consent')
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    return build('drive', 'v3', credentials=creds)

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
    Checks if covers already exist in the given Google Drive folder.
    It looks for files containing 'KAPAK' in their names.
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
        # Search for files with KAPAK in the name within this folder
        query = f"'{folder_id}' in parents and name contains 'KAPAK' and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)", pageSize=1).execute()
        files = results.get('files', [])
        return len(files) > 0
    except Exception as e:
        print(f"Error checking existing covers in Drive: {e}")
        return False

def upload_cover_to_drive(file_path: str, folder_url: str, file_name: str = None):
    """
    Uploads a file to a specific Google Drive folder.
    Expects folder_url to be a standard drive link from which we can extract the ID.
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
    target_folder_id = get_or_create_subfolder(service, folder_id, 'KAPAK')
    print(f"Uploading to KAPAK Subfolder ID: {target_folder_id}...")
    
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
    # Test execution
    # upload_cover_to_drive("outputs/autonomous_cover_final.png", "YOUR_TEST_FOLDER_URL_HERE")
    pass
