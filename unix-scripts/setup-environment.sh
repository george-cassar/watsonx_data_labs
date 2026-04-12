#!/bin/bash
#
# Setup Environment Script for Spark Custom Runtime Testing
# This script helps you set up the environment variables needed for testing
#

set -e

echo "============================================================================"
echo "                Spark Custom Runtime - Environment Setup"
echo "============================================================================"
echo ""
echo "This script will automatically configure your environment for testing"
echo "custom Spark runtime images on watsonx.data."
echo ""
echo "Prerequisites:"
echo "  ✓ OpenShift CLI (oc) must be installed"
echo "  ✓ You must be logged in to OpenShift (oc login already done)"
echo "  ✓ Docker or Podman must be installed"
echo ""
echo "The script will:"
echo "  • Auto-detect your OpenShift environment"
echo "  • Retrieve base Spark image information"
echo "  • Prompt for your container registry details"
echo "  • Generate environment configuration file"
echo ""
read -p "Press Enter to continue..."
echo ""

# Verify oc is installed and logged in
echo "⏳ Verifying OpenShift access..."
if ! command -v oc &> /dev/null; then
    echo "✗ Error: oc command not found"
    echo "  Please install OpenShift CLI and try again"
    exit 1
fi

if ! oc whoami &> /dev/null; then
    echo "✗ Error: Not logged in to OpenShift"
    echo "  Please run 'oc login' first and try again"
    exit 1
fi

echo "✓ Logged in to OpenShift as: $(oc whoami)"
echo "✓ Current project: $(oc project -q)"
echo ""

# Function to prompt for input with default value
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    
    if [ -n "$default" ]; then
        read -p "$prompt [$default]: " value
        value="${value:-$default}"
    else
        read -p "$prompt: " value
    fi
    
    eval "$var_name='$value'"
}

# Auto-detect OpenShift/watsonx.data information
echo "============================================================================"
echo "STEP 1: Detecting OpenShift/watsonx.data Configuration"
echo "============================================================================"
echo ""

# Get current namespace
CURRENT_NAMESPACE=$(oc project -q)
echo "✓ Current OpenShift namespace: $CURRENT_NAMESPACE"
echo ""

# Check if spark-hb-cluster-template exists
echo "⏳ Checking for Spark template configmap..."
if oc get cm -n ${CURRENT_NAMESPACE} spark-hb-cluster-template &> /dev/null; then
    echo "✓ Found spark-hb-cluster-template configmap"
    NAMESPACE="$CURRENT_NAMESPACE"
else
    echo "⚠ spark-hb-cluster-template not found in current namespace"
    echo ""
    prompt_with_default "Enter watsonx.data namespace (where spark-hb-cluster-template exists)" "cpd-instance" NAMESPACE
    
    # Verify the configmap exists in the provided namespace
    if ! oc get cm -n ${NAMESPACE} spark-hb-cluster-template &> /dev/null; then
        echo "✗ Error: spark-hb-cluster-template not found in namespace '${NAMESPACE}'"
        echo "  Please verify the namespace and try again"
        exit 1
    fi
    echo "✓ Found spark-hb-cluster-template in namespace '${NAMESPACE}'"
fi

echo ""

# Select Spark version and retrieve base image
echo "============================================================================"
echo "STEP 2: Select Spark Version and Retrieve Base Image"
echo "============================================================================"
echo ""
echo "Select the Spark version you want to use:"
echo ""
echo "  1) Spark 3.5 (Recommended - os-image-id-jkg35-cp4d-wxd)"
echo "  2) Spark 4.0 (Latest - os-image-id-jkg40-cp4d-wxd)"
echo "  3) Spark 3.4 (Deprecated - os-image-id-jkg34-cp4d-wxd)"
echo ""
read -p "Enter choice [1-3]: " spark_choice

case $spark_choice in
    1)
        SPARK_VERSION="3.5"
        OS_IMAGE_ID="os-image-id-jkg35-cp4d-wxd"
        ;;
    2)
        SPARK_VERSION="4.0"
        OS_IMAGE_ID="os-image-id-jkg40-cp4d-wxd"
        ;;
    3)
        SPARK_VERSION="3.4"
        OS_IMAGE_ID="os-image-id-jkg34-cp4d-wxd"
        echo "⚠ Warning: Spark 3.4 is deprecated"
        ;;
    *)
        echo "Invalid choice. Defaulting to Spark 3.5"
        SPARK_VERSION="3.5"
        OS_IMAGE_ID="os-image-id-jkg35-cp4d-wxd"
        ;;
esac

echo ""
echo "Selected: Spark $SPARK_VERSION ($OS_IMAGE_ID)"
echo ""
echo "⏳ Retrieving base image information from cluster..."
echo ""

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "✗ Error: jq is not installed"
    echo "  jq is required to parse the configmap data"
    echo "  Install jq: https://stedolan.github.io/jq/download/"
    exit 1
