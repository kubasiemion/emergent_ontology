# Scorer: deficit

## Stage 1 — cap3

| Place |  Deficit | Model                         | INC | DEC | C0  | C1  | C2  |
| ----- | -------- | ----------------------------- | --- | --- | --- | --- | --- |
|     1 |   0.0000 | cap4_ghost | INC | DEC | C0  | C1  | C2  |
|     2 |   0.0136 | cap4_ghost | DEC | INC | C2  | C1  | C0  |
|     3 |   0.0577 | cap4_acc80     | DEC | INC | C2  | C1  | C0  |
|     4 |   0.3795 | cap4_acc80     | INC | DEC | C0  | C1  | C2  |

## Stage 2 — cap4  (S1 Base = stage-1 deficit)

| Place |  Deficit |  S1 Base | Model                         | INC | DEC | C0  | C1  | C2  | C3  |
| ----- | -------- | -------- | ----------------------------- | --- | --- | --- | --- | --- | --- |
|     1 |   0.0400 |   0.3795 | cap4_acc80     | INC | DEC | C0  | C1  | C2  | C3  |
|     2 |   3.1905 |   0.5072 | cap4_acc80     | INC | DEC | C0  | C1  | C3  | C2  |
|     3 |   7.0694 |   0.0000 | cap4_ghost | INC | DEC | C0  | C1  | C2  | C3  |
|     4 |   8.6570 |   0.0136 | cap4_ghost | DEC | INC | C2  | C1  | C0  | C3  |

# Scorer: tiered  (eps=0.02  penalty=1.0)

## Stage 1 — cap3

| Place |  Deficit | Model                         | INC | DEC | C0  | C1  | C2  |
| ----- | -------- | ----------------------------- | --- | --- | --- | --- | --- |
|     1 |   0.0000 | cap4_ghost | INC | DEC | C0  | C1  | C2  |
|     2 |   0.0000 | cap4_ghost | DEC | INC | C2  | C1  | C0  |
|     3 |   2.4000 | cap4_acc80     | DEC | INC | C2  | C1  | C0  |
|     4 |  12.2000 | cap4_acc80     | INC | DEC | C0  | C1  | C2  |

## Stage 2 — cap4  (S1 Base = stage-1 deficit)

| Place |  Deficit |  S1 Base | Model                         | INC | DEC | C0  | C1  | C2  | C3  |
| ----- | -------- | -------- | ----------------------------- | --- | --- | --- | --- | --- | --- |
|     1 |   1.8000 |  12.2000 | cap4_acc80     | INC | DEC | C0  | C1  | C2  | C3  |
|     2 | 132.4000 |  16.0000 | cap4_acc80     | INC | DEC | C0  | C1  | C3  | C2  |
|     3 | 219.2000 |   0.0000 | cap4_ghost | INC | DEC | C0  | C1  | C2  | C3  |
|     4 | 225.0000 |   0.0000 | cap4_ghost | DEC | INC | C2  | C1  | C0  | C3  |

# Scorer: cross_entropy

## Stage 1 — cap3

| Place |  Deficit | Model                         | INC | DEC | C0  | C1  | C2  |
| ----- | -------- | ----------------------------- | --- | --- | --- | --- | --- |
|     1 | 374.0480 | cap4_ghost | INC | DEC | C0  | C1  | C2  |
|     2 | 375.5431 | cap4_ghost | DEC | INC | C2  | C1  | C0  |
|     3 | 386.8443 | cap4_acc80     | DEC | INC | C2  | C1  | C0  |
|     4 | 414.5687 | cap4_acc80     | DEC | INC | C3  | C1  | C0  |

## Stage 2 — cap4  (S1 Base = stage-1 deficit)

| Place |  Deficit |  S1 Base | Model                         | INC | DEC | C0  | C1  | C2  | C3  |
| ----- | -------- | -------- | ----------------------------- | --- | --- | --- | --- | --- | --- |
|     1 | 382.1242 | 435.5341 | cap4_acc80     | INC | DEC | C0  | C1  | C2  | C3  |
|     2 | 457.0821 | 445.8806 | cap4_acc80     | INC | DEC | C0  | C1  | C3  | C2  |
|     3 | 537.9306 | 374.0480 | cap4_ghost | INC | DEC | C0  | C1  | C2  | C3  |
|     4 | 601.5205 | 375.5431 | cap4_ghost | DEC | INC | C2  | C1  | C0  | C3  |

