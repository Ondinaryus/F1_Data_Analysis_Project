# Recovery methodology

The recovery pipeline rebuilds all **20 named report sources** from the 14 raw CSVs in `gunay-ozsoy/F1_Data_Analysis_Project` at commit `7e0fc6dbecba19e0a95f9f85c1cbd493821f3788`. Recorded results span **13 May 1950–7 July 2024**: 26,519 result entries, 1,113 races and 859 drivers. This is a fixed historical snapshot. Timing coverage varies by source; the manifest records its actual dates.

The original 20 SQL definitions were unavailable. The retained 180-day EU query-history search returned no matching definition jobs, and the raw notebooks did not contain those definitions. The new indices and classifications are explicit reconstructions and exploratory proxies, not recovered original formulas or objective talent measures.

## Reproduce the sources

The generated checkpoint and 24 passing tests used **Python 3.12.14 (Clang 22.1.3), pandas 2.2.3 and NumPy 2.3.5**. Use Python 3.12.14 for the current 20-source pipeline and the pinned package versions below when comparing output hashes. This validated environment applies to `rebuild_recovery_data.py`; historical guidance for the earlier summary-only script does not establish compatibility for the full pipeline.

Run from a checkout containing the pinned commit and the recovery scripts, with `python` selecting Python 3.12.14. Git must be available: the loader reads the raw files from the pinned Git revision, rather than the working-tree CSVs.

```sh
python -m pip install pandas==2.2.3 numpy==2.3.5
python -m unittest discover -s tests -v
python scripts/rebuild_recovery_data.py --group all --output /tmp/f1_recovery
```

`--group` accepts `core`, `season`, `timing` or `all`. `--repo` can select another checkout containing the pinned data and schema. The output directory receives one UTF-8 CSV per source plus `manifest.json`, recording raw input hashes, output hashes, row counts, physical fields, sizes, coverage and the recorded positive-lap DNQ anomaly. Generation validates field contracts, numeric values and specified source keys. It does not connect or upload any source to Looker Studio.

## Definitions and evidence

| Method | Scope |
| --- | --- |
| [Core data](recovery/CORE_DATA.md) | Ten sources: dimensions, result grain, calendar, standings, grid facts and DNF classification |
| [Season and career metrics](recovery/SEASON_METRICS.md) | Five sources: constructor-season summaries, exploratory driver/constructor indices and ordered teammate comparisons |
| [Timing and circuit metrics](recovery/TIMING_METRICS.md) | Five sources: recorded pit durations, lap timing, sprint/race dynamics proxies and circuit descriptors |

The [physical schema](../data/recovery/report_schema.json) defines the observed source fields. The reconstruction additionally emits `car_key` for grid facts and `dnf_other` / `nonstart_count` for DNF reconciliation. Calculated fields, parameters and connector-generated record counts are not CSV input columns. [Circuit types](../config/circuit_types.json) retain their citations, confidence and layout limitations.

The [full source manifest](../data/recovery/full_source_manifest.json) records the generated 20-source checkpoint. Independent core, season and timing reviews approved the model, and its 24 unit tests passed. Those results describe the generated model. The separate [validation checkpoint](../data/recovery/report_validation.json) records the observed live state: four sources connected, 16 still awaiting migration, and end-to-end report validation pending. See [dashboard recovery](DASHBOARD_RECOVERY.md) before presenting any live link as restored.
