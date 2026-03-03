import numpy as np
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from matplotlib.collections import LineCollection
import matplotlib.colors as mcolors
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QPushButton
from PyQt6.QtCore import pyqtSignal

COLOR_A = "#FF1E1E"
COLOR_B = "#00D2FF"

BG_DARK    = "#1a1a1a"
AX_BG      = "#242424"
GRID_COLOR = "#3a3a3a"
TEXT_COLOR = "#cccccc"
SPINE_COLOR = "#4a4a4a"
TURN_LINE_COLOR = "#666666"


# ---------------------------------------------------------------------------
# Telemetry canvas — 4 stacked subplots sharing the distance axis
# ---------------------------------------------------------------------------

class TelemetryCanvas(FigureCanvas):
    turn_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        self.fig = Figure(facecolor=BG_DARK, tight_layout=False)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._track_map     = None
        self._total_distance = 0.0
        self._zoom_spans    = []
        self._build_axes()
        self._show_placeholder()
        self.mpl_connect("pick_event", self._on_pick)

    def _build_axes(self):
        gs = GridSpec(
            4, 1, figure=self.fig,
            height_ratios=[3, 2, 1.5, 1.5],
            hspace=0.08,
            left=0.09, right=0.97, top=0.96, bottom=0.07,
        )
        self.ax_speed    = self.fig.add_subplot(gs[0])
        self.ax_delta    = self.fig.add_subplot(gs[1], sharex=self.ax_speed)
        self.ax_throttle = self.fig.add_subplot(gs[2], sharex=self.ax_speed)
        self.ax_brake    = self.fig.add_subplot(gs[3], sharex=self.ax_speed)
        self._all_axes   = [self.ax_speed, self.ax_delta, self.ax_throttle, self.ax_brake]
        self._style_axes()

    def _style_axes(self):
        labels = ["Speed (km/h)", "Δ Time (s)", "Throttle (%)", "Brake"]
        for ax, label in zip(self._all_axes, labels):
            ax.set_facecolor(AX_BG)
            ax.set_ylabel(label, color=TEXT_COLOR, fontsize=8, labelpad=4)
            ax.tick_params(colors=TEXT_COLOR, labelsize=7)
            ax.grid(True, color=GRID_COLOR, linewidth=0.5, alpha=0.8)
            for spine in ax.spines.values():
                spine.set_color(SPINE_COLOR)
            if ax is not self.ax_brake:
                ax.tick_params(labelbottom=False)
        self.ax_brake.set_xlabel("Distance (m)", color=TEXT_COLOR, fontsize=8)

    def _show_placeholder(self):
        self._clear_axes()
        self.ax_speed.text(
            0.5, 0.5,
            "Load a session and compare two drivers\nto display telemetry",
            transform=self.ax_speed.transAxes,
            ha="center", va="center",
            color="#666666", fontsize=11,
        )
        self.draw_idle()

    def _clear_axes(self):
        for ax in self._all_axes:
            ax.cla()
        self._style_axes()

    # ------------------------------------------------------------------
    def plot_comparison(self, comparator, name_a: str, name_b: str):
        self._clear_axes()
        self._zoom_spans.clear()       # axes were cla()'d; drop stale refs
        self._track_map      = getattr(comparator, "track_map", None)
        self._total_distance = float(comparator.common_dist[-1])
        dist  = comparator.common_dist
        a     = comparator.aligned_a
        b     = comparator.aligned_b
        delta = comparator.delta

        # Speed overlay
        self.ax_speed.plot(dist, a["Speed"], color=COLOR_A, lw=1.3, label=name_a)
        self.ax_speed.plot(dist, b["Speed"], color=COLOR_B, lw=1.3, label=name_b)
        self.ax_speed.legend(
            loc="lower right", fontsize=8,
            facecolor="#2a2a2a", labelcolor="white", framealpha=0.85,
            edgecolor=SPINE_COLOR,
        )

        # Delta (filled)
        self.ax_delta.axhline(0, color="#777777", lw=0.8, ls="--")
        pos = delta >= 0
        neg = delta < 0
        self.ax_delta.fill_between(dist, delta, 0, where=pos, color=COLOR_A, alpha=0.35,
                                   label=f"{name_a} slower")
        self.ax_delta.fill_between(dist, delta, 0, where=neg, color=COLOR_B, alpha=0.35,
                                   label=f"{name_b} slower")
        self.ax_delta.plot(dist, delta, color="white", lw=0.9, alpha=0.9)
        self.ax_delta.legend(
            loc="lower right", fontsize=7,
            facecolor="#2a2a2a", labelcolor="white", framealpha=0.85,
            edgecolor=SPINE_COLOR,
        )

        # Throttle
        if "Throttle" in a:
            self.ax_throttle.plot(dist, a["Throttle"], color=COLOR_A, lw=1.0, alpha=0.9)
            self.ax_throttle.plot(dist, b["Throttle"], color=COLOR_B, lw=1.0, alpha=0.9)
            self.ax_throttle.set_ylim(-5, 105)

        # Brake
        if "Brake" in a:
            self.ax_brake.fill_between(dist, a["Brake"], color=COLOR_A, alpha=0.6, lw=0)
            self.ax_brake.fill_between(dist, b["Brake"], color=COLOR_B, alpha=0.4, lw=0)
            self.ax_brake.set_ylim(-0.05, 1.15)

        # Turn markers
        if comparator.turns:
            self._draw_turn_lines(comparator.turns)

        self.draw_idle()

    def _draw_turn_lines(self, turns: list[dict]):
        """Dashed vertical lines on every subplot; turn labels on speed only."""
        xform = self.ax_speed.get_xaxis_transform()

        for turn in turns:
            d      = turn["distance"]
            number = turn["turn_number"]
            label  = turn.get("label", f"T{number}")
            for ax in self._all_axes:
                line = ax.axvline(
                    d, color=TURN_LINE_COLOR, lw=0.7, ls="--",
                    alpha=0.55, zorder=0, picker=5,
                )
                line.turn_number = number
            self.ax_speed.text(
                d, 1.0, label,
                transform=xform,
                ha="center", va="top",
                fontsize=5.5, color="#aaaaaa",
                clip_on=True,
            )

    def _on_pick(self, event):
        artist = event.artist
        if hasattr(artist, "turn_number"):
            self.zoom_to_turn(artist.turn_number)

    def zoom_to_turn(self, turn_number: int):
        """Zoom all telemetry axes to the distance range for *turn_number*."""
        if self._track_map is None:
            return
        turn = self._track_map.get_turn(turn_number)
        if turn is None:
            return

        margin = 75.0
        x0 = max(0.0, turn.start - margin)
        x1 = min(self._total_distance, turn.end + margin)

        # Replace previous highlight spans
        for span in self._zoom_spans:
            try:
                span.remove()
            except ValueError:
                pass
        self._zoom_spans.clear()
        for ax in self._all_axes:
            span = ax.axvspan(turn.start, turn.end, color="#ffd700", alpha=0.07, zorder=-1)
            self._zoom_spans.append(span)

        self.ax_speed.set_xlim(x0, x1)
        self.draw_idle()

    def reset_zoom(self):
        """Restore the full-lap distance view."""
        for span in self._zoom_spans:
            try:
                span.remove()
            except ValueError:
                pass
        self._zoom_spans.clear()
        self.ax_speed.set_xlim(0, self._total_distance)
        self.draw_idle()


