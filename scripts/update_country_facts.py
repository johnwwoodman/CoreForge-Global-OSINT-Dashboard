#!/usr/bin/env python3
"""Incremental country refresh. Provider failures never erase valid cached data."""
import datetime, json, pathlib, sys, urllib.request, urllib.parse, urllib.error, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'data/country-facts.json'
TODAY=datetime.datetime.now(datetime.timezone.utc).date().isoformat()
FIELDS='name,cca2,cca3,capital,population,currencies,languages,region,subregion,altSpellings'
REST_URLS=['https://restcountries.com/v3.1/all?fields='+FIELDS,'https://restcountries.com/v3.1/all']
WB='https://api.worldbank.org/v2/country/all/indicator/{code}?format=json&per_page=20000'
WD='https://query.wikidata.org/sparql'
HEADERS={'User-Agent':'CoreForge-Global-OSINT-Dashboard/1.3.1 (public research; GitHub project johnwwoodman/CoreForge-Global-OSINT-Dashboard)','Accept':'application/json'}
def get(url,accept=None,timeout=40):
 headers=dict(HEADERS)
 if accept:headers['Accept']=accept
 req=urllib.request.Request(url,headers=headers)
 with urllib.request.urlopen(req,timeout=timeout) as resp:return json.load(resp)
def valid_country(row):
 return isinstance(row,dict) and isinstance(row.get('name'),dict) and bool(row.get('cca2')) and bool(row['name'].get('common'))
def rest_countries():
 errors=[]
 for url in REST_URLS:
  try:
   result=get(url)
   if not isinstance(result,list):raise ValueError('Expected a list, received '+type(result).__name__)
   rows=[r for r in result if valid_country(r)]
   if len(rows)<50:raise ValueError('Only '+str(len(rows))+' valid records')
   return rows
  except Exception as e:errors.append(str(e)[:160])
 raise RuntimeError('; '.join(errors))
def wb_indicator(code):
 raw=get(WB.format(code=code))
 if not isinstance(raw,list) or len(raw)<2 or not isinstance(raw[1],list):raise ValueError('Unexpected World Bank response')
 result={}
 for row in raw[1]:
  if not isinstance(row,dict):continue
  iso=(row.get('countryiso3code') or '').upper();val=row.get('value')
  if len(iso)!=3 or val is None:continue
  year=str(row.get('date') or '')
  if iso not in result or year>result[iso]['year']:result[iso]={'value':val,'year':year}
 return result
def iso3_lookup():
 try:
  import pycountry
  return {x.alpha_2:x.alpha_3 for x in pycountry.countries}
 except ImportError:return {}
def merge(existing,patch):
 for k,v in patch.items():
  if v is not None and v!='' and v!=[]:existing[k]=v
 return existing
# Prioritise frequently consulted regions and countries with missing leadership.
# The remainder rotates daily, keeping one Wikidata request per run.
PRIORITY_CODES=('SY','GB','FJ','JO','IL','PS','LB','IQ','IR','SA','AE','QA','KW','BH','OM','YE','EG','TR','US','RU','CN','IN','UA')
def choose_wikidata_batch(countries, today, size=15):
 """Prioritise incomplete high-interest profiles while rotating worldwide coverage."""
 codes=sorted({r.get('code') for r in countries.values() if len(r.get('code') or '')==2})
 by_code={r.get('code'):r for r in countries.values() if r.get('code')}
 priority=[c for c in PRIORITY_CODES if c in codes]
 day=datetime.date.fromisoformat(today).toordinal()
 # Six rotating priority slots, nine worldwide slots; revisit missing records first.
 missing=sorted(priority,key=lambda c:(bool(by_code[c].get('headOfState') or by_code[c].get('headOfGovernment')),c))
 pstart=(day*6)%len(missing) if missing else 0
 selected=(missing[pstart:]+missing[:pstart])[:min(6,size)]
 remaining=[c for c in codes if c not in selected]
 start=(day*(size-len(selected)))%len(remaining) if remaining else 0
 return selected+(remaining[start:]+remaining[:start])[:size-len(selected)]

