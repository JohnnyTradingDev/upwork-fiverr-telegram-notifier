# ⚡ Upwork & Fiverr Realtime Telegram Notifier

> **Instant push notifications for Upwork & Fiverr freelance opportunities straight to your Telegram in less than 1 second.**  
> Powered by Gmail **IMAP IDLE** socket push — no polling delay, no public IP, and no expensive webhooks required.  
> Includes **intelligent niche classification** (Finance/Crypto Video Editing focus), **database tracking**, and **daily recap digest**.

---

## 🌟 Key Features

- ⚡ **True Real-time (< 1s):** Uses persistent IMAP IDLE socket connection. Gmail pushes new emails immediately to your server.
- 🎯 **Niche Filtering (Financial Video Editing):**
  - **Immediate Alerts** for your target niche: Video Editing for Finance, Crypto, Forex, Trading, Stocks, Faceless YouTube, Short-form, and CapCut.
  - Direct client interactions (**Invitations**, **Offers**, **Messages**, **Orders**) are **ALWAYS** alerted immediately regardless of category.
  - Non-matching job alerts (e.g. Mechanical/3D CAD or other industries) are silently recorded in the database without spamming your Telegram.
- 📊 **SQLite Database & Daily Summary Digest:**
  - Persists all jobs to a local SQLite database (`jobs.db`).
  - Categorizes into:
    - 🎯 `financial_video`: Video Tài chính / Trading (Your core niche)
    - 🎬 `general_video`: Video Editing chung
    - ⚙️ `mechanical_3d`: Cơ khí / 3D CAD (Legacy niche)
    - 📂 `other`: Other categories
  - Automatically sends a **Daily Summary** to Telegram every evening (default 22:00 local time).
- 🟢 **Fiverr & Upwork Intelligence:**
  - Extracts **Job Title**, **Budget / Order Amount**, **Client Info** (Payment Verified, Rating ⭐, Total Spent 💰, Country 📍), and **Skills**.
  - Direct **"🚀 Mở trực tiếp trên Upwork"** and **"🟢 Mở trực tiếp trên Fiverr"** action buttons.
- 📱 **Beautiful Telegram UI:** Rich HTML message formatting with intuitive emoji badges and inline buttons.
- 🛡️ **No Duplicates & No Missed Alerts:** Tracks processed message UIDs persistently in `state.json`.
- 🔄 **Fault Tolerance & Auto-reconnect:** Resilient against network drops, socket timeouts, and IMAP keepalive expiration (RFC 2177).
- ⚙️ **Production-Ready Daemon:** Built-in `systemd` user service support to run 24/7 and survive server reboots.

---

## 🏗️ Architecture

```text
[ Upwork / Fiverr Email ]
           │
           ▼
    [ Gmail Server ]
           │
           │  (IMAP IDLE Socket Push < 1s)
           ▼
┌────────────────────────────────────────────────────────┐
│       Your Linux Server / VPS                          │
│                                                        │
│   [ IMAP IDLE Listener (main.py) ]                     │
│                  │                                     │
│                  ▼                                     │
│   [ Smart Parser (parser.py) ]                         │
│   • Detect platform (Upwork / Fiverr)                  │
│   • Extract Budget, Client info, Title, URL            │
│                  │                                     │
│                  ▼                                     │
│   [ Niche Classifier (classifier.py) ]                 │
│   • Financial Video / General Video / 3D CAD / Other   │
│                  │                                     │
│         ┌────────┴────────┐                            │
│         ▼                 ▼                            │
│  [ SQLite DB ]    [ Immediate Filter ]                 │
│  (jobs.db)        • Is Financial Video OR Direct Msg?  │
│         │                 │                            │
│         │ (22:00 Daily)   ├─ Yes ──► [ Telegram Alert ]│
│         ▼                 │                            │
│  [ Daily Summary ] ───────┴─ No  ──► [ Stored in DB ]  │
└────────────────────────────────────────────────────────┘
```

---

## 📋 Prerequisites

