
# 🌑 VEILSTREAM TELEMETRY SUITE v5.1.0
**Next-Gen Remote Telemetry & Payload Management Framework**

`Python 3.11+` | `Windows / Linux` | `Production Ready` | `Private Use`

---

## 📖 OVERVIEW
VeilStream v5.1.0 is a unified, single-file telemetry and payload management framework engineered for operational security, stealth, and efficiency. Featuring a completely overhauled professional-grade C2 dashboard, AES-CBC encrypted communications, polymorphic payload generation, and zero-disk-artifact execution. Designed for authorized security assessments, internal infrastructure monitoring, and advanced red-team operations.

---

## 🔥 KEY FEATURES
🔹 **Modern SOC-Style Dashboard** - Dark-themed, terminal-inspired UI with sidebar navigation, real-time log streaming, and clean data tables. Built for operational clarity, not gimmicks.  
🔹 **Polymorphic Payload Engine** - Generates uniquely obfuscated payloads per build with randomized control flow, dead-code injection, and dynamic string encryption. Every compilation produces a cryptographically distinct binary.  
🔹 **Zero-Trace Execution** - All telemetry is buffered in-memory and transmitted via encrypted HTTP POST. No local logs, no temp files, zero forensic footprint on the target system.  
🔹 **Advanced C2 Communications** - AES-CBC encrypted payloads, per-session keys, and automated heartbeat/beacon routing with randomized jitter.  
🔹 **Dual Persistence Layer** - Automatic Registry + Scheduled Task deployment with fallback mechanisms. Survives reboots, standard cleanup routines, and user profile resets.  
🔹 **Anti-Analysis & Evasion** - Integrated debugger detection, VM/sandbox timing checks, console suppression, and runtime environment validation.  
🔹 **Network Credential Interception** - Passive packet inspection targeting authentication payloads across HTTP streams with intelligent pattern matching and payload truncation.  
🔹 **Automated Delivery System** - Built-in HTTP dropper generator for silent payload staging and remote execution without manual deployment.  

---

## 🏗️ ARCHITECTURE
```
📦 VEILSTREAM SUITE v5.1.0
├── 🖥️ unified_suite.py          # All-in-one C2 Server + Modern GUI + Builder
├── 📜 payload_template.py       # Core agent logic (auto-injected by builder)
├── 🌐 c2_delivery_endpoint      # Built-in HTTP payload staging server
└── 📊 telemetry_core.db         # SQLite backend for host & log management
```

---

## ⚙️ REQUIREMENTS
- Python 3.11 or higher
- Operating System: Windows 10/11 (Target) | Windows/Linux (Host)
- Administrator/Root privileges for packet capture and persistence deployment
- Python Dependencies: `pynput`, `scapy`, `pycryptodome`, `pyinstaller`, `customtkinter`

---

## 📦 INSTALLATION & SETUP
1. Clone or download the repository to your control machine.
2. Install required Python packages:
   ```bash
   pip install pynput scapy pycryptodome pyinstaller customtkinter
   ```
3. Launch the unified dashboard:
   ```bash
   python unified_suite.py
   ```
4. The GUI auto-initializes the encrypted C2 listener on port `8443` and the delivery endpoint on port `8080`.

---

## 📖 USAGE GUIDE

### 1. Generate Payload
- Navigate to the **PAYLOAD BUILDER** tab in the sidebar.
- Enter your C2 IP/Domain, set a disguise name, and specify an output path.
- Click **GENERATE PAYLOAD**. The builder applies polymorphic string encryption, junk code injection, and control-flow randomization before writing the final script.

### 2. Compile to Executable
- Open a terminal in the output directory.
- Run the PyInstaller command:
  ```bash
  pyinstaller --onefile --noconsole --name <disguise_name> output_payload.py
  ```
- The compiled binary will be located in the `dist/` folder.

### 3. Deploy & Monitor
- Use the **DELIVERY SYSTEM** tab to generate a lightweight dropper script that fetches the compiled payload from the C2 delivery endpoint and executes it silently.
- Monitor live telemetry in the **HOST TELEMETRY** tab. Filter by HWID, export logs, or track geolocation data in real-time. All data is stored locally in the SQLite database with WAL journaling for performance.

---

## 🛡️ OPERATIONAL SECURITY NOTES
- All network traffic is encrypted using AES-CBC with per-session keys. No plaintext credentials or keystrokes are stored locally on target or host systems.
- Payloads are designed to run silently in the background with no visible UI, console output, or system tray icons.
- Packet capture requires administrative/root privileges. Ensure target environment permissions are configured accordingly.
- The polymorphic engine ensures each generated binary has a unique cryptographic signature, defeating static hash-based detection.
- In-memory buffers are cleared immediately after successful transmission. Zero disk artifacts are left on the target.

---

## 📜 CHANGELOG v5.1.0
- 🎨 Complete GUI overhaul: Modern dark theme, sidebar navigation, terminal-style logging, professional SOC dashboard layout
- 🔒 AES-CBC encrypted C2 communications with per-session keys
- 🎭 Advanced polymorphic builder (string encryption, control-flow flattening, junk injection)
- 🌍 Integrated IP geolocation & host mapping
- 🛡️ Anti-debug/anti-VM timing checks
- 📦 Automated HTTP dropper generator
- 🗃️ Optimized SQLite backend with WAL journaling
- 🖥️ Replaced legacy Tkinter with CustomTkinter for modern, responsive UI

---

## ⚠️ DISCLAIMER
This framework is provided strictly for authorized security assessments, internal telemetry monitoring, and controlled red-team engagements. The developers assume no liability for misuse, unauthorized deployment, or violation of applicable laws. Always ensure you have explicit, documented permission before deploying telemetry agents on any system.

---

## 📜 LICENSE
Private Use Only. Redistribution, commercial licensing, or unauthorized modification is strictly prohibited. All rights reserved by the VeilStream Core Dev Team.
```
