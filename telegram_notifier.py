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

def get_badge(platform: str, email_type: str) -> str:
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
    badge = get_badge(platform, email_type)

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
