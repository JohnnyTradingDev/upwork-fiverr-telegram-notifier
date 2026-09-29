import html
import logging
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

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
    url: str = ""
) -> bool:
    """
    Sends a formatted alert to Telegram for Upwork or Fiverr.
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
        lines.append(f"\n📝 <b>Nội dung:</b>\n<i>{clean_snippet}</i>")

    lines.append(f"\n📩 <i>Từ: {escape_html(sender)}</i>")

    message_text = "\n".join(lines)

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }

    if url and url.startswith("http"):
        btn_text = "🟢 Mở trực tiếp trên Fiverr" if platform == "fiverr" else "🚀 Mở trực tiếp trên Upwork"
        payload["reply_markup"] = {
            "inline_keyboard": [
                [{"text": btn_text, "url": url}]
            ]
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
    Sends the end-of-day summary to Telegram.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing!")
        return False

    date_str = stats.get("date_str", "")
    total = stats.get("total", 0)
    cats = stats.get("categories", {})
    financial_jobs = stats.get("financial_jobs", [])

    fin_count = cats.get("financial_video", 0)
    general_video_count = cats.get("general_video", 0)
    mech_count = cats.get("mechanical_3d", 0)
    other_count = cats.get("other", 0)

    lines = [
        f"<b>📊 TỔNG KẾT VIỆC LÀM HÔM NAY ({date_str})</b>\n",
        f"Tổng số cơ hội ghi nhận: <b>{total}</b> jobs\n",
        f"🎯 <b>Video Tài chính (Ngách của bạn):</b> <b>{fin_count}</b> jobs",
        f"🎬 <b>Video Editing chung:</b> {general_video_count} jobs",
        f"⚙️ <b>Cơ khí / 3D CAD (Ngách cũ):</b> {mech_count} jobs",
        f"📂 <b>Ngành nghề khác:</b> {other_count} jobs\n"
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
