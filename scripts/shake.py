#!/usr/bin/env python3
"""
shake.py - Cross-platform, Multi-device Anti-Shake-Ad Manager
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

def sanitize_device_id(device):
    return device.replace(":", "_").replace(".", "_").replace("/", "_")

def main():
    parser = argparse.ArgumentParser(description="Mute sensors for apps with aggressive shake-ads")
    parser.add_argument("action", choices=["scan", "apply", "reset"], help="Action to execute")
    parser.add_argument("--device", "-s", help="Target device serial")
    parser.add_argument("--rule", help="Custom rule JSON path")
    args = parser.parse_args()

    res = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    devs = [l.split()[0] for l in res.stdout.splitlines()[1:] if len(l.split()) >= 2 and l.split()[1] == "device"]

    device = args.device
    if device:
        if device not in devs:
            print(f"Error: Target device '{device}' is not connected via ADB.", file=sys.stderr)
            sys.exit(1)
    else:
        if not devs:
            print("Error: No connected device found.", file=sys.stderr)
            sys.exit(1)
        device = devs[0]

    rule_file = args.rule if args.rule else os.path.join(ROOT_DIR, "rules", "apps_antispam.json")
    if not os.path.isabs(rule_file):
        rule_file = os.path.join(ROOT_DIR, rule_file)

    if not os.path.exists(rule_file):
        print(f"Error: Rule file not found: {rule_file}", file=sys.stderr)
        sys.exit(1)

    with open(rule_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    target_apps = data.get("shake_ad_apps", [])

    print("=" * 60)
    print(f" NoBS-Android Anti-Shake-Ad Tool")
    print(f" Device: {device} | Action: {args.action.upper()}")
    print("=" * 60)

    # 3rd-party installed packages
    out_3rd, _, code3 = run_adb(["shell", "pm", "list", "packages", "-3"], device)
    if code3 != 0:
        print(f"Error querying 3rd party packages on {device}", file=sys.stderr)
        sys.exit(1)
    installed_3rd = set(l.replace("package:", "").strip() for l in out_3rd.splitlines() if l.strip())

    matched = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dev_folder = sanitize_device_id(device)
    snapshots_dir = os.path.join(ROOT_DIR, "snapshots", dev_folder)
    os.makedirs(snapshots_dir, exist_ok=True)
    rollback_file = os.path.join(snapshots_dir, f"rollback_shake_{timestamp}.json")
    rollback_actions = []

    for item in target_apps:
        pkg = item["package"]
        name = item["name"]
        desc = item.get("desc", "")
        if pkg in installed_3rd:
            matched.append(item)
            if args.action == "apply":
                print(f"[!] Muting sensors for: {name} ({pkg})...", end=" ")
                run_adb(["shell", "cmd", "appops", "set", pkg, "BODY_SENSORS", "ignore"], device)
                run_adb(["shell", "cmd", "appops", "set", pkg, "ACTIVITY_RECOGNITION", "ignore"], device)
                print("LOCKED")
                rollback_actions.append({"package": pkg, "appops": ["BODY_SENSORS", "ACTIVITY_RECOGNITION"]})
            elif args.action == "reset":
                print(f"[!] Resetting sensors for: {name} ({pkg})...", end=" ")
                run_adb(["shell", "cmd", "appops", "set", pkg, "BODY_SENSORS", "default"], device)
                run_adb(["shell", "cmd", "appops", "set", pkg, "ACTIVITY_RECOGNITION", "default"], device)
                print("RESET")
            else:
                bs_status, _, _ = run_adb(["shell", "cmd", "appops", "get", pkg, "BODY_SENSORS"], device)
                status = "MUTED" if "ignore" in bs_status else "ACTIVE"
                print(f"[+] Found: {name} ({pkg}) -> Status: {status}")
                print(f"    Target: {desc}")

    print("-" * 60)
    print(f"Total target apps found installed: {len(matched)} / {len(target_apps)}")

    if args.action == "apply" and rollback_actions:
        with open(rollback_file, "w", encoding="utf-8") as f:
            json.dump({
                "device": device,
                "timestamp": timestamp,
                "type": "shake_sensor_rollback",
                "actions": rollback_actions
            }, f, indent=2, ensure_ascii=False)
        print(f"Rollback file saved for {device}: {rollback_file}")

if __name__ == "__main__":
    main()