fi

# Retrieve registry using the documented command
BASE_REGISTRY=$(oc get cm -n ${NAMESPACE} spark-hb-cluster-template -o=jsonpath='{$.data.os-image-json}' | jq -r ".docs[] | select(._id | test(\"${OS_IMAGE_ID}\")) | \"\(.docker_repo)\"" 2>/dev/null || echo "")

# Retrieve image name using the documented command
BASE_IMAGE_NAME=$(oc get cm -n ${NAMESPACE} spark-hb-cluster-template -o=jsonpath='{$.data.os-image-json}' | jq -r ".docs[] | select(._id | test(\"${OS_IMAGE_ID}\")) | \"\(.docker_image)@\(.docker_image_tag)\"" 2>/dev/null || echo "")

if [ -n "$BASE_REGISTRY" ] && [ -n "$BASE_IMAGE_NAME" ]; then
    echo "✓ Successfully retrieved base image information:"
    echo "  Registry:   $BASE_REGISTRY"
    echo "  Image:      $BASE_IMAGE_NAME"
    echo ""
else
    echo "✗ Error: Could not retrieve base image information"
    echo ""
    echo "This could mean:"
    echo "  • The OS image ID '${OS_IMAGE_ID}' is not found in the configmap"
    echo "  • The configmap structure is different than expected"
    echo ""
    echo "To debug, run:"
    echo "  oc get cm -n ${NAMESPACE} spark-hb-cluster-template -o=jsonpath='{.data.os-image-json}' | jq ."
    echo ""
    exit 1
fi

# Gather custom image information
echo ""
echo "============================================================================"
echo "STEP 3: Custom Image Configuration"
echo "============================================================================"
echo ""
echo "Now specify where you want to store your custom Spark runtime image."
echo ""
echo "→ Container Registry: Where your custom image will be pushed"
echo "  Examples:"
echo "    • Docker Hub: docker.io/yourusername"
echo "    • Quay.io: quay.io/yourusername"
echo "    • OpenShift internal: image-registry.openshift-image-registry.svc:5000/namespace"
echo ""
prompt_with_default "Your container registry URL" "docker.io/yourusername" YOUR_REGISTRY

echo ""
echo "→ Image Name: A descriptive name for your custom image"
echo "  (e.g., 'spark-custom-runtime', 'spark-ml-runtime', etc.)"
echo ""
prompt_with_default "Custom image name" "spark-custom-runtime" YOUR_IMAGE_NAME

echo ""
echo "→ Image Tag: Version tag for your image"
echo "  (e.g., 'v1.0', 'latest', '2024-01', etc.)"
echo ""
prompt_with_default "Custom image tag" "v1.0" YOUR_IMAGE_TAG

# Registry credentials
echo ""
echo "============================================================================"
echo "STEP 4: Registry Authentication"
echo "============================================================================"
echo ""
echo "Does your container registry require authentication?"
echo ""
echo "  • Public registries (like Docker Hub public repos): No"
echo "  • Private registries or private repos: Yes"
echo "  • OpenShift internal registry: Usually yes"
echo ""
read -p "Does your registry require authentication? (y/n) [n]: " needs_auth
needs_auth="${needs_auth:-n}"

if [[ "$needs_auth" =~ ^[Yy]$ ]]; then
    echo ""
    echo "→ Registry Username: Your username for the container registry"
    prompt_with_default "Registry username" "" REGISTRY_USERNAME
    echo ""
    echo "→ Registry Password: Your password or access token"
    echo "  (input will be hidden for security)"
    read -s -p "Registry password: " REGISTRY_PASSWORD
    echo ""
    USE_REGISTRY_AUTH="true"
else
    REGISTRY_USERNAME=""
    REGISTRY_PASSWORD=""
    USE_REGISTRY_AUTH="false"
fi

# Generate environment file
ENV_FILE=".env.spark-custom-runtime"

echo ""
echo "============================================================================"
echo "STEP 5: Generating Configuration"
echo "============================================================================"
echo ""
echo "⏳ Creating environment configuration file..."
cat > $ENV_FILE << EOF
# Spark Custom Runtime Testing Environment Variables
# Generated on: $(date)

# OpenShift/watsonx.data Configuration
export NAMESPACE="${NAMESPACE}"

# Base Spark Image
export BASE_REGISTRY="${BASE_REGISTRY}"
export BASE_IMAGE_NAME="${BASE_IMAGE_NAME}"
export OS_IMAGE_ID="${OS_IMAGE_ID}"
export SPARK_VERSION="${SPARK_VERSION}"

