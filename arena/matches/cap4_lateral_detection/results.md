# Pass 1 — filtered observer  (C3 removed, 8.3% of events dropped)

| Place |  Deficit | Model                         | INC | DEC | C0  | C1  | C2  |
| ----- | -------- | ----------------------------- | --- | --- | --- | --- | --- |
|     1 |   0.0400 | cap4_acc80     | INC | DEC | C0  | C1  | C2  |
|     2 |   0.9823 | cap4_acc80     | DEC | INC | C3  | C2  | C1  |
|     3 |   2.4466 | cap4_ghost | DEC | C1  | C2  | INC | C0  |
|     4 |   2.8734 | cap4_ghost | INC | C1  | C0  | DEC | C2  |
|     5 |   3.1905 | cap4_acc80     | INC | DEC | C0  | C1  | C3  |
|     6 |   3.3789 | cap4_acc80     | INC | DEC | C0  | C2  | C1  |
|     7 |   3.3845 | cap4_ghost | INC | DEC | C0  | C1  | C2  |
|     8 |   4.0286 | cap4_ghost | DEC | C0  | C2  | INC | C1  |

# Pass 2 — full observer  (complete cap4 scoring)

| Place |  Deficit | Model                         | INC | DEC | C0  | C1  | C2  | C3  |
| ----- | -------- | ----------------------------- | --- | --- | --- | --- | --- | --- |
|     1 |   0.0400 | cap4_acc80     | INC | DEC | C0  | C1  | C2  | C3  |
|     2 |   0.9823 | cap4_acc80     | DEC | INC | C3  | C2  | C1  | C0  |
|     3 |   3.1905 | cap4_acc80     | INC | DEC | C0  | C1  | C3  | C2  |
|     4 |   3.3789 | cap4_acc80     | INC | DEC | C0  | C2  | C1  | C3  |
|     5 |   6.3606 | cap4_ghost | INC | C1  | C0  | DEC | C2  | C3  |
|     6 |   6.4881 | cap4_ghost | DEC | C1  | C2  | INC | C0  | C3  |
|     7 |   7.0341 | cap4_ghost | C1  | DEC | C3  | C0  | INC | C2  |
|     8 |   7.0694 | cap4_ghost | INC | DEC | C0  | C1  | C2  | C3  |
