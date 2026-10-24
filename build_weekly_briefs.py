#!/usr/bin/env python3
"""Build source-linked weekly headline digests, without an AI dependency."""
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
WORKSPACES = {'global': 'all', 'middle-east': 'Middle East', 'europe': 'Europe', 'americas': 'Americas', 'asia-pacific': 'Asia-Pacific', 'africa': 'Africa', 'custom': 'all'}
NAMES = {'global':'Global Overview','middle-east':'Middle East','europe':'Europe','americas':'Americas','asia-pacific':'Asia-Pacific','africa':'Africa','custom':'Custom Workspace'}


def main():
    source = json.loads((DATA / 'live-feed.json').read_text(encoding='utf-8'))
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(days=7)
    result = {'generated': now.isoformat(), 'workspaces': {}}
    for key, region in WORKSPACES.items():
        candidates = []
        for record in source.get('records', []):
            if region != 'all' and region not in record.get('regions', [record.get('region', 'all')]):
                continue
            try:
                published = dt.datetime.fromisoformat(record['published'].replace('Z', '+00:00'))
                if published < cutoff:
                    continue
            except (ValueError, KeyError, TypeError):
                continue
            candidates.append(record)
        candidates = candidates[:12]
        if not candidates:
            continue
        topics = {}
        for record in candidates:
            category = record.get('category', 'Other')
            topics[category] = topics.get(category, 0) + 1
        intro = f"{NAMES[key]} weekly open-source briefing. Week ending {now:%d %B %Y}. This is an automated digest of published headlines, not an independently verified intelligence assessment. "
        overview = f"Reviewed {len(candidates)} recent source items. " + ', '.join(f'{v} {k.lower()} items' for k, v in topics.items()) + '. '
        details = 'Key reporting: ' + ' '.join(f"{i}. {r['title']}. Reported by {r['source']}." for i, r in enumerate(candidates[:8], 1))
        result['workspaces'][key] = {'generated': now.isoformat(), 'text': intro + overview + details + ' End of briefing.', 'items': [{'title': r['title'], 'url': r['url'], 'source': r['source']} for r in candidates]}
    (DATA / 'weekly-briefs.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (DATA / 'weekly-briefs.js').write_text('window.COREFORGE_BRIEFS=' + json.dumps(result, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
    print('Built', len(result['workspaces']), 'workspace briefings')

if __name__ == '__main__':
    main()
