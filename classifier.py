import re
import logging

logger = logging.getLogger(__name__)

# Keywords for Video Editing (Skills, Software, Formats & Deliverables)
VIDEO_KEYWORDS = [
    r"\bvideo\b", r"\bvideo editor\b", r"\bvideo editing\b",
    r"\bcapcut\b", r"\bpremiere\b", r"\bafter effects\b", r"\bdavinci\b",
    r"\byoutube\b", r"\byoutuber\b", r"\breels?\b", r"\btiktok\b",
    r"\bshorts?\b", r"\bshort[- ]form\b", r"\bfaceless\b",
    r"\bscreencast\b", r"\bscreencasting\b", r"\bscreen recording\b",
    r"\btalking[- ]head\b", r"\bb[- ]roll\b", r"\bbroll\b",
    r"\bsubtitles?\b", r"\bcaptions?\b", r"\bmotion graphics?\b",
    r"\bvideo production\b", r"\bvlogs?\b"
]

# Non-video keywords to prevent false positives (CAD text edit, photo edit, etc.)
EXCLUDE_NON_VIDEO = [
    r"\bautocad\b", r"\bcad\b", r"\bsolidworks\b", r"\binventor\b",
    r"\bcnc\b", r"\bmachinist\b", r"\bsheet metal\b",
    r"\bphoto edit\b", r"\bphotoshop\b", r"\bcopy edit\b", r"\bbook edit\b"
]

# Keywords for Finance, Crypto, Forex, Trading & Economics
FINANCE_KEYWORDS = [
    r"\bfinance\b", r"\bfinancial\b", r"\bcrypto\b", r"\bcryptocurrency\b",
    r"\bcryptocurrencies\b", r"\bblockchain\b", r"\bweb3\b",
    r"\bbitcoin\b", r"\bbtc\b", r"\beth\b", r"\bethereum\b", r"\bsolana\b", r"\bsol\b",
    r"\baltcoins?\b", r"\bdefi\b", r"\bforex\b", r"\bfx\b",
    r"\btrading\b", r"\btrader\b", r"\btrades?\b", r"\bscalping\b",
    r"\bday trading\b", r"\bswing trading\b",
    r"\bstocks?\b", r"\bequity\b", r"\bequities\b", r"\bshares?\b",
    r"\bmt4\b", r"\bmt5\b", r"\bmetatrader\b", r"\bfintech\b",
    r"\binvesting\b", r"\binvestment\b", r"\binvestors?\b", r"\bwealth\b",
    r"\beconomy\b", r"\beconomic\b", r"\beconomics\b", r"\bmacro\b",
    r"\bmarket update\b", r"\bmarket analysis\b", r"\btechnical analysis\b",
    r"\bchart analysis\b", r"\bbanking\b", r"\bcapital\b", r"\bbinance\b"
]

def classify_job(title: str, snippet: str = "", client_info: str = "", full_text: str = "") -> tuple[str, list[str]]:
    """
    Classifies a job into Video Editing categories:
    1. 'financial_video': Video editing for Finance / Crypto / Forex / Trading / Stocks (TARGET NICHE)
    2. 'other_video': Other video editing jobs (YouTube, TikTok, Travel, Gaming, Talking head...)
    3. 'non_video': Jobs that are not video editing

    Returns: (category, matched_tags)
    """
    search_corpus = f"{title} {title} {snippet} {full_text}".lower()

    # Check for non-video CAD/photo exclusions unless explicit video keywords exist
    is_excluded = any(bool(re.search(e, search_corpus)) for e in EXCLUDE_NON_VIDEO)
    explicit_video = bool(re.search(r"\b(video|capcut|premiere|after effects|davinci|youtube|reels?|tiktok|short[- ]form)\b", search_corpus))

    if is_excluded and not explicit_video:
        return "non_video", []

    matched_video = [k for k in VIDEO_KEYWORDS if re.search(k, search_corpus)]
    matched_finance = [k for k in FINANCE_KEYWORDS if re.search(k, search_corpus)]

    has_video = len(matched_video) > 0
    has_finance = len(matched_finance) > 0

    if has_video and has_finance:
        category = "financial_video"
        tags = matched_video[:2] + matched_finance[:2]
    elif has_video:
        category = "other_video"
        tags = matched_video[:3]
    else:
        category = "non_video"
        tags = []

    clean_tags = [t.replace(r"\b", "").replace("?", "").replace("[- ]", "-") for t in tags]
    return category, clean_tags

CATEGORY_DISPLAY = {
    "financial_video": "🎯 Video Tài chính / Trading (Ngách của bạn)",
    "other_video": "🎬 Các job Video khác",
    "non_video": "📂 Việc không liên quan video"
}
