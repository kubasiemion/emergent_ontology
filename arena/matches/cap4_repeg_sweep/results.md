# Cap4 linear — acc80 model at repeg_alpha 0, 0.1, 0.2, 0.5 vs symbolic oracle.

| Place |  Deficit | Model               | INC | DEC | C0  | C1  | C2  | C3  |
| ----- | -------- | ------------------- | --- | --- | --- | --- | --- | --- |
|     1 |   0.0000 | symbolic_cap4       | INC | DEC | C0  | C1  | C2  | C3  |
|     2 |   0.0000 | symbolic_cap4       | DEC | INC | C3  | C2  | C1  | C0  |
|     3 |   0.0518 | cap4_acc80_repeg0.0 | INC | DEC | C0  | C1  | C2  | C3  |
|     4 |   0.6736 | cap4_acc80_repeg0.0 | DEC | INC | C3  | C2  | C1  | C0  |
|     5 |   1.3826 | cap4_acc80_repeg0.1 | INC | DEC | C0  | C1  | C2  | C3  |
|     6 |   1.7068 | cap4_acc80_repeg0.1 | DEC | INC | C3  | C2  | C1  | C0  |
|     7 |   2.0997 | cap4_acc80_repeg0.2 | DEC | INC | C3  | C2  | C1  | C0  |
|     8 |   2.2703 | cap4_acc80_repeg0.2 | INC | DEC | C0  | C1  | C2  | C3  |
|     9 |   2.6268 | cap4_acc80_repeg0.5 | DEC | INC | C3  | C2  | C1  | C0  |
|    10 |   2.8308 | cap4_acc80_repeg0.0 | INC | DEC | C0  | C2  | C1  | C3  |
|    11 |   3.0784 | cap4_acc80_repeg0.5 | C1  | INC | C3  | C2  | DEC | C0  |
|    12 |   3.2508 | cap4_acc80_repeg0.5 | INC | DEC | C0  | C1  | C2  | C3  |
|    13 |   3.2848 | cap4_acc80_repeg0.5 | INC | C1  | C0  | DEC | C2  | C3  |
|    14 |   3.4324 | cap4_acc80_repeg0.0 | DEC | INC | C2  | C3  | C1  | C0  |
|    15 |   4.2000 | cap4_acc80_repeg0.2 | INC | DEC | C0  | C2  | C1  | C3  |
|    16 |   4.2154 | cap4_acc80_repeg0.1 | INC | DEC | C0  | C2  | C1  | C3  |
|    17 |   4.2319 | cap4_acc80_repeg0.2 | DEC | INC | C3  | C1  | C2  | C0  |
|    18 |   4.4444 | symbolic_cap4       | INC | DEC | C3  | C0  | C1  | C2  |
|    19 |   4.4444 | symbolic_cap4       | DEC | INC | C0  | C3  | C2  | C1  |
|    20 |   4.7092 | cap4_acc80_repeg0.1 | DEC | INC | C2  | C3  | C1  | C0  |
