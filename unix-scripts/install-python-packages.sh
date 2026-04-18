#!/bin/bash
#
# ============================================================================
# Install Custom Python Packages for Spark Runtime
# ============================================================================
#
# Purpose:
#   Installs Python libraries required by Spark applications into the
#   custom runtime image's site-packages directory.
#
# Usage:
#   This script is executed during the Docker image build process.
#   It can also be run manually for testing:
#     bash unix-scripts/install-python-packages.sh
#
# Target Directory:
#   /opt/ibm/conda/miniforgePy3.11/lib/python3.11/site-packages
#   This is the site-packages directory for the Python 3.11 environment
#   used by the Spark runtime in watsonx.data.
#
# Installed Packages:
#   - pandas==2.0.3    : Data manipulation and analysis library
#   - numpy==1.24.3    : Numerical computing library
#   - lxml==5.1.0      : XML/HTML processing library
#
# Notes:
#   - Uses --no-cache-dir to reduce image size
#   - Uses --target to install to specific directory
#   - Versions are pinned for reproducibility
#   - Script exits on any error (set -e)
#   - Pipefail ensures errors in pipes are caught
#
# Last Modified: 2026-04-18
# ============================================================================

# Exit immediately if a command exits with a non-zero status
# -e: Exit on error
# -o pipefail: Return value of a pipeline is the status of the last command
#              to exit with a non-zero status, or zero if all succeed
set -e -o pipefail

# ============================================================================
# Configuration
# ============================================================================

# Target installation directory
# This is the site-packages directory for Python 3.11 in the Spark runtime
TARGET_DIR="/opt/ibm/conda/miniforgePy3.11/lib/python3.11/site-packages"

# ============================================================================
# Installation Process
# ============================================================================

echo "============================================================================"
echo "Installing Custom Python Packages"
echo "============================================================================"
echo "Target Directory: $TARGET_DIR"
echo ""

# Install pip packages to the specified site-packages directory
# --no-cache-dir: Don't cache downloaded packages (reduces image size)
# --target: Install packages to the specified directory
pip install --no-cache-dir --target="$TARGET_DIR" \
    pandas==2.0.3 \
    numpy==1.24.3 \
    lxml==5.1.0

echo ""
echo "============================================================================"
echo "✓ Packages installed successfully to $TARGET_DIR"
echo "============================================================================"

# ============================================================================
# Adding More Packages
# ============================================================================
#
# To add more packages, uncomment and modify the following template:
#
# pip install --no-cache-dir --target="$TARGET_DIR" \
#     <package-name>==<version>
#
# Examples:
#   - requests==2.31.0        : HTTP library
#   - beautifulsoup4==4.12.3  : HTML/XML parsing
#   - scikit-learn==1.3.0     : Machine learning library
#   - matplotlib==3.8.0       : Plotting library
#
# Best Practices:
#   1. Always pin versions for reproducibility
#   2. Test packages in development before adding to production
#   3. Keep this list organized and commented
#   4. Document why each package is needed
#
# ============================================================================