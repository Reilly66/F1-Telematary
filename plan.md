FastF1 Telemetry Comparison Tool

Technical Project Specification

1. Objective

Develop a Python desktop application with a graphical user interface (GUI) that allows side-by-side telemetry comparison of two Formula 1 drivers using the FastF1 API.

The tool must enable:
	•	Selection of season, event, session, drivers, and laps.
	•	Overlay comparison of telemetry traces.
	•	Visualization of time delta across lap distance.
	•	Identification of where one driver gains or loses time.
	•	Analysis of contributing control inputs (throttle, brake, steering).

⸻

2. Core Technologies

Data Layer
	•	fastf1
	•	pandas
	•	numpy

Visualisation
	•	matplotlib (primary plotting engine)
	•	Optional: pyqtgraph (if real-time interactivity required)

GUI Framework

Preferred:
	•	PyQt6 or PySide6

Alternative (simpler but less scalable):
	•	Tkinter

⸻

3. High-Level Architecture

project_root/
│
├── main.py
├── gui/
│   ├── main_window.py
│   ├── controls_panel.py
│   ├── plot_widget.py
│   └── session_selector.py
│
├── data/
│   ├── session_loader.py
│   ├── telemetry_processor.py
│   └── comparison_engine.py
│
├── utils/
│   └── cache_manager.py
│
└── requirements.txt


⸻

4. Functional Requirements

4.1 Session Selection

User must be able to select:
	•	Season (e.g., 2024)
	•	Event (e.g., Monaco Grand Prix)
	•	Session type:
	•	Practice
	•	Qualifying
	•	Race
	•	Driver A
	•	Driver B
	•	Lap number OR fastest lap

⸻

4.2 Telemetry Retrieval

Use:

import fastf1
session = fastf1.get_session(year, event, session_type)
session.load()

Retrieve lap:

lap = session.laps.pick_driver("VER").pick_fastest()
tel = lap.get_telemetry()

Required telemetry channels:
	•	Speed
	•	Throttle
	•	Brake
	•	SteeringAngle
	•	RPM
	•	Gear
	•	Distance
	•	X, Y (track position)

⸻

4.3 Telemetry Alignment

Critical requirement: Telemetry must be aligned by distance, not time.

Steps:
	1.	Interpolate both telemetry datasets onto a common distance axis.
	2.	Normalize distance to 0 → lap_length.
	3.	Compute time delta trace.

Delta calculation approach:

delta_time(distance_i) =
    cumulative_time_driverA(distance_i)
    - cumulative_time_driverB(distance_i)


⸻

4.4 Visualisations

The GUI must include:

4.4.1 Speed Overlay Plot
	•	X-axis: Distance
	•	Y-axis: Speed
	•	Two lines (Driver A, Driver B)

4.4.2 Delta Time Plot
	•	X-axis: Distance
	•	Y-axis: Time delta
	•	Highlight regions of significant loss/gain

4.4.3 Control Inputs

Stacked plots for:
	•	Throttle
	•	Brake
	•	Steering angle

⸻

4.4.4 Track Map View

Using X and Y:
	•	Plot track outline
	•	Color-coded delta overlay
	•	Hover tooltip showing:
	•	Speed A
	•	Speed B
	•	Delta
	•	Throttle difference

⸻

5. GUI Layout

Recommended layout:

------------------------------------------------------
| Controls Panel        |        Main Plot Area      |
|-----------------------|----------------------------|
| Season Dropdown       | Speed Overlay              |
| Event Dropdown        | Delta Plot                 |
| Session Dropdown      | Throttle Plot              |
| Driver A Dropdown     | Brake Plot                 |
| Driver B Dropdown     | Steering Plot              |
| Lap Selector          |                            |
| Compare Button        |                            |
------------------------------------------------------
| Track Map (bottom panel)                           |
------------------------------------------------------


⸻

6. Data Processing Logic

6.1 Interpolation

Use:

numpy.interp()

Procedure:
	1.	Define common distance array (e.g., 0 → lap_length, 1000 points).
	2.	Interpolate:
	•	Speed
	•	Throttle
	•	Brake
	•	Steering
	•	Time

⸻

6.2 Delta Analysis Engine

Implement a comparison class:

class TelemetryComparator:
    def __init__(self, tel_a, tel_b):
        ...
    
    def align(self):
        ...
    
    def compute_delta(self):
        ...
    
    def detect_loss_regions(self, threshold=0.05):
        ...


⸻

6.3 Loss Region Detection

Define region as:

abs(delta_slope) > threshold

Return:
	•	Start distance
	•	End distance
	•	Estimated time lost

⸻

7. Performance Considerations
	•	Enable FastF1 cache:

fastf1.Cache.enable_cache("cache")

	•	Load session once.
	•	Reuse telemetry objects.
	•	Avoid reloading session on every comparison.

⸻

8. Optional Advanced Features

8.1 Sector Analysis
	•	Split lap into official sectors.
	•	Show delta per sector.

8.2 Corner Detection

Use curvature from X,Y coordinates to detect corners.

8.3 Braking Analysis

Compute:
	•	Braking start distance
	•	Minimum speed in corner
	•	Throttle reapplication distance

8.4 Export Function

Allow export of:
	•	CSV telemetry comparison
	•	PNG of plots

⸻

9. Example User Workflow
	1.	User selects:
	•	2024
	•	Silverstone
	•	Qualifying
	•	HAM vs VER
	•	Fastest lap
	2.	Clicks “Compare”.
	3.	Application:
	•	Loads session (cached)
	•	Retrieves fastest laps
	•	Aligns telemetry
	•	Computes delta
	•	Renders plots
	4.	User inspects:
	•	Large delta spike before Copse
	•	Observes earlier braking from Driver A
	•	Confirms via brake trace

⸻

10. Error Handling Requirements
	•	Handle missing telemetry channels.
	•	Handle invalid lap selections.
	•	Show loading spinner during session load.
	•	Gracefully handle FastF1 network errors.

⸻

11. Milestones

Phase 1
	•	CLI-based telemetry comparison.
	•	Produce static matplotlib overlay.

Phase 2
	•	Basic GUI with driver selection.
	•	Speed and delta plot.

Phase 3
	•	Full telemetry stack plots.
	•	Track map integration.

Phase 4
	•	Advanced analysis features.
	•	Export functionality.

⸻

12. Stretch Goals
	•	Live timing support.
	•	Compare race stints.
	•	Multi-lap average comparison.
	•	Machine learning clustering of driving styles.

⸻

13. Deliverables
	•	Fully functional Python application.
	•	Clean modular architecture.
	•	Inline documentation.
	•	Requirements file.
	•	README with usage instructions.

⸻

14. Non-Functional Requirements
	•	Python 3.10+
	•	Cross-platform (Windows/macOS/Linux)
	•	Clear separation between:
	•	GUI layer
	•	Data layer
	•	Analysis layer

⸻

This specification is ready to be used as a structured instruction file for Claude Code to scaffold and implement the project.