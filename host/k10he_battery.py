#!/usr/bin/env python3
"""Read the battery level of a Keychron K10 HE via QMK raw HID.

Minimal reference client for the custom firmware in this repository. It exercises
the KC_GET_BATTERY (0xA4) raw-HID command:

* over the USB cable it sends the command and reads the reply (pull model);
* over the 2.4 GHz dongle it can passively listen for the battery reports the
  firmware pushes on its own (--listen), since the dongle does not bridge the
  host -> keyboard raw-HID direction.

For a full tray application see the companion project "Keyboard Companion".

Usage:
    python k10he_battery.py            # read once (cable)
    python k10he_battery.py --watch    # keep polling every few seconds
    python k10he_battery.py --listen   # passively read pushed reports (dongle)
    python k10he_battery.py --list     # list candidate raw-HID interfaces
"""

import argparse
import sys
import time

try:
    import hid  # provided by the "hidapi" package
except ImportError:
    sys.exit(
        "Missing dependency 'hidapi'. Install it with:\n"
        "    pip install hidapi"
    )

# --- Keychron K10 HE identifiers -------------------------------------------
VENDOR_ID = 0x3434          # Keychron
PRODUCT_ID = 0x0EA1         # K10 HE (direct USB). The 2.4 GHz dongle may use a
                            # different PID, so by default we match any Keychron
                            # device exposing the raw-HID interface.

# QMK raw-HID interface descriptor
RAW_USAGE_PAGE = 0xFF60
RAW_USAGE = 0x61

REPORT_SIZE = 32            # RAW_EPSIZE in the firmware
READ_TIMEOUT_MS = 1000

# Custom command implemented in keychron_raw_hid.c
KC_GET_BATTERY = 0xA4

CHARGING_STATE = {
    0: "on battery",
    1: "charging",
    2: "fully charged",
}

TRANSPORT = {
    0x00: "none",
    0x01: "USB (cable)",
    0x02: "Bluetooth",
    0x04: "2.4 GHz (dongle)",
}


def find_raw_hid_interfaces(any_keychron=True):
    """Return device-info dicts for every QMK raw-HID interface we can use."""
    candidates = []
    for dev in hid.enumerate():
        if dev["usage_page"] != RAW_USAGE_PAGE or dev["usage"] != RAW_USAGE:
            continue
        if any_keychron:
            if dev["vendor_id"] != VENDOR_ID:
                continue
        else:
            if dev["vendor_id"] != VENDOR_ID or dev["product_id"] != PRODUCT_ID:
                continue
        candidates.append(dev)
    return candidates


def _parse_report(resp):
    """Parse a raw-HID report into a battery dict, or None if it is not ours."""
    if not resp:
        return None
    # Tolerate an optional leading report-ID byte.
    if resp[0] != KC_GET_BATTERY and len(resp) > 1 and resp[1] == KC_GET_BATTERY:
        resp = resp[1:]
    if not resp or resp[0] != KC_GET_BATTERY:
        return None
    voltage = resp[2] | (resp[3] << 8)
    return {
        "percentage": resp[1],
        "voltage_mv": voltage,
        "charging": resp[4],
        "transport": resp[5],
    }


def query_battery(dev_info):
    """Send the battery command to one interface and return parsed data or None."""
    h = hid.device()
    h.open_path(dev_info["path"])
    try:
        # On Windows hidapi expects a leading report-ID byte (0x00) followed by
        # the 32-byte payload.
        payload = [0x00, KC_GET_BATTERY] + [0x00] * (REPORT_SIZE - 1)
        h.write(payload)
        deadline = time.time() + (READ_TIMEOUT_MS / 1000.0)
        while time.time() < deadline:
            data = _parse_report(h.read(REPORT_SIZE, timeout_ms=READ_TIMEOUT_MS))
            if data is not None:
                return data
        return None
    finally:
        h.close()


