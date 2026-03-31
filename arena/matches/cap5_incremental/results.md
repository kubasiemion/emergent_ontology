# Stage 1 — cap3 departure  (cliff pruning)

Contenders surviving: **9**
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

# Stage 2 — cap4 extension  (cliff pruning)

Contenders surviving: **14**
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

# Stage 3 — cap5 final  (Prev = stage-2 deficit)

| Place |  Deficit |  S1 Base | Model                         | INC | DEC | C0  | C1  | C2  | C3  | C4  |
| ----- | -------- | -------- | ----------------------------- | --- | --- | --- | --- | --- | --- | --- |
|     1 |   0.0391 |   0.5457 | cap5_acc80     | INC | DEC | C0  | C1  | C2  | C3  | C4  |
|     2 |   0.5813 |   0.5928 | cap5_acc80     | INC | DEC | C0  | C1  | C2  | C4  | C3  |
|     3 |   2.8887 |   0.0166 | cap5_cap4trained_acc80 | INC | DEC | C0  | C1  | C2  | C3  | C4  |
|     4 |   5.0593 |   1.5726 | cap5_cap4trained_acc80 | INC | DEC | C0  | C1  | C3  | C2  | C4  |
|     5 |   5.9592 |   3.2518 | cap5_cap4trained_acc80 | INC | DEC | C0  | C1  | C2  | C4  | C3  |
|     6 |   8.5965 |   4.8078 | cap5_cap4trained_acc80 | INC | DEC | C0  | C1  | C3  | C4  | C2  |
