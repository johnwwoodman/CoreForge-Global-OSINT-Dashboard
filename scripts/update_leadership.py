#!/usr/bin/env python3
"""Incremental worldwide leadership enrichment via country Wikidata claims.
Uses batched Wikipedia pageprops -> Wikidata entity IDs, not SPARQL.
Candidates are NOT independent verification. Provider errors never erase cached data.
"""
import datetime, json, pathlib, time, urllib.error, urllib.parse, urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
PATH=ROOT/'data/country-facts.json'
TODAY=datetime.datetime.now(datetime.timezone.utc).date().isoformat()
UA='CoreForgeGlobalOSINT/1.4 (https://github.com/johnwwoodman/CoreForge-Global-OSINT-Dashboard; public research)'
HEADERS={'User-Agent':UA,'Accept':'application/json','Accept-Encoding':'gzip, deflate'}
API='https://en.wikipedia.org/w/api.php'
WD='https://www.wikidata.org/w/api.php'
PRIORITY=('SY','GB','US','FJ','IL','PS','JO','LB','IQ','IR','SA','AE','QA','KW','BH','OM','YE','EG','TR','UA','RU','CN','IN')

def fetch(base,params):
 url=base+'?'+urllib.parse.urlencode(params)
 req=urllib.request.Request(url,headers=HEADERS)
 with urllib.request.urlopen(req,timeout=45) as r:
  raw=r.read()
  if r.headers.get('Content-Encoding')=='gzip':
   import gzip
   raw=gzip.decompress(raw)
  return json.loads(raw)

def chunks(items,n):
 for i in range(0,len(items),n):yield items[i:i+n]

def claims(entity,prop):
 result=[]
 for claim in entity.get('claims',{}).get(prop,[]):
  if claim.get('rank')=='deprecated':continue
  mainsnak=claim.get('mainsnak',{})
  value=mainsnak.get('datavalue',{}).get('value',{})
  if not isinstance(value,dict) or not value.get('id'):continue
  qualifiers=claim.get('qualifiers',{})
  def date(p):
   try:return qualifiers[p][0]['datavalue']['value']['time'][1:11]
   except (KeyError,IndexError,TypeError):return None
  start,end=date('P580'),date('P582')
  if start and start>TODAY:continue
  if end and end<=TODAY:continue
  result.append((value['id'],claim.get('rank','normal'),start,end))
 return result

def pick(entity,prop):
 found=claims(entity,prop)
 if not found:return None
 # Multiple unended historic entries must not be guessed from rank alone.
 preferred=[r for r in found if r[1]=='preferred']
 chosen=preferred if len(preferred)==1 else found
 if len(chosen)!=1:return None
 return chosen[0][0]

def select(records,limit=42):
 all_codes=sorted(c for c in records if len(c)==2)
 day=datetime.date.fromisoformat(TODAY).toordinal()
 # Priority countries are always checked, remainder rotates deterministically.
 first=[c for c in PRIORITY if c in records]
 rest=[c for c in all_codes if c not in first]
 count=max(0,limit-len(first))
 start=(day*count)%len(rest) if rest and count else 0
 return first+(rest[start:]+rest[:start])[:count]

def main():
 data=json.loads(PATH.read_text(encoding='utf-8'))
 records={v.get('code'):v for v in data.get('countries',{}).values() if v.get('code')}
 codes=select(records)
 titles={code:rec.get('name','') for code,rec in records.items() if code in codes}
 # Wikipedia redirects resolve common country names and expose Wikidata IDs.
 ids={};errors=[]; updated=0
 try:
  for batch in chunks(list(titles.items()),25):
   res=fetch(API,{'action':'query','format':'json','redirects':'1','prop':'pageprops','ppprop':'wikibase_item','titles':'|'.join(name for _,name in batch)})
   redirects={r['from']:r['to'] for r in res.get('query',{}).get('redirects',[])}
   pages={p.get('title'):p.get('pageprops',{}).get('wikibase_item') for p in res.get('query',{}).get('pages',{}).values()}
   for code,name in batch:
    qid=pages.get(redirects.get(name,name))
    if qid:ids[code]=qid
 except Exception as e:errors.append('Wikipedia mapping: '+str(e)[:130])
 if ids:
  try:
   entity_map={}
   for batch in chunks(list(set(ids.values())),40):
    response=fetch(WD,{'action':'wbgetentities','format':'json','ids':'|'.join(batch),'props':'claims|labels','languages':'en','maxlag':'5'})
    entity_map.update(response.get('entities',{}))
    time.sleep(1.5)
   leaders=set()
   for qid in ids.values():
    entity=entity_map.get(qid,{})
    for p in ('P35','P6'):
     lid=pick(entity,p)
     if lid:leaders.add(lid)
   labels={}
   for batch in chunks(sorted(leaders),40):
    res=fetch(WD,{'action':'wbgetentities','format':'json','ids':'|'.join(batch),'props':'labels','languages':'en','maxlag':'5'})
    for lid,item in res.get('entities',{}).items():
     label=item.get('labels',{}).get('en',{}).get('value')
     if label:labels[lid]=label
    time.sleep(1.5)
   for code,qid in ids.items():
    rec=records[code];entity=entity_map.get(qid,{})
    patch={}
    for prop,key in [('P35','headOfState'),('P6','headOfGovernment')]:
     lid=pick(entity,prop)
     if lid in labels:patch[key]=labels[lid]
    # Do not overwrite a populated name with missing/ambiguous claims.
    if patch:
     rec.update(patch)
     rec.update(leadershipChecked=TODAY,leadershipStatus='Wikidata candidate; not independently verified',leadershipSource='https://www.wikidata.org/wiki/'+qid)
     updated+=1
    else:rec['leadershipAttempted']=TODAY
  except urllib.error.HTTPError as e:errors.append('Wikidata entity API HTTP '+str(e.code)+'; cached names retained')
  except Exception as e:errors.append('Wikidata entity API: '+str(e)[:140])
 data.setdefault('sourcesSucceeded',[]).append('Leadership entity refresh ('+str(updated)+' countries)') if updated else None
 data.setdefault('sourceErrors',[]).extend(errors)
 data['leadershipRun']=TODAY
 data['leadershipCoverage']={'countriesWithAnyLeader':sum(bool(r.get('headOfState') or r.get('headOfGovernment')) for r in records.values()),'countriesTotal':len(records),'countriesCheckedThisRun':len(ids),'countriesUpdatedThisRun':updated}
 PATH.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
 print('Leadership:',data['leadershipCoverage'],'errors:',errors)
 return 0
if __name__=='__main__':raise SystemExit(main())
