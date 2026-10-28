#!/usr/bin/env python3
"""
debloat.py - Cross-platform, Multi-device Safe Package Manager
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
    parser = argparse.ArgumentParser(description="NoBS-Android Debloat Tool")
    parser.add_argument("action", choices=["dry-run", "apply"], help="Execution mode")
    parser.add_argument("rule", help="Path to rules JSON file")
    parser.add_argument("--tier", default="tier0_pure_ads", help="Tier to target (default: tier0_pure_ads)")
    parser.add_argument("--device", "-s", help="Target device serial")
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

    rule_file = args.rule
    if not os.path.isabs(rule_file):
        rule_file = os.path.join(ROOT_DIR, rule_file)

    if not os.path.exists(rule_file):
        print(f"Error: Rule file not found: {rule_file}", file=sys.stderr)
        sys.exit(1)

    with open(rule_file, "r", encoding="utf-8") as f:
        rule_data = json.load(f)

    tier = rule_data.get("tiers", {}).get(args.tier, {})
    tier_desc = tier.get("name", args.tier)
    candidates = tier.get("packages", [])

    print("=" * 60)
    print(f" NoBS-Android Debloat Tool")
    print(f" Device: {device} | Action: {args.action.upper()} | Target: {tier_desc}")
    print("=" * 60)

    # Installed & disabled packages
    out_e, _, code_e = run_adb(["shell", "pm", "list", "packages"], device)
    if code_e != 0:
        print(f"Error querying packages on device {device}", file=sys.stderr)
        sys.exit(1)
    installed = set(l.replace("package:", "").strip() for l in out_e.splitlines() if l.strip())

    out_d, _, _ = run_adb(["shell", "pm", "list", "packages", "-d"], device)
    disabled = set(l.replace("package:", "").strip() for l in out_d.splitlines() if l.strip())

    matched = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dev_folder = sanitize_device_id(device)
    snapshots_dir = os.path.join(ROOT_DIR, "snapshots", dev_folder)
    os.makedirs(snapshots_dir, exist_ok=True)
    
    rollback_file = os.path.join(snapshots_dir, f"rollback_debloat_{timestamp}.json")
    rollback_actions = []

    for item in candidates:
        pkg = item["package"]
        name = item["name"]
        reason = item.get("reason", "")
        risk = item.get("risk", "none")

        if pkg in installed:
            is_disabled = pkg in disabled
            matched.append((item, is_disabled))
            if is_disabled:
                print(f"[-] {name} ({pkg}): Already disabled (OK)")
            else:
                if args.action == "apply":
                    print(f"[!] Processing: {name} ({pkg})...", end=" ")
                    out, err, code = run_adb(["shell", "pm", "disable-user", "--user", "0", pkg], device)
                    if code == 0 and ("disabled" in out.lower() or "disabled-user" in out.lower()):
                        print("SUCCESS (disabled-user)")
                        rollback_actions.append({"type": "pm_enable", "package": pkg})
                    else:
                        out_s, _, code_s = run_adb(["shell", "pm", "suspend", pkg], device)
                        if code_s == 0 and "package" in out_s.lower():
                            print("SUCCESS (pm suspend)")
                            rollback_actions.append({"type": "pm_unsuspend", "package": pkg})
                        else:
                            # AppOps fallback for vendor-restricted packages (e.g. OriginOS)
                            run_adb(["shell", "cmd", "appops", "set", pkg, "RUN_IN_BACKGROUND", "ignore"], device)
                            run_adb(["shell", "cmd", "appops", "set", pkg, "POST_NOTIFICATION", "ignore"], device)
                            run_adb(["shell", "cmd", "appops", "set", pkg, "WAKE_LOCK", "ignore"], device)
                            print("MUTED via AppOps (Background, Push & Wakelock revoked)")
                            rollback_actions.append({"type": "appops_default", "package": pkg})
                else:
                    print(f"[+] Match: {name} ({pkg})")
                    print(f"    Reason: {reason} [Risk: {risk}]")

    print("-" * 60)
    print(f"Total matched: {len(matched)} / {len(candidates)} packages")

    if args.action == "apply" and rollback_actions:
        with open(rollback_file, "w", encoding="utf-8") as f:
            json.dump({
                "device": device,
                "timestamp": timestamp,
                "actions": rollback_actions
            }, f, indent=2, ensure_ascii=False)
        print(f"Rollback file saved for {device}: {rollback_file}")

if __name__ == "__main__":
    main()
