import json
import urllib.request
import urllib.error
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings

class SendGridAPIBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        
        api_key = getattr(settings, 'SENDGRID_API_KEY', None)
        if not api_key:
            return 0
            
        success_count = 0
        url = 'https://api.sendgrid.com/v3/mail/send'
        
        for message in email_messages:
            payload = {
                "personalizations": [
                    {
                        "to": [{"email": to_email} for to_email in message.to],
                        "subject": message.subject
                    }
                ],
                "from": {
                    "email": message.from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', 'notifications@employeehub.com')
                },
                "content": [
                    {
                        "type": "text/plain",
                        "value": message.body
                    }
                ]
            }
            
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                method='POST'
            )
            
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status in (200, 202):
                        success_count += 1
            except Exception as e:
                # Catch and print error output for logs visibility
                print(f"SendGrid API send failed: {e}")
                
        return success_count