1. **Linux Server / VPS** (Ubuntu, Debian, CentOS, etc.)
2. **Python 3.10+**
3. **Gmail Account** with 2-Step Verification enabled and an **App Password** (16 characters)
4. **Telegram Bot Token** (created via [@BotFather](https://t.me/BotFather)) and your **Telegram Chat ID**

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/JohnnyTradingDev/upwork-fiverr-telegram-notifier.git
cd upwork-fiverr-telegram-notifier
```

### 2. Create Python virtual environment & install dependencies
```bash
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
```

### 3. Configure `.env`
Copy the template and fill in your credentials:
```bash
cp .env.example .env
nano .env
```

Set the following variables:
```env
# Gmail Credentials
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

# Telegram Credentials
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ
TELEGRAM_CHAT_ID=123456789

# Platform Flags (Set True / False)
ENABLE_UPWORK=True
ENABLE_FIVERR=True

# Niche Filter Configuration
ONLY_FINANCIAL_VIDEO_ALERTS=True

# Daily Summary Configuration (22 = 10 PM in your local timezone)
DAILY_SUMMARY_HOUR=22
TIMEZONE_OFFSET=7

# Advanced Settings
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
IDLE_REFRESH_SECONDS=900
```

> **How to get a Gmail App Password:**
> 1. Go to your [Google Account Security](https://myaccount.google.com/security).
> 2. Ensure **2-Step Verification** is turned ON.
> 3. Visit [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
> 4. Create an app named `Freelance Bot` and copy the 16-character password.

> **Important for Telegram:**
> Open your newly created bot in Telegram and press **/start** before testing.

### 4. Test Telegram notifications
Run the built-in test script to verify message delivery:
```bash
./manage.sh test
```

---

## ⚙️ Running 24/7 with systemd

Enable the service to run persistently in background and start automatically on boot:

```bash
# 1. Copy service file to user systemd directory
mkdir -p ~/.config/systemd/user
cp upwork-notifier.service ~/.config/systemd/user/

# 2. Reload systemd and enable service
systemctl --user daemon-reload
systemctl --user enable upwork-notifier

# 3. Start the service
systemctl --user start upwork-notifier
```

---

## 🛠️ Management Commands

A helper script `manage.sh` is included for effortless operations:

| Command | Description |
| :--- | :--- |
| `./manage.sh start` | Start the background service |
| `./manage.sh stop` | Stop the service |
| `./manage.sh restart` | Restart the service |
| `./manage.sh status` | View service status |
| `./manage.sh logs` | View live real-time log stream |
| `./manage.sh test` | Send sample Upwork & Fiverr notifications to Telegram |
| `./manage.sh summary` | Trigger daily summary for today on-demand |
| `./manage.sh summary 2026-09-29` | Trigger summary for a specific date |

---

## 📁 Project Structure

```text
upwork-telegram-notifier/
├── config.py                 # Configuration loader from .env
├── classifier.py             # Niche classifier (Financial Video, General Video, CAD, etc.)
├── db.py                     # SQLite database management for job storage & recap
├── main.py                   # IMAP IDLE listener & reconnection lifecycle
├── parser.py                 # Intelligent email parsing (Upwork & Fiverr)
├── send_summary.py           # On-demand and scheduled daily summary sender
├── telegram_notifier.py      # Rich Telegram message formatting & delivery
├── test_telegram.py          # Quick test utility
├── manage.sh                 # Operational CLI management script
├── upwork-notifier.service   # Systemd unit configuration
├── requirements.txt          # Python dependencies
├── .env.example              # Sanitized configuration template
└── README.md                 # Documentation
```

---

## 🔒 Security & Privacy

- **No Passwords Stored in Code:** All credentials are loaded exclusively from `.env`.
- `.env`, `state.json`, and `jobs.db` are listed in `.gitignore` to prevent any accidental leakage.
- Utilizes Google's recommended App Password standard rather than your primary Google account password.

---

## 📄 License

MIT License © 2026 [Johnny](https://github.com/JohnnyTradingDev)
