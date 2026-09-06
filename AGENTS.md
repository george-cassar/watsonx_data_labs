# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project Overview

This is a **documentation + scripts** repository for IBM watsonx.data hands-on training labs. There is no build system, no package manager at the root, and no test runner. The primary artifacts are:

- **`LAB0X_*.md`** — Lab instruction documents (10 labs)
- **`python-scripts/`** — PySpark jobs and Python/Presto integration scripts
- **`unix-scripts/`** — Bash scripts for Spark custom runtime image workflows
- **`jupyter_notebooks/`** — Jupyter notebooks for lab demos
- **`sample_data/`** — Retail datasets in CSV and Parquet formats
- **`postgresdb/`** — PostgreSQL setup for third-party integration labs

## No Build / Test Commands

There are no `npm`, `pip`, `make`, `pytest`, or equivalent commands at the root. Scripts are submitted directly to watsonx.data via its API or web console — they are not run locally.

## PySpark Script Conventions (python-scripts/)

- **Resource allocation is NOT in Python code** — driver/executor memory, cores, and instance count belong only in the companion `.json` payload file. Do not add `spark.driver.memory` or similar to `SparkSession.builder`.
- **Spark job submission JSON** pairs with each `.py` file (e.g., `customer_analysis.py` + `customer_analysis.json`). The JSON must specify `"application"` path as the **mount path** (e.g., `/mnts/python-scripts/customer_analysis.py`), not a local path.
- **API key** in JSON payloads uses the format `"ZenApiKey XXXX"` — the prefix `ZenApiKey` is required, it is not a Bearer/Basic token.
- **Volume mount name** format in job JSON: `"cpd::<storage-name>"` or `"ibm-hub::<storage-name>"` — these are platform-specific identifiers, not Docker volume names.
- **Catalog constant** used across all scripts is `"lab_catalog01"`. Lab 10's `create_presto_view.py` uses schema `"test"` (not `"retail"` or `"analytics"`) within the same catalog.
- **Iceberg client-pool cache must be disabled** in all job payloads: `"spark.sql.catalog.iceberg_data.client-pool-cache-enabled": "false"`.
- **Logging pattern**: All PySpark scripts use a `log(logger, msg, level)` helper that writes to both `log4j` and `stdout`. Use this pattern — don't use plain `print()` except during `spark=None` fallback.
- **Exit codes**: All `main()` functions return `int` (0/1) and call `exit(exit_code)` at module level.
- **SparkSession** must always include `.enableHiveSupport()` and the Iceberg extensions config for metastore access to work.

## Python Presto Client (python-scripts/bi-reporting/)

- Uses `presto-python-client==0.8.4` (package `prestodb`), **not** `pyhive` or `sqlalchemy`.
- Connection requires `PRESTO_PORT=8443` and `PRESTO_USE_SSL=true` by default.
- `PrestoConnection` in [`presto_connection.py`](python-scripts/bi-reporting/presto_connection.py) is the shared connection wrapper for all BI scripts — do not create raw `prestodb.dbapi.connect()` calls in other scripts.
- Configuration via `.env` file (copy from `.env.template`); never hardcode credentials.

## Spark and Presto SQL View Compatibility (Lab 10)

- **SQL views are NOT cross-engine**: A view created by Spark cannot be queried by Presto and vice versa. Presto raises `"Hive views are not supported"` on Spark-created views.
- **Iceberg tables ARE cross-engine**: Both engines share the same Hive metastore and can read the same Iceberg table files. The limitation is the SQL dialect stored in view definitions.
- The workaround in `create_presto_view.py` is to connect to Presto from inside a Spark application (via `prestodb` Python client) and issue the `CREATE VIEW` there so the view is Presto-native.

## Custom Spark Runtime Image Workflow (unix-scripts/)

- Scripts must be run from the **`unix-scripts/`** directory; they reference `./Dockerfile`, `./install-*.sh` relative to CWD.
- Run `setup-environment.sh` first — it auto-detects base image from the `spark-hb-cluster-template` ConfigMap in the OpenShift namespace and generates `.env.spark-custom-runtime`.
- Supported Spark versions via ConfigMap keys: `os-image-id-jkg35-cp4d-wxd` (3.5, recommended), `os-image-id-jkg40-cp4d-wxd` (4.0), `os-image-id-jkg34-cp4d-wxd` (3.4, deprecated).
- `build-and-push.sh` detects Podman or Docker automatically (Podman takes precedence).
- After building, set `"ae.spark.kubernetes.container.image"` in the job conf JSON — this is a watsonx.data-specific key, not a standard Spark conf.

## Key Gotchas

- **`.env.spark-custom-runtime`** is gitignored but required by `build-and-push.sh`. Always run `setup-environment.sh` in a new checkout before running `build-and-push.sh`.
- Spark version `3.4` is deprecated in the platform — default to `3.5` in new job JSON payloads.
- `sample_data/` CSV/Parquet files use a retail schema: `customers`, `orders`, `products`, `sales_transactions`. Key join: `orders.customer_id → customers.customer_id`, `orders.product_id → products.product_id`.
