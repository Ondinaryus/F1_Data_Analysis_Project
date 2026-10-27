"""Pinned input loading, validated result enrichment and contract CSV writing."""
import hashlib
import io
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

SOURCE_REF = '7e0fc6dbecba19e0a95f9f85c1cbd493821f3788'
FILES = dict(results='Race_Results', races='Race_Schedule', drivers='Driver_Details', constructors='Team_Details', circuits='Track_Information', status='Race_Status', constructor_results='Constructor_Performance', constructor_standings='Constructor_Rankings', driver_standings='Driver_Rankings', laps='Lap_Timings', pits='Pit_Stop_Records', qualifying='Qualifying_Results', sprints='Sprint_Race_Results', seasons='Season_Summaries')
NUMERIC = set('resultId raceId driverId constructorId circuitId statusId constructorResultsId constructorStandingsId driverStandingsId qualifyId year round number grid positionOrder points laps milliseconds rank lat lng alt lap stop wins'.split())
INCIDENT = {3,4,20,104,130,68,73,82,100,107,139}
VEHICLE = {5,6,7,8,9,10,21,22,23,24,25,26,27,28,29,30,32,33,34,36,37,38,39,40,41,42,43,44,46,47,48,49,51,56,59,61,63,65,67,69,70,72,75,79,80,83,84,86,87,91,93,94,95,98,99,101,102,103,105,106,108,109,110,121,126,129,131,132,135,136,140,141}
EXTRAS = {'v_grid_start_facts':['car_key'], 'v_dnf_by_circuit_year_reason':['dnf_other','nonstart_count']}


def load_tables(repo: Path, ref: str = SOURCE_REF) -> dict:
    tables = {}
    metadata = {}
    for key, name in FILES.items():
        path = f'data/raw/{name}.csv'
        raw = subprocess.run(['git','-C',str(repo),'show',f'{ref}:{path}'],check=True,capture_output=True).stdout
        df = pd.read_csv(io.BytesIO(raw), dtype=str, keep_default_na=False, na_values=['\\N',''])
        for col in NUMERIC.intersection(df.columns):
            df[col] = pd.to_numeric(df[col], errors='raise')
        # position is textual in race results but numeric in standings and qualifying
        if key in ('driver_standings','constructor_standings','qualifying','laps'):
            df['position'] = pd.to_numeric(df['position'], errors='raise')
        tables[key] = df
        metadata[path] = {'sha256':hashlib.sha256(raw).hexdigest(),'rows':len(df)}
    tables['_source_manifest'] = {'source_commit':subprocess.run(['git','-C',str(repo),'rev-parse',ref],check=True,capture_output=True,text=True).stdout.strip(),'source_repository':'gunay-ozsoy/F1_Data_Analysis_Project','sources':metadata}
    return tables


def checked_join(left, right, key, columns=None):
    if right[key].isna().any() or right.duplicated(key).any():
        raise ValueError(f'Invalid or duplicate dimension key: {key}')
    if left[key].isna().any():
        raise ValueError(f'Missing key: {key}')
    r = right if columns is None else right[[key] + columns]
    merged = left.merge(r, on=key, how='left', validate='many_to_one', indicator=True, sort=False)
    if (merged['_merge'] != 'both').any():
        raise ValueError(f'Missing dimension reference: {key}')
    return merged.drop(columns='_merge')


