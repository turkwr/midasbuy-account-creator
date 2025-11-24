# Midasbuy Account Creator

An educational/demo tool that fetches temporary emails from providers and automates account creation on the target site using Selenium. Secrets live in environment variables so nothing sensitive is committed.

## Prerequisites
- Python 3.10+ installed
- Firefox + GeckoDriver available in PATH

## Setup
1) Install dependencies: `pip install -r requirements.txt`
2) Copy `.env.example` to `.env` and fill in the values below

## Configuration (.env)
- `AMC_EMAIL_API_KEY`: Email provider API key (required)
- `AMC_DEFAULT_PASSWORD`: Password used when creating accounts (required)
- `AMC_PROXY_RESET_URL`: Proxy provider reset URL (optional; skip IP reset if empty)
- `AMC_EMAIL_API_BASE`: Email purchase API base URL (default: `https://api.xmailhub.net/purchase`)
- `AMC_MAIL_READER_BASE`: Mail reader API base URL (default: `https://api.xmailhub.net/mailreader`)
- `AMC_EMAIL_PROVIDERS`: Comma-separated provider list (default: `hotmail,outlook`)
- `AMC_EMAIL_COUNT_TARGET`: Number of emails to collect (default: 10)
- `AMC_ACCOUNT_COUNT_FOR_IP_RESET`: Accounts created before triggering IP reset (default: 10)
- `AMC_MIDAS_REGISTER_URL`: Target registration page (default: `https://www.midasbuy.com/midasbuy/tr/login#reg`)

## Running
- Windows: `python main.py`
- Linux/macOS: `python main.py`
- Output files (`mails.txt`, `results.txt`, `failed_mails.txt`) are ignored by Git; keep them out of commits anyway.

## Notes and safety
- Use this project for educational and testing purposes only.
- Store API keys and passwords only in `.env` or environment variables.
- Clear output files before sharing the repository or logs.
