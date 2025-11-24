import os
from pathlib import Path
from typing import Dict, List


def _load_dotenv(path: str = ".env") -> None:
    """Lightweight .env loader to keep secrets out of the codebase."""
    env_path = Path(path)
    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()


def _require_env(var_name: str, hint: str) -> str:
    """Read required env var with a clear error if it is missing."""
    value = os.getenv(var_name)
    if value:
        return value
    raise RuntimeError(f"Missing required environment variable {var_name}. {hint}")


# API credentials and endpoints
EMAIL_API_KEY = _require_env(
    "AMC_EMAIL_API_KEY",
    "Set AMC_EMAIL_API_KEY to your mail provider API key (keep it private; store in .env)."
)
EMAIL_API_BASE = os.getenv("AMC_EMAIL_API_BASE", "https://api.xmailhub.net/purchase")
EMAIL_PROVIDERS: List[str] = [
    provider.strip() for provider in os.getenv("AMC_EMAIL_PROVIDERS", "hotmail,outlook").split(",") if provider.strip()
]

EMAIL_ENDPOINTS: Dict[str, str] = {
    provider: f"{EMAIL_API_BASE}/{EMAIL_API_KEY}/{provider}/1"
    for provider in EMAIL_PROVIDERS
}

if not EMAIL_ENDPOINTS:
    raise RuntimeError(
        "No email providers configured. Set AMC_EMAIL_PROVIDERS (comma separated) to at least one provider name."
    )

MAIL_READER_BASE = os.getenv("AMC_MAIL_READER_BASE", "https://api.xmailhub.net/mailreader")
MAIL_READER_URL = f"{MAIL_READER_BASE}/{EMAIL_API_KEY}"

# Network / proxy settings
PROXY_RESET_URL = os.getenv(
    "AMC_PROXY_RESET_URL",
    ""  # Optional: set to enable automatic IP resets
)

# Target site
MIDAS_REGISTER_URL = os.getenv(
    "AMC_MIDAS_REGISTER_URL",
    "https://www.midasbuy.com/midasbuy/tr/login#reg"
)

# Account defaults
DEFAULT_PASSWORD = _require_env(
    "AMC_DEFAULT_PASSWORD",
    "Set AMC_DEFAULT_PASSWORD to the password you want newly created accounts to use."
)

EMAIL_COUNT_TARGET = int(os.getenv("AMC_EMAIL_COUNT_TARGET", "10"))
ACCOUNT_COUNT_FOR_IP_RESET = int(os.getenv("AMC_ACCOUNT_COUNT_FOR_IP_RESET", "10"))

XPATHS = {
    "email_input": "//*[@id='registerUsername']",
    "password_input": "//*[@id='registerPassword']",
    "country_select": "/html/body/div[1]/div[2]/div[2]/div/form/div[1]/div[1]/div[3]/div[2]",
    "region_select": "",
    "birth_date": "/html/body/div[1]/div[2]/div[2]/div/form/div[1]/div[1]/div[4]/div",
    "terms_checkbox": "/html/body/div[1]/div[2]/div[2]/div/form/div[1]/div[1]/div[5]/div[1]",
    "submit_button": "//*[@id='registerButton']",
    "verification_input": "//*[@id='activeCode']",
    "verify_button": "//*[@id='activeNextButton']"
}

SELENIUM_CONFIG = {
    "implicit_wait": 10,
    "page_load_timeout": 60,
    "request_timeout": 30,
    "navigation_timeout": 60,
    "retry_timeout": 90,
    "max_retries": 5,
    "retry_delay_base": 5,
    "connectivity_timeout": 10,
    "skip_network_check": False,
    "fallback_navigation": True
}

FILES = {
    "mails_file": "mails.txt",
    "results_file": "results.txt",
    "failed_mails_file": "failed_mails.txt"
}
