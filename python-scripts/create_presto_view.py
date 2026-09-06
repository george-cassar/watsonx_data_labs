"""
watsonx.data — Customer & Orders Tables + Presto-Native View
=============================================================
Creates two Iceberg tables in watsonx.data using Spark, then creates a live
Presto-native view over them using the prestodb Python client.

OVERVIEW
--------
Steps performed (in order):
  1. customers table    — drop if exists, create Iceberg table, insert 10 sample rows
  2. orders table       — drop if exists, create Iceberg table, insert 16 sample rows
  3. Presto-native view — drop if exists (4-layer strategy), CREATE VIEW via Presto
  4. Read-back          — query the view through the prestodb DBAPI client to confirm

WHY CREATE THE VIEW VIA PRESTO AND NOT SPARK?
---------------------------------------------
SQL views created by Spark (CREATE VIEW ... AS SELECT ...) are stored in Spark SQL
dialect inside the Hive metastore.  Presto cannot parse them — it raises:
  "Hive views are not supported: 'test.customers_active_vw'"
Creating the view through Presto stores it in Presto SQL dialect.  The view is
live — it always reflects the current state of the underlying Iceberg tables
without any periodic refresh job.

DROP STRATEGY (Step 3)
-----------------------
Four layers are applied unconditionally to handle any prior state:
  1. Presto  DROP VIEW  IF EXISTS  — removes a live Presto-native view.
  2. Presto  DROP TABLE IF EXISTS  — fallback for Hive-stored entries Presto
                                     surfaces as tables.
  3. Spark   DROP VIEW  IF EXISTS  — removes a legacy Spark/Hive SQL view stored
                                     in the metastore.  Required to prevent
                                     AlreadyExistsException on re-runs.
  4. Spark   DROP TABLE IF EXISTS  — removes any materialised Iceberg table from
                                     a previous version of this job.

PRESTO AUTHENTICATION (Basic Auth)
-----------------------------------
HTTP Basic Authentication over TLS.  Username and password are sent with every
request.  For watsonx.data on CPD the password is typically the ZenApiKey
(format: "ZenApiKey <base64>") or the CPD user password.

SPARK CONF KEYS (injected via payload — see create_presto_view_payload.json)
-----------------------------------------------------------------------------
Required:
  spark.hadoop.wxd.apikey  — CPD ZenApiKey for the Spark/Iceberg metastore
                             (env var: WXD_APIKEY, format: "ZenApiKey ...")
  spark.presto.host        — Presto engine hostname
  spark.presto.user        — Presto username (e.g. cpadmin)
  spark.presto.password    — Presto password

Optional (have defaults):
  spark.presto.port        — Presto port          (default: 443)
  spark.presto.catalog     — Iceberg catalog name  (default: lab_catalog01)
  spark.presto.schema      — Schema / database     (default: test)

PYTHON DEPENDENCY
-----------------
Requires the 'prestodb' package (presto-python-client).  If not pre-installed,
the job will pip-install it at runtime.  For production, pre-install once via
the watsonx.data library-set: customize_instance_app.py -> pip -> presto-python-client

PRE-REQUISITE
-------------
The schema referenced by SCHEMA must already exist in the catalog before this job
runs.  Create it via the watsonx.data console or Infrastructure Manager if needed.

RE-RUN BEHAVIOUR
----------------
All three objects (customers table, orders table, view) are dropped and recreated
on every run — the job is fully idempotent.

Date: 2026-09-06
Version: 2.002
"""

import subprocess
import sys
import traceback
import time
from datetime import datetime, date
from decimal import Decimal

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField,
    StringType, IntegerType, DateType, DecimalType,
)

# ============================================================================
# CONFIGURATION — Global Constants
# ============================================================================
CATALOG        = "lab_catalog01"
SCHEMA         = "test"
TABLE_CUSTOMER = "customers"
TABLE_ORDERS   = "orders"
VIEW_NAME      = "v_customers_active"

# Spark retry configuration for transient metastore HTTP 500 errors
RETRY_MAX_ATTEMPTS = 5
RETRY_BACKOFF_SECS = 3   # seconds between attempts (doubles each retry)

# Presto connection retry configuration
PRESTO_CONNECT_RETRIES = 3
PRESTO_CONNECT_BACKOFF = 5   # seconds between connection attempts

# ============================================================================
# SPARK SESSION
# ============================================================================

