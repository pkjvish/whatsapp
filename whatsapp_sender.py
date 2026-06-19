#!/usr/bin/env python3
"""
whatsapp_sender.py
------------------
Sends WhatsApp messages (+ optional file attachment) to a list of contacts
read from numberMessage.txt, using Selenium to drive WhatsApp Web directly.

Session is persisted in .chrome_profile/ so you only scan the QR code ONCE.
"""

import argparse
import csv
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional

from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich import print as rprint

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "logs"
PROFILE_DIR = BASE_DIR / ".chrome_profile"
DEFAULT_MSG_FILE = BASE_DIR / "numberMessage.txt"
DEFAULT_ATTACHMENT = BASE_DIR / "attachments" / "resume.txt"

LOG_DIR.mkdir(exist_ok=True)
PROFILE_DIR.mkdir(exist_ok=True)

# ── Constants ──────────────────────────────────────────────────────────────────
WHATSAPP_WEB_URL = "https://web.whatsapp.com"
PAGE_LOAD_TIMEOUT = 60
CHAT_OPEN_TIMEOUT = 20
MSG_SEND_TIMEOUT = 15
DELAY_BETWEEN_MSGS = 20

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "sender.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)
console = Console()


# ══════════════════════════════════════════════════════════════════════════════
# Contact parser
# ══════════════════════════════════════════════════════════════════════════════

def parse_contacts(filepath: Path) -> List[Dict]:
    contacts = []
    with open(filepath, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        for line_no, row in enumerate(reader, start=1):
            if not row or all(cell.strip() == "" for cell in row):
                continue
            if len(row) < 2:
                logger.warning("Line %d skipped (missing message): %s", line_no, row)
                continue
            number = row[0].strip()
            message = row[1].strip().strip('"')
            if not number.startswith("+"):
                logger.warning(
                    "Line %d: '%s' has no country code (needs '+XX'). Skipping.",
                    line_no, number,
                )
                continue
            contacts.append({"number": number, "message": message, "line": line_no})
    return contacts


# ══════════════════════════════════════════════════════════════════════════════
# Chrome / Selenium setup – using Selenium's built-in driver manager
# ══════════════════════════════════════════════════════════════════════════════

def build_driver(headless: bool = False) -> webdriver.Chrome:
    opts = Options()
    opts.add_argument(f"--user-data-dir={PROFILE_DIR.resolve()}")
    opts.add_argument("--profile-directory=Default")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,900")
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])

    if headless:
        opts.add_argument("--headless=new")
        logger.warning("Headless mode: file attachments may not work on some systems.")

    # Selenium 4.6+ automatically downloads and caches the correct driver
    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver


# ══════════════════════════════════════════════════════════════════════════════
# WhatsApp Web helpers (unchanged)
# ══════════════════════════════════════════════════════════════════════════════

def wait_for_login(driver: webdriver.Chrome) -> None:
    console.print("\n[yellow]⏳  Waiting for WhatsApp Web to load …[/yellow]")
    console.print("[dim]   (Scan the QR code if this is your first run)[/dim]\n")
    wait = WebDriverWait(driver, 120)
    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')
        )
    )
    console.print("[green]✔  Logged in to WhatsApp Web.[/green]\n")


def open_chat(driver: webdriver.Chrome, number: str) -> bool:
    url = f"https://web.whatsapp.com/send?phone={number}&app_absent=0"
    logger.info("Opening chat for %s → %s", number, url)
    driver.get(url)
    try:
        WebDriverWait(driver, CHAT_OPEN_TIMEOUT).until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')
            )
        )
        time.sleep(1.5)
        return True
    except TimeoutException:
        logger.error("Timed out opening chat for %s", number)
        return False


def type_and_send_message(driver: webdriver.Chrome, message: str) -> None:
    input_box = driver.find_element(
        By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'
    )
    for i, line in enumerate(message.split("\n")):
        if i > 0:
            input_box.send_keys(Keys.SHIFT + Keys.ENTER)
        input_box.send_keys(line)
    time.sleep(0.5)
    input_box.send_keys(Keys.ENTER)
    time.sleep(MSG_SEND_TIMEOUT)


def attach_and_send_file(
    driver: webdriver.Chrome, attachment: Path, caption: str
) -> None:
    abs_path = str(attachment.resolve())
    clip_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//div[@title="Attach"]'))
    )
    clip_btn.click()
    time.sleep(1)
    doc_btn = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//input[@accept="*"]'))
    )
    doc_btn.send_keys(abs_path)
    time.sleep(3)
    try:
        caption_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')
            )
        )
        caption_box.send_keys(caption)
        time.sleep(0.5)
    except TimeoutException:
        logger.warning("Caption box not found — sending without caption.")
    send_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="Send"]'))
    )
    send_btn.click()
    time.sleep(MSG_SEND_TIMEOUT)


