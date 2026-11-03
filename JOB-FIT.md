# Job triage for Johnny

Telegram:
- `/top`: 5 highest scoring job alerts, briefs, invitations or offers from the latest 7 calendar dates. At most 500 recent database rows are scanned. Scores may all be low; the list is a triage aid, not a recommendation to bid blindly.
- `/fit 123`: reasons, missing requirements, risk signals and questions for that database ID.
- `/draft 123`: English proposal draft. Read it, check capability and add a relevant portfolio link before submitting yourself.
- `/draft`: latest database job, preserving the previous command.

`freelance_profile.json` lists enabled tracks and demo assets. The score reflects similarity to those assets, not proof of skill or a probability of winning. Existing finance-video alert policy is unchanged; `/top` can also surface automation and website briefs already received by email. No new crawling, external applications or automatic proposals are enabled.

Set `portfolio_url` only to your real, reviewable HTTPS portfolio. Without it the draft omits a portfolio claim. Nothing in this feature auto-sends a proposal or promises free samples, retention, revisions, delivery dates or professional qualifications.

Local read-only command: `venv/bin/python rank_jobs.py --days 7 --limit 5`.
Tests (mocked HTTP, no real Telegram delivery): `venv/bin/python -m unittest -v test_job_fit`.

Snapshots before this change: `/home/johnny/server-maintenance/side-income-20261103/`. They include the database and pre-existing working tree changes; do not reset the repository to roll back this feature.

Refinement on 2026-11-03: manufacturing CAD/SolidWorks/NC1 workflows no longer match software automation. Generic "short clips" no longer earns vertical-format points. Truncated email listings carry limited confidence, named editing tools require verification, tiny fixed budgets and view-based compensation trigger closer review. Passing tests: 13.
