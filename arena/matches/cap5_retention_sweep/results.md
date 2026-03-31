# Retention Policy Sweep — Summary

Each cell shows contenders surviving the intermediate stage for that model.
A '0' means the model was eliminated before the final.

| Policy | cap3 counter_acc70 | cap3 counter_acc80 | cap3 cap4trained_acc80 | cap4 counter_acc70 | cap4 counter_acc80 | cap4 cap4trained_acc80 | Final winner | Final deficit |
| --- |  | ---  | ---  | ---  | ---  | ---  | --- | --- | --- |
| threshold=0.05 | 1 | 2 | 2 | 0 | 0 | 1 | cap4trained_acc80 | 2.8887 |
| cliff (gap=0.1, min=1) | 1 | 2 | 6 | 0 | 2 | 12 | counter_acc80 | 0.0391 |
| threshold=2.0 | 7 | 3 | 8 | 0 | 4 | 4 | counter_acc80 | 0.0391 |
| topk=1 | 0 | 1 | 0 | 0 | 1 | 0 | counter_acc80 | 18.4069 |

# Policy: threshold=0.05

## Stage 1 — cap3  (→ 5 contenders survive)

- **cap5_acc80**: 2
- **cap5_cap4trained_acc80**: 2
- **cap5_acc70**: 1

| Place |  Deficit | Model                         | INC | DEC | C0  | C1  | C2  |
| ----- | -------- | ----------------------------- | --- | --- | --- | --- | --- |
|     1 |   0.0096 | cap5_acc80     | DEC | INC | C2  | C1  | C0  |
|     2 |   0.0146 | cap5_cap4trained_acc80 | DEC | INC | C2  | C1  | C0  |
|     3 |   0.0166 | cap5_cap4trained_acc80 | INC | DEC | C0  | C1  | C2  |
|     4 |   0.0212 | cap5_acc80     | INC | DEC | C0  | C1  | C2  |
|     5 |   0.0481 | cap5_acc70     | DEC | INC | C2  | C1  | C0  |

## Stage 2 — cap4  (→ 1 contenders survive)

- **cap5_cap4trained_acc80**: 1

| Place |  Deficit |  S1 Base | Model                         | INC | DEC | C0  | C1  | C2  | C3  |
| ----- | -------- | -------- | ----------------------------- | --- | --- | --- | --- | --- | --- |
|     1 |   0.0166 |   0.0166 | cap5_cap4trained_acc80 | INC | DEC | C0  | C1  | C2  | C3  |
|     2 |   0.5457 |   0.0212 | cap5_acc80     | INC | DEC | C0  | C1  | C2  | C3  |
|     3 |   0.5928 |   0.0212 | cap5_acc80     | INC | DEC | C0  | C1  | C2  | C4  |
|     4 |   3.2518 |   0.0166 | cap5_cap4trained_acc80 | INC | DEC | C0  | C1  | C2  | C4  |
|     5 |   4.5927 |   0.0146 | cap5_cap4trained_acc80 | DEC | INC | C2  | C1  | C0  | C3  |
|     6 |   4.6384 |   0.0146 | cap5_cap4trained_acc80 | DEC | INC | C2  | C1  | C0  | C4  |

## Stage 3 — cap5  (final — no pruning)

| Place |  Deficit |  S1 Base | Model                         | INC | DEC | C0  | C1  | C2  | C3  | C4  |
| ----- | -------- | -------- | ----------------------------- | --- | --- | --- | --- | --- | --- | --- |
|     1 |   2.8887 |   0.0166 | cap5_cap4trained_acc80 | INC | DEC | C0  | C1  | C2  | C3  | C4  |

# Policy: cliff (gap=0.1, min=1)

## Stage 1 — cap3  (→ 9 contenders survive)

- **cap5_acc80**: 2
- **cap5_cap4trained_acc80**: 6
- **cap5_acc70**: 1

