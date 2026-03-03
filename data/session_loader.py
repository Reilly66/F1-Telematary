import fastf1
import pandas as pd


class SessionLoader:
    """Handles loading and querying FastF1 sessions."""

    def __init__(self):
        self._session = None

    def get_event_schedule(self, year: int) -> list[str]:
        """Return a list of event names for the given season."""
        schedule = fastf1.get_event_schedule(year, include_testing=False)
        return schedule["EventName"].tolist()

    def load_session(self, year: int, event: str, session_type: str):
        """Load a FastF1 session with telemetry data."""
        self._session = fastf1.get_session(year, event, session_type)
        self._session.load(telemetry=True, weather=False, messages=False)
        return self._session

    @property
    def session(self):
        return self._session

    def get_driver_list(self) -> list[str]:
        """Return sorted list of driver abbreviations for the loaded session."""
        if self._session is None:
            return []
        try:
            abbrevs = self._session.results["Abbreviation"].dropna().tolist()
            return sorted(abbrevs)
        except Exception:
            return sorted(self._session.drivers.tolist())

    def get_lap_numbers(self, driver: str) -> list[int]:
        """Return sorted valid lap numbers for a driver."""
        if self._session is None:
            return []
        laps = self._session.laps.pick_driver(driver)
        if laps.empty:
            return []
        return sorted(laps["LapNumber"].dropna().astype(int).tolist())

    def get_lap(self, driver: str, lap_selection: str = "Fastest"):
        """Return a lap object for the specified driver and lap selection."""
        if self._session is None:
            raise RuntimeError("No session loaded")
        laps = self._session.laps.pick_driver(driver)
        if laps.empty:
            raise ValueError(f"No laps found for driver {driver}")

        if lap_selection == "Fastest":
            lap = laps.pick_quicklaps().pick_fastest()
            if lap is None or (hasattr(lap, "empty") and lap.empty):
                lap = laps.pick_fastest()
            if lap is None:
                raise ValueError(f"No fastest lap found for {driver}")
            return lap

        lap_num = int(lap_selection)
        matching = laps[laps["LapNumber"] == lap_num]
        if matching.empty:
            raise ValueError(f"Lap {lap_num} not found for {driver}")
        return matching.iloc[0]
