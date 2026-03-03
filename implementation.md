Below is a structured Markdown implementation specification suitable for Claude Code.

⸻

Feature Specification: Clickable Turn Zoom for Telemetry Plots

Objective

Implement interactive functionality such that:
	•	Clicking a turn number on the track map
	•	Or clicking the corresponding dashed vertical turn marker on telemetry plots

Will zoom all telemetry plots to the distance range corresponding to that turn.

Zoom must synchronise across:
	•	Speed plot
	•	Delta-time plot
	•	Throttle plot
	•	Brake plot
	•	Steering plot

⸻

1. Assumptions
	•	Track map already displays turn numbers.
	•	Telemetry plots already contain dashed vertical lines marking turn positions.
	•	Telemetry is aligned on a common distance axis.
	•	Matplotlib is being used for plotting.
	•	GUI framework is PyQt6 or PySide6.

⸻

2. Functional Requirements

2.1 Click Behaviour

When user clicks:
	•	A turn label on the track map
OR
	•	A dashed vertical turn line

The system must:
	1.	Identify the selected turn.
	2.	Retrieve its distance bounds.
	3.	Zoom all telemetry axes to that distance interval.
	4.	Redraw plots.

⸻

2.2 Zoom Range Definition

Each turn must have:

{
    "turn_number": int,
    "start_distance": float,
    "end_distance": float,
    "apex_distance": float
}

Zoom range should include margin:

zoom_start = start_distance - margin
zoom_end   = end_distance + margin

Recommended:

margin = 50 to 100 metres


⸻

3. Data Model Extension

Create a new structure:

data/track_segments.py

Define:

class TurnSegment:
    def __init__(self, number, start, end, apex):
        self.number = number
        self.start = start
        self.end = end
        self.apex = apex

And a container:

class TrackMap:
    def __init__(self, turn_segments: list[TurnSegment]):
        self.turns = {t.number: t for t in turn_segments}
    
    def get_turn(self, number):
        return self.turns.get(number)


⸻

4. Event Handling Implementation

4.1 Matplotlib Click Detection

Use:

figure.canvas.mpl_connect("pick_event", handler)

OR:

figure.canvas.mpl_connect("button_press_event", handler)


⸻

4.2 Track Map Turn Labels

When drawing turn numbers:

ax.text(x, y, str(turn_number), picker=True)

Set:

picker=True

or

picker=5  # pixel tolerance

In click handler:

def on_pick(event):
    if isinstance(event.artist, Text):
        turn_number = int(event.artist.get_text())
        self.zoom_to_turn(turn_number)


⸻

4.3 Vertical Turn Lines

When drawing dashed vertical lines:

line = ax.axvline(distance, linestyle="--", picker=5)
line.turn_number = turn_number

Handler:

def on_pick(event):
    if hasattr(event.artist, "turn_number"):
        turn_number = event.artist.turn_number
        self.zoom_to_turn(turn_number)


⸻

5. Zoom Logic Implementation

Create centralised zoom method:

gui/plot_controller.py

def zoom_to_turn(self, turn_number: int):
    turn = self.track_map.get_turn(turn_number)
    if turn is None:
        return
    
    margin = 75
    
    start = turn.start - margin
    end = turn.end + margin
    
    for ax in self.telemetry_axes:
        ax.set_xlim(start, end)
    
    self.figure.canvas.draw_idle()


⸻

6. Synchronised Multi-Axis Zoom

Maintain:

self.telemetry_axes = [
    self.speed_ax,
    self.delta_ax,
    self.throttle_ax,
    self.brake_ax,
    self.steering_ax
]

All must share same x-limits.

Do NOT rescale y-axis automatically.

⸻

7. Optional Enhancements

7.1 Highlight Active Turn

When zooming:
	•	Change background shading for selected turn.
	•	Or temporarily change vertical line color.

Example:

ax.axvspan(turn.start, turn.end, alpha=0.1)


⸻

7.2 Reset Zoom Button

Add GUI button:

[ Reset Zoom ]

Implementation:

def reset_zoom(self):
    for ax in self.telemetry_axes:
        ax.set_xlim(0, self.total_lap_distance)
    self.figure.canvas.draw_idle()


⸻

7.3 Smooth Animated Zoom (Optional)

Instead of immediate jump:

Interpolate:

current_xlim → target_xlim

Over 200–300 ms using QTimer.

⸻

8. Edge Case Handling
	•	Ignore clicks outside turn markers.
	•	Ensure margin does not exceed lap bounds.
	•	Ensure zoom works even if telemetry not loaded.
	•	Prevent recursive redraw loops.

⸻

9. Required Refactors

If current architecture does not centralise plotting:

You must:
	•	Extract plotting logic into a controller class.
	•	Store references to all axes.
	•	Maintain turn metadata separate from rendering code.

⸻

10. Testing Plan

Test Cases
	1.	Click Turn 1 on track map → plots zoom correctly.
	2.	Click Turn 7 dashed line → plots zoom correctly.
	3.	Click empty region → no change.
	4.	Reset zoom → full lap restored.
	5.	Click multiple turns sequentially → works consistently.
	6.	Works after reloading session.

⸻

11. Deliverables
	•	TurnSegment data structure
	•	Click event wiring
	•	Unified zoom controller
	•	Reset zoom feature
	•	Clean separation between:
	•	Data model
	•	GUI event handling
	•	Plot rendering

⸻

Expected Behaviour

User workflow:
	1.	Load session.
	2.	Compare drivers.
	3.	Click “Turn 10”.
	4.	All telemetry plots zoom into Turn 10 region.
	5.	User analyses braking and throttle traces in detail.
	6.	Click Reset to return to full lap.

⸻

This document provides complete implementation guidance for adding interactive turn-based zoom functionality.