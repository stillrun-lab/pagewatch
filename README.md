# Pagewatch

Monitor any list of webpages and get notified when content changes. Reads
YAML config, runs on GitHub Actions cron, sends a digest to Telegram and
Discord. Built to be deployed in minutes with no server.

## What it does

For each URL in `pages.yaml`, pagewatch fetches the page on a schedule,
extracts the visible text, hashes it, and compares against the last known
snapshot. When the content changes, it sends a notification with the URL
and an excerpt of the new content. Optional CSS selectors let you focus on
specific page regions so noise (ads, timestamps, view counters) doesn't
trigger false alerts.

```yaml
# Example pages.yaml
pages:
  - name: "Hacker News front page"
    url: "https://news.ycombinator.com"
    selector: "tr.athing"

  - name: "Python — latest releases"
    url: "https://www.python.org/downloads/"
```

## Use cases

- Track competitor pricing pages
- Watch job boards for new postings
- Monitor product availability and restocks
- Track regulatory or government page updates
- Watch a blog or news source without manual refresh

## Architecture

```
┌──────────────────────┐
│ GitHub Actions cron  │  every hour
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐    ┌────────────────┐
│ pagewatch.py         │───►│ HTTP fetch     │
│  • load pages.yaml   │    │ + BeautifulSoup│
│  • extract text      │    └────────────────┘
│  • hash & compare    │
│  • notify on change  │
└──────────┬───────────┘
           │
   ┌───────┴────────┐
   ▼                ▼
Telegram        Discord
```

## Features

- Multiple pages from a single YAML config
- Optional CSS selectors to filter noise
- SHA-256 content hashing — resistant to false positives
- Telegram and Discord notifications (independent — use either or both)
- State persists across runs to deduplicate alerts
- Adjustable cadence via standard cron syntax
- Zero-ops deployment via GitHub Actions

## Quick start

1. Fork or clone this repo
2. Edit `pages.yaml` with the URLs you want to watch
3. Set repo secrets:
   - `TELEGRAM_BOT_TOKEN` — from [@BotFather](https://t.me/BotFather)
   - `TELEGRAM_CHAT_ID` — your Telegram user/chat ID
   - `DISCORD_WEBHOOK_URL` — optional, server channel webhook
4. Commit and push. The workflow runs automatically every hour.

## Configuration

Each entry in `pages.yaml`:

| Field      | Required | Notes                                                        |
|------------|----------|--------------------------------------------------------------|
| `name`     | yes      | Friendly label used in notifications                         |
| `url`      | yes      | Full URL with scheme                                         |
| `selector` | no       | CSS selector to scope content (e.g., `tr.athing`, `.product-price`) |

To force a re-snapshot for a page, delete its entry from `state/snapshots.json`.

To change check frequency, edit the cron in `.github/workflows/check.yml`.
Hourly is the default; tighter intervals are supported (every 15 min minimum
on GitHub Actions free tier in practice).

## Custom builds

Need this extended for your use case — multi-recipient routing, diff
visualization, screenshot capture, sentiment scoring, integration with
internal tools? I build production automation systems for traders, operators,
and businesses.

**Built by [Stillrun Lab](https://github.com/stillrun-lab)** — automation systems built to run themselves.

- 💼 Hire me on Upwork: *(link coming soon)*
- 🐦 [@trade_4l on X](https://x.com/trade_4l)
- 📧 *(email coming soon)