def wikidata_once(codes):
 # Only one request per run. Respect 429 and never retry immediately.
 values=' '.join('"'+c+'"' for c in codes)
 query="""SELECT ?code ?country ?stateLabel ?govLabel ?systemLabel WHERE {
 VALUES ?code { %s }
 ?country wdt:P297 ?code.
 OPTIONAL { ?country p:P35 ?s. ?s ps:P35 ?state. FILTER NOT EXISTS { ?s pq:P582 ?end. FILTER(?end <= NOW()) } FILTER NOT EXISTS { ?s pq:P580 ?start. FILTER(?start > NOW()) } }
 OPTIONAL { ?country p:P6 ?g. ?g ps:P6 ?gov. FILTER NOT EXISTS { ?g pq:P582 ?end2. FILTER(?end2 <= NOW()) } FILTER NOT EXISTS { ?g pq:P580 ?start2. FILTER(?start2 > NOW()) } }
 OPTIONAL { ?country wdt:P122 ?system. }
 SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}"""%values
 url=WD+'?'+urllib.parse.urlencode({'query':query,'format':'json'})
 data=get(url,'application/sparql-results+json',timeout=65)
 collected={}
 for row in data.get('results',{}).get('bindings',[]):
  def value(key):return row.get(key,{}).get('value','')
  code=value('code');
  if not code:continue
  rec=collected.setdefault(code,{'headOfState':set(),'headOfGovernment':set(),'governmentType':set(),'source':value('country')})
  for key,field in [('headOfState','stateLabel'),('headOfGovernment','govLabel'),('governmentType','systemLabel')]:
   v=value(field)
   if v and not v.startswith('Q'):rec[key].add(v)
 result={}
 for code,rec in collected.items():
  patch={}
  for field in ('headOfState','headOfGovernment','governmentType'):
   if len(rec[field])==1:patch[field]=next(iter(rec[field]))
  if any(k in patch for k in ('headOfState','headOfGovernment')):
   patch.update(leadershipChecked=TODAY,leadershipStatus='Wikidata candidate; not independently verified',leadershipSource=rec['source'])
  if patch:result[code]=patch
 return result
def main():
 try:old=json.loads(OUT.read_text(encoding='utf-8'))
 except Exception:old={'countries':{}}
 countries=dict(old.get('countries',{})); errors=[]; success=[]; mapping=iso3_lookup()
 bycode={v.get('code'):k for k,v in countries.items() if v.get('code')}
 for record in countries.values():
  code=record.get('code','')
  if not record.get('iso3') and code in mapping:record['iso3']=mapping[code]
 try:
  rows=rest_countries();changed=0
  for row in rows:
   code=row['cca2'];key=bycode.get(code,row['name']['common'].lower());prior=dict(countries.get(key,{}))
   patch={'name':row['name']['common'],'code':code,'iso3':row.get('cca3') or mapping.get(code),'capital':', '.join(row.get('capital') or []),'currency':', '.join((x.get('name','')+' ('+k+')') for k,x in (row.get('currencies') or {}).items()),'languages':', '.join((row.get('languages') or {}).values()),'region':' / '.join(filter(None,[row.get('region'),row.get('subregion')])), 'aliases':row.get('altSpellings',[])[:8], 'geographySource':'https://restcountries.com/v3.1/alpha/'+code,'geographyUpdated':TODAY}
   if not prior.get('populationYear') and row.get('population') is not None:patch.update(population=row['population'],populationNote='REST Countries estimate; year unspecified')
   countries[key]=merge(prior,patch);changed+=1
  success.append('REST Countries ('+str(changed)+')')
 except Exception as e:errors.append('REST Countries: '+str(e)[:220])
 for indicator,field in [('SP.POP.TOTL','population'),('NY.GDP.MKTP.CD','gdpUsd')]:
  try:
   values=wb_indicator(indicator);count=0
   for rec in countries.values():
    iso=rec.get('iso3') or mapping.get(rec.get('code',''))
    if not iso:continue
    rec['iso3']=iso
    item=values.get(iso)
    if not item:continue
    rec[field]=item['value'];rec[field+'Year']=item['year'];rec[field+'Source']='https://data.worldbank.org/indicator/'+indicator+'?locations='+rec.get('code','');count+=1
   if not count:raise ValueError('No matching ISO3 codes in '+str(len(values))+' World Bank records')
   success.append('World Bank '+indicator+' ('+str(count)+')')
  except Exception as e:errors.append('World Bank '+indicator+': '+str(e)[:220])
 # One query per day, prioritising high-interest countries while rotating globally.
 batch=choose_wikidata_batch(countries,TODAY)
 if batch:
  try:
   result=wikidata_once(batch)
   for rec in countries.values():
    patch=result.get(rec.get('code'))
    if patch:merge(rec,patch)
   success.append('Wikidata ('+str(len(result))+' candidates; '+','.join(batch)+')')
  except urllib.error.HTTPError as e:
   errors.append('Wikidata: HTTP '+str(e.code)+'; skipped further requests (rate limit/outage)')
  except Exception as e:errors.append('Wikidata: '+str(e)[:220])
 if not success:
  print('All providers failed; retaining last valid snapshot',file=sys.stderr)
  for err in errors:print(err,file=sys.stderr)
  return 1
 payload=dict(old);payload.update(source='REST Countries / World Bank / Wikidata; BBC reference links only',updated=TODAY,sourcesSucceeded=success,sourceErrors=errors,countries=countries)
 OUT.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
 print('Country refresh:',len(countries),'records; successes:',success)
 for err in errors:print('Provider warning:',err)
 return 0
if __name__=='__main__':sys.exit(main())
