import platform
import os
import subprocess
import psutil

def get_os_info():
    return f"{platform.system()} {platform.release()}"

def get_host_info():
    return platform.node()

def get_kernel_info():
    return platform.version() # Or platform.release() for just the version number

def get_uptime_info():
    # This is a bit more complex. On Linux, you can parse /proc/uptime
    # Or use psutil for a cross-platform way.
    # For now, let's placeholder it
    try:
        # Simplified example for Linux by running 'uptime -p'
        result = subprocess.run(["uptime", "-p"], capture_output=True, text=True, check=True)
        return result.stdout.strip().replace("up ", "") # "up 2 hours, 10 minutes" -> "2 hours, 10 minutes"
    except Exception as e:
        print(f"Error fetching uptime: {e}")
        return "N/A"

def get_package_count_dpkg():
    try:
        result = subprocess.run("dpkg -l | grep -c ^ii", shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception:
        return "N/A"

def get_memory_info():
        # to be implemented
        pass
