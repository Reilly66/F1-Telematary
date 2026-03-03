import numpy as np
import pandas as pd
from data.telemetry_processor import TelemetryProcessor
from data.track_segments import TurnSegment, TrackMap


class TelemetryComparator:
    """
    Aligns two lap telemetry datasets by distance and computes a
    time delta trace along with loss/gain regions.

    Delta convention:
        delta[i] = cumulative_time_A(dist_i) - cumulative_time_B(dist_i)
        Positive  → A is slower (B is faster) at this point in the lap
        Negative  → A is faster (B is slower)
    """

    def __init__(self, lap_a, lap_b, n_points: int = 1000):
        self.lap_a = lap_a
        self.lap_b = lap_b
        self.n_points = n_points
        self._processor = TelemetryProcessor(n_points)

        self.common_dist: np.ndarray = None
        self.aligned_a: dict = None
        self.aligned_b: dict = None
        self.delta: np.ndarray = None
        self.loss_regions: list[dict] = None
        self.turns: list[dict] = None
        self.track_map: TrackMap = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def align(self):
        """Process both laps and align them onto a shared distance axis."""
        tel_a = self._processor.process(self.lap_a)
        tel_b = self._processor.process(self.lap_b)

        max_dist = min(tel_a["Distance"].max(), tel_b["Distance"].max())
        self.common_dist = np.linspace(0, max_dist, self.n_points)

        self.aligned_a = self._processor.align_to_distance(tel_a, self.common_dist)
        self.aligned_b = self._processor.align_to_distance(tel_b, self.common_dist)

    def compute_delta(self) -> np.ndarray:
        """Compute the cumulative time delta (A minus B) across the lap."""
        if self.aligned_a is None:
            raise RuntimeError("Call align() before compute_delta()")

        self.delta = self.aligned_a["Time"] - self.aligned_b["Time"]
        return self.delta

    def detect_loss_regions(self, threshold: float = 0.005) -> list[dict]:
        """
        Identify stretches where the delta slope exceeds *threshold* (s/m).
        Returns a list of dicts with keys: start, end, time_lost.
        """
        if self.delta is None:
            raise RuntimeError("Call compute_delta() before detect_loss_regions()")

        slope = np.gradient(self.delta, self.common_dist)
        significant = np.abs(slope) > threshold

        regions = []
        in_region = False
        start_idx = 0

        for i, sig in enumerate(significant):
            if sig and not in_region:
                in_region = True
                start_idx = i
            elif not sig and in_region:
                in_region = False
                regions.append(
                    {
                        "start": float(self.common_dist[start_idx]),
                        "end": float(self.common_dist[i - 1]),
                        "time_lost": float(
                            self.delta[i - 1] - self.delta[start_idx]
                        ),
                    }
                )

        if in_region:
            regions.append(
                {
                    "start": float(self.common_dist[start_idx]),
                    "end": float(self.common_dist[-1]),
                    "time_lost": float(self.delta[-1] - self.delta[start_idx]),
                }
            )

        self.loss_regions = regions
        return regions

    def set_corners(self, corners_df: "pd.DataFrame") -> list[dict]:
        """
        Populate self.turns from a FastF1 circuit_info.corners DataFrame.

        Expected columns: Number, Letter, Distance, X, Y
        Call this before starting the comparison worker; the data is stored
        on the comparator and used by both the telemetry and track-map plots.
        """
        turns = []
        for _, row in corners_df.iterrows():
            number = int(row["Number"])
            raw_letter = row.get("Letter", "")
            letter = "" if pd.isna(raw_letter) else str(raw_letter).strip()
            turn: dict = {
                "turn_number": number,
                "label": f"T{number}{letter}",
                "distance": float(row["Distance"]),
            }
            if pd.notna(row.get("X")) and pd.notna(row.get("Y")):
                turn["x"] = float(row["X"])
                turn["y"] = float(row["Y"])
            turns.append(turn)
        self.turns = turns
        self._build_track_map(turns)
        return turns

    def _build_track_map(self, turns: list[dict]):
        """Derive start/end distance bounds for each turn from apex midpoints."""
        sorted_turns = sorted(turns, key=lambda t: t["distance"])
        n = len(sorted_turns)
        segments = []
        for i, t in enumerate(sorted_turns):
            apex = t["distance"]
            if i == 0:
                gap = sorted_turns[1]["distance"] - apex if n > 1 else 200.0
                start = max(0.0, apex - gap * 0.5)
            else:
                start = (sorted_turns[i - 1]["distance"] + apex) * 0.5

            if i == n - 1:
                gap = apex - sorted_turns[i - 1]["distance"] if n > 1 else 200.0
                end = apex + gap * 0.5
            else:
                end = (apex + sorted_turns[i + 1]["distance"]) * 0.5

            segments.append(TurnSegment(t["turn_number"], start, end, apex))
        self.track_map = TrackMap(segments)

    def run(self):
        """Convenience method: align → delta → loss regions."""
        self.align()
        self.compute_delta()
        self.detect_loss_regions()
        return self
