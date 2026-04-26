import sys
import os

# Yolu ekle
sys.path.insert(0, '/Users/dolunayozeren/Desktop/Antigravity/_knowledge/credentials/oauth')
from google_auth import get_drive_service

try:
    drive_service = get_drive_service('outreach')
    
    file_id = '1DdrIZzWpdksuOQMnlxfffyW8ewAN4WsNVt_pdDZojm4'
    user_permission = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': 'gmail-n8n@massive-hexagon-369717.iam.gserviceaccount.com'
    }
    
    command = drive_service.permissions().create(
        fileId=file_id,
        body=user_permission,
        fields='id'
    )
    res = command.execute()
    print("Permission ID:", res.get('id'))
    print("Sheet shared successfully!")
except Exception as e:
    print("Failed to share:", str(e))
