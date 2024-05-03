
import threading
import time

class Timer:
    def __init__(self, timeout_ms, callback):
        self.timeout_ms = timeout_ms
        self.timeout_sec = timeout_ms/1000
        self.callback = callback
        self.elapsed_time_ms = 0
        self.running = False
        self.timer_thread = None

    def start(self):
        self.running = True
        self.reset()
        if self.timer_thread:
            self.timer_thread.start()

    def reset(self, new_timeout_ms=None):
        if new_timeout_ms:
            self.timeout_ms = new_timeout_ms
        self.start_t = time.time()
        if self.timer_thread:
            self.timer_thread.cancel()
        self.timer_thread = threading.Timer(
            interval=self.timeout_ms/1000, 
            function=self.on_timeout, 
        )

    def on_timeout(self):
        self.running = False
        self.callback()

    def stop(self):
        self.running = False
        if self.timer_thread:
            self.timer_thread.cancel()

    def remaining_sec(self) -> float:
        # return (self.timeout_ms - self.elapsed_time_ms) / 1000
        if self.running:
            return self.timeout_sec - (time.time() - self.start_t)
        else:
            return 0.0
