#!/usr/bin/env python3
"""
probe.py - Cross-platform Android Device Detection Tool
Works seamlessly on Windows, macOS, and Linux (Python 3 standard library only).
"""
import sys
import os
import json
import subprocess
import argparse

def run_adb(cmd_args, device=None):
    base = ["adb"]
    if device:
        base.extend(["-s", device])
    base.extend(cmd_args)
    try:
        res = subprocess.run(base, capture_output=True, text=True, check=False)
        return res.stdout.strip(), res.stderr.strip(), res.returncode
    except FileNotFoundError:
        print(json.dumps({"error": "ADB not found. Please install Android Platform Tools and add to PATH."}))
        sys.exit(1)

def get_connected_devices():
    stdout, _, _ = run_adb(["devices"])
    devices = []
    for line in stdout.splitlines()[1:]:
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])
    return devices

def probe_device(device):
    def getprop(prop_name):
        out, _, _ = run_adb(["shell", "getprop", prop_name], device)
        return out.strip()

    brand = getprop("ro.product.brand").lower()
    manufacturer = getprop("ro.product.manufacturer")
    model = getprop("ro.product.model")
    market_name = getprop("ro.product.marketname")
    android_ver = getprop("ro.build.version.release")
    display_id = getprop("ro.build.display.id")

    # Detect ROM family
    vivo_ver = getprop("ro.vivo.os.version")
    miui_ver = getprop("ro.miui.ui.version.name")
    oppo_ver = getprop("ro.build.version.opporom")
    oplus_ver = getprop("ro.build.version.oplusrom")
    magic_ver = getprop("ro.build.version.magic")

    rom_family = "generic"
    rom_version = "Unknown"
    rule_file = "rules/generic.json"

    if vivo_ver or brand in ["vivo", "iqoo"]:
        rom_family = "vivo_originos"
        rom_version = f"OriginOS {vivo_ver}" if vivo_ver else "OriginOS"
        rule_file = "rules/vivo_originos.json"
    elif miui_ver or brand in ["xiaomi", "redmi", "poco"]:
        rom_family = "xiaomi_hyperos"
        rom_version = f"HyperOS/MIUI {miui_ver}" if miui_ver else "HyperOS/MIUI"
        rule_file = "rules/xiaomi_hyperos.json"
    elif oppo_ver or oplus_ver or brand in ["oppo", "oneplus", "realme"]:
        rom_family = "oppo_coloros"
        rom_version = f"ColorOS {oplus_ver or oppo_ver}"
        rule_file = "rules/oppo_coloros.json"
    elif magic_ver or brand in ["honor"]:
        rom_family = "honor_magicos"
        rom_version = f"MagicOS {magic_ver}"
        rule_file = "rules/honor_magicos.json"

    # Private DNS
    dns_mode, _, _ = run_adb(["shell", "settings", "get", "global", "private_dns_mode"], device)
    dns_spec, _, _ = run_adb(["shell", "settings", "get", "global", "private_dns_specifier"], device)

    # Package counts
    pkgs_e, _, _ = run_adb(["shell", "pm", "list", "packages", "-e"], device)
    pkgs_d, _, _ = run_adb(["shell", "pm", "list", "packages", "-d"], device)

    enabled_count = len([p for p in pkgs_e.splitlines() if p.startswith("package:")])
    disabled_count = len([p for p in pkgs_d.splitlines() if p.startswith("package:")])

    return {
        "device": device,
        "brand": brand,
        "manufacturer": manufacturer,
        "model": model,
        "market_name": market_name,
        "build_id": display_id,
        "android_version": android_ver,
        "rom_family": rom_family,
        "rom_version": rom_version,
        "matched_rule": rule_file,
        "private_dns": {
            "mode": dns_mode if dns_mode else "null",
            "specifier": dns_spec if dns_spec else "null"
        },
        "package_stats": {
            "enabled": enabled_count,
            "disabled": disabled_count
        }
    }

def main():
    parser = argparse.ArgumentParser(description="Probe connected Android device(s)")
    parser.add_argument("--device", "-s", help="Target device serial/IP:port")
    args = parser.parse_args()

    connected = get_connected_devices()
    if not connected:
        print(json.dumps({"error": "No connected Android devices found. Make sure USB/Wireless debugging is on."}))
        sys.exit(1)

    target_device = args.device
    if not target_device:
        target_device = connected[0]

    result = probe_device(target_device)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
