"""CyberScope — main application window.

Wires together the Dashboard, Packet Sniffer, and Keylogger pages with
shared statistics state and capture lifecycle. Runs on the CustomTkinter
main loop; all background capture/keylogging happens in daemon threads
and updates the GUI through thread-safe queues.
"""

import customtkinter as ctk

from core.statistics import Statistics
from ui.dashboard import Dashboard
from ui.keylogger_page import KeyloggerPage
from ui.packet_page import PacketPage
from ui.sidebar import Sidebar
from utils.logging_config import setup_logging, get_logger
from utils.theme import setup_theme

logger = get_logger(__name__)

# ------------------------------------------------------------------
# Theme
# ------------------------------------------------------------------

setup_theme()
setup_logging()

# ------------------------------------------------------------------
# Shared state
# ------------------------------------------------------------------

app = ctk.CTk()
app.geometry("1400x850")
app.title("CyberScope")

app.grid_columnconfigure(1, weight=1)
app.grid_rowconfigure(0, weight=1)

# Statistics engine (updated from GUI main thread).
stats_engine = Statistics()


def update_stats(data: dict) -> None:
    """Called from the main thread whenever a packet is processed."""
    stats_engine.update(data)


def get_capture_state():
    """Return (interface, running) for the dashboard status panel."""
    if packet_page.capture is not None:
        return packet_page.capture.interface, packet_page.capture.running
    return None, False


def get_packet_rate() -> float:
    """Return current packets-per-second for the live chart."""
    return stats_engine.get_packet_rate(window=1.0)


# ------------------------------------------------------------------
# Create pages
# ------------------------------------------------------------------

dashboard = Dashboard(
    app,
    stats_callback=lambda: dict(
        Packets=stats_engine.total_packets,
        TCP=stats_engine.protocols.get("TCP", 0),
        UDP=stats_engine.protocols.get("UDP", 0),
        ICMP=stats_engine.protocols.get("ICMP", 0),
        DNS=stats_engine.protocols.get("DNS", 0),
        Bytes=stats_engine.total_bytes,
    ),
    get_capture_state=get_capture_state,
    packet_rate_callback=get_packet_rate,
)

dashboard.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

packet_page = PacketPage(
    app,
    stats_callback=update_stats,
    capture_state_callback=lambda iface, running: None,  # handled below
)

packet_page.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

keylogger_page = KeyloggerPage(app)
keylogger_page.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

packet_page.grid_remove()
keylogger_page.grid_remove()


# ------------------------------------------------------------------
# Capture state -> dashboard status panel
# ------------------------------------------------------------------

def set_capture_state(interface: str, running: bool) -> None:
    if running:
        dashboard.status_label.configure(
            text=f"🟡 Capturing on {interface or 'unknown'}..."
        )
        dashboard.interface.configure(
            text=f"Interface : {interface or 'Not Selected'}"
        )
    else:
        dashboard.status_label.configure(
            text="🟢 Waiting for packet capture..."
        )
        dashboard.interface.configure(
            text=f"Interface : {interface or 'Not Selected'}"
        )


# Patch PacketPage's callback after creation.
packet_page.capture_state_callback = set_capture_state


# ------------------------------------------------------------------
# Navigation functions
# ------------------------------------------------------------------

def show_dashboard() -> None:
    packet_page.grid_remove()
    keylogger_page.grid_remove()
    dashboard.grid()


def show_packet_page() -> None:
    dashboard.grid_remove()
    keylogger_page.grid_remove()
    packet_page.grid()


def show_keylogger_page() -> None:
    dashboard.grid_remove()
    packet_page.grid_remove()
    keylogger_page.grid()


app.show_dashboard = show_dashboard
app.show_packet_page = show_packet_page
app.show_keylogger_page = show_keylogger_page

# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------

sidebar = Sidebar(app)
sidebar.grid(row=0, column=0, sticky="ns")

# ------------------------------------------------------------------
# Graceful shutdown
# ------------------------------------------------------------------

def on_closing() -> None:
    logger.info("Shutting down CyberScope...")
    packet_page.capture.stop()
    if keylogger_page.keylogger is not None:
        keylogger_page.keylogger.stop()
    app.destroy()


app.protocol("WM_DELETE_WINDOW", on_closing)

# ------------------------------------------------------------------
# Run app
# ------------------------------------------------------------------

logger.info("CyberScope started")
app.mainloop()
