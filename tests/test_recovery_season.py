import pandas as pd
import unittest
from scripts.f1_recovery.season import build_season


def fixture():
    races=pd.DataFrame([dict(raceId=1,year=2023,round=1),dict(raceId=2,year=2024,round=1),dict(raceId=3,year=2024,round=2)])
    rows=[]
    def add(rid,driver,team,pos,points,finish=1,grid=1):
        rows.append(dict(resultId=len(rows)+1,raceId=rid,year=2023 if rid==1 else 2024,round=1,race_name='Race',constructorId=team,team_name=f'T{team}',driverId=driver,driver_name=f'D{driver}',driverRef=f'd{driver}',driver_code=None,position=str(pos) if pos else None,positionOrder=pos or 9,points=points,grid=grid,is_nonstart=0,is_finish=finish,win_flag=int(pos==1)))
    add(1,1,1,1,10); add(1,1,1,1,2); add(1,2,1,1,5,grid=2)
    add(1,3,2,None,0,0); add(1,4,2,None,0,0,2)
    add(2,1,1,1,10); add(2,2,1,2,6,grid=2)
    t={'races':races,'constructor_results':pd.DataFrame([dict(raceId=1,constructorId=1,points=17)]),'constructor_standings':pd.DataFrame([dict(raceId=1,constructorId=1,points=7,position=1),dict(raceId=2,constructorId=1,points=16,position=1)]),'driver_standings':pd.DataFrame([dict(raceId=1,driverId=1,points=12,position=1),dict(raceId=2,driverId=1,points=10,position=1)]),'qualifying':pd.DataFrame(columns=['raceId','constructorId','driverId','position'])}
    return t,pd.DataFrame(rows)


def test_season_penalties_shared_wins_and_zero_shares():
    t,f=fixture(); out=build_season(t,f)
    s=out['constructor_summary_year_date'].query('season_year == 2023 and constructorId == 1').iloc[0]
    assert s.total_points==7 and s.season_wins==1 and s.avg_race_points==17
    ext=out['constructor_summary_extended']; a=ext.query('season_year == 2023 and driver_name == "D1"').iloc[0]
    assert a.driver_points==12 and a.contribution_rate==12/17
    assert ext.query('season_year == 2023 and driver_name == "D3"').contribution_rate.isna().all()
    team=out['constructor_goat_scores'].set_index('constructor_name')
    assert team.loc['T1','total_driver_championships']==1
    assert team.loc['T1','total_constructor_championships']==1
    assert out['GOAT_KPI'].empty


def test_ordered_pairs_ties_missing_qualifying_and_both_dnf():
    t,f=fixture(); p=build_season(t,f)['team_battle_table']
    assert not p.duplicated(['raceId','Team_Name','Driver_A','Driver_B']).any()
    tied=p.query('raceId == 1 and Driver_A == "D1" and Driver_B == "D2"').iloc[0]
    assert tied.Race_Win_Flag==0.5 and pd.isna(tied.Quali_Win_Flag)
    assert tied.Points_A==12 and tied.Points_Diff==7
    dnf=p.query('raceId == 1 and Driver_A == "D3" and Driver_B == "D4"').iloc[0]
    assert pd.isna(dnf.Race_Win_Flag) and pd.isna(dnf.Points_Share_Pct)


class SeasonTests(unittest.TestCase):
    def test_season(self):
        test_season_penalties_shared_wins_and_zero_shares()

    def test_pairs(self):
        test_ordered_pairs_ties_missing_qualifying_and_both_dnf()

class CareerThresholdTests(unittest.TestCase):
    def test_twenty_distinct_eligible_races_and_qualifying_tie(self):
        t,f=fixture()
        extra=[]
        for i in range(10,29):
            row=f.iloc[0].copy(); row['raceId']=i; row['resultId']=100+i
            extra.append(row)
        f=pd.concat([f,pd.DataFrame(extra)],ignore_index=True)
        t['races']=pd.concat([t['races'],pd.DataFrame([dict(raceId=i,year=2023,round=i) for i in range(10,29)])],ignore_index=True)
        t['qualifying']=pd.DataFrame([dict(raceId=1,constructorId=1,driverId=i,position=2) for i in (1,2)])
        out=build_season(t,f)
        assert out['GOAT_KPI'].driverId.tolist()==[1]
        assert out['team_battle_table'].query('raceId == 1 and Driver_A == "D1" and Driver_B == "D2"').iloc[0].Quali_Win_Flag==.5

class ScoringRateTests(unittest.TestCase):
    def test_excludes_nonstart_only_team_races_and_null_without_eligible_races(self):
        t, f = fixture()
        row = f.iloc[0].copy()
        row['raceId'] = 2; row['year'] = 2024; row['resultId'] = 500; row['constructorId'] = 2
        row['team_name'] = 'T2'; row['is_nonstart'] = 1; row['points'] = 0
        # Team 1's extra nonstart-only race must not dilute its 2023 rate.
        nonstart = f.iloc[0].copy()
        nonstart['raceId'] = 3; nonstart['resultId'] = 501
        nonstart['is_nonstart'] = 1; nonstart['points'] = 0
        f = pd.concat([f, pd.DataFrame([row, nonstart])], ignore_index=True)
        out = build_season(t, f)['constructor_summary_year_date']
        assert out.query('season_year == 2023 and constructorId == 1').iloc[0].scoring_rate == 1
        assert out.query('season_year == 2023 and constructorId == 2').iloc[0].scoring_rate == 0
        assert pd.isna(out.query('season_year == 2024 and constructorId == 2').iloc[0].scoring_rate)
