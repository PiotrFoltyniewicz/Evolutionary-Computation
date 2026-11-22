# Lab 7 - Large neighborhood search

Authors - Piotr Foltyniewicz 160295, Jakub Adamski 160291

## Problem description

Select 100 distinct nodes from 200 and arrange them in a closed cycle. Minimize selected-node costs plus rounded Euclidean edge lengths, including the closing edge. Node IDs are zero-based row indices. Distances are rounded to the nearest integer, with halves rounded upward.

```text
F(S) = sum(cost[S[i]] + dist(S[i], S[(i+1) mod 100]), i=0..99)
```

## Pseudocode

### Large neighborhood search

```text
LNS(operator, useLS, cycleRepair, rng, T)
    start = NOW()
    deadline = start + T
    best = first 100 nodes of SHUFFLE([0,...,199], rng)
    bestValue = LS(best)
    initialValue = bestValue
    iterations = 0
    lsCalls = 1
    accepted = 0
    while NOW() < deadline
        candidate = DESTROY(best, operator, rng)
        if cycleRepair == false
            ROTATE(candidate, uniform random origin, rng)
        value = REPAIR(candidate, cycleRepair)
        if useLS
            value = LS(candidate)
            lsCalls += 1
        iterations += 1
        if value < bestValue
            best = COPY(candidate)
            bestValue = value
            accepted += 1
    return best, bestValue, iterations, lsCalls, accepted, NOW() - start
```

### Random node removal

Shuffle all 100 cycle positions and delete the first 30 positions. Read survivors in their original cyclic order and connect consecutive survivors, including the last and first nodes.

```text
RANDOM_NODES(S, rng)
    positions = SHUFFLE([0,...,99], rng)
    removed = SET(positions[0:30])
    return [S[i] for i in 0..99 where i is outside removed]
```

### Single random subpath removal

Choose a start uniformly among the 100 cycle positions and delete the next 30 consecutive positions modulo 100. Connect survivors.

```text
SINGLE_SUBPATH(S, rng)
    start = uniform integer in [0,99]
    removed = {(start+j) mod 100 for j in 0..29}
    return [S[i] for i in 0..99 where i is outside removed]
```

### Multiple random subpath removal

Choose k uniformly from 3, 4 and 5. Split the 30 removed positions into k random lengths, and independently split the 70 surviving positions into k gap lengths. Choose a random origin and alternate a deleted subpath and a survivor gap around the cycle. Gaps ensure exactly k disjoint deleted subpaths. Connect survivors.

```text
MULTIPLE_SUBPATHS(S, rng)
    k = uniform integer in [3,5]
    lengths = POSITIVE_COMPOSITION(30, k, rng)
    gaps = POSITIVE_COMPOSITION(70, k, rng)
    position = uniform integer in [0,99]
    removed = empty set
    for segment in 0..k-1
        repeat lengths[segment] times
            add position to removed
            position = (position+1) mod 100
        position = (position+gaps[segment]) mod 100
    return [S[i] for i in 0..99 where i is outside removed]
```

### Weighted-regret repair

Choose the greedy heuristic with the lowest earlier mean objective separately for each instance. TSPA uses weighted-regret greedy-cycle insertion. TSPB uses weighted-regret nearest-neighbor insertion.

For TSPA, consider every edge of the partial cycle, including the closing edge. For TSPB, rotate the 70 survivors by a uniformly random offset and treat them as an open path, so starting/ending nodes change every time. Consider all internal insertion positions and the two endpoints, then close the completed path for objective evaluation.

For each unselected node v, find the two smallest insertion costs b1 and b2 over available positions. Insertion at an open endpoint costs one added edge plus cost[v]. Regret is b2-b1. Choose the node minimizing 0.5*b1-0.5*regret and insert it at its cheapest position. Equal scores favor the lower node ID, and equal insertion costs favor the first enumerated position.

```text
REPAIR(S, cycle)
    available = {0,...,199} minus SET(S)
    while LENGTH(S) < 100
        bestScore = infinity
        for v in available in increasing node-ID order
            positions = cycle edges if cycle else all path positions
            b1, b2, position = TWO_BEST_INSERTIONS(S, v, positions)
            regret = b2-b1
            score = 0.5*b1 - 0.5*regret
            if score < bestScore
                bestScore = score
                chosen = v
                chosenPosition = position
        INSERT(S, chosenPosition, chosen)
        REMOVE(available, chosen)
    return F(S)
```

### Steepest local search

