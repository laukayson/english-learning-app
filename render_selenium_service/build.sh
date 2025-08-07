#!/bin/bash

# Render build script for Selenium service
echo "Starting build process..."

# Install Python dependencies first
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Chrome will be installed by webdriver-manager automatically
echo "Chrome will be auto-installed by webdriver-manager during runtime"

echo "Build completed successfully!"
