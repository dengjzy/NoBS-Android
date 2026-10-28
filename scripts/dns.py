#!/usr/bin/env python3
"""
dns.py - Cross-platform System-wide DoT Private DNS Manager
Works seamlessly on Windows, macOS, and Linux.
"""
import sys
import argparse
import subprocess

def run_adb(cmd_args, device=None):
    base = ["adb"]
    if device:
        base.extend(["-s", device])
    base.extend(cmd_args)
    res = subprocess.run(base, capture_output=True, text=True, check=False)
    if res.returncode != 0:
        err_msg = res.stderr.strip()
        print(f"ADB Error (code {res.returncode}): {err_msg}", file=sys.stderr)
        if "not found" in err_msg.lower() or "device offline" in err_msg.lower():
            sys.exit(1)
    return res.stdout.strip(), res.stderr.strip(), res.returncode

def main():
    parser = argparse.ArgumentParser(description="Manage Android Private DNS (DoT)")
    parser.add_argument("action", choices=["status", "enable", "disable"], help="Action to perform")
    parser.add_argument("--device", "-s", help="Target device serial")
    parser.add_argument("--provider", default="dns.adguard-dns.com", help="DoT Provider hostname (default: dns.adguard-dns.com)")
    args = parser.parse_args()

    # Pre-check device connectivity
    res = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    connected = [l.split()[0] for l in res.stdout.splitlines()[1:] if len(l.split()) >= 2 and l.split()[1] == "device"]
    target = args.device
    if target:
        if target not in connected:
            print(f"Error: Target device '{target}' is not connected or unauthorized via ADB.", file=sys.stderr)
            sys.exit(1)
    else:
        if not connected:
            print("Error: No connected Android device found via ADB.", file=sys.stderr)
            sys.exit(1)
        target = connected[0]

    if args.action == "status":
        mode, _, code1 = run_adb(["shell", "settings", "get", "global", "private_dns_mode"], target)
        spec, _, code2 = run_adb(["shell", "settings", "get", "global", "private_dns_specifier"], target)
        if code1 != 0 or code2 != 0:
            print(f"Error querying Private DNS on {target}", file=sys.stderr)
            sys.exit(1)
        print(f"Device: {target}")
        print(f"Private DNS Mode: {mode if mode else 'off'}")
        print(f"Specifier/Host:   {spec if spec else 'none'}")
    elif args.action == "enable":
        print(f"Setting Private DNS to {args.provider} on {target}...")
        _, _, c1 = run_adb(["shell", "settings", "put", "global", "private_dns_mode", "hostname"], target)
        _, _, c2 = run_adb(["shell", "settings", "put", "global", "private_dns_specifier", args.provider], target)
        if c1 == 0 and c2 == 0:
            print("Done. System-wide encrypted ad-blocking DNS is now ACTIVE.")
        else:
            print("Failed setting Private DNS.", file=sys.stderr)
            sys.exit(1)
    elif args.action == "disable":
        print(f"Disabling Private DNS on {target}...")
        _, _, c1 = run_adb(["shell", "settings", "put", "global", "private_dns_mode", "off"], target)
        _, _, c2 = run_adb(["shell", "settings", "delete", "global", "private_dns_specifier"], target)
        if c1 == 0:
            print("Done. Private DNS disabled.")
        else:
            print("Failed disabling Private DNS.", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
