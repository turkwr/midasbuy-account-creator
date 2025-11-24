from scripts.email_fetcher import EmailFetcher
from scripts.account_creator import AccountCreator
from scripts.proxy_manager import ProxyManager
from scripts.config import ACCOUNT_COUNT_FOR_IP_RESET
import time


class AutoMailCreator:
    def __init__(self):
        self.email_fetcher = EmailFetcher()
        self.account_creator = AccountCreator()
        self.proxy_manager = ProxyManager()
        self.accounts_created = 0
        
    def run(self):
        try:
            # Start the browser and allow time for proxy setup
            self.account_creator.start_browser()
            
            # Continuous loop
            while True:
                print("=== New cycle starting ===")
                
                # Check email count
                email_count = self.email_fetcher.get_email_count_in_file()
                print(f"Current email count: {email_count}")
                
                # If there are fewer than 10 emails, fetch them one by one
                if email_count < 10:
                    print(f"Email count is insufficient ({email_count}), collecting emails one by one...")
                    self.email_fetcher.collect_emails_one_by_one(10)
                
                # When 10 emails are ready, begin account creation
                final_email_count = self.email_fetcher.get_email_count_in_file()
                if final_email_count >= 10:
                    print(f"We have {final_email_count} emails, starting account creation...")
                    
                    # Take the first 10 emails
                    emails = self.email_fetcher.load_emails_from_file()[:10]
                    
                    # Create an account for each email
                    batch_count = 0
                    for email in emails:
                        try:
                            success = self.account_creator.create_account(email)
                            
                            # Remove the used email from the file
                            self.email_fetcher.remove_email_from_file(email)
                            
                            if success:
                                self.accounts_created += 1
                                batch_count += 1
                                print(f"Total accounts created: {self.accounts_created}")
                            
                            # Clear cache to reduce side effects between accounts
                            self.account_creator.clear_browser_cache()
                            
                        except Exception as e:
                            print(f"Error processing email {email}: {e}")
                            # Remove the problematic email so the loop can continue
                            self.email_fetcher.remove_email_from_file(email)
                        
                        # Reset IP when the threshold is reached
                        if self.accounts_created > 0 and self.accounts_created % ACCOUNT_COUNT_FOR_IP_RESET == 0:
                            self.proxy_manager.reset_ip()
                            time.sleep(10)
                        
                        # Short pause between accounts
                        time.sleep(2)
                    
                    print(f"{batch_count} accounts created in this batch. Starting new cycle...")
                else:
                    print("Could not collect enough emails, retrying...")
                
                time.sleep(5)  # Short delay between cycles
            
        except KeyboardInterrupt:
            print("Process stopped by user")
        except Exception as e:
            print(f"Unhandled error: {e}")
        finally:
            self.account_creator.close_browser()


def main():
    auto_mail_creator = AutoMailCreator()
    auto_mail_creator.run()


if __name__ == "__main__":
    main()
