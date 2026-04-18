#!/bin/bash
#
# Install Custom Python Packages
# This script installs Python libraries required by your Spark application
#

set -e -o pipefail

echo "Installing custom Python packages..."

# Install pip packages
pip install --no-cache-dir \
    pandas==2.0.3 \
    numpy==1.24.3 \
    lxml==5.1.0

# Add more packages as needed
# pip install --no-cache-dir <package-name>==<version>