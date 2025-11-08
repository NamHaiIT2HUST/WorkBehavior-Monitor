import threading
import time

class SessionMonitor:
    def __init__(self, break_interval, on_break_reminder=None):
        self.break_interval = break_interval  # seconds
        self.on_break_reminder = on_break_reminder
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _run(self):
        last_break = time.time()
        while not self._stop_event.is_set():
            if time.time() - last_break >= self.break_interval:
                if self.on_break_reminder:
                    self.on_break_reminder()
                last_break = time.time()
            time.sleep(1)
