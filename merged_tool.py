"""Command-line interface for CyberScope.

Runs the packet sniffer and/or keylogger demonstration from the terminal
without the GUI. Keylogging is never started automatically — it must be
explicitly requested with ``--keylogger``.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from typing import List, Optional

from core.packet_capture import PacketCapture
from core.packet_parser import PacketParser
from core.statistics import Statistics
from utils.logging_config import setup_logging, get_logger

logger = get_logger(__name__)

__version__ = "1.0.0"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CyberScope — packet capture and keystroke demo CLI",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"CyberScope {__version__}",
    )
    parser.add_argument(
        "--list-interfaces",
        action="store_true",
        help="List available network interfaces and exit.",
    )
    parser.add_argument(
        "--interface",
        help="Network interface to sniff (default: Scapy default).",
    )
    parser.add_argument(
        "--filter",
        dest="bpf_filter",
        help="Scapy BPF capture filter (e.g. 'tcp port 80').",
    )
    parser.add_argument(
        "--output",
        help="Write captured packets to this CSV file.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=0,
        help="Stop after capturing this many packets (0 = unlimited).",
    )
    parser.add_argument(
        "--keylogger",
        action="store_true",
        help="Run the keystroke-monitoring demonstration (explicit opt-in).",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=10,
        help="Keylogger buffer flush interval in seconds (demo only).",
    )
    return parser


def print_packet(data: dict, stats: Statistics) -> None:
    """Print one parsed packet and update stats."""
    stats.update(data)
    line = (
        f"{data.get('time', '-')} "
        f"{data.get('src', '-'):<16} -> {data.get('dst', '-'):<16} "
        f"[{data.get('protocol', 'OTHER'):<6}] "
        f"{data.get('sport', '-'):>5} -> {data.get('dport', '-'):<5} "
        f"{data.get('length', '-')}B "
        f"{data.get('info', '')}"
    )
    print(line)


def main(argv: Optional[List[str]] = None) -> int:
    setup_logging()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_interfaces:
        ifaces = PacketCapture.list_interfaces()
        if not ifaces:
            print("No network interfaces found.")
            return 1
        print("Available network interfaces:")
        for iface in ifaces:
            print(f"  - {iface}")
        return 0

    stats = Statistics()
    captured: List[dict] = []

    def on_packet(data: dict) -> None:
        data["time"] = time.strftime("%H:%M:%S")
        captured.append(data)
        print_packet(data, stats)

        if args.count > 0 and len(captured) >= args.count:
            # Signal stop; main loop will exit and call stop().
            capture.request_stop()

    capture = PacketCapture(
        callback=on_packet,
        interface=args.interface,
        bpf_filter=args.bpf_filter,
    )

    keylogger = None
    if args.keylogger:
        from core.keyboard_monitor import KeyLogger

        keylogger = KeyLogger(
            callback=lambda k: print(f"[KEY] {k}"),
            interval=args.interval,
        )
        keylogger.start()
        logger.info("Keylogger demonstration started (explicit opt-in)")

    try:
        capture.start()
        iface_text = args.interface or "default"
        print(
            f"Capture started on {iface_text}"
            + (f" filter='{args.bpf_filter}'" if args.bpf_filter else "")
        )
        print("Press Ctrl+C to stop.\n")

        while capture.running:
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nStopping capture...")
    finally:
        capture.stop()
        if keylogger:
            keylogger.stop()

    # Summary
    print("\n--- Capture Summary ---")
    print(f"Total packets: {stats.total_packets}")
    print(f"Total bytes: {stats.total_bytes}")
    for proto, count in sorted(stats.get_protocol_distribution().items()):
        print(f"  {proto}: {count}")

    # CSV export
    if args.output and captured:
        rows = stats.to_csv_rows(captured)
        csv_text = Statistics.rows_to_csv_string(rows)
        try:
            with open(args.output, "w", encoding="utf-8", newline="") as f:
                f.write(csv_text)
            print(f"\nExported {len(rows)} packets to {args.output}")
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to write CSV: %s", exc)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