```text
LS(S)
    value = F(S)
    LM = GENERATE_ALL_IMPROVING_MOVE_DESCRIPTORS(S)
    loop
        move = TAKE_LOWEST_DELTA_APPLICABLE_MOVE(LM, S)
        if move == NONE
            LM = GENERATE_ALL_IMPROVING_MOVE_DESCRIPTORS(S)
            move = TAKE_LOWEST_DELTA_APPLICABLE_MOVE(LM, S)
            if move == NONE
                return value
        APPLY(move, S)
        value += move.delta
```

## Results

### Objective function values

Entries show mean (minimum - maximum). Lower values are better.

| Method | TSPA | TSPB |
|---|---:|---:|
| LNS Random Nodes | 72274.55 (71735 - 72980) | 49168.25 (48472 - 50030) |
| LNS Random Nodes + LS | 72194.65 (71746 - 72912) | 48952.40 (48228 - 49676) |
| LNS Single Subpath | 72241.60 (71827 - 73064) | 49588.05 (49016 - 50597) |
| LNS Single Subpath + LS | 72097.80 (71827 - 72969) | 48792.25 (48379 - 49537) |
| LNS Multiple Subpaths | 71780.90 (71704 - 71858) | 49003.65 (48466 - 49939) |
| LNS Multiple Subpaths + LS | **71715.50** (**71650** - 71870) | **48578.55** (**48218** - 49260) |
| MSLS (lab 6) | 73608.50 (73386 - 74027) | 50296.75 (49926 - 50760) |
| ILS (lab 6) | **71695.15** (**71534** - 71998) | **48346.10** (**48152** - 48551) |
| Move List Edges Random LS (lab 5) | 76245.98 (73815 - 80002) | 52471.51 (50420 - 55821) |
| Greedy Cycle with a weighted sum (lab 2) | 73353.51 (72011 - 75532) | 57866.33 (52731 - 63370) |
| NN with a weighted sum (lab 2) | 75561.20 (72419 - 78504) | 55698.34 (50485 - 61406) |




### Running times

Mean milliseconds per complete run.

| Method | TSPA | TSPB |
|---|---:|---:|
| LNS Random Nodes | 850.340871 | 835.192614 |
| LNS Random Nodes + LS | 850.271179 | 835.641578 |
| LNS Single Subpath | 850.351831 | 835.249443 |
| LNS Single Subpath + LS | 850.318938 | 835.420002 | 
| LNS Multiple Subpaths | 850.446852 | 835.212920 |
| LNS Multiple Subpaths + LS | 850.570457 | 835.251685 |
| MSLS (lab 6) | 849.712655 | 834.701505 |
| ILS (lab 6) | 850.016989 | 834.894892 |
| Move List Edges Random LS (lab 5) | 1.165003 | 1.158196 |
| Greedy Cycle heuristics with a weighted sum criterion (lab 2) | 1.473993 | 1.453700 |
| NN heuristics with a weighted sum criterion (lab 2) | 1.497114 | 1.497218 |



### Number of main-loop iterations

Entries show mean (minimum - maximum) across 20 runs. Initial local search is excluded.

| Method | TSPA | TSPB |
|---|---:|---:|
| LNS Random Nodes | 798.25 (747 - 880) | 777.00 (551 - 834) |
| LNS Random Nodes + LS | 675.10 (630 - 733) | 603.60 (412 - 711) |
| LNS Single Subpath | 761.85 (665 - 826) | 650.85 (510 - 787) |
| LNS Single Subpath + LS | 627.55 (458 - 683) | 622.00 (472 - 688) |
| LNS Multiple Subpaths | 714.45 (554 - 836) | 825.85 (781 - 854) |
| LNS Multiple Subpaths + LS | 560.45 (453 - 687) | 676.30 (614 - 716) |

## Best solutions and visualizations

### TSPA

#### LNS Random Nodes

Objective **71735**, run **10** (zero-based).

![TSPA - LNS Random Nodes](generated/TSPA_LNS%20Random%20Nodes.png)

**Solution node order**

```text
158 192 111 182  57  64 107  88  78 193
153 170 146 159 130  47 147 101  29 178
184 136 186 164 142  85   1 169   3  50
 93 113  89  42 151 106 150 176 174   8
 54   9  33 131  36 177  52 179  53 140
144  67  16  51  35 185 102  28 180 132
 76   4  71 157  91  80  48  31  60 108
152 100 123  83 160  49  11  63 149 116
168  97 127  69  92 171   2 189 187  30
141  87  45  73 135 114 181  58  84 134
```

#### LNS Random Nodes + LS

Objective **71746**, run **17** (zero-based).

![TSPA - LNS Random Nodes + LS](generated/TSPA_LNS%20Random%20Nodes%20%2B%20LS.png)

**Solution node order**

