import sqlite3
import os
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "jobs.db")

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
    Returns aggregated stats comparing Financial Video jobs vs Other Video jobs.
    """
    if not date_str:
        date_str = get_current_date_str()

    stats = {
        "date_str": date_str,
        "total_video": 0,
        "financial_video": 0,
        "other_video": 0,
        "financial_jobs": []
    }

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Count financial video jobs
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM jobs
                WHERE date_str = ? AND category = 'financial_video'
            """, (date_str,))
            row = cursor.fetchone()
            stats["financial_video"] = row["cnt"] if row else 0

            # Count other video jobs
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM jobs
                WHERE date_str = ? AND category = 'other_video'
            """, (date_str,))
            row = cursor.fetchone()
            stats["other_video"] = row["cnt"] if row else 0

            stats["total_video"] = stats["financial_video"] + stats["other_video"]

            # Fetch list of financial video jobs for detail summary
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

def get_job(job_id: int = None) -> dict:
    """Returns a specific job by ID, or the most recent job if job_id is None."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if job_id:
                cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            else:
                cursor.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                return dict(row)
    except Exception as e:
        logger.error(f"Error fetching job: {e}")
    return {}

def get_job_by_uid(uid: int) -> dict:
    """Returns a job by its email UID."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE uid = ?", (uid,))
            row = cursor.fetchone()
            if row:
                return dict(row)
    except Exception as e:
        logger.error(f"Error fetching job by uid: {e}")
    return {}

def get_recent_jobs(days: int = 7, limit: int = 500) -> list[dict]:
    """Bounded recent selection; existing database rows are never modified."""
    days = max(1, min(int(days), 30))
    limit = max(1, min(int(limit), 1000))
    cutoff = (datetime.now(USER_TZ) - timedelta(days=days - 1)).strftime('%Y-%m-%d')
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(r) for r in conn.execute('SELECT * FROM jobs WHERE date_str >= ? ORDER BY id DESC LIMIT ?', (cutoff, limit))]
    except sqlite3.Error:
        logger.exception('Could not read recent jobs')
        return []
