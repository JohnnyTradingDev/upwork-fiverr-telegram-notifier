import html
import logging
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from red_flags import scan_red_flags
from job_fit import score_job

logger = logging.getLogger(__name__)

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

def escape_html(text: str) -> str:
    """Escapes HTML special characters for Telegram HTML mode."""
    if not text:
        return ""
    return html.escape(text)

def get_badge(platform: str, email_type: str, category: str = "") -> str:
    if category == "financial_video":
        if platform == "fiverr":
            return "🎯 [FIVERR - VIDEO TÀI CHÍNH / TRADING]"
        return "🎯 [UPWORK - VIDEO TÀI CHÍNH / TRADING]"

    if platform == "fiverr":
        badges = {
            "order": "📦 [FIVERR - ĐƠN HÀNG MỚI]",
            "message": "💬 [FIVERR - TIN NHẮN TỪ KHÁCH]",
            "brief": "🎯 [FIVERR - CƠ HỘI / MATCH BRIEF]",
            "review": "⭐ [FIVERR - ĐÁNH GIÁ MỚI]",
            "revision": "🔄 [FIVERR - YÊU CẦU CHỈNH SỬA]",
            "general": "🟢 [FIVERR - THÔNG BÁO]"
        }
        return badges.get(email_type, "🟢 [FIVERR - THÔNG BÁO]")
    else:
        # Default to Upwork
        badges = {
            "invitation": "🎯 [UPWORK - LỜI MỜI PHỎNG VẤN]",
            "offer": "🎉 [UPWORK - LỜI ĐỀ NGHỊ NHẬN VIỆC]",
            "message": "💬 [UPWORK - TIN NHẮN TỪ CLIENT]",
            "job_alert": "💼 [UPWORK - CÔNG VIỆC MỚI]",
            "proposal": "📋 [UPWORK - CẬP NHẬT PROPOSAL]",
            "general": "🔔 [UPWORK - THÔNG BÁO]"
        }
        return badges.get(email_type, "🔔 [UPWORK - THÔNG BÁO]")

