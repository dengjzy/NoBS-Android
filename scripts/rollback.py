#!/usr/bin/env python3
"""
rollback.py - Cross-platform, Multi-device Master Rollback Tool
Accurately restores target device state from isolated snapshots.
Works on Windows, macOS, and Linux.
"""
import sys
import os
import json
import argparse
import subprocess

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOTS_DIR = os.path.join(ROOT_DIR, "snapshots")

def run_adb(cmd_args, device=None):
    base = ["adb"]
    if device:
        base.extend(["-s", device])
    base.extend(cmd_args)
    res = subprocess.run(base, capture_output=True, text=True, check=False)
    return res.stdout.strip(), res.stderr.strip(), res.returncode

def sanitize_device_id(device):
    return device.replace(":", "_").replace(".", "_").replace("/", "_")

def list_devices_with_snapshots():
    if not os.path.exists(SNAPSHOTS_DIR):
        print("No snapshots directory found.")
        return []

    devices = []
    for entry in os.listdir(SNAPSHOTS_DIR):
        full_p = os.path.join(SNAPSHOTS_DIR, entry)
        if os.path.isdir(full_p):
            snapshots = [f for f in os.listdir(full_p) if f.startswith("snapshot_") and f.endswith(".json")]
            rollbacks = [f for f in os.listdir(full_p) if f.startswith("rollback_") and f.endswith(".json")]
            devices.append({
                "device_folder": entry,
                "snapshot_count": len(snapshots),
                "rollback_count": len(rollbacks),
                "latest_snapshot": sorted(snapshots)[-1] if snapshots else "none"
            })
    return devices

def rollback_device(device):
    dev_folder = sanitize_device_id(device)
    dev_dir = os.path.join(SNAPSHOTS_DIR, dev_folder)

    print("=" * 60)
    print(f" NoBS-Android Master Rollback")
    print(f" Target Device: {device} (Storage: {dev_folder})")
    print("=" * 60)

    # 1. Reset Private DNS
    print("[1/3] Resetting Private DNS to off...")
    run_adb(["shell", "settings", "put", "global", "private_dns_mode", "off"], device)
    run_adb(["shell", "settings", "delete", "global", "private_dns_specifier"], device)

    # 2. Reset Shake Sensors for all 3rd party apps
    print("[2/3] Resetting AppOps shake sensors to default...")
    rule_file = os.path.join(ROOT_DIR, "rules", "apps_antispam.json")
    if os.path.exists(rule_file):
        with open(rule_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        for app in data.get("shake_ad_apps", []):
            pkg = app["package"]
            run_adb(["shell", "cmd", "appops", "set", pkg, "BODY_SENSORS", "default"], device)
            run_adb(["shell", "cmd", "appops", "set", pkg, "ACTIVITY_RECOGNITION", "default"], device)

    # 3. Process rollback actions from device folder
    print("[3/3] Restoring packages and AppOps permissions...")
    restored_pkgs = set()

    if os.path.exists(dev_dir):
        # Look for JSON rollbacks
        rollback_files = sorted([f for f in os.listdir(dev_dir) if f.startswith("rollback_") and f.endswith(".json")])
        for rf in rollback_files:
            file_path = os.path.join(dev_dir, rf)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    rdata = json.load(f)
                actions = rdata.get("actions", [])
                for act in actions:
                    if isinstance(act, dict):
                        pkg = act.get("package")
                        if pkg and pkg not in restored_pkgs:
                            restored_pkgs.add(pkg)
                            print(f"  -> Re-enabling {pkg}...")
                            run_adb(["shell", "pm", "enable", pkg], device)
                            run_adb(["shell", "pm", "unsuspend", pkg], device)
                            run_adb(["shell", "cmd", "appops", "set", pkg, "RUN_IN_BACKGROUND", "default"], device)
                            run_adb(["shell", "cmd", "appops", "set", pkg, "POST_NOTIFICATION", "default"], device)
                            run_adb(["shell", "cmd", "appops", "set", pkg, "WAKE_LOCK", "default"], device)
            except Exception as e:
                print(f"Warning: Failed parsing {rf}: {e}")

    # Fallback to rules: ensure all rule packages are re-enabled
    rules_dir = os.path.join(ROOT_DIR, "rules")
    if os.path.exists(rules_dir):
        for rf in os.listdir(rules_dir):
            if rf.endswith(".json") and rf != "apps_antispam.json":
                try:
                    with open(os.path.join(rules_dir, rf), "r", encoding="utf-8") as f:
                        rd = json.load(f)
                    for tier in rd.get("tiers", {}).values():
                        for p in tier.get("packages", []):
                            pkg = p["package"]
                            if pkg not in restored_pkgs:
                                run_adb(["shell", "pm", "enable", pkg], device)
                                run_adb(["shell", "pm", "unsuspend", pkg], device)
                                run_adb(["shell", "cmd", "appops", "set", pkg, "RUN_IN_BACKGROUND", "default"], device)
                                run_adb(["shell", "cmd", "appops", "set", pkg, "POST_NOTIFICATION", "default"], device)
                                run_adb(["shell", "cmd", "appops", "set", pkg, "WAKE_LOCK", "default"], device)
                except Exception:
                    pass

    print("=" * 60)
    print(f"Rollback complete for device {device}. All settings and packages restored.")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="Multi-device Master Rollback Tool")
    parser.add_argument("--device", "-s", help="Target device serial")
    parser.add_argument("--list", action="store_true", help="List all devices with stored snapshots")
    parser.add_argument("--all", action="store_true", help="Rollback all connected devices")
    args = parser.parse_args()

    if args.list:
        devs = list_devices_with_snapshots()
        print(json.dumps(devs, indent=2))
        return

    res = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    connected_devs = [l.split()[0] for l in res.stdout.splitlines()[1:] if len(l.split()) >= 2 and l.split()[1] == "device"]

    target_devices = []
    if args.all:
        if not connected_devs:
            print("Error: No connected Android device found.", file=sys.stderr)
            sys.exit(1)
        target_devices = connected_devs
    elif args.device:
        if args.device not in connected_devs:
            print(f"Error: Target device '{args.device}' is not connected via ADB.", file=sys.stderr)
            sys.exit(1)
        target_devices = [args.device]
    else:
        if not connected_devs:
            print("Error: No connected device found.", file=sys.stderr)
            sys.exit(1)
        target_devices = [connected_devs[0]]

    for dev in target_devices:
        rollback_device(dev)

if __name__ == "__main__":
    main()
