# cap4_bypass_compare

> **STATUS: ENGINEERING DIAGNOSTIC** — validates the GRU bypass fix, not a demo piece.

Same cap4_acc80 weights scored twice: once with `bypass_read_tokens=True` (current default)
and once with `bypass_read_tokens=False` (old broken behaviour).

**Finding**: bypass_on → deficit 0.052, canonical wiring.
bypass_off → deficit 6.03, incoherent wiring (C3 token interpreted as DEC action).

With bypass off, the model's GRU is fed an untrained count-token embedding on every read event,
corrupting the hidden state. The brute-force search can't recover a coherent mapping.
The untrained C3 embedding happened to land near the DEC embedding, which is why
the bypass_off best wiring shows `INC→INC, C3→DEC`.
