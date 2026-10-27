import importlib.util
from pathlib import Path
import unittest
import copy


MODULE = Path(__file__).resolve().parents[1] / 'scripts' / 'recover_summary.py'


def example_tables():
    return {
        'results': [
            {'resultId': '1', 'raceId': '100', 'driverId': '1', 'constructorId': '9', 'positionOrder': '1'},
            {'resultId': '2', 'raceId': '100', 'driverId': '2', 'constructorId': '9', 'positionOrder': '2'},
            {'resultId': '3', 'raceId': '200', 'driverId': '1', 'constructorId': '10', 'positionOrder': '5'},
        ],
        'races': [
            {'raceId': '100', 'year': '2020', 'circuitId': '77', 'name': 'Brazilian GP', 'date': '2020-11-15', 'url': 'https://example.test/brazil'},
            {'raceId': '200', 'year': '2021', 'circuitId': '88', 'name': 'Italian GP', 'date': '2021-09-12', 'url': 'https://example.test/italy'},
        ],
        'drivers': [{'driverId': '1', 'driverRef': 'alpha'}, {'driverId': '2', 'driverRef': 'beta'}],
        'constructors': [{'constructorId': '9', 'name': "Racing O'Clock"}, {'constructorId': '10', 'name': 'Beta'}],
        'circuits': [
            {'circuitId': '77', 'circuitRef': 'interlagos', 'location': 'São Paulo', 'country': 'Brazil'},
            {'circuitId': '88', 'circuitRef': 'monza', 'location': 'Monza', 'country': 'Italy'},
        ],
    }


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(MODULE.is_file(), 'The summary recovery implementation is missing')
        spec = importlib.util.spec_from_file_location('summary_recovery', MODULE)
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)

    def test_result_rows_and_winners_survive_dimension_joins(self):
        rows = self.mod.rebuild_summary(example_tables())
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0], {
            'year': 2020, 'raceId': 100, 'grand_prix': 'Brazilian GP', 'date': '2020-11-15',
            'wiki_url': 'https://example.test/brazil', 'driverId': 1, 'driverref': 'alpha',
            'constructorId': 9, 'team_name': "Racing O'Clock", 'win_flag': 1,
            'country': 'Brazil', 'circuit_location': 'São Paulo', 'circuit_ref': 'interlagos', 'circuitid': 77,
        })
        self.assertEqual([(r['driverId'], r['team_name'], r['win_flag']) for r in rows[1:]],
                         [(2, "Racing O'Clock", 0), (1, 'Beta', 0)])

    def test_duplicate_dimension_key_cannot_multiply_results(self):
        tables = example_tables()
        tables['constructors'].append(copy.deepcopy(tables['constructors'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.mod.rebuild_summary(tables)

    def test_missing_driver_cannot_silently_drop_a_result(self):
        tables = example_tables()
        tables['results'][0]['driverId'] = '999'
        with self.assertRaisesRegex(ValueError, 'Missing'):
            self.mod.rebuild_summary(tables)

    def test_unsafe_delimiter_cannot_change_embedded_row_boundaries(self):
        tables = example_tables()
        tables['constructors'][0]['name'] = 'Alpha|Beta'
        with self.assertRaisesRegex(ValueError, 'delimiter'):
            self.mod.build_snapshot_sql(tables)

    def test_oversized_snapshot_is_rejected_without_truncation(self):
        tables = example_tables()
        tables['races'][0]['url'] = 'x' * 900000
        with self.assertRaisesRegex(ValueError, 'size'):
            self.mod.build_snapshot_sql(tables)


if __name__ == '__main__':
    unittest.main()
