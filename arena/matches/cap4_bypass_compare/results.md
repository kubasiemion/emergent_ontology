# Cap4 acc80 model vs itself: read-token GRU bypass on vs off.

| Place |  Deficit | Model           | INC | DEC | C0  | C1  | C2  | C3  |
| ----- | -------- | --------------- | --- | --- | --- | --- | --- | --- |
|     1 |   0.0518 | cap4_bypass_on  | INC | DEC | C0  | C1  | C2  | C3  |
|     2 |   0.6736 | cap4_bypass_on  | DEC | INC | C3  | C2  | C1  | C0  |
|     3 |   2.8308 | cap4_bypass_on  | INC | DEC | C0  | C2  | C1  | C3  |
|     4 |   3.4324 | cap4_bypass_on  | DEC | INC | C2  | C3  | C1  | C0  |
|     5 |   4.0815 | cap4_bypass_on  | INC | DEC | C0  | C1  | C3  | C2  |
|     6 |   4.4219 | cap4_bypass_on  | DEC | INC | C3  | C1  | C2  | C0  |
|     7 |   6.0289 | cap4_bypass_off | INC | C3  | C0  | DEC | C1  | C2  |
|     8 |   6.8781 | cap4_bypass_off | C3  | INC | C2  | C1  | DEC | C0  |
|     9 |   6.9376 | cap4_bypass_off | INC | C3  | DEC | C0  | C1  | C2  |
|    10 |   7.2878 | cap4_bypass_off | INC | DEC | C3  | C0  | C1  | C2  |
|    11 |   7.3098 | cap4_bypass_off | DEC | INC | C2  | C1  | C0  | C3  |
|    12 |   8.0172 | cap4_bypass_off | C3  | INC | C2  | C1  | C0  | DEC |
