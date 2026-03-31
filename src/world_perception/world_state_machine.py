import torch
import random
from typing import Tuple, Optional


class WorldStateMachine:
    """
    Simulates a discrete world with counted categories.

    Counts live in [0, max_count - 1] (max_count is exclusive upper bound).
    Events: "increase", "decrease", "read".

    type_mod=False: out-of-bounds events are suppressed (no event emitted).
    type_mod=True:  out-of-bounds events wrap (increase at max-1 -> 0, decrease at 0 -> max-1).

    p_read: probability of a read event on each step.
    RNG is local to each instance (seed via constructor).
    """

    def __init__(
        self,
        num_categories: int = 1,
        max_count: int = 4,
        device: str = "cpu",
        type_mod: bool = False,
        p_read: float = 0.06,
        seed: Optional[int] = None,
        initial_state: Optional[int] = None,
    ):
        assert 0.0 <= p_read <= 1.0, "p_read must be in [0, 1]"
        if initial_state is not None:
            assert 0 <= initial_state < max_count, "initial_state must be in [0, max_count-1]"

        self.num_categories = num_categories
        self.max_count = max_count
        self.device = device
        self.type_mod = bool(type_mod)
        self.p_read = float(p_read)
        self._rng = random.Random(seed)

        self.state = torch.zeros(num_categories, dtype=torch.uint8, device=device)
        if initial_state is not None:
            self.state[:] = initial_state

    # --- bounds helpers -------------------------------------------------------

    def _at_max(self, n: int) -> bool:
        return int(self.state[n].item()) >= self.max_count - 1

    def _at_min(self, n: int) -> bool:
        return int(self.state[n].item()) == 0

    # --- event primitives -----------------------------------------------------

    def increase(self, n: int = 0) -> bool:
        """Increase count[n] by 1. Returns True if event was emitted."""
        if not self._at_max(n):
            self.state[n] += 1
            return True
        if self.type_mod:
            self.state[n] = 0
            return True
        return False

    def decrease(self, n: int = 0) -> bool:
        """Decrease count[n] by 1. Returns True if event was emitted."""
        if not self._at_min(n):
            self.state[n] -= 1
            return True
        if self.type_mod:
            self.state[n] = self.max_count - 1
            return True
        return False

    def read_count(self, n: int = 0) -> int:
        """Return current count for category n (always succeeds)."""
        return int(self.state[n].item())

    # --- random event generator -----------------------------------------------

    def _propose_event(self, category: int) -> str:
        """
        Propose a valid event for the given category.
        In type_mod=False mode, avoids proposing events that would be suppressed.
        Note: at boundary states, read probability is effectively elevated since
        invalid inc/dec proposals are replaced by reads.
        """
        r = self._rng.random()

        if r < self.p_read:
            return "read"

        # split remaining mass between increase and decrease
        prefer_increase = r < self.p_read + 0.5 * (1.0 - self.p_read)

        if self.type_mod:
            return "increase" if prefer_increase else "decrease"

        # type_mod=False: avoid proposing suppressed events
        can_increase = not self._at_max(category)
        can_decrease = not self._at_min(category)

        if prefer_increase:
            return "increase" if can_increase else ("decrease" if can_decrease else "read")
        else:
            return "decrease" if can_decrease else ("increase" if can_increase else "read")

    def random_event(self, max_tries: int = 10) -> Tuple[str, int, bool, torch.Tensor]:
        """
        Produce a valid emitted event.
        Retries up to max_tries if a proposed event is suppressed.
        Falls back to a read event if all retries fail.

        Returns (event_name, category, success_flag, resulting_state_tensor).
        """
        for _ in range(max_tries):
            category = self._rng.randrange(self.num_categories)
            event = self._propose_event(category)

            if event == "increase":
                success = self.increase(category)
            elif event == "decrease":
                success = self.decrease(category)
            else:
                success = True
                self.read_count(category)

            if success:
                return event, category, True, self.state.clone()

        # fallback: read is always valid
        category = self._rng.randrange(self.num_categories)
        self.read_count(category)
        return "read", category, True, self.state.clone()

    # --- utility --------------------------------------------------------------

    def set_seed(self, seed: Optional[int]):
        """Reset the internal RNG seed."""
        self._rng.seed(seed)

    def reset(self, initial_state: Optional[int] = None):
        """Reset state to zero or explicit initial_state."""
        self.state.zero_()
        if initial_state is not None:
            assert 0 <= initial_state < self.max_count
            self.state[:] = initial_state

    def __repr__(self):
        return (
            f"WorldStateMachine(state={self.state.tolist()}, "
            f"type_mod={self.type_mod}, p_read={self.p_read})"
        )


if __name__ == "__main__":
    world = WorldStateMachine(
        num_categories=1, max_count=4, device="cpu",
        type_mod=False, p_read=0.15, seed=42, initial_state=0
    )
    print("Starting world:", world)
    for step in range(20):
        event, category, ok, state = world.random_event()
        token = f"read({state[category].item()})" if event == "read" else event
        print(f"Step {step:02d}: event={token:12s}  state={state.tolist()}")