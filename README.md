# watsonx.data Training Labs

Welcome to the watsonx.data hands-on training labs! These labs are designed to provide practical experience with watsonx.data, covering everything from basic operations to advanced features.

---

## 📋 Lab Overview

This training consists of 9 comprehensive hands-on labs that progressively build your skills with watsonx.data:

| Lab # | Title | Duration | Difficulty | Topics Covered |
|-------|-------|----------|------------|----------------|
| **Lab 1** | [Initial Configuration and Interface Exploration](LAB01_Initial_Configuration_Interface.md) | 45 min | Beginner | Web console, Infrastructure Manager, Data Manager, Query Workspace, CLI access |
| **Lab 2** | [Catalog and Table Creation](LAB02_Catalog_Table_Creation.md) | 60 min | Beginner-Intermediate | Iceberg catalogs, schemas, tables, data types, external tables |
| **Lab 3** | [Data Ingestion with Presto](LAB03_Data_Ingestion_Presto.md) | 75 min | Intermediate | INSERT statements, CSV/Parquet loading, CTAS, bulk loading, MOR vs COW |
| **Lab 4** | [Partitioning and Optimization](LAB04_Partitioning_Optimization.md) | 60 min | Intermediate-Advanced | Partitioning strategies, bucketing, sorting, query optimization, caching |
| **Lab 5** | [Time Travel and Rollback Operations](LAB05_Time_Travel_Rollback.md) | 60 min | Intermediate | Time travel queries, snapshots, rollback, data recovery, auditing |
| **Lab 6** | [Spark Application Development](LAB06_Spark_Application_Development.md) | 90 min | Advanced | Spark engines, PySpark, Spark SQL, ETL pipelines, job execution, monitoring |
| **Lab 7** | [Data Compaction and Maintenance](LAB07_Data_Compaction_Maintenance.md) | 45 min | Intermediate | MOR vs COW, file compaction, manifest optimization, table maintenance |
| **Lab 8** | [Python Integration with watsonx.data](LAB08_Third_Party_Integration.md) | 60 min | Intermediate | Python environment, Presto connectivity, pandas analysis, interactive dashboards |
| **Lab 9** | [Spark Custom Runtime Image Testing](LAB09_Spark_Custom_Runtime_Image_Testing.md) | 60 min | Advanced | Custom Spark runtime images, Docker/Podman, OpenShift, registry publishing, Python package customization |

**Total Duration:** ~8.5 hours

---

## 🎯 Learning Path

### For Beginners
Start with Labs 1-3 to build foundational knowledge:
1. Lab 1: Get familiar with the interface
2. Lab 2: Learn to create catalogs and tables
3. Lab 3: Master data ingestion techniques

### For Intermediate Users
Continue with Labs 4-5 for advanced operations:
4. Lab 4: Optimize query performance
5. Lab 5: Use time travel and recovery features

### For Advanced Users
Complete Labs 6-9 for expert-level skills:
- Lab 6: Develop Spark applications
- Lab 7: Maintain and optimize tables
- Lab 8: Integrate with external tools
- Lab 9: Build and validate custom Spark runtime images

---

## 📚 Prerequisites

### Technical Requirements
- Access to a watsonx.data environment (SaaS or on-premises)
- Web browser (Chrome, Firefox, or Safari recommended)
- Terminal/SSH client for command-line exercises
- Basic SQL knowledge
- Familiarity with data warehousing concepts

### Optional Tools
- Python 3.8+ (for Lab 6, Lab 8, and Lab 9)
- Java 11+ (for Lab 1 and Lab 8)
- Docker or Podman (for Lab 9)
- OpenShift CLI (`oc`) and `jq` (for Lab 9)
- BI tool (Tableau, PowerBI, or similar) for Lab 8
- Visual Studio Code or similar IDE (for Lab 6 and Lab 9)

