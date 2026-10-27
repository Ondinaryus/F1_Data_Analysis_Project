"""Reconstructed season, career and ordered teammate metrics."""
import numpy as np
import pandas as pd


def _final_standings(tables, key):
    s=tables[key].merge(tables['races'][['raceId','year','round']],on='raceId',validate='many_to_one')
    entity='driverId' if key=='driver_standings' else 'constructorId'
    return s.sort_values(['year','round','raceId']).drop_duplicates(['year',entity],keep='last')


def _titles(tables, facts):
    scheduled=tables['races'].groupby('year').raceId.agg(set)
    completed=facts.groupby('year').raceId.agg(set)
    years=[y for y, ids in scheduled.items() if ids <= completed.get(y,set())]
    # A champion must be recorded at the final scheduled race, not merely at
    # their own last available standing earlier in the year.
    final=tables['races'].sort_values(['year','round','raceId']).drop_duplicates('year',keep='last')
    final=final[final.year.isin(years)][['raceId','year']]
    ds=tables['driver_standings'].merge(final,on='raceId',validate='many_to_one').query('position == 1')
    cs=tables['constructor_standings'].merge(final,on='raceId',validate='many_to_one').query('position == 1')
    attribution=facts.groupby(['year','driverId','constructorId'],as_index=False).agg(points=('points','sum'),entries=('resultId','count'))
    wins=facts[facts.win_flag.eq(1)].groupby(['year','driverId','constructorId']).raceId.nunique().rename('wins').reset_index()
    attribution=attribution.merge(wins,on=['year','driverId','constructorId'],how='left',validate='one_to_one'); attribution['wins']=attribution.wins.fillna(0)
    attribution=attribution.sort_values(['year','driverId','points','wins','entries','constructorId'],ascending=[True,True,False,False,False,True]).drop_duplicates(['year','driverId'])
    ds=ds.merge(attribution[['year','driverId','constructorId']],on=['year','driverId'],how='left',validate='many_to_one')
    return ds,cs


def _pairs(tables, eligible):
    f=eligible.copy()
    f['classified']=pd.to_numeric(f.position,errors='coerce')
    f['grid']=f.grid.where(f.grid.gt(0))
    # Classified result first; among repeated records take best numeric position,
    # then best order and stable result id. Its grid is the representative grid.
    f=f.sort_values(['raceId','constructorId','driverId','classified','positionOrder','resultId'],na_position='last')
    keys=['raceId','constructorId','driverId']
    points=f.groupby(keys,as_index=False).points.sum()
    d=f.drop_duplicates(keys).drop(columns='points').merge(points,on=keys,validate='one_to_one')
    q=tables['qualifying'][keys+['position']].copy(); q['position']=pd.to_numeric(q.position,errors='coerce')
    q=q.groupby(keys,as_index=False).position.min().rename(columns={'position':'quali'})
    d=d.merge(q,on=keys,how='left',validate='one_to_one')
    d['label']=d.driver_code.fillna(d.driverRef)
    pairs=d.merge(d,on=['raceId','constructorId'],suffixes=('_a','_b'),validate='many_to_many')
    pairs=pairs[pairs.driverId_a.ne(pairs.driverId_b)].copy()
    a,b=pairs.classified_a,pairs.classified_b
    race=np.where(a.notna() & b.notna(),np.where(a<b,1.,np.where(a>b,0.,.5)),np.where(a.notna(),1.,np.where(b.notna(),0.,np.nan)))
    qa,qb=pairs.quali_a,pairs.quali_b
    quali=np.where(qa.notna() & qb.notna(),np.where(qa<qb,1.,np.where(qa>qb,0.,.5)),np.nan)
    denom=pairs.points_a+pairs.points_b
    out=pd.DataFrame({'raceId':pairs.raceId,'constructorId':pairs.constructorId,'driverId_A':pairs.driverId_a,'driverId_B':pairs.driverId_b,'year':pairs.year_a,'round':pairs.round_a,'Race_Name':pairs.race_name_a,'Team_Name':pairs.team_name_a,'Driver_A':pairs.driver_name_a,'Driver_B':pairs.driver_name_b,'Driver_A_Code':pairs.label_a,'Driver_B_Code':pairs.label_b,'Finish_A':a,'Finish_B':b,'Grid_A':pairs.grid_a,'Grid_B':pairs.grid_b,'Points_A':pairs.points_a,'Points_B':pairs.points_b,'Grid_Gap':pairs.grid_b-pairs.grid_a,'Race_Gap':b-a,'Points_Diff':pairs.points_a-pairs.points_b,'Points_Share_Pct':100*pairs.points_a/denom.where(denom.gt(0)),'Quali_Win_Flag':quali,'Race_Win_Flag':race})
    if out.duplicated(['raceId','constructorId','driverId_A','driverId_B']).any(): raise ValueError('Duplicate ordered teammate pair')
    return out


