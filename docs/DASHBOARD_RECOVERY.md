# F1 dashboard recovery

**Current status: all 20 named sources rebuilt locally; live dashboard partially recovered.** The owner's repair copy is `39dad2ce-81db-4aed-be5c-96dfafa904e8`, titled **Formula 1 | Race & Performance Analysis**. Four sources are connected through authorized BigQuery fixed-snapshot SELECTs. The remaining 16 sources have not been migrated. This is not a fully restored dashboard.

Start with [reproduction and methodology](RECOVERY_METHODOLOGY.md). The [full manifest](../data/recovery/full_source_manifest.json) records generated data; the [current validation checkpoint](../data/recovery/report_validation.json) separately records observed live behavior. Local generation does not execute Google queries or certify report functionality.

## Generated model

The pipeline reconstructs 20 sources from 14 raw CSVs pinned at upstream commit `7e0fc6dbecba19e0a95f9f85c1cbd493821f3788`. Results cover 26,519 entries across 1,113 races from 13 May 1950 through 7 July 2024. The core, season and timing groups have independent approval, and 24 unit tests passed. See the [core](recovery/CORE_DATA.md), [season/career](recovery/SEASON_METRICS.md) and [timing/circuit](recovery/TIMING_METRICS.md) definitions for grains, exclusions and missing-value treatment.

The original SQL was unavailable. New indices are documented reconstructions and exploratory proxies, not recovered original formulas or objective measures of driver talent. The snapshot is historical, not a live update feed.

## Observed live checkpoint

| Named source | Applied connection | Observed rows | Field review |
| --- | --- | ---: | --- |
| `v_summary_base` | Fixed-snapshot BigQuery SELECT | 26,519 | Summary contract retained; `driverref` semantic type corrected to Text |
| `track_information` | Fixed-snapshot BigQuery SELECT | 77 | Nine fields retained |
| `stg_race_schedule` | Fixed-snapshot BigQuery SELECT | 1,113 | 20 fields; only `quali_date` type changed |
| `v_dnf_by_circuit_year_reason` | Fixed-snapshot BigQuery SELECT | 1,113 | 13 fields; only `dnf_other` and `nonstart_count` added |

| Overview check | Observed value |
| --- | ---: |
| Seasons | 75 |
| Constructors with results | 211 |
| Drivers | 859 |
| Countries | 35 |
| Grand Prix names | 54 |
| Race scorecard | 1.1K (underlying distinct races: 1,113) |

Constructor wins now use a conditional **COUNT_DISTINCT of winning `raceId`**, producing **Ferrari 245, McLaren 180 and Mercedes 127**. Counting winner result rows would overcount shared-car winners; the summary preserves those original result entries.

The DNF chart shows **Vehicle**, **Incident/health** and **Other**, excludes disqualifications and nonstarts, in a numeric table with **10 rows per page**. Incident/health is a status grouping, not attribution of driver fault. The native Geo chart now displays circuit markers from the exact-coordinate chart calculation and distinct race count. Top-left navigation is enabled with a visible header; the viewer currently exposes nine pages and two additional pages remain hidden.

## Remaining work before using a live CV link

CSV connector permission is pending; no new CSV uploads have been completed. The 16 remaining named source connections must be migrated and reviewed against the generated manifest and physical schema.

All **11 pages** still need end-to-end verification. Check each chart's fields and aggregation grain; test year, driver, constructor and race filters; set valid defaults (including one ordered teammate pair and a single race for lap curves); check navigation and overall usability; and open the shared report in a separate public viewer session. Recheck map markers and filter behavior after migrating the remaining sources. Record results against the fixed snapshot, including sources whose timing coverage ends before the overall cutoff.

Until those checks pass, use repository and dataset links in a CV and label the screenshot as a historical preview. A passing model test suite and four working connections do not establish that the other pages or public viewer work.

## Original failure and recovery history

The original public report returned a dataset configuration error:

```text
Not found: Table formula-1-analysis-477207:kpi.v_summary_base was not found in location EU
```

That observation does not establish whether objects were deleted, expired, moved or hidden by permissions. Forking the Git repository preserves data and code history; it does not restore BigQuery objects or report access. The upstream snapshot contains 14 raw and 14 processed CSVs as Git data files.

The original 20 source SQL definitions were absent from the repository and raw notebook source. A read-only search of the project's retained **180-day EU query history** returned **zero matching successful CREATE/ALTER definition jobs**. Older or externally saved SQL remains possible. The unused diagnostic source is not part of the 20 rebuilt model outputs. The repair copy also had an unknown reusable source used by two variables; the 20-source reconstruction does not certify those variables.

The earlier [live validation record](../data/recovery/live_validation.json) is a historical partial checkpoint. It predates the applied calendar/DNF sources and corrected distinct constructor wins; use [report_validation.json](../data/recovery/report_validation.json) for current status. The earlier [summary script](../scripts/recover_summary.py), [summary manifest](../data/recovery/summary_manifest.json), [track query](../sql/recovery_track_information.sql) and [track manifest](../data/recovery/track_information_manifest.json) retain the initial recovery history.

## Official references

- [BigQuery VIEWS metadata and view_definition](https://docs.cloud.google.com/bigquery/docs/information-schema-views)
- [BigQuery JOBS metadata and retained query history](https://docs.cloud.google.com/bigquery/docs/information-schema-jobs)
- [BigQuery data and query locations](https://docs.cloud.google.com/bigquery/docs/locations)
- [Edit or reconnect a Looker Studio data source](https://docs.cloud.google.com/data-studio/edit-the-data-source-connection)
- [Looker Studio data credentials](https://docs.cloud.google.com/data-studio/data-credentials)
