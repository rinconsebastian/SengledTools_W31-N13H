#!/usr/bin/env python3
"""
w31n13h.py - Flash Sengled W31-N13H Wi-Fi bulbs with Tasmota, 100% locally.

Companion tool for HamzaETTH/SengledTools. Python standard library only.
SengledTools is downloaded from its official GitHub repository (pinned to the
tested commit); it is NOT bundled here.

Commands:
  setup       Download SengledTools + Tasmota and create an isolated Python venv
  sengled     Run SengledTools (everything after "sengled" is passed through)
  check       Check that a Tasmota bulb answers and its HTTP API is enabled
  configure   Apply the W31-N13H template, Hue emulation and color parameters
  calibrate   Interactively fine-tune the cold white of one bulb
  backup      Download a bulb's Tasmota configuration (.dmp)

Run "python w31n13h.py <command> --help" for details.

Copyright (c) 2026 Sebastian Rincon (rinconsebastian). MIT License.
"""

import argparse
import hashlib
import http.client
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK = ROOT / "work"                      # everything downloaded/generated (git-ignored)
UPSTREAM_DIR = WORK / "SengledTools"
VENV_DIR = WORK / "venv"
HOME_DIR = WORK / "home"                  # SengledTools stores certs in ~/.sengled -> here
TASMOTA_BIN = WORK / "tasmota.bin"
BACKUP_DIR = ROOT / "backups"
CONFIG_FILE = ROOT / "config" / "w31-n13h.json"

# Tested versions -------------------------------------------------------------
UPSTREAM_REPO = "HamzaETTH/SengledTools"
UPSTREAM_COMMIT = "7d5eadb3b37292a84726d23e658d483f89e23f1b"   # 2026-06-04
SHIM_SHA256 = "8b8b02db78783defe9fa85a7bb437df3e16275f5ac3f9edcda1febcb5ea04bb6"
TASMOTA_TAG = "v16.0.0"
TASMOTA_SHA256 = "f928bbcd8cec62156a6165828844ff40c406b358c4dba9a4d445bd60056c9b14"

USER_AGENT = "SengledTools_W31-N13H"

# Tasmota does NOT persist VirtualCT in flash (it is lost on every reboot or
# power cut), so we re-apply it at boot with a rule. Rule3 is used to stay out
# of the way of Rule1, which people commonly use for their own automations.
CT_RULE = "Rule3"


# -----------------------------------------------------------------------------
# Small helpers
# -----------------------------------------------------------------------------
def say(msg=""):
    print(msg, flush=True)


def die(msg, code=1):
    print(f"\nERROR: {msg}", file=sys.stderr, flush=True)
    sys.exit(code)


def http_get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def venv_python():
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "bulb"


def load_config():
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)


def local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "unknown"


# -----------------------------------------------------------------------------
# setup
# -----------------------------------------------------------------------------
def download_upstream(ref):
    if ref == "tested":
        sha = UPSTREAM_COMMIT
    else:
        info = json.loads(http_get(f"https://api.github.com/repos/{UPSTREAM_REPO}"))
        branch = info.get("default_branch", "main")
        commit = json.loads(http_get(
            f"https://api.github.com/repos/{UPSTREAM_REPO}/commits/{branch}"))
        sha = commit["sha"]
    say(f"  SengledTools commit: {sha}" + ("  (tested)" if sha == UPSTREAM_COMMIT else "  (NOT the tested commit)"))

    data = http_get(f"https://codeload.github.com/{UPSTREAM_REPO}/zip/{sha}", timeout=180)
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "upstream.zip"
        zpath.write_bytes(data)
        with zipfile.ZipFile(zpath) as zf:
            zf.extractall(tmp)   # zipfile strips absolute paths and ".." components
        extracted = [p for p in Path(tmp).iterdir() if p.is_dir()]
        if len(extracted) != 1:
            die("Unexpected archive layout from GitHub.")
        if UPSTREAM_DIR.exists():
            shutil.rmtree(UPSTREAM_DIR)
        shutil.move(str(extracted[0]), str(UPSTREAM_DIR))
    (UPSTREAM_DIR / ".commit").write_text(sha + "\n", encoding="utf-8")

    shim = UPSTREAM_DIR / "firmware" / "shim.bin"
    if not shim.is_file():
        die("firmware/shim.bin not found in SengledTools download.")
    got = sha256_file(shim)
    if sha == UPSTREAM_COMMIT and got != SHIM_SHA256:
        die(f"shim.bin checksum mismatch!\n  expected {SHIM_SHA256}\n  got      {got}")
    say(f"  shim.bin sha256: {got}" + ("  OK" if got == SHIM_SHA256 else "  (unverified)"))


