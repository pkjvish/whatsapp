# 📱 WhatsApp Bulk Sender — Selenium Edition

Send personalised WhatsApp messages with a file attachment to multiple contacts
using **Selenium** to drive WhatsApp Web directly in Chrome. No third-party APIs,
no API keys — just a real browser session.

---

## 📁 Project Structure

```
whatsapp-bulk-sender/
├── whatsapp_sender.py          ← main script (Selenium)
├── numberMessage.txt           ← contacts + messages (edit this)
├── requirements.txt            ← selenium, webdriver-manager, rich
├── setup.sh                    ← one-command environment bootstrap
├── attachments/
│   └── resume.txt              ← replace with your actual file (PDF, DOCX …)
├── logs/                       ← auto-created: sender.log, report.csv
├── .chrome_profile/            ← persisted Chrome session (QR once only)
├── .github/
│   └── workflows/ci.yml        ← GitOps: lint → test → Selenium smoke-test
└── .githooks/
    └── pre-commit              ← validates phone numbers before each commit
```

---

## ⚡ Quick Start

### 1 — Clone & bootstrap

```bash
git clone https://github.com/YOUR_USER/whatsapp-bulk-sender.git
cd whatsapp-bulk-sender
bash setup.sh          # installs .venv + all deps + verifies ChromeDriver
```

### 2 — Activate environment

```bash
source .venv/bin/activate     # Linux / macOS
.venv\Scripts\activate        # Windows
```

### 3 — Edit contacts file

```
+919702309081,"hello pankaj"
+919876543210,"hello rahul, please find the attached resume"
```

### 4 — Add your attachment

```bash
cp ~/Documents/My_Resume.pdf attachments/resume.txt
```

### 5 — Run

```bash
python whatsapp_sender.py
```

**First run:** Chrome opens → scan QR on WhatsApp Web → session is saved to
`.chrome_profile/`. Every subsequent run logs in automatically — no QR needed.

---

## 🔧 CLI Options

```
python whatsapp_sender.py [OPTIONS]

  -f, --file FILE         Contacts file         (default: numberMessage.txt)
  -a, --attachment FILE   File to attach        (default: attachments/resume.txt)
      --no-attachment     Send text only
  -d, --delay SECONDS     Gap between contacts  (default: 20)
      --headless          Run Chrome headlessly (needs saved session; no QR)
```

### Examples

```bash
# Custom contacts file
python whatsapp_sender.py --file clients.txt

# Custom attachment
python whatsapp_sender.py --attachment ~/docs/portfolio.pdf

# Text-only (no attachment)
python whatsapp_sender.py --no-attachment

# Headless (after first QR scan)
python whatsapp_sender.py --headless

# Slower sending to avoid rate limits
python whatsapp_sender.py --delay 30
```

---

## 🔄 GitOps Pipeline

Every `git push` runs three jobs automatically:

| Job | Steps |
|-----|-------|
| **Lint & Audit** | `flake8` code style + `pip-audit` vulnerability scan |
| **Test Parser** | Smoke-tests `parse_contacts()` against `numberMessage.txt` |
| **Build & Verify** | Installs Chrome + ChromeDriver, runs headless Selenium smoke test |

### Enable local Git hook

```bash
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit
```

Validates phone numbers in `numberMessage.txt` before every commit.

---

## 📋 numberMessage.txt Format

```
+<country_code><number>,"<message>"
```

| Field   | Example          | Notes |
|---------|------------------|-------|
| Number  | `+919702309081`  | Must begin with `+` and country code |
| Message | `"hello pankaj"` | Wrap in double quotes |

Blank lines are ignored. Commas inside quoted messages are fine.

---

## 📊 Logs & Reports

| File | Contents |
|------|----------|
| `logs/sender.log`  | Full timestamped log of every action |
| `logs/report.csv`  | Per-contact success / failure summary |

---

## ⚠️ Prerequisites

| Requirement | Notes |
|-------------|-------|
| Python 3.10+ | `python3 --version` |
| Google Chrome | Latest stable — `setup.sh` will guide you |
| ChromeDriver | Auto-installed by `webdriver-manager` |
| WhatsApp account | Logged in on your phone |

---

## 🛡️ Responsible Use

- Keep `--delay` at **≥ 15 seconds** to avoid WhatsApp rate limits.
- Only message contacts who have consented.
- Do **not** commit `numberMessage.txt` with real numbers to public repos.
- Add `numberMessage.txt` to `.gitignore` if needed.
