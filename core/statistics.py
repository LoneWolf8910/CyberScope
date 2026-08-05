from collections import defaultdict


class Statistics:

    def __init__(self):

        self.reset()

    # ----------------------------------------
    # Reset Statistics
    # ----------------------------------------

    def reset(self):

        self.total_packets = 0

        self.protocols = defaultdict(int)

        self.total_bytes = 0

        self.packet_rate = 0

        self.last_second_packets = 0

    # ----------------------------------------
    # Update Statistics
    # ----------------------------------------

    def update(self, packet):

        self.total_packets += 1

        self.total_bytes += packet["length"]

        proto = packet["protocol"]

        self.protocols[proto] += 1

        self.last_second_packets += 1

    # ----------------------------------------
    # Dashboard Values
    # ----------------------------------------

    def get_dashboard_data(self):

        return {

            "Packets": self.total_packets,

            "TCP": self.protocols["TCP"],

            "UDP": self.protocols["UDP"],

            "ICMP": self.protocols["ICMP"],

            "DNS": self.protocols["DNS"],

            "Bytes": self.total_bytes
        }