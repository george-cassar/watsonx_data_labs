# Lab 1: Initial Configuration and Interface Exploration

**Duration:** 45 minutes
**Difficulty:** Beginner
**Prerequisites:** Access to watsonx.data environment
**Last Updated:** April 2026

---

## Lab Objectives

By the end of this lab, you will be able to:
- Access the watsonx.data web console
- Navigate the main interface components
- Understand the Infrastructure Manager
- Explore Data Manager and Query Workspace
- Generate and use API keys
- Access watsonx.data via command line (cpd-cli and cpdctl)

---

## Part 1: Accessing the Web Console (10 minutes)

### Step 1: Login to watsonx.data

1. Open your web browser and navigate to the watsonx.data URL provided by your instructor:
   ```
   https://<your-watsonx-data-url>
   ```

2. Enter your credentials:
   - **Username:** `<provided-username>`
   - **Password:** `<provided-password>`

3. Click **Sign In**

4. Upon successful login, you should see the watsonx.data home page

### Step 2: Explore the Home Page

1. Observe the main navigation menu on the left side:
   - **Home** - Dashboard and quick access
   - **Data Manager** - Catalog and table management
   - **Query Workspace** - SQL query editor
   - **Infrastructure Manager** - Engine and resource management
   - **Access Control** - Security and permissions

2. Note the user profile icon in the top-right corner

---

## Part 2: Infrastructure Manager (10 minutes)

### Step 1: Navigate to Infrastructure Manager

1. Click on **Infrastructure Manager** in the left navigation menu

2. You will see three main sections:
   - **Engines** - Query engines (Presto, Spark)
   - **Catalogs** - Data catalogs and connections
   - **Buckets** - Object storage buckets

### Step 2: Explore Engines

1. Click on the **Engines** tab

2. Observe the pre-configured engines:
   - **presto-01** (or similar name) - Presto query engine
   - Note the status (Running/Stopped)
   - Note the engine type and version

3. Click on an engine name to view details:
   - **Configuration** - Engine settings
   - **Associated catalogs** - Connected data sources
   - **Size** - Starter, Small, etc.

4. Record the following information:
   ```
   Engine Name: _________________
   Engine Type: _________________
   Status: _________________
   Number of Nodes: _________________
   ```

### Step 3: Explore Catalogs

1. Click on the **Catalogs** tab

2. You should see default catalogs such as:
   - **iceberg_data** - Iceberg catalog
   - **hive_data** - Hive metastore catalog (if configured)

3. Click on a catalog to view:
   - **Type** - Catalog type (Iceberg, Hive, etc.)
   - **Associated engines** - Which engines can access this catalog
   - **Bucket** - Storage location

### Step 4: Explore Buckets

1. Click on the **Buckets** tab

2. Observe the configured object storage buckets:
   - Bucket name
   - Type (S3, MinIO, IBM COS)
   - Status

3. Click on a bucket to view details and browse contents

---

## Part 3: Data Manager (10 minutes)

### Step 1: Navigate to Data Manager

1. Click on **Data Manager** in the left navigation menu

2. You will see a tree view of:
   - Catalogs
   - Schemas (databases)
   - Tables

### Step 2: Explore Sample Data

1. Expand the **tpch** catalog

2. Expand the **tiny** schema

3. You should see sample tables:
   - `customer`
   - `orders`
   - `lineitem`
   - `nation`
   - `region`
   - etc.

4. Click on the **customer** table

5. Observe the table details:
   - **Schema** tab - Column names and data types
   - **Data** tab - Sample data preview
   - **Details** tab - Table properties and statistics
   - **Partitions** tab - Partition information (if applicable)

6. Record the schema of the customer table:
   ```
   Column Name          Data Type
   _______________      _______________
   _______________      _______________
   _______________      _______________
   ```

---

## Part 4: Query Workspace (10 minutes)

### Step 1: Navigate to Query Workspace

1. Click on **Query Workspace** in the left navigation menu

2. You will see:
   - SQL editor on the left
   - Results panel at the bottom
   - Schema browser on the right

### Step 2: Execute Your First Query

1. In the SQL editor, type the following query:
   ```sql
   SELECT * FROM tpch.tiny.customer LIMIT 10;
   ```

2. Click the **Run** button (or press Ctrl+Enter / Cmd+Enter)

3. Observe the results in the results panel:
   - Number of rows returned
   - Execution time
   - Column headers and data

### Step 3: Explore Query Plan

1. Click on the **Explain** button (or add `EXPLAIN` before your query)

2. Run the following:
   ```sql
   EXPLAIN SELECT * FROM tpch.tiny.customer LIMIT 10;
   ```

3. Observe the query execution plan:
   - Scan operations
   - Filter operations
   - Limit operations

### Step 4: View Query History via Presto UI

**Note:** Query history may not be available directly in the watsonx.data Query Workspace interface. Instead, you can access detailed query information through the Presto UI.

