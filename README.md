# K10 HE battery firmware (QMK, raw-HID)

QMK firmware modifications that let a host PC read the battery level of a
**Keychron K10 HE** over a custom raw-HID channel — including over the **2.4 GHz
dongle**, where a normal pull request is not bridged.

This is the firmware side of the **[Keyboard Companion](https://github.com/OutersGIT/keyboard-companion)**
tray app. The app reads what this firmware exposes.

> **Derivative of QMK Firmware → licensed GPLv2** (see [`LICENSE`](LICENSE) and
> [`NOTICE`](NOTICE)). Community project, **not affiliated with or endorsed by
> Keychron** or the QMK project.

## Flash the prebuilt firmware (recommended)

If you just want the feature on your keyboard, you don't need to build anything —
download the ready-made firmware and flash it with a GUI tool.

> **Easiest on Windows: flash from Keyboard Companion.** If you use the companion
> app, you can flash this firmware straight from it — tray menu → **Flash firmware…**
> → pick the `.bin`, then follow the on-screen bootloader steps (it shows a live
> progress bar). It uses the same STM32 DFU mechanism as below and still needs the
> WinUSB driver (which QMK Toolbox installs). Get it from the
> [Keyboard Companion releases](https://github.com/OutersGIT/keyboard-companion/releases)
> (v0.3.0+). Prefer a dedicated flasher or not on Windows? Use QMK Toolbox below.

1. **Download the build for your layout** from the
   [**Releases**](https://github.com/OutersGIT/k10he-battery-firmware/releases)
   page:

   | Your K10 HE layout | File to download |
   |---|---|
   | **ANSI** (most common worldwide) | `keychron_k10_he_ansi_keychron.bin` |
   | **ISO** | `keychron_k10_he_iso_keychron.bin` |

   Not sure? ANSI has a horizontal rectangular **Enter** (and a 1-row left Shift);
   ISO has a tall **Enter** spanning two rows (and a shorter left Shift).
2. **Get [QMK Toolbox](https://github.com/qmk/qmk_toolbox/releases)** — the
   friendliest flasher; it also installs the Windows DFU driver for you.
3. In QMK Toolbox, click **Open** and pick the downloaded `.bin`.
4. **Put the keyboard in bootloader mode:** unplug USB → set the side switch to
   **Cable** → hold **Esc** → plug USB back in, then release Esc. QMK Toolbox
   should print a `STM32 DFU device connected` line.
5. Click **Flash**. When it finishes, the keyboard reboots into normal mode.

> **Heads-up**
> - Pick the `.bin` that matches your layout (**ANSI** or **ISO**). Flashing the
>   wrong layout won't brick the board, but some keys will be mislabeled.
> - **ANSI build: not yet tested on real hardware.** Only the **ISO** build has
>   been verified on a physical keyboard. The ANSI `.bin` is built from the exact
>   same shared battery code (the change is layout-agnostic), so it *should* work,
>   but you'd be the first to try it — and flashing is fully reversible (below).
> - Flashing modifies your keyboard's firmware (at your own risk). It is fully
>   **reversible**: you can re-flash the stock Keychron firmware the same way
>   (QMK Toolbox or the [Keychron Launcher](https://launcher.keychron.com/)).
> - If flashing can't open the device, the DFU driver is missing — let QMK
>   Toolbox install it (or use Zadig to bind **WinUSB** to the `STM32 BOOTLOADER`
>   device), then retry.

Prefer the command line, or want to rebuild it yourself? See
[Build & flash](#build--flash) below.

## What it adds

- A new raw-HID command **`KC_GET_BATTERY = 0xA4`** that returns: percentage,
  voltage (mV), charging state and active transport.
- A `FEATURE_BATTERY` capability bit advertised in `KC_GET_SUPPORT_FEATURE`.
- `battery_get_charging_state()` in the Keychron battery driver.
- A wireless **push model** (`kc_battery_push()`): the keyboard proactively
  sends the battery report over the 2.4 GHz link every couple of seconds. This
  is what makes the reading work through the dongle, which does not forward the
  host → keyboard raw-HID direction.
- **Cable-mode voltage polling** (`0002` patch): while on **Cable** with USB
  connected, the firmware still queries the LK module for cell voltage so
  `KC_GET_BATTERY` over USB returns fresh %/mV (not only the last wireless
  snapshot). Read-only; same interval as wireless. Apply `patches/0002-...` after
  `0001`, or use the updated `firmware/` tree.
- **Keyboard model id** (`0003` patch): an optional `model_id` byte added to the
  `KC_GET_BATTERY` report so the host can show the keyboard model **even over the
  2.4 GHz dongle** (the dongle otherwise exposes only its own generic HID name,
  e.g. "Keychron Link"). `1` for the K10 HE, `0` (unspecified) for other boards.

Report layout (`data[0..6]`): `0xA4`, `percentage`, `voltage_lo`, `voltage_hi`,
`charging_state` (0 = on battery, 1 = charging, 2 = full), `transport`
(0x01 USB / 0x02 BT / 0x04 2.4 GHz), `model_id`.

`model_id` is a low byte that identifies the keyboard model when available.
For the patched K10 HE builds in this repository it is `1`; other keyboards
or older firmwares may leave it at `0` (unspecified). Host tools should treat
missing bytes past `data[5]` as `0` for backwards compatibility. This lets the
host show the keyboard model even over the 2.4 GHz dongle, which otherwise only
exposes its own generic HID strings (e.g. "Keychron Link").

> **Porting note:** `KC_BATTERY_MODEL_ID` must be defined in the keyboard's
> `config.h`, **not** in a `.c` file. The report is assembled in the shared
> `keychron_raw_hid.c`, so a `#define` placed in `k10_he.c` is invisible to it
> (separate translation unit) and the model id silently stays `0`. The header
> provides a `0` fallback via `#ifndef`.

## Repository layout

```
patches/                             # apply in order on the Keychron QMK base
  0001-k10he-battery-raw-hid.patch        # battery raw HID + push (apply to QMK)
  0002-battery-voltage-on-usb-cable.patch # fresh %/mV in Cable mode (after 0001)
  0003-keyboard-model-id.patch            # model_id in the report (after 0002)
firmware/                            # the modified files, for reference/inspection
  keyboards/keychron/common/keychron_raw_hid.{c,h}
  keyboards/keychron/common/wireless/battery.{c,h}
  keyboards/keychron/k10_he/k10_he.c
  keyboards/keychron/k10_he/config.h   # FRAGMENT: the KC_BATTERY_MODEL_ID 1 define
                                       # only — merge it into the stock config.h,
                                       # do NOT overwrite the real file
scripts/
  build_k10he.sh                     # fetch submodules + build (run inside QMK)
  flash_k10he.sh                     # wait for DFU + flash over dfu-util
host/
  k10he_battery.py                   # tiny reference client (testing)
```

## Build & flash

You need a QMK build environment — on Windows the easiest is **QMK MSYS**.

1. **Get the Keychron QMK base.** These changes target the Keychron QMK fork,
   2025 Q3 snapshot (the K10 HE lives in the Keychron tree):

   ```bash
   git clone https://github.com/Keychron/qmk_firmware.git
   cd qmk_firmware
   # check out the 2025 Q3 branch/tag matching your board
   ```

2. **Apply the patches**, in order (`0001` → `0002` → `0003`):

   ```bash
   for p in 0001-k10he-battery-raw-hid 0002-battery-voltage-on-usb-cable 0003-keyboard-model-id; do
       git apply /path/to/k10he-battery-firmware/patches/$p.patch
       # or, without a git repo:  patch -p1 < /path/to/.../$p.patch
   done
   ```

   Alternatively, copy the files under `firmware/` over the matching paths in
   your QMK checkout — **except `k10_he/config.h`**, which is a *fragment* (only
   the `KC_BATTERY_MODEL_ID` define): add that one line to the stock `config.h`
   instead of overwriting it, or you'll lose the board's hardware configuration.

3. **Build** (from the QMK root):

   ```bash
   /path/to/k10he-battery-firmware/scripts/build_k10he.sh
   # or directly, picking your layout:
   make keychron/k10_he/ansi:keychron   # ANSI
   make keychron/k10_he/iso:keychron    # ISO
   ```

   The helper script also fetches the required ChibiOS / LUFA / printf
   submodules on first run.

4. **Flash** — put the keyboard in bootloader mode (unplug USB → set the side
   switch to **Cable** → hold **Esc** → plug USB back in), then:

   ```bash
   /path/to/k10he-battery-firmware/scripts/flash_k10he.sh ./keychron_k10_he_ansi_keychron.bin
   # (use ...iso_keychron.bin instead if your board is ISO)
   ```

   or load the `.bin` with **QMK Toolbox**.

> The change is layout-agnostic (it lives in shared raw-HID / battery code), so the
> same patch builds **both** layouts — only the make target differs.

## Verify

With the firmware flashed and the keyboard on **cable**:

```bash
cd host
pip install -r requirements.txt
python k10he_battery.py            # one-shot read over USB
python k10he_battery.py --listen   # passive read of the dongle push reports
```

## Troubleshooting

- **`make` fails with a `jsonschema` error** (e.g. *"cannot unpack non-iterable
  Draft202012Validator"*): this is a QMK/`jsonschema` version mismatch in the
  Python tooling, unrelated to the firmware change. Updating/pinning
  `jsonschema` in the QMK Python environment resolves it; as a last resort the
  schema validation step can be skipped locally.
- **Dongle shows nothing with a one-shot read:** that is expected — use
  `--listen` (push model), since the dongle does not bridge host → keyboard
  raw HID.
- **Restore the stock firmware:** flash the original Keychron firmware (QMK
  Toolbox or the Keychron Launcher) the same way.

## Restoring / safety

Flashing is reversible: the stock Keychron firmware can be re-flashed at any
time. Modifying the firmware is at your own risk.