### Account Setup
Before starting the labs, ensure you have:
- [ ] watsonx.data login credentials
- [ ] Assigned user role with appropriate permissions
- [ ] Access to object storage (S3, MinIO, or IBM COS)
- [ ] API key generated (covered in Lab 1)

---

## 🚀 Getting Started

### Step 1: Environment Access
1. Obtain your watsonx.data URL from your instructor
2. Verify you can login to the web console
3. Confirm you have access to at least one Presto engine

### Step 2: Lab Materials
1. Clone or download this repository
2. Review the lab prerequisites
3. Prepare any required sample data files

### Step 3: Start Lab 1
Begin with [Lab 1: Initial Configuration and Interface Exploration](LAB01_Initial_Configuration_Interface.md)

---

## 📖 Lab Structure

Each lab follows a consistent structure:

### Lab Components
- **Objectives**: What you'll learn
- **Prerequisites**: Required prior knowledge or labs
- **Step-by-Step Instructions**: Detailed procedures
- **Verification Checklist**: Track your progress
- **Lab Questions**: Test your understanding
- **SQL Reference**: Quick command reference
- **Best Practices**: Industry recommendations
- **Troubleshooting**: Common issues and solutions
- **Additional Resources**: Links for deeper learning

### Lab Format
- **Theory**: Conceptual explanations
- **Hands-On**: Practical exercises
- **Verification**: Confirm successful completion
- **Questions**: Reinforce learning

---

## 🗂️ Sample Data

The labs use a retail business scenario with realistic datasets provided in both CSV and Parquet formats.

### Available Datasets

All sample data files are located in the **[sample_data/](sample_data/)** directory:

| Dataset | Format | Records | Description |
|---------|--------|---------|-------------|
| **customers** | CSV + Parquet | 30 | Customer master data with demographics and loyalty tiers |
| **orders** | CSV + Parquet | 50 | Order transactions with product and shipping details |
| **products** | CSV + Parquet | 43 | Product catalog with specifications and inventory |
| **sales_transactions** | CSV + Parquet | 50 | Detailed payment and transaction records |

### Data Model
```
customers (1) ──────< (N) orders
                         │
                         │ (1)
                         ▼
                      (1) sales_transactions

products (1) ──────< (N) orders
```

### Key Relationships
- `orders.customer_id` → `customers.customer_id`
- `orders.product_id` → `products.product_id`
- `sales_transactions.order_id` → `orders.order_id`
- `sales_transactions.customer_id` → `customers.customer_id`

### Using Sample Data

**For Beginners (Labs 1-3):**
- Sample data is generated within the labs using SQL
- No external files required for basic exercises

**For Advanced Labs (Labs 6-9):**
- Use CSV files for data ingestion exercises
- Use Parquet files for performance-optimized operations
- Refer to [sample_data/README.md](sample_data/README.md) for detailed schemas and usage examples

### Quick Start with Sample Data

```bash
# View available sample files
ls -lh sample_data/

# Load customers data in Presto
COPY iceberg_data.retail.customers
FROM 'sample_data/customers.csv'
WITH (format = 'CSV', header = true);

# Read with Spark
df = spark.read.parquet("sample_data/customers.parquet")
```

For complete documentation, schemas, and usage examples, see **[sample_data/README.md](sample_data/README.md)**.

---

## 💡 Tips for Success

### General Tips
1. **Read Carefully**: Follow instructions step-by-step
2. **Take Notes**: Document your observations and learnings
3. **Experiment**: Try variations of the examples
4. **Ask Questions**: Don't hesitate to seek clarification
5. **Practice**: Repeat exercises to reinforce learning

### SQL Tips
- Use consistent formatting for readability
- Comment your queries for future reference
- Save successful queries for reuse
- Use EXPLAIN to understand query execution

### Troubleshooting Tips
- Check error messages carefully
- Verify table and column names
- Ensure proper permissions
- Review the troubleshooting section in each lab
- Ask your instructor if stuck

---

## 🔧 Common Issues and Solutions