```text
192 158  58  84 134  72 176 174 150 106
113  89  42 151 138 182  57  64 107  88
 78 193 153 170 146 159 130  47 147 101
 29 178 184 136 186 164   1 169   3  50
 93  85 142   8  54   9  33 131  36 177
 52 179  53 140 144  67  16  51  35 185
102  28 180 132  76   4  71 157  91  80
 48  31  60 108 152 100 123 160  49  11
 63 149 116 168  97 127  69  92 171   2
189 187  30 141  87  45  73 135 114 181
```

#### LNS Single Subpath

Objective **71827**, run **6** (zero-based).

![TSPA - LNS Single Subpath](generated/TSPA_LNS%20Single%20Subpath.png)

**Solution node order**

```text
106 151  42  89 113  93  50   3 169   1
 85 142 164 186 136 184 178  29 101 147
 37  47 130 159 146 170 153 193  78  88
107  64  57 182 111 192 158 134  84  58
181 114 135  73  45  87 141 189   2 171
187  30 161 127  97 160  83 123 100 152
108  49  11 168  63 149 116  60  31  48
 80  91 157  71   4  76 132 180  28 102
185  35  51  16  67 144 140  53 179  52
177  36 131  33   9  54   8 174 176 150
```

#### LNS Single Subpath + LS

Objective **71827**, run **7** (zero-based).

![TSPA - LNS Single Subpath + LS](generated/TSPA_LNS%20Single%20Subpath%20%2B%20LS.png)

**Solution node order**

```text
 76 132 180  28 102 185  35  51  16  67
144 140  53 179  52 177  36 131  33   9
 54   8 174 176 150 106 151  42  89 113
 93  50   3 169   1  85 142 164 186 136
184 178  29 101 147  37  47 130 159 146
170 153 193  78  88 107  64  57 182 111
192 158 134  84  58 181 114 135  73  45
 87 141 189   2 171 187  30 161 127  97
160  83 123 100 152 108  49  11 168  63
149 116  60  31  48  80  91 157  71   4
```

#### LNS Multiple Subpaths

Objective **71704**, run **14** (zero-based).

![TSPA - LNS Multiple Subpaths](generated/TSPA_LNS%20Multiple%20Subpaths.png)

**Solution node order**

```text
 92  69 127  97 160  83 123 100 152 108
 49  11 168  63 149 116  60  31  48  80
 91 157  71   4  76 132 180  28 156  35
 51  16  67 144 140  53 179  52 177  36
131  33   9  54   8 142 164 186 136 184
178  29 101   1 169   3  50  93  47 130
159 146 170 153 193  78  88 107  64  57
182 138 151  42  89 113 106 150 174 176
 72 134  84  58 158 192 181 114 135  73
 45 185 102  87 141  30 187 189   2 171
```

#### LNS Multiple Subpaths + LS

Objective **71650**, run **5** (zero-based).

![TSPA - LNS Multiple Subpaths + LS](generated/TSPA_LNS%20Multiple%20Subpaths%20%2B%20LS.png)

**Solution node order**

```text
113  89  42 151 182  57  64 107  88  78
193 153 170 146 159 130  93  50   3 169
  1  47 147 101  29 178 184 136 186 164
142   8  54   9  33 131  36 177  52 179
 53 140 144  67  16  51  35 156  28 180
132  76   4  71 157  91  80  48  31  60
116 149  63 168  11  49 108 152 100 123
 83 160  97 127  69  92 171   2 189 187
 30 141  87 102 185  45  73 135 114 181
192 158  58  84 134  72 176 174 150 106
```

### TSPB

#### LNS Random Nodes

Objective **48472**, run **15** (zero-based).

![TSPB - LNS Random Nodes](generated/TSPB_LNS%20Random%20Nodes.png)

**Solution node order**

```text
 71 155  97 154 140  47  38  21  30 130
183 189  69 160 172 136 133 120   8 117
 72  46 184   3 151  27  66  67  24  34
152 181 167  73  59  85  51  82  87 179
 88  99 171  17  74  20   2  14 153  90
129 127  80 192 162  54  78  10 114 196
187  70 190 104  76 185  57  89 156  48
 96 198 121  42 147 116  37 146  13 149
 28 145 158 177 125 170 115 180   6  29
132 197  36  62 175 134  45 157  60  40
```

#### LNS Random Nodes + LS

Objective **48228**, run **15** (zero-based).

![TSPB - LNS Random Nodes + LS](generated/TSPB_LNS%20Random%20Nodes%20%2B%20LS.png)

**Solution node order**

```text
 89  57 185  76 162 192  54 187  70 190
 81  94 105  61 196 114  10  90 129 127
 80 182 153  14   2  20  74  17 171  99
 88 179  87  82  51  85  59  73 167 181
152  34  24  67  66  27 151   3 184  46
 72 117 120 133 136 172 160  69 189 183
 30  21  38  47 140 154  97 155  71  40
 60 157  45 134 175  62  36 197 132  29
  6 180 115 170 125 177 158 145  28 149
 13 146  37 116 147  42 121 198  96  48
```

