# 🌑 VEILSTREAM TELEMETRY SUITE
**v5.0.0 | Premium-Grade Remote Telemetry & Payload Management Framework**

`Python 3.9+` | `Windows / Linux` | `Production Ready` | `Private Use`

---

## 📖 OVERVIEW
VeilStream is a next-generation, single-file telemetry and payload management framework engineered for maximum operational security, stealth, and efficiency. Built from the ground up with polymorphic generation, AES-CBC encrypted C2 communications, and zero-disk-artifact execution, VeilStream delivers enterprise-grade remote monitoring capabilities in a compact, undetectable package. Designed for authorized security assessments, internal infrastructure monitoring, and advanced red-team operations.

---

## 🔥 KEY FEATURES
🔹 **Polymorphic Payload Engine** - Generates uniquely obfuscated payloads per build with randomized control flow, dead-code injection, and dynamic string encryption. Every compilation produces a cryptographically distinct binary.  
🔹 **Zero-Trace Execution** - All telemetry is buffered in-memory and transmitted via encrypted HTTP POST. No local logs, no temp files, zero forensic footprint on the target system.  
🔹 **Advanced C2 Dashboard** - Cross-platform GUI with real-time host mapping, geolocation tracking, live keylog streaming, and credential capture visualization.  
🔹 **Dual Persistence Layer** - Automatic Registry + Scheduled Task deployment with fallback mechanisms. Survives reboots, standard cleanup routines, and user profile resets.  
🔹 **Anti-Analysis & Evasion** - Integrated debugger detection, VM/sandbox timing checks, console suppression, and runtime environment validation.  
🔹 **Network Credential Interception** - Passive packet inspection targeting authentication payloads across HTTP streams with intelligent pattern matching and payload truncation.  
🔹 **Automated Delivery System** - Built-in HTTP dropper generator for silent payload staging and remote execution without manual deployment.  
🔹 **Cross-Platform Host** - C2 server and dashboard run natively on Windows & Linux. Payload targets Windows with Linux compatibility layer ready.  

---

## 🏗️ ARCHITECTURE
```
📦 VEILSTREAM SUITE
├── 🖥️ unified_suite.py          # All-in-one C2 Server + GUI Dashboard + Builder
├── 📜 payload_template.py       # Core agent logic (auto-injected by builder)
├── 🌐 c2_delivery_endpoint      # Built-in HTTP payload staging server
└── 📊 telemetry_core.db         # SQLite backend for host & log management
```

---

## ⚙️ REQUIREMENTS
- Python 3.9 or higher
- Operating System: Windows 10/11 (Target) | Windows/Linux (Host)
- Administrator/Root privileges for packet capture and persistence deployment
- Python Dependencies: `pynput`, `scapy`, `pycryptodome`, `pyinstaller`, `tkinter`

---

## 📦 INSTALLATION & SETUP
1. Clone or download the repository to your control machine.
2. Install required Python packages:
   ```bash
   pip install pynput scapy pycryptodome pyinstaller
   ```
3. Launch the unified dashboard:
   ```bash
   python unified_suite.py
   ```
4. The GUI will auto-initialize the encrypted C2 listener on port `8443` and the delivery endpoint on port `8080`.

---

## 📖 USAGE GUIDE

### 1. Generate Payload
- Navigate to the **Payload Builder** tab in the dashboard.
- Enter your public C2 IP/Domain, set a disguise name (e.g., `win_svc_helper`), and specify an output path.
- Click **Generate Payload**. The builder applies polymorphic string encryption, junk code injection, and control-flow randomization before writing the final script.

### 2. Compile to Executable
- Open a terminal in the output directory.
- Run the PyInstaller command:
  ```bash
  pyinstaller --onefile --noconsole --name <disguise_name> output_payload.py
  ```
- The compiled binary will be located in the `dist/` folder.

### 3. Deploy & Monitor
- Use the **Automated Delivery** tab to generate a lightweight dropper script that fetches the compiled payload from the C2 delivery endpoint and executes it silently.
- Monitor live telemetry in the **Hosts & Telemetry** tab. Filter by HWID, export logs, or track geolocation data in real-time. All data is stored locally in the SQLite database with WAL journaling for performance.

---

## 🛡️ OPERATIONAL SECURITY NOTES
- All network traffic is encrypted using AES-CBC with per-session keys. No plaintext credentials or keystrokes are stored locally on target or host systems.
- Payloads are designed to run silently in the background with no visible UI, console output, or system tray icons.
- Packet capture requires administrative/root privileges. Ensure target environment permissions are configured accordingly.
- The polymorphic engine ensures each generated binary has a unique cryptographic signature, defeating static hash-based detection.
- In-memory buffers are cleared immediately after successful transmission. Zero disk artifacts are left on the target.

---

## ⚠️ DISCLAIMER
This framework is provided strictly for authorized security assessments, internal telemetry monitoring, and controlled red-team engagements. The developers assume no liability for misuse, unauthorized deployment, or violation of applicable laws. Always ensure you have explicit, documented permission before deploying telemetry agents on any system.

---

## 📜 LICENSE
Private Use Only. Redistribution, commercial licensing, or unauthorized modification is strictly prohibited. All rights reserved by the VeilStream Core Dev Team.