#### Option A: Access Presto UI Directly

1. Get the Presto UI URL from your instructor or construct it:
   ```
   https://<presto-engine-hostname>:<port>/ui
   ```
   
2. Open the Presto UI in a new browser tab

3. You will see the **Cluster Overview** page with:
   - **Running Queries** - Currently executing queries
   - **Queued Queries** - Queries waiting to execute
   - **Blocked Queries** - Queries blocked by resources
   - **Active Workers** - Number of active worker nodes
   - **Runnable Drivers** - Available execution threads
   - **Reserved Memory** - Memory usage statistics

4. Scroll down to the **Query Details** section to see:
   - Recent query history
   - Query ID (clickable for details)
   - User who executed the query
   - Source/Client information
   - Query state (FINISHED, RUNNING, FAILED)
   - Execution time and statistics

5. Click on a **Query ID** to view detailed information:
   - Full query text
   - Execution timeline
   - Stage details
   - Resource usage
   - Output rows and data size

#### Option B: Access via Infrastructure Manager

1. Navigate to **Infrastructure Manager** → **Engines**

2. Click on your Presto engine (e.g., `presto-01`)

3. Look for **External host** link/button

4. Click to open the Presto UI in a new tab

5. Follow steps 3-5 from Option A above

#### Option C: Query System Tables for History

If Presto UI is not accessible, you can query system tables:

```sql
-- View recent queries
SELECT
    query_id,
    query,
    state,
    user,
    source,
    created,
    started,
    "end"
FROM system.runtime.queries
ORDER BY created DESC
LIMIT 20;
```

**Record your observations:**
```
Presto UI URL: _________________________________
Number of queries in history: _________________
Most recent query state: ______________________
Average query execution time: _________________
```

---

## Part 5: API Key Generation (5 minutes)

### Step 1: Generate an API Key

1. Click on your **user profile icon** in the top-right corner

2. Select **Profile and Settings**

3. Navigate to the **API Keys** section

4. Click **Generate New API Key**

7. **IMPORTANT:** Copy and save the API key immediately (it will only be shown once)
   ```
   API Key: _________________________________
   ```

8. Store this key securely - you will need it for command-line access

---

## Part 6: Command Line Access (10 minutes)

### Step 1: Install cpd-cli (if not already installed)

1. Open a terminal on your workstation

