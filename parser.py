import re
import email
from email.message import Message
from email.header import decode_header
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def decode_mime_words(header_value: str) -> str:
    """Decodes MIME encoded header strings (e.g. =?UTF-8?B?...?=)."""
    if not header_value:
        return ""
    decoded_fragments = []
    for fragment, encoding in decode_header(header_value):
        if isinstance(fragment, bytes):
            try:
                decoded_fragments.append(fragment.decode(encoding or "utf-8", errors="replace"))
            except Exception:
                decoded_fragments.append(fragment.decode("utf-8", errors="replace"))
        else:
            decoded_fragments.append(str(fragment))
    return "".join(decoded_fragments)

def get_email_body(msg: Message) -> tuple[str, str]:
    """
    Extracts plain text and html bodies from an email Message object.
    Returns (plain_text, html_text).
    """
    plain_text = ""
    html_text = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))

            if "attachment" in content_disposition:
                continue

            charset = part.get_content_charset() or "utf-8"
            payload = part.get_payload(decode=True)
            if not payload:
                continue

            try:
                decoded_str = payload.decode(charset, errors="replace")
            except Exception:
                decoded_str = payload.decode("utf-8", errors="replace")

            if content_type == "text/plain":
                plain_text += decoded_str + "\n"
            elif content_type == "text/html":
                html_text += decoded_str + "\n"
    else:
        content_type = msg.get_content_type()
        charset = msg.get_content_charset() or "utf-8"
        payload = msg.get_payload(decode=True)
        if payload:
            try:
                decoded_str = payload.decode(charset, errors="replace")
            except Exception:
                decoded_str = payload.decode("utf-8", errors="replace")

            if content_type == "text/html":
                html_text = decoded_str
            else:
                plain_text = decoded_str

    return plain_text, html_text

