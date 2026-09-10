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
    """Collapses whitespace and removes duplicate consecutive lines."""
    lines = []
    last_line = ""
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s == last_line:
            continue
        lines.append(s)
        last_line = s
    return "\n".join(lines)

def detect_platform(sender: str, subject: str, body: str) -> str:
    """Detects whether the email is from Upwork, Fiverr, or Unknown."""
    combined_header = f"{sender} {subject}".lower()
    combined_all = f"{sender} {subject} {body}".lower()

    if "upwork" in combined_header or "@upwork.com" in combined_all or "@t.upwork.com" in combined_all or "@email.upwork.com" in combined_all:
        return "upwork"
    if "fiverr" in combined_header or "@fiverr.com" in combined_all or "@e.fiverr.com" in combined_all:
        return "fiverr"

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

    # URL extraction
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

    # Budget extraction
    budget = ""
    bm1 = re.search(r"(?:Fixed(?:\s*[- ]?price)?|Hourly|Budget):\s*\$[0-9,]+(?:\.[0-9]{2})?(?:\s*-\s*\$[0-9,]+(?:\.[0-9]{2})?)?", plain_text or cleaned_text, re.IGNORECASE)
    if bm1:
        budget = bm1.group(0)
    else:
        bm2 = re.search(r"(Fixed-price|Hourly|Fixed|Budget)\s*[\u2022·•:\s]+\s*(\$[0-9,]+(?:\.[0-9]{2})?(?:\s*-\s*\$[0-9,]+(?:\.[0-9]{2})?)?)", cleaned_text, re.IGNORECASE)
        if bm2:
            budget = f"{bm2.group(1)}: {bm2.group(2)}"
        else:
            alt_budget = re.search(r"\$[0-9,]+(?:\.[0-9]{2})?\s*/\s*hr", cleaned_text, re.IGNORECASE)
            if alt_budget:
                budget = alt_budget.group(0)

    # Client Info
    client_info_parts = []
    if re.search(r"Payment (?:method )?verified", cleaned_text, re.IGNORECASE):
        client_info_parts.append("✅ Payment Verified")

    rating_m = re.search(r"(?:Payment (?:method )?verified\s*[\u2022·•\s]+([0-5]\.[0-9]{1,2})|([0-5]\.[0-9]{1,2})\s+of\s+5\s+stars)", cleaned_text, re.IGNORECASE)
    if rating_m:
        val = rating_m.group(1) or rating_m.group(2)
        client_info_parts.append(f"⭐ {val}/5")

    spent_m = re.search(r"\$[0-9,kM\.]+\+?\s+spent", cleaned_text, re.IGNORECASE)
    if spent_m:
        client_info_parts.append(spent_m.group(0))

    country_m = re.search(r"spent\s*[\u2022·•\s]+([A-Za-z ]{2,25}?)(?:\n|View|$)", cleaned_text)
    if country_m:
        country_name = country_m.group(1).strip()
        if country_name.lower() not in ["view", "job", "details", "posted"]:
            client_info_parts.append(f"📍 {country_name}")

    client_info = " | ".join(client_info_parts)

    # Title cleanup
    job_title = subject
    strip_prefixes = [
        r"^new job alert:\s*",
        r"^jobs you might like:\s*",
        r"^invitation to interview:\s*",
        r"^you've been invited to submit a proposal to the job\s*"
    ]
    for p in strip_prefixes:
        job_title = re.sub(p, "", job_title, flags=re.IGNORECASE).strip()

    # Extract Skills
    skills_found = []
    skills_m = re.search(r"Skills:\s*\n((?:[^\n:]+:\s*https?://[^\n]+\n?)+)", plain_text)
    if skills_m:
        skills_found = [re.sub(r":\s*https?://.*", "", line).strip() for line in skills_m.group(1).splitlines() if line.strip()]

    # Form concise snippet
    lines = cleaned_text.splitlines()
    snippet_lines = []
    ignore_starts = [
        "view job", "submit proposal", "hello", "hi ", "upwork",
        "this job was just posted", "new job alert", "jobs you might like",
        "don't miss out", "invitation to interview", "skills:", "posted"
    ]
    footer_stops = [
        "view job details", "you received this email", "manage your alert",
        "privacy policy", "contact support", "notification settings", "530 lytton"
    ]

    for l in lines:
        l_lower = l.lower()
        if any(f in l_lower for f in footer_stops):
            break
        if any(l_lower.startswith(x) for x in ignore_starts):
            continue
        if l in skills_found:
            continue
        if l == job_title or l in ["Fixed-price", "Hourly", "•", "USA"] or l.startswith("$"):
            continue
        if len(l) > 10:
            snippet_lines.append(l)
        if len(snippet_lines) >= 3:
            break

    if skills_found:
        snippet_lines.append(f"🏷 <b>Kỹ năng:</b> {', '.join(skills_found[:5])}")

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

    budget = ""
    price_match = re.search(r"(?:Total|Price|Amount|Budget|Order):\s*\$([0-9,]+(?:\.[0-9]{2})?)", cleaned_text, re.IGNORECASE)
    if price_match:
        budget = f"${price_match.group(1)}"
    else:
        dollar_match = re.search(r"\$[0-9,]+(?:\.[0-9]{2})?", cleaned_text)
        if dollar_match:
            budget = dollar_match.group(0)

    client_info = ""
    buyer_match = re.search(r"(?:from|Buyer|by)\s+@?([a-zA-Z0-9_\-]+)", subject, re.IGNORECASE)
    if not buyer_match:
        buyer_match = re.search(r"(?:from|Buyer|by)\s+@?([a-zA-Z0-9_\-]+)", cleaned_text, re.IGNORECASE)
    if buyer_match:
        buyer_name = buyer_match.group(1)
        if buyer_name.lower() not in ["fiverr", "the", "a", "an", "your"]:
            client_info = f"👤 Khách: @{buyer_name}"

    title = subject

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

    soup = BeautifulSoup(html_text, "html.parser") if html_text else None
    extracted_text = ""
    if soup:
        for script in soup(["script", "style", "head", "meta"]):
            script.decompose()
        extracted_text = soup.get_text(separator="\n")
    else:
        extracted_text = plain_text

    cleaned_text = clean_text(extracted_text)
    platform = detect_platform(sender, subject, plain_text + html_text)

    if platform == "upwork":
        details = parse_upwork_details(subject, cleaned_text, soup, plain_text)
    elif platform == "fiverr":
        details = parse_fiverr_details(subject, cleaned_text, soup, plain_text)
    else:
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

parse_upwork_email = parse_freelance_email
