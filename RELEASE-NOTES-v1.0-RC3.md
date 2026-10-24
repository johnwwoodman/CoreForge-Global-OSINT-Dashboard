# CoreForge v1.0 RC3 — Specialist podcast source expansion

This release adds **publisher-validated podcast RSS discovery** for MEI Middle East Focus, MEI Taking the Edge Off, CSIS Babel, International Crisis Group Hold Your Fire, Chatham House Independent Thinking, and CFR The President’s Inbox.

GitHub Actions runs Python to discover public podcast RSS feeds through the Apple podcast catalogue, verifies publisher/title, and collects episode metadata directly from the returned HTTPS RSS feed. No Apple account or API key is required. Availability varies: a source that cannot be verified is logged as an error, never replaced with unrelated results. Source coverage is not guaranteed; the podcast may be archived or renamed.

MEI and CSIS regional shows are assigned Middle East relevance. General global shows are tagged by episode topic. Existing Guardian/BBC/news feeds remain intact. Podcast source diagnostics are included in `data/live-feed.json` under `podcast_sources`.

## Deployment
Upload the GitHub update ZIP **contents**, preserving paths. Replace `scripts/collect_feeds.py` inside `scripts/`, not in repository root. Do not replace `data/` or `.github/workflows/`. Run Collect Intelligence Feeds in GitHub Actions, then verify `collector_version: 1.0.0-rc3`, `content_counts.podcast`, and `podcast_sources` in `data/live-feed.json`.

The local Windows application reads the live GitHub data. Updating the local ZIP alone does not execute the collector. Python is needed only by GitHub Actions, not by Windows users.

This release has been syntax/fixture tested, but publisher feed discovery must be validated by the live GitHub workflow.