# Custom Image Configuration
export YOUR_REGISTRY="${YOUR_REGISTRY}"
export YOUR_IMAGE_NAME="${YOUR_IMAGE_NAME}"
export YOUR_IMAGE_TAG="${YOUR_IMAGE_TAG}"
export FULL_IMAGE_NAME="${YOUR_REGISTRY}/${YOUR_IMAGE_NAME}:${YOUR_IMAGE_TAG}"

# Registry Authentication
export USE_REGISTRY_AUTH="${USE_REGISTRY_AUTH}"
export REGISTRY_USERNAME="${REGISTRY_USERNAME}"
export REGISTRY_PASSWORD="${REGISTRY_PASSWORD}"

# Derived values
export BASE_FULL_IMAGE="${BASE_REGISTRY}/${BASE_IMAGE_NAME}"
EOF

echo "✓ Environment file created: $ENV_FILE"
echo ""

# Create a summary
echo "============================================================================"
echo "Configuration Summary"
echo "============================================================================"
echo "Namespace:           $NAMESPACE"
echo "Spark Version:       $SPARK_VERSION ($OS_IMAGE_ID)"
echo "Base Image:          $BASE_REGISTRY/$BASE_IMAGE_NAME"
echo "Custom Image:        $YOUR_REGISTRY/$YOUR_IMAGE_NAME:$YOUR_IMAGE_TAG"
echo "Registry Auth:       $USE_REGISTRY_AUTH"
echo ""

echo ""
echo "============================================================================"
echo "STEP 6: Verifying Prerequisites"
echo "============================================================================"
echo ""
echo "⏳ Checking if required tools are installed and configured..."
echo ""

# Check oc command
echo "Checking OpenShift CLI (oc)..."
if command -v oc &> /dev/null; then
    echo "  ✓ oc command found"
    if oc whoami &> /dev/null; then
        echo "  ✓ Logged in to OpenShift as: $(oc whoami)"
        echo "  ✓ Current project: $(oc project -q 2>/dev/null || echo 'none')"
    else
        echo "  ✗ Not logged in to OpenShift"
        echo "  → Action required: Run 'oc login --token=<token> --server=<server>'"
    fi
else
    echo "  ✗ oc command not found"
    echo "  → Action required: Install OpenShift CLI"
    echo "    https://docs.openshift.com/container-platform/latest/cli_reference/openshift_cli/getting-started-cli.html"
fi

echo ""

# Check container runtime (docker or podman)
echo "Checking Container Runtime (Docker/Podman)..."
if command -v podman &> /dev/null; then
    echo "  ✓ podman command found"
    if podman ps &> /dev/null; then
        echo "  ✓ Podman is running"
    else
        echo "  ✗ Podman is not running properly"
        echo "  → Action required: Check podman status"
    fi
elif command -v docker &> /dev/null; then
    echo "  ✓ docker command found"
    if docker ps &> /dev/null; then
        echo "  ✓ Docker daemon is running"
    else
        echo "  ✗ Docker daemon is not running"
        echo "  → Action required: Start Docker and try again"
    fi
else
    echo "  ✗ Neither docker nor podman found"
    echo "  → Action required: Install a container runtime"
    echo "    Docker: https://docs.docker.com/get-docker/"
    echo "    Podman: https://podman.io/getting-started/installation"
fi

echo ""
echo "============================================================================"
echo "                            Setup Complete!"
echo "============================================================================"
echo ""
echo "Your environment has been configured successfully!"
echo ""
echo "📝 Configuration saved to: $ENV_FILE"
echo ""
echo "============================================================================"
echo "Next Steps:"
echo "============================================================================"
echo ""
echo "1️⃣  Load the environment variables:"
echo "    source $ENV_FILE"
echo ""
echo "2️⃣  Create the required customization files:"
echo "    • install-os-packages.sh      (OS packages like vim)"
echo "    • install-python-packages.sh  (Python libraries like pandas, numpy)"
echo "    • install-jar.sh              (Additional JAR files)"
echo "    • Dockerfile                  (Image build instructions)"
echo ""
echo "    See README.md Step 2 for file templates"
echo ""
echo "3️⃣  Build and push your custom image:"
echo "    ./build-and-push.sh"
echo ""
echo "4️⃣  Follow the detailed testing guide:"
echo "    spark-custom-runtime-testing-guide.md"
echo ""
echo "5️⃣  Track your progress with:"
echo "    quick-start-checklist.md"
echo ""
echo "============================================================================"
echo "Need Help?"
echo "============================================================================"
echo ""
echo "• Full documentation: spark-custom-runtime-testing-guide.md"
echo "• Python libraries guide: PYTHON-LIBRARIES-GUIDE.md"
echo "• Quick reference: quick-start-checklist.md"
echo ""