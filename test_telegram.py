import sys
import time
from telegram_notifier import send_telegram_alert

if __name__ == "__main__":
    print("1. Gửi tin nhắn test Upwork...")
    upwork_ok = send_telegram_alert(
        subject="Invitation to interview: Fullstack Python / AI Engineer Needed",
        sender="Upwork Notifications <upwork@t.upwork.com>",
        email_type="invitation",
        platform="upwork",
        title="Fullstack Python / AI Engineer Needed",
        budget="Hourly: $50.00 - $75.00",
        client_info="✅ Payment Verified | $80k+ spent | ⭐ 4.95/5 | 📍 United States",
        snippet="We are seeking an experienced engineer to develop an automated real-time notification pipeline. Must have solid Python, IMAP, and Telegram Bot experience.",
        url="https://www.upwork.com"
    )
    
    time.sleep(1)
    
    print("2. Gửi tin nhắn test Fiverr...")
    fiverr_ok = send_telegram_alert(
        subject="You got an order from alex_crypto!",
        sender="Fiverr Orders <no-reply@e.fiverr.com>",
        email_type="order",
        platform="fiverr",
        title="Đơn hàng mới từ @alex_crypto - Gói Premium Bot",
        budget="$150.00",
        client_info="👤 Khách hàng: @alex_crypto",
        snippet="Chúc mừng! Bạn vừa nhận được 1 đơn hàng mới cho Gig: 'I will develop automated Telegram bots and scripts'. Hạn giao hàng: 3 ngày.",
        url="https://www.fiverr.com"
    )

    if upwork_ok and fiverr_ok:
        print("✅ Thành công! Đã gửi cả 2 tin nhắn mẫu (Upwork & Fiverr) tới Telegram của bạn.")
    else:
        print(f"Kết quả: Upwork={upwork_ok}, Fiverr={fiverr_ok}")