| Place |  Deficit | Model                         | INC | DEC | C0  | C1  | C2  |
| ----- | -------- | ----------------------------- | --- | --- | --- | --- | --- |
|     1 |   0.0096 | cap5_acc80     | DEC | INC | C2  | C1  | C0  |
|     2 |   0.0146 | cap5_cap4trained_acc80 | DEC | INC | C2  | C1  | C0  |
|     3 |   0.0166 | cap5_cap4trained_acc80 | INC | DEC | C0  | C1  | C2  |
|     4 |   0.0212 | cap5_acc80     | INC | DEC | C0  | C1  | C2  |
|     5 |   0.0481 | cap5_acc70     | DEC | INC | C2  | C1  | C0  |
|     6 |   0.3065 | cap5_cap4trained_acc80 | INC | DEC | C0  | C1  | C3  |

## Stage 2 — cap4  (→ 14 contenders survive)

- **cap5_cap4trained_acc80**: 12
- **cap5_acc80**: 2

| Place |  Deficit |  S1 Base | Model                         | INC | DEC | C0  | C1  | C2  | C3  |
| ----- | -------- | -------- | ----------------------------- | --- | --- | --- | --- | --- | --- |
|     1 |   0.0166 |   0.0166 | cap5_cap4trained_acc80 | INC | DEC | C0  | C1  | C2  | C3  |
|     2 |   0.5457 |   0.0212 | cap5_acc80     | INC | DEC | C0  | C1  | C2  | C3  |
|     3 |   0.5928 |   0.0212 | cap5_acc80     | INC | DEC | C0  | C1  | C2  | C4  |
|     4 |   1.5726 |   0.3065 | cap5_cap4trained_acc80 | INC | DEC | C0  | C1  | C3  | C2  |
|     5 |   3.2518 |   0.0166 | cap5_cap4trained_acc80 | INC | DEC | C0  | C1  | C2  | C4  |
|     6 |   4.5673 |   0.7326 | cap5_cap4trained_acc80 | DEC | INC | C3  | C1  | C0  | C2  |

## Stage 3 — cap5  (final — no pruning)

| Place |  Deficit |  S1 Base | Model                         | INC | DEC | C0  | C1  | C2  | C3  | C4  |
| ----- | -------- | -------- | ----------------------------- | --- | --- | --- | --- | --- | --- | --- |
|     1 |   0.0391 |   0.5457 | cap5_acc80     | INC | DEC | C0  | C1  | C2  | C3  | C4  |
|     2 |   0.5813 |   0.5928 | cap5_acc80     | INC | DEC | C0  | C1  | C2  | C4  | C3  |
|     3 |   2.8887 |   0.0166 | cap5_cap4trained_acc80 | INC | DEC | C0  | C1  | C2  | C3  | C4  |
|     4 |   5.0593 |   1.5726 | cap5_cap4trained_acc80 | INC | DEC | C0  | C1  | C3  | C2  | C4  |
|     5 |   5.9592 |   3.2518 | cap5_cap4trained_acc80 | INC | DEC | C0  | C1  | C2  | C4  | C3  |
|     6 |   8.5965 |   4.8078 | cap5_cap4trained_acc80 | INC | DEC | C0  | C1  | C3  | C4  | C2  |

# Policy: threshold=2.0

## Stage 1 — cap3  (→ 18 contenders survive)

- **cap5_acc80**: 3
- **cap5_cap4trained_acc80**: 8
- **cap5_acc70**: 7

| Place |  Deficit | Model                         | INC | DEC | C0  | C1  | C2  |
| ----- | -------- | ----------------------------- | --- | --- | --- | --- | --- |
|     1 |   0.0096 | cap5_acc80     | DEC | INC | C2  | C1  | C0  |
|     2 |   0.0146 | cap5_cap4trained_acc80 | DEC | INC | C2  | C1  | C0  |
|     3 |   0.0166 | cap5_cap4trained_acc80 | INC | DEC | C0  | C1  | C2  |
|     4 |   0.0212 | cap5_acc80     | INC | DEC | C0  | C1  | C2  |
|     5 |   0.0481 | cap5_acc70     | DEC | INC | C2  | C1  | C0  |
|     6 |   0.3065 | cap5_cap4trained_acc80 | INC | DEC | C0  | C1  | C3  |

