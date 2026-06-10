
# 🌑 VEILSTREAM TELEMETRY SUITE
**Fully Automated C2 Framework & Remote Telemetry Platform**

`Python 3.11+` | `Windows / Linux` | `Zero-Terminal GUI` | `Production Ready`

---

## 📖 OVERVIEW
VeilStream is a next-generation, GUI-driven telemetry and payload management framework engineered for operational security, stealth, and complete automation. The entire lifecycle—from payload generation and compilation to deployment and live monitoring—is handled within a single, modern interface. **No terminal commands, manual compilation, or external tools required.**

Designed for authorized security assessments, internal infrastructure monitoring, and advanced red-team operations.

---

## 🔥 KEY FEATURES
🔹 **Zero-Terminal Automated Pipeline** - Configure, compile, stage, and deploy entirely through the GUI. PyInstaller runs silently in the background.  
🔹 **Polymorphic Payload Engine** - Generates cryptographically distinct binaries per build via randomized control flow, dead-code injection, and dynamic string encryption.  
🔹 **Built-in Compilation & Staging** - One-click build process automatically compiles the agent and hosts it on an integrated HTTP delivery endpoint.  
🔹 **One-Click Deployment** - Generates a silent PowerShell one-liner, auto-copies it to your clipboard, and requires zero manual configuration on the target.  
🔹 **Live Telemetry Dashboard** - Auto-refreshing host table, real-time log streaming, and decrypted payload viewing. Updates every 3 seconds without manual intervention.  
🔹 **AES-CBC Encrypted C2** - Per-session keys, randomized beacon jitter (45–120s), and memory-only buffer handling. Zero plaintext transmission.  
🔹 **Advanced Evasion** - Integrated debugger detection, VM/sandbox timing checks, console suppression, and silent background execution.  
🔹 **Dual Persistence Layer** - Automatic Registry + Scheduled Task deployment. Survives reboots and standard cleanup routines.  
🔹 **Passive Telemetry Collection** - Background keylogger (flushes at 40+ keys) and HTTP credential interceptor targeting authentication payloads.  
🔹 **Compact Purple-Red UI** - Dense, SOC-style layout with zero dead space, live terminal feed, and custom icon support.

---

## 🏗️ ARCHITECTURE
```
📦 VEILSTREAM SUITE
├── 🖥️ unified_suite.py          # All-in-one GUI, C2 Server, Builder & Compiler
├── 📊 telemetry_core.db         # SQLite backend with WAL journaling
└── 🌐 Built-in HTTP Delivery    # Auto-hosts compiled payloads on port 8080
```

---

## ⚙️ REQUIREMENTS
- Python 3.11 or higher
- Operating System: Windows 10/11 (Target) | Windows/Linux (Host)
- Administrator/Root privileges for packet capture and persistence deployment
- Python Dependencies: `customtkinter`, `pycryptodome`, `pyinstaller`, `pynput`, `scapy`

---

## 📦 INSTALLATION & SETUP
1. Clone or download the repository to your control machine.
2. Install required packages:
   ```bash
   pip install customtkinter pycryptodome pyinstaller pynput scapy
   ```
3. Launch the automated dashboard:
   ```bash
   python unified_suite.py
   ```
4. The GUI automatically initializes the encrypted C2 listener on port `8443` and the delivery endpoint on port `8080`.

---

## 📖 USAGE GUIDE (STEP-BY-STEP)

### 1. CONFIGURE & BUILD
- Open the **OPERATIONS** tab.
- Enter your host machine's reachable IP in `C2 IP / Host`.
- Set a `Disguise Name` (e.g., `win_svc_helper`).
- Click **1. BUILD & COMPILE**.
- The GUI handles polymorphic obfuscation, writes the script, and runs PyInstaller in a background thread. Wait for `[SUCCESS]` in the log panel.

### 2. DEPLOY TO TARGET
- Once compilation finishes, click **2. GENERATE DEPLOY CMD**.
- A silent PowerShell one-liner is automatically generated and copied to your clipboard.
- Transfer the command to the target machine and execute it in an elevated CMD or PowerShell window.
- The target fetches the compiled agent, executes it hidden, and establishes a secure beacon.

### 3. MONITOR TELEMETRY
- Switch to the **TELEMETRY** tab.
- The host table auto-refreshes every 3 seconds. Click any connected host to view live logs.
- View decrypted keystrokes, captured HTTP credentials, and heartbeat status in real-time.
- No manual refresh or database queries required.

---

## 🛡️ OPERATIONAL SECURITY NOTES
- **Zero Local Artifacts:** All telemetry is buffered in-memory and cleared immediately after encrypted transmission. No logs, configs, or temp files are created by the agent.
- **Encrypted Communications:** All C2 traffic uses AES-CBC with per-session keys. Payloads are never transmitted in plaintext.
- **Stealth Execution:** Console is suppressed instantly. No UI, tray icons, or visible processes. Runs under current user context.
- **Polymorphic Builds:** Every compilation produces a unique cryptographic signature, defeating static hash-based detection.
- **Network Requirements:** Outbound TCP to C2 port `8443`. Passive packet inspection requires administrative privileges on the target.

---

## 📜 CHANGELOG v6.1.0

🎨 Complete UI overhaul: Compact purple-red gradient theme, dense SOC-style layout
🖼️ Custom icon support: Auto-applies veilstream.ico to window & compiled binaries
📉 Reduced footprint: Tightened padding, smaller fonts, optimized treeview rows, zero dead space

---

## ⚠️ DISCLAIMER
This framework is provided strictly for authorized security assessments, internal telemetry monitoring, and controlled red-team engagements. The developers assume no liability for misuse, unauthorized deployment, or violation of applicable laws. Always ensure you have explicit, documented permission before deploying telemetry agents on any system.

---

## 📜 LICENSE
Private Use Only. Redistribution, commercial licensing, or unauthorized modification is strictly prohibited. All rights reserved by the VeilStream Core Dev Team.
