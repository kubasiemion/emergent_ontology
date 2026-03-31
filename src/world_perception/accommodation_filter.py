class AccommodationFilter:
    """
    Perceptual accommodation filter for the prototype stream.

    When active, suppresses consecutive read tokens after the first —
    modelling sensory accommodation (the brain stops reporting a stimulus
    that hasn't changed). The first read after any non-read passes; all
    subsequent reads are dropped until a non-read resets the gate.

    Technical debt: currently read-only. In principle accommodation applies
    to all repeated sensory inputs; generalisation is deferred.

    Usage:
        filt = AccommodationFilter(active=True)
        passes = filt(event_name)   # True → propagate, False → drop
    """

    def __init__(self, active: bool = False):
        self.active       = active
        self._last_was_read = False

    def __call__(self, event_name: str) -> bool:
        """Return True if the token should propagate, False if it should be dropped."""
        if not self.active:
            return True

        is_read = (event_name == "read")
        if is_read and self._last_was_read:
            return False          # drop consecutive read

        self._last_was_read = is_read
        return True

    def set_active(self, active: bool):
        """Toggle the filter and reset internal state."""
        self.active         = active
        self._last_was_read = False
