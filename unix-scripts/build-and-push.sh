#!/bin/bash
#
# Build and Push Custom Spark Runtime Image
# This script automates the container image build and push process
# Supports both Docker and Podman
#

set -e

# Detect container runtime (docker or podman)
if command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
    echo "Using Podman as container runtime"
elif command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
    echo "Using Docker as container runtime"
else
    echo "Error: Neither docker nor podman found. Please install one of them."
    exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load environment variables
if [ -f ".env.spark-custom-runtime" ]; then
    source .env.spark-custom-runtime
    echo -e "${GREEN}✓ Loaded environment from .env.spark-custom-runtime${NC}"
else
    echo -e "${RED}✗ Environment file not found!${NC}"
    echo "Please run setup-environment.sh first"
    exit 1
fi

echo "=========================================="
echo "Build and Push Custom Spark Runtime Image"
echo "=========================================="
echo ""

# Verify required files exist
echo "=== Verifying Required Files ==="
required_files=("Dockerfile" "install-os-packages.sh" "install-python-packages.sh" "install-jar.sh")
missing_files=()

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file (missing)"
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -ne 0 ]; then
    echo ""
    echo -e "${RED}Error: Missing required files!${NC}"
    echo "Please create the following files before building:"
    for file in "${missing_files[@]}"; do
        echo "  - $file"
    done
    exit 1
fi

echo ""

# Display build configuration
echo "=== Build Configuration ==="
echo "Base Image:    $BASE_FULL_IMAGE"
echo "Custom Image:  $FULL_IMAGE_NAME"
echo "Registry:      $YOUR_REGISTRY"
echo ""

# Confirm before proceeding
read -p "Proceed with build? (y/n) [y]: " confirm
confirm="${confirm:-y}"

if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Build cancelled."
    exit 0
fi

# Step 1: Pull base image
echo ""
echo "=== Step 1: Pulling Base Image ==="
echo "Pulling: $BASE_FULL_IMAGE"

if $CONTAINER_CMD pull "$BASE_FULL_IMAGE"; then
    echo -e "${GREEN}✓ Base image pulled successfully${NC}"
else
    echo -e "${YELLOW}⚠ Could not pull base image directly${NC}"
    echo "You may need to:"
    echo "  1. Login to OpenShift registry: oc registry login"
    echo "  2. Or use: $CONTAINER_CMD login -u \$(oc whoami) -p \$(oc whoami -t) $BASE_REGISTRY"
    read -p "Continue anyway? (y/n) [n]: " continue_anyway
    continue_anyway="${continue_anyway:-n}"
    if [[ ! "$continue_anyway" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 2: Build custom image
echo ""
echo "=== Step 2: Building Custom Image ==="
echo "Building: $FULL_IMAGE_NAME"

if $CONTAINER_CMD build -t "$FULL_IMAGE_NAME" \
    --build-arg REGISTRY="$BASE_REGISTRY" \
    --build-arg IMAGE_NAME="$BASE_IMAGE_NAME" \
    .; then
    echo -e "${GREEN}✓ Image built successfully${NC}"
else
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi

# Verify image was created
echo ""
echo "=== Verifying Built Image ==="
if $CONTAINER_CMD images | grep -q "$YOUR_IMAGE_NAME"; then
    echo -e "${GREEN}✓ Image found in local registry${NC}"
    $CONTAINER_CMD images | grep "$YOUR_IMAGE_NAME"
else
    echo -e "${RED}✗ Image not found in local registry${NC}"
    exit 1
fi

# Step 3: Test image (optional)
echo ""
read -p "Test the image before pushing? (y/n) [y]: " test_image
test_image="${test_image:-y}"

if [[ "$test_image" =~ ^[Yy]$ ]]; then
    echo "=== Testing Image ==="
    echo "Running container to verify customizations..."
    
    # Test if vim is installed (from install-os-packages.sh)
    if $CONTAINER_CMD run --rm "$FULL_IMAGE_NAME" which vim &> /dev/null; then
        echo -e "${GREEN}✓ Custom OS packages verified (vim found)${NC}"
    else
        echo -e "${YELLOW}⚠ Could not verify vim installation${NC}"
    fi
    
    # Test if Python packages are installed
    if $CONTAINER_CMD run --rm "$FULL_IMAGE_NAME" python3 -c "import pandas; import numpy; import sklearn" &> /dev/null; then
        echo -e "${GREEN}✓ Custom Python packages verified${NC}"
        $CONTAINER_CMD run --rm "$FULL_IMAGE_NAME" python3 -c "import pandas; import numpy; import sklearn; print(f'pandas: {pandas.__version__}, numpy: {numpy.__version__}')"
    else
        echo -e "${YELLOW}⚠ Could not verify Python packages${NC}"
    fi
    
    # Test if custom JARs directory exists
    if $CONTAINER_CMD run --rm "$FULL_IMAGE_NAME" ls /opt/ibm/spark/external-jars/ &> /dev/null; then
        echo -e "${GREEN}✓ External JARs directory exists${NC}"
        echo "Contents:"
        $CONTAINER_CMD run --rm "$FULL_IMAGE_NAME" ls -lh /opt/ibm/spark/external-jars/
    else
        echo -e "${YELLOW}⚠ Could not verify external JARs directory${NC}"
    fi
fi

# Step 4: Login to registry
echo ""
echo "=== Step 3: Registry Authentication ==="

if [ "$USE_REGISTRY_AUTH" = "true" ]; then
    echo "Logging in to $YOUR_REGISTRY..."
    if echo "$REGISTRY_PASSWORD" | $CONTAINER_CMD login "$YOUR_REGISTRY" -u "$REGISTRY_USERNAME" --password-stdin; then
        echo -e "${GREEN}✓ Logged in to registry${NC}"
    else
        echo -e "${RED}✗ Registry login failed${NC}"
        exit 1
    fi
else
    echo "No authentication required (public registry)"
fi

# Step 5: Push image
echo ""
echo "=== Step 4: Pushing Image to Registry ==="
echo "Pushing: $FULL_IMAGE_NAME"

if $CONTAINER_CMD push "$FULL_IMAGE_NAME"; then
    echo -e "${GREEN}✓ Image pushed successfully${NC}"
else
    echo -e "${RED}✗ Push failed${NC}"
    exit 1
fi

# Step 6: Verify push
echo ""
echo "=== Step 5: Verifying Push ==="
echo "Attempting to pull image from registry..."

if $CONTAINER_CMD pull "$FULL_IMAGE_NAME"; then
    echo -e "${GREEN}✓ Image successfully pulled from registry${NC}"
else
    echo -e "${YELLOW}⚠ Could not verify image in registry${NC}"
fi

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}Build and Push Complete!${NC}"
echo "=========================================="
echo ""
echo "Image Details:"
echo "  Name:     $FULL_IMAGE_NAME"
echo "  Registry: $YOUR_REGISTRY"
echo "  Tag:      $YOUR_IMAGE_TAG"
echo ""
echo "Next Steps:"
echo "1. Create your Spark application configuration"
echo "2. Update the job config JSON with this image:"
echo "   \"ae.spark.kubernetes.container.image\": \"$FULL_IMAGE_NAME\""
echo "3. Submit your Spark application"
echo ""
echo "For detailed instructions, see: spark-custom-runtime-testing-guide.md"
echo ""