import customtkinter as ctk
import threading
import time
import re
import csv
import json
import glob
import os
import datetime
from PIL import Image
from customtkinter import CTkImage
from tkinter import filedialog, messagebox
from wifi_scanner import get_wifi_networks

# ---------- SETTINGS ----------

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

FONT_HEADER = ("Consolas", 24, "bold")
FONT_BODY = ("Consolas", 14)
NEON_GREEN = "#39FF14"
DARK_BG = "#050505"
HISTORY_DIR = "./scan_history"

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        import sys
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_last_scan_data():
    """ Fetch the most recent historical scan data """
    if not os.path.exists(HISTORY_DIR):
        os.makedirs(HISTORY_DIR)
        return None
    files = glob.glob(os.path.join(HISTORY_DIR, "scan_*.json"))
    if not files:
        return None
    # Sort files alphabetically to get the latest by timestamp format
    files.sort()
    latest_file = files[-1]
    try:
        with open(latest_file, "r") as f:
            data = json.load(f)
            return data.get("networks", {})
    except Exception as e:
        print("Error reading historical scan file:", e)
        return None

def save_scan_data(networks):
    """ Save scan results to history """
    if not os.path.exists(HISTORY_DIR):
        os.makedirs(HISTORY_DIR)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(HISTORY_DIR, f"scan_{timestamp}.json")
    try:
        with open(filename, "w") as f:
            json.dump({
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "networks": networks
            }, f, indent=4)
    except Exception as e:
        print("Error saving scan details:", e)

class HackerUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Wi-Fi Recon & Analysis Dashboard")
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
        self.minsize(1024, 768)
        self.resizable(True, True)

        # State vars
        self.current_networks = {}
        self.last_networks = None
        self.scan_results_cache = None

        # Escape closes app
        self.bind("<Escape>", lambda e: self.destroy())

        self.container = ctk.CTkFrame(self, fg_color=DARK_BG)
        self.container.pack(fill="both", expand=True)

        self.show_intro()

    def show_intro(self):
        self.clear_frame()

        # Background image
        bg_path = get_resource_path("hacker_bg.jpg")
        try:
            bg_raw = Image.open(bg_path).resize(
                (self.winfo_screenwidth(), self.winfo_screenheight()))
            bg_img = CTkImage(light_image=bg_raw, dark_image=bg_raw,
                              size=(self.winfo_screenwidth(), self.winfo_screenheight()))
            bg_label = ctk.CTkLabel(self.container, image=bg_img, text="")
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            print("Background image load failed:", e)

        # Neon label
        self.type_label = ctk.CTkLabel(self.container, text="", font=FONT_HEADER,
                                       text_color=NEON_GREEN, fg_color="transparent")
        self.type_label.place(relx=0.5, rely=0.3, anchor="center")

        # Start Button
        self.start_button = ctk.CTkButton(
            self.container,
            text="▶ START SCAN",
            command=self.start_loading,
            font=("Consolas", 18, "bold"),
            width=220,
            height=55,
            fg_color="#08f7fe",
            hover_color="#01d8c2",
            text_color="black",
            corner_radius=20
        )
        self.start_button.place(relx=0.5, rely=0.5, anchor="center")

        self.animate_typing("Initializing radio frequency analysis...")

    def animate_typing(self, text):
        def _type():
            typed = ""
            for char in text:
                typed += char
                if hasattr(self, "type_label") and self.type_label.winfo_exists():
                    self.type_label.configure(text=typed)
                    self.update()
                time.sleep(0.04)
        threading.Thread(target=_type, daemon=True).start()

    def start_loading(self):
        self.clear_frame()

        # Terminal style scanning screen
        self.loading_frame = ctk.CTkFrame(self.container, fg_color="#020202")
        self.loading_frame.pack(fill="both", expand=True)

        loading_title = ctk.CTkLabel(
            self.loading_frame, 
            text="⚡ INITIALIZING WIRELESS RECONNAISSANCE ⚡", 
            font=("Consolas", 18, "bold"), 
            text_color=NEON_GREEN
        )
        loading_title.pack(pady=(80, 20))

        self.terminal_box = ctk.CTkTextbox(
            self.loading_frame, 
            font=FONT_BODY, 
            text_color=NEON_GREEN, 
            fg_color="black", 
            border_color="#39FF14", 
            border_width=1, 
            width=700, 
            height=300
        )
        self.terminal_box.pack(pady=20)
        
        self.terminal_box.insert("end", "[*] Activating RF monitoring module...\n")
        self.terminal_box.configure(state="disabled")

        self.terminal_logs = [
            "[*] Scanning wireless frequencies...",
            "[*] Sniffing beacon frames...",
            "[*] Extracting SSIDs and BSSIDs...",
            "[*] Decoding security capabilities (WPA/WPA2/WPA3)...",
            "[*] Estimating signal RSSI values...",
            "[*] Performing channel congestion analysis...",
            "[*] Resolving historical scan differences...",
            "[*] Compilation complete. Rendering dashboard."
        ]
        self.log_index = 0
        self.scan_results_cache = None
        
        # Start scanning in background thread
        threading.Thread(target=self.run_background_scan, daemon=True).start()
        self.update_loading_terminal()

    def update_loading_terminal(self):
        if not hasattr(self, "terminal_box") or not self.terminal_box.winfo_exists():
            return
            
        if self.log_index < len(self.terminal_logs):
            self.terminal_box.configure(state="normal")
            self.terminal_box.insert("end", f"{self.terminal_logs[self.log_index]}\n")
            self.terminal_box.see("end")
            self.terminal_box.configure(state="disabled")
            self.log_index += 1
            self.after(300, self.update_loading_terminal)
        else:
            if self.scan_results_cache is not None:
                self.show_results(self.scan_results_cache)
            else:
                self.terminal_box.configure(state="normal")
                self.terminal_box.insert("end", "[*] Waiting for wireless hardware response...\n")
                self.terminal_box.see("end")
                self.terminal_box.configure(state="disabled")
                self.after(200, self.update_loading_terminal)

    def run_background_scan(self):
        try:
            self.scan_results_cache = get_wifi_networks()
        except Exception as e:
            print("Scanning failed:", e)
            self.scan_results_cache = {}

    def parse_signal_strength(self, signal_str):
        if not signal_str or not isinstance(signal_str, str):
            return 0, "Weak"
        
        match = re.search(r"(-?\d+)", signal_str)
        if not match:
            return 0, "Weak"
        
        val = int(match.group(1))
        if "dBm" in signal_str:
            # RSSI range: -100 dBm (weak) to -30 dBm (strong)
            score = max(0, min(100, int((val + 100) * 10 / 7)))
            if val >= -60:
                quality = "Excellent"
            elif val >= -80:
                quality = "Good"
            else:
                quality = "Weak"
            return score, quality
        elif "%" in signal_str or val >= 0:
            # Percentage: 0 to 100%
            score = max(0, min(100, val))
            if score >= 75:
                quality = "Excellent"
            elif score >= 35:
                quality = "Good"
            else:
                quality = "Weak"
            return score, quality
        else:
            # Negative number fallback
            score = max(0, min(100, int((val + 100) * 10 / 7)))
            if val >= -60:
                quality = "Excellent"
            elif val >= -80:
                quality = "Good"
            else:
                quality = "Weak"
            return score, quality

    def show_results(self, networks):
        self.clear_frame()
        
        self.current_networks = networks
        self.last_networks = get_last_scan_data()
        
        # Save current scan to history
        save_scan_data(networks)
        
        # Dashboard frames
        self.dashboard_frame = ctk.CTkFrame(self.container, fg_color=DARK_BG)
        self.dashboard_frame.pack(fill="both", expand=True)
        
        # Left Panel (Sidebar)
        self.left_panel = ctk.CTkFrame(self.dashboard_frame, width=320, fg_color="#0e0e12", corner_radius=0)
        self.left_panel.pack(side="left", fill="y")
        self.left_panel.pack_propagate(False)
        
        # Right Panel (Main Dashboard)
        self.right_panel = ctk.CTkFrame(self.dashboard_frame, fg_color=DARK_BG, corner_radius=0)
        self.right_panel.pack(side="right", fill="both", expand=True)
        
        self.setup_left_panel()
        self.setup_right_panel()
        self.render_networks()

    def setup_left_panel(self):
        # Header/Branding
        logo_label = ctk.CTkLabel(self.left_panel, text="☣ WI-FI RECON STATION ☣", font=("Consolas", 15, "bold"), text_color=NEON_GREEN)
        logo_label.pack(pady=20, padx=10)
        
        # Action button
        self.rescan_btn = ctk.CTkButton(
            self.left_panel, 
            text="⚡ RESCAN SYSTEM", 
            command=self.start_loading, 
            font=("Consolas", 14, "bold"), 
            fg_color="#00ffcc", 
            hover_color="#00b386", 
            text_color="black", 
            height=40,
            corner_radius=8
        )
        self.rescan_btn.pack(pady=10, padx=20, fill="x")
        
        # Security statistics panel
        sec_frame = ctk.CTkFrame(self.left_panel, fg_color="#121216", border_width=1, border_color="#1f1f28", corner_radius=8)
        sec_frame.pack(pady=10, padx=15, fill="x")
        
        sec_title = ctk.CTkLabel(sec_frame, text="[ SECURITY ASSESSMENT ]", font=("Consolas", 12, "bold"), text_color="#00ffcc")
        sec_title.pack(pady=5)
        
        sec_counts = {"WPA3": 0, "WPA2": 0, "Open": 0, "Other": 0}
        for ssid, details in self.current_networks.items():
            sec = details.get("Security", "Open")
            if sec == "WPA3":
                sec_counts["WPA3"] += 1
            elif sec == "WPA2":
                sec_counts["WPA2"] += 1
            elif sec == "Open":
                sec_counts["Open"] += 1
            else:
                sec_counts["Other"] += 1
                
        wpa3_lbl = ctk.CTkLabel(sec_frame, text=f"WPA3 Networks : {sec_counts['WPA3']}", font=("Consolas", 12), text_color="#39FF14")
        wpa3_lbl.pack(anchor="w", padx=15, pady=2)
        wpa2_lbl = ctk.CTkLabel(sec_frame, text=f"WPA2 Networks : {sec_counts['WPA2']}", font=("Consolas", 12), text_color="#00ffcc")
        wpa2_lbl.pack(anchor="w", padx=15, pady=2)
        open_lbl = ctk.CTkLabel(sec_frame, text=f"Open Networks : {sec_counts['Open']}", font=("Consolas", 12), text_color="#FF3131" if sec_counts["Open"] > 0 else "white")
        open_lbl.pack(anchor="w", padx=15, pady=2)
        
        # Alert if open networks are detected
        if sec_counts["Open"] > 0:
            self.alert_label = ctk.CTkLabel(sec_frame, text="⚠️ WARNING: OPEN NETWORKS DETECTED!", font=("Consolas", 10, "bold"), text_color="#FF3131")
            self.alert_label.pack(pady=8, padx=10)
            self.alert_blink_state = True
            self.blink_alert()
            
        # Channel Analyzer Panel
        chan_frame = ctk.CTkFrame(self.left_panel, fg_color="#121216", border_width=1, border_color="#1f1f28", corner_radius=8)
        chan_frame.pack(pady=10, padx=15, fill="x")
        
        chan_title = ctk.CTkLabel(chan_frame, text="[ CHANNEL ANALYSIS ]", font=("Consolas", 12, "bold"), text_color="#00ffcc")
        chan_title.pack(pady=5)
        
        chan_counts = {}
        for ssid, details in self.current_networks.items():
            ch = details.get("Channel", "N/A")
            if ch != "N/A":
                chan_counts[ch] = chan_counts.get(ch, 0) + 1
                
        sorted_channels = sorted(chan_counts.items(), key=lambda x: x[1], reverse=True)
        
        chan_list_str = ""
        if not sorted_channels:
            chan_list_str = "No active channels found.\n"
        else:
            for ch, count in sorted_channels[:3]:
                chan_list_str += f"Channel {ch} : {count} network{'s' if count > 1 else ''}\n"
                
        chan_lbl = ctk.CTkLabel(chan_frame, text=chan_list_str.strip(), font=("Consolas", 12), justify="left")
        chan_lbl.pack(padx=15, pady=5)
        
        # Recommended Channel Logic (Standard non-overlapping: 1, 6, 11)
        c1 = chan_counts.get(1, 0)
        c6 = chan_counts.get(6, 0)
        c11 = chan_counts.get(11, 0)
        
        rec_24 = 11
        min_count = c11
        if c1 < min_count:
            rec_24 = 1
            min_count = c1
        if c6 < min_count:
            rec_24 = 6
            min_count = c6
            
        rec_lbl = ctk.CTkLabel(chan_frame, text=f"Recommended 2.4G : Ch {rec_24}", font=("Consolas", 12, "bold"), text_color="#39FF14")
        rec_lbl.pack(pady=(5, 2))
        
        # Suggest 5G channel if 5G detected
        five_g_chans = [ch for ch in chan_counts.keys() if isinstance(ch, int) and ch >= 36]
        if five_g_chans:
            rec_5 = min(five_g_chans, key=lambda ch: chan_counts.get(ch, 0))
            rec_5_lbl = ctk.CTkLabel(chan_frame, text=f"Recommended 5G  : Ch {rec_5}", font=("Consolas", 12, "bold"), text_color="#39FF14")
            rec_5_lbl.pack(pady=(0, 8))
        else:
            rec_5_lbl = ctk.CTkLabel(chan_frame, text="Recommended 5G  : Ch 36 (Default)", font=("Consolas", 12, "bold"), text_color="#39FF14")
            rec_5_lbl.pack(pady=(0, 8))
            
        # Data Export Panel
        exp_frame = ctk.CTkFrame(self.left_panel, fg_color="#121216", border_width=1, border_color="#1f1f28", corner_radius=8)
        exp_frame.pack(pady=10, padx=15, fill="x")
        
        exp_title = ctk.CTkLabel(exp_frame, text="[ DATA EXPORT ]", font=("Consolas", 12, "bold"), text_color="#00ffcc")
        exp_title.pack(pady=5)
        
        csv_btn = ctk.CTkButton(
            exp_frame, 
            text="📥 EXPORT CSV", 
            command=self.export_csv, 
            font=("Consolas", 11, "bold"), 
            fg_color="#1f1f28", 
            hover_color="#2d2d3d", 
            text_color="#00ffcc",
            border_width=1,
            border_color="#00ffcc",
            height=30
        )
        csv_btn.pack(pady=5, padx=20, fill="x")
        
        txt_btn = ctk.CTkButton(
            exp_frame, 
            text="📥 EXPORT TXT", 
            command=self.export_txt, 
            font=("Consolas", 11, "bold"), 
            fg_color="#1f1f28", 
            hover_color="#2d2d3d", 
            text_color="#00ffcc",
            border_width=1,
            border_color="#00ffcc",
            height=30
        )
        txt_btn.pack(pady=(5, 10), padx=20, fill="x")
        
        # Footer
        footer = ctk.CTkLabel(self.left_panel, text="ESC to close terminal", font=("Consolas", 10), text_color="#555")
        footer.pack(side="bottom", pady=10)

    def blink_alert(self):
        if hasattr(self, "alert_label") and self.alert_label.winfo_exists():
            self.alert_blink_state = not self.alert_blink_state
            color = "#FF3131" if self.alert_blink_state else "#0e0e12"
            self.alert_label.configure(text_color=color)
            self.after(500, self.blink_alert)

    def setup_right_panel(self):
        # 1. Statistics Cards
        stats_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        stats_frame.pack(pady=(15, 10), padx=20, fill="x")
        
        total = len(self.current_networks)
        strong = 0
        medium = 0
        weak = 0
        
        for ssid, details in self.current_networks.items():
            _, qual = self.parse_signal_strength(details.get("Signal", "N/A"))
            if qual == "Excellent":
                strong += 1
            elif qual == "Good":
                medium += 1
            else:
                weak += 1
                
        new_networks_count = 0
        if self.last_networks is not None:
            for ssid in self.current_networks.keys():
                if ssid not in self.last_networks:
                    new_networks_count += 1
                    
        def create_stat_card(parent, value, label, neon_color):
            card = ctk.CTkFrame(parent, fg_color="#0e0e12", border_width=1, border_color="#1f1f28", height=70)
            card.pack(side="left", fill="both", expand=True, padx=5)
            card.pack_propagate(False)
            
            num_lbl = ctk.CTkLabel(card, text=str(value), font=("Consolas", 22, "bold"), text_color=neon_color)
            num_lbl.pack(pady=(8, 2))
            
            lbl = ctk.CTkLabel(card, text=label, font=("Consolas", 10), text_color="#aaa")
            lbl.pack()
            
        create_stat_card(stats_frame, total, "TOTAL NETWORKS", "#00ffcc")
        create_stat_card(stats_frame, strong, "STRONG SIGNALS", "#39FF14")
        create_stat_card(stats_frame, medium, "MEDIUM SIGNALS", "#FFD700")
        create_stat_card(stats_frame, weak, "WEAK SIGNALS", "#FF3131")
        
        hist_label = f"NEW FOUND (+{new_networks_count})" if self.last_networks is not None else "NEW FOUND"
        create_stat_card(stats_frame, new_networks_count, hist_label, "#FF00FF")
        
        # 2. Historical comparison sub-header
        if self.last_networks is not None:
            comparison_frame = ctk.CTkFrame(self.right_panel, fg_color="#121216", height=30)
            comparison_frame.pack(pady=5, padx=25, fill="x")
            
            last_total = len(self.last_networks)
            comp_text = f"📊 HISTORICAL REPORT: Last Scan ({last_total} networks) vs Current Scan ({total} networks). New: {new_networks_count} | Diff: {total - last_total:+} networks."
            comp_lbl = ctk.CTkLabel(comparison_frame, text=comp_text, font=("Consolas", 11), text_color="#00ffcc")
            comp_lbl.pack(pady=2, padx=10, side="left")
            
        # 3. Controls Row (Search and Sort)
        ctrl_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        ctrl_frame.pack(pady=10, padx=20, fill="x")
        
        self.search_entry = ctk.CTkEntry(
            ctrl_frame, 
            placeholder_text="🔍 Search SSID...", 
            font=FONT_BODY,
            fg_color="#0e0e12", 
            border_color="#1f1f28",
            text_color="white",
            height=35
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(5, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self.render_networks())
        
        sort_lbl = ctk.CTkLabel(ctrl_frame, text="Sort by:", font=("Consolas", 12), text_color="white")
        sort_lbl.pack(side="left", padx=5)
        
        self.sort_combo = ctk.CTkComboBox(
            ctrl_frame,
            values=[
                "Signal: Strongest First",
                "Signal: Weakest First",
                "SSID: A-Z",
                "SSID: Z-A",
                "Channel: Lowest First"
            ],
            command=lambda v: self.render_networks(),
            font=("Consolas", 12),
            fg_color="#0e0e12",
            border_color="#1f1f28",
            button_color="#1f1f28",
            button_hover_color="#2d2d3d",
            dropdown_fg_color="#0e0e12",
            dropdown_text_color="white",
            dropdown_hover_color="#1f1f28",
            height=35,
            width=220
        )
        self.sort_combo.pack(side="left", padx=5)
        self.sort_combo.set("Signal: Strongest First")
        
        # 4. Scrollable Container
        self.networks_scroll_frame = ctk.CTkScrollableFrame(
            self.right_panel, 
            fg_color="#050505", 
            scrollbar_button_color="#1f1f28",
            scrollbar_button_hover_color="#2d2d3d"
        )
        self.networks_scroll_frame.pack(fill="both", expand=True, padx=20, pady=(5, 15))

    def get_sorted_filtered_networks(self):
        query = self.search_entry.get().strip().lower()
        filtered = []
        for ssid, details in self.current_networks.items():
            if query and query not in ssid.lower():
                continue
            filtered.append((ssid, details))
            
        sort_val = self.sort_combo.get()
        if sort_val == "Signal: Strongest First":
            filtered.sort(key=lambda x: self.parse_signal_strength(x[1].get("Signal", "N/A"))[0], reverse=True)
        elif sort_val == "Signal: Weakest First":
            filtered.sort(key=lambda x: self.parse_signal_strength(x[1].get("Signal", "N/A"))[0])
        elif sort_val == "SSID: A-Z":
            filtered.sort(key=lambda x: x[0].lower())
        elif sort_val == "SSID: Z-A":
            filtered.sort(key=lambda x: x[0].lower(), reverse=True)
        elif sort_val == "Channel: Lowest First":
            def channel_key(x):
                ch = x[1].get("Channel", "N/A")
                try:
                    return int(ch)
                except ValueError:
                    return 9999
            filtered.sort(key=channel_key)
            
        return filtered

    def render_networks(self):
        for widget in self.networks_scroll_frame.winfo_children():
            widget.destroy()
            
        sorted_filtered = self.get_sorted_filtered_networks()
        
        if not sorted_filtered:
            no_results_lbl = ctk.CTkLabel(
                self.networks_scroll_frame, 
                text="No networks match the current filters.",
                font=FONT_BODY,
                text_color="#555"
            )
            no_results_lbl.pack(pady=40)
            return
            
        for ssid, details in sorted_filtered:
            is_new = False
            if self.last_networks is not None and ssid not in self.last_networks:
                is_new = True
                
            sig_str = details.get("Signal", "N/A")
            score, quality = self.parse_signal_strength(sig_str)
            
            card = ctk.CTkFrame(
                self.networks_scroll_frame, 
                fg_color="#0e0e12", 
                border_width=1, 
                border_color="#1f1f28", 
                corner_radius=8
            )
            card.pack(fill="x", pady=5, padx=5)
            
            title_row = ctk.CTkFrame(card, fg_color="transparent")
            title_row.pack(fill="x", padx=15, pady=(8, 4))
            
            ssid_lbl = ctk.CTkLabel(title_row, text=ssid, font=("Consolas", 15, "bold"), text_color="white")
            ssid_lbl.pack(side="left")
            
            sec = details.get("Security", "Open")
            if sec == "Open":
                open_badge = ctk.CTkLabel(
                    title_row, 
                    text=" UNSECURE / OPEN ", 
                    font=("Consolas", 10, "bold"), 
                    text_color="black", 
                    fg_color="#FF3131",
                    corner_radius=4
                )
                open_badge.pack(side="left", padx=8)
            elif sec == "WPA3":
                secure_badge = ctk.CTkLabel(
                    title_row, 
                    text=" WPA3 SECURE ", 
                    font=("Consolas", 10, "bold"), 
                    text_color="black", 
                    fg_color="#39FF14",
                    corner_radius=4
                )
                secure_badge.pack(side="left", padx=8)
                
            if is_new:
                new_badge = ctk.CTkLabel(
                    title_row, 
                    text=" NEW ", 
                    font=("Consolas", 10, "bold"), 
                    text_color="black", 
                    fg_color="#FF00FF",
                    corner_radius=4
                )
                new_badge.pack(side="left", padx=2)
                
            details_row = ctk.CTkFrame(card, fg_color="transparent")
            details_row.pack(fill="x", padx=15, pady=(2, 8))
            
            if quality == "Excellent":
                prog_color = "#39FF14"
            elif quality == "Good":
                prog_color = "#FFD700"
            else:
                prog_color = "#FF3131"
                
            progress_container = ctk.CTkFrame(details_row, fg_color="transparent")
            progress_container.pack(side="left", fill="y")
            
            prog_bar = ctk.CTkProgressBar(
                progress_container,
                width=120,
                height=8,
                progress_color=prog_color,
                fg_color="#222"
            )
            prog_bar.pack(side="left", pady=8)
            prog_bar.set(score / 100.0)
            
            qual_lbl = ctk.CTkLabel(
                progress_container, 
                text=f"{quality} ({sig_str})", 
                font=("Consolas", 11, "bold"), 
                text_color=prog_color
            )
            qual_lbl.pack(side="left", padx=8)
            
            chan = details.get("Channel", "N/A")
            tech_text = f"Channel: {chan}  |  Security: {sec}"
            tech_lbl = ctk.CTkLabel(details_row, text=tech_text, font=("Consolas", 11), text_color="#aaa")
            tech_lbl.pack(side="right")

    def export_csv(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Scanned Networks as CSV"
        )
        if not file_path:
            return
            
        try:
            with open(file_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["SSID", "Channel", "Security", "Signal", "Quality", "Timestamp"])
                
                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                for ssid, details in self.current_networks.items():
                    sig_str = details.get("Signal", "N/A")
                    _, quality = self.parse_signal_strength(sig_str)
                    writer.writerow([
                        ssid,
                        details.get("Channel", "N/A"),
                        details.get("Security", "Open"),
                        sig_str,
                        quality,
                        now_str
                    ])
            self.show_toast("Export Successful (CSV)")
        except Exception as e:
            self.show_toast(f"Export Failed: {str(e)}", is_error=True)
            
    def export_txt(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Export Scanned Networks as Text"
        )
        if not file_path:
            return
            
        try:
            with open(file_path, mode="w", encoding="utf-8") as f:
                f.write("=" * 50 + "\n")
                f.write("          WI-FI RECON TERMINAL REPORT\n")
                f.write(f"  Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                
                for ssid, details in self.current_networks.items():
                    sig_str = details.get("Signal", "N/A")
                    _, quality = self.parse_signal_strength(sig_str)
                    f.write(f"SSID: {ssid}\n")
                    f.write(f"Channel: {details.get('Channel', 'N/A')}\n")
                    f.write(f"Security: {details.get('Security', 'Open')}\n")
                    f.write(f"Signal: {sig_str} ({quality})\n")
                    f.write("-" * 30 + "\n")
            self.show_toast("Export Successful (TXT)")
        except Exception as e:
            self.show_toast(f"Export Failed: {str(e)}", is_error=True)

    def show_toast(self, message, is_error=False):
        if is_error:
            messagebox.showerror("Error", message)
        else:
            messagebox.showinfo("Wi-Fi Analyzer", message)

    def clear_frame(self):
        for widget in self.container.winfo_children():
            widget.destroy()

if __name__ == '__main__':
    app = HackerUI()
    app.mainloop()
