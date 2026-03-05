#!/bin/bash

# EC2 Setup Script for AWS FCJ Project
# Run this script on your EC2 instance to prepare for deployment

set -e

echo "Setting up EC2 instance for AWS FCJ Project..."

# Update system
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
echo "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "Docker installed successfully"
else
    echo "Docker already installed"
fi

# Install Git
echo "Installing Git..."
if ! command -v git &> /dev/null; then
    sudo apt-get install -y git
    echo "Git installed successfully"
else
    echo "Git already installed"
fi

# Create app directory
APP_DIR="${HOME}/aws-fcj-project"
echo "Creating app directory at ${APP_DIR}..."
mkdir -p ${APP_DIR}

# Notes for GitHub Actions based deployment
echo ""
echo "MANUAL STEP REQUIRED:"
echo "1. Ensure this instance was created with the correct EC2 key pair (Terraform variable: ec2_key_name)."
echo "   The matching private key must be stored in GitHub secret: EC2_SSH_PRIVATE_KEY."
echo ""
echo "2. Re-login after Docker install so your SSH user can run docker without sudo:"
echo "   exit"
echo "   # SSH back in"
echo "   docker ps"
echo ""
echo "3. You do NOT need to clone the repo on the instance for the default workflow."
echo "   GitHub Actions will copy the backend .env via scp and run the GHCR image via docker."
echo ""

# Configure firewall
echo "Configuring firewall..."
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8000/tcp  # Backend API
sudo ufw --force enable
echo "Firewall configured"

# Display versions
echo ""
echo "Setup complete! Installed versions:"
docker --version
git --version

echo ""
echo "Next steps:"
echo "1. Complete the manual steps above"
echo "2. Set up GitHub Actions secrets"
echo "3. Push code to trigger deployment"
echo ""
echo "EC2 instance is ready for deployment!"
