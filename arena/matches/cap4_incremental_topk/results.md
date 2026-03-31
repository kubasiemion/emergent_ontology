# Stage 1 — cap3 departure  (cliff pruning)

Contenders surviving to stage 2: **14**
- **cap4_ghost**: 2
- **cap4_acc70**: 8
- **cap4_acc80**: 4

| Place |  Deficit | Model                         | INC | DEC | C0  | C1  | C2  |
| ----- | -------- | ----------------------------- | --- | --- | --- | --- | --- |
|     1 |   0.0000 | cap4_ghost | INC | DEC | C0  | C1  | C2  |
|     2 |   0.0048 | cap4_acc70     | INC | DEC | C1  | C2  | C3  |
|     3 |   0.0136 | cap4_ghost | DEC | INC | C2  | C1  | C0  |
|     4 |   0.0263 | cap4_acc70     | DEC | INC | C2  | C1  | C0  |
|     5 |   0.0577 | cap4_acc80     | DEC | INC | C2  | C1  | C0  |
|     6 |   0.0661 | cap4_acc70     | INC | DEC | C0  | C2  | C3  |

# Stage 2 — cap4 extension  (S1 Base = stage-1 deficit)

| Place |  Deficit |  S1 Base | Model                     | INC | DEC | C0  | C1  | C2  | C3  |
| ----- | -------- | -------- | ------------------------- | --- | --- | --- | --- | --- | --- |
|     1 |   0.0400 |   0.3795 | cap4_acc80 | INC | DEC | C0  | C1  | C2  | C3  |
|     2 |   0.1386 |   0.1386 | cap4_acc70 | INC | DEC | C0  | C1  | C2  | C3  |
|     3 |   0.6548 |   0.6773 | cap4_acc70 | DEC | INC | C3  | C2  | C1  | C0  |
|     4 |   2.9332 |   0.1386 | cap4_acc70 | INC | DEC | C0  | C1  | C3  | C2  |
|     5 |   3.1905 |   0.5072 | cap4_acc80 | INC | DEC | C0  | C1  | C3  | C2  |
|     6 |   5.7268 |   0.6601 | cap4_acc70 | DEC | INC | C3  | C2  | C0  | C1  |
