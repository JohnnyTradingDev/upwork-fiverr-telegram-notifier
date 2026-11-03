import os
from dotenv import load_dotenv

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(ENV_PATH)

# Gmail Configuration
GMAIL_USER = os.getenv("GMAIL_USER", "").strip()
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "").strip()
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# Upwork Session Cookie (for scraping full descriptions through Cloudflare)
UPWORK_COOKIE = os.getenv("UPWORK_COOKIE", "").strip()

# Platform Flags
ENABLE_UPWORK = os.getenv("ENABLE_UPWORK", "True").lower() in ("true", "1", "yes")
ENABLE_FIVERR = os.getenv("ENABLE_FIVERR", "True").lower() in ("true", "1", "yes")

# Niche Filter Configuration
# If True: only jobs classified as 'financial_video' will trigger immediate alerts.
# Non-matching jobs are saved to the database for daily summary.
# Direct messages/invites/offers are ALWAYS alerted immediately regardless of this flag.
ONLY_FINANCIAL_VIDEO_ALERTS = os.getenv("ONLY_FINANCIAL_VIDEO_ALERTS", "True").lower() in ("true", "1", "yes")

# Daily Summary Configuration (Hour in user timezone, e.g. 22 = 10 PM)
DAILY_SUMMARY_HOUR = int(os.getenv("DAILY_SUMMARY_HOUR", "22"))
TIMEZONE_OFFSET = int(os.getenv("TIMEZONE_OFFSET", "7"))

# IDLE refresh interval (seconds) - recommended 10-15 minutes (Gmail drops idle after ~29m)
IDLE_REFRESH_SECONDS = int(os.getenv("IDLE_REFRESH_SECONDS", "900"))
