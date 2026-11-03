import re

RED_FLAG_PATTERNS = [
    (
        r"(?:per|/)\s*(?:1[,.]?000|1000|1k)\s*views|pay(?:ment)?\s*(?:based|depends)\s*on\s*views",
        "⚠️ Có cơ chế trả theo lượt xem; cần xác nhận khoản trả cố định và cách tính."
    ),
    (
        r"(?:free|unpaid)\s*(?:test|sample|trial)|edit\s*(?:a\s*)?sample\s*for\s*free|do\s*a\s*free\s*video",
        "🚨 Yêu cầu làm test miễn phí (Free / Unpaid sample)"
    ),
    (
        r"(?:premiere|after effects|ae)\s*(?:project|source|\.prproj|\.aep)|deliver\s*(?:the\s*)?(?:project|source)\s*files?",
        "⚠️ Đòi giao file project gốc Premiere / After Effects"
    ),
    (
        r"(?:contact|message|reach|dm)\s*(?:me\s*)?(?:on|via|at)\s*(?:telegram|whatsapp|skype|gmail|email)|t\.me\/|wa\.me\/",
        "🚨 Yêu cầu liên hệ ngoài Upwork (Nguy cơ scam / Vi phạm TOS)"
    ),
    (
        r"\$5\s*(?:per|/)\s*(?:video|clip|short)|\$5\s*fixed",
        "⚠️ Giá quá thấp / phá giá ($5/video)"
    ),
    (
        r"character animation|unreal engine|blender 3d|3d animation|cinema 4d|houdini",
        "⚠️ Đòi hỏi 3D / Character Animation phức tạp"
    ),
    (
        r"unlimited revisions",
        "⚠️ Khách đòi Unlimited Revisions (Sửa không giới hạn)"
    )
]

def scan_red_flags(text: str) -> list[str]:
    """
    Scans full email text/snippet for known Upwork red flags.
    Returns a list of human-readable warnings.
    """
    found = []
    text_lower = text.lower()
    for pattern, warning in RED_FLAG_PATTERNS:
        if re.search(pattern, text_lower):
            found.append(warning)
    return found
