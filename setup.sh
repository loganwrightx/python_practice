#!/bin/bash
# Author: Logan Wright
# Date: 10/03/2026
# Description: This script sets up a Python virtual environment and installs dependencies needed to run these projects

set -e

PYTHON_EXE=python3.13

# Try to setup the virtual environment, or fail if python has any issues
{
    # Grab the full python version
    PYTHON_VERSION="$($PYTHON_EXE --version)"
    # Create the venv
    $PYTHON_EXE -m venv .venv
    # Activate the virtual environment
    . ./.venv/bin/activate
    # Upgrade pip
    pip install --upgrade pip
} 2>/dev/null || {
    echo "python3 is not a valid command either. Please make sure python 3.13 is installed on your machine and try again!"
    exit 1
}

# Then install dependencies
pip install -r requirements.txt

echo "Virtual environment created at ./.venv/ with $PYTHON_VERSION"