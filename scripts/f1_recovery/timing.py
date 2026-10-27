"""Reconstructed timing and circuit sources; see docs/recovery/TIMING_METRICS.md."""
import json
import numpy as np
import pandas as pd
from .common import enrich_entries


def load_circuit_types(path, circuits):
    records=json.loads(path.read_text(encoding='utf8'))
    ids=[r['circuitId'] for r in records]
    expected=dict(zip(circuits.circuitId,circuits.circuitRef))
    if len(ids)!=len(set(ids)) or set(ids)!=set(expected): raise ValueError('Circuit lookup IDs do not match snapshot')
    allowed={'Race circuit','Road circuit','Street circuit','Unknown'}
    for row in records:
        if row['circuitRef']!=expected[row['circuitId']] or row['type'] not in allowed or not row.get('source_url') or not row.get('note'):
            raise ValueError('Invalid circuit lookup reference or provenance')
    return {row['circuitId']:row['type'] for row in records}


def pit_metrics(pits, facts):
    key=['raceId','driverId']
    attrs=key+['constructorId','constructorRef','driverRef','race_name','year_circuit']
    refs=facts[attrs].drop_duplicates().merge(pits[key].drop_duplicates(),on=key,how='inner',validate='many_to_one')
    if refs.duplicated(key).any():
        raise ValueError('Ambiguous pit driver-race constructor')
    p=pits.merge(refs,on=key,how='left',validate='many_to_one',indicator=True)
    if p['_merge'].ne('both').any(): raise ValueError('Pit stop without result entry')
    p['seconds']=pd.to_numeric(p.milliseconds,errors='raise')/1000
    g=p.groupby(attrs,dropna=False,sort=False).seconds
    out=g.agg(avg_pit_s='mean',median_pit_s='median',fastest_pit_s='min',pit_count='size').reset_index()
    out['sd_pit_s']=g.std(ddof=0).to_numpy()
    out['iqr_pit_s']=(g.quantile(.75)-g.quantile(.25)).to_numpy()
    return out


def lap_metrics(laps,races,drivers):
    key=['raceId','driverId','lap']
    if laps[key].isna().any().any() or laps.duplicated(key).any(): raise ValueError('Invalid lap grain')
    l=laps.merge(races[['raceId','name','year','date','time']].rename(columns={'time':'race_time'}),on='raceId',validate='many_to_one',how='left',indicator=True)
    if l['_merge'].ne('both').any(): raise ValueError('Lap race missing')
    l=l.drop(columns='_merge').merge(drivers[['driverId','driverRef']],on='driverId',validate='many_to_one',how='left',indicator=True)
    if l['_merge'].ne('both').any(): raise ValueError('Lap driver missing')
    l=l.sort_values(key).copy()
    ms=pd.to_numeric(l.milliseconds,errors='raise')
    l['lap_time_seconds']=ms/1000
    l['lap_time_formatted']=ms.map(lambda x: f'{int(x)//60000}:{(int(x)%60000)//1000:02d}.{int(x)%1000:03d}' if pd.notna(x) else None)
    starts=pd.to_datetime(l.date.astype('string')+' '+l.race_time.astype('string'),format='%Y-%m-%d %H:%M:%S',errors='raise')
    cumulative=ms.groupby([l.raceId,l.driverId]).cumsum(skipna=False)
    ts=starts+pd.to_timedelta(cumulative,unit='ms')
    l['race_start_ts']=starts.dt.strftime('%Y-%m-%d %H:%M:%S')
    l['lap_timestamp']=ts.dt.strftime('%Y-%m-%d %H:%M:%S.%f').str.slice(stop=-3)
    return l.rename(columns={'raceId':'raceid','driverId':'driverid','driverRef':'driverref','name':'race_name'})


def dynamics(facts):
    records=[]
    for race_id,g in facts.groupby('raceId',sort=True):
        eligible=g[g.is_nonstart.eq(0)]
        classified=eligible[eligible.is_finish.eq(1) & pd.to_numeric(eligible.position,errors='coerce').notna()]
        grid=pd.to_numeric(eligible.grid,errors='coerce'); positive=grid[grid.gt(0)]
        field=max(2,len(eligible),positive.max() if len(positive) else 0)
        valid=classified[pd.to_numeric(classified.grid,errors='coerce').gt(0)]
        moves=(pd.to_numeric(valid.grid)-pd.to_numeric(valid.position)).abs()
        chaos=moves.mean()/(field-1) if len(moves) else np.nan
        dnf=eligible.is_dnf.sum()/len(eligible) if len(eligible) else np.nan
        winners=classified[classified.positionOrder.eq(1)]
        winner_grid=pd.to_numeric(winners.grid,errors='coerce'); winner_grid=winner_grid[winner_grid.gt(0)]
        surprise=(winner_grid.iloc[0]-1)/(field-1) if len(winner_grid) else np.nan
        density=classified.statusId.eq(1).sum()/len(classified) if len(classified) else np.nan
        components=pd.Series([chaos,dnf,surprise,density],dtype=float).clip(0,1)
        first=g.iloc[0]
        records.append(dict(raceId=race_id,year_circuit=first.year_circuit,season_start_date=f'{int(first.year):04d}-01-01',norm_chaos=components.iloc[0],norm_dnf=components.iloc[1],norm_surprise=components.iloc[2],norm_density=components.iloc[3],excitement_score=components.mean()))
    return pd.DataFrame(records)


def circuit_metrics(circuits,facts,circuit_types):
    f=facts.copy(); f['speed']=pd.to_numeric(f.fastestLapSpeed,errors='coerce'); f.loc[~np.isfinite(f.speed) | f.speed.le(0),'speed']=np.nan
    speed=f.groupby('circuitId').speed.mean()
    eligible=f[f.is_nonstart.eq(0)].groupby('circuitId').is_dnf.agg(['sum','count'])
    out=circuits.copy(); out['Altitude_Category']=np.select([out.alt.isna(),out.alt.lt(250),out.alt.lt(1000)],['Unknown','Low','Medium'],default='High')
    out['Avg_Track_Speed']=out.circuitId.map(speed)
    out['Track_Volatility_Score']=out.circuitId.map(100*eligible['sum']/eligible['count'])
    out['Track_Type']=out.circuitId.map(circuit_types).fillna('Unknown')
    out['Map_Location_Text']=out.apply(lambda r: f'{r.lat},{r.lng}' if pd.notna(r.lat) and pd.notna(r.lng) else None,axis=1)
    return out.rename(columns={'alt':'Altitude','name':'Circuit_Name','country':'Country','location':'Location'})


def build_timing(tables,facts,circuit_types):
    sprint=enrich_entries(tables['sprints'],tables)
    return {'kpi_pit_driver_team':pit_metrics(tables['pits'],facts), 'v_lap_chart_from_stg':lap_metrics(tables['laps'],tables['races'],tables['drivers']), 'sprint_heycan_score_v2':dynamics(sprint), 'sprint_heycan_score_v2_no_indy':dynamics(facts[facts.race_name.ne('Indianapolis 500')]), 'circuit_dna':circuit_metrics(tables['circuits'],facts,circuit_types)}