#### LNS Single Subpath

Objective **49016**, run **6** (zero-based).

![TSPB - LNS Single Subpath](generated/TSPB_LNS%20Single%20Subpath.png)

**Solution node order**

```text
 60 157  45 134 175  62  36 197   6  29
132 103 178  65 145  28 149 158 177 125
170 115  97 154 140  47  38  21  30 191
130 121 198  96  48 156  89  57 185  76
104 194 190  70 187 196 114  10  78  54
162 192  80 127 129  90 153  74  20  14
  2  17 171  99  88 179  87  82  51  85
 59  73 167 181 152  34  24  67  66  27
151   3 184  46  72 117   8 120 133 136
172 160  69 124  64  33  40 141 155  71
```

#### LNS Single Subpath + LS

Objective **48379**, run **15** (zero-based).

![TSPB - LNS Single Subpath + LS](generated/TSPB_LNS%20Single%20Subpath%20%2B%20LS.png)

**Solution node order**

```text
 45 134 175  62  36 197 132  29   6 180
115 170 125 158 145  28 149  13 146  37
116 147  42 121 198  96  48 156  89  57
185  76 104 190  70 187 169  81  94 105
 61 196 114  10  78  54 162 192  80 127
129  90 153  14   2  20  74  17 171  99
 88 179  87  82  51  85  59  73 167 181
152  67  24  34  98 151   3 184  46  72
120 133 136 172 160  69 189 183  30  21
 38  47 140 154  97 155  71  40  60 157
```

#### LNS Multiple Subpaths

Objective **48466**, run **7** (zero-based).

![TSPB - LNS Multiple Subpaths](generated/TSPB_LNS%20Multiple%20Subpaths.png)

**Solution node order**

```text
 34 152 181 167  73  59  85  51  82  87
179  88  99 171  17  74  20   2  14 153
 90 129 127  80 192 162  54  78  10 114
196 187  70 190 104  76 185  57  89 156
 48  96 198 121  42 147 116  37 146  13
149  28 145  65 178 103 132  29   6 197
 36  62 175 134  45 157  60  40  71 155
 97 115 170 177 125  26 154 140  47  38
 21  30 183 168  69 160 172 136 133 120
  8 117  72  46 184   3 151  98  24  67
```

#### LNS Multiple Subpaths + LS

Objective **48218**, run **10** (zero-based).

![TSPB - LNS Multiple Subpaths + LS](generated/TSPB_LNS%20Multiple%20Subpaths%20%2B%20LS.png)

**Solution node order**

```text
167 181 152  34  24  67  66  27 151   3
184  46  72 117 120 133 136 172 160  69
183  30  21  38  47 140 154  26 125 177
170 115 155  71  40  60 157  45 134 175
 62  36 197   6  29 132 103 178  65 145
 28 149  13 146  37 116 147  42 121 198
 96  48 156  89  57 185  76 162 192  54
187  70 190  81  94 105  61 196 114  10
127  80 129  90 153  14   2  20  74  17
171  99  88 179  87  82  51  85  59  73
```

## Source code

- [LNS and destroy operators](../src/lns.cpp)
- [Experiment runner](../src/lab7_experiment.cpp)
- [Weighted-regret repair](../../lab2/src/lab2_methods.cpp)
- [Move-list steepest local search](../../lab5/src/move_list_search.cpp)
- [Validation and report generator](../src/create_report.py)
- [Lab6 report and full LS pseudocode](../../lab6/out/report.md)
- [Historical MSLS/ILS results and budgets](../../lab6/out/generated/summary.csv)
- [Historical construction and LS comparisons](../../lab6/out/generated/comparison_summary.csv)

## Conclusions

LNS Multiple Subpaths + LS achieves the lowest mean objective among LNS variants on both instances:
| Instance | Mean | Best | Mean iterations | Mean vs. MSLS | Mean vs. ILS |
|---|---:|---:|---:|---:|---:|
| TSPA | 71715.50 | 71650 | 560.45 | 2.572% lower | 0.028% higher |
| TSPB | 48578.55 | 48218 | 676.30 | 3.416% lower | 0.481% higher |

Post-repair LS improves the mean objective for every destroy operator, while reducing iteration counts. Across 20 paired runs per operator, it wins 12–18 times on TSPA and 17–20 times on TSPB.

Overall, LNS Multiple Subpaths + LS outperforms MSLS on average and approaches ILS. ILS retains lower mean and best objectives on both instances.