def clean_text(text: str) -> str:
    """Collapses whitespace and extra blank lines."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)

def detect_platform(sender: str, subject: str, body: str) -> str:
    """Detects whether the email is from Upwork, Fiverr, or Unknown."""
    combined_header = f"{sender} {subject}".lower()
    combined_all = f"{sender} {subject} {body}".lower()

    if "upwork" in combined_header or "@upwork.com" in combined_all or "@t.upwork.com" in combined_all or "@email.upwork.com" in combined_all:
        return "upwork"
    if "fiverr" in combined_header or "@fiverr.com" in combined_all or "@e.fiverr.com" in combined_all:
        return "fiverr"

    # Fallback to body content check
    if "upwork.com" in combined_all:
        return "upwork"
    if "fiverr.com" in combined_all:
        return "fiverr"

    return "unknown"

def parse_upwork_details(subject: str, cleaned_text: str, soup: BeautifulSoup, plain_text: str) -> dict:
    sub_lower = subject.lower()
    if any(k in sub_lower for k in ["invitation to interview", "invited you", "lời mời"]):
        email_type = "invitation"
    elif any(k in sub_lower for k in ["job offer", "offer from", "contract offer"]):
        email_type = "offer"
    elif any(k in sub_lower for k in ["message from", "sent you a message"]):
        email_type = "message"
    elif any(k in sub_lower for k in ["proposal was", "proposal submitted", "proposal accepted"]):
        email_type = "proposal"
    elif any(k in sub_lower for k in ["jobs you might like", "new job", "job alert", "saved search"]):
        email_type = "job_alert"
    else:
        email_type = "general"

    # URL
    url = ""
    if soup:
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "upwork.com" in href:
                if any(x in href for x in ["/jobs/", "/proposals/", "/nx/wm/", "/messages/"]):
                    url = href
                    break
        if not url:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "upwork.com" in href and not any(x in href.lower() for x in ["unsubscribe", "preferences"]):
                    url = href
                    break

    if not url:
        match_url = re.search(r"https?://(?:www\.)?upwork\.com/[^\s\"'>]+", plain_text or cleaned_text)
        if match_url:
            url = match_url.group(0)

    # Budget
    budget = ""
    budget_patterns = [
        r"Hourly:\s*\$[0-9,]+(?:\.[0-9]{2})?(?:\s*-\s*\$[0-9,]+(?:\.[0-9]{2})?)?",
        r"Fixed[- ]price:\s*\$[0-9,]+(?:\.[0-9]{2})?",
        r"Budget:\s*\$[0-9,]+(?:\.[0-9]{2})?",
        r"\$[0-9,]+(?:\.[0-9]{2})?(?:\s*-\s*\$[0-9,]+(?:\.[0-9]{2})?)?\s*/\s*hr",
        r"\$[0-9,]+(?:\.[0-9]{2})?\s*Est\.\s*Budget"
    ]
    for pattern in budget_patterns:
        m = re.search(pattern, cleaned_text, re.IGNORECASE)
        if m:
            budget = m.group(0)
            break

    # Client Info
    client_info_parts = []
    if re.search(r"Payment (?:method )?verified", cleaned_text, re.IGNORECASE):
        client_info_parts.append("✅ Payment Verified")
    client_spent = re.search(r"\$[0-9,kM\.]+\+?\s+spent", cleaned_text, re.IGNORECASE)
    if client_spent:
        client_info_parts.append(client_spent.group(0))
    rating_match = re.search(r"([0-5]\.[0-9]{1,2})\s+of\s+5\s+stars", cleaned_text, re.IGNORECASE)
    if rating_match:
        client_info_parts.append(f"⭐ {rating_match.group(1)}/5")
    country_match = re.search(r"(?:Location|Country):\s*([A-Za-z\s]+)", cleaned_text, re.IGNORECASE)
    if country_match:
        client_info_parts.append(f"📍 {country_match.group(1).strip()}")

    client_info = " | ".join(client_info_parts)

    # Title
    job_title = ""
    if "invitation to interview:" in sub_lower:
        job_title = re.sub(r"(?i)invitation to interview:\s*", "", subject).strip()
    elif "you've been invited to submit a proposal to the job" in sub_lower:
        job_title = re.sub(r"(?i)you've been invited to submit a proposal to the job\s*", "", subject).strip()
    else:
        job_title = subject

    # Snippet
    lines = cleaned_text.splitlines()
    snippet_lines = []
    ignore_starts = ["view job", "submit proposal", "hello", "hi ", "upwork", "you have a new", "don't miss out", "invitation to interview"]
    for l in lines:
        if any(l.lower().startswith(x) for x in ignore_starts):
            continue
        if len(l) > 15:
            snippet_lines.append(l)
        if len(snippet_lines) >= 4:
            break

    snippet = "\n".join(snippet_lines) if snippet_lines else cleaned_text[:300]

    return {
        "email_type": email_type,
        "title": job_title,
        "budget": budget,
        "client_info": client_info,
        "snippet": snippet,
        "url": url
    }

def parse_fiverr_details(subject: str, cleaned_text: str, soup: BeautifulSoup, plain_text: str) -> dict:
    sub_lower = subject.lower()
    text_lower = cleaned_text.lower()

    if any(k in sub_lower for k in ["you got an order", "order placed", "received an order", "new order"]):
        email_type = "order"
    elif any(k in sub_lower for k in ["sent you a message", "new message", "inbox"]):
        email_type = "message"
    elif any(k in sub_lower for k in ["matched with a brief", "buyer request", "new brief", "opportunity"]):
        email_type = "brief"
    elif any(k in sub_lower for k in ["review", "feedback"]):
        email_type = "review"
    elif any(k in sub_lower for k in ["revision"]):
        email_type = "revision"
    else:
        email_type = "general"

    # URL
    url = ""
    if soup:
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "fiverr.com" in href:
                if any(x in href for x in ["/orders/", "/inbox/", "/users/", "/manage_orders/"]):
                    url = href
                    break
        if not url:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "fiverr.com" in href and not any(x in href.lower() for x in ["unsubscribe", "preferences", "privacy"]):
                    url = href
                    break

    if not url:
        match_url = re.search(r"https?://(?:www\.)?fiverr\.com/[^\s\"'>]+", plain_text or cleaned_text)
        if match_url:
            url = match_url.group(0)

    # Price / Order Amount
    budget = ""
    price_match = re.search(r"(?:Total|Price|Amount|Budget|Order):\s*\$([0-9,]+(?:\.[0-9]{2})?)", cleaned_text, re.IGNORECASE)
    if price_match:
        budget = f"${price_match.group(1)}"
    else:
        dollar_match = re.search(r"\$[0-9,]+(?:\.[0-9]{2})?", cleaned_text)
        if dollar_match:
            budget = dollar_match.group(0)

    # Buyer / Client Info
    client_info = ""
    buyer_match = re.search(r"(?:from|Buyer|by)\s+@?([a-zA-Z0-9_\-]+)", subject, re.IGNORECASE)
    if not buyer_match:
        buyer_match = re.search(r"(?:from|Buyer|by)\s+@?([a-zA-Z0-9_\-]+)", cleaned_text, re.IGNORECASE)
    if buyer_match:
        buyer_name = buyer_match.group(1)
        if buyer_name.lower() not in ["fiverr", "the", "a", "an", "your"]:
            client_info = f"👤 Khách: @{buyer_name}"

    # Title
    title = subject

    # Snippet
    lines = cleaned_text.splitlines()
    snippet_lines = []
    ignore_starts = ["view order", "view message", "reply now", "hello", "hi ", "fiverr", "great news"]
    for l in lines:
        if any(l.lower().startswith(x) for x in ignore_starts):
            continue
        if len(l) > 15:
            snippet_lines.append(l)
        if len(snippet_lines) >= 4:
            break

    snippet = "\n".join(snippet_lines) if snippet_lines else cleaned_text[:300]

    return {
        "email_type": email_type,
        "title": title,
        "budget": budget,
        "client_info": client_info,
        "snippet": snippet,
        "url": url
    }

def parse_freelance_email(raw_email_bytes: bytes) -> dict:
    """
    Parses an email byte stream, detecting platform (Upwork, Fiverr) and extracting details.
    """
    msg = email.message_from_bytes(raw_email_bytes)

    subject = decode_mime_words(msg.get("Subject", ""))
    sender = decode_mime_words(msg.get("From", ""))
    date = msg.get("Date", "")

    plain_text, html_text = get_email_body(msg)

    # Parse HTML soup
    soup = BeautifulSoup(html_text, "html.parser") if html_text else None
    extracted_text = ""
    if soup:
        for script in soup(["script", "style", "head", "meta"]):
            script.decompose()
        extracted_text = soup.get_text(separator="\n")
    else:
        extracted_text = plain_text

    cleaned_text = clean_text(extracted_text)

    # Detect platform
    platform = detect_platform(sender, subject, plain_text + html_text)

    if platform == "upwork":
        details = parse_upwork_details(subject, cleaned_text, soup, plain_text)
    elif platform == "fiverr":
        details = parse_fiverr_details(subject, cleaned_text, soup, plain_text)
    else:
        # Generic fallback
        details = {
            "email_type": "general",
            "title": subject,
            "budget": "",
            "client_info": "",
            "snippet": cleaned_text[:300],
            "url": ""
        }

    return {
        "platform": platform,
        "subject": subject,
        "sender": sender,
        "date": date,
        "email_type": details["email_type"],
        "title": details["title"],
        "budget": details["budget"],
        "client_info": details["client_info"],
        "snippet": details["snippet"],
        "url": details["url"],
        "is_supported": platform in ("upwork", "fiverr")
    }

# Backward compatibility alias
parse_upwork_email = parse_freelance_email
