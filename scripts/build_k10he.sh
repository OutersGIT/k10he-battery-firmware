#!/usr/bin/env bash
#
# Build the Keychron K10 HE (ISO) firmware with the custom battery raw-HID
# command applied.
#
# Prerequisites:
#   * QMK MSYS (Windows) or a working QMK build environment.
#   * A QMK Firmware checkout with the patch from ../patches/ already applied
#     (see the repository README for the exact steps).
#
# Usage (run from inside the QMK Firmware root, OR pass it as the first arg):
#
#     /path/to/build_k10he.sh [QMK_ROOT]
#
# It will:
#   1. Fetch the Keychron ChibiOS submodules into lib/ (only if missing)
#   2. Build keychron/k10_he/iso:keychron
#   3. Tell you where the resulting firmware is.
#
set -euo pipefail

QMK_ROOT="${1:-$PWD}"

if [ ! -f "$QMK_ROOT/Makefile" ] || [ ! -d "$QMK_ROOT/keyboards/keychron" ]; then
    echo "ERROR: '$QMK_ROOT' does not look like a QMK Firmware checkout." >&2
    echo "Run this from the QMK root, or pass the QMK root as the first argument." >&2
    exit 1
fi

cd "$QMK_ROOT"
echo "==> QMK root: $QMK_ROOT"

# --- Fetch submodules required for the STM32F401 / Keychron build ------------
clone_if_empty () {
    local path="$1" url="$2" branch="${3:-}"
    if [ -n "$(ls -A "$path" 2>/dev/null || true)" ]; then
        echo "    [skip] $path already populated"
        return
    fi
    echo "    [clone] $url ${branch:+($branch)} -> $path"
    rm -rf "$path"
    if [ -n "$branch" ]; then
        git clone --depth 1 --recurse-submodules -b "$branch" "$url" "$path"
    else
        git clone --depth 1 "$url" "$path"
    fi
}

echo "==> Fetching submodules (this may take a minute the first time)"
clone_if_empty "lib/chibios"         "https://github.com/Keychron/ChibiOS"         "25q3"
clone_if_empty "lib/chibios-contrib" "https://github.com/Keychron/ChibiOS-Contrib" "chibios-21.11.x"
clone_if_empty "lib/lufa"            "https://github.com/qmk/lufa"
clone_if_empty "lib/printf"          "https://github.com/qmk/printf"

# --- Build -------------------------------------------------------------------
echo "==> Building keychron/k10_he/iso:keychron"
make keychron/k10_he/iso:keychron

echo
echo "==> Build finished. Resulting firmware:"
ls -la "$QMK_ROOT"/keychron_k10_he_iso_keychron.* 2>/dev/null || ls -la "$QMK_ROOT"/*.bin 2>/dev/null || true
echo
echo "To flash: put the keyboard in bootloader mode (unplug USB, set the mode"
echo "switch to 'Cable', hold Esc, plug USB back in), then run flash_k10he.sh"
echo "or load the .bin with QMK Toolbox."
