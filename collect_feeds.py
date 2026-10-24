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
MAX_PER_FEED = 35
MAX_DESC = 500

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
    'Middle East': ['iran','iraq','israel','gaza','west bank','palestin','lebanon','syria','jordan','yemen','saudi','qatar','bahrain','oman','kuwait','uae','emirates','turkey','türkiye','afghanistan','pakistan','tehran','beirut','riyadh','jerusalem','kabul','islamabad'],
    'Europe': ['france','french','paris','germany','german','berlin','ukraine','ukrainian','russia','russian','moscow','britain','british','london','europe','eu ','nato','italy','italian','spain','spanish','poland','polish','brussels','sweden','swedish'],
    'Americas': ['united states','u.s.','american','washington','canada','canadian','mexico','mexican','brazil','brazilian','argentina','venezuela','colombia','cuba','peru','chile'],
    'Asia-Pacific': ['china','chinese','beijing','taiwan','japan','japanese','tokyo','korea','korean','india','indian','new delhi','indonesia','philippines','vietnam','australia','australian','myanmar','thailand','pacific'],
    'Africa': ['africa','african','sudan','sudanese','somalia','somali','ethiopia','ethiopian','kenya','kenyan','nigeria','nigerian','egypt','egyptian','libya','libyan','morocco','moroccan','congo','mali','sahel','tunisia','algeria'],
}
def infer_regions(title, description, feed_region):
    text = ' ' + (title+' '+description[:220]).lower() + ' '
    found = [region for region, words in REGION_TERMS.items() if any(re.search(r'(?<![a-z])'+re.escape(word)+r'(?![a-z])', text) for word in words)]
    if feed_region != 'all' and feed_region not in found:
        found.insert(0, feed_region)
    return found

def collect():
    records, errors, seen = [], [], set()
    for source, url, category, region in FEEDS:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'CoreForgeOSINT/0.2 (+open-source RSS metadata collector)', 'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml'})
            with urllib.request.urlopen(req, timeout=18) as response:
                raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise ValueError('Feed exceeds 2 MB limit')
            root = ET.fromstring(raw)
            if root.tag.endswith('rss') or root.find('channel') is not None:
                entries = root.findall('./channel/item')
                atom = False
            else:
                entries = root.findall('{http://www.w3.org/2005/Atom}entry')
                atom = True
            count = 0
            for item in entries:
                if count >= MAX_PER_FEED:
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
                seen.add(clean_link)
                clean_title=strip_markup(title)[:300]
                clean_description=strip_markup(description)[:MAX_DESC]
                regions=infer_regions(clean_title,clean_description,region)
                records.append({'title': clean_title, 'source': source, 'description': clean_description, 'category': category, 'region': regions[0] if regions else 'all', 'regions': regions, 'kind': 'news', 'url': clean_link, 'published': date_iso(published)})
                count += 1
            print(f'{source}: {count} articles')
        except Exception as exc:
            errors.append({'source': source, 'message': str(exc)[:200]})
            print(f'{source}: ERROR {exc}')
    records.sort(key=lambda x: x['published'], reverse=True)
    return {'updated': dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00','Z'), 'records': records, 'errors': errors}

if __name__ == '__main__':
    payload = collect()
    if not payload['records']:
        raise SystemExit('No articles collected; leaving last successful snapshot untouched.')
    data = ROOT / 'data'
    text = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    (data / 'live-feed.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (data / 'live-feed.js').write_text('window.COREFORGE_FEED='+text+';\n', encoding='utf-8')
    print(f'Wrote {len(payload["records"])} records; {len(payload["errors"])} feed errors')
