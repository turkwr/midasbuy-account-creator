import requests
import urllib3
from .config import PROXY_RESET_URL

# Disable SSL warnings when verification is disabled
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ProxyManager:
    def __init__(self):
        pass
    
    def reset_ip(self) -> bool:
        try:
            if not PROXY_RESET_URL:
                print("Proxy reset URL is not configured (set AMC_PROXY_RESET_URL). Skipping IP reset.")
                return False

            print("Resetting IP address...")
            # Disable SSL verification for buymobileproxy.com due to certificate issues
            response = requests.get(PROXY_RESET_URL, timeout=30, verify=False)
            
            if response.status_code == 200:
                print("IP address reset successfully")
                return True
            else:
                print(f"IP reset failed with status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"IP reset error: {e}")
            return False
