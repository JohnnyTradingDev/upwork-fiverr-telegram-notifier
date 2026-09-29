import time
import logging
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TIMEZONE_OFFSET
import db
from telegram_notifier import send_daily_summary, escape_html
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("telegram_bot")

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def send_reply(text: str, reply_markup=None):
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(f"{TELEGRAM_API}/sendMessage", json=payload, timeout=10)
    except Exception as e:
        logger.error(f"Error sending bot reply: {e}")

def handle_command(cmd: str):
    cmd = cmd.strip().lower().split()[0]
    user_now = datetime.now(timezone(timedelta(hours=TIMEZONE_OFFSET)))
    today_str = user_now.strftime("%Y-%m-%d")

    if cmd in ("/start", "/help"):
        msg = (
            "👋 <b>Xin chào Johnny!</b>\n"
            "Bot săn job Upwork & Fiverr đang túc trực 24/7.\n\n"
            "📌 <b>Các lệnh nhanh:</b>\n"
            "📊 /summary - Xem tổng kết job Video hôm nay\n"
            "🔥 /today - Xem các job Video Tài chính hôm nay\n"
            "⚡ /status - Kiểm tra trạng thái server & Gmail\n"
            "🧪 /test - Gửi lại tin nhắn mẫu thử nghiệm"
        )
        send_reply(msg)

    elif cmd == "/summary":
        stats = db.get_daily_stats(today_str)
        send_daily_summary(stats)

    elif cmd == "/today":
        stats = db.get_daily_stats(today_str)
        financial_jobs = stats.get("financial_jobs", [])
        if not financial_jobs:
            send_reply(f"💡 <b>Hôm nay ({today_str})</b> chưa ghi nhận job Video Tài chính nào. Bot sẽ báo ngay khi xuất hiện!")
            return

        lines = [f"🔥 <b>CÁC JOB VIDEO TÀI CHÍNH HÔM NAY ({today_str}):</b>\n"]
        for i, j in enumerate(financial_jobs, 1):
            title = escape_html(j.get("title", ""))
            budget = escape_html(j.get("budget", ""))
            client = escape_html(j.get("client_info", ""))
            url = j.get("url", "")
            
            job_block = f"<b>{i}. {title}</b>\n"
            if budget:
                job_block += f"💰 Ngân sách: <code>{budget}</code>\n"
            if client:
                job_block += f"👤 Khách: {client}\n"
            if url:
                job_block += f"👉 <a href=\"{url}\">Mở trực tiếp trên Upwork</a>\n"
            lines.append(job_block)

        send_reply("\n".join(lines))

    elif cmd == "/status":
        stats = db.get_daily_stats(today_str)
        msg = (
            "⚡ <b>TRẠNG THÁI HỆ THỐNG:</b>\n\n"
            "🟢 <b>Server:</b> Hoạt động 24/7 (homesever)\n"
            "📡 <b>Chế độ Gmail:</b> IMAP IDLE Real-time Push (< 1s)\n"
            f"🕒 <b>Giờ server:</b> {user_now.strftime('%H:%M:%S (UTC+7)')}\n"
            f"📊 <b>Job Video hôm nay:</b> {stats['total_video']} (Tài chính: {stats['financial_video']})\n"
            "🛡️ <b>Bộ lọc:</b> Đang bật cảnh báo Red Flag & lọc ngách tài chính"
        )
        send_reply(msg)

    elif cmd == "/test":
        send_reply("🧪 Đang kích hoạt kiểm tra hệ thống...")
        from test_telegram import send_telegram_alert
        send_telegram_alert(
            subject="Test Command Triggered",
            sender="System",
            email_type="job_alert",
            category="financial_video",
            title="Kiểm tra tương tác 2 chiều thành công!",
            budget="Test: $50/hr",
            client_info="✅ System OK",
            snippet="Bot đang phản hồi lệnh của bạn từ Telegram theo thời gian thực.",
            url="https://www.upwork.com"
        )

def run_bot_listener():
    """Background loop polling for user commands via Telegram getUpdates."""
    logger.info("Starting Telegram interactive command listener...")
    offset = 0

    while True:
        try:
            url = f"{TELEGRAM_API}/getUpdates?offset={offset}&timeout=25"
            res = requests.get(url, timeout=30)
            if res.status_code != 200:
                time.sleep(5)
                continue

            data = res.json()
            if not data.get("ok"):
                time.sleep(5)
                continue

            for update in data.get("result", []):
                offset = update["update_id"] + 1
                message = update.get("message")
                if not message:
                    continue

                from_chat_id = str(message.get("chat", {}).get("id", ""))
                # Only respond to authorized chat id
                if from_chat_id != str(TELEGRAM_CHAT_ID):
                    continue

                text = message.get("text", "")
                if text.startswith("/"):
                    logger.info(f"Received Telegram command: {text}")
                    handle_command(text)

        except Exception as e:
            logger.debug(f"Bot listener tick error: {e}")
            time.sleep(3)
