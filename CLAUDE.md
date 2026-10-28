# CLAUDE.md - Andrej Karpathy Engineering Guidelines

This repository follows the core guidelines from [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) to ensure simplicity, safety, and verifiable outcomes:

## 1. Think Before Coding
* **Don't assume. Don't hide confusion. Surface tradeoffs.**
* State assumptions explicitly. If uncertain, pause and ask.
* Android debloating touches live hardware: never guess a package's purpose without verifying against system core dependencies.

## 2. Simplicity First
* **Minimum code that solves the problem. Nothing speculative.**
* No heavy framework bloat (no unnecessary daemons or dependencies).
* Use native ADB commands and minimal Python standard library scripts (`probe`, `debloat`, `dns`, `shake`).
* Keep changes surgical and readable.

## 3. Surgical Changes
* **Touch only what you must. Clean up only your own mess.**
* Strict safety boundaries:
  - NEVER execute `pm uninstall` (delete). Only `pm disable-user --user 0` or `pm suspend`.
  - ALWAYS capture a baseline snapshot before applying changes.
  - Generate a 100% reversible `rollback.sh` for every executed action.
* Never touch critical system frameworks (RIL, Telephony, Keyguard, biometrics, SystemUI).

## 4. Goal-Driven Execution
* **Define success criteria. Loop until verified.**
* Every action must have an explicit verification step:
  - Step 1: Snapshot creation -> Verify rollback script exists and is executable.
  - Step 2: Package disabling -> Verify via `pm list packages -d`.
  - Step 3: Shake ad muting -> Verify via `cmd appops get <pkg> BODY_SENSORS`.
  - Step 4: Private DNS -> Verify via `settings get global private_dns_mode`.
  - Step 5: Visual proof -> Capture before/after screenshots of the device.