def download_tasmota(tag):
    if tag == "latest":
        rel = json.loads(http_get("https://api.github.com/repos/arendst/Tasmota/releases/latest"))
    else:
        rel = json.loads(http_get(f"https://api.github.com/repos/arendst/Tasmota/releases/tags/{tag}"))
    asset = next((a for a in rel.get("assets", []) if a["name"] == "tasmota.bin"), None)
    if not asset:
        die(f"tasmota.bin not found in Tasmota release {rel.get('tag_name', tag)}.")
    expected = None
    if rel.get("tag_name") == TASMOTA_TAG:
        expected = TASMOTA_SHA256
    elif (asset.get("digest") or "").startswith("sha256:"):
        expected = asset["digest"].split(":", 1)[1]

    say(f"  Tasmota {rel.get('tag_name')}: downloading tasmota.bin ({asset['size']} bytes)")
    data = http_get(asset["browser_download_url"], timeout=180)
    got = hashlib.sha256(data).hexdigest()
    if expected and got != expected:
        die(f"tasmota.bin checksum mismatch!\n  expected {expected}\n  got      {got}")
    TASMOTA_BIN.write_bytes(data)
    say(f"  tasmota.bin sha256: {got}" + ("  OK" if expected else "  (no published digest to compare)"))


def create_venv():
    if not venv_python().exists():
        say("  Creating virtual environment...")
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])
    env = dict(os.environ)
    # PyYAML (pulled in by amqtt) has no wheels for very new Python versions;
    # this makes it build in pure-Python mode instead of needing a C compiler.
    env["PYYAML_FORCE_LIBYAML"] = "0"
    say("  Installing SengledTools requirements (paho-mqtt, psutil, amqtt, cryptography)...")
    subprocess.check_call([str(venv_python()), "-m", "pip", "install", "--disable-pip-version-check",
                           "-q", "-r", str(UPSTREAM_DIR / "requirements.txt")], env=env)
    subprocess.check_call([str(venv_python()), "-c",
                           "import paho.mqtt, psutil, amqtt, cryptography, yaml"], env=env)
    say("  Dependencies OK")


def cmd_setup(args):
    if sys.version_info < (3, 10):
        die("Python 3.10 or newer is required.")
    WORK.mkdir(exist_ok=True)
    HOME_DIR.mkdir(exist_ok=True)
    say("[1/3] SengledTools")
    if UPSTREAM_DIR.exists() and not args.force and args.upstream == "tested" \
            and (UPSTREAM_DIR / ".commit").read_text().strip() == UPSTREAM_COMMIT:
        say("  Already downloaded (use --force to download again)")
    else:
        download_upstream(args.upstream)
    say("[2/3] Tasmota firmware")
    if TASMOTA_BIN.exists() and not args.force and args.tasmota == TASMOTA_TAG \
            and sha256_file(TASMOTA_BIN) == TASMOTA_SHA256:
        say(f"  Already downloaded: {TASMOTA_BIN}")
    else:
        download_tasmota(args.tasmota)
    say("[3/3] Python environment")
    create_venv()
    say("\nSetup complete.")
    say(f"  Tasmota image to upload later: {TASMOTA_BIN}")
    say(f"  This PC's LAN IP: {local_ip()}")
    say("Next: reset the bulb and run:  python w31n13h.py sengled --setup-wifi")


