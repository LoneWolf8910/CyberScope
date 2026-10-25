"""Packet capture engine for CyberScope.

Wraps Scapy's sniff() in a background thread with a thread-safe queue,
interface listing, graceful start/stop, and duplicate-capture prevention.
"""

from __future__ import annotations

import threading
from queue import Queue, Full
from typing import Callable, List, Optional

from scapy.all import get_if_list, sniff
from scapy.packet import Packet

from core.packet_parser import PacketParser
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Maximum queued packets before dropping (backpressure).
MAX_QUEUE_SIZE = 1000


class PacketCapture:
    """Manages live packet capture on a network interface.

    Parameters
    ----------
    callback : callable, optional
        Function called (on the GUI thread via queue) with each parsed
        packet dict.
    interface : str, optional
        Network interface to capture on. If ``None``, Scapy uses its
        default interface.
    bpf_filter : str, optional
        Scapy BPF filter string (e.g. ``"tcp port 80"``).
    """

    def __init__(
        self,
        callback: Optional[Callable[[dict], None]] = None,
        interface: Optional[str] = None,
        bpf_filter: Optional[str] = None,
    ):
        self.callback = callback
        self.interface = interface
        self.bpf_filter = bpf_filter

        self._queue: Queue = Queue(maxsize=MAX_QUEUE_SIZE)
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._stop_event = threading.Event()

    # ----------------------------------------------------------------
    # Interface discovery
    # ----------------------------------------------------------------

    @staticmethod
    def list_interfaces() -> List[str]:
        """Return a list of available network interface names."""
        try:
            return list(get_if_list())
        except Exception as exc:  # pragma: no cover - platform specific
            logger.error("Failed to list interfaces: %s", exc)
            return []

    # ----------------------------------------------------------------
    # Capture lifecycle
    # ----------------------------------------------------------------

    def start(self) -> bool:
        """Start capture in a background daemon thread.

        Returns ``True`` if capture was started, ``False`` if already
        running.
        """
        if self._thread is not None and self._thread.is_alive():
            logger.warning("Capture already running on %s", self.interface)
            return False

        self._stop_event.clear()
        self._running = True

        self._thread = threading.Thread(
            target=self._capture_loop,
            args=(self.interface,),
            daemon=True,
            name="packet-capture",
        )
        self._thread.start()
        logger.info(
            "Capture started on interface=%s filter=%s",
            self.interface or "default",
            self.bpf_filter or "none",
        )
        return True

    def stop(self) -> None:
        """Request capture shutdown and wait for the thread to exit."""
        if self._thread is None:
            self._running = False
            return

        self._running = False
        self._stop_event.set()

        if self._thread.is_alive():
            self._thread.join(timeout=5)

        self._thread = None
        logger.info("Capture stopped on interface=%s", self.interface)

    @property
    def running(self) -> bool:
        return self._running and (
            self._thread is not None and self._thread.is_alive()
        )

    def request_stop(self) -> None:
        """Request capture shutdown without joining (safe from callback thread)."""
        self._running = False
        self._stop_event.set()

    # ----------------------------------------------------------------
    # Internal capture loop
    # ----------------------------------------------------------------

    def _capture_loop(self, interface: Optional[str]) -> None:
        """Run sniff() repeatedly until stopped (runs in capture thread)."""

        while self._running and not self._stop_event.is_set():
            try:
                sniff(
                    iface=interface,
                    filter=self.bpf_filter,
                    prn=self._process_packet,
                    stop_filter=lambda _: not self._running,
                    timeout=1,
                    store=False,
                )
            except PermissionError:
                logger.error(
                    "Permission denied capturing on interface %s. "
                    "Run with CAP_NET_RAW or as root.",
                    interface,
                )
                self._running = False
                break
            except OSError as exc:
                logger.error("OS error capturing on %s: %s", interface, exc)
                self._running = False
                break
            except Exception as exc:  # noqa: BLE001 - capture thread must not die
                logger.exception("Unexpected capture error: %s", exc)
                self._running = False
                break

    def _process_packet(self, packet: Packet) -> None:
        """Parse a packet and enqueue it for GUI delivery."""
        try:
            data = PacketParser.parse(packet)
            if data is None:
                return

            # Non-blocking enqueue with backpressure drop.
            try:
                self._queue.put_nowait(data)
            except Full:
                logger.debug("Packet queue full, dropping packet")

            # Deliver to callback (must be thread-safe / queue-based).
            if self.callback:
                try:
                    self.callback(data)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Callback error: %s", exc)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Packet processing error: %s", exc)

    # ----------------------------------------------------------------
    # Queue draining (for GUI polling)
    # ----------------------------------------------------------------

    def drain_queue(self) -> List[dict]:
        """Drain all pending packets from the queue (call from GUI thread)."""
        packets: List[dict] = []
        while True:
            try:
                packets.append(self._queue.get_nowait())
            except Exception:
                break
        return packets
