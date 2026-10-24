#!/usr/bin/env python3
"""Collect public RSS/Atom headline metadata into a static, source-linked snapshot.
Uses Python standard library; only GitHub Actions / maintainers need Python.
"""
import datetime as dt
import email.utils
import html
import json
import pathlib
import re
import urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
FEEDS = [
    ('BBC World', 'https://feeds.bbci.co.uk/news/world/rss.xml', 'Geopolitics', 'all'),
    ('BBC Middle East', 'https://feeds.bbci.co.uk/news/world/middle_east/rss.xml', 'Geopolitics', 'Middle East'),
    ('BBC Europe', 'https://feeds.bbci.co.uk/news/world/europe/rss.xml', 'Geopolitics', 'Europe'),
    ('BBC Africa', 'https://feeds.bbci.co.uk/news/world/africa/rss.xml', 'Geopolitics', 'Africa'),
    ('BBC Asia', 'https://feeds.bbci.co.uk/news/world/asia/rss.xml', 'Geopolitics', 'Asia-Pacific'),
    ('BBC Americas', 'https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml', 'Geopolitics', 'Americas'),
    ('The Guardian World', 'https://www.theguardian.com/world/rss', 'Geopolitics', 'all'),
    ('The Guardian Middle East', 'https://www.theguardian.com/world/middleeast/rss', 'Geopolitics', 'Middle East'),
    ('UN News', 'https://news.un.org/feed/subscribe/en/news/all/rss.xml', 'Humanitarian', 'all'),
    ('UN News Middle East', 'https://news.un.org/feed/subscribe/en/news/region/middle-east/rss.xml', 'Humanitarian', 'Middle East'),
]
# Additional publisher feeds; failures are isolated and reported in source health.
FEEDS.extend([
    ('BBC Business', 'https://feeds.bbci.co.uk/news/business/rss.xml', 'Economics', 'all'),
    ('BBC Technology', 'https://feeds.bbci.co.uk/news/technology/rss.xml', 'Cyber', 'all'),
    ('The Guardian Environment', 'https://www.theguardian.com/environment/rss', 'Disasters', 'all'),
    ('The Guardian Global Development', 'https://www.theguardian.com/global-development/rss', 'Humanitarian', 'all'),
    ('The Guardian Europe', 'https://www.theguardian.com/world/europe-news/rss', 'Geopolitics', 'Europe'),
    ('The Guardian Africa', 'https://www.theguardian.com/world/africa/rss', 'Geopolitics', 'Africa'),
    ('The Guardian Asia', 'https://www.theguardian.com/world/asia/rss', 'Geopolitics', 'Asia-Pacific'),
])

# Specialist source endpoints are best-effort. Invalid/unavailable feeds are reported,
# not silently treated as successful collection. Entries remain linked to publishers.
SPECIAL_FEEDS = [
    ('BBC Global News Podcast', 'https://podcasts.files.bbci.co.uk/p02nq0gn.rss', 'Geopolitics', 'all', 'podcast'),
    ('BBC Newshour Podcast', 'https://podcasts.files.bbci.co.uk/p002vsnk.rss', 'Geopolitics', 'all', 'podcast'),
    ('The Guardian Long Read', 'https://www.theguardian.com/news/series/the-long-read/rss', 'Geopolitics', 'all', 'research'),
    ('The Guardian Global Development Analysis', 'https://www.theguardian.com/global-development/rss', 'Humanitarian', 'all', 'research'),
]
# Podcast discovery uses Apple's public podcast catalogue to obtain current RSS URLs.
# Publisher/title constraints avoid accidentally importing unrelated similarly named shows.
# No Apple account, API key or paid service is required. RSS is fetched directly from publishers.
PODCAST_CATALOGUE = [
    ('MEI Middle East Focus', 'Middle East Focus Middle East Institute', ('middle east focus',), ('middle east institute', 'mei'), 'Middle East'),
    ('MEI Taking the Edge Off', 'Taking the Edge Off the Middle East Brian Katulis', ('taking the edge off',), ('middle east institute', 'mei'), 'Middle East'),
    ('CSIS Babel', 'Babel Translating the Middle East CSIS', ('babel',), ('csis', 'strategic and international studies'), 'Middle East'),
    ('Crisis Group Hold Your Fire', 'Hold Your Fire International Crisis Group', ('hold your fire',), ('crisis group',), 'all'),
    ('Chatham House podcasts', 'Chatham House Independent Thinking podcast', ('independent thinking',), ('chatham house',), 'all'),
    ('CFR The President Inbox', 'The President Inbox Council on Foreign Relations', ('president', 'inbox'), ('council on foreign relations', 'cfr'), 'all'),
]

