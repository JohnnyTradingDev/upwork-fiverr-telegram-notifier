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

def handle_command(cmd_text: str):
    parts = cmd_text.strip().split()
    cmd = parts[0].lower()
    user_now = datetime.now(timezone(timedelta(hours=TIMEZONE_OFFSET)))
    today_str = user_now.strftime("%Y-%m-%d")

    if cmd in ("/start", "/help"):
        msg = (
            "👋 <b>Xin chào Johnny!</b>\n"
            "Bot săn job Upwork & Fiverr đang túc trực 24/7.\n\n"
            "📌 <b>Các lệnh nhanh:</b>\n"
            "✍️ /draft - Soạn nhanh Proposal cho job mới nhất\n"
            "✍️ /draft [id] - Soạn Proposal cho job theo ID (vd: /draft 1125)\n"
            "🎯 /top - 5 job phù hợp trong 7 ngày\n"
            "🔎 /fit [id] - Điểm phù hợp và điều cần hỏi\n"
            "📊 /summary - Xem tổng kết job Video hôm nay\n"
            "🔥 /today - Xem các job Video Tài chính hôm nay\n"
            "⚡ /status - Kiểm tra trạng thái server & Gmail\n"
            "🧪 /test - Gửi lại tin nhắn mẫu thử nghiệm"
        )
        send_reply(msg)

    elif cmd == "/top":
        from job_fit import rank_jobs
        ranked = rank_jobs(db.get_recent_jobs(), limit=5)
        lines = ["🎯 <b>SHORTLIST 7 NGÀY</b>", "Điểm khớp với demo, không phải xác suất trúng job."]
        if not ranked:
            lines.append("Chưa có job phù hợp để xếp hạng trong 7 ngày qua.")
        for item in ranked:
            job, fit = item['job'], item['fit']
            lines.append(f"\n<b>#{job['id']} · {fit['score']}/100 · {escape_html(fit['label'])}</b>\n{escape_html(str(job.get('title', ''))[:180])}")
            if fit['reasons']:
                lines.append(escape_html(fit['reasons'][0]))
            if fit['gaps']:
                lines.append("Cần kiểm tra: " + escape_html(fit['gaps'][0]))
            lines.append(f"/fit {job['id']} · /draft {job['id']}")
        send_reply("\n".join(lines))

    elif cmd == "/fit":
        from job_fit import score_job, format_fit
        if len(parts) != 2 or not parts[1].isdigit():
            send_reply("Dùng /fit [id], ví dụ /fit 1125. Xem ID trong /top.")
            return
        job = db.get_job(int(parts[1]))
        if not job:
            send_reply("Không tìm thấy job theo ID này.")
            return
        send_reply(f"<b>ĐỘ PHÙ HỢP JOB #{job['id']}</b>\n" + escape_html(format_fit(score_job(job))))

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

    elif cmd in ("/draft", "/proposal"):
        job_id = None
        if len(parts) > 1:
            if len(parts) != 2 or not parts[1].isdigit():
                send_reply("Dùng /draft [id] với ID trong /top, hoặc /draft cho job mới nhất.")
                return
            job_id = int(parts[1])

        job = db.get_job(job_id)
        if not job:
            send_reply("❌ <b>Không tìm thấy job trong database.</b>")
            return

        from proposal_generator import draft_proposal
        proposal_text = draft_proposal(job)
        jid = job.get("id")
        title = escape_html(job.get("title", ""))
        budget = escape_html(job.get("budget", ""))
        url = job.get("url", "")

        msg = (
            f"✍️ <b>PROPOSAL GỢI Ý CHO JOB #{jid}</b>\n"
            f"📌 <b>Tiêu đề:</b> {title}\n"
        )
        if budget:
            msg += f"💰 <b>Ngân sách:</b> <code>{budget}</code>\n"
        if url:
            msg += f"👉 <a href=\"{url}\">Mở link Upwork</a>\n"

        msg += (
            f"\n📋 <b>Bản nháp chào thầu:</b>\n"
            f"<pre>{escape_html(proposal_text)}</pre>\n\n"
            f"💡 <i>Bản nháp cần đọc lại, bổ sung mẫu liên quan và xác nhận phạm vi trước khi gửi.</i>"
        )
        send_reply(msg)

def handle_callback_query(cq: dict):
    cq_id = cq.get("id")
    from_user = cq.get("from", {})
    from_id = str(from_user.get("id", ""))
    if from_id != str(TELEGRAM_CHAT_ID):
        return

    # Acknowledge callback query immediately so button spinner stops
    try:
        requests.post(f"{TELEGRAM_API}/answerCallbackQuery", json={"callback_query_id": cq_id, "text": "⚡ Đang tạo Proposal..."}, timeout=5)
    except Exception:
        pass

    data = cq.get("data", "")
    if data.startswith("draft:"):
        target_id_str = data.split("draft:")[1]
        job = None
        if target_id_str.isdigit():
            val = int(target_id_str)
            job = db.get_job_by_uid(val)

        if not job:
            send_reply("❌ <b>Không tìm thấy dữ liệu job này trong database.</b>")
            return

        from proposal_generator import draft_proposal
        proposal_text = draft_proposal(job)
        jid = job.get("id")
        title = escape_html(job.get("title", ""))
        budget = escape_html(job.get("budget", ""))
        url = job.get("url", "")

        msg = (
            f"⚡ <b>PROPOSAL CHÀO THẦU CẤP TỐC (Job #{jid})</b>\n"
            f"📌 <b>Tiêu đề:</b> {title}\n"
        )
        if budget:
            msg += f"💰 <b>Ngân sách:</b> <code>{budget}</code>\n"
        if url:
            msg += f"👉 <a href=\"{url}\">Mở link Upwork để nộp thầu</a>\n"

        msg += (
            f"\n📋 <b>Bản nháp chào thầu:</b>\n"
            f"<pre>{escape_html(proposal_text)}</pre>\n\n"
            f"💡 <i>Bản nháp cần đọc lại, bổ sung mẫu liên quan và xác nhận phạm vi trước khi gửi.</i>"
        )
        send_reply(msg)

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

                # Handle inline button click (callback_query)
                cq = update.get("callback_query")
                if cq:
                    handle_callback_query(cq)
                    continue

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
