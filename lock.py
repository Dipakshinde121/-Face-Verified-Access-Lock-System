"""
lock.py - Workstation Lock Module.
"""
import ctypes
import os

def lock_workstation() -> bool:
    """Executes OS-level workstation lock."""
    try:
        if os.name == "nt":
            return bool(ctypes.windll.user32.LockWorkStation())
        return os.system("loginctl lock-session >/dev/null 2>&1") == 0
    except Exception as e:
        print(f"[Lock Error] Failed to execute lock: {e}")
        return False

if __name__ == "__main__":
    lock_workstation()