def discover_podcast_feed(query, title_terms, publisher_terms):
    """Resolve an RSS feed from a public catalogue; reject uncertain matches."""
    from urllib.parse import urlencode, urlparse
    api = 'https://itunes.apple.com/search?' + urlencode({'term':query, 'entity':'podcast', 'media':'podcast', 'limit':30})
    req = urllib.request.Request(api, headers={'User-Agent':'CoreForgeOSINT/1.0', 'Accept':'application/json'})
    with urllib.request.urlopen(req, timeout=18) as response:
        payload = json.load(response)
    for item in payload.get('results', []):
        title = str(item.get('collectionName', '')).lower()
        artist = str(item.get('artistName', '')).lower()
        feed = str(item.get('feedUrl', ''))
        parsed = urlparse(feed)
        if (any(term in title for term in title_terms)
                and any(term in artist or term in title for term in publisher_terms)
                and parsed.scheme == 'https' and parsed.hostname):
            return feed
    raise ValueError('No verified publisher/title match with an HTTPS RSS feed in podcast catalogue')

# Approximate reference points, NOT verified incident coordinates. Only title matches
# are mapped; descriptions can mention a place in unrelated background context.
# Country markers represent the country, not a precise incident location.
PLACE_POINTS = {
    'tehran': (35.69, 51.39), 'beirut': (33.89, 35.50), 'gaza': (31.50, 34.47),
    'jerusalem': (31.77, 35.21), 'damascus': (33.51, 36.29), 'baghdad': (33.31, 44.37),
    'riyadh': (24.71, 46.68), 'sanaa': (15.37, 44.19), 'kabul': (34.53, 69.17),
    'islamabad': (33.69, 73.06), 'paris': (48.86, 2.35), 'london': (51.51, -0.13),
    'berlin': (52.52, 13.40), 'kyiv': (50.45, 30.52), 'moscow': (55.75, 37.62),
    'brussels': (50.85, 4.35), 'rome': (41.90, 12.50), 'madrid': (40.42, -3.70),
    'washington': (38.90, -77.04), 'new york': (40.71, -74.01),
    'beijing': (39.90, 116.40), 'tokyo': (35.68, 139.69), 'taipei': (25.03, 121.56),
    'seoul': (37.57, 126.98), 'delhi': (28.61, 77.21),
    'nairobi': (-1.29, 36.82), 'khartoum': (15.50, 32.56),
    'addis ababa': (9.03, 38.74), 'cairo': (30.04, 31.24),
    'tripoli': (32.89, 13.19), 'aleppo': (36.20, 37.16), 'mosul': (36.34, 43.13),
    'ramallah': (31.90, 35.20), 'rafah': (31.30, 34.25), 'doha': (25.29, 51.53),
    'dubai': (25.20, 55.27), 'abu dhabi': (24.45, 54.38), 'karachi': (24.86, 67.01),
    'lahore': (31.55, 74.34), 'peshawar': (34.01, 71.58), 'herat': (34.35, 62.20),
    'kandahar': (31.63, 65.74), 'odessa': (46.48, 30.73), 'odesa': (46.48, 30.73),
    'kharkiv': (49.99, 36.23), 'tbilisi': (41.72, 44.79), 'baku': (40.41, 49.87),
    'tashkent': (41.30, 69.24), 'astana': (51.17, 71.43),
    'iran': (32.43, 53.69), 'iraq': (33.22, 43.68), 'israel': (31.05, 34.85),
    'lebanon': (33.85, 35.86), 'syria': (34.80, 38.99), 'yemen': (15.55, 48.52),
    'afghanistan': (33.94, 67.71), 'pakistan': (30.38, 69.35),
    'france': (46.60, 2.21), 'germany': (51.17, 10.45),
    'ukraine': (48.38, 31.17), 'russia': (61.52, 105.32),
    'china': (35.86, 104.20), 'taiwan': (23.70, 120.96),
    'japan': (36.20, 138.25), 'sudan': (12.86, 30.22),
    'somalia': (5.15, 46.20), 'ethiopia': (9.15, 40.49),
    'egypt': (26.82, 30.80), 'brazil': (-14.24, -51.93),
    'canada': (56.13, -106.35), 'mexico': (23.63, -102.55),
}
CITY_NAMES = {'tehran','beirut','gaza','jerusalem','damascus','baghdad','riyadh','sanaa','kabul','islamabad','paris','london','berlin','kyiv','moscow','brussels','rome','madrid','washington','new york','beijing','tokyo','taipei','seoul','delhi','nairobi','khartoum','addis ababa','cairo','tripoli','aleppo','mosul','ramallah','rafah','doha','dubai','abu dhabi','karachi','lahore','peshawar','herat','kandahar','odessa','odesa','kharkiv','tbilisi','baku','tashkent','astana'}
def approximate_place(title):
    lower = title.lower()
    matches = [(name,point) for name,point in PLACE_POINTS.items()
               if re.search(r'(?<![a-z])'+re.escape(name)+r'(?![a-z])', lower)]
    if not matches:
        return {}
    # A title naming multiple locations is ambiguous: do not invent a single incident point.
    # Prefer explicit city over its enclosing country only when unambiguous.
    cities = [(name,point) for name,point in matches if name in CITY_NAMES]
    selected = cities if cities else matches
    if len(selected) != 1:
        return {}
    name, (lat,lon) = selected[0]
    return {'lat':lat,'lon':lon,'place':name.title(),'location_precision':'city-reference' if name in CITY_NAMES else 'country-centroid', 'location_method':'headline-keyword', 'location_verified':False}

