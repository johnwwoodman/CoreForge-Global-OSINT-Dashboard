## v1.3.3 — Reliability and country intelligence (2026-10-25)

- Country Profile layout now wraps long values and collapses provider diagnostics.
- Added copyable country summaries and browser-local analyst notes (not synced).
- Shows primary currency by default and clear leadership check status.
- Improved rotating leadership collection to include six priority countries per run while retaining worldwide coverage.
- Shortened UN publisher errors; previously collected UN News items remain preserved during upstream failures. Publisher HTTP 406 responses cannot be bypassed reliably by a static RSS client.
- Population and GDP automation, map layers, podcasts, and local AI remain unchanged.

## v1.3.2 — Leadership coverage and concurrent updates

- Daily Wikidata batch includes one rotating priority country (Middle East and major global countries) plus worldwide rotation; candidate names remain unverified.
- Country update workflow fetches and rebases against the latest main branch before publishing, with bounded retries and no force pushes.
- Existing data remains cached if an upstream service is unavailable.

## v1.3.1 — Country collector reliability fix

- REST Countries: validate usable records instead of requiring a fixed country count; retry without field filtering.
- World Bank: populate missing ISO3 identifiers, select latest dated population/GDP records, and allow partial successes.
- Wikidata: limit to one small rotating batch per daily run, stop on HTTP 429, and retain previously cached leadership. Full global leadership coverage is gradual and depends on Wikidata availability and accuracy.
- Preserve previous snapshot if every source fails. Existing map, feeds and UI are unchanged.
- Workflow installs `pycountry` to map ISO2 to ISO3.

## v1.3 — Automated Country Intelligence (25 October 2026)

- Daily GitHub Actions refresh for geography (REST Countries), dated population and GDP (World Bank), and candidate political leadership/government descriptions (Wikidata).
- Last-good-value preservation on partial upstream outages, with per-source refresh diagnostics in the generated `data/country-facts.json`.
- Country Profile displays head of state and head of government separately, data-source links, update dates, GDP and dated population where available, and publisher/date for related intelligence.
- BBC World links are provided for context; BBC content is **not scraped or republished**. Older BBC country profiles may be stale.
- Wikidata leadership is explicitly **not independently verified**; missing/ambiguous values are not presented as confirmed. GitHub Actions must successfully run to populate new values.
- All features remain browser-first and free; Python runs in GitHub Actions, not on end-user machines.
- Existing map layers, UN feed collection, podcasts, and local Ollama integration are unchanged.

**Deployment:** upload the update ZIP preserving folders; run **Actions → Update country intelligence → Run workflow**, then wait for the action to commit `data/country-facts.json`. A successful workflow is necessary to replace the bundled historical population and fill leadership. If repository Actions lacks Contents write permissions, enable workflow read/write permissions. The first update is not pre-populated with live leadership because external API access could not be verified in the build environment.

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

## v1.2.0 — 25 October 2026

**Worldwide country profiles:** Bundled country reference data for worldwide offline lookup, including Fiji and Syria. Historical populations in the bundled fallback are explicitly labelled as undated and must not be treated as current. When the online REST Countries API is available, it can update the displayed basic facts. Added related reporting from the current intelligence snapshot and direct reference links. Political leadership and government type are not automatically verified and are intentionally linked rather than guessed. BBC World coverage is a reference link, not a scraped or licensed BBC dataset.

**Automated updates:** Added `scripts/update_country_facts.py` and a weekly GitHub Actions workflow to refresh the country snapshot. A failed refresh leaves the existing snapshot untouched. Map layers, podcasts, local AI and the now-working UN feeds are unchanged.

## v1.1.1 — 25 October 2026

**Map layers and country profiles:** Moved the layer controls below the map so they are always visible rather than clipped by the map viewport. Added Standard, Maritime, Aviation and Clear presets, plus individual layer switches. Choices persist in the browser. Switching layers no longer redraws the entire dashboard or closes the layer controls.

**Country profiles:** Corrected the REST Countries request to specify fields, and added offline reference facts for 27 commonly used country names so basic profiles still display when the external service is unavailable. Offline population figures are approximate and not live; leadership information is deliberately not invented. Other countries continue to use REST Countries when reachable.

**UN News:** Added publisher-hosted alternate RSS endpoint attempts and clearer collection diagnostics. The dedicated UN News Middle East feed and global UN News feed remain configured. These endpoints must be verified by a successful GitHub Actions run; if the publisher serves invalid content at every endpoint, Data Health will continue to report the failure.

The maritime and aviation routes remain indicative geographic reference lines, not live vessel or aircraft positions.

## v1.1.0 — 25 October 2026

Introduced maritime and aviation reference layers, selectable strategic chokepoints, major ports, airports, sea labels and a country profile widget. Existing intelligence collection, podcasts, research and optional Ollama analysis were retained.

## v1.0 Stable — 24 October 2026

Expanded podcast discovery to specialist international-affairs programmes, including Middle East Institute, CSIS, International Crisis Group, Chatham House and Council on Foreign Relations. Added source-level diagnostics for discovered feeds and their episode counts. Added pagination to the Podcasts, Research and Directory tabs: 5, 10, 20 or 50 entries per page, with 10 as the default.

**Maintenance update:** Retained the dedicated UN News Middle East feed and added checks for empty or invalid responses, with a fallback to relevant articles from the main UN News feed when necessary. Collection results depend on publisher availability.

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

### UN News Middle East feed resilience (24 October 2026)

The dedicated UN News Middle East RSS source remains configured. Some collection
requests return an empty or non-XML response even though RSS directories report
the URL as active. The collector now detects that response, attempts the UN News
global RSS feed, and retains only articles classified as Middle East-related.
When fallback is used, `warnings` in the generated JSON explains this. If both
UN feeds fail, Data Health continues to report an error. This is a fallback,
not proof that the dedicated regional endpoint is reliably accessible.



### v1.1.2 — Country profile and UN News diagnostics
- Country profiles now show bundled reference facts immediately for supported countries, even when the country API is blocked.
- Country facts remain clearly marked as approximate; political officeholders require current verification.
- UN News collector now reports failures without falsely marking feeds healthy and preserves previously collected genuine UN News articles when available (not labelled as fresh).
- UN News RSS availability remains dependent on publisher access from GitHub Actions.

### v1.4.0 — Worldwide political leadership collection (25 October 2026)
- New `scripts/update_leadership.py` enriches country profiles with head-of-state and head-of-government candidates using Wikipedia country-to-Wikidata mappings and batched Wikidata entity claims. It avoids the previously rate-limited SPARQL service.
- Daily refresh prioritises Middle East countries, the UK, US and other high-interest countries; other countries rotate through subsequent runs. Coverage is reported in the country profile. Names remain explicitly **unverified** until independently corroborated.
- The collector only accepts unambiguous current claims based on recorded start/end qualifiers, and retains cached data when a provider fails. Incomplete Wikidata claims can still leave countries without names; coverage is not guaranteed.
- REST Countries parser handles structured JSON error envelopes without treating them as country records. The legacy v3 endpoint is deprecated; when it fails, previously cached geographic facts remain.
- The local Windows bundle contains a snapshot and does not automatically inherit new GitHub Actions results. For latest leadership, use the GitHub Pages edition after the daily workflow completes.
