# F1 dashboard recovery

## Verified state

The public Looker Studio report displays a dataset configuration error. Its detail dialog reports:

```text
Not found: Table formula-1-analysis-477207:kpi.v_summary_base was not found in location EU
```

The upstream snapshot has 14 CSV files under `data/raw/` and 14 under `data/processed/`. They are Git data files, not Git LFS pointers. Its tree and notebook source cells do not contain the original SQL definition of `v_summary_base`. A documented summary reconstruction is available below.

The observed error does not establish that the object was deleted. The object name, dataset location, existence and access must be checked in the Google Cloud project. A GitHub fork does not restore a cloud view, copy its dataset or grant access to the report.

## 1. Inspect the source in BigQuery

Use an account with access to the existing project. In BigQuery Explorer, inspect the `kpi` dataset's details and its actual location. Check whether `v_summary_base` exists and whether it is a table or a view.

If using an already authenticated Google Cloud CLI, these commands inspect metadata without changing resources:

```sh
bq show --format=prettyjson formula-1-analysis-477207:kpi
bq show --format=prettyjson formula-1-analysis-477207:kpi.v_summary_base
```

If the view exists, recover its definition using the following metadata query. Run it in the dataset's actual location:

```sql
SELECT
  table_name,
  view_definition,
  use_standard_sql
FROM `formula-1-analysis-477207.kpi.INFORMATION_SCHEMA.VIEWS`
WHERE table_name = 'v_summary_base';
```

This query was prepared from the documented metadata schema; it has not been executed against this project. An empty result means no matching view was returned by that metadata query; it does not distinguish a base table from a missing object. Check the object's metadata and any access error separately.

If the view is absent, recover its SQL from the project owner's saved queries, available query history, or a backup. Preserve the result's column names, types, granularity and joins used by the report. Raw CSV files alone do not specify the original report's calculated fields or view definition.

Save recovered SQL in this repository before restoring it. If the SQL cannot be recovered, first inventory the report's required fields and calculations with an editor; then rebuild and validate the model against that contract. Do not replace the view with an arbitrary join just to remove the connection error.

## 2. Reconnect the report

After a valid source is available, a report/data-source editor can:

1. Open the existing data source for editing.
2. Choose **Edit connection**.
3. Select the correct project, dataset and view/table, or correct the custom query.
4. Choose **Reconnect** and review the field changes before applying them.
5. Check the data credentials. The credentials used by the report must be able to read the selected source and any underlying resources.

Embedded data sources can be edited by report editors. Reusable data sources require their own **Can Edit** permission. The public viewer link alone is not sufficient.

## 3. Validate before adding the live link to a CV

- Open all report pages, including overview, lap performance, excitement, grid position and team/driver views.
- Test year, driver, constructor and race filters.
- Check totals and aggregation grain against the underlying data; confirm that joins do not multiply race or lap records.
- Confirm that each chart has its required fields and calculations after reconnection.
- Open the shared link in a separate viewer session and verify that charts load under the intended sharing and credentials configuration.

Until this passes, use the repository and dataset links in the CV and label the existing screenshot as a preview.

## Account-level checks and summary reconstruction

The signed-in connector listed the F1 project and the `kpi`, `formula1_dataset`, `revize` and `staging` datasets. Each dataset's table picker returned no available tables. A direct query to the old summary view returned **Entity not found**, while `SELECT 1 AS connection_test` successfully reached the connection-change preview. The control query was cancelled rather than applied. These checks show that the query connection can operate; they do not establish whether the old objects were deleted, expired, moved, or hidden by resource permissions.

The repair copy started with 11 pages, 20 named BigQuery data sources and one unknown reusable source used by two variables. A separate, unused diagnostic source was later added for the history check below. Reconnecting the summary alone does not restore every page. Preserve the other KPI definitions until their calculations can be recovered.

The [recovery script](../scripts/recover_summary.py) rebuilds the observed summary contract from the original CSV revision. Run from the repository root with Python 3.8 or later:

```sh
python -m unittest discover -s tests -v
python scripts/recover_summary.py --ref 7e0fc6dbecba19e0a95f9f85c1cbd493821f3788
```

This generates `data/recovery/v_summary_base.csv` and `sql/recovery_v_summary_base.sql`. The generated SELECT embeds a fixed upstream snapshot and needs no stored BigQuery tables. It does not create views, load data, change billing or recover the missing original SQL. The [manifest](../data/recovery/summary_manifest.json) records source hashes, the source commit and snapshot coverage.