# ---------------------------------------------------------------------------
# Track map canvas — delta-coloured line + turn number badges
# ---------------------------------------------------------------------------

class TrackMapCanvas(FigureCanvas):
    turn_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        self.fig = Figure(facecolor=BG_DARK)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.ax = self.fig.add_subplot(111)
        self._style_ax()
        self._show_placeholder()
        self.mpl_connect("pick_event", self._on_pick)

    def _style_ax(self):
        self.ax.set_facecolor(AX_BG)
        self.ax.tick_params(colors=TEXT_COLOR, labelbottom=False, labelleft=False)
        for spine in self.ax.spines.values():
            spine.set_color(SPINE_COLOR)

    def _show_placeholder(self):
        self.ax.cla()
        self._style_ax()
        self.ax.set_title("Track Map", color=TEXT_COLOR, fontsize=10, pad=6)
        self.ax.text(
            0.5, 0.5, "Track map appears after comparison",
            transform=self.ax.transAxes,
            ha="center", va="center", color="#666666", fontsize=10,
        )
        self.draw_idle()

    def plot_track(self, comparator):
        self.ax.cla()
        self._style_ax()

        a     = comparator.aligned_a
        delta = comparator.delta

        if "X" not in a or "Y" not in a:
            self.ax.set_title("Track Map — position data unavailable",
                               color=TEXT_COLOR, pad=6)
            self.draw_idle()
            return

        x = a["X"]
        y = a["Y"]

        # Grey outline
        self.ax.plot(x, y, color="#555555", lw=6, solid_capstyle="round", zorder=1)

        # Delta-coloured segments
        points   = np.stack([x, y], axis=1).reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        dmin, dmax = float(delta.min()), float(delta.max())
        if dmin < 0 < dmax:
            norm = mcolors.TwoSlopeNorm(vmin=dmin, vcenter=0.0, vmax=dmax)
        else:
            norm = mcolors.Normalize(vmin=dmin, vmax=dmax)

        lc = LineCollection(segments, cmap="RdBu_r", norm=norm, lw=4, zorder=2)
        lc.set_array(delta[:-1])
        self.ax.add_collection(lc)

        cbar = self.fig.colorbar(lc, ax=self.ax, fraction=0.025, pad=0.02)
        cbar.set_label("Δ Time (s)", color=TEXT_COLOR, fontsize=8)
        cbar.ax.yaxis.set_tick_params(color=TEXT_COLOR, labelcolor=TEXT_COLOR)

        # Turn number badges
        if comparator.turns:
            self._draw_turn_badges(comparator.turns, x, y)

        self.ax.set_title("Track Map — Delta Overlay", color=TEXT_COLOR, fontsize=10, pad=6)
        self.ax.autoscale_view()
        self.ax.set_aspect("equal")
        self.ax.axis("off")
        self.draw_idle()

    def _draw_turn_badges(self, turns: list[dict], x_track, y_track):
        """
        Annotate each turn apex with a labelled badge.

        Each badge is offset radially outward from the track centroid so it
        sits just outside the coloured track line rather than on top of it.
        """
        cx = float(np.mean(x_track))
        cy = float(np.mean(y_track))
        # Characteristic track scale for a fixed offset distance
        badge_offset = max(float(np.ptp(x_track)), float(np.ptp(y_track))) * 0.04

        for turn in turns:
            if "x" not in turn:
                continue
            tx, ty  = turn["x"], turn["y"]
            label   = turn.get("label", str(turn["turn_number"]))

            # Unit vector from centroid → corner, then scale to badge_offset
            vx, vy  = tx - cx, ty - cy
            dist    = np.hypot(vx, vy) + 1e-8
            bx = tx + (vx / dist) * badge_offset
            by = ty + (vy / dist) * badge_offset

            txt = self.ax.text(
                bx, by, label,
                fontsize=6, color="white",
                ha="center", va="center",
                zorder=10, picker=5,
                bbox=dict(
                    boxstyle="round,pad=0.25",
                    facecolor="#1e1e1e",
                    edgecolor="#999999",
                    linewidth=0.75,
                    alpha=0.9,
                ),
            )
            txt.turn_number = turn["turn_number"]

    def _on_pick(self, event):
        artist = event.artist
        if hasattr(artist, "turn_number"):
            self.turn_clicked.emit(artist.turn_number)


