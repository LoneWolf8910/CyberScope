from scapy.layers.inet import IP, TCP, UDP, ICMP


class PacketParser:

    @staticmethod
    def parse(packet):

        if IP not in packet:
            return None

        data = {
            "src": packet[IP].src,
            "dst": packet[IP].dst,
            "ttl": packet[IP].ttl,
            "length": len(packet),
            "protocol": "OTHER",
            "sport": "-",
            "dport": "-",
            "info": ""
        }

        if TCP in packet:

            data["protocol"] = "TCP"
            data["sport"] = packet[TCP].sport
            data["dport"] = packet[TCP].dport

            flags = packet.sprintf("%TCP.flags%")
            data["info"] = f"Flags={flags}"

        elif UDP in packet:

            data["protocol"] = "UDP"
            data["sport"] = packet[UDP].sport
            data["dport"] = packet[UDP].dport
            data["info"] = "UDP Packet"

        elif ICMP in packet:

            data["protocol"] = "ICMP"
            data["info"] = "Echo"

        return data