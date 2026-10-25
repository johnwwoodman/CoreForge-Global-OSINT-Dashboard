#!/usr/bin/env python3
"""Fetch historical annual World Bank data for population and GDP in two bulk requests."""
import datetime as dt
import json
import pathlib
import urllib.request

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'data/country-history.json'
INDICATORS={'population':'SP.POP.TOTL','gdpUsd':'NY.GDP.MKTP.CD'}

def main():
    try:old=json.loads(OUT.read_text(encoding='utf-8'))
    except (OSError,ValueError):old={'countries':{}}
    data=old.get('countries',{})
    success=[];errors=[]
    for name,indicator in INDICATORS.items():
        url=f'https://api.worldbank.org/v2/country/all/indicator/{indicator}?format=json&per_page=30000&date=2000:2026'
        try:
            request=urllib.request.Request(url,headers={'User-Agent':'CoreForge-OSINT/1.9 (public country research)','Accept':'application/json'})
            with urllib.request.urlopen(request,timeout=45) as response:rows=json.load(response)
            if not isinstance(rows,list) or len(rows)<2 or not isinstance(rows[1],list):raise ValueError('Unexpected response')
            count=0
            for row in rows[1]:
                code=row.get('countryiso3code') or ''
                if len(code)!=3 or row.get('value') is None:continue
                year=str(row.get('date') or '')
                if not (year.isdigit() and 2000<=int(year)<=2026):continue
                data.setdefault(code,{}).setdefault(name,{})[year]=row['value'];count+=1
            success.append(f'{name}: {count} observations')
        except Exception as exc:errors.append(f'{name}: {str(exc)[:160]}')
    OUT.write_text(json.dumps({'updated':dt.datetime.now(dt.timezone.utc).date().isoformat(),'countries':data,'sources':INDICATORS,'success':success,'errors':errors},separators=(',',':'))+'\n',encoding='utf-8')
    print('World Bank history:',success,'errors:',errors)

if __name__=='__main__':main()
