import logging
import os
import re
import sys
import time

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

DEFAULT_URL = "https://www.mgya.org/oktatas/302"
DEFAULT_POLL_INTERVAL_MINUTES = 5
SEATS_PATTERN = re.compile(r"Szabad helyek száma:\s*(\d+)\s*fő")


def get_available_seats(url: str) -> int | None:
    """Fetch the page and return the number of available seats, or None if unparseable."""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    match = SEATS_PATTERN.search(resp.text)
    if match is None:
        return None
    return int(match.group(1))


def send_telegram_message(token: str, chat_id: str, message: str) -> None:
    """Send a message via the Telegram Bot API."""
    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(
        api_url,
        json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
        timeout=15,
    )
    resp.raise_for_status()
    log.info("Telegram message sent successfully.")


def check_once(token: str, chat_id: str, target_url: str, already_notified: bool) -> bool:
    """Run a single check cycle. Returns the updated already_notified state."""
    log.info("Checking %s for available seats...", target_url)

    try:
        seats = get_available_seats(target_url)
    except requests.RequestException:
        log.exception("Failed to fetch the page.")
        send_telegram_message(token, chat_id, "⚠️ <b>mgya-watcher error:</b> Failed to fetch the page. Check pod logs.")
        return already_notified

    if seats is None:
        log.warning("Could not parse seat count from the page. The page structure may have changed.")
        send_telegram_message(
            token, chat_id,
            "⚠️ <b>mgya-watcher error:</b> Could not parse seat count. The page structure may have changed.",
        )
        return already_notified

    log.info("Available seats: %d", seats)

    if seats > 0:
        if not already_notified:
            message = (
                f"🎉 <b>{seats} seat(s) available!</b>\n\n"
                f"<a href=\"{target_url}\">Open registration page</a>\n"
                f"Hurry up and register!"
            )
            try:
                send_telegram_message(token, chat_id, message)
            except requests.RequestException:
                log.exception("Failed to send Telegram message.")
                return False
            return True
        else:
            log.info("Already notified, skipping.")
            return True
    else:
        log.info("No seats available yet.")
        return False


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    target_url = os.environ.get("TARGET_URL", DEFAULT_URL)
    poll_interval = int(os.environ.get("POLL_INTERVAL_MINUTES", DEFAULT_POLL_INTERVAL_MINUTES))

    if not token or not chat_id:
        log.error("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars are required.")
        sys.exit(1)

    log.info("mgya-watcher started. Polling every %d minute(s). Target: %s", poll_interval, target_url)

    try:
        send_telegram_message(
            token, chat_id,
            f"✅ <b>mgya-watcher started.</b>\nPolling every {poll_interval} min.\nTarget: {target_url}",
        )
    except requests.RequestException:
        log.exception("Failed to send welcome message.")

    already_notified = False
    while True:
        already_notified = check_once(token, chat_id, target_url, already_notified)
        time.sleep(poll_interval * 60)


if __name__ == "__main__":
    main()
