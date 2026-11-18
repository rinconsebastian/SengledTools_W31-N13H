# SengledTools W31-N13H — Tasmota for Sengled W31-N13H bulbs, 100% local

[Español](README.es.md) · [Troubleshooting](docs/TROUBLESHOOTING.md) · [Credits](CREDITS.md) · [MIT License](LICENSE)

Sengled's cloud is gone, so its Wi-Fi bulbs stopped working with the app and Alexa.
This guide brings a **Sengled W31-N13H** (color + white, A19) back to life with the
open firmware [Tasmota](https://tasmota.github.io/), **without opening the bulb,
without soldering and without any cloud**.

It is a companion to the excellent [HamzaETTH/SengledTools](https://github.com/HamzaETTH/SengledTools),
which does the hard part (pairing and the over-the-air upload). This repository adds
what the W31-N13H needs and was missing:

- ✅ **A verified Tasmota template.** Every color channel was tested on real bulbs.
- ✅ **Real warm *and* cold white in Alexa.** The bulb has only one white LED, a warm one. Cold white is mixed from the RGB LEDs, and the mix was calibrated by eye.
- ✅ **One small tool, `w31n13h.py`.** It covers setup, configuration, calibration and backups. It uses only the Python standard library.
- ✅ **A troubleshooting guide** built from every problem found along the way.

No account, no app and no AI are needed: just a PC with Wi-Fi, Python and a web browser.

> [!CAUTION]
> Flashing replaces the original firmware and **cannot be undone over Wi-Fi**.
> If something goes wrong, the bulb can only be recovered by opening it and using a
> serial adapter. Make the full backup in step 5. You do this at your own risk.

---

## Contents

1. [What you need](#what-you-need)
2. [How it works](#how-it-works)
3. [Step by step](#step-by-step)
4. [Color parameters (the important part)](#color-parameters)
5. [Configuring without the tool](#configuring-without-the-tool)
6. [Backups and going back](#backups-and-going-back)
7. [Tool reference](#tool-reference)
8. [What was tested](#what-was-tested)
9. [Credits and license](#credits-and-license)

---

## What you need

| | |
|---|---|
| **Bulb** | Sengled **W31-N13H**. The model is printed on the bulb. During pairing the tool must report `typeCode: W31-N13H` and `identifyNO: ESP8266`. |
| **PC** | Windows, Linux or macOS, with Wi-Fi. |
| **Python** | 3.10 or newer ([python.org](https://www.python.org/downloads/)). |
| **Wi-Fi network** | It must have **2.4 GHz**, because the bulb cannot see 5 GHz-only networks. Mesh networks work. |
| **Time** | About 20–30 minutes for the first bulb, 10 for each additional one. |

> [!WARNING]
> Only bulbs with an **ESP8266** chip (Sengled module WF863) can be flashed this way.
> If pairing reports anything other than `ESP8266`, stop. You can still control it
> locally with SengledTools, but not flash it.

## How it works

```
 Your PC                          The bulb
 ───────                          ────────
 1. Pairing      ── Wi-Fi + "cloud" address ──▶  stock Sengled firmware
    (SengledTools pretends to be Sengled's cloud and MQTT broker)
 2. OTA upload   ── shim.bin over HTTP ───────▶  Sengled-Rescue (tiny flasher)
 3. Browser      ── backup + tasmota.bin ─────▶  Tasmota
 4. w31n13h.py   ── template + colors ────────▶  Tasmota, ready for Alexa
```

1. **Pairing.** SengledTools gives the bulb your Wi-Fi password and tells it that your PC is "the cloud".
2. **OTA upload.** Through Sengled's own update mechanism, the bulb downloads a small program called **Sengled-Rescue**.
3. **Browser.** Sengled-Rescue creates its own Wi-Fi network with a web page. There you back up the chip and upload Tasmota.
4. **`w31n13h.py`.** Tasmota joins your Wi-Fi, and `w31n13h.py` applies the pins, the Hue emulation and the color calibration.

## Step by step

Open a terminal in this folder. On Windows, if `python` doesn't work, use `py`.

### 1. Prepare the PC (once)

```bash
python w31n13h.py setup
```

This downloads SengledTools (at the exact version tested) and the Tasmota firmware into
`work/`, checks their SHA-256 checksums, and creates an isolated Python environment.
Nothing is installed system-wide.

### 2. Pair the bulb

1. **Factory-reset the bulb.** Switch it off and on **5 or more times quickly** until it starts blinking. A Wi-Fi network called `Sengled_Wi-Fi Bulb_XXXXXX` appears. ([reset animation](https://github.com/HamzaETTH/SengledTools/blob/master/docs/RESET_PROCEDURES.md))
2. **Start pairing:**
   ```bash
   python w31n13h.py sengled --setup-wifi
   ```
3. **Follow the prompts.** When asked, connect the PC to the bulb's network. Pick your **2.4 GHz** network from the list and type its password. The PC goes back to your home network and the bulb contacts it.
4. **Check the result:**
   - The tool must show `typeCode: W31-N13H`, `identifyNO: ESP8266` and *UDP control test passed*.
   - **Write down the bulb's MAC address.**
5. **Close the tool:** press Enter to quit.

> `--setup-wifi` does **not** offer flashing. That's expected; it is the next step.

### 3. Upload the Sengled-Rescue shim

You need **two terminals**.

**Terminal A** – start the local servers and leave them running:

```bash
python w31n13h.py sengled --run-servers
```

Wait until it shows `Served GET on /jbalancer/new/bimqtt`, which means the bulb has reconnected. This can take up to a minute.

**Terminal B** – optional test: the bulb should dim.

```bash
python w31n13h.py sengled --mac AA:BB:CC:DD:EE:FF --brightness 30
```

Then send the shim. Use your MAC; the path is exactly as written:

```bash
python w31n13h.py sengled --mac AA:BB:CC:DD:EE:FF --upgrade firmware/shim.bin
```

Confirm the two warnings. In **terminal A** you will see
`Served firmware: shim.bin (495728 bytes)`. From that moment there is no way back to
the Sengled firmware. Stop terminal A with Ctrl+C.

### 4. Wait for Sengled-Rescue

After 1–3 minutes a Wi-Fi network called **`Sengled-Rescue`** appears. Connect the PC to
it and open **http://192.168.4.1**. The page is very slow; refresh until it loads.

### 5. Back up, then flash Tasmota

1. **Back up the whole chip.** Select **full** and click **Backup selected**. Save the 2 MB file somewhere safe and give it a name that identifies the bulb. **It is your only way back.**
2. **Upload Tasmota.** Select **boot**, choose `work/tasmota.bin` (*not* a `.gz` file) and click **Flash selected**.
3. **If it says "write blocked (overlaps running slot)":** click **Relocate to ota_1**, reconnect to `Sengled-Rescue` and repeat step 2.

The bulb reboots into Tasmota and starts **blinking blue**. That means Tasmota is running
and waiting for you to set up Wi-Fi.

### 6. Connect Tasmota to your Wi-Fi

1. Connect to the `tasmota_XXXXXX-####` network and open **http://192.168.4.1**.
2. Enter your 2.4 GHz Wi-Fi and save. When the bulb joins your network, the light changes to **steady blue**.
3. Find the bulb's new IP in your router's client list (the hostname starts with `tasmota-`).

> [!IMPORTANT]
> **Steady blue, but no valid IP?** In our test the Wi-Fi details were correct, yet the
> router showed the bulb connected without a valid IP, and it did not answer. Switch the
> bulb **off and on once**. After that reboot it got its IP and everything continued
> normally. Only one power cycle: several quick ones trigger Tasmota's recovery modes
> (see [Troubleshooting](docs/TROUBLESHOOTING.md)).

Tip: reserve that IP for the bulb's MAC in your router (DHCP reservation).

### 7. Enable Tasmota's HTTP API

Tasmota 16 ships with its HTTP API **disabled**. Open `http://<bulb-ip>` →
**Configuration → Configure Other** → tick **HTTP API** → **Save**.

### 8. Apply the W31-N13H configuration

```bash
python w31n13h.py configure --ip 192.168.1.50 --name "Sengled kitchen"
```

The tool takes about one minute, and the bulb reboots twice along the way. It:

- applies the template;
- sets the name;
- turns on Hue emulation;
- sets the warm/cold white mix, with a boot rule so it is not lost;
- checks every setting;
- saves a configuration backup in `backups/`;
- leaves the bulb in **cold white** so you can look at it.

### 9. Fine-tune the cold white (only if needed)

LEDs vary a little between bulbs. If the cold white looks slightly pink, green, blue or
yellow:

```bash
python w31n13h.py calibrate --ip 192.168.1.50
```

Answer with one key (`p` pink, `g` green, `b` blue, `y` yellow, `+` brighter…) until it
looks neutral, then `s` to save.

### 10. Add it to Alexa

In the Alexa app go to **Add device → Light → Philips Hue**, or simply say
*"Alexa, discover devices"*. The bulb appears with the name you gave it.

## Color parameters

This is the knowledge this repository adds. The values are also in
[`config/w31-n13h.json`](config/w31-n13h.json).

### Template (pins)

```json
{"NAME":"Sengled W31-N13H","GPIO":[0,0,0,0,419,0,0,0,416,418,0,417,0,0],"FLAG":0,"BASE":18}
```

| GPIO | Tasmota | LED |
|---|---|---|
| GPIO12 | PWM1 | red |
| GPIO15 | PWM2 | green |
| GPIO13 | PWM3 | blue |
| GPIO4 | PWM4 | **warm** white (the only white LED) |

> [!NOTE]
> A mapping that circulates online (GPIO12 → PWM1, GPIO13 → PWM3, GPIO14 → PWM4)
> is **wrong** for this bulb: it has no green channel. The table above was verified
> one channel at a time.

### Why the white needs extra work

The W31-N13H has no cold-white LED. By default Tasmota sends every white to the warm
LED, so in Alexa **"cold white" and "warm white" look identical**. The original Sengled
firmware mixed cold white from the RGB LEDs; Tasmota can do the same:

| Command | What it does |
|---|---|
| `SetOption106 1` | Enables a *virtual color temperature* for RGBW bulbs. |
| `VirtualCT {"153":"F8E2B480","500":"000000FF"}` | Coldest (153 mireds ≈ 6500 K) = R F8, G E2, B B4 + white LED 50%. Warmest (500 mireds ≈ 2000 K) = white LED only. Tones in between are blended. |
| `Rule3 ON System#Boot DO VirtualCT {...} ENDON` + `Rule3 1` | **Required.** Tasmota does not save `VirtualCT` in flash, so without this rule the cold white goes back to bluish after every power cut. |
| `SetOption30 1` + `Emulation 2` | Hue emulation, so Alexa controls the bulb directly and locally. |

**Tested cold-white values** (`RRGGBBWW`):

| Value | Result |
|---|---|
| `FFFFFF00` | Tasmota default: far too blue. |
| `F8D89640` | Neutral but noticeably dimmer than the warm white. |
| **`F8E2B480`** | **Default.** Neutral and brighter (white LED at 50%). |
| `F8EAB480` | The same with a little more green, for a bulb that looked slightly pink. |

Even so, the cold white will always be a bit dimmer than the warm white. The warm white
uses a dedicated, efficient LED; the cold white comes mostly from the less efficient RGB
LEDs. Mid tones ("soft white", "white") are in between.

## Configuring without the tool

Paste these lines into the bulb's web **Console** (Tasmota → Tools → Console), one at a
time. The bulb reboots after the first two:

```
Backlog Template {"NAME":"Sengled W31-N13H","GPIO":[0,0,0,0,419,0,0,0,416,418,0,417,0,0],"FLAG":0,"BASE":18}; Module 0
Backlog FriendlyName1 Sengled kitchen; DeviceName Sengled kitchen; SetOption30 1; SetOption106 1; Emulation 2
VirtualCT {"153":"F8E2B480","500":"000000FF"}
Rule3 ON System#Boot DO VirtualCT {"153":"F8E2B480","500":"000000FF"} ENDON
Rule3 1
```

## Backups and going back

| You have | How to restore |
|---|---|
| Tasmota configuration (`.dmp`, from `configure`, `calibrate` or `backup`) | Bulb web UI → **Configuration → Restore Configuration**. |
| Full chip backup (2 MB `.bin`, from Sengled-Rescue) | Only with a serial adapter and `esptool.py` after opening the bulb. See the [Sengled-Rescue notes](https://github.com/HamzaETTH/SengledTools/tree/master/firmware/sengled_ota). |

Keep your backups out of this repository: `backups/`, `*.dmp` and `*.bin` are git-ignored on purpose.

## Tool reference

| Command | What it does |
|---|---|
| `python w31n13h.py setup [--force] [--tasmota latest] [--upstream latest]` | Downloads SengledTools and Tasmota (tested versions by default), verifies their checksums and creates the venv. |
| `python w31n13h.py sengled <options>` | Runs SengledTools. Its certificates and settings stay inside `work/home`, not in your user profile. |
| `python w31n13h.py check --ip IP` | Says whether the bulb answers and why not (HTTP API off, wrong IP…), and shows the template, colors, boot rule and Wi-Fi signal. |
| `python w31n13h.py configure --ip IP --name NAME [--cold RRGGBBWW] [--dry-run]` | Applies the full W31-N13H configuration. `--dry-run` only prints the commands. |
| `python w31n13h.py calibrate --ip IP` | Interactive cold-white tuning; saves the value with its boot rule. |
| `python w31n13h.py backup --ip IP [--name NAME]` | Downloads the Tasmota configuration to `backups/`. |

All bulb commands accept `--password` if you set a web password in Tasmota.

## What was tested

| | |
|---|---|
| Bulbs | 2 × Sengled W31-N13H (WF863 / ESP8266EX, 2 MB flash) |
| SengledTools | commit `7d5eadb` (2026-06-04) |
| Tasmota | 16.0.0 (`tasmota.bin`) |
| PC | Windows 11, Python 3.15 |
| Assistant | Alexa, through Tasmota's Hue emulation |

Linux and macOS should work, because everything is plain Python, but they were not tested.
If you try them, please open an issue with your results.

## Credits and license

Testing, pin verification, color calibration and documentation:
**Sebastian Rincon** ([@rinconsebastian](https://github.com/rinconsebastian)).

Built on the work of **HamzaETTH** ([SengledTools](https://github.com/HamzaETTH/SengledTools)),
**Matt Falcon / FalconFour** (Sengled-Rescue shim) and **Theo Arends and the Tasmota
contributors**. Full details in [CREDITS.md](CREDITS.md).

The files in this repository are under the [MIT License](LICENSE): use, change and share
them freely, keeping the copyright notice. Third-party software is downloaded from its
official sources and keeps its own license; SengledTools publishes no license, so it is
**not** redistributed here.

Not affiliated with or endorsed by Sengled.
