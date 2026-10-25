"""Keystroke-monitoring demonstration page for CyberScope.

A clearly labeled, consent-based educational demonstration using pynput.
Keys are kept in a local in-memory buffer only — nothing is transmitted
to any remote server. The demonstration only runs after the user
explicitly clicks Start and shows a visible recording indicator.
"""

from __future__ import annotations

import queue
from typing import Optional

import customtkinter as ctk

from core.keyboard_monitor import KeyLogger


class KeyloggerPage(ctk.CTkFrame):

    def __init__(self, master):

        super().__init__(master)

        self.key_queue = queue.Queue()
        self.keylogger: Optional[KeyLogger] = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        # ----------------------------------------------------------
        # Title
        # ----------------------------------------------------------

        title = ctk.CTkLabel(
            self,
            text="Keylogger Demonstration",
            font=("JetBrains Mono", 28, "bold"),
        )
        title.grid(row=0, column=0, pady=(20, 8))

        # ----------------------------------------------------------
        # Consent notice
        # ----------------------------------------------------------

        consent = ctk.CTkLabel(
            self,
            text=(
                "Educational demonstration only. "
                "Keystrokes stay in a local in-memory buffer. "
                "Nothing is transmitted or stored permanently."
            ),
            font=("JetBrains Mono", 13),
            text_color="#ffcc00",
            wraplength=1100,
            justify="center",
        )
        consent.grid(row=1, column=0, pady=(0, 12))

        # ----------------------------------------------------------
        # Controls
        # ----------------------------------------------------------

        controls = ctk.CTkFrame(self)
        controls.grid(row=2, column=0, sticky="ew", padx=30, pady=10)
        controls.grid_columnconfigure((1, 3), weight=1)

        self.start_btn = ctk.CTkButton(
            controls,
            text="▶ Start Demonstration",
            width=190,
            command=self.start_logger,
        )
        self.start_btn.pack(side="left", padx=10, pady=8)

        self.stop_btn = ctk.CTkButton(
            controls,
            text="■ Stop",
            width=120,
            state="disabled",
            command=self.stop_logger,
        )
        self.stop_btn.pack(side="left", padx=10, pady=8)

        self.clear_btn = ctk.CTkButton(
            controls,
            text="🗑 Clear",
            width=120,
            command=self.clear_text,
        )
        self.clear_btn.pack(side="left", padx=10, pady=8)

        # ----------------------------------------------------------
        # Status
        # ----------------------------------------------------------

        self.status_label = ctk.CTkLabel(
            self,
            text="● Demonstration stopped",
            font=("JetBrains Mono", 13),
        )
        self.status_label.grid(row=3, column=0, pady=(5, 0))

        # ----------------------------------------------------------
        # Log text
        # ----------------------------------------------------------

        self.log_text = ctk.CTkTextbox(self, width=1180, height=420)
        self.log_text.grid(row=4, column=0, sticky="nsew", padx=30, pady=20)
        self.log_text.configure(state="disabled")

        # ----------------------------------------------------------
        # Queue polling
        # ----------------------------------------------------------

        self.after(100, self.process_queue)

    # --------------------------------------------------------------
    # Queue processing
    # --------------------------------------------------------------

    def process_queue(self) -> None:
        try:
            while True:
                key_text = self.key_queue.get_nowait()
                self.log_text.configure(state="normal")
                self.log_text.insert("end", key_text)
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except Exception:
            pass

        self.after(100, self.process_queue)

    # --------------------------------------------------------------
    # Start / stop
    # --------------------------------------------------------------

    def start_logger(self) -> None:
        if self.keylogger is not None and self.keylogger.listener.running:
            return

        self.keylogger = KeyLogger(callback=self.key_callback)
        self.keylogger.start()

        self.status_label.configure(
            text="🔴 Recording keys (local buffer only)..."
        )
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

    def stop_logger(self) -> None:
        if self.keylogger:
            self.keylogger.stop()

        self.status_label.configure(text="● Demonstration stopped")
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

    # --------------------------------------------------------------
    # Callbacks
    # --------------------------------------------------------------

    def key_callback(self, key_data: str) -> None:
        self.key_queue.put(key_data)

    def clear_text(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")