## Stage 2 — cap4  (→ 8 contenders survive)

- **cap5_cap4trained_acc80**: 4
- **cap5_acc80**: 4

| Place |  Deficit |  S1 Base | Model                         | INC | DEC | C0  | C1  | C2  | C3  |
| ----- | -------- | -------- | ----------------------------- | --- | --- | --- | --- | --- | --- |
|     1 |   0.0166 |   0.0166 | cap5_cap4trained_acc80 | INC | DEC | C0  | C1  | C2  | C3  |
|     2 |   0.5457 |   0.0212 | cap5_acc80     | INC | DEC | C0  | C1  | C2  | C3  |
|     3 |   0.5928 |   0.0212 | cap5_acc80     | INC | DEC | C0  | C1  | C2  | C4  |
|     4 |   0.6978 |   1.4301 | cap5_acc80     | INC | DEC | C0  | C1  | C3  | C4  |
|     5 |   0.7520 |   1.9450 | cap5_cap4trained_acc80 | DEC | INC | C3  | C2  | C1  | C0  |
|     6 |   1.5726 |   0.3065 | cap5_cap4trained_acc80 | INC | DEC | C0  | C1  | C3  | C2  |

## Stage 3 — cap5  (final — no pruning)

| Place |  Deficit |  S1 Base | Model                         | INC | DEC | C0  | C1  | C2  | C3  | C4  |
| ----- | -------- | -------- | ----------------------------- | --- | --- | --- | --- | --- | --- | --- |
|     1 |   0.0391 |   0.5457 | cap5_acc80     | INC | DEC | C0  | C1  | C2  | C3  | C4  |
|     2 |   0.3833 |   1.6621 | cap5_acc80     | INC | DEC | C0  | C1  | C3  | C2  | C4  |
|     3 |   0.5813 |   0.5928 | cap5_acc80     | INC | DEC | C0  | C1  | C2  | C4  | C3  |
|     4 |   1.8025 |   0.6978 | cap5_acc80     | INC | DEC | C0  | C1  | C3  | C4  | C2  |
|     5 |   2.8887 |   0.0166 | cap5_cap4trained_acc80 | INC | DEC | C0  | C1  | C2  | C3  | C4  |
|     6 |   3.6921 |   0.7520 | cap5_cap4trained_acc80 | DEC | INC | C3  | C2  | C1  | C0  | C4  |

# Policy: topk=1

## Stage 1 — cap3  (→ 1 contenders survive)

- **cap5_acc80**: 1

| Place |  Deficit | Model                     | INC | DEC | C0  | C1  | C2  |
| ----- | -------- | ------------------------- | --- | --- | --- | --- | --- |
|     1 |   0.0096 | cap5_acc80 | DEC | INC | C2  | C1  | C0  |

## Stage 2 — cap4  (→ 1 contenders survive)

- **cap5_acc80**: 1

| Place |  Deficit |  S1 Base | Model                     | INC | DEC | C0  | C1  | C2  | C3  |
| ----- | -------- | -------- | ------------------------- | --- | --- | --- | --- | --- | --- |
|     1 |  12.2303 |   0.0096 | cap5_acc80 | DEC | INC | C2  | C1  | C0  | C3  |
|     2 |  12.4249 |   0.0096 | cap5_acc80 | DEC | INC | C2  | C1  | C0  | C4  |

## Stage 3 — cap5  (final — no pruning)

| Place |  Deficit |  S1 Base | Model                     | INC | DEC | C0  | C1  | C2  | C3  | C4  |
| ----- | -------- | -------- | ------------------------- | --- | --- | --- | --- | --- | --- | --- |
|     1 |  18.4069 |  12.2303 | cap5_acc80 | DEC | INC | C2  | C1  | C0  | C3  | C4  |