def enrich_entries(entries: pd.DataFrame, tables: dict) -> pd.DataFrame:
    f = entries.copy()
    if 'results' in tables:
        for column in tables['results'].columns.difference(f.columns):
            f[column] = pd.NA
    if f['resultId'].isna().any() or f['resultId'].duplicated().any():
        raise ValueError('Invalid or duplicate resultId')
    races = tables['races'].rename(columns={'name':'race_name','time':'race_time','url':'race_url'})
    f=checked_join(f,races,'raceId',['year','round','circuitId','date','race_time','race_name','race_url'])
    d=tables['drivers'].copy(); d['driver_name']=d['forename'].fillna('')+' '+d['surname'].fillna('')
    d=d.rename(columns={'code':'driver_code','nationality':'driver_nationality'})
    f=checked_join(f,d,'driverId',['driverRef','driver_name','driver_code','driver_nationality'])
    c=tables['constructors'].rename(columns={'name':'team_name','nationality':'team_nationality'})
    f=checked_join(f,c,'constructorId',['constructorRef','team_name','team_nationality'])
    c=tables['circuits'].rename(columns={'name':'circuit_name','url':'circuit_url'})
    f=checked_join(f,c,'circuitId',['circuitRef','circuit_name','circuit_url','country','location','lat','lng','alt'])
    f=checked_join(f,tables['status'],'statusId',['status'])
    f['year_circuit']=f['year'].astype(int).astype(str)+' | '+f['race_name']+' | '+f['raceId'].astype(int).astype(str)
    number=f['number'].map(lambda x: str(int(x)) if pd.notna(x) else None)
    f['car_key']=f['raceId'].astype(int).astype(str)+' | '+f['constructorId'].astype(int).astype(str)+' | '+number.fillna('driver:'+f['driverId'].astype(int).astype(str))
    finish=(f.statusId.eq(1) | f.status.str.fullmatch(r'\+\d+ Laps?',na=False))
    nonstart=f.statusId.isin([77,81,97]) | (f.statusId.eq(54) & f.laps.eq(0))
    dq=f.statusId.isin([2,92,96]); incident=f.statusId.isin(INCIDENT); vehicle=f.statusId.isin(VEHICLE)
    f['outcome_group']=np.select([finish,nonstart,dq,incident,vehicle],['finish','nonstart','disqualified','incident','vehicle'],default='other')
    for col, groups in {'is_finish':['finish'],'is_nonstart':['nonstart'],'is_disqualified':['disqualified'],'is_dnf':['incident','vehicle','other'],'is_incident':['incident'],'is_vehicle':['vehicle'],'is_other_dnf':['other']}.items(): f[col]=f.outcome_group.isin(groups).astype(int)
    f['win_flag']=f.positionOrder.eq(1).astype(int)
    return f


def build_facts(tables):
    return enrich_entries(tables['results'],tables)


def find_anomalies(facts: pd.DataFrame) -> list:
    """Report positive-lap DNQ without changing its nonstart classification."""
    rows = facts.loc[facts.statusId.eq(81) & facts.laps.gt(0), ['resultId','raceId','driverId','statusId','laps']]
    return [{k: int(v) for k, v in row.items()} for row in rows.to_dict('records')]


def write_sources(outputs: dict, out_dir: Path, schema_path: Path) -> dict:
    out_dir=Path(out_dir); out_dir.mkdir(parents=True,exist_ok=True)
    schemas={s['source']:s for s in json.loads(Path(schema_path).read_text(encoding='utf8'))}
    manifest={}
    for name, df in outputs.items():
        if name not in schemas: raise ValueError(f'Unknown source: {name}')
        fields=[f['name'] for f in schemas[name]['fields'] if f['kind']=='physical' and f['name']!='Record Count']+EXTRAS.get(name,[])
        if len(fields)!=len(set(fields)) or any(not re.fullmatch(r'[A-Za-z0-9_]+',x) for x in fields): raise ValueError(f'Invalid fields: {name}')
        missing=set(fields)-set(df.columns)
        if missing: raise ValueError(f'{name} missing fields {sorted(missing)}')
        keys={'stg_race_result':['resultId'], 'stg_constructor_rankings':['constructorId','year_circuit'], 'stg_constructor_performance':['constructorResultsId'], 'stg_driver_rankings':['driverStandingsId'], 'stg_race_schedule':['raceid'], 'team_details':['constructorid'], 'track_information':['circuitid'], 'v_dnf_by_circuit_year_reason':['raceId']}
        key=keys.get(name)
        if key and (df[key].isna().any().any() or df.duplicated(key).any()): raise ValueError(f'Invalid grain: {name}')
        selected=df[fields].copy()
        for f in schemas[name]['fields']:
            if f['name'] in fields and f['type']=='type_numeric':
                v=pd.to_numeric(selected[f['name']],errors='raise')
                if not np.isfinite(v.dropna()).all(): raise ValueError(f'Nonfinite {name}.{f["name"]}')
        for field in ('dnf_other','nonstart_count'):
            if field in EXTRAS.get(name, []):
                v=pd.to_numeric(selected[field],errors='raise')
                if not np.isfinite(v.dropna()).all(): raise ValueError(f'Nonfinite {name}.{field}')
        if selected.astype('string').apply(lambda c: c.str.contains(r'[\r\n]',na=False)).any().any(): raise ValueError(f'Embedded newline in {name}')
        path=out_dir/f'{name}.csv'; selected.to_csv(path,index=False,encoding='utf8',lineterminator='\n',na_rep='')
        raw=path.read_bytes()
        if len(raw)>=100000000: raise ValueError(f'Output too large: {name}')
        manifest[name]={'rows':len(df),'fields':fields,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    (out_dir/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    return manifest
