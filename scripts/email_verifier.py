import requests
import time
import re
from typing import Optional
from .config import MAIL_READER_URL


class EmailVerifier:
    def __init__(self):
        pass
    
    def get_verification_code(self, email: str, max_attempts: int = 10) -> Optional[str]:
        print(f"Waiting for verification code: {email}")

        for attempt in range(max_attempts):
            try:
                url = f"{MAIL_READER_URL}?mail={email}"
                response = requests.get(url, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    mails = []
                    if "data" in data and "mailFolder" in data["data"]:
                        mails = data["data"]["mailFolder"]
                    elif "mails" in data:
                        mails = data["mails"]

                    # If newest emails are last, iterate from newest to oldest
                    for mail in reversed(mails):
                        subject = mail.get("subject", "")
                        content = mail.get("message", mail.get("content", ""))

                        if "verification" in subject.lower() or "verify" in subject.lower() or "code" in subject.lower():
                            # Try extracting from subject line first
                            code = self._extract_verification_code(subject)
                            if code:
                                print(f"Verification code found in subject: {code}")
                                return code
                            
                            # If not found in subject, try extracting from content
                            code = self._extract_verification_code(content)
                            if code:
                                print(f"Verification code found in content: {code}")
                                return code

                elif response.status_code == 401:
                    print(f"API Error: HTTP 401 - {email} failed, adding to failed_mails")
                    if not hasattr(self, "failed_mails"):
                        self.failed_mails = []
                    self.failed_mails.append(email)
                    return None

                print(f"Attempt {attempt + 1}/{max_attempts} - verification code not received yet...")
                time.sleep(10)
            except Exception as e:
                print(f"Mail check error: {e}")
                time.sleep(5)

        print("Verification code could not be retrieved")
        return None
    
    def _extract_verification_code(self, content: str) -> Optional[str]:
        patterns = [
            r'(\d{6})\s+is your verification code',  # Code before "is your verification code"
            r'verification code[:\s]*(\d{6})',       # Code after "verification code"
            r'code[:\s]*(\d{6})',                    # Generic code pattern
            r'(\d\s+\d\s+\d\s+\d\s+\d\s+\d)',        # Spaced digits pattern like "7 3 0 1 3 5"
            r'(\d{6})'                               # Any 6 digits
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                code = match.group(1)
                # If it's spaced digits, remove spaces
                if ' ' in code:
                    code = code.replace(' ', '')
                
                if len(code) == 6 and code.isdigit():
                    return code
        
        return None
