import customtkinter as ctk


class StatsCards(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        self.grid_columnconfigure((0, 1, 2), weight=1)

        self.cards = {}

        items = [
            ("Packets", "0"),
            ("TCP", "0"),
            ("UDP", "0"),
            ("DNS", "0"),
            ("ICMP", "0"),
            ("Bytes", "0 B")
        ]

        row = 0
        col = 0

        for title, value in items:

            card = ctk.CTkFrame(
                self,
                corner_radius=15,
                height=120
            )

            card.grid(
                row=row,
                column=col,
                padx=12,
                pady=12,
                sticky="nsew"
            )

            title_label = ctk.CTkLabel(
                card,
                text=title,
                font=("JetBrains Mono", 18, "bold")
            )

            title_label.pack(pady=(18, 8))

            value_label = ctk.CTkLabel(
                card,
                text=value,
                font=("JetBrains Mono", 28, "bold")
            )

            value_label.pack()

            self.cards[title] = value_label

            col += 1

            if col == 3:
                col = 0
                row += 1

    # -----------------------------------------
    # Update Cards
    # -----------------------------------------

    def update_stats(self, stats):

        self.cards["Packets"].configure(
            text=str(stats["Packets"])
        )

        self.cards["TCP"].configure(
            text=str(stats["TCP"])
        )

        self.cards["UDP"].configure(
            text=str(stats["UDP"])
        )

        self.cards["DNS"].configure(
            text=str(stats["DNS"])
        )

        self.cards["ICMP"].configure(
            text=str(stats["ICMP"])
        )

        bytes_count = stats["Bytes"]

        if bytes_count < 1024:
            text = f"{bytes_count} B"

        elif bytes_count < 1024 * 1024:
            text = f"{bytes_count/1024:.1f} KB"

        else:
            text = f"{bytes_count/(1024*1024):.2f} MB"

        self.cards["Bytes"].configure(text=text)