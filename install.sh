#!/bin/bash
#
# TVArgenta Installation Script
# This script sets up a Raspberry Pi for TVArgenta
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# LEGACY FUNCTION
# Contains any previous installation steps (currently empty)
# =============================================================================
legacy() {
    log_info "Legacy function - no previous installation steps defined"
    # This function is a placeholder for any existing installation logic
    # that was present before the modular refactoring
}

# =============================================================================
# BOOTLOADER SETUP
# Configures /boot/firmware/config.txt and cmdline.txt for TVArgenta
# =============================================================================
setup_bootloader() {
    log_info "Setting up bootloader configuration..."

    local CONFIG_FILE="/boot/firmware/config.txt"
    local CMDLINE_FILE="/boot/firmware/cmdline.txt"

    # Backup original files
    if [[ ! -f "${CONFIG_FILE}.original" ]]; then
        sudo cp "$CONFIG_FILE" "${CONFIG_FILE}.original"
        log_info "Backed up original config.txt"
    fi

    if [[ ! -f "${CMDLINE_FILE}.original" ]]; then
        sudo cp "$CMDLINE_FILE" "${CMDLINE_FILE}.original"
        log_info "Backed up original cmdline.txt"
    fi

    # --- config.txt modifications ---
    log_info "Modifying config.txt..."

    # Comment out onboard audio (we use HiFiBerry DAC)
    if grep -q "^dtparam=audio=on" "$CONFIG_FILE"; then
        sudo sed -i 's/^dtparam=audio=on/#dtparam=audio=on/' "$CONFIG_FILE"
        log_info "Disabled onboard audio"
    fi

    # Switch from vc4-kms-v3d to vc4-fkms-v3d (legacy fake KMS for mpv DRM)
    if grep -q "^dtoverlay=vc4-kms-v3d" "$CONFIG_FILE"; then
        sudo sed -i 's/^dtoverlay=vc4-kms-v3d/#dtoverlay=vc4-kms-v3d\ndtoverlay=vc4-fkms-v3d/' "$CONFIG_FILE"
        log_info "Switched to vc4-fkms-v3d (legacy fake KMS)"
    fi

    # Check if [all] section exists and add our customizations
    if ! grep -q "^dtoverlay=hifiberry-dac" "$CONFIG_FILE"; then
        # Remove any existing [all] section content we might add
        # and append our configuration at the end

        # First, check if there's already an [all] section
        if grep -q "^\[all\]" "$CONFIG_FILE"; then
            # Append after [all] section
            sudo sed -i '/^\[all\]/a\
# TVArgenta HiFiBerry DAC audio setup\
dtparam=i2s=on\
dtoverlay=i2s-mmap\
dtoverlay=hifiberry-dac\
\
# Clean boot appearance\
disable_splash=1\
\
# Disable onboard Bluetooth (using USB dongle)\
dtoverlay=disable-bt' "$CONFIG_FILE"
        else
            # Add [all] section at the end
            echo "" | sudo tee -a "$CONFIG_FILE" > /dev/null
            echo "[all]" | sudo tee -a "$CONFIG_FILE" > /dev/null
            echo "# TVArgenta HiFiBerry DAC audio setup" | sudo tee -a "$CONFIG_FILE" > /dev/null
            echo "dtparam=i2s=on" | sudo tee -a "$CONFIG_FILE" > /dev/null
            echo "dtoverlay=i2s-mmap" | sudo tee -a "$CONFIG_FILE" > /dev/null
            echo "dtoverlay=hifiberry-dac" | sudo tee -a "$CONFIG_FILE" > /dev/null
            echo "" | sudo tee -a "$CONFIG_FILE" > /dev/null
            echo "# Clean boot appearance" | sudo tee -a "$CONFIG_FILE" > /dev/null
            echo "disable_splash=1" | sudo tee -a "$CONFIG_FILE" > /dev/null
            echo "" | sudo tee -a "$CONFIG_FILE" > /dev/null
            echo "# Disable onboard Bluetooth (using USB dongle)" | sudo tee -a "$CONFIG_FILE" > /dev/null
            echo "dtoverlay=disable-bt" | sudo tee -a "$CONFIG_FILE" > /dev/null
        fi
        log_info "Added HiFiBerry DAC and boot customizations"
    else
        log_warn "HiFiBerry DAC config already present, skipping"
    fi

    # Remove enable_uart if present (not needed for production)
    if grep -q "^enable_uart=1" "$CONFIG_FILE"; then
        sudo sed -i 's/^enable_uart=1/#enable_uart=1/' "$CONFIG_FILE"
        log_info "Disabled UART (not needed for production)"
    fi

    # --- cmdline.txt modifications ---
    log_info "Modifying cmdline.txt..."

    local CMDLINE=$(cat "$CMDLINE_FILE")
    local MODIFIED=false

    # Remove serial console if present
    if echo "$CMDLINE" | grep -q "console=serial0,115200"; then
        CMDLINE=$(echo "$CMDLINE" | sed 's/console=serial0,115200 //')
        MODIFIED=true
        log_info "Removed serial console"
    fi

    # Add silent boot parameters if not present
    if ! echo "$CMDLINE" | grep -q "loglevel=0"; then
        CMDLINE="$CMDLINE loglevel=0"
        MODIFIED=true
    fi

    if ! echo "$CMDLINE" | grep -q "systemd.show_status=0"; then
        CMDLINE="$CMDLINE systemd.show_status=0"
        MODIFIED=true
    fi

    if ! echo "$CMDLINE" | grep -q "udev.log_level=3"; then
        CMDLINE="$CMDLINE udev.log_level=3"
        MODIFIED=true
    fi

    if ! echo "$CMDLINE" | grep -q "vt.global_cursor_default=0"; then
        CMDLINE="$CMDLINE vt.global_cursor_default=0"
        MODIFIED=true
    fi

    if ! echo "$CMDLINE" | grep -q "logo.nologo"; then
        CMDLINE="$CMDLINE logo.nologo"
        MODIFIED=true
    fi

    if [[ "$MODIFIED" == true ]]; then
        echo "$CMDLINE" | sudo tee "$CMDLINE_FILE" > /dev/null
        log_info "Added silent boot parameters to cmdline.txt"
    else
        log_warn "cmdline.txt already configured, skipping"
    fi

    log_info "Bootloader setup complete!"
    log_warn "A reboot is required for changes to take effect"
}