# -----------------------------------------------------------------------------
# sengled (pass-through launcher)
# -----------------------------------------------------------------------------
def run_sengled(passthrough):
    if not venv_python().exists() or not (UPSTREAM_DIR / "sengled_tool.py").exists():
        die('Run "python w31n13h.py setup" first.')
    env = dict(os.environ)
    env["USERPROFILE"] = str(HOME_DIR)      # Windows home -> keeps certs inside work/
    env["HOME"] = str(HOME_DIR)             # Linux/macOS home
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    HOME_DIR.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen([str(venv_python()), "sengled_tool.py", *passthrough],
                            cwd=str(UPSTREAM_DIR), env=env)
    while True:
        try:
            return proc.wait()
        except KeyboardInterrupt:
            continue   # Ctrl+C is delivered to the child too; wait for it to exit


# -----------------------------------------------------------------------------
# Tasmota HTTP API
# -----------------------------------------------------------------------------
class Bulb:
    def __init__(self, ip, password=None):
        self.ip = ip
        self.password = password

    def _url(self, path, params=None):
        params = dict(params or {})
        if self.password:
            params.update({"user": "admin", "password": self.password})
        q = "&".join(f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in params.items())
        return f"http://{self.ip}{path}" + (f"?{q}" if q else "")

    def cmd(self, command, timeout=15):
        body = http_get(self._url("/cm", {"cmnd": command}), timeout=timeout).decode("utf-8", "replace")
        try:
            return json.loads(body) if body.strip() else {}
        except json.JSONDecodeError:
            return {"_raw": body}

    def download_config(self, timeout=30):
        return http_get(self._url("/dl"), timeout=timeout)

    def server_header(self, timeout=20):
        req = urllib.request.Request(self._url("/"), headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.headers.get("Server", "")

    def wait_back(self, first_delay=6, limit=150):
        time.sleep(first_delay)
        deadline = time.time() + limit
        while time.time() < deadline:
            try:
                if self.cmd("Status 2", timeout=5):
                    return True
            except Exception:
                pass
            time.sleep(3)
        return False


def diagnose(bulb, attempts=3):
    """Return (ok, message). Explains the common failure modes.
    Timeouts are retried: Tasmota's dynamic sleep makes the first request flaky."""
    for attempt in range(1, attempts + 1):
        ok, msg, retry = _diagnose_once(bulb)
        if not retry or attempt == attempts:
            return ok, msg
        say(f"  (no answer yet, retrying {attempt}/{attempts - 1}...)")
        time.sleep(2)


def _diagnose_once(bulb):
    ok, msg = _probe(bulb)
    retry = msg.startswith("No answer") or msg.startswith("Empty reply")
    return ok, msg, retry


def _probe(bulb):
    try:
        st = bulb.cmd("Status 2", timeout=20)
        fw = st.get("StatusFWR", {})
        if fw:
            return True, f"Tasmota {fw.get('Version')} on {fw.get('Hardware')}"
        if "_raw" in st or not st:
            return False, "The device answered but not like Tasmota. Is this the right IP?"
        return True, json.dumps(st)
    except http.client.RemoteDisconnected:
        pass
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return False, "Tasmota has a web password. Pass it with --password."
        return False, f"HTTP error {e.code}"
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError, OSError) as e:
        return False, (f"No answer from {bulb.ip} ({e}).\n"
                       "  - Check the IP in your router's client list.\n"
                       "  - Make sure this PC is on your home network (not the bulb's AP).\n"
                       "  - Occasional ping loss is normal (Tasmota dynamic sleep); retry.")
    # Empty reply on /cm: usually the HTTP API is disabled
    try:
        server = bulb.server_header()
    except Exception:
        server = ""
    if "Tasmota" in server:
        return False, (f"{server} is running, but its HTTP API is DISABLED.\n"
                       f"  Open http://{bulb.ip} -> Configuration -> Configure Other ->\n"
                       "  tick 'HTTP API' -> Save. Then run this command again.")
    return False, "Empty reply from the device. Retry in a few seconds."


