from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import WebDriverException, NoSuchWindowException, TimeoutException
import time
import requests
import random
from typing import Optional
from .config import MIDAS_REGISTER_URL, DEFAULT_PASSWORD, XPATHS, SELENIUM_CONFIG, FILES
from .email_verifier import EmailVerifier


class AccountCreator:
    def __init__(self):
        self.driver = None
        self.email_verifier = EmailVerifier()
        
    def setup_firefox(self) -> webdriver.Firefox:
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        # Add user agent to appear more like a regular browser
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0")
        
        driver = webdriver.Firefox(options=options)
        driver.implicitly_wait(SELENIUM_CONFIG["implicit_wait"])
        driver.set_page_load_timeout(SELENIUM_CONFIG["page_load_timeout"])
        
        return driver
    
    def check_network_connectivity(self, test_url: str = None) -> bool:
        """Check if network connectivity is available"""
        if test_url is None:
            test_url = MIDAS_REGISTER_URL
            
        try:
            # Test connectivity to the specified URL
            response = requests.head(test_url, timeout=SELENIUM_CONFIG["connectivity_timeout"])
            if response.status_code in [200, 301, 302, 403]:  # Common successful responses
                print("Network connectivity confirmed")
                return True
            else:
                print(f"Network check failed with status code: {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"Network connectivity check failed: {e}")
            return False
    
    def wait_for_network_recovery(self, max_wait_time: int = 60) -> bool:
        """Wait for network connectivity to recover"""
        print("Waiting for network connectivity to recover...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            if self.check_network_connectivity():
                return True
            time.sleep(5)
        
        print(f"Network connectivity not restored after {max_wait_time} seconds")
        return False
    
    def wait_for_proxy_setup(self):
        print("Firefox opened, please set up your proxy now.")
        print("Press Enter when you are ready...")
        input()
        print("Starting process...")
    
    def is_browser_context_valid(self) -> bool:
        """Check if the browser context is still valid"""
        try:
            if self.driver is None:
                return False
            # Try to access window handles to check if context is valid
            _ = self.driver.window_handles
            return True
        except (WebDriverException, NoSuchWindowException):
            return False
    
    def restart_browser_if_needed(self) -> bool:
        """Restart browser if context is invalid"""
        try:
            if not self.is_browser_context_valid():
                print("Browser context is invalid, restarting browser...")
                self.close_browser()
                time.sleep(2)  # Give time for cleanup
                
                # Try to start new browser instance
                retry_count = 3
                for i in range(retry_count):
                    try:
                        self.driver = self.setup_firefox()
                        print("Browser restarted successfully")
                        return True
                    except Exception as e:
                        print(f"Browser restart attempt {i+1} failed: {e}")
                        if i < retry_count - 1:
                            time.sleep(3)
                        else:
                            print("Failed to restart browser after multiple attempts")
                            return False
            return True  # Browser was already valid
            
        except Exception as e:
            print(f"Error in restart_browser_if_needed: {e}")
            return False
    
    def safe_navigate(self, url: str, max_retries: int = None) -> bool:
        """Safely navigate to URL with enhanced retry logic, exponential backoff, and connectivity checks"""
        if max_retries is None:
            max_retries = SELENIUM_CONFIG["max_retries"]
        
        retry_delay_base = SELENIUM_CONFIG["retry_delay_base"]
        
        for attempt in range(max_retries):
            try:
                print(f"Navigation attempt {attempt + 1} to {url}")
                
                # Check network connectivity before attempting navigation (if not disabled)
                if not SELENIUM_CONFIG.get("skip_network_check", False):
                    if not self.check_network_connectivity(url):
                        if SELENIUM_CONFIG.get("fallback_navigation", True):
                            print("Network check failed, but fallback navigation enabled - continuing...")
                        else:
                            if not self.wait_for_network_recovery():
                                print(f"Network connectivity failed on attempt {attempt + 1}")
                                if attempt < max_retries - 1:
                                    delay = retry_delay_base * (2 ** attempt) + random.uniform(1, 3)
                                    print(f"Waiting {delay:.1f} seconds before retry...")
                                    time.sleep(delay)
                                continue
                
                # Ensure browser context is valid
                if not self.is_browser_context_valid():
                    print("Browser context invalid, restarting...")
                    if not self.restart_browser_if_needed():
                        continue
                
                # Set appropriate timeout for this attempt
                if attempt == 0:
                    timeout = SELENIUM_CONFIG["navigation_timeout"]
                else:
                    timeout = SELENIUM_CONFIG["retry_timeout"]
                
                self.driver.set_page_load_timeout(timeout)
                
                # Attempt navigation
                print(f"Attempting to load {url} with {timeout}s timeout")
                self.driver.get(url)
                
                # Verify page loaded successfully
                WebDriverWait(self.driver, 10).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
                
                print(f"Successfully navigated to {url}")
                return True
                
            except TimeoutException as e:
                print(f"Navigation attempt {attempt + 1} timed out: {e}")
                
                # Try to stop page loading if possible
                try:
                    self.driver.execute_script("window.stop();")
                except:
                    pass
                    
            except (WebDriverException, NoSuchWindowException) as e:
                print(f"Navigation attempt {attempt + 1} failed with WebDriver error: {e}")
                
            except Exception as e:
                print(f"Navigation attempt {attempt + 1} failed with unexpected error: {e}")
            
            # If this wasn't the last attempt, wait and potentially restart browser
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                delay = retry_delay_base * (2 ** attempt) + random.uniform(1, 5)
                print(f"Waiting {delay:.1f} seconds before retry {attempt + 2}...")
                time.sleep(delay)
                
                # Consider restarting browser after 2 failed attempts
                if attempt >= 1:
                    print("Multiple failures detected, restarting browser...")
                    self.restart_browser_if_needed()
        
        print(f"Failed to navigate to {url} after {max_retries} attempts")
        return False
    
    def save_successful_account(self, email: str, password: str):
        """Save successful account creation to results.txt"""
        try:
            with open(FILES["results_file"], "a") as f:
                f.write(f"{email}':{password}'\n")
            print(f"Successful account saved to {FILES['results_file']}: {email}")
        except Exception as e:
            print(f"Error saving successful account: {e}")
    
    def save_failed_email(self, email: str):
        """Save failed email to failed_mails.txt"""
        try:
            with open(FILES["failed_mails_file"], "a") as f:
                f.write(f"{email}\n")
            print(f"Failed email saved to {FILES['failed_mails_file']}: {email}")
        except Exception as e:
            print(f"Error saving failed email: {e}")
    
    def create_account(self, email: str) -> bool:
        try:
            print(f"Creating account: {email}")
            
            # Use safe navigation instead of direct get
            if not self.safe_navigate(MIDAS_REGISTER_URL):
                print(f"Failed to navigate to registration page for {email}")
                self.save_failed_email(email)
                return False
            
            wait = WebDriverWait(self.driver, SELENIUM_CONFIG["request_timeout"])
            
            # Cookie consent
            try:
                cookie_button = self.driver.find_element(By.XPATH, "/html/body/div[1]/div[6]/div[3]/div/div[2]/div[1]")
                cookie_button.click()
                time.sleep(1)
            except:
                pass
            
            # Email input
            email_input = wait.until(EC.presence_of_element_located((By.XPATH, XPATHS["email_input"])))
            email_input.clear()
            email_input.send_keys(email)
            
            # Password input
            password_input = self.driver.find_element(By.XPATH, XPATHS["password_input"])
            password_input.clear()
            password_input.send_keys(DEFAULT_PASSWORD)
            
            # Country selection
            try:
                country_button = self.driver.find_element(By.XPATH, XPATHS["country_select"])
                country_button.click()
                time.sleep(1)
                turkey_option = self.driver.find_element(By.XPATH, "//div[contains(text(), 'Turkey')]")
                turkey_option.click()
            except:
                pass
            
            # Birth date
            try:
                birth_date = self.driver.find_element(By.XPATH, XPATHS["birth_date"])
                birth_date.click()
                time.sleep(1)
                # Select day 9
                day_option = self.driver.find_element(By.XPATH, "/html/div/div[3]/ul/li[2]/span")
                day_option.click()
                
            except:
                pass
            
            # Accept terms
            try:
                terms_checkbox = self.driver.find_element(By.XPATH, XPATHS["terms_checkbox"])
                if not terms_checkbox.is_selected():
                    terms_checkbox.click()
            except:
                pass
            
            # Submit registration
            submit_button = self.driver.find_element(By.XPATH, XPATHS["submit_button"])
            submit_button.click()
            
            # Wait for email verification
            success = self._handle_email_verification(email)
            
            if success:
                self.save_successful_account(email, DEFAULT_PASSWORD)
            else:
                self.save_failed_email(email)
            
            return success
            
        except Exception as e:
            print(f"Account creation error: {e}")
            self.save_failed_email(email)
            return False
    
    def _handle_email_verification(self, email: str) -> bool:
        try:
            # Wait for the verification code input
            wait = WebDriverWait(self.driver, SELENIUM_CONFIG["request_timeout"])
            verification_input = wait.until(EC.presence_of_element_located((By.XPATH, XPATHS["verification_input"])))
            
            # Retrieve verification code from API
            verification_code = self.email_verifier.get_verification_code(email)
            
            if verification_code:
                verification_input.clear()
                verification_input.send_keys(verification_code)
                
                verify_button = self.driver.find_element(By.XPATH, XPATHS["verify_button"])
                verify_button.click()
                
                # Wait 10 seconds for site to redirect to main page
                time.sleep(10)
                print(f"Account created successfully: {email}")
                return True
            else:
                print(f"Verification code could not be retrieved: {email}")
                return False
                
        except Exception as e:
            print(f"Email verification error: {e}")
            return False
    
    def clear_browser_cache(self, max_retries: int = 3):
        """Clear browser cache with retry logic for context errors"""
        for attempt in range(max_retries):
            try:
                if not self.is_browser_context_valid():
                    if not self.restart_browser_if_needed():
                        continue
                
                # Clear cookies and storage
                self.driver.delete_all_cookies()
                try:
                    self.driver.execute_script("window.localStorage.clear();")
                    self.driver.execute_script("window.sessionStorage.clear();")
                except Exception as e:
                    print(f"Warning: Could not clear storage: {e}")
                
                print("Browser cache cleared")
                
                # After clearing cache, reset browser session for fresh start
                self._reset_browser_session()
                return
                
            except (WebDriverException, NoSuchWindowException) as e:
                print(f"Cache clearing error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    if not self.restart_browser_if_needed():
                        time.sleep(2)
                else:
                    print(f"Cache clearing failed after {max_retries} attempts")
            except Exception as e:
                print(f"Unexpected cache clearing error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    break
    
    def _reset_browser_session(self):
        """Close current tab and open new one for fresh session"""
        try:
            # Get current window handles
            handles = self.driver.window_handles
            
            if len(handles) > 1:
                # If multiple tabs open, close current tab
                self.driver.close()
                # Switch to remaining tab
                self.driver.switch_to.window(handles[0])
            else:
                # If only one tab, open new tab and close old one
                self.driver.execute_script("window.open('');")
                new_handles = self.driver.window_handles
                # Switch to new tab
                self.driver.switch_to.window(new_handles[-1])
                # Close the old tab
                if len(new_handles) > 1:
                    old_handle = new_handles[0]
                    self.driver.switch_to.window(old_handle)
                    self.driver.close()
                    # Switch back to new tab
                    self.driver.switch_to.window(new_handles[-1])
            
            print("Browser session reset with new tab")
            
        except Exception as e:
            print(f"Error resetting browser session: {e}")
            # If tab management fails, just continue with current tab
    
    def start_browser(self):
        self.driver = self.setup_firefox()
        self.wait_for_proxy_setup()
    
    def close_browser(self):
        """Safely close the browser"""
        try:
            if self.driver:
                self.driver.quit()
                print("Browser closed")
        except Exception as e:
            print(f"Browser closing error (expected if context was already lost): {e}")
        finally:
            self.driver = None
