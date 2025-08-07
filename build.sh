#!/bin/bash

# Build script for Render deployment with Chrome support
echo "🚀 Starting build process for English Learning App..."

# Update package lists
echo "📦 Updating package lists..."
apt-get update

# Install Chrome dependencies
echo "🌐 Installing Chrome and dependencies..."
apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1

# Add Google Chrome repository
echo "🔑 Adding Google Chrome repository..."
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list

# Update package lists again
apt-get update

# Install Google Chrome
echo "🌐 Installing Google Chrome..."
apt-get install -y google-chrome-stable

# Verify Chrome installation
echo "✅ Verifying Chrome installation..."
google-chrome --version || echo "⚠️ Chrome installation verification failed"

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install -r requirements.txt

echo "✅ Build completed successfully!"

# Set Chrome binary path for Selenium
export GOOGLE_CHROME_BIN=/usr/bin/google-chrome-stable
echo "🎯 Chrome binary path set: $GOOGLE_CHROME_BIN"
