"""Ten physical core report sources from validated raw tables."""
import pandas as pd
from .common import checked_join


def build_core(tables, facts):
    f=facts.copy()
    races=tables['races'][tables['races'].raceId.isin(f.raceId)].copy()
    races=checked_join(races,tables['circuits'],'circuitId',['circuitRef'])
    races['year_circuit']=races.year.astype(int).astype(str)+' | '+races['name']+' | '+races.raceId.astype(int).astype(str)
    schedule=races.rename(columns={'raceId':'raceid','circuitId':'circuitid'})
    teams=tables['constructors'].rename(columns={'constructorId':'constructorid','constructorRef':'constructorref'})
    circuits=tables['circuits'].rename(columns={'circuitId':'circuitid','circuitRef':'circuitref'})
    common=f.rename(columns={'driverRef':'driverref','constructorRef':'constructorref','race_name':'grand_prix','circuitId':'circuitid','circuitRef':'circuit_ref','location':'circuit_location','race_url':'wiki_url'})
    summary=common
    grid=f[f.is_nonstart.eq(0) & f.grid.gt(0)].rename(columns={'driverRef':'driverref','constructorRef':'constructorref','race_name':'grand_prix','grid':'grid_position'})
    result=f.rename(columns={'driverRef':'driverref','constructorRef':'constructorref'}).copy()
    result['seconds']=result.milliseconds/1000
    performance=checked_join(tables['constructor_results'],tables['constructors'],'constructorId',['constructorRef'])
    performance=checked_join(performance,tables['races'].rename(columns={'name':'race_name'}),'raceId',['race_name']).rename(columns={'constructorRef':'constructorref'})
    ranking=checked_join(tables['constructor_standings'],tables['constructors'].rename(columns={'name':'team_name','nationality':'team_nationality'}),'constructorId',['team_name','team_nationality'])
    ranking=checked_join(ranking,races.rename(columns={'name':'race_name','round':'race_round'}),'raceId',['race_name','race_round','year_circuit'])
    cr=tables['constructor_results'][['raceId','constructorId','points']].rename(columns={'points':'race_points'})
    if cr.duplicated(['raceId','constructorId']).any(): raise ValueError('Duplicate constructor race results')
    ranking=ranking.merge(cr,on=['raceId','constructorId'],how='left',validate='many_to_one')
    ranking=ranking.rename(columns={'position':'championship_position','points':'total_points','wins':'total_wins'})
    dr=checked_join(tables['driver_standings'],tables['drivers'],'driverId',['driverRef'])
    dr=checked_join(dr,tables['races'].rename(columns={'name':'race_name'}),'raceId',['race_name']).rename(columns={'driverRef':'driverref'})
    f['starts']=1-f.is_nonstart
    dnf=f.groupby(['raceId','year','circuitId','circuitRef','race_name'],dropna=False,as_index=False).agg(starts=('starts','sum'),finishes=('is_finish','sum'),disqualified_count=('is_disqualified','sum'),dnfs=('is_dnf','sum'),dnf_human=('is_incident','sum'),dnf_vehicle=('is_vehicle','sum'),dnf_other=('is_other_dnf','sum'),nonstart_count=('is_nonstart','sum')).rename(columns={'race_name':'grand_prix'})
    return {'team_details':teams,'track_information':circuits,'stg_race_schedule':schedule,'v_summary_base':summary,'v_grid_start_facts':grid,'stg_race_result':result,'stg_constructor_performance':performance,'stg_constructor_rankings':ranking,'stg_driver_rankings':dr,'v_dnf_by_circuit_year_reason':dnf}
