"""Packet Sniffer page for CyberScope.

Provides interface selection, capture start/stop, protocol filtering,
search, a scrollable packet table, and CSV export. All packet capture
runs in a background thread; the GUI is updated through a thread-safe
queue on the main Tkinter thread.
"""

from __future__ import annotations

import csv
import io
import queue
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox
from typing import Callable, List, Optional

import customtkinter as ctk

from core.packet_capture import PacketCapture
from ui.packet_table import PacketTable


class PacketPage(ctk.CTkFrame):

    def __init__(
        self,
        master,
        stats_callback: Optional[Callable[[dict], None]] = None,
        capture_state_callback: Optional[
            Callable[[Optional[str], bool], None]
        ] = None,
    ):

        super().__init__(master)

        self.stats_callback = stats_callback
        self.capture_state_callback = capture_state_callback

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        # ----------------------------------------------------------
        # Capture engine + queue
        # ----------------------------------------------------------

        self.capture = PacketCapture(callback=self._enqueue_packet)
        self.packet_queue: queue.Queue = queue.Queue()
        self._captured_packets: List[dict] = []  # for CSV export

        # ----------------------------------------------------------
        # Title
        # ----------------------------------------------------------

        title = ctk.CTkLabel(
            self,
            text="Packet Sniffer",
            font=("JetBrains Mono", 32, "bold"),
        )
        title.grid(row=0, column=0, pady=(20, 10))

        # ----------------------------------------------------------
        # Controls
        # ----------------------------------------------------------

        controls = ctk.CTkFrame(self)
        controls.grid(
            row=1, column=0, sticky="ew", padx=30, pady=10
        )
        controls.grid_columnconfigure(1, weight=1)
        controls.grid_columnconfigure(3, weight=1)

        # --- Interface ---
        ctk.CTkLabel(controls, text="Interface").grid(
            row=0, column=0, padx=10, pady=10
        )
        self.interface = ctk.CTkOptionMenu(controls, values=["Loading..."])
        self.interface.set("Select interface")
        self.interface.grid(
            row=0, column=1, sticky="ew", padx=10, pady=10
        )

        # --- Capture filter ---
        ctk.CTkLabel(controls, text="BPF Filter").grid(
            row=1, column=0, padx=10, pady=10
        )
        self.capture_filter = ctk.CTkEntry(
            controls,
            placeholder_text="e.g. tcp port 80 (optional)",
        )
        self.capture_filter.grid(
            row=1, column=1, sticky="ew", padx=10, pady=10
        )

        # Load interfaces after widget is created.
        self.after(100, self._load_interfaces)

        # ----------------------------------------------------------
        # Button area
        # ----------------------------------------------------------

        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=2, column=0, pady=10)

        self.start_btn = ctk.CTkButton(
            button_frame,
            text="▶ Start Capture",
            width=150,
            command=self.start_capture,
        )
        self.start_btn.pack(side="left", padx=10, pady=8)

        self.stop_btn = ctk.CTkButton(
            button_frame,
            text="■ Stop",
            width=120,
            command=self.stop_capture,
            state="disabled",
        )
        self.stop_btn.pack(side="left", padx=10, pady=8)

        self.clear_btn = ctk.CTkButton(
            button_frame,
            text="🗑 Clear",
            width=120,
            command=self.clear_table,
        )
        self.clear_btn.pack(side="left", padx=10, pady=8)

        self.export_btn = ctk.CTkButton(
            button_frame,
            text="💾 Export CSV",
            width=140,
            command=self.export_csv,
        )
        self.export_btn.pack(side="left", padx=10, pady=8)

        # ----------------------------------------------------------
        # Status
        # ----------------------------------------------------------

        self.status_label = ctk.CTkLabel(
            self,
            text="● Capture stopped",
            font=("JetBrains Mono", 13),
        )
        self.status_label.grid(row=3, column=0, pady=(5, 0))

        # ----------------------------------------------------------
        # Search + protocol filter
        # ----------------------------------------------------------

        filter_frame = ctk.CTkFrame(self)
        filter_frame.grid(row=4, column=0, sticky="ew", padx=30, pady=(10, 0))
        filter_frame.grid_columnconfigure(1, weight=1)

        self.search_entry = ctk.CTkEntry(
            filter_frame,
            placeholder_text="Search packets...",
        )
        self.search_entry.grid(
            row=0, column=0, sticky="ew", padx=(10, 5), pady=10
        )
        self.search_entry.bind("<KeyRelease>", lambda _e: self._apply_filters())

        self.proto_filter = ctk.CTkOptionMenu(
            filter_frame,
            values=["All", "TCP", "UDP", "ICMP", "DNS", "ARP", "IPv6"],
            command=lambda _v: self._apply_filters(),
        )
        self.proto_filter.set("All")
        self.proto_filter.grid(
            row=0, column=1, sticky="ew", padx=(5, 10), pady=10
        )

        # ----------------------------------------------------------
        # Packet table
        # ----------------------------------------------------------

        self.table = PacketTable(self)
        self.table.grid(
            row=5, column=0, sticky="nsew", padx=30, pady=20
        )

        # ----------------------------------------------------------
        # Start queue polling
        # ----------------------------------------------------------

        self.after(100, self.process_queue)

    # --------------------------------------------------------------
    # Interface loading
    # --------------------------------------------------------------

    def _load_interfaces(self) -> None:
        """Populate the interface dropdown from available interfaces."""
        interfaces = PacketCapture.list_interfaces()
        if interfaces:
            self.interface.configure(values=interfaces)
            self.interface.set(interfaces[0])
        else:
            self.interface.configure(values=["None available"])
            self.interface.set("None available")
            self.start_btn.configure(state="disabled")

    # --------------------------------------------------------------
    # Packet handling
    # --------------------------------------------------------------

    def _enqueue_packet(self, data: dict) -> None:
        """Called from capture thread: enqueue parsed packet."""
        # Add a local timestamp for the table.
        data["time"] = datetime.now().strftime("%H:%M:%S")
        try:
            self.packet_queue.put_nowait(data)
        except Exception:
            pass  # queue bounded; drop if full

    def process_queue(self) -> None:
        """Drain the packet queue and update the table (main thread)."""
        try:
            while True:
                packet = self.packet_queue.get_nowait()
                self._captured_packets.append(packet)

                # Bound the in-memory packet list to avoid unbounded growth.
                if len(self._captured_packets) > 5000:
                    self._captured_packets = self._captured_packets[-5000:]

                self.table.add_packet(packet)

                # Update shared dashboard stats.
                if self.stats_callback:
                    self.stats_callback(packet)

        except queue.Empty:
            pass

        self.after(100, self.process_queue)

    # --------------------------------------------------------------
    # Filters
    # --------------------------------------------------------------

    def _apply_filters(self) -> None:
        """Re-filter the displayed table rows."""
        search = self.search_entry.get().strip().lower()
        proto = self.proto_filter.get()

        # Rebuild visible rows from the full captured list.
        self.table.clear()
        for pkt in self._captured_packets:
            if proto != "All" and pkt.get("protocol") != proto:
                continue
            if search and search not in str(pkt).lower():
                continue
            self.table.add_packet(pkt)

    # --------------------------------------------------------------
    # Capture start / stop
    # --------------------------------------------------------------

    def start_capture(self) -> None:
        interface = self.interface.get()
        if not interface or interface == "None available":
            messagebox.showwarning(
                "No interface",
                "Please select a valid network interface.",
            )
            return

        bpf = self.capture_filter.get().strip() or None

        # Validate BPF filter by attempting a quick sniff will surface
        # errors; here we just pass it through.
        self.capture.interface = interface
        self.capture.bpf_filter = bpf

        if not self.capture.start():
            return

        if self.capture_state_callback:
            self.capture_state_callback(interface, True)

        self.status_label.configure(text=f"● Capturing on {interface}")
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

    def stop_capture(self) -> None:
        interface = self.interface.get()
        self.capture.stop()

        if self.capture_state_callback:
            self.capture_state_callback(interface, False)

        self.status_label.configure(text="● Capture stopped")
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

    # --------------------------------------------------------------
    # Clear + export
    # --------------------------------------------------------------

    def clear_table(self) -> None:
        self.table.clear()
        self._captured_packets.clear()
        try:
            while True:
                self.packet_queue.get_nowait()
        except queue.Empty:
            pass

    def export_csv(self) -> None:
        """Export captured packets to a CSV file."""
        if not self._captured_packets:
            messagebox.showinfo(
                "No data", "No packets captured to export."
            )
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export captured packets",
        )
        if not path:
            return

        try:
            from core.statistics import Statistics

            stats = Statistics()
            rows = stats.to_csv_rows(self._captured_packets)
            csv_text = Statistics.rows_to_csv_string(rows)

            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(csv_text)

            messagebox.showinfo(
                "Exported",
                f"Exported {len(rows)} packets to {path}",
            )
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Export failed", str(exc))

    # --------------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------------

    def destroy(self) -> None:
        self.capture.stop()
        super().destroy()
