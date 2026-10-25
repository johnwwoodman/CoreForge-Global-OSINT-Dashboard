#!/usr/bin/env python3
"""Detect changes between committed and newly generated country snapshots.
A change is an unverified collection signal, not a confirmed office transition.
"""
import datetime as dt
import json
import pathlib
import subprocess

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'data/leadership-changes.json'
CURRENT=ROOT/'data/country-facts.json'

def country_by_code(data):
    return {v['code']:v for v in data.get('countries',{}).values() if isinstance(v,dict) and v.get('code')}

def main():
    now=json.loads(CURRENT.read_text(encoding='utf-8'))
    try:
        before=subprocess.check_output(['git','show','HEAD:data/country-facts.json'],cwd=ROOT,stderr=subprocess.DEVNULL)
        old=json.loads(before)
    except (subprocess.CalledProcessError,FileNotFoundError,ValueError):
        old={'countries':{}}
    previous=country_by_code(old)
    changes=[]
    today=dt.datetime.now(dt.timezone.utc).date().isoformat()
    for code,country in country_by_code(now).items():
        prior=previous.get(code)
        if not prior:continue
        for field in ('headOfState','headOfGovernment'):
            a=str(prior.get(field) or '').strip();b=str(country.get(field) or '').strip()
            if a and b and a!=b:
                changes.append({'code':code,'country':country.get('name',code),'field':field,'previous':a,'current':b,'detected':today,'verification':'Unverified source-data change'})
    try:
        existing=json.loads(OUT.read_text(encoding='utf-8')).get('changes',[])
    except (FileNotFoundError,ValueError):existing=[]
    unique={}
    for row in existing+changes:
        key=(row.get('code'),row.get('field'),row.get('previous'),row.get('current'))
        unique[key]=row
    result={'updated':today,'description':'Changes in collected candidate data; not independently confirmed political transitions.','changes':sorted(unique.values(),key=lambda x:x.get('detected',''),reverse=True)[:200]}
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Leadership change signals:',len(changes))

if __name__=='__main__':main()
