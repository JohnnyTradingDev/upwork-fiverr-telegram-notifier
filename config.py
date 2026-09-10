import os
from dotenv import load_dotenv

load_dotenv()

# Gmail Configuration
GMAIL_USER = os.getenv("GMAIL_USER", "").strip()
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "").strip()
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# Platform Flags
ENABLE_UPWORK = os.getenv("ENABLE_UPWORK", "True").lower() in ("true", "1", "yes")
ENABLE_FIVERR = os.getenv("ENABLE_FIVERR", "True").lower() in ("true", "1", "yes")

# IDLE refresh interval (seconds) - recommended 10-15 minutes (Gmail drops idle after ~29m)
IDLE_REFRESH_SECONDS = int(os.getenv("IDLE_REFRESH_SECONDS", "900"))