2. Download and install cpd-cli following the official IBM documentation:
   
   **📖 Installation Guide:** [Installing the cpd-cli](https://www.ibm.com/docs/en/software-hub/5.3.x?topic=cli-installing-cpd)
   
   The installation process varies by operating system:
   
   **For Linux/macOS:**
   ```bash
   # Download the cpd-cli installer
   wget https://github.com/IBM/cpd-cli/releases/latest/download/cpd-cli-linux-EE-<version>.tgz
   
   # Extract the archive
   tar -xvf cpd-cli-linux-EE-<version>.tgz
   
   # Move to a directory in your PATH
   cd cpd-cli-linux-EE-<version>
   sudo mv * /usr/local/bin/
   
   # Make it executable
   sudo chmod +x /usr/local/bin/cpd-cli
   ```

3. Verify installation:
   ```bash
   cpd-cli version
   ```
   
   Expected output:
   ```
   cpd-cli version: <version-number>
   ```

4. If you encounter issues, refer to the [troubleshooting section](https://www.ibm.com/docs/en/software-hub/5.3.x?topic=cli-troubleshooting-cpd) in the IBM documentation

### Step 2: Configure cpd-cli

1. Set up your connection profile:
   ```bash
   cpd-cli config users set lab-user \
     --username <your-username> \
     --apikey <your-api-key>
   ```

2. Set up the server profile:
   ```bash
   cpd-cli config profiles set lab-profile \
     --url https://<your-watsonx-data-url> \
     --user lab-user
   ```
   Example:
   ```bash
   cpd-cli config profiles set lab-profile \
     --url https://cpd-cpd.apps.itz-me1g6c.infra01-lb.lon04.techzone.ibm.com/ \
     --user lab-user
   ```

3. Test the connection:
   ```bash
   cpd-cli config profiles list
   ```

### Step 3: Basic cpd-cli Commands

1. List available services:
   ```bash
   cpd-cli service-instance list --profile lab-profile
   ```

2. Get watsonx.data instance details:
   ```bash
   cpd-cli service-instance get <instance-name> --profile lab-profile
   ```

### Step 4: Using cpdctl

1. Verify cpdctl installation:
   ```bash
   cpdctl version
   ```

2. Configure cpdctl:
   ```bash
   cpdctl config user set lab-user \
     --username <your-username> \
     --apikey <your-api-key>
   
   cpdctl config profile set lab-profile \
     --url https://<your-watsonx-data-url> \
     --user lab-user
   ```

3. Test cpdctl on watsonx.data by listing available engines:
   ```bash
   cpdctl wx-data engine list
   ```

---

## Part 7: Presto CLI Access (Bonus)

The Presto CLI is a terminal-based interactive shell for running queries directly against your Presto engine.

### Step 1: Download and Install Presto CLI

1. **Download the Presto CLI executable:**

   **For Linux/macOS:**
   ```bash
   # Download the latest Presto CLI
   curl -L https://repo1.maven.org/maven2/com/facebook/presto/presto-cli/0.284/presto-cli-0.284-executable.jar -o presto-cli
   
   # Make it executable
   chmod +x presto-cli
   
   # Move to a directory in your PATH (optional)
   sudo mv presto-cli /usr/local/bin/
   ```

   **For Windows:**
   ```powershell
   # Download using PowerShell
   Invoke-WebRequest -Uri "https://repo1.maven.org/maven2/com/facebook/presto/presto-cli/0.284/presto-cli-0.284-executable.jar" -OutFile "presto-cli.jar"
   
   # Create a batch file to run it
   echo @java -jar "%~dp0presto-cli.jar" %* > presto-cli.bat
   ```

2. **Verify the download:**
   ```bash
   # Linux/macOS
   presto-cli --version
   
   # Windows
   java -jar presto-cli.jar --version
   ```

### Step 2: Connect to Presto CLI

1. **Get your Presto coordinator URL:**
   - From Infrastructure Manager → Engines → Click on your Presto engine
   - Note the hostname and port (typically 8443 for HTTPS)

2. **Connect using presto-cli:**

   **Basic connection:**
   ```bash
   presto-cli --server https://<presto-coordinator-url>:8443 \
     --user <your-username> \
     --password
   ```

   **Example with actual values:**
   ```bash
   presto-cli --server https://ibm-lh-lakehouse-presto555-presto-svc-cpd.apps.itz-me1g6c.infra01-lb.lon04.techzone.ibm.com/ \
     --user cpadmin \
     --password \
     --catalog iceberg_data \
     --schema default
   ```

3. **Alternative: Use web-based terminal** if available in the watsonx.data console

### Step 2: Execute a Query via CLI

1. Once connected, run:
   ```sql
   SHOW CATALOGS;
   ```

2. List schemas:
   ```sql
   SHOW SCHEMAS FROM tpch;
   ```

3. Run a simple query:
   ```sql
   SELECT COUNT(*) FROM tpch.tiny.customer;
   ```

4. Exit Presto CLI:
   ```sql
   quit;
   ```

---

## Verification Checklist

Mark each item as you complete it:

- [ ] Successfully logged into watsonx.data web console
- [ ] Explored Infrastructure Manager (Engines, Catalogs, Buckets)
- [ ] Navigated Data Manager and viewed table schemas
- [ ] Executed queries in Query Workspace
- [ ] Viewed query execution plan
- [ ] Generated and saved API key
- [ ] Configured cpd-cli with connection profile
- [ ] Configured cpdctl with connection profile
- [ ] Executed basic commands via CLI
- [ ] (Bonus) Connected to Presto CLI

---

## Lab Questions

Answer the following questions based on your exploration:

1. **How many Presto engines are configured in your environment?**
   
   Answer: _________________

2. **What is the default Iceberg catalog name?**
   
   Answer: _________________

3. **How many tables are in the tpch.tiny schema?**
   
   Answer: _________________

4. **What is the execution time for your first query?**
   
   Answer: _________________

5. **What authentication method did you use for CLI access?**
   
   Answer: _________________

---

## Troubleshooting

### Issue: Cannot login to web console
**Solution:** 
- Verify the URL is correct
- Check username and password
- Ensure your account is activated
- Contact your administrator

### Issue: API key generation fails
**Solution:**
- Check if you have permission to generate API keys
- Verify you haven't exceeded the maximum number of keys
- Try logging out and back in

### Issue: cpd-cli connection fails
**Solution:**
- Verify the URL format (should include https://)
- Check API key is correct
- Ensure network connectivity
- Verify SSL certificates if using self-signed certificates

### Issue: Cannot see any catalogs or tables
**Solution:**
- Check if you have been granted access permissions
- Verify the engines are running
- Contact your administrator to assign appropriate roles

---

## Additional Resources

- [watsonx.data Documentation](https://www.ibm.com/docs/en/watsonxdata)
- [Presto Documentation](https://prestodb.io/docs/current/)
- [cpd-cli Reference](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.8.x?topic=interface-cpd-cli-command-reference)

---

## Next Steps

Proceed to **[Lab 2: Catalog and Table Creation](LAB02_Catalog_Table_Creation.md)** where you will:
- Create your own Iceberg catalog
- Create schemas and tables
- Load data into tables
- Explore table properties

---

**Lab Completed!** ✓

Please inform your instructor that you have completed Lab 1 before proceeding to Lab 2.
