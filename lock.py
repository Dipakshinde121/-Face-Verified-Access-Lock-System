"""
lock.py - Cross-platform OS Lock Module
Companion to TRD v1.0 §2.
Provides unified OS workstation locking mechanism for Windows, Linux, and macOS.
"""

import os
import platform
import subprocess

def lock_workstation():
    """
    Executes an OS-level workstation lock.
    Returns True if the lock signal was successfully dispatched, False otherwise.
    """
    sys_os = platform.system()
    try:
        if sys_os == "Windows":
            import ctypes
            return bool(ctypes.windll.user32.LockWorkStation())
        elif sys_os == "Linux":
            # Attempt standard Desktop Environment screen lock commands
            commands = [
                ["loginctl", "lock-session"],
                ["dbus-send", "--type=method_call", "--dest=org.gnome.ScreenSaver",
                 "/org/gnome/ScreenSaver", "org.gnome.ScreenSaver.Lock"],
                ["xdg-screensaver", "lock"]
            ]
            for cmd in commands:
                try:
                    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    if res.returncode == 0:
                        return True
                except FileNotFoundError:
                    continue
            return False
        elif sys_os == "Darwin":
            res = subprocess.run(["pmset", "displaysleepnow"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return res.returncode == 0
        else:
            print(f"[Lock Warning] Unsupported operating system: {sys_os}")
            return False
    except Exception as e:
        print(f"[Lock Error] Failed to execute workstation lock: {e}")
        return False

if __name__ == "__main__":
    print("[Testing] Triggering workstation lock...")
    lock_workstation()
