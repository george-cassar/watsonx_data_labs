# Lab 10: Spark and Presto SQL View Compatibility

**Duration:** 60 minutes  
**Difficulty:** Advanced  
**Prerequisites:** Completion of Labs 6 and 8, access to Spark and Presto engines, and permission to create objects in the `lab_catalog01.test` schema  
**Last Updated:** September 2026

---

## Lab Objectives

By the end of this lab, you will be able to:

- Explain why Spark and Presto cannot query each other's SQL views
- Distinguish SQL view compatibility from Iceberg table compatibility
- Evaluate alternatives for sharing derived data across engines
- Create Iceberg source tables with Spark
- Create a Presto-native SQL view from a Spark application
- Configure password-based Presto authentication
- Verify the view through the `prestodb` Python client
- Understand the cross-engine cleanup strategy used for repeatable execution

---

## Part 1: Understand the Limitation (10 minutes)

### Step 1: Review the documented known issue

IBM documents this limitation in [SQL views cannot be queried across engines (Spark and Presto)](https://cloud.ibm.com/docs/watsonxdata?topic=watsonxdata-known_issues&locale=en#known_issue20697):

> SQL views created by an engine with Hive iceberg catalog are recognised by other engines, but cannot be queried across engines, as one engine cannot understand the SQL dialect of another engine.

A shared Hive metastore allows both engines to recognize the view object. It does
not translate the SQL dialect stored in the view definition.

An Iceberg **table** and an SQL **view** are different types of objects:

- An Iceberg table has a standardized metadata model and data files that compatible
  engines can read.
- An SQL view stores a logical query rather than a copied result set. That query
  contains engine-specific SQL syntax, identifiers, functions, type rules, and
  other dialect-dependent semantics.
- The metastore provides object discovery, but it does not provide a common SQL
  parser or a translation layer between Spark SQL and Presto SQL.

Consequently, recognizing a view in the shared catalog does not mean that another
engine can parse, plan, or execute its stored definition.

| View creator | Spark | Presto |
|--------------|-------|--------|
| Spark | Can query the Spark view | Recognizes the object but cannot query it |
| Presto | Recognizes the object but cannot query it | Can query the Presto view |

The limitation applies to the **SQL view definition**, not to the underlying
Iceberg tables. Spark and Presto can still query the same source tables because
both engines understand the Iceberg table format.

### Step 2: Recognize the typical failure

A view created through Spark might use the following statement:

```sql
CREATE VIEW lab_catalog01.test.v_customers_active AS
SELECT *
FROM lab_catalog01.test.customers
WHERE account_status = 'ACTIVE';
```

When Presto queries that Spark-created view, it can report an error similar to:

```text
Hive views are not supported: 'test.v_customers_active'
```

The reverse direction has the same architectural limitation: a Presto-native view
is not a portable Spark SQL view. The reliable rule is:

> Create and query an SQL view through the same engine.

### Step 3: Evaluate possible alternatives

The appropriate solution depends on which engines must consume the derived data,
how current the result must be, and whether additional storage is acceptable.

| Alternative | Implementation | Advantages | Considerations | Recommended when |
|-------------|----------------|------------|----------------|------------------|
| **A. Create an engine-native view in each engine** | Create one Spark view for Spark consumers and an equivalent Presto view for Presto consumers. | Each engine receives a live view in its own SQL dialect.<br>No result data is duplicated.<br>Consumers continue to use normal views. | Two definitions must be maintained and tested for equivalent behavior.<br>Functions, data types, and null-handling rules can differ.<br>Business-logic changes must be deployed to both views. | Both engines require live views and the team can manage two engine-specific definitions. |
| **B. Materialize the result as an Iceberg table** | Execute the transformation with Spark or Presto and write the result to a physical Iceberg table that both engines query. | The derived dataset is interoperable across engines.<br>Complex logic is evaluated during refresh instead of for every query.<br>Iceberg snapshots and time travel remain available. | The result is only as current as its last refresh.<br>Additional storage and scheduled processing are required.<br>Refresh and failure-recovery logic must be maintained. | Native cross-engine access is mandatory and snapshot semantics are acceptable. |
| **C. Route queries through the view-owning engine** | Create the view in one engine and route every query to that engine. For example, a Spark application can use a Presto DBAPI or JDBC connection instead of `spark.sql()`. | Only one live definition is maintained.<br>No result-set storage or refresh schedule is required.<br>The owning engine applies consistent SQL semantics. | Consumers need credentials and a client or driver for the owning engine.<br>Execution remains on that engine.<br>The other engine cannot treat the object as its native view. | One engine is the designated query layer for the derived data. **This is the alternative implemented in this lab.** |
| **D. Move the transformation into application code** | Implement joins, filters, or aggregations in a shared pipeline and expose the result through an Iceberg table or application API. | Business logic can be versioned, tested, and deployed as code.<br>The design does not depend on cross-engine view parsing. | Pipeline or service code introduces an operational lifecycle.<br>Iceberg output needs refresh management, while an API introduces a service dependency. | Transformation governance or application-level reuse is more important than direct SQL-view access. |

### Step 4: Understand how this lab overcomes the limitation

This lab implements **Alternative C** and designates Presto as the view-owning and
querying engine:

1. Spark creates the `customers` and `orders` source tables in the shared Iceberg
   catalog.
2. The Spark driver opens a separate HTTPS connection to Presto through the
   `prestodb` DBAPI client.
3. `CREATE VIEW` is sent to Presto, so `v_customers_active` is stored as a
   Presto-native view definition.
4. Verification queries are sent through the same Presto connection instead of
   through `spark.sql()` or `spark.table()`.

```text
Spark application
  ├─ Spark SQL ────────> Iceberg source tables
  └─ prestodb client ──> Presto ──> Presto-native view ──> Iceberg source tables
```

This approach does not make the view portable and does not remove the documented
product limitation. It avoids the incompatible path by ensuring that Presto both
creates and queries the view. The resulting view remains live and introduces no
result-set storage, but Spark consumers must use Presto to access it. If native
access from both Spark and Presto were required, **Alternative B**, a materialized
Iceberg table, would be the preferred option.

---

## Part 2: Prepare the Lab (10 minutes)

### Step 1: Review the supplied files

| File | Purpose |
|------|---------|
| [`python-scripts/create_presto_view.py`](python-scripts/create_presto_view.py) | Creates the Iceberg tables, connects to Presto, creates the view, and verifies it |
| [`python-scripts/create_presto_view_payload.json`](python-scripts/create_presto_view_payload.json) | Spark application payload template |

The application performs these operations:

1. Drops and recreates `lab_catalog01.test.customers`, then inserts 10 sample rows.
2. Drops and recreates `lab_catalog01.test.orders`, then inserts 16 sample rows.
3. Ensures that the `prestodb` package is available.
4. Opens an HTTPS connection to Presto with a username and password.
5. Creates `lab_catalog01.test.v_customers_active` in Presto SQL dialect.
6. Queries the view through Presto and writes the results to the Spark driver log.

> **Important:** The application drops and recreates all three lab objects. Do not
> run it against tables or a view that contain data you need to retain.

### Step 2: Confirm the prerequisites

Before continuing, verify that:

- A Spark engine is running and associated with the `lab_catalog01` catalog.
- A Presto engine is running and can access the same catalog.
- The `test` schema already exists.
- Your Spark identity can create and drop the two Iceberg tables.
- Your Presto user can connect and create, query, and drop views.
- The Spark runtime contains `presto-python-client`, or the driver can access the
  Python package index for the runtime installation fallback.

For repeatable environments, install `presto-python-client` in the watsonx.data
library set instead of relying on installation during every run.

### Step 3: Make the application available to Spark

Upload [`python-scripts/create_presto_view.py`](python-scripts/create_presto_view.py)
to the Spark-accessible volume mounted as `ibm-hub::spark-apps`. The supplied
payload expects the following location:

```text
/mnts/spark-apps/apps/create_presto_view.py
```

If you use a different volume or location, update both `application` and `volumes`
in the payload.

---

## Part 3: Configure Presto Access (10 minutes)

### Step 1: Prepare the payload

Create a working copy of the payload before adding environment-specific values:

```bash
cp python-scripts/create_presto_view_payload.json \
   python-scripts/create_presto_view_payload.local.json
```

Do not commit the local payload because it contains credentials.

### Step 2: Set the connection properties

Replace the placeholders in the local payload with values for your environment:

| Spark property | Required | Description |
|----------------|----------|-------------|
| `spark.presto.host` | Yes | Presto hostname without `https://` |
| `spark.presto.port` | No | HTTPS port; the script defaults to `443` |
| `spark.presto.user` | Yes | Presto username |
| `spark.presto.password` | Yes | Password for the Presto user |
| `spark.presto.catalog` | No | Presto catalog; defaults to `lab_catalog01` |
| `spark.presto.schema` | No | Presto schema; defaults to `test` |

Example configuration:

```json
{
  "spark.presto.host": "presto.example.com",
  "spark.presto.port": "443",
  "spark.presto.user": "cpadmin",
  "spark.presto.password": "your-password",
  "spark.presto.catalog": "lab_catalog01",
  "spark.presto.schema": "test"
}
```

The application uses HTTP Basic Authentication over TLS:

```python
BasicAuthentication(cfg["user"], cfg["password"])
```

TLS certificate validation remains enabled with `verify=True`. The application
masks the password when writing its configuration to the driver log.

> `spark.hadoop.wxd.apikey` in the payload supports Spark access to the
> watsonx.data catalog. It is separate from the password used for the Presto
> connection.

---

## Part 4: Run the Spark Application (15 minutes)

### Step 1: Submit the application

Submit the application using the same Spark job submission method used in Lab 6,
with `python-scripts/create_presto_view_payload.local.json` as the payload.

Monitor the application until it reaches a completed or failed state.

### Step 2: Confirm the table creation steps

Review the Spark driver log and confirm that it reports successful completion of:

```text
Step 1 complete
Step 2 complete
```

Spark metastore operations are retried up to five times for recognized transient
HTTP 500, Thrift transport, or lost-client errors. The retry delays increase from
3 to 6, 12, and 24 seconds.

### Step 3: Confirm the Presto connection

The application checks for `prestodb`, reads the Spark connection properties, and
tests the connection with:

```sql
SELECT 1;
```

Connection establishment is attempted up to three times. The application waits
5 seconds after the first failure and 10 seconds after the second failure.

Look for this confirmation in the driver log:

```text
Presto connection established and verified (Basic Auth)
```

---

## Part 5: Create and Verify the Presto View (10 minutes)

### Step 1: Review the view definition

The application sends this logical query to Presto:

```sql
CREATE VIEW lab_catalog01.test.v_customers_active AS
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
    o.total_amount AS order_amount,
    o.currency AS order_currency
FROM lab_catalog01.test.customers c
JOIN lab_catalog01.test.orders o
  ON c.customer_id = o.customer_id
WHERE c.account_status = 'ACTIVE';
```

Because Presto executes `CREATE VIEW`, the definition is stored in the SQL dialect
that Presto can query.

### Step 2: Understand repeatable execution

Before creating the view, the application clears possible registrations left by
current or earlier implementations:

| Layer | Engine | Behavior |
|-------|--------|----------|
| 1 | Presto | Executes `DROP VIEW IF EXISTS` |
| 2 | Presto | Tries `DROP TABLE IF EXISTS` only if the Presto view drop fails |
| 3 | Spark | Attempts `DROP VIEW IF EXISTS`; errors are logged as warnings |
| 4 | Spark | Drops a table only when `SHOW TABLES` lists the target name |

If both Presto drop operations fail, view creation stops. Spark-side cleanup errors
are non-fatal, but an object left behind can still cause `CREATE VIEW` to fail.

### Step 3: Verify the results

Step 3 performs a non-fatal count and five-row preview. Step 4 performs the required
full read-back through Presto:

```sql
SELECT COUNT(*)
FROM lab_catalog01.test.v_customers_active;

SELECT *
FROM lab_catalog01.test.v_customers_active
ORDER BY customer_id, order_id;
```

Confirm that the driver log contains:

- A successful view creation message
- The number of rows in the view
- A formatted table containing all rows
- `Job completed successfully`

A failure during the Step 3 preview is logged as a warning. A failure during the
Step 4 full read-back causes the application to return exit code `1`.

---

## Part 6: Troubleshooting (5 minutes)

### `prestodb` cannot be imported

Install `presto-python-client` in the Spark runtime library set, or confirm that
the Spark driver can reach the Python package index. The runtime fallback has a
120-second installation timeout.

### Presto authentication fails

- Verify `spark.presto.user` and `spark.presto.password`.
- Confirm that the account is not locked and the password has not expired.
- Ensure the host and port identify the correct Presto endpoint.
- Confirm that the endpoint accepts HTTP Basic Authentication.

### TLS connection fails

- Use the hostname represented by the endpoint certificate.
- Confirm that the Spark runtime trusts the certificate authority.
- Do not disable `verify=True` as a workaround.

### View creation fails

- Confirm that `lab_catalog01.test.customers` and `lab_catalog01.test.orders` exist.
- Verify that both tables are visible to Presto.
- Confirm that the Presto user can create and drop objects in the schema.
- Check for a conflicting table or view named `v_customers_active`.

### Spark cannot query the Presto view

This is the documented cross-engine limitation, not a failed view creation. Query
the view through Presto, or materialize the result as an Iceberg table when both
engines must query the same derived dataset.

---

## Verification Checklist

- [ ] I reviewed the IBM cross-engine SQL view known issue.
- [ ] I confirmed that the `test` schema and both engines are available.
- [ ] I configured the Presto hostname, port, username, and password.
- [ ] The Spark application created the `customers` and `orders` tables.
- [ ] The application established the Presto connection.
- [ ] Presto created `v_customers_active`.
- [ ] The full view result was printed in the Spark driver log.
- [ ] I understand why Spark should not directly query this Presto-native view.

---

## Lab Questions

1. Why can Spark and Presto recognize the same view but not query it across engines?
2. What is the difference between interoperability of an Iceberg table and
   portability of an SQL view definition?
3. Why does creating and querying the view through Presto avoid the failure?
4. When would separate engine-native views be preferable to a materialized table?
5. When would a materialized Iceberg table be preferable to a Presto-native view?
6. Why does the application attempt cleanup through both Presto and Spark?
7. Which Spark properties contain the Presto login credentials?

---

## Best Practices

- Create and query a SQL view through the same engine.
- Use Iceberg tables when a derived dataset must be readable by multiple engines.
- Store passwords in an approved secret-management mechanism and inject them only
  at submission time.
- Do not commit payloads containing real credentials.
- Keep TLS certificate validation enabled.
- Pre-install Python dependencies in a managed runtime for repeatable production jobs.
- Review driver logs after every run and verify the view through Presto.

---

## Additional Resources

- [IBM watsonx.data known issue: SQL views cannot be queried across engines (Spark and Presto)](https://cloud.ibm.com/docs/watsonxdata?topic=watsonxdata-known_issues&locale=en#known_issue20697)
- [IBM watsonx.data documentation](https://www.ibm.com/docs/en/watsonxdata)
- [Presto Python client](https://github.com/prestodb/presto-python-client)
- [Apache Iceberg documentation](https://iceberg.apache.org/docs/latest/)

---

## Next Steps

You have completed the final lab in this training series. Apply the engine-specific
view rule when designing workloads that share an Iceberg catalog between Spark and
Presto.

---

**Lab Completed!** ✓

Please inform your instructor that you have completed Lab 10 and the watsonx.data
training series.
