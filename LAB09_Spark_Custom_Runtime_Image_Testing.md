# Lab 09: Spark Custom Runtime Image Testing for watsonx.data

This lab provides comprehensive testing materials for submitting Spark applications using custom runtime images on IBM watsonx.data deployed on OpenShift.

## 📋 Overview

This lab helps you validate the process documented in the [IBM watsonx.data documentation](https://www.ibm.com/docs/en/watsonxdata/standard/2.3.x?topic=ssabunse-submitting-spark-application-by-using-custom-runtime-image) for creating and using custom Spark runtime images.

## 🎯 What You'll Test

1. Creating a custom Docker image that extends the base Spark runtime
2. Adding custom OS packages (vim, etc.)
3. **Adding custom Python libraries (pandas, numpy, scikit-learn, matplotlib, seaborn)**
4. Adding custom JAR files
5. Building and pushing the custom image to a container registry
6. Configuring and submitting a Spark application using the custom image
7. Verifying the custom runtime and Python libraries work correctly

## 📁 Lab Contents

| File | Description |
|------|-------------|
| [`unix-scripts/spark-custom-runtime-testing-guide.md`](unix-scripts/spark-custom-runtime-testing-guide.md) | **Main testing guide** - Detailed step-by-step instructions |
| [`unix-scripts/setup-environment.sh`](unix-scripts/setup-environment.sh) | Interactive script to configure your environment |
| [`unix-scripts/build-and-push.sh`](unix-scripts/build-and-push.sh) | Automated script to build and push Docker images |
| [`unix-scripts/install-python-packages.sh`](unix-scripts/install-python-packages.sh) | Script to install custom Python packages |
| [`unix-scripts/spark-job-config.template.json`](unix-scripts/spark-job-config.template.json) | Template for Spark job configuration |

## 🚀 Quick Start

### Prerequisites

Before you begin, ensure you have:

- ✅ Access to an OpenShift cluster with watsonx.data deployed
- ✅ OpenShift CLI (`oc`) installed and configured
- ✅ **Docker or Podman** installed and running on your local machine
- ✅ Access to a container registry (Docker Hub, OpenShift registry, etc.)
- ✅ Administrator privileges to run `oc` and container commands

**Note:** This lab supports both Docker and Podman. All scripts automatically detect which container runtime you have installed.

### Step 1: Setup Your Environment

Run the interactive setup script from the [`unix-scripts/`](unix-scripts/) directory to configure your environment:

```bash
chmod +x unix-scripts/setup-environment.sh
./unix-scripts/setup-environment.sh
```

This will:
- Prompt you for necessary configuration values
- Create a `.env.spark-custom-runtime` file with your settings
- Verify prerequisites are met

After completion, load the environment:

```bash
source .env.spark-custom-runtime
```

### Step 2: Create Required Files

You'll need to create four files for your custom image.

#### 2.1 Create `install-os-packages.sh`

```bash
cat > install-os-packages.sh << 'EOF'
#!/bin/bash
set -e -o pipefail

# Install operating system packages
microdnf update -y
microdnf install -y vim

# Add any other OS packages your application needs
EOF

chmod +x install-os-packages.sh
```

#### 2.2 Review or customize `install-python-packages.sh`

A starter version already exists at [`unix-scripts/install-python-packages.sh`](unix-scripts/install-python-packages.sh). You can reuse it directly or adapt it locally as needed:

```bash
cp unix-scripts/install-python-packages.sh ./install-python-packages.sh
chmod +x install-python-packages.sh
```

#### 2.3 Create `install-jar.sh`

```bash
cat > install-jar.sh << 'EOF'
#!/bin/bash
set -e -o pipefail

# Install additional JAR files
# Example: Download a JAR from Maven repository
wget -c -P /opt/ibm/spark/external-jars/ \
  https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-databind/2.13.0/jackson-databind-2.13.0.jar
EOF

chmod +x install-jar.sh
```

#### 2.4 Create `Dockerfile`

```bash
cat > Dockerfile << 'EOF'
ARG REGISTRY
ARG IMAGE_NAME
FROM ${REGISTRY}/${IMAGE_NAME}
USER root:3000
COPY *.sh /tmp/
RUN bash /tmp/install-os-packages.sh && \
    bash /tmp/install-python-packages.sh && \
    bash /tmp/install-jar.sh
USER ${CLUSTER_USER}
WORKDIR ${WORK_DIR}
EOF
```

### Step 3: Build and Push Your Custom Image

Use the automated build script from [`unix-scripts/build-and-push.sh`](unix-scripts/build-and-push.sh):

```bash
chmod +x unix-scripts/build-and-push.sh
./unix-scripts/build-and-push.sh
```

This script will:
- Pull the base Spark image
- Build your custom image with the customizations
- Test the image locally
- Push it to your container registry
- Verify the push was successful

### Step 4: Create and Submit Spark Application

Follow the detailed instructions in [`unix-scripts/spark-custom-runtime-testing-guide.md`](unix-scripts/spark-custom-runtime-testing-guide.md) starting from **Step 7** to:
- Create a test Spark application
- Configure the job to use your custom image
- Submit and monitor the application

You can also use the provided template at [`unix-scripts/spark-job-config.template.json`](unix-scripts/spark-job-config.template.json) as a starting point.

## 📖 Detailed Documentation

For comprehensive step-by-step instructions, troubleshooting tips, and detailed explanations, refer to:

**[📘 Spark Custom Runtime Testing Guide](unix-scripts/spark-custom-runtime-testing-guide.md)**

This guide includes:
- Detailed prerequisites
- Step-by-step instructions for each phase
- Command examples with explanations
- Troubleshooting section
- Verification steps
- Cleanup procedures

## 🔍 Testing Phases

### Phase 1: Image Preparation (Steps 1-6)
- Retrieve base Spark image
- Create customization scripts
- Build custom Docker image
- Push to registry

### Phase 2: Application Setup (Steps 7-10)
- Create test Spark application
- Configure job with custom image
- Prepare for submission

### Phase 3: Execution & Validation (Steps 11-15)
- Submit Spark application
- Monitor execution
- Verify custom runtime
- Review results

## 🛠️ Helper Scripts

### `setup-environment.sh`
Interactive script that:
- Collects configuration information
- Creates environment file
- Verifies prerequisites
- Provides next steps

**Usage:**
```bash
./unix-scripts/setup-environment.sh
source .env.spark-custom-runtime
```

### `build-and-push.sh`
Automated build script that:
- Validates required files
- Pulls base image
- Builds custom image
- Tests the image
- Pushes to registry
- Verifies deployment

**Usage:**
```bash
./unix-scripts/build-and-push.sh
```

### `install-python-packages.sh`
Reusable helper script that:
- Installs pandas, numpy, scikit-learn, matplotlib, and seaborn
- Verifies the installed package versions
- Can be copied into your build context before building the image

**Usage:**
```bash
cp unix-scripts/install-python-packages.sh ./install-python-packages.sh
chmod +x install-python-packages.sh
```

## 📝 Example Workflow

Here's a typical testing workflow:

```bash
# 1. Setup environment
./unix-scripts/setup-environment.sh
source .env.spark-custom-runtime

# 2. Reuse provided Python package installer
cp unix-scripts/install-python-packages.sh ./install-python-packages.sh
chmod +x install-python-packages.sh

# 3. Create remaining customization files (see Step 2 above)

# 4. Build and push image
./unix-scripts/build-and-push.sh

# 5. Create test application
cat > test-app.py << 'EOF'
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("CustomRuntimeTest").getOrCreate()
print("Testing Custom Runtime Image")
data = [("Alice", 34), ("Bob", 45)]
df = spark.createDataFrame(data, ["Name", "Age"])
df.show()
spark.stop()
EOF

# 6. Create job configuration from template
cp unix-scripts/spark-job-config.template.json ./spark-job-config.json

# 7. Update the image reference in spark-job-config.json

# 8. Submit via watsonx.data UI or CLI
# (See detailed guide for submission instructions)

# 9. Monitor execution
oc get pods -n ${NAMESPACE} | grep spark
oc logs -f <spark-driver-pod> -n ${NAMESPACE}
```

## 🐛 Troubleshooting

Common issues and solutions:

### Image Pull Errors
```bash
# Login to OpenShift registry
oc registry login
docker login -u $(oc whoami) -p $(oc whoami -t) ${BASE_REGISTRY}
```

### Custom Packages Not Found
```bash
# Verify image contents
docker run -it ${FULL_IMAGE_NAME} /bin/bash
which vim
ls -la /opt/ibm/spark/external-jars/
```

### Application Fails to Start
```bash
# Check pod events and logs
oc describe pod <spark-driver-pod> -n ${NAMESPACE}
oc logs <spark-driver-pod> -n ${NAMESPACE}
```

For more troubleshooting tips, see the [Testing Guide](unix-scripts/spark-custom-runtime-testing-guide.md#troubleshooting).

## ✅ Success Criteria

Your test is successful when:

- ✅ Custom Docker image builds without errors
- ✅ Image successfully pushed to registry
- ✅ Spark application pod starts and pulls custom image
- ✅ Application logs show custom packages are available
- ✅ Application completes successfully with expected output
- ✅ No errors in driver or executor logs

## 📚 Additional Resources

- [IBM watsonx.data Documentation](https://www.ibm.com/docs/en/watsonxdata)
- [Supported Spark versions](https://www.ibm.com/docs/en/watsonxdata/standard/2.3.x)
- [OpenShift Container Platform Documentation](https://docs.openshift.com/)
- [Docker Documentation](https://docs.docker.com/)

## 🤝 Support

If you encounter issues:

1. Check the [Troubleshooting section](unix-scripts/spark-custom-runtime-testing-guide.md#troubleshooting) in the testing guide
2. Review the helper scripts in [`unix-scripts/`](unix-scripts/) and confirm all required files are present
3. Verify your environment configuration in `.env.spark-custom-runtime`
4. Check OpenShift pod logs for detailed error messages

## 📄 License

This testing suite is provided as-is for testing IBM watsonx.data functionality.

---

**Ready to start testing?** Begin with [`unix-scripts/setup-environment.sh`](unix-scripts/setup-environment.sh) and follow the [Testing Guide](unix-scripts/spark-custom-runtime-testing-guide.md)!