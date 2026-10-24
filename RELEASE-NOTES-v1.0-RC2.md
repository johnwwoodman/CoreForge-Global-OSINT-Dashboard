# CoreForge v1.0 RC2 — Podcast collection correction

- Podcast and research tabs read the full collected dataset and respect workspace region and disabled sources, rather than being suppressed by unrelated news filters.
- Collector detects podcast episodes in general RSS feeds from audio enclosures and explicit podcast titles; only verified audio enclosures produce a player.
- Podcast-specific RSS feeds remain supported and failures are listed by source in Data Health / Source Directory.
- Collector reports counts by content type in JSON and console logs.
- No change to Ollama, local launcher or GitHub Actions workflow.

**Important:** A local application update alone cannot create missing episodes. The corrected collector must be committed to `scripts/collect_feeds.py` and run via GitHub Actions, then the local dashboard refreshed. Feed availability cannot be guaranteed.
