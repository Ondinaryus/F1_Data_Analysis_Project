#!/usr/bin/env python3
"""Rebuild physical report sources from the pinned upstream snapshot."""
import argparse
import json
from pathlib import Path
from f1_recovery.common import load_tables, build_facts, write_sources, find_anomalies
from f1_recovery.core import build_core
from f1_recovery.season import build_season
from f1_recovery.timing import build_timing, load_circuit_types


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--group', choices=['core','season','timing','all'], default='core')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1])
    args=p.parse_args()
    tables=load_tables(args.repo); facts=build_facts(tables)
    outputs={}
    if args.group in ('core','all'): outputs.update(build_core(tables,facts))
    if args.group in ('season','all'): outputs.update(build_season(tables,facts))
    if args.group in ('timing','all'):
        circuit_types=load_circuit_types(args.repo/'config/circuit_types.json',tables['circuits'])
        outputs.update(build_timing(tables,facts,circuit_types))
    manifest=write_sources(outputs,args.output,args.repo/'data/recovery/report_schema.json')
    race_dates=tables['races'].set_index('raceId')['date']
    for name, frame in outputs.items():
        key='raceId' if 'raceId' in frame else ('raceid' if 'raceid' in frame else None)
        if key:
            dates=frame[key].map(race_dates).dropna()
            if len(dates): manifest[name]['coverage']={'races':int(frame[key].nunique()),'first_date':str(dates.min()),'last_date':str(dates.max())}

    metadata={'source':tables['_source_manifest'],'coverage':{'result_rows':len(facts),'races':int(facts.raceId.nunique()),'drivers':int(facts.driverId.nunique()),'first_date':str(facts.date.min()),'last_date':str(facts.date.max()),'outcomes':{str(k):int(v) for k,v in facts.outcome_group.value_counts().items()}},'anomalies':{'positive_lap_did_not_qualify_nonstart':find_anomalies(facts)},'outputs':manifest}
    (args.output/'manifest.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf8')
    print(json.dumps(metadata['coverage']))

if __name__=='__main__': main()