### Cannot Login
- Verify URL is correct
- Check username and password
- Ensure account is activated
- Clear browser cache

### Tables Not Visible
- Check catalog is associated with engine
- Verify you have read permissions
- Refresh the Data Manager view
- Ensure tables were created successfully

### Query Fails
- Verify SQL syntax
- Check table and column names
- Ensure data types match
- Review error message details

### Slow Performance
- Check if partitioning is used
- Verify statistics are up to date
- Review query execution plan
- Consider adding indexes or bucketing

---

## 📊 Progress Tracking

Use this checklist to track your lab completion:

- [ ] Lab 1: Initial Configuration and Interface Exploration
- [ ] Lab 2: Catalog and Table Creation
- [ ] Lab 3: Data Ingestion with Presto
- [ ] Lab 4: Partitioning and Optimization
- [ ] Lab 5: Time Travel and Rollback Operations
- [ ] Lab 6: Spark Application Development
- [ ] Lab 7: Data Compaction and Maintenance
- [ ] Lab 8: Third-party Tool Integration
- [ ] Lab 9: Spark Custom Runtime Image Testing

---

## 🎓 Certification

Upon completing all labs, you will have:
- ✓ Hands-on experience with watsonx.data
- ✓ Understanding of lakehouse architecture
- ✓ Skills in data ingestion and management
- ✓ Knowledge of query optimization
- ✓ Mastery of time travel and data recovery
- ✓ Experience with Spark ETL pipeline development
- ✓ Proficiency in data compaction and maintenance
- ✓ Capability to build Python analytics solutions with interactive dashboards
- ✓ Ability to create, publish, and validate custom Spark runtime images

### Next Steps After Labs
1. Review the [watsonx.data documentation](https://www.ibm.com/docs/en/watsonxdata)
2. Explore advanced features not covered in labs
3. Apply learnings to your own use cases
4. Join the watsonx.data community
5. Consider IBM certification programs

---

## 📞 Support and Resources

### During Training
- **Instructor**: Ask questions during lab sessions
- **Lab Assistants**: Get help with technical issues
- **Peer Support**: Collaborate with other participants

### After Training
- **Documentation**: [IBM watsonx.data Docs](https://www.ibm.com/docs/en/watsonxdata)
- **Community**: [IBM Community Forums](https://community.ibm.com)
- **Support**: [IBM Support Portal](https://www.ibm.com/support)
- **Learning**: [IBM Training](https://www.ibm.com/training)

### Additional Resources
- [Apache Iceberg Documentation](https://iceberg.apache.org/docs/latest/)
- [Presto Documentation](https://prestodb.io/docs/current/)
- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [SQL Reference Guide](https://prestodb.io/docs/current/sql.html)

---

## 🤝 Contributing

Found an issue or have a suggestion? Please:
1. Document the issue clearly
2. Provide steps to reproduce
3. Suggest improvements
4. Share with your instructor

---

## 📝 Lab Feedback

After completing each lab, please provide feedback on:
- Clarity of instructions
- Difficulty level
- Time required
- Technical issues encountered
- Suggestions for improvement

Your feedback helps improve the training for future participants!

---

## 📄 License and Usage

These training materials are provided for educational purposes. Please:
- Use for learning and training
- Share with team members
- Provide attribution when reusing
- Do not redistribute commercially

---

## 🔄 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | March 2026 | Initial release with Labs 1-5 |
| 1.1 | April 2026 | Labs 6-8 added, comprehensive Python integration |
| 1.2 | April 2026 | Lab restructuring, enhanced Lab 7 & 8 |
| 1.3 | April 2026 | Lab 9 added for Spark custom runtime image testing |

---

## 📧 Contact

For questions about these labs:
- **Training Coordinator**: [George Cassar, Arancha Ocana]

---

**Happy Learning!** 🚀

Start your journey with [Lab 1: Initial Configuration and Interface Exploration](LAB01_Initial_Configuration_Interface.md)