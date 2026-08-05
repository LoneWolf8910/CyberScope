import customtkinter as ctk

from ui.stats_cards import StatsCards


class Dashboard(ctk.CTkFrame):

    def __init__(self, master):

        super().__init__(master)

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
            pady=(20,10)
        )

        # self.status_label = ctk.CTkLabel(
        #     status,
        #     text="🟢 Waiting for packet capture...",
        #     font=("JetBrains Mono",16)
        # )

        # self.status_label.pack(
        #     anchor="w",
        #     padx=20
        # )

        # self.bandwidth = ctk.CTkLabel(
        #     status,
        #     text="Bandwidth : 0 KB/s",
        #     font=("JetBrains Mono",15)
        # )

        # self.bandwidth.pack(
        #     anchor="w",
        #     padx=20,
        #     pady=8
        # )

        self.interface = ctk.CTkLabel(
            status,
            text="Interface : Not Selected",
            font=("JetBrains Mono",15)
        )

        self.interface.pack(
            anchor="w",
            padx=20
        )