def require_tasmota(bulb):
    ok, msg = diagnose(bulb)
    say(("OK: " if ok else "") + msg)
    if not ok:
        sys.exit(2)


def cmd_check(args):
    bulb = Bulb(args.ip, args.password)
    require_tasmota(bulb)
    try:
        tpl = bulb.cmd("Template")
        wifi = bulb.cmd("Status 11").get("StatusSTS", {}).get("Wifi", {})
        names = bulb.cmd("FriendlyName1")
        vct = bulb.cmd("VirtualCT")
        rule = bulb.cmd(CT_RULE).get(CT_RULE, {})
    except Exception as e:
        die(f"Bulb stopped answering: {e}")
    expected = load_config()["template"]
    say(f"  Name:      {names.get('FriendlyName1')}")
    say(f"  Template:  {tpl.get('NAME')}" + ("  (W31-N13H template OK)" if tpl.get("GPIO") == expected["GPIO"]
                                             else "  (not the W31-N13H template - run 'configure')"))
    say(f"  VirtualCT: {vct.get('VirtualCT', 'not available (template missing or SetOption106 off)')}")
    rules = rule.get("Rules", "")
    if rule.get("State") == "ON" and "VirtualCT" in rules:
        say(f"  {CT_RULE}:     ON - cold white is re-applied at every boot")
    else:
        say(f"  {CT_RULE}:     MISSING - cold white will reset on reboot; run 'configure'")
    if wifi:
        say(f"  Wi-Fi:     {wifi.get('SSId')}  signal {wifi.get('Signal')} dBm  ({wifi.get('RSSI')}%)")


# -----------------------------------------------------------------------------
# backup
# -----------------------------------------------------------------------------
def save_backup(bulb, label):
    BACKUP_DIR.mkdir(exist_ok=True)
    data = bulb.download_config()
    if len(data) < 1024:
        die("Configuration download looks wrong (too small).")
    path = BACKUP_DIR / f"{slugify(label)}_{time.strftime('%Y%m%d-%H%M%S')}.dmp"
    path.write_bytes(data)
    return path


def cmd_backup(args):
    bulb = Bulb(args.ip, args.password)
    require_tasmota(bulb)
    label = args.name or bulb.cmd("FriendlyName1").get("FriendlyName1") or args.ip
    path = save_backup(bulb, label)
    say(f"Saved: {path}")
    say("Restore it from the bulb's web UI: Configuration -> Restore Configuration.")


# -----------------------------------------------------------------------------
# configure
# -----------------------------------------------------------------------------
def vct_json(vct):
    return json.dumps(vct, separators=(",", ":"))


def apply_virtual_ct(bulb, vct):
    """Set VirtualCT now and make it survive reboots via a boot rule."""
    payload = vct_json(vct)
    bulb.cmd(f"VirtualCT {payload}")
    bulb.cmd(f"{CT_RULE} ON System#Boot DO VirtualCT {payload} ENDON")
    bulb.cmd(f"{CT_RULE} 1")


def rule_matches(bulb, vct):
    r = bulb.cmd(CT_RULE).get(CT_RULE, {})
    return r.get("State") == "ON" and vct_json(vct) in r.get("Rules", "")


def validate_hex(value, length):
    v = value.strip().upper()
    if not re.fullmatch(rf"[0-9A-F]{{{length}}}", v):
        die(f"'{value}' must be {length} hex digits (RRGGBBWW).")
    return v


