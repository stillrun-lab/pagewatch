"""
Pagewatch — monitor webpages for content changes.

Reads pages.yaml, fetches each URL on a schedule, compares against the last
known snapshot, and notifies via Telegram/Discord when content changes.
State persists in state/snapshots.json.
"""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml
from bs4 import BeautifulSoup

BASE = Path(__file__).parent
PAGES_FILE = BASE / "pages.yaml"
STATE_FILE = BASE / "state" / "snapshots.json"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT = os.getenv("TELEGRAM_CHAT_ID")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")

USER_AGENT = (
    "Mozilla/5.0 (compatible; Pagewatch/1.0; "
    "+https://github.com/stillrun-lab/pagewatch)"
)


def load_pages() -> list[dict]:
    with PAGES_FILE.open() as f:
        return yaml.safe_load(f).get("pages", [])


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def fetch_content(url: str, selector: str | None = None) -> str:
    """Fetch URL and return normalized text. Optionally filter by CSS selector."""
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Strip noise that changes every load
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    if selector:
        elements = soup.select(selector)
        text = "\n".join(el.get_text(" ", strip=True) for el in elements)
    else:
        text = soup.get_text(" ", strip=True)

    return " ".join(text.split())


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def excerpt(text: str, max_len: int = 180) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "..."


def send_telegram(msg: str) -> None:
    if not (TELEGRAM_TOKEN and TELEGRAM_CHAT):
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={
                "chat_id": TELEGRAM_CHAT,
                "text": msg,
                "disable_web_page_preview": "true",
            },
            timeout=10,
        )
    except Exception as e:
        print(f"  ! telegram failed: {e}", file=sys.stderr)


def send_discord(msg: str) -> None:
    if not DISCORD_WEBHOOK:
        return
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": msg}, timeout=10)
    except Exception as e:
        print(f"  ! discord failed: {e}", file=sys.stderr)


def notify(msg: str) -> None:
    print(f"  → CHANGE DETECTED:\n{msg}")
    send_telegram(msg)
    send_discord(msg)


def main() -> int:
    pages = load_pages()
    state = load_state()
    now = datetime.now(timezone.utc).isoformat()
    print(f"[{now}] Pagewatch — checking {len(pages)} page(s)")

    for page in pages:
        name = page.get("name", page["url"])
        url = page["url"]
        selector = page.get("selector")

        try:
            content = fetch_content(url, selector)
        except Exception as e:
            print(f"  ! {name}: fetch failed ({e})", file=sys.stderr)
            continue

        new_hash = content_hash(content)
        prev_hash = state.get(url, {}).get("hash")

        if prev_hash is None:
            print(f"  + {name}: first snapshot recorded")
        elif new_hash != prev_hash:
            msg = (
                f"📰 Page changed: {name}\n{url}\n\n"
                f"New content (excerpt):\n{excerpt(content)}"
            )
            notify(msg)
        else:
            print(f"  · {name}: unchanged")

        state[url] = {
            "hash": new_hash,
            "checked": now,
            "excerpt": excerpt(content, 100),
        }

    save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())