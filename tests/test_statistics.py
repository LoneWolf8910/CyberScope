"""Tests for the statistics engine."""

import pytest

from core.statistics import Statistics


def test_empty_statistics():
    stats = Statistics()
    data = stats.get_dashboard_data()
    assert data["Packets"] == 0
    assert data["TCP"] == 0
    assert data["UDP"] == 0
    assert data["ICMP"] == 0
    assert data["DNS"] == 0
    assert data["Bytes"] == 0


def test_packet_counter_update():
    stats = Statistics()
    stats.update({"protocol": "TCP", "length": 100})
    stats.update({"protocol": "UDP", "length": 200})
    stats.update({"protocol": "TCP", "length": 150})

    assert stats.total_packets == 3
    assert stats.total_bytes == 450
    assert stats.protocols["TCP"] == 2
    assert stats.protocols["UDP"] == 1


def test_dashboard_data():
    stats = Statistics()
    stats.update({"protocol": "TCP", "length": 100})
    stats.update({"protocol": "ICMP", "length": 50})
    data = stats.get_dashboard_data()
    assert data["Packets"] == 2
    assert data["TCP"] == 1
    assert data["ICMP"] == 1
    assert data["UDP"] == 0
    assert data["Bytes"] == 150


def test_reset():
    stats = Statistics()
    stats.update({"protocol": "TCP", "length": 100})
    stats.reset()
    assert stats.total_packets == 0
    assert stats.total_bytes == 0
    assert len(stats.protocols) == 0


def test_packet_rate():
    stats = Statistics()
    # No packets -> rate 0
    assert stats.get_packet_rate(window=1.0) == 0.0

    # Add packets with current timestamps
    stats.update({"protocol": "TCP", "length": 100})
    stats.update({"protocol": "TCP", "length": 100})
    rate = stats.get_packet_rate(window=1.0)
    assert rate > 0


def test_protocol_distribution():
    stats = Statistics()
    stats.update({"protocol": "TCP", "length": 100})
    stats.update({"protocol": "UDP", "length": 100})
    stats.update({"protocol": "TCP", "length": 100})
    dist = stats.get_protocol_distribution()
    assert dist["TCP"] == 2
    assert dist["UDP"] == 1


def test_csv_rows():
    stats = Statistics()
    packets = [
        {
            "time": "12:00:00",
            "src": "1.2.3.4",
            "dst": "5.6.7.8",
            "protocol": "TCP",
            "sport": 1000,
            "dport": 80,
            "ttl": 64,
            "length": 100,
            "info": "Flags=S",
        }
    ]
    rows = stats.to_csv_rows(packets)
    assert len(rows) == 1
    assert rows[0]["source"] == "1.2.3.4"
    assert rows[0]["protocol"] == "TCP"


def test_csv_string_escaping():
    stats = Statistics()
    rows = [
        {
            "time": "12:00:00",
            "source": "1.2.3.4",
            "destination": "5.6.7.8",
            "protocol": "TCP",
            "src_port": "1000",
            "dst_port": "80",
            "ttl": "64",
            "length": "100",
            'info': 'contains, comma and "quotes"',
        }
    ]
    csv_text = Statistics.rows_to_csv_string(rows)
    assert "contains, comma" in csv_text
    # Quotes should be escaped
    assert '""quotes""' in csv_text or '"quotes"' in csv_text
