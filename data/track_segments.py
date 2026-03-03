class TurnSegment:
    __slots__ = ("number", "start", "end", "apex")

    def __init__(self, number: int, start: float, end: float, apex: float):
        self.number = number
        self.start  = start
        self.end    = end
        self.apex   = apex


class TrackMap:
    def __init__(self, turn_segments: list):
        self.turns = {t.number: t for t in turn_segments}

    def get_turn(self, number: int) -> "TurnSegment | None":
        return self.turns.get(number)
