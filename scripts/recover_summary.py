"""Reconstruct the report summary contract from the upstream CSV snapshot.

The generated SELECT contains its input snapshot and needs no stored tables.
This is a documented reconstruction, not the missing view's original SQL.
"""
import argparse
import csv
from datetime import date
import hashlib
import io
import json
from pathlib import Path
import subprocess


FIELDS = ('year', 'raceId', 'grand_prix', 'date', 'wiki_url', 'driverId',
          'driverref', 'constructorId', 'team_name', 'win_flag', 'country',
          'circuit_location', 'circuit_ref', 'circuitid')
FILES = {'results': 'Race_Results.csv', 'races': 'Race_Schedule.csv',
         'drivers': 'Driver_Details.csv', 'constructors': 'Team_Details.csv',
         'circuits': 'Track_Information.csv'}
SPECS = {
    'results': [('raceId', 'raceId', 'INT64'), ('driverId', 'driverId', 'INT64'),
                ('constructorId', 'constructorId', 'INT64'), ('positionOrder', 'positionOrder', 'INT64')],
    'races': [('raceId', 'raceId', 'INT64'), ('year', 'year', 'INT64'),
              ('circuitId', 'circuitid', 'INT64'), ('name', 'grand_prix', 'STRING'),
              ('date', 'date', 'DATE'), ('url', 'wiki_url', 'STRING')],
    'drivers': [('driverId', 'driverId', 'INT64'), ('driverRef', 'driverref', 'STRING')],
    'constructors': [('constructorId', 'constructorId', 'INT64'), ('name', 'team_name', 'STRING')],
    'circuits': [('circuitId', 'circuitid', 'INT64'), ('country', 'country', 'STRING'),
                 ('location', 'circuit_location', 'STRING'), ('circuitRef', 'circuit_ref', 'STRING')],
}


def clean(value):
    return None if value is None or value == r'\N' or value == '' else str(value)


def integer(value):
    value = clean(value)
    if value is None:
        raise ValueError('Missing integer key or value')
    return int(value)


def index_rows(rows, key):
    index = {}
    for row in rows:
        identity = integer(row[key])
        if identity in index:
            raise ValueError(f'Duplicate {key}: {identity}')
        index[identity] = row
    return index


def rebuild_summary(tables):
    races = index_rows(tables['races'], 'raceId')
    drivers = index_rows(tables['drivers'], 'driverId')
    constructors = index_rows(tables['constructors'], 'constructorId')
    circuits = index_rows(tables['circuits'], 'circuitId')
    index_rows(tables['results'], 'resultId')
    output = []
    for result in tables['results']:
        race_id, driver_id, constructor_id = (integer(result[k]) for k in
                                               ('raceId', 'driverId', 'constructorId'))
        try:
            race, driver, constructor = races[race_id], drivers[driver_id], constructors[constructor_id]
            circuit_id = integer(race['circuitId'])
            circuit = circuits[circuit_id]
        except KeyError as error:
            raise ValueError(f'Missing dimension reference for result {result["resultId"]}: {error}') from error
        values = [integer(race['year']), race_id, clean(race['name']),
                  date.fromisoformat(race['date']).isoformat(), clean(race['url']), driver_id,
                  clean(driver['driverRef']), constructor_id, clean(constructor['name']),
                  int(integer(result['positionOrder']) == 1), clean(circuit['country']),
                  clean(circuit['location']), clean(circuit['circuitRef']), circuit_id]
        output.append(dict(zip(FIELDS, values)))
    if not output:
        raise ValueError('Missing result rows')
    return output


