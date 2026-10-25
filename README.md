# CyberScope — Cybersecurity Monitoring Desktop Application

A Python-based cybersecurity and network monitoring desktop application built with CustomTkinter, Scapy, and pynput. Designed for educational cybersecurity research, authorized network auditing, and learning about packet analysis and endpoint monitoring.

## Features

- **Dashboard** — Live statistic cards (packets, TCP, UDP, ICMP, DNS, bytes), a protocol-distribution donut chart, and a live network activity line chart with a rolling time window.
- **Packet Sniffer** — Live packet capture using Scapy with interface selection, BPF filtering, a scrollable packet table, search/protocol filters, and CSV export.
- **Keylogger Demonstration** — Consent-based, educational keystroke-monitoring demo using pynput. Keystrokes stay in a local in-memory buffer; nothing is transmitted or stored permanently.
- **CLI Mode** — Headless packet capture and CSV export via `argparse` (`merged_tool.py`) with `--list-interfaces`, `--interface`, `--filter`, `--output`, `--count`, `--version`.
- **Thread-safe UI** — Background capture/keylogging threads communicate with the GUI through queues; Tkinter widgets are updated only from the main thread.
- **Logging** — Rotating file and console logging via Python's `logging` module.

## Technology Stack

| Component | Technology |
|-----------|-----------|
| GUI | CustomTkinter (dark theme) |
| Packet capture & parsing | Scapy |
| Keystroke monitoring | pynput |
| HTTP library | requests |
| Data processing | pandas, NumPy |
| Charts | Matplotlib |
| System metrics | psutil |
| Threading / queues | `threading`, `queue` |
| CLI | argparse |
| Testing | pytest |

## Project Structure

```
CyberScope/
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
├── app.py                 # GUI entry point
├── merged_tool.py         # CLI entry point
├── core/
│   ├── __init__.py
│   ├── packet_parser.py   # IPv4/IPv6/TCP/UDP/ICMP/ARP parsing
│   ├── packet_capture.py  # Scapy capture engine (threaded, queue-based)
│   ├── keyboard_monitor.py# Consent-based keylogger demo
│   └── statistics.py      # Counters, protocol distribution, CSV export
├── ui/
│   ├── __init__.py
│   ├── dashboard.py       # Stats cards + matplotlib charts
│   ├── packet_page.py     # Packet sniffer page
│   ├── packet_table.py    # Scrollable packet table
│   ├── keylogger_page.py  # Keylogger demo page
│   ├── sidebar.py         # Left navigation sidebar
│   ├── stats_cards.py     # Statistic cards widget
│   └── status_bar.py      # Status bar placeholder
├── utils/
│   ├── __init__.py
│   ├── logging_config.py  # Rotating file + console logging
│   └── theme.py           # CustomTkinter dark theme
├── tests/
│   ├── __init__.py
│   ├── test_packet_parser.py
│   ├── test_statistics.py
│   └── test_config.py
├── assets/                # Screenshot placeholder (add your screenshot here)
└── logs/                  # Rotating log files (created at runtime)
```

## Screenshot

The dashboard screenshot should be placed at `assets/dashboard.png`.

> **Note:** No screenshot is currently included in the repository. Add a PNG screenshot of the running application to `assets/dashboard.png` and reference it here:
>
> ![CyberScope Dashboard](assets/dashboard.png)

## Installation (Ubuntu)

### 1. System dependencies

Install Tkinter and Scapy dependencies:

```bash
sudo apt update
sudo apt install -y python3-tk python3-pip python3-venv
```

Scapy packet capture requires raw socket access. On Ubuntu, you can either run as root or grant the capture binary the `CAP_NET_RAW` capability:

```bash
# Option A: run the GUI/CLI with sudo (simple)
sudo ./venv/bin/python app.py

# Option B: grant CAP_NET_RAW to the Python binary (avoid sudo)
sudo setcap cap_net_raw+ep /path/to/venv/bin/python
```

### 2. Virtual environment workflow

```bash
# 1. Create a virtual environment
python3 -m venv venv

# 2. Activate it
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the GUI
python app.py

# 5. Run the CLI
python merged_tool.py --list-interfaces
python merged_tool.py --interface lo --count 10 --output packets.csv

# 6. Execute tests
pytest
```

> Packet capture on Linux requires `CAP_NET_RAW`. If you are not root, use `sudo` or grant the capability as shown above.

## Usage

### GUI

```bash
source venv/bin/activate
python app.py
```

The window opens on the Dashboard. Use the left sidebar to navigate:

- **Dashboard** — live stats and charts
- **Packet Sniffer** — select an interface, click ▶ Start Capture, view packets, export CSV
- **Keylogger** — educational demo; click ▶ Start Demonstration (keys stay local only)

### CLI

```bash
# List interfaces
python merged_tool.py --list-interfaces

# Capture packets on an interface (requires CAP_NET_RAW / root)
sudo python merged_tool.py --interface lo --count 20 --output capture.csv

# Capture with a BPF filter
sudo python merged_tool.py --interface wlo1 --filter "tcp port 80" --count 50

# Keylogger demonstration (explicit opt-in only)
python merged_tool.py --keylogger
```

## Packet-Capture Permissions

Scapy opens a raw socket to sniff packets, which requires `CAP_NET_RAW` on Linux. The application handles `PermissionError` gracefully and reports it in the UI/logs.

**Recommended approach** (avoid running the entire GUI as root):

```bash
sudo setcap cap_net_raw+ep $(which python3)
```

Or run with `sudo` for simplicity:

```bash
sudo ./venv/bin/python app.py
```

## Testing

```bash
source venv/bin/activate
pytest
```

Tests cover packet parsing (TCP, UDP, ICMP, ARP, IPv6, missing layers), statistics counters, rate calculation, and CSV export.

## Security & Ethical Use Disclaimer

**CyberScope is for educational cybersecurity research and authorized network auditing only.**

- The keystroke-monitoring feature is a **demonstration only**. It requires explicit user action to start, shows a visible recording indicator, keeps data in a local in-memory buffer, and transmits nothing.
- Do **not** use this tool to monitor networks or systems you do not own or have explicit written authorization to test.
- Do **not** capture passwords, credentials, or sensitive information.
- The default keylogger host has been changed from an external IP to `127.0.0.1` to prevent accidental external transmission.

## Known Limitations

- Packet capture on Linux requires root/`CAP_NET_RAW` privileges.
- The dashboard charts update once per second (not per-packet) to keep the UI responsive during high-volume capture.
- The in-memory packet table is bounded to 5,000 packets to avoid unbounded memory growth.
- The GUI has been tested on Ubuntu with an X11/Wayland display; headless systems cannot launch the window.

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit your changes with a descriptive message.
4. Push to your fork and open a pull request.

Please run `pytest` before submitting changes and ensure all tests pass.

## License

MIT License. See [LICENSE](LICENSE).
