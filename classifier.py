import re
import logging

logger = logging.getLogger(__name__)

# Keywords for Video Editing (Skills & Deliverables)
VIDEO_KEYWORDS = [
    r"\bvideo\b", r"\beditor\b", r"\bediting\b", r"\bedits?\b",
    r"\bcapcut\b", r"\bpremiere\b", r"\bafter effects\b", r"\bdavinci\b",
    r"\byoutube\b", r"\byoutuber\b", r"\breels?\b", r"\btiktok\b",
    r"\bshorts?\b", r"\bshort[- ]form\b", r"\bfaceless\b",
    r"\bscreencast\b", r"\bscreencasting\b", r"\bscreen recording\b",
    r"\btalking[- ]head\b", r"\bb[- ]roll\b", r"\bbroll\b",
    r"\bsubtitles?\b", r"\bcaptions?\b", r"\bmotion graphics?\b",
    r"\bvideo production\b", r"\bcontent creator\b", r"\bcontent creation\b"
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

# Keywords for Mechanical, Sheet Metal & 3D CAD (Legacy niche)
MECHANICAL_KEYWORDS = [
    r"\bcad\b", r"\bautocad\b", r"\bsolidworks\b", r"\binventor\b",
    r"\bfusion 360\b", r"\bcatia\b", r"\bcreo\b", r"\brhino\b",
    r"\bsheet metal\b", r"\bsheetmetal\b", r"\benclosure\b",
    r"\bcnc\b", r"\bmachinist\b", r"\bmachining\b", r"\bmill\b", r"\blathe\b",
    r"\bmechanical\b", r"\bmechanic\b", r"\b3d model\b", r"\b3d modeling\b",
    r"\b3d cad\b", r"\b3d print\b", r"\b3d design\b", r"\bdrafter\b",
    r"\bdrafting\b", r"\bdraftsman\b", r"\bdwg\b", r"\bdxf\b", r"\bstep\b",
    r"\bstp\b", r"\bstl\b", r"\bfloor plan\b"
]

def classify_job(title: str, snippet: str = "", client_info: str = "", full_text: str = "") -> tuple[str, list[str]]:
    """
    Classifies a job into one of 4 categories:
    1. 'financial_video': Video editing for Finance/Crypto/Forex/Trading (CORE NICHE)
    2. 'general_video': Video editing in general (YouTube, TikTok, talking-head, etc.)
    3. 'mechanical_3d': Mechanical, sheet metal, 3D CAD (Legacy niche)
    4. 'other': Any other job (translation, web dev, marketing, etc.)

    Returns: (category, matched_tags)
    """
    # Give high weight to title and snippet
    search_corpus = f"{title} {title} {snippet} {full_text}".lower()

    matched_video = [k for k in VIDEO_KEYWORDS if re.search(k, search_corpus)]
    matched_finance = [k for k in FINANCE_KEYWORDS if re.search(k, search_corpus)]
    matched_mechanical = [k for k in MECHANICAL_KEYWORDS if re.search(k, search_corpus)]

    has_video = len(matched_video) > 0
    has_finance = len(matched_finance) > 0
    has_mechanical = len(matched_mechanical) > 0

    if has_video and has_finance:
        category = "financial_video"
        tags = matched_video[:2] + matched_finance[:2]
    elif has_video:
        category = "general_video"
        tags = matched_video[:3]
    elif has_mechanical:
        category = "mechanical_3d"
        tags = matched_mechanical[:3]
    else:
        category = "other"
        tags = []

    clean_tags = [t.replace(r"\b", "").replace("?", "").replace("[- ]", "-") for t in tags]
    return category, clean_tags

CATEGORY_DISPLAY = {
    "financial_video": "🎯 Video Tài chính / Trading (Ngách của bạn)",
    "general_video": "🎬 Video Editing chung",
    "mechanical_3d": "⚙️ Cơ khí / 3D CAD (Ngách cũ)",
    "other": "📂 Ngành nghề khác"
}