# ---------------------------------------------------------------------------
# Container widget
# ---------------------------------------------------------------------------

class PlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.telemetry_canvas = TelemetryCanvas(self)
        self.track_canvas     = TrackMapCanvas()

        toolbar = NavigationToolbar(self.telemetry_canvas, self)
        toolbar.setStyleSheet("background: #1a1a1a; color: #cccccc; border: none;")

        self.reset_zoom_btn = QPushButton("Reset Zoom")
        self.reset_zoom_btn.setEnabled(False)
        self.reset_zoom_btn.setFixedHeight(22)
        self.reset_zoom_btn.setStyleSheet(
            "QPushButton { background: #2a2a2a; color: #aaa;"
            "  border: 1px solid #444; font-size: 9px; padding: 0 8px; }"
            "QPushButton:hover { background: #333; color: #fff; }"
            "QPushButton:disabled { color: #555; border-color: #333; }"
        )
        self.reset_zoom_btn.clicked.connect(self.telemetry_canvas.reset_zoom)

        # Track-map badge clicks → telemetry zoom
        self.track_canvas.turn_clicked.connect(self.telemetry_canvas.zoom_to_turn)

        layout.addWidget(toolbar)
        layout.addWidget(self.reset_zoom_btn)
        layout.addWidget(self.telemetry_canvas)

    def plot_comparison(self, comparator, name_a: str, name_b: str):
        self.telemetry_canvas.plot_comparison(comparator, name_a, name_b)
        self.track_canvas.plot_track(comparator)
        self.reset_zoom_btn.setEnabled(True)

    def export_png(self, path: str):
        self.telemetry_canvas.fig.savefig(
            path, dpi=150, bbox_inches="tight", facecolor=BG_DARK
        )
