"""Statistics engine for CyberScope.

Tracks live packet counters, protocol breakdown, rolling rate, and total
bytes. Provides dashboard data and CSV export.
"""

from __future__ import annotations

import csv
import io
import time
from collections import defaultdict
from typing import Dict, List


class Statistics:
    """Thread-safe-ish statistics tracker (updated from GUI main thread)."""

    def __init__(self) -> None:
        self.reset()
        self._start_time = time.time()

    # ----------------------------------------------------------------
    # Reset
    # ----------------------------------------------------------------

    def reset(self) -> None:
        self.total_packets = 0
        self.total_bytes = 0
        self.protocols: Dict[str, int] = defaultdict(int)
        self._timestamps: List[float] = []

    # ----------------------------------------------------------------
    # Update
    # ----------------------------------------------------------------

    def update(self, packet: dict) -> None:
        """Record a parsed packet."""

        self.total_packets += 1
        self.total_bytes += int(packet.get("length", 0))

        proto = packet.get("protocol", "OTHER")
        self.protocols[proto] += 1

        self._timestamps.append(time.time())

    # ----------------------------------------------------------------
    # Dashboard data
    # ----------------------------------------------------------------

    def get_dashboard_data(self) -> dict:
        """Return the dashboard stat-card values."""

        return {
            "Packets": self.total_packets,
            "TCP": self.protocols.get("TCP", 0),
            "UDP": self.protocols.get("UDP", 0),
            "ICMP": self.protocols.get("ICMP", 0),
            "DNS": self.protocols.get("DNS", 0),
            "Bytes": self.total_bytes,
        }

    def get_protocol_distribution(self) -> dict:
        """Return protocol counts for charting."""
        return dict(self.protocols)

    # ----------------------------------------------------------------
    # Rolling packet rate (packets per second)
    # ----------------------------------------------------------------

    def get_packet_rate(self, window: float = 1.0) -> float:
        """Return packets per second over the last ``window`` seconds."""
        now = time.time()
        cutoff = now - window
        recent = [t for t in self._timestamps if t >= cutoff]
        # Trim old timestamps to avoid unbounded growth.
        self._timestamps = recent
        return len(recent) / window if window > 0 else 0.0

    # ----------------------------------------------------------------
    # CSV export
    # ----------------------------------------------------------------

    def to_csv_rows(self, packets: List[dict]) -> List[dict]:
        """Normalize packets into CSV-ready rows (metadata only)."""
        rows = []
        for p in packets:
            rows.append(
                {
                    "time": p.get("time", ""),
                    "source": p.get("src", "-"),
                    "destination": p.get("dst", "-"),
                    "protocol": p.get("protocol", "OTHER"),
                    "src_port": p.get("sport", "-"),
                    "dst_port": p.get("dport", "-"),
                    "ttl": p.get("ttl", "-"),
                    "length": p.get("length", "-"),
                    "info": p.get("info", ""),
                }
            )
        return rows

    @staticmethod
    def rows_to_csv_string(rows: List[dict]) -> str:
        """Serialize CSV rows to a properly escaped CSV string."""
        if not rows:
            return ""
        fieldnames = [
            "time",
            "source",
            "destination",
            "protocol",
            "src_port",
            "dst_port",
            "ttl",
            "length",
            "info",
        ]
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        return buffer.getvalue()
