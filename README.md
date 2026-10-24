# CoreForge Global OSINT Dashboard

CoreForge is a browser-based, open-source dashboard for public reporting, approximate geographic references, research publications and podcasts. Optional local analysis uses Ollama; the public dashboard does not require AI or an installation.

## Using CoreForge

Open the GitHub Pages dashboard for live reporting, regional workspaces, the map, source controls, podcasts and research. The collector runs on GitHub Actions, not on visitors' computers. The dashboard reads the published `data/live-feed.json` snapshot. Source availability varies and may change without notice.

For local AI on Windows, install Ollama, download the Windows package, extract it and run `START-COREFORGE-WINDOWS.bat`. The local launcher uses PowerShell and does not require Python. Keep the launcher window open while using the local AI analyst. Qwen3 8B works on a 16 GB CPU-only machine but longer assessments can take several minutes. AI results are based on collected titles, summaries and metadata, not independently verified full articles.

## Updating the repository

Place `app.js`, `index.html`, `styles.css` and `README.md` in the repository root. Place `collect_feeds.py` and `build_weekly_briefs.py` inside `scripts/`. Keep the existing `.github/workflows/` and `data/` directories. Run the intelligence collection workflow after changing the collector. Avoid uploading duplicate scripts at the root.

## Data and limitations

Sources are linked to their original publishers. Approximate map references identify locations mentioned in headlines; they are not verified incident locations. RSS feeds can fail or return no records. Publisher preferences and layout settings are saved in the browser. Local AI analysis should be checked against original sources and must not be treated as corroborated intelligence.

---

# Release history

All release notes are kept in this README. No separate `RELEASE-NOTES*.md` files are needed.

## v1.0 RC3 — 24 October 2026

Expanded podcast discovery to specialist international-affairs programmes, including Middle East Institute, CSIS, International Crisis Group, Chatham House and Council on Foreign Relations. Added source-level diagnostics for discovered feeds and their episode counts. Added pagination to the Podcasts, Research and Directory tabs: 5, 10, 20 or 50 entries per page, with 10 as the default.

**Maintenance update:** Removed the non-working dedicated UN News Middle East RSS endpoint after it returned an empty or invalid XML response. The collector continues to use the UN News global feed and classifies relevant articles by region. This removes the repeated parser error without claiming the retired endpoint is operational. Regional coverage depends on articles present in the global feed.

## v1.0 RC2 — 24 October 2026

Improved podcast detection, audio-enclosure handling and filtering between podcasts and research publications. Added podcast counts and collection diagnostics to help distinguish empty feeds from display problems.

## v1.0 RC1 — 24 October 2026

Split Podcasts & Research into Podcasts, Research and Directory tabs. Kept the specialist publisher directory, shortened descriptions and marked older publications. Added selectable source limits and elapsed-time feedback for Ollama assessments. The Windows launcher remained Python-free.

## v0.8.1 — 24 October 2026

Replaced the Windows Python-based local connector with a PowerShell-based launcher. Ollama still needs to be installed separately for AI analysis.

## v0.8.0 — 24 October 2026

Introduced the optional local AI Analyst, workspace-specific questions and assessments, source references, CMI/CIMIC prompts and export. AI analysis runs locally and the online dashboard remains available without it.

## v0.7.0 — 24 October 2026

Improved source management and the Source Directory behaviour, added podcast and research collection, expanded weekly briefings and introduced the Data Health widget with collection status, errors and freshness information.

## v0.6.1

Improved RSS classification, approximate geographic references and collector version metadata. Geographic references are not confirmed incident coordinates.

## v0.6.0

Developed regional workspaces, geographic reference handling and interactive map framing.

## v0.5.0

Expanded automated RSS collection, GitHub Actions integration and publication metadata handling.

## v0.4.0

Developed source-linked weekly briefings and browser read-aloud support.

## v0.3.3

Added Intelligence Feed pagination, more filters, saved articles and CSV export.

## v0.3.2

Improved Intelligence Feed sizing, scrolling and widget expand/collapse behaviour.

## v0.3.0

Expanded configurable widgets, regional workspaces, reporting views and map interaction.

## v0.2.0

Expanded the dashboard layout, navigation, intelligence widgets and initial automated collection support.

## v0.1.0

Established the initial browser-based dashboard, dark theme, configurable widgets, regional views, source directory and CoreForge branding.

*Earlier entries summarise the development history rather than reproduce every historical commit.*


### UN News Middle East RSS correction

The dedicated UN News Middle East source has been retained and its feed URL corrected to the regional RSS endpoint (`/news/region/middle-east/feed/rss.xml`). The main UN News feed remains enabled separately. The revised URL is listed by an independent feed monitor as working; a successful GitHub Actions collection is still required to confirm access from the runner.
