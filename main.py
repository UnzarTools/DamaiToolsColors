#!/usr/bin/env python3
"""
DamaiTool — Entry Point
======================
1. Requests Administrator elevation (required for SetDeviceGammaRamp).
2. Sets the working directory so relative paths work in both dev & frozen mode.
3. Launches the DamaiToolApp.
"""

import sys
import os
import ctypes


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def elevate():
    """Re-launch the current script / exe with Administrator rights via UAC."""
    if getattr(sys, "frozen", False):
        # Frozen .exe — re-launch the exe itself
        exe  = sys.executable
        args = " ".join(f'"{a}"' for a in sys.argv[1:])
    else:
        # Plain .py script — re-launch via python
        exe  = sys.executable
        args = f'"{os.path.abspath(__file__)}"'
    ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, args, None, 1)


if __name__ == "__main__":
    # ── Admin elevation ────────────────────────────────────────────────────
    if not is_admin():
        elevate()
        sys.exit(0)

    # ── Working directory ──────────────────────────────────────────────────
    if getattr(sys, "frozen", False):
        os.chdir(os.path.dirname(sys.executable))
    else:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # ── Launch ─────────────────────────────────────────────────────────────
    try:
        from app import DamaiToolApp
        DamaiToolApp().run()
    except Exception:
        import traceback
        msg = traceback.format_exc()
        ctypes.windll.user32.MessageBoxW(
            0,
            f"DamaiTool failed to start:\n\n{msg}",
            "DamaiTool — Error",
            0x10  # MB_ICONERROR
        )
        sys.exit(1)
