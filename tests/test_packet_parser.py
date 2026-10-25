"""Tests for the packet parser using synthetic Scapy packets."""

import pytest

from scapy.layers.inet import IP, TCP, UDP, ICMP
from scapy.layers.inet6 import IPv6
from scapy.layers.l2 import ARP
from scapy.packet import Raw

from core.packet_parser import PacketParser


def _build_packet(layers):
    """Stack Scapy layers and return a packet object."""
    pkt = layers[0]
    for layer in layers[1:]:
        pkt = pkt / layer
    return pkt


# ----------------------------------------------------------------
# IPv4 / TCP
# ----------------------------------------------------------------

def test_tcp_packet_parsing():
    pkt = _build_packet([IP(src="10.0.0.1", dst="10.0.0.2"), TCP(sport=12345, dport=80)])
    data = PacketParser.parse(pkt)
    assert data is not None
    assert data["protocol"] == "TCP"
    assert data["src"] == "10.0.0.1"
    assert data["dst"] == "10.0.0.2"
    assert data["sport"] == 12345
    assert data["dport"] == 80
    assert data["length"] > 0


def test_tcp_flags_present():
    pkt = _build_packet([IP(src="1.2.3.4", dst="5.6.7.8"), TCP(sport=443, dport=54321, flags="SA")])
    data = PacketParser.parse(pkt)
    assert data is not None
    assert "Flags=" in data["info"]


# ----------------------------------------------------------------
# IPv4 / UDP
# ----------------------------------------------------------------

def test_udp_packet_parsing():
    pkt = _build_packet([IP(src="10.0.0.1", dst="10.0.0.2"), UDP(sport=5000, dport=53)])
    data = PacketParser.parse(pkt)
    assert data is not None
    assert data["protocol"] == "DNS"  # port 53 detected
    assert data["sport"] == 5000
    assert data["dport"] == 53


def test_udp_non_dns():
    pkt = _build_packet([IP(src="10.0.0.1", dst="10.0.0.2"), UDP(sport=4000, dport=4001)])
    data = PacketParser.parse(pkt)
    assert data is not None
    assert data["protocol"] == "UDP"


# ----------------------------------------------------------------
# IPv4 / ICMP
# ----------------------------------------------------------------

def test_icmp_packet_parsing():
    pkt = _build_packet([IP(src="10.0.0.1", dst="10.0.0.2"), ICMP()])
    data = PacketParser.parse(pkt)
    assert data is not None
    assert data["protocol"] == "ICMP"


# ----------------------------------------------------------------
# ARP
# ----------------------------------------------------------------

def test_arp_packet_parsing():
    pkt = ARP(psrc="10.0.0.1", pdst="10.0.0.2", hwsrc="aa:bb:cc:dd:ee:ff", hwdst="00:11:22:33:44:55", op=1)
    data = PacketParser.parse(pkt)
    assert data is not None
    assert data["protocol"] == "ARP"
    assert data["src"] == "10.0.0.1"
    assert data["dst"] == "10.0.0.2"
    assert "request" in data["info"]


# ----------------------------------------------------------------
# IPv6
# ----------------------------------------------------------------

def test_ipv6_packet_parsing():
    pkt = _build_packet([IPv6(src="2001:db8::1", dst="2001:db8::2"), TCP(sport=1000, dport=443)])
    data = PacketParser.parse(pkt)
    assert data is not None
    assert data["protocol"] == "TCPv6"
    assert data["src"] == "2001:db8::1"
    assert data["dst"] == "2001:db8::2"


# ----------------------------------------------------------------
# Missing / malformed layers
# ----------------------------------------------------------------

def test_packet_without_ip_returns_none_or_l2():
    # A raw packet with no network layer should not crash.
    pkt = Raw(load=b"\x00\x01\x02\x03")
    data = PacketParser.parse(pkt)
    # Should return a dict (L2) or None — never crash.
    assert data is None or isinstance(data, dict)


def test_none_packet_returns_none():
    assert PacketParser.parse(None) is None


def test_missing_layers_no_crash():
    # IP layer without transport should still parse.
    pkt = IP(src="1.2.3.4", dst="5.6.7.8")
    data = PacketParser.parse(pkt)
    assert data is not None
    assert data["protocol"] == "IPv4" or data["protocol"] in ("OTHER", "IPv4")


# ----------------------------------------------------------------
# Summary helper
# ----------------------------------------------------------------

def test_summary_string():
    pkt = _build_packet([IP(src="1.2.3.4", dst="5.6.7.8"), TCP(sport=1000, dport=80)])
    summary = PacketParser.summary(pkt)
    assert "1.2.3.4" in summary
    assert "5.6.7.8" in summary
    assert "TCP" in summary