def send_to_contact(
    driver: webdriver.Chrome,
    number: str,
    message: str,
    attachment: Optional[Path],
) -> bool:
    try:
        if not open_chat(driver, number):
            return False
        if attachment and attachment.exists():
            logger.info("Attaching '%s' with caption for %s", attachment.name, number)
            attach_and_send_file(driver, attachment, message)
        else:
            logger.info("Sending text message to %s", number)
            type_and_send_message(driver, message)
        logger.info("✔ Sent to %s", number)
        return True
    except (NoSuchElementException, WebDriverException, TimeoutException) as exc:
        logger.error("✗ Failed to send to %s: %s", number, exc)
        return False


def print_summary(results: List[Dict]) -> None:
    table = Table(title="WhatsApp Send Summary", show_lines=True)
    table.add_column("Line", style="dim", width=6)
    table.add_column("Number", style="cyan")
    table.add_column("Message", style="white", max_width=40)
    table.add_column("Status", style="bold")
    for r in results:
        status = "[green]✓ Sent[/green]" if r["success"] else "[red]✗ Failed[/red]"
        table.add_row(str(r["line"]), r["number"], r["message"][:40], status)
    console.print(table)
    total = len(results)
    success = sum(1 for r in results if r["success"])
    rprint(
        f"\n[bold]Total:[/bold] {total}  |  "
        f"[green]Sent: {success}[/green]  |  "
        f"[red]Failed: {total - success}[/red]\n"
    )
    report = LOG_DIR / "report.csv"
    with open(report, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["line", "number", "message", "success"])
        writer.writeheader()
        writer.writerows(results)
    console.print(f"[dim]Report saved → {report}[/dim]")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send WhatsApp messages (+ attachment) via Selenium."
    )
    parser.add_argument(
        "--file", "-f",
        type=Path, default=DEFAULT_MSG_FILE,
        help=f"Contacts file  (default: {DEFAULT_MSG_FILE})",
    )
    parser.add_argument(
        "--attachment", "-a",
        type=Path, default=DEFAULT_ATTACHMENT,
        help=f"File to attach (default: {DEFAULT_ATTACHMENT})",
    )
    parser.add_argument(
        "--no-attachment", action="store_true",
        help="Send text-only messages (skip attachment)",
    )
    parser.add_argument(
        "--delay", "-d",
        type=int, default=DELAY_BETWEEN_MSGS,
        help=f"Seconds between messages (default: {DELAY_BETWEEN_MSGS})",
    )
    parser.add_argument(
        "--headless", action="store_true",
        help="Run Chrome in headless mode (QR scan impossible; needs saved session)",
    )
    args = parser.parse_args()

    if not args.file.exists():
        console.print(f"[red]✗ Contacts file not found: {args.file}[/red]")
        sys.exit(1)

    contacts = parse_contacts(args.file)
    if not contacts:
        console.print("[red]✗ No valid contacts in file.[/red]")
        sys.exit(1)

    attachment: Optional[Path] = None
    if not args.no_attachment:
        attachment = args.attachment
        if not attachment.exists():
            console.print(
                f"[yellow]⚠  Attachment not found at {attachment} — "
                "sending text only.[/yellow]"
            )
            attachment = None

    console.print("\n[bold cyan]━━━  WhatsApp Bulk Sender (Selenium)  ━━━[/bold cyan]")
    console.print(f"  Contacts   : {len(contacts)}")
    console.print(f"  Attachment : {attachment or 'None'}")
    console.print(f"  Delay      : {args.delay} s between messages")
    console.print(f"  Headless   : {args.headless}\n")

    driver = build_driver(headless=args.headless)

    try:
        driver.get(WHATSAPP_WEB_URL)
        wait_for_login(driver)

        results = []
        for i, contact in enumerate(track(contacts, description="Sending …")):
            success = send_to_contact(
                driver,
                contact["number"],
                contact["message"],
                attachment,
            )
            results.append({**contact, "success": success})
            if i < len(contacts) - 1:
                logger.info("Waiting %d s before next contact …", args.delay)
                time.sleep(args.delay)

        print_summary(results)

    finally:
        driver.quit()
        logger.info("Browser closed.")


if __name__ == "__main__":
    main()
