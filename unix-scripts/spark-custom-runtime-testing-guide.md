# Testing Guide: Submitting Spark Application with Custom Runtime Image on watsonx.data

This guide provides step-by-step instructions to test the process of submitting a Spark application using a custom runtime image on IBM watsonx.data deployed on OpenShift.

**Documentation Reference:** [IBM watsonx.data - Submitting Spark application by using custom runtime image](https://www.ibm.com/docs/en/watsonxdata/standard/2.3.x?topic=ssabunse-submitting-spark-application-by-using-custom-runtime-image)

---

## Prerequisites

Before starting, ensure you have:

1. **Access to watsonx.data cluster** with Spark engine installed
2. **Administrator privileges** to run `oc` and container commands
3. **Container runtime** - Either Docker or Podman installed
4. **Base image ID** for your Spark version:
   - Spark 3.4 (Deprecated): `os-image-id-jkg34-cp4d-wxd`
   - Spark 3.5: `os-image-id-jkg35-cp4d-wxd`
   - Spark 4.0: `os-image-id-jkg40-cp4d-wxd`
5. **Container registry** access (e.g., Docker Hub, OpenShift internal registry, or private registry)

**Note:** This guide uses `docker` commands, but all commands work with `podman` as well. Simply replace `docker` with `podman` in all commands, or create an alias: `alias docker=podman`

---

## Step 1: Verify Prerequisites

### 1.1 Check OpenShift Access
```bash
# Login to OpenShift cluster
oc login --token=<your-token> --server=<your-server-url>

# Verify you're in the correct namespace where watsonx.data is installed
oc project <cpd-instance-namespace>

# Check if Spark engine is running
oc get pods | grep spark
```

### 1.2 Verify Container Runtime (Docker or Podman)

**For Docker:**
```bash
# Check Docker is installed and running
docker --version
docker ps

# Login to your container registry
docker login <your-registry-url>
```

**For Podman:**
```bash
# Check Podman is installed
podman --version
podman ps

# Login to your container registry
podman login <your-registry-url>

# Optional: Create alias for compatibility
alias docker=podman
```

**Note:** Podman is a drop-in replacement for Docker. All `docker` commands in this guide work with `podman` by simply replacing the command name.

### 1.3 Identify Your Spark Version
```bash
# Check which Spark version is deployed
oc get cm -n <namespace> | grep spark
```

---

## Step 2: Retrieve Base Spark Image

### 2.1 Get Registry and Image Information
```bash
# Get the internal registry URL from OpenShift
REGISTRY=$(oc get cm -n cpd-instance spark-hb-cluster-config -o jsonpath='{.data.registry}')
echo "Registry: $REGISTRY"

# Get the base image name for your Spark version
# Replace <os-image-id> with the appropriate ID for your Spark version
IMAGE_NAME=$(oc get cm -n cpd-instance spark-hb-cluster-config -o jsonpath='{.data.image}')
echo "Base Image: $IMAGE_NAME"
```

### 2.2 Pull the Base Image
```bash
# Set variables (replace with your actual values)
REGISTRY="<your-registry-url>"
IMAGE_NAME="<base-spark-image-name>"

# Pull the base image
docker pull ${REGISTRY}/${IMAGE_NAME}

# Tag it for easier reference
docker tag ${REGISTRY}/${IMAGE_NAME} spark-base:latest
```

---

## Step 3: Create Customization Scripts

### 3.1 Create `install-os-packages.sh`
This script installs operating system packages needed by your application.

```bash
cat > install-os-packages.sh << 'EOF'
#!/bin/bash
set -e -o pipefail

# Install operating system packages
microdns update -y
microdns install -y vim

# Add any other OS packages your application needs
# microdns install -y <package-name>
EOF

chmod +x install-os-packages.sh
```

### 3.2 Create `install-python-packages.sh`
This script installs custom Python libraries needed by your Spark application.

```bash
cat > install-python-packages.sh << 'EOF'
#!/bin/bash
set -e -o pipefail

# Install custom Python packages
pip install --no-cache-dir \
    pandas==2.0.3 \
    numpy==1.24.3 \
    scikit-learn==1.3.0 \
    matplotlib==3.7.2 \
    seaborn==0.12.2

# Add more packages as needed
# pip install --no-cache-dir <package-name>==<version>

# Verify installations
echo "Verifying Python package installations..."
python3 -c "import pandas; print(f'pandas version: {pandas.__version__}')"
python3 -c "import numpy; print(f'numpy version: {numpy.__version__}')"
python3 -c "import sklearn; print(f'scikit-learn version: {sklearn.__version__}')"

echo "Python packages installed successfully!"
EOF

chmod +x install-python-packages.sh
```

**Note:** You can customize the Python packages based on your application needs. Always specify versions for reproducibility.

### 3.3 Create `install-jar.sh`
This script downloads additional JAR files required by your application.

```bash
cat > install-jar.sh << 'EOF'
#!/bin/bash
set -e -o pipefail

# Install additional JAR files
# Example: Download a JAR from Maven repository
wget -c -P /opt/ibm/spark/external-jars/ \
  https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-databind/2.13.0/jackson-databind-2.13.0.jar

# Add more JAR downloads as needed
# wget -c -P /opt/ibm/spark/external-jars/ <jar-url>
EOF

chmod +x install-jar.sh
```

---

## Step 4: Create Dockerfile

Create a `Dockerfile` that extends the base Spark image with your customizations:

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

**Note:** This Dockerfile installs OS packages, Python libraries, and JAR files. You can customize the order or remove any step you don't need.

---

## Step 5: Build the Custom Docker Image

### 5.1 Set Build Variables
```bash
# Set your registry URL
YOUR_REGISTRY="<your-registry-url>"

# Set your custom image name
YOUR_IMAGE_NAME="spark-custom-runtime:v1.0"

# Set the base image registry and name
REGISTRY="<base-image-registry>"
IMAGE_NAME="<base-image-name>"
```

### 5.2 Build the Image
```bash
# Build the custom image
docker build -t ${YOUR_REGISTRY}/${YOUR_IMAGE_NAME} \
  --build-arg REGISTRY=${REGISTRY} \
  --build-arg IMAGE_NAME=${IMAGE_NAME} \
  .

# Verify the image was created
docker images | grep spark-custom-runtime
```

---

## Step 6: Push Image to Container Registry

### 6.1 Push to Registry
```bash
# Push the custom image to your registry
docker push ${YOUR_REGISTRY}/${YOUR_IMAGE_NAME}

# Verify the push was successful
docker pull ${YOUR_REGISTRY}/${YOUR_IMAGE_NAME}
```

### 6.2 Make Image Accessible to OpenShift (if using external registry)
If using an external registry, ensure OpenShift can pull the image:

```bash
# Create image pull secret if needed
oc create secret docker-registry my-registry-secret \
  --docker-server=${YOUR_REGISTRY} \
  --docker-username=<username> \
  --docker-password=<password> \
  --docker-email=<email> \
  -n <cpd-instance-namespace>

# Link the secret to the service account
oc secrets link spark <secret-name> --for=pull -n <cpd-instance-namespace>
```

---

## Step 7: Create Spark Application Configuration

### 7.1 Create Application Files
First, create a simple Spark application for testing:

```bash
mkdir -p /opt/ibm/spark/examples/src/main
cat > /opt/ibm/spark/examples/src/main/test-app.py << 'EOF'
from pyspark.sql import SparkSession
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

spark = SparkSession.builder.appName("CustomRuntimeTest").getOrCreate()

# Test custom runtime with Python libraries
print("=" * 60)
print("Testing Custom Runtime Image with Python Libraries")
print("=" * 60)

# Test 1: Basic Spark DataFrame
print("\n1. Testing Spark DataFrame:")
data = [("Alice", 34), ("Bob", 45), ("Charlie", 28)]
df = spark.createDataFrame(data, ["Name", "Age"])
df.show()

# Test 2: Verify custom Python packages
print("\n2. Verifying Custom Python Packages:")
print(f"   - pandas version: {pd.__version__}")
print(f"   - numpy version: {np.__version__}")
print(f"   - scikit-learn available: Yes")

# Test 3: Use pandas with Spark
print("\n3. Testing pandas integration:")
pandas_df = pd.DataFrame({
    'x': [1, 2, 3, 4, 5],
    'y': [2, 4, 5, 4, 5]
})
spark_df = spark.createDataFrame(pandas_df)
print("   Pandas DataFrame converted to Spark DataFrame:")
spark_df.show()

# Test 4: Use numpy
print("\n4. Testing numpy operations:")
arr = np.array([1, 2, 3, 4, 5])
print(f"   Array mean: {np.mean(arr)}")
print(f"   Array std: {np.std(arr)}")

# Test 5: Use scikit-learn
print("\n5. Testing scikit-learn:")
X = np.array([[1], [2], [3], [4], [5]])
y = np.array([2, 4, 5, 4, 5])
model = LinearRegression()
model.fit(X, y)
print(f"   Linear regression coefficient: {model.coef_[0]:.2f}")
print(f"   Linear regression intercept: {model.intercept_:.2f}")

print("\n" + "=" * 60)
print("Custom runtime test completed successfully!")
print("All custom Python packages are working correctly!")
print("=" * 60)

spark.stop()
EOF
```

**Note:** This test application verifies that all custom Python libraries (pandas, numpy, scikit-learn) are properly installed and working in the Spark environment.

### 7.2 Create Job Configuration JSON
Create a JSON configuration file that specifies your custom image:

```bash
cat > spark-job-config.json << 'EOF'
{
  "application_details": {
    "application": "/opt/ibm/spark/examples/src/main/test-app.py",
    "arguments": ["/opt/ibm/spark/examples/src/main/sample.csv"],
    "conf": {
      "ae.spark.kubernetes.container.image": "<YOUR_REGISTRY>/<YOUR_IMAGE_NAME>",
      "ae.spark.kubernetes.container.registry.name": "<registry-name>",
      "ae.spark.kubernetes.container.registry.username": "<username>",
      "ae.spark.kubernetes.container.registry.password": "<password>"
    }
  }
}
EOF
```

**Important:** 
- Replace `<YOUR_REGISTRY>/<YOUR_IMAGE_NAME>` with your actual custom image
- If your registry is publicly accessible without authentication, remove the `registry.username` and `registry.password` fields

---

## Step 8: Submit the Spark Application

### 8.1 Submit via watsonx.data UI
1. Log in to watsonx.data web console
2. Navigate to **Query workspace** → **Spark applications**
3. Click **Create application**
4. Upload or paste your job configuration JSON
5. Click **Submit**

### 8.2 Submit via CLI (Alternative)
```bash
# Using curl to submit the job
curl -X POST https://<wxd-hostname>/lakehouse/api/v2/spark_engines/<engine-id>/applications \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d @spark-job-config.json
```

---

## Step 9: Monitor and Verify

### 9.1 Check Application Status
```bash
# Monitor pods in OpenShift
oc get pods -n <namespace> | grep spark

# Watch pod logs
oc logs -f <spark-driver-pod-name> -n <namespace>
```

### 9.2 Verify Custom Runtime
Check the logs to confirm:
- Custom packages are available
- Custom JARs are loaded
- Application runs successfully

### 9.3 Expected Output
You should see:
```
==================================================
Testing Custom Runtime Image
==================================================
Sample DataFrame:
+-------+---+
|   Name|Age|
+-------+---+
|  Alice| 34|
|    Bob| 45|
|Charlie| 28|
+-------+---+

Custom runtime test completed successfully!
```

---

## Troubleshooting

### Issue: Image Pull Errors
**Solution:** Verify registry credentials and image pull secrets
```bash
oc get secrets -n <namespace>
oc describe pod <spark-pod-name> -n <namespace>
```

### Issue: Custom Packages Not Found
**Solution:** Verify the Dockerfile build process completed successfully
```bash
docker run -it ${YOUR_REGISTRY}/${YOUR_IMAGE_NAME} /bin/bash
# Inside container, check if packages are installed
which vim
ls -la /opt/ibm/spark/external-jars/
```

### Issue: Application Fails to Start
**Solution:** Check Spark driver logs
```bash
oc logs <spark-driver-pod> -n <namespace>
```

---

## Cleanup

After testing, clean up resources:

```bash
# Delete test application files
rm -f spark-job-config.json test-app.py

# Remove local Docker images (optional)
docker rmi ${YOUR_REGISTRY}/${YOUR_IMAGE_NAME}
docker rmi spark-base:latest

# Delete image pull secrets (if created)
oc delete secret my-registry-secret -n <namespace>
```

---

## Next Steps

1. **Customize further:** Add more packages, libraries, or configurations to your custom image
2. **Automate:** Create CI/CD pipelines to build and deploy custom images
3. **Version control:** Tag images with versions for better tracking
4. **Security:** Scan images for vulnerabilities before deployment
5. **Performance:** Monitor application performance with custom runtime vs. base runtime

---

## Additional Resources

- [IBM watsonx.data Documentation](https://www.ibm.com/docs/en/watsonxdata)
- [Supported Spark versions](https://www.ibm.com/docs/en/watsonxdata/standard/2.3.x)
- [OpenShift Container Platform Documentation](https://docs.openshift.com/)
- [Docker Documentation](https://docs.docker.com/)