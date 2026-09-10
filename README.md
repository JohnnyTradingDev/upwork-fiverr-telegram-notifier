# ⚡ Upwork & Fiverr Realtime Telegram Notifier

> **Instant push notifications for Upwork & Fiverr freelance opportunities straight to your Telegram in less than 1 second.**  
> Powered by Gmail **IMAP IDLE** socket push — no polling delay, no public IP, and no expensive webhooks required.

---

## 🌟 Key Features

- ⚡ **True Real-time (< 1s):** Uses persistent IMAP IDLE socket connection. Gmail pushes new emails immediately to your server.
- 🎯 **Upwork Intelligence:**
  - Detects **Invitations to Interview**, **Contract Offers**, **Client Messages**, **Proposals Updates**, and **Saved Search Job Alerts**.
  - Extracts **Job Title**, **Budget / Hourly Rate**, **Client Info** (Payment Verified, Rating ⭐, Total Spent 💰, Country 📍), and **Description Snippet**.
  - Direct **"🚀 Mở trực tiếp trên Upwork"** action button.
- 🟢 **Fiverr Intelligence:**
  - Detects **New Orders**, **Client Messages**, **Matched Briefs / Buyer Requests**, **Revisions**, and **Reviews**.
  - Extracts **Order Amount ($)**, **Buyer Handle (@buyer)**, and **Gig Description**.
  - Direct **"🟢 Mở trực tiếp trên Fiverr"** action button.
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
┌──────────────────────────────────────────────┐
│       Your Linux Server / VPS                │
│                                              │
│   [ IMAP IDLE Listener (main.py) ]           │
│                  │                           │
│                  ▼                           │
│   [ Smart Parser (parser.py) ]               │
│   • Detect platform (Upwork / Fiverr)        │
│   • Extract Budget, Client info, Title, URL  │
│                  │                           │
│                  ▼                           │
│   [ Telegram Notifier (telegram_notifier.py)]│
└──────────────────┬───────────────────────────┘
                   │
                   ▼ (Telegram Bot API)
       [ Your Telegram Chat / Mobile 🚀 ]
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
git clone https://github.com/JohnnyTradingDev/upwork-telegram-notifier.git
cd upwork-telegram-notifier
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
Run the built-in test script to verify both Upwork and Fiverr message delivery:
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

---

## 📁 Project Structure

```text
upwork-telegram-notifier/
├── config.py                 # Configuration loader from .env
├── main.py                   # IMAP IDLE listener & reconnection lifecycle
├── parser.py                 # Intelligent email parsing (Upwork & Fiverr)
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
- `.env` and `state.json` are listed in `.gitignore` to prevent any accidental leakage.
- Utilizes Google's recommended App Password standard rather than your primary Google account password.

---

## 📄 License

MIT License © 2026 [Johnny](https://github.com/JohnnyTradingDev)
