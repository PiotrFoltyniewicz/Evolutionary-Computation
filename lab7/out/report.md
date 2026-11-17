# Lab 7 - Large neighborhood search

Authors - Piotr Foltyniewicz 160295, Jakub Adamski 160291

## Problem description

Select 100 distinct nodes from 200 and arrange them in a closed cycle. Minimize selected-node costs plus rounded Euclidean edge lengths, including the closing edge. Node IDs are zero-based row indices. Distances are rounded to the nearest integer, with halves rounded upward.

```text
F(S) = sum(cost[S[i]] + dist(S[i], S[(i+1) mod 100]), i=0..99)
```

## Pseudocode

### Large neighborhood search

All six variants start from a random permutation of the 200 nodes truncated to 100 nodes. Apply steepest local search to this initial solution. Every main-loop iteration destroys a copy of the incumbent, repairs it to 100 nodes, optionally applies local search, and accepts a strict decrease in F. Rejected candidates leave the incumbent available for the next iteration.

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

Shuffle all 100 cycle positions and delete the first 30 positions. Every size-30 subset has equal probability. Read survivors in their original cyclic order and connect consecutive survivors, including the last and first nodes. The operator returns a 70-node partial cycle.

```text
RANDOM_NODES(S, rng)
    positions = SHUFFLE([0,...,99], rng)
    removed = SET(positions[0:30])
    return [S[i] for i in 0..99 where i is outside removed]
```

### Single random subpath removal

Choose a start uniformly among the 100 cycle positions and delete the next 30 consecutive positions modulo 100. This includes subpaths crossing the stored last-to-first boundary. Keep the other 70 nodes in cyclic order.

```text
SINGLE_SUBPATH(S, rng)
    start = uniform integer in [0,99]
    removed = {(start+j) mod 100 for j in 0..29}
    return [S[i] for i in 0..99 where i is outside removed]
```

### Multiple random subpath removal

Choose k uniformly from 3, 4 and 5. Split the 30 removed positions into k positive random lengths, and independently split the 70 surviving positions into k positive gap lengths. Choose a random origin and alternate a deleted subpath and a survivor gap around the cycle. Positive gaps ensure exactly k disjoint deleted subpaths. The total number removed is always 30.

A positive composition of a total into k parts is sampled by shuffling the boundaries from 1 through total-1, taking k-1 boundaries, sorting them with 0 and total, and returning consecutive differences. This samples positive ordered compositions uniformly. Survivors retain their cyclic order.

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

Choose the greedy heuristic with the lowest earlier mean objective separately for each instance, considering construction methods from labs 1 and 2, including regret. TSPA uses weighted-regret greedy-cycle insertion, with an earlier mean of 73353.51. TSPB uses weighted-regret open-path insertion, with an earlier mean of 55698.34. This choice is fixed from the historical comparisons saved in lab6 and is shared by all six variants on that instance.

For TSPA, consider every edge of the partial cycle, including the closing edge. For TSPB, rotate the 70 survivors by a uniformly random offset and treat them as an open path. This randomly chooses which survivor edge is broken. Consider all internal insertion positions and the two endpoints, then close the completed path for objective evaluation.

For each unselected node v, find the two smallest insertion costs b1 and b2 over available positions. Insertion cost includes the cost of v. An internal insertion between a and b costs dist(a,v)+dist(v,b)-dist(a,b)+cost[v]. Insertion at an open endpoint costs one added edge plus cost[v]. Regret is b2-b1. Choose the node minimizing 0.5*b1-0.5*regret and insert it at its cheapest position. Equal scores favor the lower node ID, and equal insertion costs favor the first enumerated position. Repeat until 100 nodes are selected. Removed nodes and nodes outside the previous incumbent are all eligible.

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

The implementation calls the existing lab2 weighted-regret selector to complete a partial solution.

### Steepest local search

Use the move-list steepest search from lab5, also used by MSLS and ILS in lab6. It searches node replacements with unselected nodes and intra-cycle 2-opt edge exchanges. A replacement includes the difference in node costs. A 2-opt move reverses the segment between two nonadjacent cycle edges. At each step the search applies the lowest-delta applicable improving move. The move list is rebuilt when no stored improving move applies. Search ends when a freshly rebuilt list also has no applicable improving move.

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

The full move descriptors, validity checks and reversal handling are documented in the lab6 report. The + LS variants apply this search after every repair. Every variant applies it once before the main loop.

### Computational experiment

Run each of the three destroy operators with and without post-repair local search, giving six methods. Use exactly 30% removal. Run each method 20 times on TSPA and TSPB, giving 240 runs. Seed run r on instance i with 20261117+1000*i+r, where i=0 for TSPA, i=1 for TSPB and r ranges from 0 to 19. All six variants share the same random start and initial local optimum for a given instance and run. Each variant then uses its own generator object.

Set each instance's time budget to the average duration of its 20 complete MSLS runs saved in lab6. TSPA uses 470.65018675 ms and TSPB uses 469.3097464 ms. These are the budgets used by the C++ runner. Timing starts before initial solution generation and includes initial local search, destroy, repair, and subsequent local search. Complete each iteration started before the deadline, so a run can exceed its limit by the remainder of one iteration.

Count complete main-loop iterations, excluding initial local search. Without post-repair LS, the LS count is 1. With post-repair LS, it is iterations+1. Record strict accepted improvements, initial objective, final cycle, seed, elapsed time and budget in the raw results.

