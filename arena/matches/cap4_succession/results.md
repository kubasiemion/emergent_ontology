# Stage 1 — cap3 departure  (cliff pruning)

Contenders surviving to stage 2: **6**
- **cap4_ghost**: 2
- **cap4_acc80**: 4

| Place |  Deficit | Model                         | INC | DEC | C0  | C1  | C2  |
| ----- | -------- | ----------------------------- | --- | --- | --- | --- | --- |
|     1 |   0.0000 | cap4_ghost | INC | DEC | C0  | C1  | C2  |
|     2 |   0.0136 | cap4_ghost | DEC | INC | C2  | C1  | C0  |
|     3 |   0.0577 | cap4_acc80     | DEC | INC | C2  | C1  | C0  |
|     4 |   0.3795 | cap4_acc80     | INC | DEC | C0  | C1  | C2  |

# Stage 2 — cap4 extension  (S1 Base = stage-1 deficit)

| Place |  Deficit |  S1 Base | Model                         | INC | DEC | C0  | C1  | C2  | C3  |
| ----- | -------- | -------- | ----------------------------- | --- | --- | --- | --- | --- | --- |
|     1 |   0.0400 |   0.3795 | cap4_acc80     | INC | DEC | C0  | C1  | C2  | C3  |
|     2 |   3.1905 |   0.5072 | cap4_acc80     | INC | DEC | C0  | C1  | C3  | C2  |
|     3 |   7.0694 |   0.0000 | cap4_ghost | INC | DEC | C0  | C1  | C2  | C3  |
|     4 |   8.6570 |   0.0136 | cap4_ghost | DEC | INC | C2  | C1  | C0  | C3  |