# Rule-based topic labels are approximate; source/feed section is only a fallback.
TOPIC_PATTERNS = {
    'Humanitarian': [r'\bhumanitarian\b',r'\baid\b',r'\brefugee',r'\bdisplac',r'\bfamine\b',r'\bhunger\b',r'\bfood insecurity\b',r'\brelief\b',r'\bhealth crisis\b'],
    'Defence': [r'\bmilitary\b',r'\bmissile',r'\bdrone',r'\bairstrike',r'\barmed forces\b',r'\bdefen[cs]e\b',r'\bweapon',r'\bnaval\b',r'\barmy\b',r'\btroops\b',r'\bceasefire\b'],
    'Cyber': [r'\bcyber',r'\bhack',r'\bransomware\b',r'\bmalware\b',r'\bdata breach\b',r'\bphishing\b'],
    'Disasters': [r'\bearthquake',r'\bflood',r'\bwildfire',r'\bcyclone',r'\bhurricane',r'\btsunami',r'\blandslide',r'\bdrought\b'],
    'Economics': [r'\binflation\b',r'\bgdp\b',r'\beconom',r'\btrade\b',r'\btariff',r'\bcentral bank\b',r'\binterest rate',r'\bmarket',r'\bexports?\b',r'\bimports?\b'],
}
def infer_category(title, description, fallback):
    # Title carries greater relevance than contextual feed descriptions.
    title_text = title.lower()
    description_text = description[:240].lower()
    for category, patterns in TOPIC_PATTERNS.items():
        if any(re.search(pattern, title_text) for pattern in patterns):
            return category
    if fallback != 'Geopolitics':
        return fallback
    for category, patterns in TOPIC_PATTERNS.items():
        if any(re.search(pattern, description_text) for pattern in patterns):
            return category
    return fallback

def approximate_reference(title, description):
    point = approximate_place(title)
    if point:
        return point
    # Lead-sentence matches only, and only where exactly one location is present.
    lead = re.split(r'[.!?]', description[:180], maxsplit=1)[0]
    point = approximate_place(lead)
    if point:
        point['location_method'] = 'description-lead-keyword'
    return point

MAX_PER_FEED = 35
MAX_DESC = 500
PODCAST_TITLE = re.compile(r'\bpodcast\b|\b(audio|listen)\s+(episode|edition)\b', re.I)

def strip_markup(s):
    s = re.sub(r'<[^>]*>', ' ', s or '')
    return re.sub(r'\s+', ' ', html.unescape(s)).strip()

