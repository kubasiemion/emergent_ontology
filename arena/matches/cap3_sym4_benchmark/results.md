# Cap3 linear world — acc70, acc80 (cap3 models) vs symbolic cap4 oracle.

| Place |  Deficit | Model                     | INC | DEC | C0  | C1  | C2  |
| ----- | -------- | ------------------------- | --- | --- | --- | --- | --- |
|     1 |   0.0000 | symbolic_cap4_linear      | INC | DEC | C0  | C1  | C2  |
|     2 |   0.0000 | symbolic_cap4_linear      | INC | DEC | C1  | C2  | C3  |
|     3 |   0.0000 | symbolic_cap4_linear      | DEC | INC | C2  | C1  | C0  |
|     4 |   0.0000 | symbolic_cap4_linear      | DEC | INC | C3  | C2  | C1  |
|     5 |   1.8929 | cap3_acc80 | INC | DEC | C0  | C1  | C2  |
|     6 |   2.2103 | cap3_acc70 | INC | DEC | C0  | C1  | C2  |
|     7 |   2.4515 | cap3_acc80 | DEC | INC | C2  | C1  | C0  |
|     8 |   2.5595 | cap3_acc70 | INC | C1  | C0  | DEC | C2  |
|     9 |   3.1655 | cap3_acc70 | DEC | INC | C2  | C1  | C0  |
|    10 |   3.8818 | cap3_acc70 | C1  | INC | C2  | DEC | C0  |
|    11 |   4.2009 | cap3_acc70 | C1  | DEC | C0  | INC | C2  |
|    12 |   4.5000 | symbolic_cap4_linear      | INC | DEC | C0  | C1  | C3  |
|    13 |   4.5000 | symbolic_cap4_linear      | DEC | INC | C3  | C2  | C0  |
|    14 |   4.5541 | cap3_acc80 | C2  | INC | C1  | DEC | C0  |
|    15 |   4.6507 | cap3_acc80 | INC | C1  | C0  | DEC | C2  |
|    16 |   4.7480 | cap3_acc70 | C2  | C0  | INC | C1  | DEC |
|    17 |   4.8370 | cap3_acc80 | C1  | DEC | C0  | INC | C2  |
|    18 |   4.9104 | cap3_acc80 | INC | C2  | C0  | DEC | C1  |
