import sys
from datetime import datetime, timezone, timedelta
from config import TIMEZONE_OFFSET
import db
from telegram_notifier import send_daily_summary

def trigger_summary(date_str: str = None) -> bool:
    db.init_db()
    if not date_str:
        user_now = datetime.now(timezone(timedelta(hours=TIMEZONE_OFFSET)))
        date_str = user_now.strftime("%Y-%m-%d")
    
    print(f"Generating summary for date: {date_str}...")
    stats = db.get_daily_stats(date_str)
    print(f"Total jobs recorded: {stats['total']}")
    print(f"Categories breakdown: {stats['categories']}")
    print(f"Financial video jobs: {len(stats['financial_jobs'])}")
    
    ok = send_daily_summary(stats)
    return ok

if __name__ == "__main__":
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    success = trigger_summary(target_date)
    if success:
        print("✅ Thành công! Đã gửi tin nhắn tổng kết tới Telegram.")
    else:
        print("❌ Gửi tổng kết thất bại. Vui lòng kiểm tra log hoặc token bot.")