def findtext(el, *names):
    for name in names:
        v = el.findtext(name)
        if v:
            return v.strip()
    return ''

def date_iso(raw):
    if not raw:
        return ''
    try:
        d = email.utils.parsedate_to_datetime(raw)
        return d.astimezone(dt.timezone.utc).isoformat().replace('+00:00', 'Z')
    except (ValueError, TypeError, IndexError):
        try:
            return dt.datetime.fromisoformat(raw.replace('Z', '+00:00')).isoformat()
        except ValueError:
            return ''

# Conservative keyword matching: regional relevance, NOT event geolocation.
REGION_TERMS = {
    'Middle East': ['iran','iraq','israel','gaza','west bank','palestin','lebanon','kurdish','kurds','houthi','hezbollah','hamas','taliban','kabul','karachi','lahore','peshawar','herat','kandahar','rafah','ramallah','aleppo','mosul','doha','dubai','abu dhabi','syria','jordan','yemen','saudi','qatar','bahrain','oman','kuwait','uae','emirates','turkey','türkiye','afghanistan','pakistan','tehran','beirut','riyadh','jerusalem','kabul','islamabad'],
    'Europe': ['france','french','paris','germany','german','berlin','ukraine','ukrainian','russia','russian','moscow','britain','british','london','europe','eu ','nato','italy','italian','spain','spanish','poland','polish','brussels','kharkiv','odesa','odessa','georgia','tbilisi','azerbaijan','baku','sweden','swedish'],
    'Americas': ['united states','u.s.','american','washington','canada','canadian','mexico','mexican','brazil','brazilian','argentina','venezuela','colombia','cuba','peru','chile'],
    'Asia-Pacific': ['china','chinese','beijing','taiwan','japan','japanese','tokyo','korea','korean','india','indian','new delhi','indonesia','philippines','vietnam','australia','australian','myanmar','thailand','pacific','north korea','south korea','kashmir','kazakhstan','uzbekistan','astana','tashkent'],
    'Africa': ['africa','african','sudan','sudanese','somalia','somali','ethiopia','ethiopian','kenya','kenyan','nigeria','nigerian','egypt','egyptian','libya','libyan','morocco','moroccan','congo','mali','sahel','tunisia','algeria'],
}
def infer_regions(title, description, feed_region):
    text = ' ' + (title+' '+description[:220]).lower() + ' '
    found = [region for region, words in REGION_TERMS.items() if any(re.search(r'(?<![a-z])'+re.escape(word)+r'(?![a-z])', text) for word in words)]
    if feed_region != 'all' and feed_region not in found:
        found.insert(0, feed_region)
    return found

def classify_kind(default_kind, title, item, atom=False):
    """Detect embedded podcast episodes even in non-podcast publisher feeds."""
    enclosure = item.find('enclosure') if not atom else None
    if atom:
        enclosure = next((link for link in item.findall('{http://www.w3.org/2005/Atom}link')
                          if link.get('rel') == 'enclosure'), None)
    audio_url = ''
    if enclosure is not None:
        candidate = enclosure.get('url', '') if not atom else enclosure.get('href', '')
        mime = enclosure.get('type', '').lower()
        if candidate.startswith('https://') and (mime.startswith('audio/') or re.search(r'\.(mp3|m4a|aac|ogg)(?:[?#]|$)', candidate, re.I)):
            audio_url = candidate
    # A podcast-specific feed can contain entries with no downloadable audio.
    # Publisher feeds can contain podcast episodes with an audio enclosure.
    # Title-only matches are flagged as podcast but without an invented player.
    kind = 'podcast' if default_kind == 'podcast' or audio_url or PODCAST_TITLE.search(title) else default_kind
    return kind, audio_url

