#!/usr/bin/env python3
"""
PyFetch - A cross-platform system information tool
Compatible with Linux, macOS, BSD, and other Unix-like systems
"""

import os
import sys
import platform
import subprocess
import socket
import pwd
import time
from datetime import timedelta
import shutil

class Colors:
    """ANSI color codes for terminal output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'

class SystemInfo:
    def __init__(self):
        self.system = platform.system()
        self.info = {}
        self.collect_info()
    
    def run_command(self, cmd, shell=True):
        """Safely run a command and return output"""
        try:
            result = subprocess.run(cmd, shell=shell, capture_output=True, 
                                  text=True, timeout=5)
            return result.stdout.strip() if result.returncode == 0 else None
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            return None
    
    def get_distro_info(self):
        """Get distribution information"""
        if self.system == "Darwin":
            # macOS
            version = platform.mac_ver()[0]
            return f"macOS {version}"
        elif self.system == "Linux":
            # Try multiple methods to get Linux distro info
            if os.path.exists('/etc/os-release'):
                try:
                    with open('/etc/os-release', 'r') as f:
                        lines = f.readlines()
                        for line in lines:
                            if line.startswith('PRETTY_NAME='):
                                return line.split('=', 1)[1].strip().strip('"')
                except:
                    pass
            
            # Fallback methods
            for cmd in ['lsb_release -d', 'cat /etc/issue']:
                result = self.run_command(cmd)
                if result:
                    if 'lsb_release' in cmd:
                        return result.split('\t')[1] if '\t' in result else result
                    else:
                        return result.split('\\')[0].strip()
            
            return f"Linux {platform.release()}"
        else:
            # Other Unix systems (BSD, etc.)
            return f"{self.system} {platform.release()}"
    
    def get_kernel_info(self):
        """Get kernel information"""
        return platform.release()
    
    def get_uptime(self):
        """Get system uptime"""
        try:
            if self.system == "Darwin":
                # macOS
                result = self.run_command("sysctl -n kern.boottime")
                if result:
                    boot_time = float(result.split(',')[0].split()[-1])
                    uptime_seconds = time.time() - boot_time
                else:
                    return "Unknown"
            else:
                # Linux and other Unix systems
                if os.path.exists('/proc/uptime'):
                    with open('/proc/uptime', 'r') as f:
                        uptime_seconds = float(f.readline().split()[0])
                else:
                    # Fallback for systems without /proc/uptime
                    result = self.run_command("uptime -s")
                    if result:
                        from datetime import datetime
                        boot_time = datetime.strptime(result, "%Y-%m-%d %H:%M:%S")
                        uptime_seconds = (datetime.now() - boot_time).total_seconds()
                    else:
                        return "Unknown"
            
            uptime = str(timedelta(seconds=int(uptime_seconds)))
            # Format nicely
            parts = uptime.split(':')
            if len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                if hours >= 24:
                    days = hours // 24
                    hours = hours % 24
                    return f"{days}d {hours}h {minutes}m"
                else:
                    return f"{hours}h {minutes}m"
            return uptime
        except:
            return "Unknown"
    
    def get_packages(self):
        """Get package count"""
        package_managers = [
            ('dpkg', 'dpkg -l | grep -c "^ii"'),
            ('rpm', 'rpm -qa | wc -l'),
            ('pacman', 'pacman -Q | wc -l'),
            ('brew', 'brew list | wc -l'),
            ('pkg', 'pkg info | wc -l'),
            ('pkgin', 'pkgin list | wc -l'),
        ]
        
        for pm_name, cmd in package_managers:
            if shutil.which(pm_name.split()[0]):
                result = self.run_command(cmd)
                if result and result.isdigit():
                    return f"{result} ({pm_name})"
        
        return "Unknown"
    
    def get_shell(self):
        """Get current shell"""
        shell = os.environ.get('SHELL', '')
        if shell:
            return os.path.basename(shell)
        return "Unknown"
    
    def get_desktop_environment(self):
        """Get desktop environment"""
        # Check common DE environment variables
        desktop_vars = ['XDG_CURRENT_DESKTOP', 'DESKTOP_SESSION', 'GDMSESSION']
        
        for var in desktop_vars:
            de = os.environ.get(var, '').lower()
            if de:
                return de.title()
        
        # Check if we're in a terminal multiplexer or SSH
        if os.environ.get('SSH_CLIENT') or os.environ.get('SSH_TTY'):
            return "SSH"
        elif os.environ.get('TMUX'):
            return "tmux"
        elif os.environ.get('STY'):  # GNU Screen
            return "screen"
        
        return "TTY"
    
    def get_terminal(self):
        """Get terminal emulator"""
        term = os.environ.get('TERM_PROGRAM')
        if term:
            return term
        
        term = os.environ.get('TERM')
        if term:
            return term
        
        return "Unknown"
    
    def get_cpu_info(self):
        """Get CPU information"""
        if self.system == "Darwin":
            # macOS
            brand = self.run_command("sysctl -n machdep.cpu.brand_string")
            if brand:
                return brand
        elif self.system == "Linux":
            # Linux
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if line.startswith('model name'):
                            return line.split(':', 1)[1].strip()
            except:
                pass
        
        # Fallback
        return platform.processor() or "Unknown"
    
    def get_memory_info(self):
        """Get memory information"""
        if self.system == "Darwin":
            # macOS
            total = self.run_command("sysctl -n hw.memsize")
            if total:
                total_mb = int(total) // 1024 // 1024
                # Get used memory (approximate)
                vm_stat = self.run_command("vm_stat")
                if vm_stat:
                    pages_free = 0
                    page_size = 4096
                    for line in vm_stat.split('\n'):
                        if 'Pages free:' in line:
                            pages_free = int(line.split(':')[1].strip().rstrip('.'))
                            break
                    used_mb = total_mb - (pages_free * page_size // 1024 // 1024)
                    return f"{used_mb}MB / {total_mb}MB"
                return f"? / {total_mb}MB"
        elif self.system == "Linux":
            # Linux
            try:
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                    total = None
                    available = None
                    for line in meminfo.split('\n'):
                        if line.startswith('MemTotal:'):
                            total = int(line.split()[1]) // 1024
                        elif line.startswith('MemAvailable:'):
                            available = int(line.split()[1]) // 1024
                        elif available is None and line.startswith('MemFree:'):
                            available = int(line.split()[1]) // 1024
                    
                    if total and available:
                        used = total - available
                        return f"{used}MB / {total}MB"
            except:
                pass
        
        return "Unknown"
    
    def get_gpu_info(self):
        """Get GPU information"""
        # Try different methods to get GPU info
        gpu_commands = [
            "lspci | grep -i vga",
            "lspci | grep -i display",
            "system_profiler SPDisplaysDataType | grep 'Chipset Model'",
            "glxinfo | grep 'OpenGL renderer'",
            "nvidia-smi --query-gpu=name --format=csv,noheader,nounits",
        ]
        
        for cmd in gpu_commands:
            result = self.run_command(cmd)
            if result:
                # Clean up the result
                if "Chipset Model:" in result:
                    return result.split("Chipset Model:")[1].strip()
                elif "OpenGL renderer" in result:
                    return result.split("OpenGL renderer string:")[1].strip()
                elif "VGA" in result or "Display" in result:
                    # Extract GPU name from lspci output
                    parts = result.split(':')
                    if len(parts) >= 3:
                        return parts[2].strip()
                return result.strip()
        
        return "Unknown"
    
    def collect_info(self):
        """Collect all system information"""
        self.info = {
            'user': pwd.getpwuid(os.getuid()).pw_name,
            'hostname': socket.gethostname(),
            'os': self.get_distro_info(),
            'kernel': self.get_kernel_info(),
            'uptime': self.get_uptime(),
            'packages': self.get_packages(),
            'shell': self.get_shell(),
            'desktop': self.get_desktop_environment(),
            'terminal': self.get_terminal(),
            'cpu': self.get_cpu_info(),
            'memory': self.get_memory_info(),
            'gpu': self.get_gpu_info(),
        }
    
    def get_ascii_art(self):
        """Get ASCII art based on the system"""
        if self.system == "Darwin":
            return [
                "                    'c.",
                "                 ,xNMM.",
                "               .OMMMMo",
                "               OMMM0,",
                "     .;loddo:' loolloddol;.",
                "   cKMMMMMMMMMMNWMMMMMMMMMM0:",
                " .KMMMMMMMMMMMMMMMMMMMMMMMWd.",
                " XMMMMMMMMMMMMMMMMMMMMMMMX.",
                ";MMMMMMMMMMMMMMMMMMMMMMMM:",
                ":MMMMMMMMMMMMMMMMMMMMMMMM:",
                ".MMMMMMMMMMMMMMMMMMMMMMMMX.",
                " kMMMMMMMMMMMMMMMMMMMMMMMMWd.",
                " .XMMMMMMMMMMMMMMMMMMMMMMMMMMk",
                "  .XMMMMMMMMMMMMMMMMMMMMMMMMK.",
                "    kMMMMMMMMMMMMMMMMMMMMMMd",
                "     ;KMMMMMMMWXXWMMMMMMMk.",
                "       .cooc,.    .,coo:."
            ]
        elif "arch" in self.info.get('os', '').lower():
            return [
                "                   -`",
                "                  .o+`",
                "                 `ooo/",
                "                `+oooo:",
                "               `+oooooo:",
                "               -+oooooo+:",
                "             `/:-:++oooo+:",
                "            `/++++/+++++++:",
                "           `/++++++++++++++:",
                "          `/+++ooooooooo+++/`",
                "         ./ooosssso++osssssso+`",
                "        .oossssso-````/ossssss+`",
                "       -osssssso.      :ssssssso.",
                "      :osssssss/        osssso+++.",
                "     /ossssssss/        +ssssooo/-",
                "   `/ossssso+/:-        -:/+osssso+-",
                "  `+sso+:-`                 `.-/+oso:",
                " `++:.                           `-/+/",
                " .`                                 `/"
            ]
        else:
            # Generic Unix/Linux logo
            return [
                "        #####",
                "       #######",
                "       ##O#O##",
                "       #####",
                "     ##  ###  ##",
                "    #############",
                "   ###############",
                "   ################",
                "  #################",
                "#####################",
                "#####################",
                "  #################"
            ]
    
    def display(self):
        """Display the system information"""
        ascii_art = self.get_ascii_art()
        
        # Color scheme
        primary_color = Colors.CYAN
        secondary_color = Colors.WHITE
        accent_color = Colors.MAGENTA
        
        # Information lines
        info_lines = [
            f"{primary_color}{self.info['user']}{Colors.RESET}@{primary_color}{self.info['hostname']}{Colors.RESET}",
            "─" * (len(self.info['user']) + len(self.info['hostname']) + 1),
            f"{accent_color}OS{Colors.RESET}: {secondary_color}{self.info['os']}{Colors.RESET}",
            f"{accent_color}Kernel{Colors.RESET}: {secondary_color}{self.info['kernel']}{Colors.RESET}",
            f"{accent_color}Uptime{Colors.RESET}: {secondary_color}{self.info['uptime']}{Colors.RESET}",
            f"{accent_color}Packages{Colors.RESET}: {secondary_color}{self.info['packages']}{Colors.RESET}",
            f"{accent_color}Shell{Colors.RESET}: {secondary_color}{self.info['shell']}{Colors.RESET}",
            f"{accent_color}DE{Colors.RESET}: {secondary_color}{self.info['desktop']}{Colors.RESET}",
            f"{accent_color}Terminal{Colors.RESET}: {secondary_color}{self.info['terminal']}{Colors.RESET}",
            f"{accent_color}CPU{Colors.RESET}: {secondary_color}{self.info['cpu']}{Colors.RESET}",
            f"{accent_color}Memory{Colors.RESET}: {secondary_color}{self.info['memory']}{Colors.RESET}",
            f"{accent_color}GPU{Colors.RESET}: {secondary_color}{self.info['gpu']}{Colors.RESET}",
            "",
            f"{Colors.RED}██{Colors.GREEN}██{Colors.YELLOW}██{Colors.BLUE}██{Colors.MAGENTA}██{Colors.CYAN}██{Colors.WHITE}██{Colors.RESET}"
        ]
        
        # Calculate the width needed for ASCII art (actual character width, not display width)
        ascii_width = max(len(line) for line in ascii_art) if ascii_art else 0
        padding = 4  # Space between ASCII art and info
        
        # Display ASCII art and info side by side
        max_lines = max(len(ascii_art), len(info_lines))
        
        for i in range(max_lines):
            ascii_line = ascii_art[i] if i < len(ascii_art) else ""
            info_line = info_lines[i] if i < len(info_lines) else ""
            
            # Color the ASCII art
            colored_ascii = f"{primary_color}{ascii_line}{Colors.RESET}" if ascii_line else ""
            
            # Calculate padding needed (account for the actual character length, not display length)
            spaces_needed = ascii_width - len(ascii_line) + padding
            
            # Print with proper spacing
            print(f"{colored_ascii}{' ' * spaces_needed}{info_line}")

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("PyFetch - Cross-platform system information tool")
        print("Usage: python3 pyfetch.py")
        print("Compatible with Linux, macOS, BSD, and other Unix-like systems")
        return
    
    try:
        system_info = SystemInfo()
        system_info.display()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()