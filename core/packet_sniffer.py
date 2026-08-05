import threading

from scapy.all import sniff
from core.packet_parser import PacketParser


class PacketSniffer:

    def __init__(self, callback):

        self.callback = callback

        self.running = False

        self.thread = None

    # =====================================
    # Packet Processing
    # =====================================

    def process_packet(self, packet):

        data = PacketParser.parse(packet)

        if data is None:
            return

        self.callback(data)

    # =====================================
    # Capture Loop
    # =====================================

    def capture(self, interface):

        self.running = True

        while self.running:

            sniff(
                iface=interface,
                prn=self.process_packet,
                timeout=1,
                store=False
            )

    # =====================================
    # Start Capture
    # =====================================

    def start(self, interface):

        if self.thread is not None:

            if self.thread.is_alive():

                return

        self.thread = threading.Thread(
            target=self.capture,
            args=(interface,),
            daemon=True
        )

        self.thread.start()

    # =====================================
    # Stop Capture
    # =====================================

    def stop(self):

        self.running = False