#!/usr/bin/env python3
"""
snapshot.py - Multi-device baseline snapshot & rollback generator.
Supports multiple devices independently without collision.
Works on Windows, macOS, and Linux.
"""
import sys
import os
import json
import argparse
import subprocess
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_adb(cmd_args, device=None):
    base = ["adb"]
    if device:
        base.extend(["-s", device])
    base.extend(cmd_args)
    res = subprocess.run(base, capture_output=True, text=True, check=False)
    return res.stdout.strip(), res.stderr.strip(), res.returncode

def get_connected_devices():
    res = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    return [l.split()[0] for l in res.stdout.splitlines()[1:] if len(l.split()) >= 2 and l.split()[1] == "device"]

def sanitize_device_id(device):
    return device.replace(":", "_").replace(".", "_").replace("/", "_")

def create_snapshot(device):
    dev_folder_name = sanitize_device_id(device)
    dev_dir = os.path.join(ROOT_DIR, "snapshots", dev_folder_name)
    os.makedirs(dev_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_json_path = os.path.join(dev_dir, f"snapshot_{timestamp}.json")

    # Capture enabled and disabled packages
    out_e, _, code1 = run_adb(["shell", "pm", "list", "packages", "-e"], device)
    out_d, _, code2 = run_adb(["shell", "pm", "list", "packages", "-d"], device)

    if code1 != 0 or code2 != 0:
        print(f"Error querying packages on device {device}", file=sys.stderr)
        sys.exit(1)

    enabled_pkgs = sorted([p.replace("package:", "").strip() for p in out_e.splitlines() if p.strip()])
    disabled_pkgs = sorted([p.replace("package:", "").strip() for p in out_d.splitlines() if p.strip()])

    # Capture settings
    dns_mode, _, _ = run_adb(["shell", "settings", "get", "global", "private_dns_mode"], device)
    dns_spec, _, _ = run_adb(["shell", "settings", "get", "global", "private_dns_specifier"], device)

    # Device metadata
    brand, _, _ = run_adb(["shell", "getprop", "ro.product.brand"], device)
    model, _, _ = run_adb(["shell", "getprop", "ro.product.model"], device)

    snapshot_data = {
        "device": device,
        "device_folder": dev_folder_name,
        "timestamp": timestamp,
        "brand": brand,
        "model": model,
        "private_dns": {
            "mode": dns_mode if dns_mode else "off",
            "specifier": dns_spec if dns_spec else ""
        },
        "enabled_count": len(enabled_pkgs),
        "disabled_count": len(disabled_pkgs),
        "disabled_packages": disabled_pkgs
    }

    with open(snapshot_json_path, "w", encoding="utf-8") as f:
        json.dump(snapshot_data, f, indent=2, ensure_ascii=False)

    print(json.dumps({
        "status": "success",
        "device": device,
        "timestamp": timestamp,
        "snapshot_path": snapshot_json_path
    }, indent=2, ensure_ascii=False))

def main():
    parser = argparse.ArgumentParser(description="Create multi-device safety baseline snapshot")
    parser.add_argument("--device", "-s", help="Target device serial")
    args = parser.parse_args()

    connected = get_connected_devices()
    device = args.device
    if device:
        if device not in connected:
            print(f"Error: Target device '{device}' is not connected via ADB.", file=sys.stderr)
            sys.exit(1)
    else:
        if not connected:
            print(json.dumps({"error": "No connected device found"}))
            sys.exit(1)
        device = connected[0]

    create_snapshot(device)

if __name__ == "__main__":
    main()
