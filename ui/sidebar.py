import customtkinter as ctk


class Sidebar(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master, width=220, corner_radius=0)

        self.grid_propagate(False)

        title = ctk.CTkLabel(
            self,
            text="CyberScope",
            font=("JetBrains Mono", 26, "bold")
        )

        title.pack(pady=(35, 40))

        buttons = {
            "Dashboard": master.show_dashboard,
            "Packet Sniffer": master.show_packet_page,
            "Keylogger": master.show_keylogger_page
        }

        for text, command in buttons.items():

            button = ctk.CTkButton(
                self,
                text=text,
                command=command
            )

            button.pack(fill="x", padx=15, pady=8)