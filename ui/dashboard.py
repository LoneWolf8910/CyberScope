"""Dashboard page for CyberScope.

Shows live statistic cards, a protocol-distribution donut chart, and a
live network activity line chart. Updated from the main Tkinter thread
via polling (no direct Tkinter access from capture threads).
"""

from __future__ import annotations

import customtkinter as ctk

from ui.stats_cards import StatsCards


class Dashboard(ctk.CTkFrame):

    def __init__(
        self,
        master,
        stats_callback=None,
        get_capture_state=None,
        packet_rate_callback=None,
    ):

        super().__init__(master)

        self.stats_callback = stats_callback
        self.get_capture_state = get_capture_state
        self.packet_rate_callback = packet_rate_callback

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ----------------------------------------------------------
        # Title
        # ----------------------------------------------------------

        title = ctk.CTkLabel(
            self,
            text="Dashboard",
            font=("JetBrains Mono", 32, "bold"),
        )
        title.grid(row=0, column=0, pady=(25, 20))

        # ----------------------------------------------------------
        # Statistics cards
        # ----------------------------------------------------------

        self.stats = StatsCards(self)
        self.stats.grid(row=1, column=0, sticky="ew", padx=30)

        # ----------------------------------------------------------
        # Charts row (donut + line)
        # ----------------------------------------------------------

        charts = ctk.CTkFrame(self, fg_color="transparent")
        charts.grid(row=2, column=0, sticky="nsew", padx=30, pady=20)
        charts.grid_columnconfigure(0, weight=1)
        charts.grid_columnconfigure(1, weight=1)
        charts.grid_rowconfigure(0, weight=1)

        # --- Protocol Distribution (donut) ---
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure

        donut_frame = ctk.CTkFrame(charts)
        donut_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        donut_frame.grid_rowconfigure(0, weight=1)
        donut_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            donut_frame,
            text="Protocol Distribution",
            font=("JetBrains Mono", 16, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))

        self.donut_fig = Figure(figsize=(4.5, 3.5), dpi=100)
        self.donut_ax = self.donut_fig.add_subplot(111)
        self.donut_canvas = FigureCanvasTkAgg(self.donut_fig, master=donut_frame)
        self.donut_canvas.get_tk_widget().grid(
            row=1, column=0, sticky="nsew", padx=15, pady=(0, 15)
        )
        self.donut_canvas.draw()

        # --- Live Network Activity (line) ---
        line_frame = ctk.CTkFrame(charts)
        line_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=0)
        line_frame.grid_rowconfigure(0, weight=1)
        line_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            line_frame,
            text="Live Network Activity",
            font=("JetBrains Mono", 16, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))

        self.line_fig = Figure(figsize=(4.5, 3.5), dpi=100)
        self.line_ax = self.line_fig.add_subplot(111)
        self.line_canvas = FigureCanvasTkAgg(self.line_fig, master=line_frame)
        self.line_canvas.get_tk_widget().grid(
            row=1, column=0, sticky="nsew", padx=15, pady=(0, 15)
        )
        self.line_canvas.draw()

        # Rolling data for the line chart.
        self._time_points = []
        self._rate_points = []

        # ----------------------------------------------------------
        # Status panel
        # ----------------------------------------------------------

        status = ctk.CTkFrame(self)
        status.grid(row=3, column=0, sticky="ew", padx=30, pady=(0, 20))
        status.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            status,
            text="Network Status",
            font=("JetBrains Mono", 22, "bold"),
        ).pack(anchor="w", padx=20, pady=(20, 10))

        self.status_label = ctk.CTkLabel(
            status,
            text="🟢 Waiting for packet capture...",
            font=("JetBrains Mono", 16),
        )
        self.status_label.pack(anchor="w", padx=20)

        self.bandwidth = ctk.CTkLabel(
            status,
            text="Bandwidth : 0 B/s",
            font=("JetBrains Mono", 15),
        )
        self.bandwidth.pack(anchor="w", padx=20, pady=8)

        self.interface = ctk.CTkLabel(
            status,
            text="Interface : Not Selected",
            font=("JetBrains Mono", 15),
        )
        self.interface.pack(anchor="w", padx=20, pady=(0, 20))

        # ----------------------------------------------------------
        # Start live refresh
        # ----------------------------------------------------------

        self._last_bytes = 0
        self.after(1000, self.refresh)

    # --------------------------------------------------------------
    # Refresh (runs on main thread every 1s)
    # --------------------------------------------------------------

    def refresh(self) -> None:

        # --- Stats cards ---
        if self.stats_callback:
            stats = self.stats_callback()
            self.stats.update_stats(stats)

            current_bytes = stats.get("Bytes", 0)
            delta = current_bytes - self._last_bytes
            self._last_bytes = current_bytes

            if delta < 1024:
                bw_text = f"{delta} B/s"
            elif delta < 1024 * 1024:
                bw_text = f"{delta / 1024:.1f} KB/s"
            else:
                bw_text = f"{delta / (1024 * 1024):.2f} MB/s"
            self.bandwidth.configure(text=f"Bandwidth : {bw_text}")

        # --- Packet rate for line chart ---
        if self.packet_rate_callback:
            try:
                rate = self.packet_rate_callback()
            except Exception:
                rate = 0.0
        else:
            rate = 0.0

        import time

        now = time.time()
        self._time_points.append(now)
        self._rate_points.append(rate)

        # Keep rolling window (last 60 seconds).
        cutoff = now - 60
        self._time_points = [t for t in self._time_points if t >= cutoff]
        self._rate_points = self._rate_points[-len(self._time_points):]

        # --- Capture status + interface ---
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

        # --- Redraw charts (throttled: every refresh is fine at 1s) ---
        self._draw_donut()
        self._draw_line()

        self.after(1000, self.refresh)

    # --------------------------------------------------------------
    # Chart drawing
    # --------------------------------------------------------------

    def _draw_donut(self) -> None:
        self.donut_ax.clear()

        if self.stats_callback:
            try:
                dist = self.stats_callback()
            except Exception:
                dist = {}
        else:
            dist = {}

        # Extract protocol counts (exclude non-protocol keys).
        proto_keys = ("TCP", "UDP", "ICMP", "DNS", "OTHER")
        labels = []
        sizes = []
        colors = ["#1E90FF", "#32CD32", "#FFB84D", "#FF4D4D", "#888888"]

        for i, key in enumerate(proto_keys):
            val = dist.get(key, 0)
            if val > 0:
                labels.append(key)
                sizes.append(val)

        if not sizes:
            # Nothing captured yet — show empty state.
            self.donut_ax.text(
                0.5, 0.5, "No packets\ncaptured yet",
                ha="center", va="center",
                transform=self.donut_ax.transAxes,
                fontsize=14, color="#666666",
            )
            self.donut_ax.set_xticks([])
            self.donut_ax.set_yticks([])
        else:
            wedges, _ = self.donut_ax.pie(
                sizes,
                labels=labels,
                colors=colors[: len(sizes)],
                startangle=90,
                counterclock=False,
                wedgeprops=dict(width=0.4, edgecolor="#2b2b2b"),
                autopct="%1.1f%%",
                textprops=dict(fontsize=10, color="white"),
            )

        self.donut_ax.set_title(
            "Protocol Distribution",
            fontsize=13,
            fontweight="bold",
            color="white",
        )
        self.donut_fig.patch.set_facecolor("#2b2b2b")
        self.donut_ax.set_facecolor("#2b2b2b")
        self.donut_canvas.draw_idle()

    def _draw_line(self) -> None:
        self.line_ax.clear()

        if not self._time_points:
            self.line_ax.text(
                0.5, 0.5, "No activity",
                ha="center", va="center",
                transform=self.line_ax.transAxes,
                fontsize=14, color="#666666",
            )
            self.line_ax.set_xticks([])
            self.line_ax.set_yticks([])
        else:
            # Relative seconds from the first point.
            t0 = self._time_points[0]
            x = [t - t0 for t in self._time_points]
            y = self._rate_points

            self.line_ax.plot(
                x, y, color="#1E90FF", linewidth=2,
            )
            self.line_ax.fill_between(
                x, y, color="#1E90FF", alpha=0.2,
            )
            self.line_ax.set_xlabel("Seconds", fontsize=10, color="white")
            self.line_ax.set_ylabel("Packets/sec", fontsize=10, color="white")
            self.line_ax.tick_params(colors="white", labelsize=9)
            self.line_ax.spines["bottom"].set_color("white")
            self.line_ax.spines["left"].set_color("white")
            self.line_ax.spines["top"].set_visible(False)
            self.line_ax.spines["right"].set_visible(False)

        self.line_ax.set_title(
            "Live Network Activity",
            fontsize=13,
            fontweight="bold",
            color="white",
        )
        self.line_fig.patch.set_facecolor("#2b2b2b")
        self.line_ax.set_facecolor("#2b2b2b")
        self.line_canvas.draw_idle()
