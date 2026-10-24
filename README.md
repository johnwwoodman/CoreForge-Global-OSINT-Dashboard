# CoreForge Global OSINT Dashboard — Release Notes

This document records the development of CoreForge Global OSINT Dashboard, from the initial dashboard through to the introduction of local AI analysis.

CoreForge is an open-source intelligence dashboard designed to bring together publicly available reporting, regional analysis, research publications and podcasts in one place.

The dashboard can be accessed through a web browser, with optional local AI analysis using Ollama.

## Version 1.0 RC3 — Podcast and publication pagination

The Podcasts, Research and Directory tabs now display a manageable number of entries at a time, with Previous and Next controls. Choose 5, 10, 20 or 50 items per page; the default is 10. Each tab keeps its own page selection and item limit while the dashboard is open.

The intelligence feed, podcast collection, regional workspaces and local Ollama analysis are unchanged.

## Version 1.0 RC3 — 24 October 2026

### Specialist Podcast Sources

This update expands the podcast collection system, with a particular focus on Middle East reporting and analysis.

**Changes**

* Added support for collecting podcast episodes from specialist foreign-policy and security organisations.
* Expanded the source catalogue to include programmes from the Middle East Institute, CSIS, International Crisis Group, Chatham House and the Council on Foreign Relations.
* Improved the way podcast episodes are associated with regional workspaces.
* Added collection diagnostics to help identify feeds that are unavailable or not returning episodes.
* Retained audio playback where publishers provide accessible audio files.

Podcast availability depends on the individual publishers' feeds. Not every programme will necessarily return episodes during each collection.

## Version 1.0 RC2 — 24 October 2026

### Podcast Collection Improvements

This release addresses problems with podcast episodes not appearing in the dashboard.

**Changes**

* Improved identification of podcast episodes in RSS feeds.
* Added support for audio attachments supplied by podcast publishers.
* Corrected filtering between podcasts and research publications.
* Added podcast collection information to Data Health.
* Improved messages displayed when no podcast episodes are available.

The underlying intelligence collection and local Ollama integration remain unchanged.

## Version 1.0 RC1 — 24 October 2026

### Dashboard and AI Improvements

This release brings together the main dashboard features and introduces several usability improvements ahead of the first stable release.

**Changes**

* Reorganised Podcasts & Research into three tabs: Podcasts, Research and Directory.
* Retained the original directory of specialist publishers and research organisations.
* Shortened publication descriptions to make browsing easier.
* Added indicators for older publications.
* Introduced configurable source limits for AI-generated assessments.
* Added elapsed-time information while Ollama processes an assessment.
* Improved the Windows launch process without requiring Python.

AI assessments continue to use the selected workspace's collected reporting, with references to the original sources.

## Version 0.8.1 — 24 October 2026

### Simplified Windows Setup

This update removes the need to install Python when running CoreForge with Ollama on Windows.

**Changes**

* Replaced the Python-based local connector with a PowerShell-based alternative.
* Added a Windows launcher that starts the local dashboard and connects to Ollama.
* Updated the setup instructions.
* Retained the existing dashboard and local AI features.

Ollama must still be installed separately to use AI analysis.

## Version 0.8.0 — 24 October 2026

### Local AI Integration

This release introduces optional AI analysis using Ollama.

**Changes**

* Added a Local AI Analyst widget.
* Introduced AI-generated intelligence assessments based on collected reporting.
* Added the ability to ask questions about reporting within a selected workspace.
* Included civil-environment and CMI/CIMIC considerations in assessment prompts.
* Added source references to AI-generated outputs.
* Introduced assessment export.
* Added a local connection between the dashboard and Ollama.

AI analysis runs on the user's computer. The standard dashboard remains usable without Ollama.

Assessments are generated from collected headlines, descriptions and metadata, rather than the full text of every publication.

## Version 0.7.0 — 24 October 2026

### Intelligence Sources and Data Monitoring

This release expands the intelligence collection system and improves source management.

**Changes**

* Fixed an issue where opening the Source Directory replaced live intelligence records.
* Added controls for enabling and disabling publishers within individual workspaces.
* Introduced podcast and research feed collection.
* Added audio playback support for podcast episodes where available.
* Improved the structure of automated weekly briefings.
* Added a Data Health widget showing collection status, feed errors and data freshness.
* Improved interaction with geographic references on the map.
* Added collector version information to assist troubleshooting.

Publisher preferences are stored locally in the browser.

## Version 0.6.1

### Intelligence Collector Improvements

This update focuses on the reliability of the intelligence collection process.

**Changes**

* Updated the RSS collector to improve regional classification.
* Improved identification of geographic references in reporting.
* Expanded intelligence categories beyond general geopolitics.
* Added collector version information to the generated data.
* Improved compatibility between collected records and dashboard widgets.

Geographic references indicate places mentioned in reporting. They should not be treated as confirmed incident locations.

## Version 0.6.0

### Regional Intelligence and Mapping

This release develops the dashboard's regional intelligence capabilities.

**Changes**

* Improved regional workspace handling.
* Expanded geographic reference detection.
* Refined the interactive map and regional framing.
* Improved integration between collected reporting and map references.
* Continued development of intelligence categorisation and filtering.

## Version 0.5.0

### Automated Intelligence Collection

This release develops the use of automatically collected intelligence reporting.

**Changes**

* Expanded RSS-based intelligence collection.
* Improved integration with GitHub Actions.
* Continued development of automatically generated intelligence data.
* Improved handling of source information and publication metadata.

## Version 0.4.0

### Intelligence Briefings

This release introduces and develops briefing functionality.

**Changes**

* Added automated intelligence briefing features.
* Improved the presentation of collected reporting.
* Introduced source-linked briefing content.
* Added support for reading briefings aloud through the browser.

## Version 0.3.3

### Intelligence Feed Controls

**Changes**

* Added pagination options for the Intelligence Feed.
* Expanded filtering by category, publisher, date and region.
* Added saved articles.
* Introduced CSV export.
* Improved handling of map references and watchlist filtering.

## Version 0.3.2

### Dashboard Layout Improvements

**Changes**

* Improved Intelligence Feed sizing and scrolling.
* Added more consistent widget resizing.
* Improved expand and collapse behaviour.
* Refined the dashboard layout for different screen sizes.

## Version 0.3.0

### Interactive Dashboard Development

**Changes**

* Expanded configurable dashboard widgets.
* Developed regional workspaces.
* Improved the presentation of intelligence sources.
* Continued development of the interactive map and reporting views.

## Version 0.2.0

### Dashboard Expansion

**Changes**

* Expanded the initial dashboard layout.
* Added further intelligence widgets and controls.
* Improved navigation and workspace organisation.
* Developed the visual design and user interface.

## Version 0.1.0

### Initial Release

The first version of CoreForge Global OSINT Dashboard established the foundation for a browser-based intelligence dashboard.

**Initial features**

* Dark-themed dashboard interface.
* Configurable intelligence widgets.
* Regional intelligence workspaces.
* Initial source directory.
* Early intelligence feed and mapping functionality.
* CoreForge branding.

---

## Development Status

The main dashboard, automated intelligence collection and optional local Ollama analysis are operational.

Development is focused on improving source coverage, checking platform compatibility and resolving remaining issues before the first stable release.

