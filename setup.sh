#!/bin/bash
#
# Setup Script for the Video Dubbing Tool
#
# This script automates the setup and execution of the application.
# It checks for dependencies, sets up a virtual environment,
# installs required packages, and runs the application using gunicorn.
#
set -e # Exit immediately if a command exits with a non-zero status.

# ---  configurable variables ---
# Leave these blank to be prompted during setup.
DEFAULT_PORT=""
# --- end of configurable variables ---

VENV_DIR="venv"
PYTHON_CMD="python3"

# --- colors for output ---
C_RESET='\033[0m'
C_RED='\033[0;31m'
C_GREEN='\033[0;32m'
C_BLUE='\033[0;34m'
C_YELLOW='\033[0;33m'

# --- helper functions ---
info() {
    echo -e "${C_BLUE}[INFO]${C_RESET} $1"
}

success() {
    echo -e "${C_GREEN}[SUCCESS]${C_RESET} $1"
}

error() {
    echo -e "${C_RED}[ERROR]${C_RESET} $1"
    exit 1
}

warn() {
    echo -e "${C_YELLOW}[WARNING]${C_RESET} $1"
}

# --- dependency check function ---
check_system_deps() {
    info "Checking system dependencies..."
    local missing_deps=()

    command -v $PYTHON_CMD >/dev/null 2>&1 || missing_deps+=("python3")
    command -v pip3 >/dev/null 2>&1 || missing_deps+=("python3-pip")
    command -v ffmpeg >/dev/null 2>&1 || missing_deps+=("ffmpeg")
    $PYTHON_CMD -m venv --help >/dev/null 2>&1 || missing_deps+=("python3-venv")

    if [ ${#missing_deps[@]} -ne 0 ]; then
        warn "The following dependencies are missing: ${missing_deps[*]}"
        if command -v apt-get >/dev/null 2>&1; then
            info "Attempting to install missing dependencies using apt-get (Debian/Ubuntu)..."
            sudo apt-get update
            for dep in "${missing_deps[@]}"; do
                sudo apt-get install -y "$dep" || error "Failed to install $dep. Please install it manually and re-run the script."
            done
            success "System dependencies installed."
        else
            error "Cannot automatically install dependencies on this system. Please install them manually and re-run the script."
        fi
    else
        success "All system dependencies are already installed."
    fi
}

# --- main logic ---
main() {
    check_system_deps

    # --- Setup Virtual Environment ---
    if [ ! -d "$VENV_DIR" ]; then
        info "Creating Python virtual environment in '$VENV_DIR'..."
        $PYTHON_CMD -m venv "$VENV_DIR" || error "Failed to create virtual environment."
    else
        info "Virtual environment '$VENV_DIR' already exists."
    fi

    info "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"

    # --- Install Python Packages ---
    info "Installing Python dependencies from requirements.txt..."
    pip install -r requirements.txt || error "Failed to install Python packages. Please check requirements.txt and your internet connection."
    success "Python dependencies installed successfully."

    # --- Get Port from User ---
    if [ -z "$DEFAULT_PORT" ]; then
        read -p "Please enter the port to run the application on (e.g., 5000): " APP_PORT
    else
        APP_PORT=$DEFAULT_PORT
    fi

    # Validate port is a number
    if ! [[ "$APP_PORT" =~ ^[0-9]+$ ]]; then
        error "Invalid port number. Please enter a valid number."
    fi

    # --- Check if Port is Available ---
    while lsof -i :$APP_PORT > /dev/null; do
        warn "Port $APP_PORT is already in use."
        read -p "Please enter a different port number: " APP_PORT
        if ! [[ "$APP_PORT" =~ ^[0-9]+$ ]]; then
            error "Invalid port number. Please enter a valid number."
        fi
    done
    info "Port $APP_PORT is available."

    # --- Run Application ---
    info "Starting the application using gunicorn on port $APP_PORT..."
    info "You can access the application at http://0.0.0.0:$APP_PORT"
    info "Press CTRL+C to stop the server."

    gunicorn --bind 0.0.0.0:$APP_PORT --workers 4 app:app

    success "Application stopped."
}

# --- run script ---
main
