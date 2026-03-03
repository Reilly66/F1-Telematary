import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QSpinBox,
    QPushButton, QGroupBox, QProgressBar, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

_CURRENT_YEAR = datetime.date.today().year

SESSION_TYPES = [
    ("Race",              "R"),
    ("Qualifying",        "Q"),
    ("Practice 1",        "FP1"),
    ("Practice 2",        "FP2"),
    ("Practice 3",        "FP3"),
    ("Sprint",            "S"),
    ("Sprint Qualifying", "SQ"),
]


class ControlsPanel(QWidget):
    """Left-hand sidebar: all dropdowns, buttons and status display."""

    load_session_requested = pyqtSignal(int, str, str)    # year, event, session_type
    compare_requested      = pyqtSignal(str, str, str, str)  # drv_a, drv_b, lap_a, lap_b

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(250)
        self._session_loader = None
        self._setup_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(10, 12, 10, 12)

        # Header
        title = QLabel("F1 Telemetry")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f = QFont(); f.setBold(True); f.setPointSize(15)
        title.setFont(f)
        title.setStyleSheet("color: #E8002D;")
        root.addWidget(title)

        sub = QLabel("Comparison Tool")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: #666; font-size: 10px;")
        root.addWidget(sub)

        root.addWidget(_divider())

        # --- Session group ---
        sg, sl = _group("Session")
        sl.addWidget(_label("Year"))
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2018, _CURRENT_YEAR)
        self.year_spin.setValue(_CURRENT_YEAR - 1)
        sl.addWidget(self.year_spin)

        sl.addWidget(_label("Event"))
        self.event_combo = QComboBox()
        self.event_combo.addItem("— load events first —")
        sl.addWidget(self.event_combo)

        sl.addWidget(_label("Session"))
        self.session_combo = QComboBox()
        for label, code in SESSION_TYPES:
            self.session_combo.addItem(label, code)
        self.session_combo.setCurrentIndex(1)  # default: Qualifying
        sl.addWidget(self.session_combo)

        self.load_btn = QPushButton("Load Session")
        self.load_btn.setObjectName("load_btn")
        self.load_btn.clicked.connect(self._emit_load)
        sl.addWidget(self.load_btn)
        root.addWidget(sg)

        # --- Drivers group ---
        dg, dl = _group("Drivers")

        dl.addWidget(_label("Driver A"))
        self.driver_a_combo = QComboBox()
        self.driver_a_combo.setEnabled(False)
        dl.addWidget(self.driver_a_combo)

        dl.addWidget(_label("Lap A"))
        self.lap_a_combo = QComboBox()
        self.lap_a_combo.setEnabled(False)
        dl.addWidget(self.lap_a_combo)

        dl.addWidget(_label("Driver B"))
        self.driver_b_combo = QComboBox()
        self.driver_b_combo.setEnabled(False)
        dl.addWidget(self.driver_b_combo)

        dl.addWidget(_label("Lap B"))
        self.lap_b_combo = QComboBox()
        self.lap_b_combo.setEnabled(False)
        dl.addWidget(self.lap_b_combo)

        root.addWidget(dg)

        # Compare button
        self.compare_btn = QPushButton("Compare")
        self.compare_btn.setObjectName("compare_btn")
        self.compare_btn.setEnabled(False)
        self.compare_btn.clicked.connect(self._emit_compare)
        root.addWidget(self.compare_btn)

        root.addWidget(_divider())

        # Status / progress
        self.status_label = QLabel("Select a year and load a session to begin.")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #777; font-size: 9px;")
        root.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(6)
        root.addWidget(self.progress_bar)

        root.addStretch()

        # Wire driver combos to lap updates
        self.driver_a_combo.currentTextChanged.connect(
            lambda d: self._refresh_laps(d, self.lap_a_combo)
        )
        self.driver_b_combo.currentTextChanged.connect(
            lambda d: self._refresh_laps(d, self.lap_b_combo)
        )

    # ------------------------------------------------------------------
    # Signal emitters
    # ------------------------------------------------------------------

    def _emit_load(self):
        year  = self.year_spin.value()
        event = self.event_combo.currentText()
        stype = self.session_combo.currentData()
        if event and not event.startswith("—"):
            self.load_session_requested.emit(year, event, stype)

    def _emit_compare(self):
        drv_a = self.driver_a_combo.currentText()
        drv_b = self.driver_b_combo.currentText()
        lap_a = self.lap_a_combo.currentText()
        lap_b = self.lap_b_combo.currentText()
        if drv_a and drv_b:
            self.compare_requested.emit(drv_a, drv_b, lap_a, lap_b)

    # ------------------------------------------------------------------
    # Public API called by MainWindow
    # ------------------------------------------------------------------

    def populate_events(self, events: list[str]):
        self.event_combo.clear()
        for e in events:
            self.event_combo.addItem(e)

    def populate_drivers(self, drivers: list[str], session_loader):
        self._session_loader = session_loader

        # Disconnect to avoid stale callbacks during repopulation
        try:
            self.driver_a_combo.currentTextChanged.disconnect()
            self.driver_b_combo.currentTextChanged.disconnect()
        except TypeError:
            pass

        self.driver_a_combo.clear()
        self.driver_b_combo.clear()
        for d in drivers:
            self.driver_a_combo.addItem(d)
            self.driver_b_combo.addItem(d)
        if len(drivers) >= 2:
            self.driver_b_combo.setCurrentIndex(1)

        # Re-connect
        self.driver_a_combo.currentTextChanged.connect(
            lambda d: self._refresh_laps(d, self.lap_a_combo)
        )
        self.driver_b_combo.currentTextChanged.connect(
            lambda d: self._refresh_laps(d, self.lap_b_combo)
        )

        for w in (self.driver_a_combo, self.driver_b_combo,
                  self.lap_a_combo, self.lap_b_combo, self.compare_btn):
            w.setEnabled(True)

        # Populate lap combos for the initial driver selection
        self._refresh_laps(self.driver_a_combo.currentText(), self.lap_a_combo)
        self._refresh_laps(self.driver_b_combo.currentText(), self.lap_b_combo)

    def set_loading(self, loading: bool):
        self.progress_bar.setVisible(loading)
        self.load_btn.setEnabled(not loading)
        if loading:
            self.compare_btn.setEnabled(False)

    def set_status(self, text: str, color: str = "#777"):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 9px;")

    def enable_compare(self, enabled: bool):
        self.compare_btn.setEnabled(enabled)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _refresh_laps(self, driver: str, combo: QComboBox):
        if not driver or self._session_loader is None:
            return
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("Fastest")
        try:
            for n in self._session_loader.get_lap_numbers(driver):
                combo.addItem(str(n))
        except Exception:
            pass
        combo.blockSignals(False)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _group(title: str):
    grp = QGroupBox(title)
    lay = QVBoxLayout(grp)
    lay.setSpacing(5)
    return grp, lay


def _label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet("color: #aaa; font-size: 10px;")
    return lbl


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet("color: #333;")
    return line
