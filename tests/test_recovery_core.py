import json
import tempfile
import unittest
from pathlib import Path
import pandas as pd

try:
    from scripts.f1_recovery.common import enrich_entries, write_sources
    from scripts.f1_recovery.core import build_core
except ImportError:
    enrich_entries = write_sources = build_core = None


def fixture():
    return {
        'races': pd.DataFrame([dict(raceId=i, year=1950, round=i, circuitId=1, date='1950-05-13', time=None, name=n, url='u') for i,n in [(1,'A'),(2,'B')]]),
        'drivers': pd.DataFrame([dict(driverId=i, driverRef=f'd{i}', forename='First', surname=str(i), code=None, nationality='X') for i in range(1,7)]),
        'constructors': pd.DataFrame([dict(constructorId=1,constructorRef='team',name='Team',nationality='X',url='u')]),
        'circuits': pd.DataFrame([dict(circuitId=1,circuitRef='c',name='Circuit',url='u',country='X',location='Y',lat=1.,lng=2.,alt=None)]),
        'status': pd.DataFrame([dict(statusId=i,status=s) for i,s in [(1,'Finished'),(54,'Withdrew'),(2,'Disqualified'),(96,'Excluded')]]),
    }


def entries():
    return pd.DataFrame([dict(resultId=i, raceId=1 if i<6 else 2, driverId=i, constructorId=1, number=7 if i<3 else i, grid=1, position=1 if i==1 else None, positionOrder=i, points=0, laps=laps, milliseconds=None, statusId=status) for i,status,laps in [(1,1,5),(2,54,0),(3,54,2),(4,2,4),(5,96,1),(6,1,5)]])


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(enrich_entries, 'core recovery module must be implemented')

    def test_entry_grain_shared_car_and_race_keys(self):
        rows=entries(); rows.loc[2,'driverId']=1
        f=enrich_entries(rows,fixture())
        self.assertEqual(f.resultId.tolist(),[1,2,3,4,5,6])
        self.assertEqual(f[f.driverId.eq(1)].resultId.tolist(),[1,3])
        self.assertEqual(f.car_key[0],f.car_key[1])
        self.assertNotEqual(f.year_circuit[0],f.year_circuit[5])
        self.assertEqual(f.year_circuit[0],'1950 | A | 1')

    def test_outcomes_reconcile_with_withdrawal_and_exclusion(self):
        f=enrich_entries(entries(),fixture())
        self.assertEqual(f.outcome_group.tolist(),['finish','nonstart','other','disqualified','disqualified','finish'])
        self.assertEqual(int(f.is_dnf.sum()),1)

    def test_missing_and_duplicate_dimensions_rejected(self):
        t=fixture(); t['drivers']=t['drivers'].iloc[:-1]
        with self.assertRaises(ValueError): enrich_entries(entries(),t)
        t=fixture(); t['drivers']=pd.concat([t['drivers'],t['drivers'].iloc[[0]]])
        with self.assertRaises(ValueError): enrich_entries(entries(),t)

    def test_writer_rejects_duplicate_result_keys(self):
        schema=[{'source':'stg_race_result','fields':[{'name':'resultId','kind':'physical','type':'type_numeric'}]}]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); (p/'schema.json').write_text(json.dumps(schema))
            with self.assertRaises(ValueError):
                write_sources({'stg_race_result':pd.DataFrame({'resultId':[1,1]})},p/'out',p/'schema.json')

    def test_missing_optional_result_columns_are_retained(self):
        t=fixture(); t['results']=entries().assign(fastestLapSpeed='123')
        f=enrich_entries(entries().drop(columns='milliseconds'),t)
        self.assertTrue(f.milliseconds.isna().all())
        self.assertTrue(f.fastestLapSpeed.isna().all())

    def test_positive_lap_dnq_is_flagged_as_nonstart(self):
        from scripts.f1_recovery import common
        self.assertTrue(hasattr(common, 'find_anomalies'), 'anomaly detector is required')
        t=fixture(); t['status']=pd.concat([t['status'],pd.DataFrame([{'statusId':81,'status':'Did not qualify'}])],ignore_index=True)
        rows=entries().iloc[[0]].copy(); rows.loc[0,['resultId','statusId','laps']]=[13547,81,9]
        f=enrich_entries(rows,t)
        self.assertEqual(int(f.is_nonstart.iloc[0]),1)
        self.assertEqual(common.find_anomalies(f),[{'resultId':13547,'raceId':1,'driverId':1,'statusId':81,'laps':9}])

    def test_grid_source_excludes_nonstarts_and_zero_grid(self):
        t=fixture()
        t['constructor_results']=pd.DataFrame([dict(constructorResultsId=1,raceId=1,constructorId=1,points=1)])
        t['constructor_standings']=pd.DataFrame([dict(constructorStandingsId=1,raceId=1,constructorId=1,position=1,points=1,wins=1)])
        t['driver_standings']=pd.DataFrame([dict(driverStandingsId=1,raceId=1,driverId=1,position=1,points=1,wins=1)])
        rows=entries(); rows.loc[2,'grid']=0; rows.loc[3,'number']=7
        f=enrich_entries(rows,t)
        grid=build_core(t,f)['v_grid_start_facts']
        self.assertEqual(grid.resultId.tolist(),[1,4,5,6])
        self.assertEqual(grid.iloc[0].win_flag,1)
        self.assertEqual(grid.iloc[0].car_key, grid.iloc[1].car_key)

    def test_writer_rejects_duplicate_constructor_race_rankings(self):
        schema=[{'source':'stg_constructor_rankings','fields':[{'name':x,'kind':'physical','type':typ} for x,typ in [('constructorId','type_numeric'),('year_circuit','type_text')]]}]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); (p/'schema.json').write_text(json.dumps(schema))
            with self.assertRaises(ValueError):
                write_sources({'stg_constructor_rankings':pd.DataFrame({'constructorId':[1,1],'year_circuit':['1950 | A | 1']*2})},p/'out',p/'schema.json')

    def test_writer_rejects_infinite_approved_numeric_extra(self):
        schema=[{'source':'v_dnf_by_circuit_year_reason','fields':[{'name':'raceId','kind':'physical','type':'type_numeric'}]}]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); (p/'schema.json').write_text(json.dumps(schema))
            with self.assertRaises(ValueError):
                write_sources({'v_dnf_by_circuit_year_reason':pd.DataFrame({'raceId':[1],'dnf_other':[float('inf')],'nonstart_count':[0]})},p/'out',p/'schema.json')

    def test_writer_excludes_nonphysical_and_preserves_null_utf8(self):
        schema=[{'source':'sample','fields':[{'name':'name','kind':'physical','type':'type_text'},{'name':'seconds','kind':'physical','type':'type_numeric'},{'name':'Record Count','kind':'physical','type':'type_numeric'},{'name':'calc','kind':'calculated','type':'type_numeric'},{'name':'param','kind':'parameter','type':'type_text'}]}]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); (p/'schema.json').write_text(json.dumps(schema))
            write_sources({'sample':pd.DataFrame({'name':['Émile'],'seconds':[None],'calc':[5],'param':['x']})},p/'out',p/'schema.json')
            self.assertEqual((p/'out'/'sample.csv').read_text(encoding='utf8'),'name,seconds\nÉmile,\n')
