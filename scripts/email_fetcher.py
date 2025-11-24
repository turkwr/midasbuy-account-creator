import requests
import time
import json
from typing import List, Dict, Optional
from .config import EMAIL_ENDPOINTS, EMAIL_COUNT_TARGET, FILES


class EmailFetcher:
    def __init__(self):
        self.emails = []
        
    def fetch_single_email(self, url: str, label: str) -> Optional[str]:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            print(f"Request made for {label}: {data}")
            
            if data.get("status") == 200 and "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
                email_data = data["data"][0]
                if "Email" in email_data:
                    return email_data["Email"]

            if data.get("status") == 0 and data.get("message") == "No stock":
                print(f"No stock for {label}: {data.get('message')}")
                return None
            
            if data.get("email"):
                return data["email"]
                
            return None
        except requests.exceptions.RequestException as e:
            print(f"Request error for {label}: {e}")
            return None
        except (json.JSONDecodeError, IndexError) as e:
            print(f"JSON parse error or unexpected format for {label}: {e}")
            return None
    
    def fetch_emails_from_source(self, source: str, target_count: int) -> List[str]:
        url = EMAIL_ENDPOINTS[source]
        emails = []
        
        print(f"Fetching emails from {source}...")
        
        while len(emails) < target_count:
            email = self.fetch_single_email(url, source)
            if email:
                emails.append(email)
                print(f"{source} email: {email}")
            else:
                print(f"Could not get email from {source}, retrying...")
            time.sleep(1)
            
        return emails
    
    
    def collect_emails_one_by_one(self, target_count: int = 10) -> bool:
        """Collect emails one by one and save immediately until target count is reached"""
        current_count = self.get_email_count_in_file()
        
        if current_count >= target_count:
            print(f"Already have {current_count} emails, no need to collect more")
            return True
            
        emails_needed = target_count - current_count
        print(f"Need {emails_needed} more emails to reach target of {target_count}")
        
        emails_collected = 0
        sources = list(EMAIL_ENDPOINTS.keys())
        source_index = 0
        
        while emails_collected < emails_needed:
            source = sources[source_index % len(sources)]
            url = EMAIL_ENDPOINTS[source]
            
            print(f"Fetching email from {source}...")
            email = self.fetch_single_email(url, source)
            
            if email:
                # Immediately save the email to file
                self.append_email_to_file(email)
                emails_collected += 1
                
                # Check if we've reached the target
                current_total = self.get_email_count_in_file()
                print(f"Progress: {current_total}/{target_count} emails collected")
                
                if current_total >= target_count:
                    print(f"Target of {target_count} emails reached!")
                    return True
            else:
                print(f"Failed to get email from {source}, trying next source...")
            
            source_index += 1
            time.sleep(1)  # Small delay between requests
        
        return True
    
    def collect_emails(self) -> List[str]:
        """Legacy method - kept for compatibility, now uses one-by-one collection"""
        print("Using legacy collect_emails method - switching to one-by-one collection")
        self.collect_emails_one_by_one(EMAIL_COUNT_TARGET)
        return self.load_emails_from_file()
    
    def save_emails_to_file(self, emails: List[str]):
        with open(FILES["mails_file"], "w") as f:
            for email in emails:
                f.write(f"{email}\n")
        print(f"{len(emails)} emails saved to {FILES['mails_file']}")
    
    def append_email_to_file(self, email: str):
        """Append a single email to mails.txt file immediately"""
        try:
            with open(FILES["mails_file"], "a") as f:
                f.write(f"{email}\n")
            print(f"Email immediately saved: {email}")
        except Exception as e:
            print(f"Error appending email to file: {e}")
    
    def load_emails_from_file(self) -> List[str]:
        try:
            with open(FILES["mails_file"], "r") as f:
                emails = [line.strip() for line in f.readlines() if line.strip()]
            return emails
        except FileNotFoundError:
            return []
    
    def remove_email_from_file(self, email: str):
        """Remove a specific email from mails.txt file"""
        try:
            emails = self.load_emails_from_file()
            if email in emails:
                emails.remove(email)
                with open(FILES["mails_file"], "w") as f:
                    for remaining_email in emails:
                        f.write(f"{remaining_email}\n")
                print(f"Email {email} removed from {FILES['mails_file']}")
            else:
                print(f"Email {email} not found in {FILES['mails_file']}")
        except Exception as e:
            print(f"Error removing email from file: {e}")
    
    def get_email_count_in_file(self) -> int:
        """Get the count of emails currently in mails.txt"""
        emails = self.load_emails_from_file()
        return len(emails)
    
    def get_emails(self) -> List[str]:
        existing_emails = self.load_emails_from_file()
        
        if len(existing_emails) >= EMAIL_COUNT_TARGET:
            print(f"{FILES['mails_file']} contains {len(existing_emails)} emails")
            return existing_emails[:EMAIL_COUNT_TARGET]
        
        print("Fetching new emails...")
        new_emails = self.collect_emails()
        self.save_emails_to_file(new_emails)
        return new_emails