def format_result(data):
    charging = CHARGING_STATE.get(data["charging"], f"unknown ({data['charging']})")
    transport = TRANSPORT.get(data["transport"], f"unknown (0x{data['transport']:02X})")
    return (
        f"Battery: {data['percentage']}%  "
        f"({data['voltage_mv']} mV)  |  "
        f"State: {charging}  |  "
        f"Link: {transport}"
    )


def read_once(any_keychron=True):
    interfaces = find_raw_hid_interfaces(any_keychron=any_keychron)
    if not interfaces:
        print("No Keychron raw-HID interface found.")
        print("Make sure the keyboard (or dongle) is connected and that the")
        print("custom firmware with the battery command (0xA4) is flashed.")
        return False

    for dev_info in interfaces:
        try:
            data = query_battery(dev_info)
        except OSError as exc:
            print(f"Cannot open {dev_info['path']!r}: {exc}")
            continue
        if data is not None:
            print(format_result(data))
            return True

    print("Battery command sent but no valid reply.")
    print("Likely causes: firmware without the 0xA4 command, or the 2.4 GHz")
    print("dongle does not bridge raw HID. Try over the USB cable first, or use")
    print("--listen for the wireless push model.")
    return False


def listen(any_keychron=True, duration=None):
    """Passively read raw-HID interfaces waiting for pushed 0xA4 battery reports.

    Used with the PUSH-model firmware: the keyboard sends the battery state on
    its own over the wireless link, so the host only needs to read (no write).
    """
    interfaces = find_raw_hid_interfaces(any_keychron=any_keychron)
    if not interfaces:
        print("No Keychron raw-HID interface found.")
        return False

    devices = []
    for info in interfaces:
        try:
            h = hid.device()
            h.open_path(info["path"])
            h.set_nonblocking(True)
            devices.append((info, h))
        except OSError as exc:
            print(f"Cannot open {info['path']!r}: {exc}")

    if not devices:
        return False

    print("Listening for pushed battery reports on raw HID... Ctrl+C to quit.")
    start = time.time()
    got = False
    try:
        while True:
            for _info, h in devices:
                data = _parse_report(h.read(REPORT_SIZE))
                if data is not None:
                    print(format_result(data))
                    got = True
            if duration is not None and (time.time() - start) > duration:
                break
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        for _, h in devices:
            h.close()
    if not got and duration is not None:
        print("No battery report received before the timeout.")
    return got


def list_interfaces():
    interfaces = find_raw_hid_interfaces(any_keychron=True)
    if not interfaces:
        print("No Keychron raw-HID interface (VID 0x3434) found.")
        return
    print("Candidate raw-HID interfaces:")
    for dev in interfaces:
        product = dev.get("product_string") or "?"
        print(
            f"  VID=0x{dev['vendor_id']:04X} PID=0x{dev['product_id']:04X}"
            f"  '{product}'  path={dev['path']!r}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Read the Keychron K10 HE battery over raw HID."
    )
    parser.add_argument("--watch", action="store_true", help="Poll continuously")
    parser.add_argument("--interval", type=float, default=5.0, help="Polling interval in seconds (with --watch)")
    parser.add_argument("--list", action="store_true", help="List the raw-HID interfaces found")
    parser.add_argument("--listen", action="store_true", help="Passive mode: listen for pushed battery reports (dongle)")
    parser.add_argument("--timeout", type=float, default=None, help="Timeout in seconds for --listen")
    parser.add_argument("--strict", action="store_true", help="Match only the K10 HE PID (0x0EA1), ignore the dongle")
    args = parser.parse_args()

    if args.list:
        list_interfaces()
        return

    any_keychron = not args.strict

    if args.listen:
        ok = listen(any_keychron=any_keychron, duration=args.timeout)
        sys.exit(0 if ok else 1)

    if args.watch:
        try:
            while True:
                read_once(any_keychron=any_keychron)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            pass
    else:
        ok = read_once(any_keychron=any_keychron)
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
