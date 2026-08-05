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
# Create Pages
# -------------------------

dashboard = Dashboard(app)

dashboard.grid(
    row=0,
    column=1,
    sticky="nsew",
    padx=20,
    pady=20
)

packet_page = PacketPage(app)

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