def send_telegram_alert(
    subject: str,
    sender: str,
    email_type: str,
    platform: str = "upwork",
    category: str = "",
    job_title: str = "",
    title: str = "",
    budget: str = "",
    client_info: str = "",
    snippet: str = "",
    url: str = "",
    uid: int = None
) -> bool:
    """
    Sends a formatted alert to Telegram for Upwork or Fiverr,
    including Red Flag warnings and portfolio proof suggestions.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing!")
        return False

    display_title = title or job_title or subject
    badge = get_badge(platform, email_type, category)

    lines = [f"<b>{badge}</b>\n"]

    if display_title:
        lines.append(f"📌 <b>Tiêu đề:</b> {escape_html(display_title)}")

    if budget:
        budget_label = "Giá trị đơn:" if email_type == "order" else "Ngân sách:"
        lines.append(f"💰 <b>{budget_label}</b> <code>{escape_html(budget)}</code>")

    if client_info:
        lines.append(f"👤 <b>Khách hàng:</b> {escape_html(client_info)}")

    if snippet:
        clean_snippet = snippet.strip()
        if len(clean_snippet) > 1200:
            clean_snippet = clean_snippet[:1200] + "..."
        lines.append(f"\n📝 <b>Nội dung:</b>\n<i>{escape_html(clean_snippet)}</i>")

    # Scan for Red Flags in title + snippet
    corpus = f"{display_title} {snippet}".lower()
    flags = scan_red_flags(corpus)
    if flags:
        lines.append("\n🚨 <b>CẢNH BÁO RED FLAG:</b>")
        for f in flags:
            lines.append(f"• <i>{f}</i>")

    fit = score_job({"title": display_title, "snippet": snippet, "budget": budget})
    lines.append(f"\n🎯 <b>Độ phù hợp: {fit['score']}/100 · {fit['label']}</b>")
    for reason in fit['reasons'][:2]:
        lines.append("+ " + escape_html(reason))
    for gap in fit['gaps'][:2]:
        lines.append("Cần kiểm tra: " + escape_html(gap))
    lines.append("<i>Độ khớp với demo, không phải xác suất trúng job. /top để xem shortlist.</i>")

    lines.append(f"\n📩 <i>Từ: {escape_html(sender)}</i>")

    message_text = "\n".join(lines)

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }

    keyboard_row = []
    if url and url.startswith("http"):
        btn_text = "🟢 Mở trên Fiverr" if platform == "fiverr" else "🚀 Mở trên Upwork"
        keyboard_row.append({"text": btn_text, "url": url})

    if uid:
        keyboard_row.append({"text": "✍️ Soạn Proposal", "callback_data": f"draft:{uid}"})

    if keyboard_row:
        payload["reply_markup"] = {
            "inline_keyboard": [keyboard_row]
        }

    try:
        res = requests.post(TELEGRAM_API_URL, json=payload, timeout=10)
        res_data = res.json()
        if res.status_code == 200 and res_data.get("ok"):
            logger.info("Alert successfully sent to Telegram.")
            return True
        else:
            logger.warning(f"Telegram API responded with error: {res_data}")
            if "can't parse entities" in res_data.get("description", "").lower():
                logger.info("Retrying without HTML parse mode...")
                plain_payload = {
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": f"{badge}\n{display_title}\n\nBudget: {budget}\n\n{snippet}\n\nLink: {url}",
                    "disable_web_page_preview": False
                }
                res2 = requests.post(TELEGRAM_API_URL, json=plain_payload, timeout=10)
                return res2.status_code == 200 and res2.json().get("ok")
            return False
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False

def send_daily_summary(stats: dict) -> bool:
    """
    Sends the end-of-day summary comparing Financial Video jobs vs Other Video jobs.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing!")
        return False

    date_str = stats.get("date_str", "")
    total_video = stats.get("total_video", 0)
    fin_count = stats.get("financial_video", 0)
    other_video_count = stats.get("other_video", 0)
    financial_jobs = stats.get("financial_jobs", [])

    pct = f"{round((fin_count / total_video) * 100)}%" if total_video > 0 else "0%"

    lines = [
        f"<b>📊 TỔNG KẾT JOB VIDEO HÔM NAY ({date_str})</b>\n",
        f"Tổng số cơ hội Video ghi nhận: <b>{total_video}</b> jobs\n",
        f"🎯 <b>Video Tài chính / Crypto / Trading:</b> <b>{fin_count}</b> jobs ({pct})",
        f"🎬 <b>Các job Video khác:</b> {other_video_count} jobs\n"
    ]

    if financial_jobs:
        lines.append("🔥 <b>Các job Video Tài chính đã báo hôm nay:</b>")
        for i, j in enumerate(financial_jobs[:8], 1):
            title = escape_html(j.get("title", ""))
            budget = escape_html(j.get("budget", ""))
            url = j.get("url", "")
            budget_str = f" - <code>{budget}</code>" if budget else ""
            if url:
                lines.append(f"{i}. <a href=\"{url}\">{title}</a>{budget_str}")
            else:
                lines.append(f"{i}. {title}{budget_str}")
        if len(financial_jobs) > 8:
            lines.append(f"<i>... và {len(financial_jobs) - 8} job khác</i>")
    else:
        lines.append("<i>💡 Hôm nay chưa có job Video Tài chính mới nào. Bot vẫn đang túc trực 24/7!</i>")

    message_text = "\n".join(lines)

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    try:
        res = requests.post(TELEGRAM_API_URL, json=payload, timeout=10)
        res_data = res.json()
        if res.status_code == 200 and res_data.get("ok"):
            logger.info("Daily summary sent to Telegram successfully.")
            return True
        else:
            logger.warning(f"Failed to send summary: {res_data}")
            return False
    except Exception as e:
        logger.error(f"Error sending daily summary: {e}")
        return False
