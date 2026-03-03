import pandas as pd
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter,
    QFileDialog, QMessageBox, QScrollArea,
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QTimer

from data.session_loader import SessionLoader
from data.comparison_engine import TelemetryComparator
from gui.controls_panel import ControlsPanel
from gui.plot_widget import PlotWidget
from gui.session_selector import (
    EventScheduleWorker,
    SessionLoaderWorker,
    ComparisonWorker,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("F1 Telemetry Comparison")
        self.setMinimumSize(1280, 800)
        self.resize(1440, 900)

        self._loader = SessionLoader()
        self._last_comparator: TelemetryComparator = None
        self._last_driver_a = ""
        self._last_driver_b = ""

        # Workers (kept as instance vars to prevent GC mid-thread)
        self._event_worker:      EventScheduleWorker = None
        self._session_worker:    SessionLoaderWorker = None
        self._comparison_worker: ComparisonWorker    = None

        # Debounce timer for year spinbox
        self._year_timer = QTimer()
        self._year_timer.setSingleShot(True)
        self._year_timer.setInterval(400)
        self._year_timer.timeout.connect(self._fetch_event_schedule)

        self._build_ui()
        self._build_menu()
        self._connect_signals()

        # Kick off initial event schedule load
        self._fetch_event_schedule()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.controls = ControlsPanel()
        root.addWidget(self.controls)

        # Right side: vertical splitter (telemetry plots top, track map bottom)
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(4)
        splitter.setStyleSheet("QSplitter::handle { background: #333; }")

        # Telemetry canvas in a scroll area
        self.plot_widget = PlotWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.plot_widget)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        splitter.addWidget(scroll)
        splitter.addWidget(self.plot_widget.track_canvas)
        splitter.setSizes([620, 260])

        root.addWidget(splitter, stretch=1)

    def _build_menu(self):
        mb = self.menuBar()

        file_menu = mb.addMenu("File")

        act_png = QAction("Export Plots (PNG)…", self)
        act_png.setShortcut("Ctrl+Shift+S")
        act_png.triggered.connect(self._export_png)
        file_menu.addAction(act_png)

        act_csv = QAction("Export Data (CSV)…", self)
        act_csv.triggered.connect(self._export_csv)
        file_menu.addAction(act_csv)

        file_menu.addSeparator()

        act_quit = QAction("Quit", self)
        act_quit.setShortcut("Ctrl+Q")
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

    def _connect_signals(self):
        self.controls.year_spin.valueChanged.connect(
            lambda _: self._year_timer.start()
        )
        self.controls.load_session_requested.connect(self._load_session)
        self.controls.compare_requested.connect(self._run_comparison)

    # ------------------------------------------------------------------
    # Event schedule
    # ------------------------------------------------------------------

    def _fetch_event_schedule(self):
        year = self.controls.year_spin.value()
        self.controls.set_status(f"Fetching {year} schedule…")
        self.controls.set_loading(True)

        self._event_worker = EventScheduleWorker(year, self._loader)
        self._event_worker.schedule_loaded.connect(self._on_schedule_loaded)
        self._event_worker.error_occurred.connect(self._on_worker_error)
        self._event_worker.start()

    def _on_schedule_loaded(self, events: list):
        self.controls.populate_events(events)
        self.controls.set_loading(False)
        self.controls.set_status("Select an event then click Load Session.")

    # ------------------------------------------------------------------
    # Session loading
    # ------------------------------------------------------------------

    def _load_session(self, year: int, event: str, session_type: str):
        self.controls.set_status(f"Loading {event} ({session_type})…")
        self.controls.set_loading(True)

        self._session_worker = SessionLoaderWorker(
            self._loader, year, event, session_type
        )
        self._session_worker.session_loaded.connect(self._on_session_loaded)
        self._session_worker.error_occurred.connect(self._on_worker_error)
        self._session_worker.start()

    def _on_session_loaded(self, _session):
        drivers = self._loader.get_driver_list()
        self.controls.populate_drivers(drivers, self._loader)
        self.controls.set_loading(False)
        self.controls.set_status(
            f"Session loaded ({len(drivers)} drivers). Select drivers and click Compare."
        )

    # ------------------------------------------------------------------
    # Comparison
    # ------------------------------------------------------------------

    def _run_comparison(self, drv_a: str, drv_b: str, lap_a: str, lap_b: str):
        try:
            lap_obj_a = self._loader.get_lap(drv_a, lap_a)
            lap_obj_b = self._loader.get_lap(drv_b, lap_b)
        except ValueError as exc:
            self._show_error(str(exc))
            return

        self._last_driver_a = drv_a
        self._last_driver_b = drv_b
        comparator = TelemetryComparator(lap_obj_a, lap_obj_b)

        self.controls.set_status(f"Comparing {drv_a} vs {drv_b}…")
        self.controls.set_loading(True)

        self._comparison_worker = ComparisonWorker(comparator)
        self._comparison_worker.comparison_done.connect(self._on_comparison_done)
        self._comparison_worker.error_occurred.connect(self._on_worker_error)
        self._comparison_worker.start()

    def _on_comparison_done(self, comparator: TelemetryComparator):
        self._last_comparator = comparator
        self.plot_widget.plot_comparison(
            comparator, self._last_driver_a, self._last_driver_b
        )
        self.controls.set_loading(False)
        self.controls.enable_compare(True)

        total_delta = float(comparator.delta[-1])
        if abs(total_delta) < 0.001:
            summary = "Identical lap times."
        elif total_delta > 0:
            summary = (
                f"{self._last_driver_a} was {abs(total_delta):.3f}s slower overall."
            )
        else:
            summary = (
                f"{self._last_driver_a} was {abs(total_delta):.3f}s faster overall."
            )
        self.controls.set_status(f"Done! {summary}", color="#55cc77")

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    def _on_worker_error(self, message: str):
        self.controls.set_loading(False)
        self.controls.enable_compare(True)
        self.controls.set_status(f"Error: {message}", color="#ff6b6b")
        self._show_error(message)

    def _show_error(self, message: str):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Error")
        dlg.setText(message)
        dlg.setIcon(QMessageBox.Icon.Warning)
        dlg.exec()

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _export_png(self):
        if self._last_comparator is None:
            self._show_error("Run a comparison first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Plots", "telemetry_comparison.png", "PNG Files (*.png)"
        )
        if path:
            try:
                self.plot_widget.export_png(path)
            except Exception as exc:
                self._show_error(str(exc))

    def _export_csv(self):
        if self._last_comparator is None:
            self._show_error("Run a comparison first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Data", "telemetry_comparison.csv", "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            comp = self._last_comparator
            a, b = comp.aligned_a, comp.aligned_b

            data = {"Distance_m": comp.common_dist, "Delta_s": comp.delta}
            for ch in ("Speed", "Throttle", "Brake", "nGear", "RPM", "Steering"):
                if ch in a:
                    data[f"{self._last_driver_a}_{ch}"] = a[ch]
                if ch in b:
                    data[f"{self._last_driver_b}_{ch}"] = b[ch]

            pd.DataFrame(data).to_csv(path, index=False)
        except Exception as exc:
            self._show_error(str(exc))