Earlier MSLS and ILS results come from lab6. Earlier greedy and local-search comparisons use lab6's saved comparison table, where the methods were rerun on the same machine. Select the best greedy and the best local search by mean objective on each instance and include both instance winners. Also include the exact move-list LS kernel. The historical construction and single-start LS summaries each cover 200 starts, while each metaheuristic summary covers 20 runs. Timing figures describe the saved experiments and depend on compiler and machine load.

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
| LNS Multiple Subpaths + LS | 71715.50 (71650 - 71870) | 48578.55 (48218 - 49260) |
| Greedy Cycle heuristics with a weighted sum criterion (lab 2) | 73353.51 (72011 - 75532) | 57866.33 (52731 - 63370) |
| NN heuristics with a weighted sum criterion (lab 2) | 75561.20 (72419 - 78504) | 55698.34 (50485 - 61406) |
| Greedy Edges Greedy (lab 3) | 72989.61 (71955 - 74861) | 53171.39 (49537 - 60266) |
| Move List Edges Random (lab 5) | 76245.98 (73815 - 80002) | 52471.51 (50420 - 55821) |
| MSLS (lab 6) | 73608.50 (73386 - 74027) | 50296.75 (49926 - 50760) |
| ILS (lab 6) | 71695.15 (71534 - 71998) | 48346.10 (48152 - 48551) |

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
| Greedy Cycle heuristics with a weighted sum criterion (lab 2) | 1.473993 | 1.453700 |
| NN heuristics with a weighted sum criterion (lab 2) | 1.497114 | 1.497218 |
| Greedy Edges Greedy (lab 3) | 2.079999 | 2.803250 |
| Move List Edges Random (lab 5) | 1.165003 | 1.158196 |
| MSLS (lab 6) | 849.712655 | 834.701505 |
| ILS (lab 6) | 850.016989 | 834.894892 |

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

## Solution checking

All 240 exported cycles contain 100 distinct valid node IDs. Independently recomputed objectives and summary statistics match the CSV records. Each group contains exactly 20 runs. Recorded seeds, shared initial local optima, time budgets, elapsed times, accepted improvements and LS counts are consistent. All 120 final cycles from + LS runs have no improving node replacement or 2-opt move in the full neighborhood. All 12 plotted cycles attain their group minima.

## Source code

- [LNS and destroy operators](../src/lns.cpp)
- [Experiment runner](../src/lab7_experiment.cpp)
- [Weighted-regret repair](../../lab2/src/lab2_methods.cpp)
- [Move-list steepest local search](../../lab5/src/move_list_search.cpp)
- [Validation and report generator](../src/create_report.py)
- [Lab6 report and full LS pseudocode](../../lab6/out/report.md)
- [Historical MSLS/ILS results and budgets](../../lab6/out/generated/summary.csv)
- [Historical construction and LS comparisons](../../lab6/out/generated/comparison_summary.csv)

- [All 240 raw results](generated/results.csv)
- [Summary](generated/summary.csv)
- [Main-loop iterations](generated/iterations.csv)
- [Comparison summaries](generated/comparison_summary.csv)
- [Best solutions](generated/best_solutions.csv)

## Conclusions

On TSPA, LNS Multiple Subpaths + LS has the lowest LNS mean objective of 71715.50, with a best value of 71650. Its mean run completes 560.45 main-loop iterations.

Its mean is 2.572% lower than MSLS's 73608.50. The best MSLS value is 73386.

Its mean is 0.028% higher than ILS's 71695.15. The best ILS value is 71534.

For Random Nodes on TSPA, post-repair LS changes the mean from 72274.55 to 72194.65. Mean iterations change from 798.25 to 675.10. In 20 comparisons with the same initial local optimum, the + LS variant wins 12, ties 1, and loses 7.

For Single Subpath on TSPA, post-repair LS changes the mean from 72241.60 to 72097.80. Mean iterations change from 761.85 to 627.55. In 20 comparisons with the same initial local optimum, the + LS variant wins 14, ties 1, and loses 5.

For Multiple Subpaths on TSPA, post-repair LS changes the mean from 71780.90 to 71715.50. Mean iterations change from 714.45 to 560.45. In 20 comparisons with the same initial local optimum, the + LS variant wins 18, ties 0, and loses 2.

On TSPB, LNS Multiple Subpaths + LS has the lowest LNS mean objective of 48578.55, with a best value of 48218. Its mean run completes 676.30 main-loop iterations.

Its mean is 3.416% lower than MSLS's 50296.75. The best MSLS value is 49926.

Its mean is 0.481% higher than ILS's 48346.10. The best ILS value is 48152.

For Random Nodes on TSPB, post-repair LS changes the mean from 49168.25 to 48952.40. Mean iterations change from 777.00 to 603.60. In 20 comparisons with the same initial local optimum, the + LS variant wins 18, ties 0, and loses 2.

For Single Subpath on TSPB, post-repair LS changes the mean from 49588.05 to 48792.25. Mean iterations change from 650.85 to 622.00. In 20 comparisons with the same initial local optimum, the + LS variant wins 20, ties 0, and loses 0.

For Multiple Subpaths on TSPB, post-repair LS changes the mean from 49003.65 to 48578.55. Mean iterations change from 825.85 to 676.30. In 20 comparisons with the same initial local optimum, the + LS variant wins 17, ties 0, and loses 3.

Each LNS variant runs under the same per-instance historical MSLS budget. Iteration counts measure the search performed within that budget. The two instances use different repair variants, so comparisons between destroy operators are made within each instance. These are descriptive results over the measured runs.
