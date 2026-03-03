from PyQt6.QtCore import QThread, pyqtSignal

from data.session_loader import SessionLoader
from data.comparison_engine import TelemetryComparator


class EventScheduleWorker(QThread):
    """Fetches the event schedule for a given year in a background thread."""

    schedule_loaded = pyqtSignal(list)   # list[str] of event names
    error_occurred = pyqtSignal(str)

    def __init__(self, year: int, loader: SessionLoader):
        super().__init__()
        self._year = year
        self._loader = loader

    def run(self):
        try:
            events = self._loader.get_event_schedule(self._year)
            self.schedule_loaded.emit(events)
        except Exception as exc:
            self.error_occurred.emit(str(exc))


class SessionLoaderWorker(QThread):
    """Loads a FastF1 session (network + cache) in a background thread."""

    session_loaded = pyqtSignal(object)  # the loaded session
    error_occurred = pyqtSignal(str)

    def __init__(self, loader: SessionLoader, year: int, event: str, session_type: str):
        super().__init__()
        self._loader = loader
        self._year = year
        self._event = event
        self._session_type = session_type

    def run(self):
        try:
            session = self._loader.load_session(
                self._year, self._event, self._session_type
            )
            self.session_loaded.emit(session)
        except Exception as exc:
            self.error_occurred.emit(str(exc))


class ComparisonWorker(QThread):
    """Runs telemetry alignment and delta computation in a background thread."""

    comparison_done = pyqtSignal(object)  # the completed TelemetryComparator
    error_occurred = pyqtSignal(str)

    def __init__(self, comparator: TelemetryComparator):
        super().__init__()
        self._comparator = comparator

    def run(self):
        try:
            self._comparator.run()
            self.comparison_done.emit(self._comparator)
        except Exception as exc:
            self.error_occurred.emit(str(exc))
