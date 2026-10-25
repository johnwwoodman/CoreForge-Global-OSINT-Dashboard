#!/usr/bin/env python3
"""Refresh local country reference data. Run from repository root. No browser API dependency."""
import json, pathlib, urllib.request, datetime, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
FIELDS='name,cca2,cca3,capital,population,currencies,languages,region,subregion,altSpellings'
URL='https://restcountries.com/v3.1/all?fields='+FIELDS
req=urllib.request.Request(URL,headers={'User-Agent':'CoreForge-CountryReference/1.2 (public reference refresh)','Accept':'application/json'})
try:
 with urllib.request.urlopen(req,timeout=25) as r: raw=json.load(r)
 if not isinstance(raw,list) or len(raw)<190:raise ValueError('Unexpected response size')
 countries={}
 for c in raw:
  name=c.get('name',{}).get('common','')
  if not name:continue
  countries[name.lower()]={'name':name,'code':c.get('cca2',''),'capital':', '.join(c.get('capital') or []),'population':c.get('population'),'populationNote':'Source estimate; publication year not specified','currency':', '.join((v.get('name','')+' ('+k+')') for k,v in (c.get('currencies') or {}).items()),'languages':', '.join((c.get('languages') or {}).values()),'region':' / '.join(filter(None,[c.get('region'),c.get('subregion')])), 'aliases':c.get('altSpellings',[])[:8]}
 out=ROOT/'data'/'country-facts.json';out.write_text(json.dumps({'source':'REST Countries v3.1','updated':datetime.date.today().isoformat(),'countries':countries},ensure_ascii=False,separators=(',',':'))+'\n')
 print('Updated',len(countries),'country references')
except Exception as e:
 print('Country reference refresh failed; retaining last snapshot:',e,file=sys.stderr)
 sys.exit(1)
