import os
import sys
import time
import json
import signal
import logging
from imapclient import IMAPClient
from config import (
    GMAIL_USER,
    GMAIL_APP_PASSWORD,
    IMAP_SERVER,
    IMAP_PORT,
    ENABLE_UPWORK,
    ENABLE_FIVERR,
    IDLE_REFRESH_SECONDS
)
from parser import parse_freelance_email
from telegram_notifier import send_telegram_alert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("freelance_notifier")

STATE_FILE = os.path.join(os.path.dirname(__file__), "state.json")
running = True
current_client = None

def signal_handler(signum, frame):
    global running, current_client
    logger.info("Signal received. Stopping gracefully...")
    running = False
    if current_client:
        try:
            current_client.shutdown()
        except Exception:
            pass
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read state file: {e}")
    return {"last_uid": 0}

def save_state(state: dict):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save state: {e}")

def process_new_messages(client: IMAPClient, state: dict) -> dict:
    last_uid = state.get("last_uid", 0)
    
    # Search for messages with UID greater than last_uid
    if last_uid > 0:
        search_criteria = ["UID", f"{last_uid + 1}:*"]
    else:
        search_criteria = ["ALL"]

    uids = client.search(search_criteria)
    
    # Filter only UIDs strictly greater than last_uid
    new_uids = [uid for uid in sorted(uids) if uid > last_uid]
    if not new_uids:
        return state

    logger.info(f"Found {len(new_uids)} new email(s). Processing...")

    for uid in new_uids:
        try:
            raw_data = client.fetch([uid], ["RFC822"])
            if uid not in raw_data or b"RFC822" not in raw_data[uid]:
                continue
            
            raw_email = raw_data[uid][b"RFC822"]
            parsed = parse_freelance_email(raw_email)
            platform = parsed.get("platform")

            if platform == "upwork" and not ENABLE_UPWORK:
                logger.info(f"Skipping Upwork email (disabled in config): '{parsed['subject']}'")
                state["last_uid"] = uid
                save_state(state)
                continue
            elif platform == "fiverr" and not ENABLE_FIVERR:
                logger.info(f"Skipping Fiverr email (disabled in config): '{parsed['subject']}'")
                state["last_uid"] = uid
                save_state(state)
                continue
            elif platform not in ("upwork", "fiverr"):
                logger.info(f"Skipping non-freelance email: '{parsed['subject']}' from {parsed['sender']}")
                state["last_uid"] = uid
                save_state(state)
                continue

            logger.info(f"🚀 {platform.upper()} email detected: '{parsed['subject']}' from {parsed['sender']}")
            
            sent = send_telegram_alert(
                subject=parsed["subject"],
                sender=parsed["sender"],
                email_type=parsed["email_type"],
                platform=parsed["platform"],
                title=parsed["title"],
                budget=parsed["budget"],
                client_info=parsed["client_info"],
                snippet=parsed["snippet"],
                url=parsed["url"]
            )
            
            if sent:
                logger.info(f"Telegram notification sent for UID {uid} ({platform})")
            else:
                logger.warning(f"Could not send Telegram notification for UID {uid}")

            state["last_uid"] = uid
            save_state(state)

        except Exception as e:
            logger.error(f"Error processing UID {uid}: {e}", exc_info=True)

    return state

def run_service():
    global running, current_client
    state = load_state()

    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        logger.error("GMAIL_USER or GMAIL_APP_PASSWORD is not set in .env! Please configure them.")
        logger.info("Exiting...")
        return

    backoff = 5

    while running:
        client = None
        try:
            logger.info(f"Connecting to {IMAP_SERVER}:{IMAP_PORT} as {GMAIL_USER}...")
            client = IMAPClient(IMAP_SERVER, port=IMAP_PORT, ssl=True)
            current_client = client
            client.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            select_info = client.select_folder("INBOX")
            logger.info("Connected to Gmail INBOX successfully!")

            # If this is the first run (last_uid is 0), initialize last_uid to latest UID
            if state.get("last_uid", 0) == 0:
                all_uids = client.search(["ALL"])
                if all_uids:
                    state["last_uid"] = max(all_uids)
                    logger.info(f"First run initialized: latest UID is {state['last_uid']}. Watching for new emails...")
                else:
                    state["last_uid"] = 0
                save_state(state)

            # Check if any messages arrived while we were disconnected
            state = process_new_messages(client, state)

            # Reset backoff on successful connect
            backoff = 5

            logger.info(f"Entering IMAP IDLE (real-time push mode). Refreshing every {IDLE_REFRESH_SECONDS}s...")

            while running:
                client.idle()
                idle_start = time.time()
                
                # Check in short intervals (e.g. 15s) so signals/stop requests are responsive
                has_updates = False
                while running and (time.time() - idle_start < IDLE_REFRESH_SECONDS):
                    responses = client.idle_check(timeout=15)
                    if responses:
                        logger.info(f"IDLE event received from Gmail: {responses}")
                        has_updates = True
                        break

                client.idle_done()

                if has_updates:
                    state = process_new_messages(client, state)

        except SystemExit:
            logger.info("Exiting on SystemExit.")
            break
        except Exception as e:
            logger.warning(f"Connection lost or error occurred: {e}")
            if running:
                logger.info(f"Reconnecting in {backoff} seconds...")
                time.sleep(backoff)
                backoff = min(backoff * 2, 120)
        finally:
            if client:
                try:
                    client.logout()
                except Exception:
                    pass
            current_client = None

    logger.info("Service has shut down.")

if __name__ == "__main__":
    run_service()
