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
                records.append({'title': strip_markup(title)[:300], 'source': source, 'description': strip_markup(description)[:MAX_DESC], 'category': category, 'region': region, 'kind': 'news', 'url': clean_link, 'published': date_iso(published)})
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
