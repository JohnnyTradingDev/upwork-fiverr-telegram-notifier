import sys
from imapclient import IMAPClient
from config import GMAIL_USER, GMAIL_APP_PASSWORD, IMAP_SERVER, IMAP_PORT
from parser import parse_freelance_email
from classifier import classify_job
import db
from datetime import datetime, timezone, timedelta

def rescan():
    db.init_db()
    with IMAPClient(IMAP_SERVER, port=IMAP_PORT, ssl=True) as client:
        client.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        client.select_folder("INBOX")
        uids = client.search(["SINCE", "29-Sep-2026"])
        print(f"Scanning {len(uids)} emails received today (29-Sep-2026)...")
        
        for uid in uids:
            try:
                raw_data = client.fetch([uid], ["RFC822"])
                if uid not in raw_data or b"RFC822" not in raw_data[uid]:
                    continue
                raw_email = raw_data[uid][b"RFC822"]
                parsed = parse_freelance_email(raw_email)
                
                if not parsed.get("is_supported"):
                    continue
                    
                category, tags = classify_job(
                    title=parsed.get("title", ""),
                    snippet=parsed.get("snippet", ""),
                    client_info=parsed.get("client_info", "")
                )
                
                print(f"UID {uid} | [{category:15}] {parsed.get('title', '')[:55]} | Tags: {tags}")
                
                is_direct = parsed.get("email_type") in ("invitation", "offer", "message", "order", "revision")
                notified = (category == "financial_video" or is_direct)
                
                db.save_job(
                    uid=uid,
                    platform=parsed.get("platform", "upwork"),
                    email_type=parsed.get("email_type", "job_alert"),
                    category=category,
                    title=parsed.get("title", ""),
                    budget=parsed.get("budget", ""),
                    client_info=parsed.get("client_info", ""),
                    url=parsed.get("url", ""),
                    snippet=parsed.get("snippet", ""),
                    notified_immediately=notified
                )
            except Exception as e:
                print(f"Error on UID {uid}: {e}")

    stats = db.get_daily_stats("2026-09-29")
    print("\n=== KẾT QUẢ THỐNG KÊ NGÀY 2026-09-29 ===")
    print(f"Tổng số job Video: {stats['total_video']}")
    print(f"Job Video Tài chính / Trading / Crypto: {stats['financial_video']}")
    print(f"Các job Video khác: {stats['other_video']}")
    print(f"Chi tiết job tài chính: {stats['financial_jobs']}")

if __name__ == "__main__":
    rescan()
