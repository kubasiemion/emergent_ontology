# Cap4 world: fully-trained cap4 vs cap4-ghost (trained only to cap3) vs symbolic oracle.

| Place |  Deficit | Model                         | INC | DEC | C0  | C1  | C2  | C3  |
| ----- | -------- | ----------------------------- | --- | --- | --- | --- | --- | --- |
|     1 |   0.0000 | symbolic_cap4                 | INC | DEC | C0  | C1  | C2  | C3  |
|     2 |   0.0000 | symbolic_cap4                 | DEC | INC | C3  | C2  | C1  | C0  |
|     3 |   0.0400 | cap4_acc80     | INC | DEC | C0  | C1  | C2  | C3  |
|     4 |   0.9823 | cap4_acc80     | DEC | INC | C3  | C2  | C1  | C0  |
|     5 |   3.1905 | cap4_acc80     | INC | DEC | C0  | C1  | C3  | C2  |
|     6 |   3.3789 | cap4_acc80     | INC | DEC | C0  | C2  | C1  | C3  |
|     7 |   4.0405 | cap4_acc80     | DEC | INC | C3  | C1  | C2  | C0  |
|     8 |   4.3333 | symbolic_cap4                 | INC | DEC | C1  | C2  | C3  | C0  |
|     9 |   4.3333 | symbolic_cap4                 | DEC | INC | C2  | C1  | C0  | C3  |
|    10 |   4.7333 | symbolic_cap4                 | INC | DEC | C3  | C0  | C1  | C2  |
|    11 |   4.7333 | symbolic_cap4                 | DEC | INC | C0  | C3  | C2  | C1  |
|    12 |   4.8028 | cap4_acc80     | DEC | INC | C2  | C3  | C1  | C0  |
|    13 |   6.3606 | cap4_ghost | INC | C1  | C0  | DEC | C2  | C3  |
|    14 |   6.4881 | cap4_ghost | DEC | C1  | C2  | INC | C0  | C3  |
|    15 |   7.0341 | cap4_ghost | C1  | DEC | C3  | C0  | INC | C2  |
|    16 |   7.0694 | cap4_ghost | INC | DEC | C0  | C1  | C2  | C3  |
|    17 |   7.1203 | cap4_ghost | C1  | INC | C3  | C2  | DEC | C0  |
|    18 |   7.6556 | cap4_ghost | DEC | INC | C3  | C1  | C2  | C0  |
