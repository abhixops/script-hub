#!/usr/bin/env python3
import os
import platform
import psutil
import socket
import shutil
import getpass
import subprocess
import time
from datetime import timedelta

# ─────────────────────────────
# Colors (Nord-inspired)
# ─────────────────────────────
colors = {
    "fg": "\033[38;2;171;178;191m",
    "red": "\033[38;2;224;108;117m",
    "green": "\033[38;2;152;195;121m",
    "yellow": "\033[38;2;229;192;123m",
    "blue": "\033[38;2;97;175;239m",
    "magenta": "\033[38;2;198;120;221m",
    "cyan": "\033[38;2;86;182;194m",
    "white": "\033[38;2;255;255;255m",
    "reset": "\033[0m"
}

# ─────────────────────────────
# Info Functions
# ─────────────────────────────
def get_user_host():
    return f"{getpass.getuser()}@{platform.node()}"

def get_os():
    return f"{platform.system()} {platform.release()}"

def get_cpu():
    return platform.processor() or "Unknown CPU"

def get_battery():
    try:
        battery = psutil.sensors_battery()
        if battery:
            return f"{battery.percent}%"
        return "Not Available"
    except Exception:
        return "Not Available"

def get_temp():
    # macOS needs istats for accurate temp
    return "Not Available (use istats)"

def get_wm():
    # On macOS, Finder is always running
    return "Finder"

def get_uptime():
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time
    td = timedelta(seconds=int(uptime_seconds))
    # Short format: days, hours:minutes
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes = remainder // 60
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    return f"{hours}h {minutes}m"

def get_memory():
    mem = psutil.virtual_memory()
    used = round((mem.total - mem.available) / (1024**2))
    total = round(mem.total / (1024**2))
    return f"{used}MiB / {total}MiB ({mem.percent}%)"

def get_disk():
    total, used, free = shutil.disk_usage("/")
    used_gb = round(used / (1024**3))
    total_gb = round(total / (1024**3))
    percent = int((used / total) * 100)
    return f"{used_gb}Gi / {total_gb}Gi ({percent}%)"

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "N/A"

# ─────────────────────────────
# Main
# ─────────────────────────────
def main():
    print("============================================")
    print(f"  {colors['blue']}{get_user_host()}{colors['reset']}")
    print(f"  {colors['green']}{get_os()}{colors['reset']}")
    print(f"  {colors['yellow']}{get_cpu()}{colors['reset']}")
    print(f"  {colors['magenta']}{get_battery()}{colors['reset']}")
    print(f"  {colors['cyan']}{get_temp()}{colors['reset']}")
    print(f" 缾 {colors['red']}{get_wm()}{colors['reset']}")
    print(f"  {colors['fg']}{get_uptime()}{colors['reset']}")
    print(f"  {colors['green']}{get_memory()}{colors['reset']}")
    print(f"  {colors['yellow']}{get_disk()}{colors['reset']}")
    print(f"  {colors['blue']}{get_ip()}{colors['reset']}")
    print(f" 🍀🌸🐱🐶🐹🐰")
    print("============================================")

if __name__ == "__main__":
    main()