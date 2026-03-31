import torch

class SymbolicCounter:
    """
    Exact symbolic counter. Satisfies BoxedModel protocol.
    
    State transitions are deterministic. predict() returns a one-hot
    distribution — probability 1.0 on the correct next state, 0.0 elsewhere.
    Deficit against this model on the correct wiring is exactly zero.
    """

    def __init__(self, n_counts: int):
        self.n_tokens  = 2 + n_counts
        self.n_counts  = n_counts
        self._state    = 0
        self._repeg    = True
        self._probs    = self._make_probs()

    def set_repeg(self, enabled: bool) -> None:
        self._repeg = enabled

    def reset(self) -> None:
        self._state = 0
        self._probs = self._make_probs()

    def step(self, token: int) -> None:
        if token == 0:    # INC
            self._state = min(self._state + 1, self.n_counts - 1)
        elif token == 1:  # DEC
            self._state = max(self._state - 1, 0)
        elif self._repeg:  # read(k) — absorb ground-truth count only if pegging enabled
            self._state = token - 2
        self._probs = self._make_probs()

    def predict(self) -> torch.Tensor:
        return self._probs

    def _make_probs(self) -> torch.Tensor:
        probs = torch.zeros(self.n_tokens)
        probs[0] = 1.0 / self.n_tokens          # INC
        probs[1] = 1.0 / self.n_tokens          # DEC
        probs[2 + self._state] = self.n_counts / self.n_tokens
        return probs

