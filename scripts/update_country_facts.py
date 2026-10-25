#!/usr/bin/env python3
"""Refresh CoreForge country facts; preserve last good values on partial outages.
REST Countries supplies geography; World Bank supplies dated population/GDP;
Wikidata supplies candidate current leadership and government descriptions.
"""
import datetime,json,pathlib,sys,time,urllib.request,urllib.parse
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'country-facts.json'
TODAY=datetime.datetime.now(datetime.timezone.utc).date().isoformat()
FIELDS='name,cca2,cca3,capital,population,currencies,languages,region,subregion,altSpellings,independent'
URL='https://restcountries.com/v3.1/all?fields='+FIELDS
WB='https://api.worldbank.org/v2/country/all/indicator/{indicator}?format=json&per_page=20000&mrnev=1'
WD='https://query.wikidata.org/sparql'
def get(url,accept='application/json',timeout=45):
 req=urllib.request.Request(url,headers={'User-Agent':'CoreForgeDashboard/1.3 (public country intelligence; contact via GitHub project)','Accept':accept})
 with urllib.request.urlopen(req,timeout=timeout) as r:return json.load(r)
def previous():
 try:return json.loads(OUT.read_text())
 except Exception:return {'countries':{}}
def merge(old,new):
 result=dict(old)
 for k,v in new.items():
  if v is not None and v!='' and v!=[]:result[k]=v
 return result
def wb_indicator(code):
 raw=get(WB.format(indicator=code));rows=raw[1] if isinstance(raw,list) and len(raw)>1 else []
 values={}
 for r in rows:
  iso=r.get('countryiso3code');value=r.get('value')
  if iso and value is not None and iso not in values:values[iso]={'value':value,'year':str(r.get('date',''))}
 return values
# Query in small batches; Wikidata may throttle or have missing/ambiguous records.
# Truthy P6/P35 statements are only accepted when the statement has no past end-date.
def wikidata_batch(codes):
 vals=' '.join('"'+c+'"' for c in codes)
 q="""SELECT ?code ?country ?countryLabel ?state ?stateLabel ?gov ?govLabel ?systemLabel WHERE {
 VALUES ?code { %s }
 ?country wdt:P297 ?code.
 OPTIONAL { ?country p:P35 ?ss. ?ss ps:P35 ?state. FILTER NOT EXISTS { ?ss pq:P582 ?ended. FILTER(?ended < NOW()) } }
 OPTIONAL { ?country p:P6 ?gs. ?gs ps:P6 ?gov. FILTER NOT EXISTS { ?gs pq:P582 ?ended2. FILTER(?ended2 < NOW()) } }
 OPTIONAL { ?country wdt:P122 ?system. }
 SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}"""%vals
 url=WD+'?'+urllib.parse.urlencode({'query':q,'format':'json'})
 data=get(url,'application/sparql-results+json',75)
 out={}
 for row in data.get('results',{}).get('bindings',[]):
  def v(key):return row.get(key,{}).get('value','')
  code=v('code'); rec=out.setdefault(code,{'headOfState':[],'headOfGovernment':[],'governmentTypes':[],'leadershipSource':'https://www.wikidata.org/wiki/'+v('country').split('/')[-1],'leadershipChecked':TODAY})
  for key,val in [('headOfState',v('stateLabel')),('headOfGovernment',v('govLabel')),('governmentTypes',v('systemLabel'))]:
   if val and val not in rec[key] and not val.startswith('Q'):rec[key].append(val)
 return {code:{'headOfState':', '.join(r['headOfState']) if len(r['headOfState'])==1 else '', 'headOfGovernment':', '.join(r['headOfGovernment']) if len(r['headOfGovernment'])==1 else '', 'governmentType':', '.join(r['governmentTypes'][:2]),'leadershipSource':r['leadershipSource'],'leadershipChecked':TODAY,'leadershipStatus':'Wikidata candidate; not independently verified'} for code,r in out.items()}
def main():
 old=previous();countries=dict(old.get('countries',{}));errors=[];success=[]
 try:
  raw=get(URL)
  if not isinstance(raw,list) or len(raw)<190:raise ValueError('Unexpected country count')
  bycode={v.get('code'):k for k,v in countries.items() if v.get('code')}
  for c in raw:
   name=c.get('name',{}).get('common','');code=c.get('cca2','');iso3=c.get('cca3','')
   if not name or not code:continue
   key=bycode.get(code,name.lower());prior=countries.get(key,{})
   fresh={'name':name,'code':code,'iso3':iso3,'capital':', '.join(c.get('capital') or []),'currency':', '.join((v.get('name','')+' ('+k+')') for k,v in (c.get('currencies') or {}).items()),'languages':', '.join((c.get('languages') or {}).values()),'region':' / '.join(filter(None,[c.get('region'),c.get('subregion')])), 'aliases':c.get('altSpellings',[])[:8], 'geographySource':'https://restcountries.com/v3.1/alpha/'+code,'geographyUpdated':TODAY}
   # REST Countries population is only a fallback; no dated year is supplied.
   if not prior.get('populationYear'):fresh.update(population=c.get('population'),populationNote='REST Countries estimate; reference year unspecified')
   countries[key]=merge(prior,fresh)
  success.append('REST Countries')
 except Exception as e:errors.append('REST Countries: '+str(e))
 for indicator,field in [('SP.POP.TOTL','population'),('NY.GDP.MKTP.CD','gdpUsd')]:
  try:
   data=wb_indicator(indicator);count=0
   for record in countries.values():
    item=data.get(record.get('iso3',''))
    if item:
     record[field]=item['value'];record[field+'Year']=item['year'];record[field+'Source']='https://data.worldbank.org/indicator/'+indicator+'?locations='+record.get('code','');count+=1
   if count<100:raise ValueError('Only '+str(count)+' country matches')
   success.append('World Bank '+indicator+' ('+str(count)+')')
  except Exception as e:errors.append('World Bank '+indicator+': '+str(e))
 codes=sorted({r.get('code') for r in countries.values() if r.get('code') and len(r.get('code'))==2})
 wd={};worked=0
 for i in range(0,len(codes),25):
  try:wd.update(wikidata_batch(codes[i:i+25]));worked+=1
  except Exception as e:errors.append('Wikidata batch '+str(i//25+1)+': '+str(e)[:180])
  time.sleep(1)
 for record in countries.values():
  candidate=wd.get(record.get('code'))
  if candidate:
   # Never overwrite previously known leaders with an empty response.
   record.update(merge({k:record.get(k) for k in candidate},candidate))
 if worked:success.append('Wikidata leadership ('+str(len(wd))+' country matches)')
 if not success:
  print('All providers failed; retaining last valid snapshot',file=sys.stderr)
  for err in errors:print(err,file=sys.stderr)
  return 1
 payload={'source':'REST Countries / World Bank / Wikidata; BBC links are references, not scraped content','updated':TODAY,'sourcesSucceeded':success,'sourceErrors':errors,'countries':countries}
 OUT.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n')
 print('Country refresh:',len(countries),'records; successes:',success,'errors:',errors)
 return 0
if __name__=='__main__':sys.exit(main())
