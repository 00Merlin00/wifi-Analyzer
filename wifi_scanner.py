import subprocess
import re
import platform

def standardize_security(sec_str):
    if not sec_str or not isinstance(sec_str, str):
        return "Open"
    sec_strip = sec_str.strip()
    if sec_strip == "" or sec_strip == "N/A" or sec_strip == "None":
        return "Open"
    sec_lower = sec_strip.lower()
    if sec_lower in ["--", "open", "none", "no security", "wep", "wep40", "wep104"]:
        if "wep" in sec_lower:
            return "WEP"
        return "Open"
    elif "wpa3" in sec_lower:
        return "WPA3"
    elif "wpa2" in sec_lower:
        return "WPA2"
    elif "wpa" in sec_lower:
        return "WPA"
    return sec_strip

def get_wifi_networks():
    networks = {}
    sys_platform = platform.system()

    if sys_platform == "Darwin":  # macOS
        result = subprocess.run(
            ['system_profiler', 'SPAirPortDataType'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.stderr:
            print("Error:", result.stderr)
            return networks

        ssid_match = re.compile(r"^\s+(.+):$")
        channel_match = re.compile(r"Channel:\s+(\d+)")
        security_match = re.compile(r"Security(?: Type)?:\s+(.+)")
        signal_match = re.compile(r"(?:Signal / Noise|RSSI|Signal Strength):\s*(-?\d+)")

        current_ssid = None
        current_info = {}

        for line in result.stdout.splitlines():
            ssid_found = ssid_match.search(line)
            if ssid_found:
                ssid = ssid_found.group(1).strip()
                if ssid in ["Software Versions", "Interfaces", "Current Network Information",
                            "Other Local Wi-Fi Networks", "awdl0", "en0"]:
                    continue

                if current_ssid:
                    current_info["Security"] = standardize_security(current_info.get("Security", "Open"))
                    unique_ssid = current_ssid
                    counter = 1
                    while unique_ssid in networks:
                        unique_ssid = f"{current_ssid} ({counter})"
                        counter += 1
                    networks[unique_ssid] = current_info

                current_ssid = ssid
                current_info = {"Channel": "N/A", "Security": "Open", "Signal": "N/A"}
                continue

            if current_ssid:
                channel_found = channel_match.search(line)
                if channel_found:
                    current_info["Channel"] = int(channel_found.group(1))
                    continue

                security_found = security_match.search(line)
                if security_found:
                    current_info["Security"] = security_found.group(1).strip()
                    continue

                signal_found = signal_match.search(line)
                if signal_found:
                    current_info["Signal"] = f"{signal_found.group(1)} dBm"

        if current_ssid:
            current_info["Security"] = standardize_security(current_info.get("Security", "Open"))
            unique_ssid = current_ssid
            counter = 1
            while unique_ssid in networks:
                unique_ssid = f"{current_ssid} ({counter})"
                counter += 1
            networks[unique_ssid] = current_info

    elif sys_platform == "Windows":  # Windows
        result = subprocess.run(
            ["netsh", "wlan", "show", "networks", "mode=bssid"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8"
        )
        if result.stderr:
            print("Error:", result.stderr)
            return networks

        ssid_match = re.compile(r"^\s*SSID\s+\d+\s+:\s(.+)$")
        channel_match = re.compile(r"^\s*Channel\s+:\s+(\d+)")
        security_match = re.compile(r"^\s*Authentication\s+:\s+(.+)$")
        signal_match = re.compile(r"^\s*Signal\s+:\s+(\d+)%")

        current_ssid = None
        current_info = {}

        for line in result.stdout.splitlines():
            ssid_found = ssid_match.search(line)
            if ssid_found:
                if current_ssid:
                    current_info["Security"] = standardize_security(current_info.get("Security", "Open"))
                    unique_ssid = current_ssid
                    counter = 1
                    while unique_ssid in networks:
                        unique_ssid = f"{current_ssid} ({counter})"
                        counter += 1
                    networks[unique_ssid] = current_info
                current_ssid = ssid_found.group(1).strip()
                current_info = {"Channel": "N/A", "Security": "Open", "Signal": "N/A"}
                continue

            if current_ssid:
                channel_found = channel_match.search(line)
                if channel_found:
                    current_info["Channel"] = int(channel_found.group(1))
                    continue

                security_found = security_match.search(line)
                if security_found:
                    current_info["Security"] = security_found.group(1).strip()
                    continue

                signal_found = signal_match.search(line)
                if signal_found:
                    current_info["Signal"] = f"{signal_found.group(1)}%"

        if current_ssid:
            current_info["Security"] = standardize_security(current_info.get("Security", "Open"))
            unique_ssid = current_ssid
            counter = 1
            while unique_ssid in networks:
                unique_ssid = f"{current_ssid} ({counter})"
                counter += 1
            networks[unique_ssid] = current_info

    elif sys_platform == "Linux":  # Linux support
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "SSID,CHAN,SIGNAL,SECURITY", "dev", "wifi"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8"
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if not line.strip():
                        continue
                    # Character-by-character split to support backslash-escaped colons
                    parts = []
                    current = []
                    escaped = False
                    for char in line:
                        if escaped:
                            current.append(char)
                            escaped = False
                        elif char == '\\':
                            escaped = True
                        elif char == ':':
                            parts.append("".join(current))
                            current = []
                        else:
                            current.append(char)
                    parts.append("".join(current))

                    if len(parts) >= 4:
                        ssid = parts[0].strip()
                        if not ssid:
                            continue  # Ignore hidden networks with empty SSIDs
                        
                        try:
                            channel = int(parts[1].strip())
                        except ValueError:
                            channel = "N/A"
                            
                        signal = f"{parts[2].strip()}%"
                        security = standardize_security(parts[3].strip())
                        
                        unique_ssid = ssid
                        counter = 1
                        while unique_ssid in networks:
                            unique_ssid = f"{ssid} ({counter})"
                            counter += 1
                        networks[unique_ssid] = {
                            "Channel": channel,
                            "Security": security,
                            "Signal": signal
                        }
            else:
                print("nmcli error:", result.stderr)
        except FileNotFoundError:
            # nmcli not available, fall back to /proc/net/wireless or empty
            print("nmcli command not found on Linux.")

    return networks
