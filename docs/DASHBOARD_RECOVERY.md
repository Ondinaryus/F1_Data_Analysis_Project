# F1 dashboard recovery

## Verified state

The public Looker Studio report displays a dataset configuration error. Its detail dialog reports:

```text
Not found: Table formula-1-analysis-477207:kpi.v_summary_base was not found in location EU
```

The repository has 14 CSV files under `data/raw/` and 14 under `data/processed/`. They are Git data files, not Git LFS pointers. The current repository tree and notebook source cells do not contain a definition of `v_summary_base`.

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

## Official references

- [BigQuery VIEWS metadata and view_definition](https://docs.cloud.google.com/bigquery/docs/information-schema-views)
- [BigQuery data and query locations](https://docs.cloud.google.com/bigquery/docs/locations)
- [Edit or reconnect a Looker Studio data source](https://docs.cloud.google.com/data-studio/edit-the-data-source-connection)
- [Looker Studio data credentials](https://docs.cloud.google.com/data-studio/data-credentials)