def build_season(tables, facts):
    f=facts.copy(); f['classified']=pd.to_numeric(f.position,errors='coerce')
    eligible=f[f.is_nonstart.eq(0)].copy(); keys=['year','constructorId']
    race=f.groupby(keys+['raceId'],as_index=False).agg(earned=('points','sum'),win=('win_flag','max'))
    cr=tables['constructor_results'][['raceId','constructorId','points']].rename(columns={'points':'official'})
    if cr.duplicated(['raceId','constructorId']).any(): raise ValueError('Duplicate constructor race results')
    race=race.merge(cr,on=['raceId','constructorId'],how='left',validate='one_to_one'); race['race_points']=race.official.fillna(race.earned)
    r=race.groupby(keys,as_index=False).agg(season_wins=('win','sum'),team_races=('raceId','nunique'),avg_race_points=('race_points','mean'),max_points_race=('race_points','max'),avg_points_when_scoring=('race_points',lambda x: x[x.gt(0)].mean()))
    eligible_races=eligible[keys+['raceId']].drop_duplicates()
    scoring=eligible_races.merge(race[keys+['raceId','race_points']],on=keys+['raceId'],validate='one_to_one').groupby(keys,as_index=False).agg(scoring_rate=('race_points',lambda x: x.gt(0).mean()))
    r=r.merge(scoring,on=keys,how='left',validate='one_to_one')
    e=eligible.groupby(keys,as_index=False).agg(finish_rate=('is_finish','mean'),podium_rate=('classified',lambda x: x.le(3).mean()),avg_finish=('classified','mean'),finish_std=('classified',lambda x: x.std(ddof=0)))
    s=f.groupby(keys,as_index=False).agg(team_name=('team_name','first'),earned=('points','sum')).merge(r,on=keys).merge(e,on=keys,how='left')
    s['consistency_score']=1/(1+s.finish_std); s['dominance_index']=s.season_wins/s.team_races
    st=_final_standings(tables,'constructor_standings')[keys+['points','position']].rename(columns={'points':'official_points','position':'official_rank'})
    s=s.merge(st,on=keys,how='left',validate='one_to_one'); s['total_points']=s.official_points.fillna(s.earned)
    # Fallback rank is calculated over all recorded constructors' earned points.
    fallback=s.groupby('year').earned.rank(method='dense',ascending=False)
    s['rank']=s.official_rank.fillna(fallback); s['season_start_date']=s.year.astype(int).astype(str)+'-01-01'; s=s.rename(columns={'year':'season_year'})
    drivers=f.groupby(['year','constructorId','driverId','driver_name'],as_index=False).points.sum().rename(columns={'points':'driver_points','year':'season_year'})
    drivers['contribution_rate']=drivers.driver_points/drivers.groupby(['season_year','constructorId']).driver_points.transform('sum').replace(0,np.nan)
    extended=drivers.merge(s,on=['season_year','constructorId'],validate='many_to_one')
    pairs=_pairs(tables,eligible); ds,cs=_titles(tables,f)
    team=f.groupby(['constructorId','team_name'],as_index=False).agg(total_wins=('win_flag',lambda x: 0))
    team=team.drop(columns='total_wins')
    team_races=eligible.groupby('constructorId').raceId.nunique(); wins=f[f.win_flag.eq(1)].groupby('constructorId').raceId.nunique()
    podium=eligible[eligible.classified.le(3)].groupby('constructorId').raceId.nunique(); poles=eligible[eligible.grid.eq(1)].groupby('constructorId').raceId.nunique()
    team['total_wins']=team.constructorId.map(wins).fillna(0); team['total_podiums']=team.constructorId.map(podium).fillna(0); team['total_poles']=team.constructorId.map(poles).fillna(0)
    team['total_constructor_championships']=team.constructorId.map(cs.groupby('constructorId').size()).fillna(0); team['total_driver_championships']=team.constructorId.map(ds.groupby('constructorId').size()).fillna(0)
    team['win_percentage_100']=100*team.total_wins/team.constructorId.map(team_races)
    completion=eligible.groupby('constructorId').classified.apply(lambda x: x.notna().mean())
    team['reliability_score_100']=100*team.constructorId.map(completion)
    def norm(x): return 100*x/x.max() if x.max()>0 else x*0
    team['final_goat_score']=pd.concat([team.win_percentage_100,team.reliability_score_100,norm(team.total_wins),norm(team.total_constructor_championships),norm(team.total_driver_championships)],axis=1).fillna(0).mean(axis=1)
    team=team.rename(columns={'team_name':'constructor_name'})
    dr=eligible.groupby(['driverId','driver_name','driverRef'],as_index=False).agg(starts=('raceId','nunique'),classified_count=('classified',lambda x: x.notna().sum()))
    # Deduplicate driver races to avoid inflating shared/repeated records.
    de=eligible.groupby(['driverId','raceId'],as_index=False).agg(win=('win_flag','max'),podium=('classified',lambda x: int(x.le(3).any())),classified=('classified',lambda x: int(x.notna().any())))
    stats=de.groupby('driverId').agg(wins=('win','sum'),podiums=('podium','sum'),classified=('classified','sum'))
    dr=dr.join(stats,on='driverId'); dr['successScore']=100*(.6*dr.wins/dr.starts+.4*dr.podiums/dr.starts)
    dr['consistencyScore']=100*dr.classified/dr.starts; dr['longevityScore']=norm(dr.starts)
    dr['championshipScore']=norm(dr.driverId.map(ds.groupby('driverId').size()).fillna(0))
    winning=eligible[eligible.win_flag.eq(1)].groupby('driverId').constructorId.nunique(); dr['multiTeamScore']=norm(dr.driverId.map(winning).fillna(0))
    dr['teammateDominanceScore']=100*dr.driverId.map(pairs.groupby('driverId_A').Race_Win_Flag.mean())
    per=eligible.groupby(['driverId','raceId','constructorId'],as_index=False).points.sum(); per['total']=per.groupby(['raceId','constructorId']).points.transform('sum'); per['share']=per.points/per.total.where(per.total.gt(0))
    dr['carAdjustedScore']=100*dr.driverId.map(per.groupby('driverId').share.mean())
    annual=eligible.groupby(['year','driverId','raceId'],as_index=False).win_flag.max().groupby(['year','driverId']).win_flag.agg(['sum','count']).reset_index(); annual['rate']=annual['sum']/annual['count']; annual['max']=annual.groupby('year').rate.transform('max'); annual['weighted']=annual['count']*annual.rate/annual['max'].replace(0,np.nan)
    era=annual.groupby('driverId').agg(weighted=('weighted','sum'),starts=('count','sum')); dr['eraScore']=100*dr.driverId.map(era.weighted/era.starts)
    cols=['successScore','championshipScore','consistencyScore','longevityScore','multiTeamScore','teammateDominanceScore','carAdjustedScore','eraScore']
    dr['GOAT_PUAN']=dr[cols].fillna(0).mean(axis=1); dr=dr[dr.starts.ge(20)].rename(columns={'driver_name':'driverName'})
    return {'constructor_summary_year_date':s,'constructor_summary_extended':extended,'GOAT_KPI':dr,'constructor_goat_scores':team,'team_battle_table':pairs}
