"""
Upwork Job Fetcher Module
Provides capability to fetch full job descriptions from Upwork using authenticated session cookies or visitor endpoints.
"""
import re
import json
import logging
from typing import Optional, Dict, Any
from curl_cffi import requests

logger = logging.getLogger(__name__)

GRAPHQL_URL = "https://www.upwork.com/api/graphql/v1"

def extract_job_ciphertext(url: str) -> Optional[str]:
    """Extracts job ciphertext from Upwork URL (e.g. ~01... or ~02...)."""
    match = re.search(r"~([0-9a-zA-Z]+)", url)
    if match:
        return f"~{match.group(1)}"
    return None

def fetch_upwork_job_details(url: str, cookie: str = "") -> Dict[str, Any]:
    """
    Attempts to fetch full job details from Upwork.
    If cookie is provided, uses authenticated session to bypass Cloudflare.
    """
    ciphertext = extract_job_ciphertext(url)
    if not ciphertext:
        return {"error": "Invalid Upwork URL: No ciphertext found"}

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": f"https://www.upwork.com/jobs/{ciphertext}",
    }

    if cookie:
        headers["Cookie"] = cookie

    # Strategy 1: Visitor API Endpoint
    api_url = f"https://www.upwork.com/job-details/visitor/api/v1/job-details/{ciphertext}"
    try:
        r = requests.get(api_url, headers=headers, impersonate="chrome131", timeout=12)
        if r.status_code == 200:
            data = r.json()
            job = data.get("job", {})
            return {
                "success": True,
                "title": job.get("title", ""),
                "description": job.get("description", ""),
                "budget": job.get("budget", {}),
                "skills": [s.get("prefLabel") for s in job.get("skills", []) if s.get("prefLabel")],
                "questions": [q.get("question") for q in job.get("questions", []) if q.get("question")],
                "client": job.get("client", {}),
                "proposals_tier": job.get("proposalsTier", ""),
                "connects_cost": job.get("connectPrice", 0)
            }
        elif r.status_code == 403:
            return {
                "success": False,
                "error": "Cloudflare blocked request (403). Session cookie is required in .env (UPWORK_COOKIE)."
            }
        else:
            return {
                "success": False,
                "error": f"API returned status code {r.status_code}"
            }
    except Exception as e:
        logger.error(f"Error fetching job details: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import sys
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.upwork.com/jobs/~022110632964620047559"
    print(f"Testing URL: {test_url}")
    result = fetch_upwork_job_details(test_url)
    print("Result:", json.dumps(result, indent=2, ensure_ascii=False))
