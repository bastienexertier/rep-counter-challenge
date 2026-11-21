"""Rep detector to implement. See AGENTS.md for the problem, the data and the rules.

`main.py` creates a new RepDetector for each recording, feeds it every sensor sample in time order with
`add_sample`, and reads `rep_count` after each sample. The count after the last sample is the answer for that set.
"""


class RepDetector:
    def __init__(self):
        """Create a detector ready to receive the first sample of a set."""

    def add_sample(self, sensor: str, t: float, x: float, y: float, z: float) -> None:
        """Receive one sensor sample.

        sensor   "accelerometer": raw acceleration, gravity included (|a| ~ 9.81 when still).
                 "gravity":       Android's estimate of the gravity vector (TYPE_GRAVITY).
                 "linear":        Android's acceleration minus gravity (TYPE_LINEAR_ACCELERATION).
        t        seconds since the first sample of the set (non-decreasing across all sensors, ~200 Hz per sensor,
                 irregular spacing).
        x, y, z  m/s^2, in the phone's coordinate frame.
        """

    @property
    def rep_count(self) -> int:
        """Reps counted so far. Read after every sample; it must never decrease."""
        return 0