def create_spark_session() -> "SparkSession":
    """
    Create and return a SparkSession configured for watsonx.data Iceberg workloads.

    Configuration notes:
    - Iceberg extensions and Hive catalog are registered so Spark can read/write
      Iceberg tables stored in the watsonx.data metastore.
    - Adaptive Query Execution is enabled for better partition coalescing.
    - GC metric collector names are set to match the JVM in this environment
      (collectors report as 'scavenge'/'global') to prevent the warning:
        "To enable non-built-in garbage collector List(scavenge)"
    - UseCompressedOops is explicitly set on driver and executor to suppress
      the SizeEstimator warning:
        "Failed to check whether UseCompressedOops is set; assuming yes"
    - Resource allocation (memory, cores, executor count) is left out here —
      it is controlled via the JSON submission payload.
    """
    jvm_opts = "-XX:+UseCompressedOops"
    return (
        SparkSession.builder
        .appName("watsonx.data-Customer-Orders-Presto-View-Creator")
        # Enable Iceberg SQL extensions (MERGE INTO, ALTER TABLE, etc.)
        .config("spark.sql.extensions",
                "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
        # Register the watsonx.data Iceberg catalog backed by the Hive metastore
        .config(f"spark.sql.catalog.{CATALOG}", "org.apache.iceberg.spark.SparkCatalog")
        .config(f"spark.sql.catalog.{CATALOG}.type", "hive")
        # Hive metastore support (required for the Iceberg Hive catalog type)
        .enableHiveSupport()
        # Adaptive Query Execution — coalesces shuffle partitions automatically
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        # Suppress "To enable non-built-in garbage collector List(scavenge)" warning
        .config("spark.eventLog.gcMetrics.youngGenerationGarbageCollectors", "scavenge")
        .config("spark.eventLog.gcMetrics.oldGenerationGarbageCollectors", "global,scavenge")
        # Suppress "Failed to check whether UseCompressedOops is set" warning
        .config("spark.driver.extraJavaOptions",   jvm_opts)
        .config("spark.executor.extraJavaOptions", jvm_opts)
        .getOrCreate()
    )

# ============================================================================
# LOGGING HELPERS
# ============================================================================

def setup_logging(spark) -> object:
    """
    Configure log levels and return the application logger.

    Suppressions applied:
    - org.apache.hadoop.hive.metastore        -> ERROR
        Eliminates verbose Thrift/metastore connection chatter.
    - org.apache.iceberg.hive                 -> ERROR
        Eliminates Iceberg HMS INFO noise on every catalog operation.
    - org.apache.iceberg.ClientPoolImpl       -> ERROR
        Eliminates connection-pool INFO spam on every Iceberg call.
    - org.apache.spark.sql.execution          -> ERROR
        Suppresses watsonx.data MIRA WARN messages:
        "[MIRA] Tagging RDD / Not tagging class ..." printed at every stage.
    - org.apache.spark.sql.catalyst.rules     -> WARN
        Suppresses repeated INFO:
        "CombineJoinedAggregates: Merge Aggregate rule Injected"
        which fires twice per Spark action and adds noise with no diagnostic value.
    """
    spark.sparkContext.setLogLevel("INFO")

    log4j = spark._jvm.org.apache.log4j
    log4j.Logger.getLogger("org.apache.hadoop.hive.metastore").setLevel(log4j.Level.ERROR)
    log4j.Logger.getLogger("org.apache.iceberg.hive").setLevel(log4j.Level.ERROR)
    log4j.Logger.getLogger("org.apache.iceberg.ClientPoolImpl").setLevel(log4j.Level.ERROR)
    # Suppress watsonx.data MIRA query-tracking noise at every Spark stage
    log4j.Logger.getLogger("org.apache.spark.sql.execution").setLevel(log4j.Level.ERROR)
    # Suppress "CombineJoinedAggregates: Merge Aggregate rule Injected" INFO spam
    log4j.Logger.getLogger("org.apache.spark.sql.catalyst.rules").setLevel(log4j.Level.WARN)

    return log4j.LogManager.getLogger("CustomerOrdersPrestoViewCreator")


def log(logger, msg: str, level: str = "INFO"):
    """Log a timestamped message to both log4j and stdout."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{ts}] {msg}"
    if level == "INFO":
        logger.info(formatted)
    elif level == "WARN":
        logger.warn(formatted)
    elif level == "ERROR":
        logger.error(formatted)
    print(formatted)


def section(logger, title: str):
    """Print a clearly visible section banner to make logs easy to scan."""
    log(logger, "=" * 80)
    log(logger, f"  {title}")
    log(logger, "=" * 80)

# ============================================================================
# SPARK RETRY / METASTORE HELPERS
# ============================================================================

def is_transient_metastore_error(exc: Exception) -> bool:
    """Return True for transient Hive metastore errors worth retrying."""
    msg = str(exc)
    return (
        "HTTP Response code: 500" in msg
        or "TTransportException" in msg
        or "MetaStoreClient lost connection" in msg
    )


def sql_with_retry(spark, logger, sql: str, description: str):
    """
    Execute a Spark SQL statement with exponential-backoff retries on
    transient metastore HTTP 500 errors.  Returns collected rows on success.
    """
    backoff = RETRY_BACKOFF_SECS
    for attempt in range(1, RETRY_MAX_ATTEMPTS + 1):
        try:
            log(logger, f"    [attempt {attempt}/{RETRY_MAX_ATTEMPTS}] {description}")
            collected = spark.sql(sql).collect()
            return collected
        except Exception as exc:
            if attempt < RETRY_MAX_ATTEMPTS and is_transient_metastore_error(exc):
                log(logger,
                    f"    Transient metastore error on attempt {attempt} — "
                    f"retrying in {backoff}s... ({str(exc)[:120]})", "WARN")
                time.sleep(backoff)
                backoff *= 2
            else:
                raise


def object_exists(spark, logger, catalog: str, schema: str, name: str) -> bool:
    """Return True if *name* exists in SHOW TABLES for catalog.schema."""
    try:
        rows = sql_with_retry(
            spark, logger,
            f"SHOW TABLES IN {catalog}.{schema}",
            f"SHOW TABLES IN {catalog}.{schema}",
        )
        return name in [row.tableName for row in rows]
    except Exception as exc:
        log(logger,
            f"    Could not list tables — treating '{name}' as non-existent: "
            f"{str(exc)[:200]}", "WARN")
        return False


def drop_if_exists(spark, logger, catalog: str, schema: str, name: str,
                   object_type: str = "TABLE") -> None:
    """
    Drop a TABLE or VIEW via Spark SQL if it currently exists in the metastore.

    Parameters
    ----------
    spark       : active SparkSession
    logger      : log4j logger returned by setup_logging()
    catalog     : Iceberg catalog name (e.g. "lab_catalog01")
    schema      : schema / database name (e.g. "test")
    name        : unqualified object name (e.g. "customers")
    object_type : "TABLE" or "VIEW" — controls the DROP statement issued
    """
    if object_type not in ("TABLE", "VIEW"):
        raise ValueError(f"object_type must be 'TABLE' or 'VIEW', got '{object_type}'")

    full_name = f"{catalog}.{schema}.{name}"
    log(logger, f"  Checking whether {object_type.lower()} '{full_name}' already exists...")
    if object_exists(spark, logger, catalog, schema, name):
        log(logger, f"  '{full_name}' exists — dropping before recreation...", "WARN")
        sql_with_retry(
            spark, logger,
            f"DROP {object_type} IF EXISTS {full_name}",
            f"DROP {object_type} {full_name}",
        )
        log(logger, f"  ✓ '{full_name}' dropped successfully")
    else:
        log(logger, f"  '{full_name}' does not exist — no drop needed")

# ============================================================================
# STEP 1 — Customers table (Spark / Iceberg)
# ============================================================================

def create_customers_table(spark, logger) -> bool:
    """Drop (if exists) and recreate the Iceberg customers table with sample data."""
    full_table = f"{CATALOG}.{SCHEMA}.{TABLE_CUSTOMER}"

    section(logger, f"STEP 1 — Customers Table  ({full_table})")
    log(logger, f"  Catalog      : {CATALOG}")
    log(logger, f"  Schema       : {SCHEMA}")
    log(logger, f"  Table        : {TABLE_CUSTOMER}")
    log(logger, f"  Max retries  : {RETRY_MAX_ATTEMPTS}")
    log(logger, f"  Retry backoff: {RETRY_BACKOFF_SECS}s (doubles each attempt)")

    # --- Drop if exists ---
    try:
        drop_if_exists(spark, logger, CATALOG, SCHEMA, TABLE_CUSTOMER, "TABLE")
    except Exception as e:
        log(logger, f"  ERROR: Could not drop existing customers table: {str(e)}", "ERROR")
        log(logger, traceback.format_exc(), "ERROR")
        return False

    # --- Create table ---
    log(logger, f"  Creating Iceberg table '{full_table}'...")
    try:
        start_time = time.time()
        sql_with_retry(spark, logger, f"""
            CREATE TABLE {full_table} (
                customer_id     INT     NOT NULL,
                first_name      STRING,
                last_name       STRING,
                email           STRING,
                phone           STRING,
                country         STRING,
                account_status  STRING  NOT NULL,
                credit_limit    DECIMAL(12, 2),
                joined_date     DATE
            )
            USING iceberg
            TBLPROPERTIES (
                'write.format.default'             = 'parquet',
                'write.parquet.compression-codec'  = 'snappy'
            )
        """, f"CREATE TABLE {full_table}")
        log(logger, f"  ✓ Table '{full_table}' created in {time.time() - start_time:.2f} seconds")
    except Exception as e:
        log(logger, "  ERROR: Failed to create customers table", "ERROR")
        log(logger, f"  Error Message: {str(e)}", "ERROR")
        log(logger, traceback.format_exc(), "ERROR")
        _log_troubleshooting(logger, include_table_hint=False)
        return False

    # --- Insert sample data ---
    log(logger, f"  Inserting sample customer rows into '{full_table}'...")
    try:
        start_time = time.time()

        data_schema = StructType([
            StructField("customer_id",    IntegerType(),      nullable=False),
            StructField("first_name",     StringType(),       nullable=False),
            StructField("last_name",      StringType(),       nullable=False),
            StructField("email",          StringType(),       nullable=True),
            StructField("phone",          StringType(),       nullable=True),
            StructField("country",        StringType(),       nullable=True),
            StructField("account_status", StringType(),       nullable=False),
            StructField("credit_limit",   DecimalType(12, 2), nullable=True),
            StructField("joined_date",    DateType(),         nullable=True),
        ])

        sample_data = [
            (1,  "Alice",   "Johnson",  "alice.johnson@example.com",  "+1-555-0101", "US", "ACTIVE",    Decimal("5000.00"),  date(2021, 3, 15)),
            (2,  "Bob",     "Smith",    "bob.smith@example.com",      "+1-555-0102", "US", "ACTIVE",    Decimal("7500.00"),  date(2020, 7, 22)),
            (3,  "Carlos",  "Martinez", "carlos.m@example.com",       "+34-600-001", "ES", "INACTIVE",  Decimal("2500.00"),  date(2019, 11, 5)),
            (4,  "Diana",   "Chen",     "diana.chen@example.com",     "+44-700-002", "GB", "ACTIVE",    Decimal("12000.00"), date(2022, 1, 30)),
            (5,  "Ethan",   "Brown",    "ethan.b@example.com",        "+1-555-0105", "US", "SUSPENDED", Decimal("1000.00"),  date(2018, 6, 18)),
            (6,  "Fatima",  "Ali",      "fatima.ali@example.com",     "+971-50-001", "AE", "ACTIVE",    Decimal("9000.00"),  date(2023, 4, 10)),
            (7,  "George",  "Taylor",   "george.t@example.com",       "+61-400-001", "AU", "ACTIVE",    Decimal("6500.00"),  date(2021, 9, 3)),
            (8,  "Hannah",  "Wilson",   "hannah.w@example.com",       "+49-170-001", "DE", "INACTIVE",  Decimal("3000.00"),  date(2017, 12, 1)),
            (9,  "Ivan",    "Petrov",   "ivan.petrov@example.com",    "+7-900-0001", "RU", "ACTIVE",    Decimal("4500.00"),  date(2022, 8, 25)),
            (10, "Julia",   "Nguyen",   "julia.nguyen@example.com",   "+84-90-0001", "VN", "ACTIVE",    Decimal("8000.00"),  date(2023, 2, 14)),
        ]

        log(logger, f"  Building DataFrame with {len(sample_data)} customer rows...")
        df = spark.createDataFrame(sample_data, schema=data_schema)

        backoff = RETRY_BACKOFF_SECS
        for attempt in range(1, RETRY_MAX_ATTEMPTS + 1):
            try:
                log(logger, f"    [attempt {attempt}/{RETRY_MAX_ATTEMPTS}] writeTo {full_table}")
                df.writeTo(full_table).append()
                break
            except Exception as exc:
                if attempt < RETRY_MAX_ATTEMPTS and is_transient_metastore_error(exc):
                    log(logger,
                        f"    Transient error on write attempt {attempt} — "
                        f"retrying in {backoff}s... ({str(exc)[:120]})", "WARN")
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    raise

        log(logger, f"  ✓ Inserted {len(sample_data)} customer rows in {time.time() - start_time:.2f} seconds")
        log(logger, "  Customers table schema:")
        log(logger, df._jdf.schema().treeString())
        log(logger, "  Customers table contents:")
        spark.sql(f"SELECT * FROM {full_table} ORDER BY customer_id").show(truncate=False)

    except Exception as e:
        log(logger, "  ERROR: Failed to insert data into customers table", "ERROR")
        log(logger, f"  Error Message: {str(e)}", "ERROR")
        log(logger, traceback.format_exc(), "ERROR")
        return False

    return True

# ============================================================================
# STEP 2 — Orders table (Spark / Iceberg)
# ============================================================================

def create_orders_table(spark, logger) -> bool:
    """Drop (if exists) and recreate the Iceberg orders table with sample data."""
    full_table = f"{CATALOG}.{SCHEMA}.{TABLE_ORDERS}"

    section(logger, f"STEP 2 — Orders Table  ({full_table})")
    log(logger, f"  Catalog      : {CATALOG}")
    log(logger, f"  Schema       : {SCHEMA}")
    log(logger, f"  Table        : {TABLE_ORDERS}")
    log(logger, f"  Max retries  : {RETRY_MAX_ATTEMPTS}")
    log(logger, f"  Retry backoff: {RETRY_BACKOFF_SECS}s (doubles each attempt)")

    # --- Drop if exists ---
    try:
        drop_if_exists(spark, logger, CATALOG, SCHEMA, TABLE_ORDERS, "TABLE")
    except Exception as e:
        log(logger, f"  ERROR: Could not drop existing orders table: {str(e)}", "ERROR")
        log(logger, traceback.format_exc(), "ERROR")
        return False

    # --- Create table ---
    log(logger, f"  Creating Iceberg table '{full_table}'...")
    try:
        start_time = time.time()
        sql_with_retry(spark, logger, f"""
            CREATE TABLE {full_table} (
                order_id        INT     NOT NULL,
                customer_id     INT     NOT NULL,
                order_date      DATE    NOT NULL,
                order_status    STRING  NOT NULL,
                total_amount    DECIMAL(12, 2),
                currency        STRING
            )
            USING iceberg
            TBLPROPERTIES (
                'write.format.default'             = 'parquet',
                'write.parquet.compression-codec'  = 'snappy'
            )
        """, f"CREATE TABLE {full_table}")
        log(logger, f"  ✓ Table '{full_table}' created in {time.time() - start_time:.2f} seconds")
    except Exception as e:
        log(logger, "  ERROR: Failed to create orders table", "ERROR")
        log(logger, f"  Error Message: {str(e)}", "ERROR")
        log(logger, traceback.format_exc(), "ERROR")
        _log_troubleshooting(logger, include_table_hint=False)
        return False

    # --- Insert sample data ---
    log(logger, f"  Inserting sample order rows into '{full_table}'...")
    try:
        start_time = time.time()

        data_schema = StructType([
            StructField("order_id",      IntegerType(),      nullable=False),
            StructField("customer_id",   IntegerType(),      nullable=False),
            StructField("order_date",    DateType(),         nullable=False),
            StructField("order_status",  StringType(),       nullable=False),
            StructField("total_amount",  DecimalType(12, 2), nullable=True),
            StructField("currency",      StringType(),       nullable=True),
        ])

        # Each ACTIVE customer has at least one order.  INACTIVE/SUSPENDED
        # customers have orders too — they are stored for completeness but
        # will be excluded from the view by the account_status filter.
        sample_data = [
            (1001, 1,  date(2024, 1, 10), "COMPLETED", Decimal("250.00"),  "USD"),
            (1002, 1,  date(2024, 3, 22), "COMPLETED", Decimal("89.99"),   "USD"),
            (1003, 2,  date(2024, 2, 14), "COMPLETED", Decimal("1200.00"), "USD"),
            (1004, 2,  date(2024, 4, 5),  "PENDING",   Decimal("450.50"),  "USD"),
            (1005, 3,  date(2023, 12, 1), "COMPLETED", Decimal("320.00"),  "EUR"),
            (1006, 4,  date(2024, 1, 28), "COMPLETED", Decimal("780.00"),  "GBP"),
            (1007, 4,  date(2024, 5, 17), "SHIPPED",   Decimal("199.99"),  "GBP"),
            (1008, 5,  date(2023, 11, 9), "CANCELLED", Decimal("60.00"),   "USD"),
            (1009, 6,  date(2024, 3, 3),  "COMPLETED", Decimal("3400.00"), "AED"),
            (1010, 6,  date(2024, 6, 1),  "PENDING",   Decimal("500.00"),  "AED"),
            (1011, 7,  date(2024, 2, 20), "COMPLETED", Decimal("675.00"),  "AUD"),
            (1012, 8,  date(2023, 10, 15),"COMPLETED", Decimal("215.00"),  "EUR"),
            (1013, 9,  date(2024, 4, 11), "COMPLETED", Decimal("940.00"),  "USD"),
            (1014, 9,  date(2024, 5, 30), "SHIPPED",   Decimal("310.00"),  "USD"),
            (1015, 10, date(2024, 1, 7),  "COMPLETED", Decimal("1850.00"), "USD"),
            (1016, 10, date(2024, 6, 12), "PENDING",   Decimal("220.00"),  "USD"),
        ]

        log(logger, f"  Building DataFrame with {len(sample_data)} order rows...")
        df_orders = spark.createDataFrame(sample_data, schema=data_schema)

        backoff = RETRY_BACKOFF_SECS
        for attempt in range(1, RETRY_MAX_ATTEMPTS + 1):
            try:
                log(logger, f"    [attempt {attempt}/{RETRY_MAX_ATTEMPTS}] writeTo {full_table}")
                df_orders.writeTo(full_table).append()
                break
            except Exception as exc:
                if attempt < RETRY_MAX_ATTEMPTS and is_transient_metastore_error(exc):
                    log(logger,
                        f"    Transient error on write attempt {attempt} — "
                        f"retrying in {backoff}s... ({str(exc)[:120]})", "WARN")
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    raise

        log(logger, f"  ✓ Inserted {len(sample_data)} order rows in {time.time() - start_time:.2f} seconds")
        log(logger, "  Orders table schema:")
        log(logger, df_orders._jdf.schema().treeString())
        log(logger, "  Orders table contents:")
        spark.sql(f"SELECT * FROM {full_table} ORDER BY order_id").show(truncate=False)

    except Exception as e:
        log(logger, "  ERROR: Failed to insert data into orders table", "ERROR")
        log(logger, f"  Error Message: {str(e)}", "ERROR")
        log(logger, traceback.format_exc(), "ERROR")
        return False

    return True

# ============================================================================
# STEP 3 — Presto-native view
# ============================================================================

def ensure_prestodb(logger) -> bool:
    """
    Verify that the 'prestodb' package is importable.  If not, attempt a
    runtime pip install.

    For production use, pre-install via the watsonx.data library-set mechanism
    (customize_instance_app.py → pip → presto-python-client) so this install
    step is skipped on every run.
    """
    try:
        import prestodb  # noqa: F401
        log(logger, "  ✓ prestodb package is already available")
        return True
    except ImportError:
        pass

    log(logger, "  prestodb not found — attempting runtime pip install...", "WARN")
    log(logger, "  Tip: pre-install via the watsonx.data library-set to avoid this.", "WARN")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", "presto-python-client"],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            log(logger, f"  pip install failed:\n{result.stderr}", "ERROR")
            return False
        import prestodb  # noqa: F401
        log(logger, "  ✓ prestodb installed and imported successfully")
        return True
    except Exception as exc:
        log(logger, f"  Failed to install prestodb: {str(exc)}", "ERROR")
        return False


def read_presto_config(spark, logger) -> dict:
    """
    Read Presto connection parameters injected via the payload conf block.
    Raises ValueError if a required key is absent.
    """
    conf = spark.sparkContext.getConf()

    def require(key: str) -> str:
        val = conf.get(key, "")
        if not val:
            raise ValueError(
                f"Missing required Spark conf property '{key}'. "
                f"Add it to the payload conf block."
            )
        return val

    cfg = {
        "host":     require("spark.presto.host"),
        "port":     int(conf.get("spark.presto.port", "443")),
        "user":     require("spark.presto.user"),
        "password": require("spark.presto.password"),
        "catalog":  conf.get("spark.presto.catalog", CATALOG),
        "schema":   conf.get("spark.presto.schema",  SCHEMA),
    }

    log(logger, f"  Presto host    : {cfg['host']}")
    log(logger, f"  Presto port    : {cfg['port']}")
    log(logger, f"  Presto user    : {cfg['user']}")
    log(logger, f"  Presto password: {'*' * 8}{cfg['password'][-4:]}  (masked)")
    log(logger, f"  Presto catalog : {cfg['catalog']}")
    log(logger, f"  Presto schema  : {cfg['schema']}")
    return cfg


def open_presto_connection(cfg: dict, logger):
    """
    Open a verified HTTPS DBAPI connection to Presto using username / password
    Basic Authentication.

    Authentication method: HTTP Basic Auth (username + password over TLS).
    For watsonx.data on CPD the password is typically the ZenApiKey
    (format: "ZenApiKey <base64>") or the CPD user password.
    """
    import prestodb
    from prestodb.auth import BasicAuthentication

    backoff  = PRESTO_CONNECT_BACKOFF
    last_exc = None

    log(logger, f"  Connecting as user '{cfg['user']}' (Basic Auth) ...")

    for attempt in range(1, PRESTO_CONNECT_RETRIES + 1):
        try:
            log(logger, f"  [attempt {attempt}/{PRESTO_CONNECT_RETRIES}] "
                        f"Connecting to Presto at {cfg['host']}:{cfg['port']}...")
            conn = prestodb.dbapi.connect(
                host=cfg["host"],
                port=cfg["port"],
                user=cfg["user"],
                auth=BasicAuthentication(cfg["user"], cfg["password"]),
                http_scheme="https",
                catalog=cfg["catalog"],
                schema=cfg["schema"],
                verify=True,
            )
            # Verify the connection is alive with a lightweight query
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchone()
            log(logger, "  ✓ Presto connection established and verified (Basic Auth)")
            return conn
        except Exception as exc:
            last_exc = exc
            if attempt < PRESTO_CONNECT_RETRIES:
                log(logger,
                    f"  Connection attempt {attempt} failed — retrying in {backoff}s... "
                    f"({str(exc)[:120]})", "WARN")
                time.sleep(backoff)
                backoff *= 2
            else:
                raise RuntimeError(
                    f"Could not connect to Presto after {PRESTO_CONNECT_RETRIES} attempts. "
                    f"Last error: {str(last_exc)}"
                ) from last_exc


def create_presto_view(spark, conn, logger, catalog: str, schema: str) -> bool:
    """
    Drop any existing view/table under VIEW_NAME (via both Presto and Spark to
    cover all legacy cases), then create a Presto-native view joining active
    customers with their orders.

    DROP strategy:
      1. Presto  DROP VIEW  IF EXISTS  — removes a Presto-native view.
      2. Presto  DROP TABLE IF EXISTS  — fallback for Hive-stored view entries
                                         that Presto exposes as tables.
      3. Spark   DROP VIEW  IF EXISTS  — removes any Spark/Hive SQL view stored
                                         in the metastore (the legacy case that
                                         triggered AlreadyExistsException).
      4. Spark   DROP TABLE IF EXISTS  — removes any materialised Iceberg table
                                         written by the previous version of this
                                         job.
    """
    full_view      = f"{catalog}.{schema}.{VIEW_NAME}"
    full_customers = f"{catalog}.{schema}.{TABLE_CUSTOMER}"
    full_orders    = f"{catalog}.{schema}.{TABLE_ORDERS}"

    section(logger, f"STEP 3 — Presto-Native View  ({full_view})")
    log(logger, f"  Source tables  : {full_customers}")
    log(logger, f"                   {full_orders}")
    log(logger, f"  View name      : {full_view}")
    log(logger,  "  Filter         : account_status = 'ACTIVE' customers only")
    log(logger,  "  Implementation : Presto SQL dialect — live, no refresh needed")

    # -----------------------------------------------------------------------
    # Layer 1 & 2 — Drop via Presto
    # Handles a live Presto-native view (layer 1) and any Hive-stored entry
    # that Presto surfaces as a table (layer 2 fallback).
    # -----------------------------------------------------------------------
    log(logger, "  Dropping any existing view via Presto (layers 1 & 2)...")
    cur = conn.cursor()
    try:
        cur.execute(f"DROP VIEW IF EXISTS {full_view}")
        log(logger, "  ✓ Presto DROP VIEW IF EXISTS completed")
    except Exception as exc:
        log(logger,
            f"  DROP VIEW raised an error — trying DROP TABLE fallback: "
            f"{str(exc)[:120]}", "WARN")
        try:
            cur.execute(f"DROP TABLE IF EXISTS {full_view}")
            log(logger, "  ✓ Presto DROP TABLE IF EXISTS fallback completed")
        except Exception as exc2:
            log(logger, f"  ERROR: Presto drop failed: {str(exc2)}", "ERROR")
            return False

    # -----------------------------------------------------------------------
    # Layer 3 & 4 — Drop via Spark
    # Clears any Spark/Iceberg metastore registration for the same name.
    # Prevents AlreadyExistsException when the name was previously a Spark SQL
    # view (layer 3) or a materialised Iceberg table from an older run (layer 4).
    # -----------------------------------------------------------------------
    log(logger, f"  Clearing any Spark/Iceberg registration for '{full_view}' (layers 3 & 4)...")
    try:
        sql_with_retry(spark, logger,
                       f"DROP VIEW IF EXISTS {full_view}",
                       f"DROP VIEW IF EXISTS {full_view}")
        log(logger, "  ✓ Spark DROP VIEW IF EXISTS completed")
    except Exception as exc:
        log(logger,
            f"  Spark DROP VIEW raised an error (non-fatal): {str(exc)[:120]}", "WARN")

    try:
        drop_if_exists(spark, logger, catalog, schema, VIEW_NAME, "TABLE")
    except Exception as exc:
        log(logger,
            f"  Spark DROP TABLE raised an error (non-fatal): {str(exc)[:120]}", "WARN")

    # -----------------------------------------------------------------------
    # Create the Presto-native view
    # The SQL is stored in Presto dialect — fully readable by Presto without
    # any cross-engine compatibility issues.
    # -----------------------------------------------------------------------
    log(logger, f"  Creating Presto-native view '{full_view}'...")
    view_sql = f"""
        CREATE VIEW {full_view} AS
        SELECT
            c.customer_id,
            c.first_name,
            c.last_name,
            c.email,
            c.country,
            c.credit_limit,
            c.joined_date,
            o.order_id,
            o.order_date,
            o.order_status,
            o.total_amount  AS order_amount,
            o.currency      AS order_currency
        FROM {full_customers} c
        JOIN {full_orders} o
          ON c.customer_id = o.customer_id
        WHERE c.account_status = 'ACTIVE'
    """
    try:
        start = time.time()
        # Reuse the existing cursor — no need to open a new one
        cur.execute(view_sql)
        log(logger, f"  ✓ View '{full_view}' created in {time.time() - start:.2f} seconds")
    except Exception as exc:
        log(logger, f"  ERROR: Failed to create view: {str(exc)}", "ERROR")
        log(logger, traceback.format_exc(), "ERROR")
        _log_troubleshooting(logger, include_table_hint=True)
        return False

    # -----------------------------------------------------------------------
    # Verify — lightweight query to confirm the view is immediately readable.
    # Non-fatal: CREATE succeeded even if this check raises an exception.
    # -----------------------------------------------------------------------
    log(logger, f"  Verifying view by querying '{full_view}'...")
    try:
        cur.execute(f"SELECT COUNT(*) FROM {full_view}")
        row_count = cur.fetchone()[0]
        log(logger, f"  ✓ View is queryable — {row_count} rows returned")

        cur.execute(
            f"SELECT * FROM {full_view} ORDER BY customer_id, order_id LIMIT 5"
        )
        rows      = cur.fetchall()
        col_names = [d[0] for d in cur.description]
        log(logger, f"  Preview (first {len(rows)} rows):")
        log(logger, f"    {' | '.join(col_names)}")
        log(logger, f"    {'-' * 80}")
        for r in rows:
            log(logger, f"    {' | '.join(str(v) for v in r)}")
    except Exception as exc:
        log(logger, f"  Could not verify view (non-fatal): {str(exc)}", "WARN")

    return True

# ============================================================================
# STEP 4 — Read back the view via Presto (confirms Spark cannot, Presto can)
# ============================================================================

def read_view_via_presto(conn, logger, catalog: str, schema: str) -> bool:
    """
    Read all rows from the Presto-native view using the already-open prestodb
    connection and display them in a formatted table in the logs.

    WHY NOT spark.table() OR spark.sql()?
    --------------------------------------
    Spark cannot read a Presto-native view directly.  The view is stored in
    Presto SQL dialect inside the Hive metastore.  If you call:
        spark.table("lab_catalog01.test.v_customers_active")
    Spark will raise an AnalysisException because it cannot parse the view's
    stored SQL.  The only correct way to read a Presto-native view from inside
    a Spark job is to route the query back through Presto — either via the
    prestodb DBAPI client (used here) or via Spark's JDBC connector pointed at
    Presto.  This step uses the existing prestodb connection, which is already
    open and verified, so no extra configuration is needed.
    """
    full_view = f"{catalog}.{schema}.{VIEW_NAME}"

    section(logger, f"STEP 4 — Read Presto View via prestodb Client  ({full_view})")
    log(logger,  "  Engine  : Presto (routing through the prestodb DBAPI connection)")
    log(logger,  "  Note    : spark.table() / spark.sql() cannot read Presto-native")
    log(logger,  "            views — the query must be routed through Presto itself.")

    try:
        cur = conn.cursor()

        # --- Row count --------------------------------------------------------
        log(logger, f"  Executing: SELECT COUNT(*) FROM {full_view}")
        cur.execute(f"SELECT COUNT(*) FROM {full_view}")
        total_rows = cur.fetchone()[0]
        log(logger, f"  ✓ View contains {total_rows} rows")

        # --- Full result set --------------------------------------------------
        log(logger, f"  Executing: SELECT * FROM {full_view} ORDER BY customer_id, order_id")
        cur.execute(
            f"SELECT * FROM {full_view} ORDER BY customer_id, order_id"
        )
        rows = cur.fetchall()
        col_names = [d[0] for d in cur.description]

        # Compute column widths for aligned output
        col_widths = [len(c) for c in col_names]
        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val) if val is not None else "NULL"))

        sep  = "+-" + "-+-".join("-" * w for w in col_widths) + "-+"
        hdr  = "| " + " | ".join(c.ljust(col_widths[i]) for i, c in enumerate(col_names)) + " |"

        log(logger, f"  View contents ({len(rows)} rows):")
        log(logger, f"  {sep}")
        log(logger, f"  {hdr}")
        log(logger, f"  {sep}")
        for row in rows:
            line = "| " + " | ".join(
                str(v if v is not None else "NULL").ljust(col_widths[i])
                for i, v in enumerate(row)
            ) + " |"
            log(logger, f"  {line}")
        log(logger, f"  {sep}")
        log(logger, f"  ✓ All {len(rows)} rows displayed successfully")

    except Exception as exc:
        log(logger, f"  ERROR: Failed to read view via Presto: {str(exc)}", "ERROR")
        log(logger, traceback.format_exc(), "ERROR")
        return False

    return True

# ============================================================================
# SHARED HELPERS
# ============================================================================

def _log_troubleshooting(logger, include_table_hint: bool = False) -> None:
    """
    Emit a numbered troubleshooting checklist at ERROR level.

    Called after catching an unexpected exception so that the person reading
    the Spark driver log gets actionable next steps without digging through
    the full stack trace first.

    Parameters
    ----------
    logger             : log4j logger returned by setup_logging()
    include_table_hint : when True, adds a hint about verifying that the source
                         tables exist (relevant for Step 3 / view creation failures).
    """
    log(logger, "  TROUBLESHOOTING STEPS:", "ERROR")
    log(logger, f"  1. Verify catalog '{CATALOG}' is associated with your Spark engine", "ERROR")
    log(logger, f"  2. Confirm schema '{SCHEMA}' exists in catalog '{CATALOG}'", "ERROR")
    if include_table_hint:
        log(logger, f"  3. Ensure tables '{TABLE_CUSTOMER}' and '{TABLE_ORDERS}' exist in schema '{SCHEMA}'", "ERROR")
        log(logger,  "  4. Check Spark engine status in Infrastructure Manager", "ERROR")
        log(logger,  "  5. Verify Presto host, port, user, and password in the payload conf", "ERROR")
        log(logger,  "  6. Review Spark driver logs for additional details", "ERROR")
    else:
        log(logger,  "  3. Check Spark engine status in Infrastructure Manager", "ERROR")
        log(logger,  "  4. Verify you have write permissions on the catalog", "ERROR")
        log(logger,  "  5. Review Spark driver logs for additional details", "ERROR")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """
    Main execution — initialise Spark, create tables via Spark/Iceberg,
    connect to Presto, create the view, then read it back via Presto.
    """
    spark  = None
    logger = None
    conn   = None

    try:
        print("=" * 80)
        print("  watsonx.data Customer & Orders Tables + Presto-Native View — starting up")
        print("=" * 80)
        print("Initialising Spark session...")

        spark  = create_spark_session()
        logger = setup_logging(spark)

        log(logger, "Spark session initialised successfully")
        log(logger, f"  Spark Version  : {spark.version}")
        log(logger, f"  Application ID : {spark.sparkContext.applicationId}")

        section(logger, "JOB CONFIGURATION")
        log(logger, f"  Catalog            : {CATALOG}")
        log(logger, f"  Schema             : {SCHEMA}")
        log(logger, f"  Customers table    : {TABLE_CUSTOMER}")
        log(logger, f"  Orders table       : {TABLE_ORDERS}")
        log(logger, f"  View               : {VIEW_NAME}  (Presto-native, live)")
        log(logger, f"  Retry max attempts : {RETRY_MAX_ATTEMPTS}")
        log(logger, f"  Retry backoff      : {RETRY_BACKOFF_SECS}s (doubles per attempt)")
        log(logger,  "  Re-run behaviour   : all objects dropped and recreated on every run")

        overall_start = time.time()

        # ---- Step 1: customers table -----------------------------------------
        log(logger, "")
        log(logger, "Starting Step 1: customers table...")
        if not create_customers_table(spark, logger):
            log(logger, "✗ Job failed at Step 1 (customers table). Aborting.", "ERROR")
            return 1
        log(logger, "Step 1 complete ✓")

        # ---- Step 2: orders table --------------------------------------------
        log(logger, "")
        log(logger, "Starting Step 2: orders table...")
        if not create_orders_table(spark, logger):
            log(logger, "✗ Job failed at Step 2 (orders table). Aborting.", "ERROR")
            return 1
        log(logger, "Step 2 complete ✓")

        # ---- Step 3: Presto-native view --------------------------------------
        log(logger, "")
        log(logger, "Starting Step 3: Presto-native view...")

        # 3a — Ensure prestodb is importable
        section(logger, "STEP 3a — Dependency Check: prestodb package")
        if not ensure_prestodb(logger):
            log(logger, "✗ prestodb unavailable — cannot create Presto view.", "ERROR")
            log(logger, "  Pre-install: customize_instance_app.py → pip → presto-python-client", "ERROR")
            return 1

        # 3b — Read and log Presto connection configuration
        section(logger, "STEP 3b — Presto Connection Configuration")
        cfg = read_presto_config(spark, logger)

        # 3c — Open connection to Presto
        section(logger, "STEP 3c — Connecting to Presto")
        conn = open_presto_connection(cfg, logger)

        # 3d — Drop legacy objects and create the view
        if not create_presto_view(spark, conn, logger, cfg["catalog"], cfg["schema"]):
            log(logger, "✗ Job failed at Step 3 (Presto view). Aborting.", "ERROR")
            return 1
        log(logger, "Step 3 complete ✓")

        # ---- Step 4: read view back via Presto --------------------------------
        log(logger, "")
        log(logger, "Starting Step 4: read Presto view via prestodb client...")
        if not read_view_via_presto(conn, logger, cfg["catalog"], cfg["schema"]):
            log(logger, "✗ Job failed at Step 4 (read view). Aborting.", "ERROR")
            return 1
        log(logger, "Step 4 complete ✓")

        # ---- Summary ---------------------------------------------------------
        overall_elapsed = time.time() - overall_start
        section(logger, "JOB SUMMARY")
        log(logger, f"  ✓ Customers table : {CATALOG}.{SCHEMA}.{TABLE_CUSTOMER}")
        log(logger, f"  ✓ Orders table    : {CATALOG}.{SCHEMA}.{TABLE_ORDERS}")
        log(logger, f"  ✓ Presto view     : {cfg['catalog']}.{cfg['schema']}.{VIEW_NAME}")
        log(logger,  "    Stored as Presto SQL dialect — live, readable by Presto natively")
        log(logger,  "    Read back confirmed via prestodb DBAPI client")
        log(logger, f"  Total elapsed     : {overall_elapsed:.2f} seconds")
        log(logger,  "  Job completed successfully")
        return 0

    except Exception as exc:
        if logger:
            log(logger, f"✗ Fatal error: {str(exc)}", "ERROR")
            log(logger, traceback.format_exc(), "ERROR")
        else:
            print(f"Fatal error: {str(exc)}")
            print(traceback.format_exc())
        return 1

    finally:
        if conn:
            try:
                conn.close()
                if logger:
                    log(logger, "✓ Presto connection closed")
            except Exception:
                pass
        if spark:
            msg = "Stopping Spark session..."
            if logger:
                log(logger, msg)
            else:
                print(msg)
            spark.stop()
            msg = "✓ Spark session stopped"
            if logger:
                log(logger, msg)
            else:
                print(msg)


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
