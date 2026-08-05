import customtkinter as ctk
from tkinter import ttk
from datetime import datetime


# -----------------------------
# Treeview Style
# -----------------------------

style = ttk.Style()
style.theme_use("clam")

style.configure(
    "Treeview",
    background="#2b2b2b",
    foreground="white",
    fieldbackground="#2b2b2b",
    rowheight=30,
    font=("JetBrains Mono", 11)
)

style.configure(
    "Treeview.Heading",
    background="#1976D2",
    foreground="white",
    font=("JetBrains Mono", 11, "bold")
)

style.map(
    "Treeview",
    background=[("selected", "#1565C0")]
)


class PacketTable(ctk.CTkFrame):

    def __init__(self, master):

        super().__init__(master)

        title = ctk.CTkLabel(
            self,
            text="Live Packet Capture",
            font=("JetBrains Mono", 22, "bold")
        )

        title.pack(anchor="w", padx=15, pady=(15, 10))

        # -----------------------------
        # Search + Filter
        # -----------------------------

        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=15)

        self.search = ctk.CTkEntry(
            top,
            placeholder_text="Search..."
        )

        self.search.pack(side="left", padx=10)

        self.filter = ctk.CTkOptionMenu(
            top,
            values=[
                "All",
                "TCP",
                "UDP",
                "ICMP"
            ]
        )

        self.filter.pack(side="right", padx=10)

        # -----------------------------
        # Table
        # -----------------------------

        columns = (
            "Time",
            "Source",
            "Destination",
            "Protocol",
            "Src Port",
            "Dst Port",
            "TTL",
            "Length",
            "Info"
        )

        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=15, pady=15)

        self.table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        widths = {
            "Time":100,
            "Source":170,
            "Destination":170,
            "Protocol":90,
            "Src Port":80,
            "Dst Port":80,
            "TTL":60,
            "Length":70,
            "Info":220
        }

        for col in columns:

            self.table.heading(col, text=col)

            self.table.column(
                col,
                width=widths[col],
                anchor="center"
            )

        scroll = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.table.yview
        )

        self.table.configure(
            yscrollcommand=scroll.set
        )

        scroll.pack(
            side="right",
            fill="y"
        )

        self.table.pack(
            fill="both",
            expand=True
        )

        # Row Colors

        self.table.tag_configure(
            "odd",
            background="#2B2B2B"
        )

        self.table.tag_configure(
            "even",
            background="#353535"
        )

    # ------------------------------------
    # Add Packet
    # ------------------------------------

    def add_packet(self, data):

        now = datetime.now().strftime("%H:%M:%S")

        count = len(self.table.get_children())

        tag = "even" if count % 2 == 0 else "odd"

        self.table.insert(
            "",
            "end",
            values=(
                now,
                data["src"],
                data["dst"],
                data["protocol"],
                data["sport"],
                data["dport"],
                data["ttl"],
                data["length"],
                data["info"]
            ),
            tags=(tag,)
        )

        children = self.table.get_children()

        if children:
            self.table.see(children[-1])

    # ------------------------------------
    # Clear
    # ------------------------------------

    def clear(self):

        for row in self.table.get_children():
            self.table.delete(row)