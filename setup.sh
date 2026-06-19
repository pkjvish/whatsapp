#!/usr/bin/env bash
# setup.sh — Bootstrap the WhatsApp Sender environment (Selenium edition)
set -euo pipefail

VENV_DIR=".venv"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  WhatsApp Bulk Sender — Setup (Selenium) ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── 1. Python check ───────────────────────────────────────────────────────────
PY=$(command -v python3 || true)
[[ -z "$PY" ]] && { echo "❌  python3 not found. Install Python 3.10+ and retry."; exit 1; }
PY_VER=$("$PY" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✔  Python ${PY_VER} detected."

# ── 2. Google Chrome check ────────────────────────────────────────────────────
if command -v google-chrome &>/dev/null; then
    CHROME_VER=$(google-chrome --version 2>/dev/null | awk '{print $3}')
    echo "✔  Google Chrome ${CHROME_VER} detected."
elif command -v chromium-browser &>/dev/null || command -v chromium &>/dev/null; then
    echo "✔  Chromium detected."
else
    echo ""
    echo "⚠   Google Chrome not found."
    echo "    Install it from: https://www.google.com/chrome/"
    echo "    On Ubuntu/Debian:"
    echo "      wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -"
    echo "      sudo sh -c 'echo \"deb [arch=amd64] https://dl.google.com/linux/chrome/deb/ stable main\" > /etc/apt/sources.list.d/google-chrome.list'"
    echo "      sudo apt-get update && sudo apt-get install -y google-chrome-stable"
    echo ""
fi

# ── 3. Virtual environment ────────────────────────────────────────────────────
if [[ ! -d "$VENV_DIR" ]]; then
    echo "→  Creating virtual environment in ${VENV_DIR}/ …"
    "$PY" -m venv "$VENV_DIR"
else
    echo "✔  Virtual environment already exists."
fi

# shellcheck source=/dev/null
source "${VENV_DIR}/bin/activate"

# ── 4. Install dependencies ───────────────────────────────────────────────────
echo "→  Upgrading pip …"
pip install --quiet --upgrade pip

echo "→  Installing dependencies …"
pip install --quiet -r requirements.txt
echo "✔  Dependencies installed:"
pip show selenium webdriver-manager rich | grep -E "^(Name|Version):" | paste - - | awk '{print "    "$2" "$4}'

# ── 5. ChromeDriver check ─────────────────────────────────────────────────────
echo "→  Verifying webdriver-manager can locate ChromeDriver …"
python3 - <<'PYEOF'
from webdriver_manager.chrome import ChromeDriverManager
path = ChromeDriverManager().install()
print(f"✔  ChromeDriver ready: {path}")
PYEOF

# ── 6. Directories & template files ──────────────────────────────────────────
mkdir -p logs attachments .chrome_profile
echo "✔  Directories ready: logs/, attachments/, .chrome_profile/"

if [[ ! -f "numberMessage.txt" ]]; then
    cat > numberMessage.txt <<'TMPL'
+919702309081,"hello pankaj"
+919876543210,"hello rahul, please find the attached resume"
TMPL
    echo "✔  Template numberMessage.txt created — edit it with your contacts."
fi

# ── 7. Done ───────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   ✅  Setup complete!                    ║"
echo "║                                          ║"
echo "║   Next steps:                            ║"
echo "║   1. Edit  numberMessage.txt             ║"
echo "║   2. Place resume in attachments/        ║"
echo "║   3. Run:                                ║"
echo "║      source .venv/bin/activate           ║"
echo "║      python whatsapp_sender.py           ║"
echo "║                                          ║"
echo "║   First run: scan QR code in browser.   ║"
echo "║   Session is saved — no QR next time.   ║"
echo "╚══════════════════════════════════════════╝"
echo ""