def parse_feed(raw, source, category, region, kind, seen):
    root = ET.fromstring(raw)
    if root.tag.endswith('rss') or root.find('channel') is not None:
        entries = root.findall('./channel/item')
        atom = False
    else:
        entries = root.findall('{http://www.w3.org/2005/Atom}entry')
        atom = True
    output = []
    for item in entries:
        if len(output) >= MAX_PER_FEED:
            break
        if atom:
            ns = '{http://www.w3.org/2005/Atom}'
            title = findtext(item, ns+'title')
            description = findtext(item, ns+'summary', ns+'content')
            published = findtext(item, ns+'published', ns+'updated')
            links = item.findall(ns+'link')
            link = next((x.get('href', '') for x in links if x.get('rel', 'alternate') == 'alternate'), '')
        else:
            title = findtext(item, 'title')
            description = findtext(item, 'description')
            published = findtext(item, 'pubDate')
            link = findtext(item, 'link')
        if not title or not link.startswith('https://'):
            continue
        clean_link = link.split('#')[0]
        if clean_link in seen:
            continue
        clean_title = strip_markup(title)[:300]
        clean_description = strip_markup(description)[:MAX_DESC]
        entry_kind, audio_url = classify_kind(kind, clean_title, item, atom)
        regions = infer_regions(clean_title, clean_description, region)
        output.append({'title': clean_title, 'source': source, 'description': clean_description,
                       'category': infer_category(clean_title, clean_description, category),
                       'region': regions[0] if regions else 'all', 'regions': regions,
                       'kind': entry_kind, **({'audio_url': audio_url} if audio_url else {}),
                       'url': clean_link, 'published': date_iso(published),
                       **approximate_reference(clean_title, clean_description)})
        seen.add(clean_link)
    return output

def collect():
    records, errors, seen = [], [], set()
    for source, url, category, region, kind in [(s,u,c,r,'news') for s,u,c,r in FEEDS]+SPECIAL_FEEDS:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'CoreForgeOSINT/0.2 (+open-source RSS metadata collector)', 'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml'})
            with urllib.request.urlopen(req, timeout=18) as response:
                raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise ValueError('Feed exceeds 2 MB limit')
            added = parse_feed(raw, source, category, region, kind, seen)
            records.extend(added)
            print(f'{source}: {len(added)} records ({sum(x["kind"] == "podcast" for x in added)} podcasts)')
        except Exception as exc:
            errors.append({'source': source, 'message': str(exc)[:200]})
            print(f'{source}: ERROR {exc}')
    # Keep specialist discovery failures isolated from existing news collection.
    # Deduplication is shared with ordinary feeds, so one episode is only stored once.
    podcast_diagnostics = []
    for source, query, titles, publishers, region in PODCAST_CATALOGUE:
        try:
            url = discover_podcast_feed(query, titles, publishers)
            req = urllib.request.Request(url, headers={'User-Agent':'CoreForgeOSINT/1.0', 'Accept':'application/rss+xml, application/xml, text/xml'})
            with urllib.request.urlopen(req, timeout=18) as response:
                raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise ValueError('Podcast RSS exceeds 2 MB limit')
            added = parse_feed(raw, source, 'Geopolitics', region, 'podcast', seen)
            records.extend(added)
            podcast_diagnostics.append({'source':source,'status':'ok','episodes':len(added)})
            print(f'{source}: {len(added)} podcast episodes')
        except Exception as exc:
            errors.append({'source':source, 'message':str(exc)[:200]})
            podcast_diagnostics.append({'source':source,'status':'error','episodes':0})
            print(f'{source}: ERROR {exc}')
    records.sort(key=lambda x: x['published'], reverse=True)
    return {'updated': dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00','Z'), 'records': records, 'errors': errors, 'sources_checked': len(FEEDS)+len(SPECIAL_FEEDS)+len(PODCAST_CATALOGUE), 'sources_ok': len(FEEDS)+len(SPECIAL_FEEDS)+len(PODCAST_CATALOGUE)-len(errors), 'collector_version':'1.0.0-rc3', 'classification_method':'keyword-heuristic', 'location_method':'headline-or-lead-reference', 'content_counts': {kind: sum(r['kind'] == kind for r in records) for kind in ('news','podcast','research')}, 'podcast_sources': podcast_diagnostics, 'feed_health': 'See errors for failed source names'}

if __name__ == '__main__':
    payload = collect()
    if not payload['records']:
        raise SystemExit('No articles collected; leaving last successful snapshot untouched.')
    data = ROOT / 'data'
    text = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    (data / 'live-feed.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (data / 'live-feed.js').write_text('window.COREFORGE_FEED='+text+';\n', encoding='utf-8')
    print(f'Wrote {len(payload["records"])} records; {len(payload["errors"])} feed errors')
