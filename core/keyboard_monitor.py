import threading

from pynput import keyboard


class KeyLogger:
    """Keyboard listener that reports each key press through a callback.

    Parameters
    ----------
    callback : callable, optional
        Function called with a string representation of each pressed key.
    host : str
        Keylogger server host (kept for API compatibility).
    port : int
        Keylogger server port (kept for API compatibility).
    interval : int
        Send interval in seconds (kept for API compatibility).
    """

    def __init__(self, callback=None, host="127.0.0.1", port=8080, interval=10):
        self.callback = callback
        self.host = host
        self.port = port
        self.interval = interval

        self.text = ""
        self.stop_event = threading.Event()
        self.timer = None

        self.listener = keyboard.Listener(on_press=self._on_press)

    # ------------------------------------------------------------------
    # Key processing
    # ------------------------------------------------------------------

    def _format_key(self, key):
        """Return a printable string for a pynput key, or None to ignore it."""

        if key == keyboard.Key.enter:
            return "\n"
        if key == keyboard.Key.tab:
            return "\t"
        if key == keyboard.Key.space:
            return " "

        ignore_keys = {
            keyboard.Key.shift,
            keyboard.Key.shift_l,
            keyboard.Key.shift_r,
            keyboard.Key.ctrl_l,
            keyboard.Key.ctrl_r,
            keyboard.Key.alt_l,
            keyboard.Key.alt_r,
            keyboard.Key.cmd,
            keyboard.Key.cmd_l,
            keyboard.Key.cmd_r,
            keyboard.Key.caps_lock,
        }
        if key in ignore_keys:
            return None

        if key == keyboard.Key.backspace:
            self.text = self.text[:-1] if self.text else ""
            return None

        if key == keyboard.Key.esc:
            return "ESC"

        # Regular character keys
        return str(key).strip("'")

    def _on_press(self, key):
        key_data = self._format_key(key)

        # Special-case ESC: stop the listener
        if key == keyboard.Key.esc:
            return False

        if key_data is None:
            return

        self.text += key_data

        if self.callback:
            self.callback(key_data)

    # ------------------------------------------------------------------
    # Start / Stop
    # ------------------------------------------------------------------

    def start(self):
        self.stop_event.clear()
        self.listener.start()

    def stop(self):
        self.stop_event.set()
        if self.timer:
            self.timer.cancel()
        if self.listener.running:
            self.listener.stop()