def cmd_configure(args):
    cfg = load_config()
    if re.search(r"[;\"{}]", args.name):
        die("The name cannot contain ; \" { or }.")
    vct = dict(cfg["virtual_ct"])
    if args.cold:
        vct["153"] = validate_hex(args.cold, 8)
    template = json.dumps(cfg["template"], separators=(",", ":"))
    steps = [
        (f"Backlog Template {template}; Module 0", True),
        (f"Backlog FriendlyName1 {args.name}; DeviceName {args.name}; " + "; ".join(cfg["options"]), True),
    ]
    ct_cmds = [f"VirtualCT {vct_json(vct)}",
               f"{CT_RULE} ON System#Boot DO VirtualCT {vct_json(vct)} ENDON",
               f"{CT_RULE} 1"]
    if args.dry_run:
        say("Commands that would be sent (Tasmota console syntax):")
        for c, _ in steps:
            say(f"  {c}")
        for c in ct_cmds:
            say(f"  {c}")
        return

    bulb = Bulb(args.ip, args.password)
    require_tasmota(bulb)
    total = len(steps) + 1
    for i, (command, restarts) in enumerate(steps, 1):
        say(f"[{i}/{total}] {command[:70]}{'...' if len(command) > 70 else ''}")
        bulb.cmd(command)
        if restarts:
            say("      waiting for the bulb to restart...")
            if not bulb.wait_back():
                die("The bulb did not come back. Check it in your router and run 'check'.")
    say(f"[{total}/{total}] VirtualCT {vct_json(vct)} (+ {CT_RULE} so it survives reboots)")
    apply_virtual_ct(bulb, vct)

    say("Verifying...")
    problems = []
    if bulb.cmd("Template").get("GPIO") != cfg["template"]["GPIO"]:
        problems.append("Template")
    if bulb.cmd("FriendlyName1").get("FriendlyName1") != args.name:
        problems.append("FriendlyName1")
    if bulb.cmd("Emulation").get("Emulation") != 2:
        problems.append("Emulation")
    for opt in ("SetOption30", "SetOption106"):
        if bulb.cmd(opt).get(opt) != "ON":
            problems.append(opt)
    got_vct = bulb.cmd("VirtualCT").get("VirtualCT", {})
    for k, v in vct.items():
        if not str(got_vct.get(k, "")).upper().startswith(v.upper()):
            problems.append(f"VirtualCT {k}")
    if not rule_matches(bulb, vct):
        problems.append(f"{CT_RULE} (boot rule for VirtualCT)")
    if problems:
        die("These settings did not stick: " + ", ".join(problems) + ". Run configure again.")
    say("  All settings OK")

    path = save_backup(bulb, args.name)
    say(f"  Config backup: {path}")
    bulb.cmd("Backlog Power ON; Dimmer 100; CT 153")
    say("\nDone. The bulb is now showing COLD white.")
    say("If it looks slightly pink/green/blue, run:  "
        f"python w31n13h.py calibrate --ip {args.ip}")


# -----------------------------------------------------------------------------
# calibrate
# -----------------------------------------------------------------------------
CAL_MENU = """
  What do you see?
    p = a bit pink          g = a bit green
    b = too blue            y = too yellow / warm
    + = brighter (more white LED)    - = dimmer, more color-mixed
    w = show warm white for comparison   c = show cold white again
    s = save and quit       q = quit and restore the original value
"""


def parse_rgbw(value):
    v = value.upper()[:8].ljust(8, "0")
    return [int(v[i:i + 2], 16) for i in range(0, 8, 2)]


def fmt_rgbw(ch):
    return "".join(f"{max(0, min(255, c)):02X}" for c in ch)


