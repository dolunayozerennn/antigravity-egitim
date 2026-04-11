import os
import sys
import base64
from email.mime.text import MIMEText

# Add _knowledge to path
_antigravity_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(_antigravity_root, "_knowledge", "credentials", "oauth"))
from google_auth import get_gmail_service

def send_email(service, to, subject, body):
    try:
        message = MIMEText(body, 'plain') # plain instead of html to match the text structure
        message['to'] = to
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        sent_message = service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()
        return True, sent_message['id']
    except Exception as e:
        return False, str(e)

def main():
    service = get_gmail_service("swc") # d.ozeren@sweatco.in

    emails_to_send = [
        {"creator": "Conner Mather", "first_name": "Conner", "email": "cmathersocial@gmail.com"},
        {"creator": "Michelle Rider", "first_name": "Michelle", "email": "jj@33andwest.com"},
        {"creator": "Leon Ondieki", "first_name": "Leon", "email": "Leon@ondbusiness.com"},
        {"creator": "Natalie", "first_name": "Natalie", "email": "annie@corporatenatalie.com"},
        {"creator": "Josie Kay", "first_name": "Josie", "email": "josiekayyyy@gmail.com"},
        {"creator": "Kristen Hollingshaus", "first_name": "Kristen", "email": "contact@hauskris.com"},
    ]

    body_template = """Hi {first_name},

I'm Dolunay from the Sweatcoin team. We've been following your TikTok content and absolutely love your style—especially how relatable and engaging your videos are!

We're currently looking for creative partners to help us with some content sourcing. We'd love to collaborate with you to create a short, authentic UGC-style video for our brand. (For context, Sweatcoin is a health app that rewards users for their daily steps, and we think your audience would really resonate with our message).

Could you let us know if you're open to this kind of collaboration right now? If so, we'd appreciate it if you could share your media kit and let us know your rates for a single dedicated video. 

Looking forward to hearing from you.

Best regards,

Dolunay Özeren
Sweatcoin Team"""

    for target in emails_to_send:
        subject = f"Collaboration Inquiry: Sweatcoin x {target['creator']}"
        body = body_template.format(first_name=target['first_name'])
        
        success, res = send_email(service, target['email'], subject, body)
        if success:
            print(f"✅ Sent to {target['creator']} ({target['email']}) - ID: {res}")
        else:
            print(f"❌ Failed to send to {target['creator']} ({target['email']}) - Error: {res}")

if __name__ == "__main__":
    main()
