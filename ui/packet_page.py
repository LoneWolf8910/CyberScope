import customtkinter as ctk
import queue

from ui.packet_table import PacketTable
from core.packet_sniffer import PacketSniffer


class PacketPage(ctk.CTkFrame):

    def __init__(self, master, stats_callback=None, capture_state_callback=None):
        super().__init__(master)

        self.stats_callback = stats_callback
        self.capture_state_callback = capture_state_callback

        # ==========================================
        # PACKET QUEUE + SNIFFER
        # ==========================================

        self.packet_queue = queue.Queue()

        self.sniffer = PacketSniffer(
            callback=self.packet_callback
        )

        # ==========================================
        # LAYOUT
        # ==========================================

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        # ==========================================
        # TITLE
        # ==========================================

        title = ctk.CTkLabel(
            self,
            text="Packet Sniffer",
            font=("JetBrains Mono", 32, "bold")
        )

        title.grid(
            row=0,
            column=0,
            pady=(20, 10)
        )

        # ==========================================
        # CONTROLS
        # ==========================================

        controls = ctk.CTkFrame(self)

        controls.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=30,
            pady=10
        )

        controls.grid_columnconfigure(1, weight=1)

        # ------------------------------------------
        # Interface
        # ------------------------------------------

        interface_label = ctk.CTkLabel(
            controls,
            text="Interface"
        )

        interface_label.grid(
            row=0,
            column=0,
            padx=10,
            pady=10
        )

        self.interface = ctk.CTkOptionMenu(
            controls,
            values=[
                "wlo1",
                "eno1",
                "lo"
            ]
        )

        self.interface.set("wlo1")

        self.interface.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=10,
            pady=10
        )

        # ------------------------------------------
        # Capture Filter
        # ------------------------------------------

        filter_label = ctk.CTkLabel(
            controls,
            text="Capture Filter"
        )

        filter_label.grid(
            row=1,
            column=0,
            padx=10,
            pady=10
        )

        self.capture_filter = ctk.CTkEntry(
            controls,
            placeholder_text="Filter support coming next..."
        )

        self.capture_filter.grid(
            row=1,
            column=1,
            sticky="ew",
            padx=10,
            pady=10
        )

        # ==========================================
        # BUTTON AREA
        # ==========================================

        button_frame = ctk.CTkFrame(self)

        button_frame.grid(
            row=2,
            column=0,
            pady=10
        )

        # ------------------------------------------
        # Start
        # ------------------------------------------

        self.start_btn = ctk.CTkButton(
            button_frame,
            text="▶ Start Capture",
            width=150,
            command=self.start_capture
        )

        self.start_btn.pack(
            side="left",
            padx=10,
            pady=8
        )

        # ------------------------------------------
        # Stop
        # ------------------------------------------

        self.stop_btn = ctk.CTkButton(
            button_frame,
            text="■ Stop",
            width=120,
            command=self.stop_capture
        )

        self.stop_btn.pack(
            side="left",
            padx=10,
            pady=8
        )

        # ------------------------------------------
        # Clear
        # ------------------------------------------

        self.clear_btn = ctk.CTkButton(
            button_frame,
            text="🗑 Clear",
            width=120,
            command=self.clear_table
        )

        self.clear_btn.pack(
            side="left",
            padx=10,
            pady=8
        )

        # ==========================================
        # STATUS
        # ==========================================

        self.status_label = ctk.CTkLabel(
            self,
            text="● Capture stopped",
            font=("JetBrains Mono", 13)
        )

        self.status_label.grid(
            row=3,
            column=0,
            pady=(5, 0)
        )

        # ==========================================
        # PACKET TABLE
        # ==========================================

        self.table = PacketTable(self)

        self.table.grid(
            row=4,
            column=0,
            sticky="nsew",
            padx=30,
            pady=20
        )

        # ==========================================
        # START QUEUE POLLING
        # ==========================================

        self.after(
            100,
            self.process_queue
        )

    # ==============================================
    # CALLBACK FROM PACKET SNIFFER
    # ==============================================

    def packet_callback(self, data):

        # IMPORTANT:
        # Scapy runs in another thread.
        # We therefore do NOT touch Tkinter here.

        self.packet_queue.put(data)

    # ==============================================
    # PROCESS PACKET QUEUE
    # ==============================================

    def process_queue(self):

        try:

            while True:

                packet = self.packet_queue.get_nowait()

                self.table.add_packet(packet)

                # Update shared stats (runs on main thread via after())
                if self.stats_callback:
                    self.stats_callback(packet)

        except queue.Empty:

            pass

        # Run again after 100 ms
        self.after(
            100,
            self.process_queue
        )

    # ==============================================
    # START CAPTURE
    # ==============================================

    def start_capture(self):

        interface = self.interface.get()

        self.sniffer.start(interface)

        # Report capture state to dashboard
        if self.capture_state_callback:
            self.capture_state_callback(interface, True)

        self.status_label.configure(
            text=f"● Capturing on {interface}"
        )

        self.start_btn.configure(
            state="disabled"
        )

        self.stop_btn.configure(
            state="normal"
        )

    # ==============================================
    # STOP CAPTURE
    # ==============================================

    def stop_capture(self):

        interface = self.interface.get()

        self.sniffer.stop()

        # Report capture state to dashboard
        if self.capture_state_callback:
            self.capture_state_callback(interface, False)

        self.status_label.configure(
            text="● Capture stopped"
        )

        self.start_btn.configure(
            state="normal"
        )

        self.stop_btn.configure(
            state="disabled"
        )

    # ==============================================
    # CLEAR PACKETS
    # ==============================================

    def clear_table(self):

        self.table.clear()

        # Also remove packets still waiting
        # inside the GUI queue.

        try:

            while True:
                self.packet_queue.get_nowait()

        except queue.Empty:

            pass