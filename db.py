import sqlite3
import os
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "jobs.db")

# Default Timezone offset (Vietnam is UTC+7)
TZ_OFFSET = int(os.getenv("TIMEZONE_OFFSET", "7"))
USER_TZ = timezone(timedelta(hours=TZ_OFFSET))

def get_current_date_str() -> str:
    """Returns today's date string YYYY-MM-DD in the user's timezone."""
    now = datetime.now(USER_TZ)
    return now.strftime("%Y-%m-%d")

def init_db():
    """Initializes the SQLite database schema."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid INTEGER UNIQUE,
                platform TEXT,
                email_type TEXT,
                category TEXT,
                title TEXT,
                budget TEXT,
                client_info TEXT,
                url TEXT,
                snippet TEXT,
                notified_immediately INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_str TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_date ON jobs(date_str)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_category ON jobs(category)")
        conn.commit()
    logger.info("Database initialized successfully.")

def save_job(
    uid: int,
    platform: str,
    email_type: str,
    category: str,
    title: str,
    budget: str,
    client_info: str,
    url: str,
    snippet: str,
    notified_immediately: bool
) -> bool:
    """Saves or updates a job in the database."""
    date_str = get_current_date_str()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO jobs (
                    uid, platform, email_type, category, title, budget,
                    client_info, url, snippet, notified_immediately, date_str
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(uid) DO UPDATE SET
                    platform=excluded.platform,
                    email_type=excluded.email_type,
                    category=excluded.category,
                    title=excluded.title,
                    budget=excluded.budget,
                    client_info=excluded.client_info,
                    url=excluded.url,
                    snippet=excluded.snippet,
                    notified_immediately=excluded.notified_immediately
            """, (
                uid, platform, email_type, category, title, budget,
                client_info, url, snippet, 1 if notified_immediately else 0, date_str
            ))
            conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error saving job to DB: {e}")
        return False

def get_daily_stats(date_str: str = None) -> dict:
    """
    Returns aggregated stats for a given date (defaults to today).
    """
    if not date_str:
        date_str = get_current_date_str()

    stats = {
        "date_str": date_str,
        "total": 0,
        "categories": {
            "financial_video": 0,
            "general_video": 0,
            "mechanical_3d": 0,
            "other": 0
        },
        "financial_jobs": []
    }

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Group counts by category
            cursor.execute("""
                SELECT category, COUNT(*) as cnt
                FROM jobs
                WHERE date_str = ?
                GROUP BY category
            """, (date_str,))
            rows = cursor.fetchall()
            for r in rows:
                cat = r["category"]
                cnt = r["cnt"]
                if cat in stats["categories"]:
                    stats["categories"][cat] = cnt
                else:
                    stats["categories"]["other"] += cnt
                stats["total"] += cnt

            # Get list of financial video jobs for detail summary
            cursor.execute("""
                SELECT title, budget, client_info, url, platform
                FROM jobs
                WHERE date_str = ? AND category = 'financial_video'
                ORDER BY id DESC
            """, (date_str,))
            stats["financial_jobs"] = [dict(r) for r in cursor.fetchall()]

    except Exception as e:
        logger.error(f"Error reading daily stats from DB: {e}")

    return stats
