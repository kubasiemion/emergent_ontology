# Screen Violation — all stage-1 wirings  (cap3 world, 10% corruption)

Sorted by violation deficit. S1 Def = original stage-1 deficit from source match.

| Place |  S1 Def | Viol Def | Model                         | INC | DEC | C0  | C1  | C2  |
| ----- | ------- | -------- | ----------------------------- | --- | --- | --- | --- | --- |
|     1 |  0.0136 |   1.1062 | cap4_ghost | DEC | INC | C2  | C1  | C0  |
|     2 |  0.0000 |   1.1137 | cap4_ghost | INC | DEC | C0  | C1  | C2  |
|     3 |  0.0048 |   1.2194 | cap4_acc70     | INC | DEC | C1  | C2  | C3  |
|     4 |  0.0263 |   1.2435 | cap4_acc70     | DEC | INC | C2  | C1  | C0  |
|     5 |  0.0577 |   1.3079 | cap4_acc80     | DEC | INC | C2  | C1  | C0  |
|     6 |  0.1386 |   1.4486 | cap4_acc70     | INC | DEC | C0  | C1  | C2  |
|     7 |  0.3795 |   1.6938 | cap4_acc80     | INC | DEC | C0  | C1  | C2  |
|     8 |  0.1369 |   1.9721 | cap4_acc70     | DEC | INC | C3  | C1  | C0  |
|     9 |  0.0661 |   1.9920 | cap4_acc70     | INC | DEC | C0  | C2  | C3  |
|    10 |  0.1386 |   2.1138 | cap4_acc70     | INC | DEC | C0  | C1  | C3  |
|    11 |  0.4764 |   2.2437 | cap4_acc80     | DEC | INC | C3  | C1  | C0  |
|    12 |  0.5072 |   2.3083 | cap4_acc80     | INC | DEC | C0  | C1  | C3  |
|    13 |  2.0277 |   2.9992 | cap4_acc80     | INC | DEC | C1  | C2  | C3  |
|    14 |  2.8542 |   3.5393 | cap4_ghost | C1  | DEC | C0  | INC | C2  |
|    15 |  3.0755 |   3.7917 | cap4_ghost | C1  | INC | C2  | DEC | C0  |
|    16 |  2.1918 |   3.9017 | cap4_acc80     | INC | DEC | C0  | C2  | C3  |
|    17 |  2.6429 |   3.9496 | cap4_ghost | INC | C1  | C0  | DEC | C2  |
|    18 |  2.6014 |   3.9990 | cap4_ghost | DEC | C1  | C2  | INC | C0  |

## Same wirings sorted by stage-1 deficit

| Place |  S1 Def | Viol Def | Model                         | INC | DEC | C0  | C1  | C2  |
| ----- | ------- | -------- | ----------------------------- | --- | --- | --- | --- | --- |
|     1 |  0.0000 |   1.1137 | cap4_ghost | INC | DEC | C0  | C1  | C2  |
|     2 |  0.0048 |   1.2194 | cap4_acc70     | INC | DEC | C1  | C2  | C3  |
|     3 |  0.0136 |   1.1062 | cap4_ghost | DEC | INC | C2  | C1  | C0  |
|     4 |  0.0263 |   1.2435 | cap4_acc70     | DEC | INC | C2  | C1  | C0  |
|     5 |  0.0577 |   1.3079 | cap4_acc80     | DEC | INC | C2  | C1  | C0  |
|     6 |  0.0661 |   1.9920 | cap4_acc70     | INC | DEC | C0  | C2  | C3  |
|     7 |  0.1369 |   1.9721 | cap4_acc70     | DEC | INC | C3  | C1  | C0  |
|     8 |  0.1386 |   1.4486 | cap4_acc70     | INC | DEC | C0  | C1  | C2  |
|     9 |  0.1386 |   2.1138 | cap4_acc70     | INC | DEC | C0  | C1  | C3  |
|    10 |  0.3795 |   1.6938 | cap4_acc80     | INC | DEC | C0  | C1  | C2  |
|    11 |  0.4764 |   2.2437 | cap4_acc80     | DEC | INC | C3  | C1  | C0  |
|    12 |  0.5072 |   2.3083 | cap4_acc80     | INC | DEC | C0  | C1  | C3  |
|    13 |  2.0277 |   2.9992 | cap4_acc80     | INC | DEC | C1  | C2  | C3  |
|    14 |  2.1918 |   3.9017 | cap4_acc80     | INC | DEC | C0  | C2  | C3  |
|    15 |  2.6014 |   3.9990 | cap4_ghost | DEC | C1  | C2  | INC | C0  |
|    16 |  2.6429 |   3.9496 | cap4_ghost | INC | C1  | C0  | DEC | C2  |
|    17 |  2.8542 |   3.5393 | cap4_ghost | C1  | DEC | C0  | INC | C2  |
|    18 |  3.0755 |   3.7917 | cap4_ghost | C1  | INC | C2  | DEC | C0  |
