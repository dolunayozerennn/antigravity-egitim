import os
import base64
from email.message import EmailMessage
from typing import Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

class GmailClient:
    def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.json"):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.creds = self._authenticate()
        self.service = build('gmail', 'v1', credentials=self.creds)

    def _authenticate(self) -> Credentials:
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = self._run_oauth_flow()
            else:
                creds = self._run_oauth_flow()
                
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
                
        return creds

    def _run_oauth_flow(self) -> Credentials:
        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(f"Gmail API kimlik bilgileri bulunamadı: {self.credentials_path}")
        flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
        return flow.run_local_server(port=0)

    def send_email(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        message = EmailMessage()
        message.set_content(body)
        message['To'] = to
        message['From'] = "me"
        message['Subject'] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}

        try:
            sent_message = self.service.users().messages().send(userId="me", body=create_message).execute()
            return {"status": "success", "message_id": sent_message['id']}
        except HttpError as error:
            print(f"Gmail API Gönderim Hatası: {error}")
            return {"status": "error", "error_message": str(error)}