Local validation produced **26,519 result rows across 1,113 races**, covering **1950 through 7 July 2024**. All rows matched an independent set of pandas joins. `win_flag` explicitly means `positionOrder = 1`; its 1,116 flagged rows include the shared-car winners in three historical races, so result grain is preserved. The five unit tests cover row mapping, missing references, duplicate dimension keys, unsafe literal delimiters and query size.

The recovered field contract is: `year`, `raceId`, `grand_prix`, `date`, `wiki_url`, `driverId`, `driverref`, `constructorId`, `team_name`, `win_flag`, `country`, `circuit_location`, `circuit_ref`, `circuitid`.

To validate in the repair copy, edit the embedded summary source, choose BigQuery **Custom Query**, select the existing F1 project and paste the generated SELECT. Review the connection-change preview: names and types must match the existing fields. Apply only after checking the preview, then test chart totals and filters against the manifest. The snapshot contains historical data, not a live update feed.

## Live validation on 27 October 2026

**Status: partial recovery.** The summary query was applied to the owner's repair copy after checking the connection-change preview. No summary fields were added or removed. The `driverref` semantic type was explicitly corrected from City to Text. Overview indicators, team wins and Grand Prix counts now return data. This validates the reconstructed snapshot, not the missing view's original business logic.

| Overview check | Observed value | Independent snapshot value |
| --- | --- | --- |
| Seasons | 75 | 75 |
| Constructors with results | 211 | 211 |
| Drivers | 859 | 859 |
| Countries | 35 | 35 |
| Grand Prix names | 54 | 54 |
| Ferrari / McLaren / Mercedes win rows | 246 / 180 / 127 | 246 / 180 / 127 |

The race scorecard displays the rounded value **1.1K**; the independently validated snapshot contains **1,113 distinct races**. Filtering to 2024 returned **12 races, 21 drivers, 10 constructors, 12 countries and 12 Grand Prix names**, matching the source snapshot through 7 July 2024. The filter was then cleared.

The [track query](../sql/recovery_track_information.sql) preserves all **77 raw track rows** and the nine observed source fields. Its [manifest](../data/recovery/track_information_manifest.json) records the source and query hashes. Reconnection reported **No field changes**. A live data preview returned **77 rows**, including Albert Park at `-37.8497, 144.968` and Istanbul Park at `40.9517, 29.405`.

The map also depends on `stg_race_schedule`. A preview using its 18 original CSV columns reported missing `year_circuit` and `circuitRef` fields, plus five changed practice/qualifying/sprint date fields. That preview and its unsaved connection draft were discarded; the schedule source was not replaced. Restoring track data alone does not establish that map markers work.

The DNF source requires `dnf_human` and `dnf_vehicle` classifications whose original SQL was not found. Other custom sources, including GOAT scores and constructor summaries, also retain unresolved definitions. The report's 11 pages and all filters have not passed end-to-end validation, and public viewer access has not been verified. Keep using the repository and dataset links in the CV until the complete dashboard passes those checks.

An additional read-only query checked the F1 project's EU `INFORMATION_SCHEMA.JOBS_BY_PROJECT` history. It searched successful CREATE/ALTER query jobs from the retained 180 days for the original report's source names. The live preview returned **0 matching definition jobs**. This does not rule out older queries or SQL saved elsewhere. The diagnostic source is named **F1 SQL History Check (Diagnostic)** and is used by no charts. Completing the original report requires saved SQL definitions or another authoritative backup from the project contributors.

The [live validation record](../data/recovery/live_validation.json) is separate from generated snapshot manifests: generating a SQL file performs local checks and does not execute it against Google or certify a live report.

## Official references

- [BigQuery VIEWS metadata and view_definition](https://docs.cloud.google.com/bigquery/docs/information-schema-views)
- [BigQuery JOBS metadata and retained query history](https://docs.cloud.google.com/bigquery/docs/information-schema-jobs)
- [BigQuery data and query locations](https://docs.cloud.google.com/bigquery/docs/locations)
- [Edit or reconnect a Looker Studio data source](https://docs.cloud.google.com/data-studio/edit-the-data-source-connection)
- [Looker Studio data credentials](https://docs.cloud.google.com/data-studio/data-credentials)
