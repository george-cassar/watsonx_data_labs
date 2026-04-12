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