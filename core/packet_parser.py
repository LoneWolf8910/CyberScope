"""Enhanced packet parser for CyberScope.

Parses IPv4, IPv6, TCP, UDP, ICMP, ICMPv6, ARP and other packet types
using Scapy. Gracefully handles packets with missing or malformed layers.
"""

from __future__ import annotations

from typing import Optional

from scapy.layers.inet import IP, TCP, UDP, ICMP
from scapy.layers.inet6 import IPv6, ICMPv6EchoRequest, ICMPv6EchoReply
from scapy.layers.l2 import ARP
from scapy.packet import Packet


class PacketParser:
    """Static packet parser that converts Scapy packets into plain dicts."""

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------

    @staticmethod
    def parse(packet: Packet) -> Optional[dict]:
        """Parse a Scapy packet into a dictionary.

        Parameters
        ----------
        packet : scapy.packet.Packet
            The raw Scapy packet to parse.

        Returns
        -------
        dict or None
            A dictionary with packet metadata, or ``None`` if the packet
            cannot be parsed at all (e.g. no network layer).
        """

        if packet is None:
            return None

        data: dict = {
            "src": "-",
            "dst": "-",
            "ttl": "-",
            "length": len(packet),
            "protocol": "OTHER",
            "sport": "-",
            "dport": "-",
            "info": "",
            "src_ip": "-",
            "dst_ip": "-",
        }

        # ------------------------------------------------------------
        # ARP
        # ------------------------------------------------------------
        if ARP in packet:
            data["protocol"] = "ARP"
            data["src"] = packet[ARP].psrc
            data["dst"] = packet[ARP].pdst
            data["src_ip"] = packet[ARP].psrc
            data["dst_ip"] = packet[ARP].pdst
            op = packet[ARP].op
            op_name = {1: "request", 2: "reply"}.get(int(op), f"op={op}")
            data["info"] = f"ARP {op_name} {packet[ARP].hwsrc} -> {packet[ARP].hwdst}"
            return data

        # ------------------------------------------------------------
        # IPv6
        # ------------------------------------------------------------
        if IPv6 in packet:
            ipv6 = packet[IPv6]
            data["src"] = ipv6.src
            data["dst"] = ipv6.dst
            data["src_ip"] = ipv6.src
            data["dst_ip"] = ipv6.dst
            data["ttl"] = ipv6.hlim
            data["protocol"] = "IPv6"

            if ICMPv6EchoRequest in packet:
                data["protocol"] = "ICMPv6"
                data["info"] = "ICMPv6 Echo Request"
            elif ICMPv6EchoReply in packet:
                data["protocol"] = "ICMPv6"
                data["info"] = "ICMPv6 Echo Reply"
            elif TCP in packet:
                data["protocol"] = "TCPv6"
                data["sport"] = packet[TCP].sport
                data["dport"] = packet[TCP].dport
                data["info"] = f"TCPv6 {packet[TCP].sport} -> {packet[TCP].dport}"
            elif UDP in packet:
                data["protocol"] = "UDPv6"
                data["sport"] = packet[UDP].sport
                data["dport"] = packet[UDP].dport
                data["info"] = f"UDPv6 {packet[UDP].sport} -> {packet[UDP].dport}"
            return data

        # ------------------------------------------------------------
        # IPv4
        # ------------------------------------------------------------
        if IP not in packet:
            # Non-IP, non-ARP packet (e.g. raw L2).
            data["protocol"] = "L2"
            data["info"] = f"Layer-2 packet ({packet.name})"
            return data

        ip = packet[IP]
        data["src"] = ip.src
        data["dst"] = ip.dst
        data["src_ip"] = ip.src
        data["dst_ip"] = ip.dst
        data["ttl"] = ip.ttl

        if TCP in packet:
            tcp = packet[TCP]
            data["protocol"] = "TCP"
            data["sport"] = tcp.sport
            data["dport"] = tcp.dport
            flags = packet.sprintf("%TCP.flags%")
            data["info"] = f"TCP {tcp.sport} -> {tcp.dport} Flags={flags}"

            # Detect DNS over TCP (port 53)
            if tcp.sport == 53 or tcp.dport == 53:
                data["protocol"] = "DNS"

        elif UDP in packet:
            udp = packet[UDP]
            data["protocol"] = "UDP"
            data["sport"] = udp.sport
            data["dport"] = udp.dport
            data["info"] = f"UDP {udp.sport} -> {udp.dport}"

            # Detect DNS over UDP (port 53)
            if udp.sport == 53 or udp.dport == 53:
                data["protocol"] = "DNS"

        elif ICMP in packet:
            data["protocol"] = "ICMP"
            data["info"] = "ICMP packet"
        else:
            data["info"] = f"IPv4 proto={ip.proto}"

        return data

    @staticmethod
    def summary(packet: Packet) -> str:
        """Return a one-line human-readable summary of a packet."""
        data = PacketParser.parse(packet)
        if data is None:
            return "unparsable"
        return (
            f"{data['src']}:{data['sport']} -> {data['dst']}:{data['dport']} "
            f"[{data['protocol']}] {data['length']}B"
        )
