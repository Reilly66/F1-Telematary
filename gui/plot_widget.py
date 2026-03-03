import numpy as np
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from matplotlib.collections import LineCollection
import matplotlib.colors as mcolors
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy

# Driver colour palette (high-visibility on dark background)
COLOR_A = "#FF1E1E"   # bright red
COLOR_B = "#00D2FF"   # bright cyan

BG_DARK = "#1a1a1a"
AX_BG = "#242424"
GRID_COLOR = "#3a3a3a"
TEXT_COLOR = "#cccccc"
SPINE_COLOR = "#4a4a4a"


# ---------------------------------------------------------------------------
# Telemetry canvas — 5 stacked subplots sharing the distance axis
# ---------------------------------------------------------------------------

class TelemetryCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(facecolor=BG_DARK, tight_layout=False)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._build_axes()
        self._show_placeholder()

    # ------------------------------------------------------------------
    def _build_axes(self):
        gs = GridSpec(
            5, 1, figure=self.fig,
            height_ratios=[3, 2, 1.5, 1.5, 1.5],
            hspace=0.08,
            left=0.09, right=0.97, top=0.96, bottom=0.06,
        )
        self.ax_speed    = self.fig.add_subplot(gs[0])
        self.ax_delta    = self.fig.add_subplot(gs[1], sharex=self.ax_speed)
        self.ax_throttle = self.fig.add_subplot(gs[2], sharex=self.ax_speed)
        self.ax_brake    = self.fig.add_subplot(gs[3], sharex=self.ax_speed)
        self.ax_steering = self.fig.add_subplot(gs[4], sharex=self.ax_speed)
        self._all_axes = [
            self.ax_speed, self.ax_delta, self.ax_throttle,
            self.ax_brake, self.ax_steering,
        ]
        self._style_axes()

    def _style_axes(self):
        labels = ["Speed (km/h)", "Δ Time (s)", "Throttle (%)", "Brake", "Steering (°)"]
        for ax, label in zip(self._all_axes, labels):
            ax.set_facecolor(AX_BG)
            ax.set_ylabel(label, color=TEXT_COLOR, fontsize=8, labelpad=4)
            ax.tick_params(colors=TEXT_COLOR, labelsize=7)
            ax.grid(True, color=GRID_COLOR, linewidth=0.5, alpha=0.8)
            for spine in ax.spines.values():
                spine.set_color(SPINE_COLOR)
            # Hide x-tick labels on all but the bottom axis
            if ax is not self.ax_steering:
                ax.tick_params(labelbottom=False)
        self.ax_steering.set_xlabel("Distance (m)", color=TEXT_COLOR, fontsize=8)

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

        # Delta time (filled)
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

        # Brake (fill for on/off clarity)
        if "Brake" in a:
            self.ax_brake.fill_between(dist, a["Brake"], color=COLOR_A, alpha=0.6, lw=0)
            self.ax_brake.fill_between(dist, b["Brake"], color=COLOR_B, alpha=0.4, lw=0)
            self.ax_brake.set_ylim(-0.05, 1.15)

        # Steering
        if "Steering" in a:
            self.ax_steering.plot(dist, a["Steering"], color=COLOR_A, lw=1.0, alpha=0.9)
            self.ax_steering.plot(dist, b["Steering"], color=COLOR_B, lw=1.0, alpha=0.9)
            self.ax_steering.axhline(0, color="#555555", lw=0.6, ls=":")
        else:
            self.ax_steering.text(
                0.5, 0.5, "Steering data unavailable",
                transform=self.ax_steering.transAxes,
                ha="center", va="center", color="#666666", fontsize=9,
            )

        self.draw_idle()


# ---------------------------------------------------------------------------
# Track map canvas — single matplotlib axes, colored by delta
# ---------------------------------------------------------------------------

class TrackMapCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(facecolor=BG_DARK)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.ax = self.fig.add_subplot(111)
        self._style_ax()
        self._show_placeholder()

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
            self.ax.set_title("Track Map — position data unavailable", color=TEXT_COLOR, pad=6)
            self.draw_idle()
            return

        x = a["X"]
        y = a["Y"]

        # Background track (grey outline)
        self.ax.plot(x, y, color="#555555", lw=6, solid_capstyle="round", zorder=1)

        # Coloured line segments by delta value
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

        self.ax.set_title("Track Map — Delta Overlay", color=TEXT_COLOR, fontsize=10, pad=6)
        self.ax.autoscale_view()
        self.ax.set_aspect("equal")
        self.ax.axis("off")
        self.draw_idle()


# ---------------------------------------------------------------------------
# Container widget for the telemetry canvas + navigation toolbar
# ---------------------------------------------------------------------------

class PlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.telemetry_canvas = TelemetryCanvas(self)
        self.track_canvas     = TrackMapCanvas()   # lives in the splitter

        toolbar = NavigationToolbar(self.telemetry_canvas, self)
        toolbar.setStyleSheet("background: #1a1a1a; color: #cccccc; border: none;")

        layout.addWidget(toolbar)
        layout.addWidget(self.telemetry_canvas)

    def plot_comparison(self, comparator, name_a: str, name_b: str):
        self.telemetry_canvas.plot_comparison(comparator, name_a, name_b)
        self.track_canvas.plot_track(comparator)

    def export_png(self, path: str):
        self.telemetry_canvas.fig.savefig(
            path, dpi=150, bbox_inches="tight", facecolor=BG_DARK
        )
