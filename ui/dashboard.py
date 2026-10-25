import customtkinter as ctk

from ui.stats_cards import StatsCards


class Dashboard(ctk.CTkFrame):

    def __init__(self, master, stats_callback=None, get_capture_state=None):

        super().__init__(master)

        self.stats_callback = stats_callback
        self.get_capture_state = get_capture_state

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # -----------------------------
        # Title
        # -----------------------------

        title = ctk.CTkLabel(
            self,
            text="Dashboard",
            font=("JetBrains Mono", 32, "bold")
        )

        title.grid(
            row=0,
            column=0,
            pady=(25, 20)
        )

        # -----------------------------
        # Statistics Cards
        # -----------------------------

        self.stats = StatsCards(self)

        self.stats.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=30
        )

        # -----------------------------
        # Status Panel
        # -----------------------------

        status = ctk.CTkFrame(self)

        status.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=30,
            pady=20
        )

        status.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            status,
            text="Network Status",
            font=("JetBrains Mono", 22, "bold")
        ).pack(
            anchor="w",
            padx=20,
            pady=(20, 10)
        )

        self.status_label = ctk.CTkLabel(
            status,
            text="🟢 Waiting for packet capture...",
            font=("JetBrains Mono", 16)
        )

        self.status_label.pack(
            anchor="w",
            padx=20
        )

        self.bandwidth = ctk.CTkLabel(
            status,
            text="Bandwidth : 0 B/s",
            font=("JetBrains Mono", 15)
        )

        self.bandwidth.pack(
            anchor="w",
            padx=20,
            pady=8
        )

        self.interface = ctk.CTkLabel(
            status,
            text="Interface : Not Selected",
            font=("JetBrains Mono", 15)
        )

        self.interface.pack(
            anchor="w",
            padx=20
        )

        # -----------------------------
        # Start live refresh
        # -----------------------------

        self.after(1000, self.refresh)

    # ---------------------------------
    # Refresh dashboard stats + status
    # ---------------------------------

    def refresh(self):

        # Update stats cards
        if self.stats_callback:
            stats = self.stats_callback()
            self.stats.update_stats(stats)

            # Bandwidth = bytes since last refresh
            current_bytes = stats.get("Bytes", 0)
            if not hasattr(self, "_last_bytes"):
                self._last_bytes = 0
            delta = current_bytes - self._last_bytes
            self._last_bytes = current_bytes

            if delta < 1024:
                bw_text = f"{delta} B/s"
            elif delta < 1024 * 1024:
                bw_text = f"{delta / 1024:.1f} KB/s"
            else:
                bw_text = f"{delta / (1024 * 1024):.2f} MB/s"

            self.bandwidth.configure(text=f"Bandwidth : {bw_text}")

        # Update capture status + interface
        if self.get_capture_state:
            interface, running = self.get_capture_state()

            if running:
                self.status_label.configure(
                    text=f"🟡 Capturing on {interface or 'unknown'}..."
                )
                self.interface.configure(
                    text=f"Interface : {interface or 'Not Selected'}"
                )
            else:
                self.status_label.configure(
                    text="🟢 Waiting for packet capture..."
                )
                self.interface.configure(
                    text=f"Interface : {interface or 'Not Selected'}"
                )

        # Schedule next refresh
        self.after(1000, self.refresh)