def build_snapshot_sql(tables):
    rebuild_summary(tables)
    ctes = []
    for table, columns in SPECS.items():
        packed = []
        for row in tables[table]:
            values = []
            for original, _, _ in columns:
                value = clean(row[original]) or ''
                if any(marker in value for marker in ('|', '\n', '\r', '\\', '"""')):
                    raise ValueError(f'Unsafe snapshot delimiter in {table}.{original}')
                values.append(value)
            packed.append('|'.join(values))
        payload = '\n'.join(packed)
        expressions = []
        for i, (_, alias, kind) in enumerate(columns):
            expr = f"NULLIF(p[OFFSET({i})], '')"
            if kind != 'STRING':
                expr = f'CAST({expr} AS {kind})'
            expressions.append(f'    {expr} AS {alias}')
        ctes.append(f'{table} AS (\n  SELECT\n' + ',\n'.join(expressions)
                    + '\n  FROM (SELECT SPLIT(line, \'|\') AS p\n'
                    + '        FROM UNNEST(SPLIT(r"""' + payload
                    + '""", \'\\n\')) AS line)\n)')
    sql = '-- Reconstructed upstream snapshot; win_flag means positionOrder = 1.\nWITH\n'
    sql += ',\n'.join(ctes)
    sql += '''
SELECT
  r.year, f.raceId, r.grand_prix, r.date, r.wiki_url,
  f.driverId, d.driverref, f.constructorId, c.team_name,
  IF(f.positionOrder = 1, 1, 0) AS win_flag,
  t.country, t.circuit_location, t.circuit_ref, t.circuitid
FROM results AS f
JOIN races AS r ON f.raceId = r.raceId
JOIN drivers AS d ON f.driverId = d.driverId
JOIN constructors AS c ON f.constructorId = c.constructorId
JOIN circuits AS t ON r.circuitid = t.circuitid
'''
    if len(sql.encode('utf-8')) >= 900000:
        raise ValueError('Snapshot SQL size exceeds the 900000-byte safety limit')
    return sql


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--ref', default='HEAD')
    args = parser.parse_args()
    tables, sources = {}, {}
    for key, filename in FILES.items():
        path = 'data/raw/' + filename
        raw = subprocess.run(['git', '-C', str(args.repo), 'show', args.ref + ':' + path],
                             check=True, capture_output=True, timeout=60).stdout
        tables[key] = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
        sources[path] = {'rows': len(tables[key]), 'sha256': hashlib.sha256(raw).hexdigest()}
    rows = rebuild_summary(tables)
    sql = build_snapshot_sql(tables)
    data_dir, sql_dir = args.repo / 'data/recovery', args.repo / 'sql'
    data_dir.mkdir(parents=True, exist_ok=True)
    sql_dir.mkdir(parents=True, exist_ok=True)
    with (data_dir / 'v_summary_base.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    (sql_dir / 'recovery_v_summary_base.sql').write_text(sql, encoding='utf-8')
    commit = subprocess.run(['git', '-C', str(args.repo), 'rev-parse', args.ref],
                            check=True, capture_output=True, text=True).stdout.strip()
    manifest = {'source_commit': commit, 'source_repository': 'gunay-ozsoy/F1_Data_Analysis_Project',
                'sources': sources, 'fields': list(FIELDS), 'rows': len(rows),
                'races': len({r['raceId'] for r in rows}), 'drivers': len({r['driverId'] for r in rows}),
                'winner_rows': sum(r['win_flag'] for r in rows),
                'min_year': min(r['year'] for r in rows), 'max_year': max(r['year'] for r in rows),
                'last_race_date': max(r['date'] for r in rows), 'query_bytes': len(sql.encode('utf-8')),
                'query_sha256': hashlib.sha256(sql.encode('utf-8')).hexdigest(),
                'status': 'locally_validated_snapshot',
                'limitation': 'Reconstructed summary only; original view SQL and other KPI definitions are not recovered.'}
    (data_dir / 'summary_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: manifest[k] for k in ['rows', 'races', 'drivers', 'winner_rows', 'min_year',
                                              'max_year', 'last_race_date', 'query_bytes', 'status']}))


if __name__ == '__main__':
    main()
