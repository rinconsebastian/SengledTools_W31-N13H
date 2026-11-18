# Troubleshooting

[Español](TROUBLESHOOTING.es.md) · [Back to README](../README.md)

Every item here happened during real testing on W31-N13H bulbs. Find the step where you
got stuck. When in doubt about a flashed bulb, start with:

```bash
python w31n13h.py check --ip <bulb-ip>
```

It tells you whether the bulb answers, and if not, the most likely reason.

---

## Setup (`w31n13h.py setup`)

**pip fails building `pyyaml`: "Unable to find a compatible Visual Studio installation"**
Very new Python versions have no ready-made PyYAML package, so pip tries to compile it.
`setup` already avoids this by setting `PYYAML_FORCE_LIBYAML=0`, which builds it in
pure-Python mode. If you install SengledTools by hand, set that variable first.

**"Python 3.10 or newer is required"**
Install a recent Python from [python.org](https://www.python.org/downloads/). On Windows,
try `py w31n13h.py ...` if `python` points to an old version.

**Checksum mismatch**
The download was corrupted or changed. Run `python w31n13h.py setup --force`. If it keeps
failing with the tested versions, do not continue; open an issue.

---

## Pairing (`sengled --setup-wifi`)

**The `Sengled_Wi-Fi Bulb_XXXXXX` network doesn't appear**
Reset again: switch the bulb off and on 5 or more times quickly until it blinks. See the
[reset animation](https://github.com/HamzaETTH/SengledTools/blob/master/docs/RESET_PROCEDURES.md).

**"Waiting for bulb response…" forever**
The PC must be connected to the bulb's own Wi-Fi at that moment. Disconnect and reconnect
to it; the tool keeps retrying.

**My network is not in the list, or the bulb never joins it**
The bulb only uses **2.4 GHz**. If your router is 5 GHz only, enable the 2.4 GHz band, or
create a separate 2.4 GHz network. Mesh networks with the same name on both bands work.

**Verification times out ("make sure no firewall is blocking")**
The bulb joined your Wi-Fi but cannot reach your PC.
- The PC must be back on the **same** home network.
- When Windows asks, allow Python on **private** networks.
- Turn off "AP isolation" or "client isolation" in the router.
- Test: from a phone on the same Wi-Fi, open `http://<pc-ip>:57542/jbalancer/new/bimqtt`. If it doesn't show text, fix the network first.

**Pairing finished but it never offered to flash**
That's how `--setup-wifi` works. Continue with step 3 of the README (`--run-servers` +
`--upgrade`).

---

## Uploading the shim (`--run-servers` + `--upgrade`)

**"HTTP server failed on port 57542. Port is already in use"**
Another copy of SengledTools is still running. Usually it is the pairing tool waiting on
*"Press Enter to quit"*. Close it, then start `--run-servers` again.

**`--upgrade` says "Port 8883 is not listening"**
Start `python w31n13h.py sengled --run-servers` in another terminal first, and keep it
open.

**The bulb never shows up in `--run-servers`**
- Wait up to a minute.
- Switch the bulb off and on **once**.
- Make sure the PC still has the **same IP** it had during pairing, because the bulb was told that address. Reserve the PC's IP in the router, or pair again.

**The `--brightness 30` test does nothing**
MQTT isn't working, so don't send `--upgrade`. Re-check the previous point.

**The bulb reports a model other than W31-N13H, or `identifyNO` is not ESP8266**
Stop. Only ESP8266 (WF863) bulbs can be flashed this way. Others, such as WF864/MX1290 or
EMW3091, would be bricked. They can still be controlled locally with SengledTools.

---

## Sengled-Rescue (http://192.168.4.1)

**The `Sengled-Rescue` network doesn't appear**
Check that terminal A showed `Served firmware: shim.bin (495728 bytes)`, then wait 3–5
minutes. Don't keep switching the bulb off and on.

**The page is extremely slow or half-loaded**
That's normal; the bulb is a tiny device. Refresh until it loads completely.

**"write blocked (overlaps running slot)" and the Flash button is grey**
Click **Relocate to ota_1**. Wait for the bulb to reboot, reconnect to `Sengled-Rescue`
and flash again.

**Which file do I flash?**
`work/tasmota.bin`, selected as **boot**. Never flash the `.bin.gz` file.

---

## After flashing Tasmota

**What the blue light means**
Without a template, Tasmota doesn't control the colors yet, so the light only shows its
state:

| Light | Meaning | Next step |
|---|---|---|
| Blinking blue | Tasmota is running and has no Wi-Fi configured. | Connect to `tasmota_XXXXXX-####` and set up your Wi-Fi. |
| Steady blue | It joined your Wi-Fi. | Find its IP in the router. |

**Steady blue and the router shows it connected, but there is no valid IP (no answer, no ping)**
This happened to us even though the Wi-Fi details were correct. Switch the bulb off and on
**once**. After that single reboot it got its IP and everything continued normally. Then
open `http://<ip>` in a browser. Reserving its IP in the router (DHCP reservation) helps
next time. Don't do several quick power cycles: they trigger the recovery modes described
below.

**The web page loads, but commands fail with an empty reply (`curl: (52)`)**
Tasmota's **HTTP API is disabled**, which is the default in Tasmota 16. Go to
**Configuration → Configure Other → HTTP API → Save**. `check` detects this case.

**Pings get lost or the first request times out**
Tasmota's dynamic sleep saves power and makes the bulb answer slowly at times. That's
normal; just retry. The tool retries automatically.

---

## Colors and Alexa

**Alexa's "cold white" and "warm white" look the same**
`SetOption106 1` and `VirtualCT` are missing. Run `configure`. The README explains why.

**The cold white went back to bluish after a power cut**
Tasmota does **not** save `VirtualCT` in flash. The `Rule3` boot rule re-applies it.
`check` shows `Rule3: MISSING` when that rule is absent; run `configure` (or
`calibrate` → `s`).

**The cold white has a tint**
Run `python w31n13h.py calibrate --ip <ip>` and correct it step by step:

| You see | Key | Change |
|---|---|---|
| a bit pink | `p` | more green |
| a bit green | `g` | less green |
| too blue | `b` | less blue |
| too yellow / warm | `y` | more blue |
| too dim | `+` | more white LED, plus a little blue |

Phone cameras auto-correct white balance, so trust your eyes, not the hex value the camera
shows.

**The cold white is dimmer than the warm white**
This is expected. The warm white has its own efficient LED, while the cold white comes
mostly from the RGB LEDs. `+` in `calibrate` raises the white LED share, but too much makes
the "cold" white more neutral.

**Wrong colors, or no green at all**
The template is wrong. Use the verified one from the README. The commonly shared
GPIO12/13/14 mapping has no green channel.

**The bulb suddenly lost its configuration: it shows "Generic" and the colors don't respond**
This is Tasmota's **boot-loop protection** (`SetOption36`). When the bulb restarts because
of an error (exception or watchdog) several times in a row, each time within 10 seconds of
booting, Tasmota resets settings step by step. At the 4th step it **erases the template
pins**. This happened to one of our bulbs; we don't know what caused its restarts.
- **Fix:** run `configure` again. Your name and Wi-Fi are kept.
- **If it keeps happening:** `SetOption36 0` disables this protection. The trade-off is that Tasmota then can't recover by itself from a real crash loop. Please open an issue too, because the cause is still unknown.

**I switched the bulb off and on many times, and now it's back to the `tasmota_` network**
Tasmota resets **all** settings, Wi-Fi included, after **7 quick power cycles**. This is
the [fast power-cycle recovery](https://tasmota.github.io/docs/Device-Recovery/). Set up
Wi-Fi again, enable the HTTP API and run `configure`. If your power is unreliable,
`SetOption65 1` disables this feature (but you also lose this recovery path).

**Alexa doesn't find the bulb**
- Check that `Emulation` is `2` (`check`, or console `Emulation`).
- The Echo and the bulb must be on the same network or VLAN.
- In the Alexa app, add it as **Light → Philips Hue** and give discovery a few minutes.

**I renamed the bulb but Alexa still shows the old name**
Rename it in the Alexa app, or delete it there and run discovery again.

**The Hue description says "Amazon-Echo-HA-Bridge"**
That's how Tasmota's Hue emulation identifies itself. Alexa shows the bulb's
`FriendlyName1`.

---

## Getting back

| Situation | What to do |
|---|---|
| A setting broke the bulb's behavior | Restore a `.dmp` in **Configuration → Restore Configuration**, or run `configure` again. |
| Tasmota doesn't boot at all | Open the bulb, connect a serial adapter and write your full backup with `esptool.py`. See the [Sengled-Rescue notes](https://github.com/HamzaETTH/SengledTools/tree/master/firmware/sengled_ota). |

Still stuck? Open an issue and include the output of `python w31n13h.py check --ip <ip>`.
Remove your Wi-Fi password first if it appears in what you paste.
