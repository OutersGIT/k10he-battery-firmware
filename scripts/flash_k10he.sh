#!/usr/bin/env bash
#
# Flash the freshly built K10 HE (ISO) firmware over DFU.
#
# This script WAITS for the keyboard to appear in bootloader mode, so you can
# start it first and then put the keyboard into the bootloader:
#   1. Unplug the USB cable
#   2. Set the side mode switch to "Cable"
#   3. Hold the Esc key (or the reset button under the spacebar)
#   4. While holding, plug the USB cable back in, then release
#
# Usage:
#     /path/to/flash_k10he.sh [FIRMWARE.bin]
#
# If no path is given, it defaults to ./keychron_k10_he_iso_keychron.bin
# (i.e. run it from the QMK root after a build).
#
set -uo pipefail

FW="${1:-./keychron_k10_he_iso_keychron.bin}"
DFU_ID="0483:df11"   # STM32 system DFU bootloader
TIMEOUT=180          # seconds to wait for the bootloader

if [ ! -f "$FW" ]; then
    echo "ERROR: firmware file not found: $FW" >&2
    echo "Build it first (build_k10he.sh) or pass the .bin path as an argument." >&2
    exit 1
fi

echo "==> Waiting up to ${TIMEOUT}s for the keyboard in bootloader mode (STM32 DFU ${DFU_ID})..."
echo "    Put the keyboard in bootloader mode now:"
echo "    unplug USB -> switch to 'Cable' -> hold Esc -> plug USB back in."
echo

found=0
for ((i=0; i<TIMEOUT; i++)); do
    if dfu-util -l 2>/dev/null | grep -iq "$DFU_ID"; then
        found=1
        break
    fi
    sleep 1
done

if [ "$found" -ne 1 ]; then
    echo "!! Timeout: no STM32 DFU device detected."
    echo "   Either the keyboard was not put in bootloader mode, or the Windows"
    echo "   DFU driver (WinUSB) is missing. Current dfu-util view:"
    dfu-util -l || true
    exit 1
fi

echo "==> DFU device detected. Flashing:"
echo "    $FW"
dfu-util -a 0 -d "$DFU_ID" -s 0x08000000:leave -D "$FW"
rc=$?

if [ "$rc" -eq 0 ]; then
    echo
    echo "==> Flash complete. The keyboard should reboot into normal mode now."
else
    echo
    echo "!! dfu-util returned an error (code $rc). The bootloader is still safe;"
    echo "   you can retry. If it cannot open the device, the WinUSB driver is"
    echo "   likely missing (use Zadig or QMK Toolbox)."
fi
exit $rc
