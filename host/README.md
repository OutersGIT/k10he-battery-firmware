# Host reference client

A tiny command-line client that reads the battery using the custom raw-HID
command (`0xA4`) added by this firmware. It is meant for testing/verification;
for everyday use see the companion tray app **Keyboard Companion**.

```bash
pip install -r requirements.txt

python k10he_battery.py            # read once (USB cable)
python k10he_battery.py --watch    # poll every few seconds
python k10he_battery.py --listen   # read the wireless push reports (dongle)
python k10he_battery.py --list     # list candidate raw-HID interfaces
```

Notes:
- Over the **USB cable** the pull model works (the client writes the command and
  reads the reply).
- Over the **2.4 GHz dongle** use `--listen`: the dongle does not forward the
  host -> keyboard raw-HID direction, so the firmware *pushes* the battery on its
  own and the client only reads.
- **Bluetooth** does not expose this raw-HID channel; read the battery from the
  OS instead (Windows exposes it via the BLE Battery Service).
