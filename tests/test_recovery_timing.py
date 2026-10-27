import numpy as np
import pandas as pd
import unittest
from scripts.f1_recovery.timing import pit_metrics, lap_metrics, dynamics, circuit_metrics


def facts():
    return pd.DataFrame([
        dict(resultId=1,raceId=1,driverId=1,constructorId=1,constructorRef='t',driverRef='d',race_name='United States Grand Prix',year_circuit='2004 | United States Grand Prix | 1',year=2004,grid=0,position='1',positionOrder=1,is_finish=1,is_nonstart=0,is_dnf=0,laps=2,statusId=1,circuitId=19,fastestLapSpeed=None),
        dict(resultId=2,raceId=1,driverId=1,constructorId=1,constructorRef='t',driverRef='d',race_name='United States Grand Prix',year_circuit='2004 | United States Grand Prix | 1',year=2004,grid=0,position='1',positionOrder=1,is_finish=1,is_nonstart=0,is_dnf=0,laps=2,statusId=1,circuitId=19,fastestLapSpeed=None),
        dict(resultId=3,raceId=2,driverId=2,constructorId=2,constructorRef='u',driverRef='e',race_name='Indianapolis 500',year_circuit='1950 | Indianapolis 500 | 2',year=1950,grid=2,position='1',positionOrder=1,is_finish=1,is_nonstart=0,is_dnf=0,laps=2,statusId=1,circuitId=19,fastestLapSpeed='123')])


def test_pits_do_not_multiply_duplicates_and_retain_long_stops():
    pits=pd.DataFrame([dict(raceId=1,driverId=1,milliseconds=x) for x in (1000,2000,3000,100000)])
    row=pit_metrics(pits,facts()).iloc[0]
    assert row.pit_count==4 and row.avg_pit_s==26.5
    assert row.iqr_pit_s==25.5 and np.isclose(row.sd_pit_s,np.std([1,2,3,100]))


def test_laps_sorted_for_cumulative_time_and_missing_start():
    laps=pd.DataFrame([dict(raceId=1,driverId=1,lap=2,milliseconds=61234),dict(raceId=1,driverId=1,lap=1,milliseconds=60123),dict(raceId=2,driverId=2,lap=1,milliseconds=40000)])
    races=pd.DataFrame([dict(raceId=1,name='A',year=2020,date='2020-01-01',time='12:00:00'),dict(raceId=2,name='B',year=2020,date='2020-01-02',time=None)])
    drivers=pd.DataFrame([dict(driverId=1,driverRef='d'),dict(driverId=2,driverRef='e')])
    out=lap_metrics(laps,races,drivers).set_index(['raceid','lap'])
    assert out.loc[(1,2),'lap_timestamp']=='2020-01-01 12:02:01.357'
    assert out.loc[(1,2),'lap_time_formatted']=='1:01.234'
    assert pd.isna(out.loc[(2,1),'race_start_ts']) and pd.isna(out.loc[(2,1),'lap_timestamp'])


def test_dynamics_unknown_winner_grid_and_indy_exclusion():
    f=facts().drop_duplicates(['raceId','driverId'])
    out=dynamics(f[f.race_name.ne('Indianapolis 500')])
    assert out.raceId.tolist()==[1] and pd.isna(out.iloc[0].norm_surprise)
    assert out.iloc[0].norm_density==1


def test_circuit_altitude_boundaries_missing_type_and_speed():
    circuits=pd.DataFrame([dict(circuitId=i,name=str(i),country='C',location='L',lat=1,lng=2,alt=alt) for i,alt in [(19,249),(20,250),(21,1000),(22,None)]])
    f=facts(); f['fastestLapSpeed']=None
    out=circuit_metrics(circuits,f,{19:'Race circuit'}).set_index('Circuit_Name')
    assert out.Altitude_Category.tolist()==['Low','Medium','High','Unknown']
    assert out.loc['20','Track_Type']=='Unknown' and out.Avg_Track_Speed.isna().all()

class TimingTests(unittest.TestCase):
    def test_pits(self): test_pits_do_not_multiply_duplicates_and_retain_long_stops()
    def test_laps(self): test_laps_sorted_for_cumulative_time_and_missing_start()
    def test_dynamics(self): test_dynamics_unknown_winner_grid_and_indy_exclusion()
    def test_circuit(self): test_circuit_altitude_boundaries_missing_type_and_speed()

class IntegrationTests(unittest.TestCase):
    def test_lookup_validation_and_actual_sprint_scope(self):
        from pathlib import Path
        from scripts.f1_recovery.common import load_tables, build_facts
        from scripts.f1_recovery.timing import load_circuit_types, build_timing
        repo=Path(__file__).resolve().parents[1]
        tables=load_tables(repo); facts_all=build_facts(tables)
        lookup=load_circuit_types(repo/'config/circuit_types.json',tables['circuits'])
        self.assertEqual(len(lookup),77)
        self.assertEqual(lookup[44],'Unknown')
        out=build_timing(tables,facts_all,lookup)
        sprint=out['sprint_heycan_score_v2']; normal=out['sprint_heycan_score_v2_no_indy']
        self.assertEqual(sprint.raceId.nunique(),15)
        self.assertEqual(set(sprint.raceId),set(tables['sprints'].raceId))
        self.assertEqual(set(normal.raceId),set(facts_all.loc[facts_all.race_name.ne('Indianapolis 500'),'raceId']))
        self.assertTrue(any(normal.year_circuit.str.contains('United States Grand Prix')))
        self.assertEqual(len(out['v_lap_chart_from_stg']),575029)
        self.assertEqual(out['kpi_pit_driver_team'].pit_count.sum(),10990)
