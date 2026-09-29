import sys
import time
from telegram_notifier import send_telegram_alert

if __name__ == "__main__":
    print("1. Gửi tin nhắn test Upwork (Ngách Video Tài chính)...")
    upwork_ok = send_telegram_alert(
        subject="New job alert: YouTube Video Editor for Crypto & Forex Channel",
        sender="Upwork Notification <donotreply@upwork.com>",
        email_type="job_alert",
        platform="upwork",
        category="financial_video",
        title="YouTube Video Editor for Crypto & Forex Channel (Shorts & Faceless)",
        budget="Hourly: $20.00 - $35.00",
        client_info="✅ Payment Verified | $40k+ spent | ⭐ 4.95/5 | 📍 United States",
        snippet="We need a talented video editor specializing in finance, crypto & forex content. Must know CapCut or Premiere to edit fast-paced shorts, reels and faceless YouTube videos with charts and b-roll.",
        url="https://www.upwork.com"
    )
    
    time.sleep(1)
    
    print("2. Gửi tin nhắn test Fiverr (Đơn hàng Video Tài chính)...")
    fiverr_ok = send_telegram_alert(
        subject="You got an order from trader_mike!",
        sender="Fiverr Orders <no-reply@e.fiverr.com>",
        email_type="order",
        platform="fiverr",
        category="financial_video",
        title="Đơn hàng mới từ @trader_mike - Video Editing Trading / Forex",
        budget="$120.00",
        client_info="👤 Khách hàng: @trader_mike",
        snippet="Chúc mừng! Bạn vừa nhận được đơn hàng mới cho Gig Video Editing Finance/Trading. Hạn giao: 2 ngày.",
        url="https://www.fiverr.com"
    )

    if upwork_ok and fiverr_ok:
        print("✅ Thành công! Đã gửi cả 2 tin nhắn mẫu đúng ngách Video Tài chính tới Telegram của bạn.")
    else:
        print(f"Kết quả: Upwork={upwork_ok}, Fiverr={fiverr_ok}")
