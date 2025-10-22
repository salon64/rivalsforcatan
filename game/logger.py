# logger.py
class Logger:
    def on_event(self, event_type, payload):
        print(f"[LOG] {event_type}: {payload}")
