import numpy as np
import pandas as pd

NUMERIC_CHANNELS = ["Speed", "Throttle", "Brake", "nGear", "RPM"]
STEERING_CHANNEL = "SteeringAngle"
POSITION_CHANNELS = ["X", "Y"]


class TelemetryProcessor:
    """Cleans and aligns telemetry onto a common distance axis."""

    def __init__(self, n_points: int = 1000):
        self.n_points = n_points

    def process(self, lap) -> pd.DataFrame:
        """Retrieve and clean telemetry from a lap object."""
        tel = lap.get_telemetry()
        if tel is None or tel.empty:
            raise ValueError("No telemetry data available for this lap")
        tel = tel.drop_duplicates(subset="Distance")
        tel = tel.sort_values("Distance").reset_index(drop=True)
        # Ensure Brake is numeric (it can be boolean in some API versions)
        if "Brake" in tel.columns:
            tel["Brake"] = tel["Brake"].astype(float)
        return tel

    def align_to_distance(self, tel: pd.DataFrame, common_dist: np.ndarray) -> dict:
        """Interpolate all channels onto a shared distance array."""
        dist = tel["Distance"].values
        result = {"Distance": common_dist}

        for ch in NUMERIC_CHANNELS:
            if ch in tel.columns:
                result[ch] = np.interp(common_dist, dist, tel[ch].astype(float).values)

        if STEERING_CHANNEL in tel.columns:
            result["Steering"] = np.interp(
                common_dist, dist, tel[STEERING_CHANNEL].astype(float).values
            )

        # Cumulative time in seconds (from lap start)
        time_s = tel["Time"].dt.total_seconds().values
        time_s -= time_s[0]
        result["Time"] = np.interp(common_dist, dist, time_s)

        for ch in POSITION_CHANNELS:
            if ch in tel.columns:
                result[ch] = np.interp(common_dist, dist, tel[ch].astype(float).values)

        return result
