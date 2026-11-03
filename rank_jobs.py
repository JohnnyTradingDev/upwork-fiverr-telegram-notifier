#!/usr/bin/env python3
"""Read-only local shortlist. Does not contact Telegram or freelance platforms."""
import argparse
import json
import db
from job_fit import rank_jobs
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=7)
    parser.add_argument('--limit', type=int, default=5)
    args = parser.parse_args()
    print(json.dumps(rank_jobs(db.get_recent_jobs(args.days), max(1, min(20, args.limit))), ensure_ascii=False, indent=2))