def cmd_calibrate(args):
    bulb = Bulb(args.ip, args.password)
    require_tasmota(bulb)
    current = bulb.cmd("VirtualCT").get("VirtualCT", {})
    if "153" not in current:
        die("VirtualCT is not set. Run 'configure' first.")
    original = {k: v[:8] for k, v in current.items()}
    warm = original.get("500", "000000FF")
    ch = parse_rgbw(original["153"])

    def apply():
        bulb.cmd("VirtualCT " + json.dumps({"153": fmt_rgbw(ch), "500": warm}, separators=(",", ":")))
        bulb.cmd("Backlog Power ON; Dimmer 100; CT 300")
        bulb.cmd("CT 153")    # re-select so the new mix is shown

    say("Cold white calibration. Small steps; colors look different on phone cameras,")
    say("so trust your eyes. Current value: " + fmt_rgbw(ch))
    apply()
    while True:
        say(CAL_MENU)
        choice = input(f"  [{fmt_rgbw(ch)}] > ").strip().lower()
        if choice == "p":
            ch[1] += 8
        elif choice == "g":
            ch[1] -= 8
        elif choice == "b":
            ch[2] -= 16
        elif choice == "y":
            ch[2] += 16
        elif choice == "+":
            ch[3] += 32
            ch[2] += 12     # the white LED is warm: compensate with a little blue
        elif choice == "-":
            ch[3] -= 32
            ch[2] -= 12
        elif choice == "w":
            bulb.cmd("CT 500")
            continue
        elif choice == "c":
            bulb.cmd("CT 153")
            continue
        elif choice == "s":
            final = {"153": fmt_rgbw(ch), "500": warm}
            apply_virtual_ct(bulb, final)
            if not rule_matches(bulb, final):
                die(f"Could not save {CT_RULE}; the value will be lost on reboot.")
            path = save_backup(bulb, bulb.cmd("FriendlyName1").get("FriendlyName1") or args.ip)
            say(f"Saved on the bulb (survives reboots via {CT_RULE}). Cold white = {fmt_rgbw(ch)}")
            say(f"Config backup: {path}")
            say(f"To reuse it on another bulb: python w31n13h.py configure --ip <IP> --name <NAME> --cold {fmt_rgbw(ch)}")
            return
        elif choice == "q":
            bulb.cmd("VirtualCT " + vct_json(original))   # the boot rule was never changed
            bulb.cmd("CT 153")
            say("Original value restored.")
            return
        else:
            continue
        ch = [max(0, min(255, c)) for c in ch]
        apply()


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def main():
    # "sengled" passes every following argument straight to SengledTools.
    if len(sys.argv) > 1 and sys.argv[1] == "sengled":
        sys.exit(run_sengled(sys.argv[2:]))

    p = argparse.ArgumentParser(
        prog="w31n13h.py",
        description="Flash Sengled W31-N13H bulbs with Tasmota, 100% locally.",
        epilog='SengledTools pass-through:  python w31n13h.py sengled <SengledTools options>')
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("setup", help="download SengledTools + Tasmota, create the venv")
    s.add_argument("--upstream", default="tested", metavar="tested|latest",
                   help="SengledTools version (default: tested commit)")
    s.add_argument("--tasmota", default=TASMOTA_TAG, metavar="TAG|latest",
                   help=f"Tasmota release (default: {TASMOTA_TAG}, the tested one)")
    s.add_argument("--force", action="store_true", help="download again even if present")
    s.set_defaults(func=cmd_setup)

    sub.add_parser("sengled", help="run SengledTools (e.g. sengled --setup-wifi)")

    def bulb_args(sp):
        sp.add_argument("--ip", required=True, help="bulb IP address on your network")
        sp.add_argument("--password", help="Tasmota web password, if you set one")

    c = sub.add_parser("check", help="check a Tasmota bulb and its HTTP API")
    bulb_args(c)
    c.set_defaults(func=cmd_check)

    c = sub.add_parser("configure", help="apply template, Hue emulation and colors")
    bulb_args(c)
    c.add_argument("--name", required=True, help='name shown in Alexa/Tasmota, e.g. "Sengled kitchen"')
    c.add_argument("--cold", metavar="RRGGBBWW",
                   help="custom cold-white mix (default from config/w31-n13h.json)")
    c.add_argument("--dry-run", action="store_true", help="print the commands without sending them")
    c.set_defaults(func=cmd_configure)

    c = sub.add_parser("calibrate", help="interactively fine-tune the cold white")
    bulb_args(c)
    c.set_defaults(func=cmd_calibrate)

    c = sub.add_parser("backup", help="download the bulb's Tasmota configuration")
    bulb_args(c)
    c.add_argument("--name", help="label for the file (default: bulb name)")
    c.set_defaults(func=cmd_backup)

    args = p.parse_args()
    if getattr(args, "func", None) is None:
        p.print_help()
        return
    try:
        args.func(args)
    except KeyboardInterrupt:
        say("\nCancelled.")
        sys.exit(130)


if __name__ == "__main__":
    main()
