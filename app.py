import customtkinter as ctk

from utils.theme import setup_theme
from ui.sidebar import Sidebar
from ui.dashboard import Dashboard
from ui.packet_page import PacketPage
from ui.keylogger_page import KeyloggerPage

# -------------------------
# Theme
# -------------------------

setup_theme()

# -------------------------
# Main Window
# -------------------------

app = ctk.CTk()

app.geometry("1400x800")
app.title("CyberScope")

app.grid_columnconfigure(1, weight=1)
app.grid_rowconfigure(0, weight=1)

# -------------------------
# Shared stats + capture state
# -------------------------

app.stats = {
    "Packets": 0,
    "TCP": 0,
    "UDP": 0,
    "DNS": 0,
    "ICMP": 0,
    "Bytes": 0,
}

app.capture_interface = None
app.capture_running = False


def update_stats(data):
    """Called from the main thread whenever a packet is processed."""
    app.stats["Packets"] += 1
    app.stats["Bytes"] += data.get("length", 0)

    proto = data.get("protocol", "OTHER")
    sport = data.get("sport", "-")
    dport = data.get("dport", "-")

    if proto == "TCP":
        app.stats["TCP"] += 1
    elif proto == "UDP":
        app.stats["UDP"] += 1
    elif proto == "ICMP":
        app.stats["ICMP"] += 1

    # DNS detection (port 53)
    if sport == 53 or dport == 53:
        app.stats["DNS"] += 1


def set_capture_state(interface, running):
    app.capture_interface = interface
    app.capture_running = running


# -------------------------
# Create Pages
# -------------------------

dashboard = Dashboard(
    app,
    stats_callback=lambda: dict(app.stats),
    get_capture_state=lambda: (app.capture_interface, app.capture_running),
)

dashboard.grid(
    row=0,
    column=1,
    sticky="nsew",
    padx=20,
    pady=20
)

packet_page = PacketPage(
    app,
    stats_callback=update_stats,
    capture_state_callback=set_capture_state,
)

packet_page.grid(
    row=0,
    column=1,
    sticky="nsew",
    padx=20,
    pady=20
)

keylogger_page = KeyloggerPage(app)

keylogger_page.grid(
    row=0,
    column=1,
    sticky="nsew",
    padx=20,
    pady=20
)

packet_page.grid_remove()
keylogger_page.grid_remove()

# -------------------------
# Navigation Functions
# -------------------------

def show_dashboard():
    packet_page.grid_remove()
    keylogger_page.grid_remove()
    dashboard.grid()

def show_packet_page():
    dashboard.grid_remove()
    keylogger_page.grid_remove()
    packet_page.grid()


def show_keylogger_page():
    dashboard.grid_remove()
    packet_page.grid_remove()
    keylogger_page.grid()

# -------------------------
# Attach Functions to App
# -------------------------

app.show_dashboard = show_dashboard
app.show_packet_page = show_packet_page
app.show_keylogger_page = show_keylogger_page

# -------------------------
# Sidebar
# -------------------------

sidebar = Sidebar(app)
sidebar.grid(row=0, column=0, sticky="ns")

# -------------------------
# Run App
# -------------------------

app.mainloop()