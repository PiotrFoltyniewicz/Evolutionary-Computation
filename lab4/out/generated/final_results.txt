# Lab 4: Candidate moves in local search

Authors: Piotr Foltyniewicz 160295, Jakub Adamski 160291

## Problem description

Each instance consists of 200 nodes. A row in the input file contains the node's planar coordinates and selection cost, in the form `x;y;cost`. Node indices are zero-based and correspond to row order. The task is to select exactly 100 distinct nodes (half of the available nodes), order them, and form a closed cycle that minimizes the sum of travel distances and selected-node costs.

Distances are Euclidean, rounded to the nearest integer and precomputed after reading the instance. All algorithms use this distance matrix. The evaluation sums all selected-node costs and all cycle edges, including last -> first. In the pseudocode, `m = 100`, `n = 200`, `c[v]` is node cost, and `d(a, b)` is the precomputed distance. A solution `S` is an ordered list of `m` distinct nodes; `U` denotes the set of nodes not in `S`.

The objective for an ordered selection `S` is:

```text
F(S) = sum(c[S[i]]) + sum(d(S[i], S[(i + 1) mod length(S)]))
```

## Pseudocode

All indices are zero-based. Local search starts from a given solution and applies moves until none improves the objective. Moves are evaluated only through deltas; the neighbor solution is never built and `F` is never recalculated from scratch. Lab 3 found edge exchange (2-opt) to be the best intra-route neighborhood from random starts on both instances, so we combine it with inter-route replacement. Candidate lists restrict this neighborhood to moves introducing at least one candidate edge. The full-neighborhood steepest search is rerun as a baseline.

### Candidate edges

For each node u, choose k other nodes minimizing `d(u, v) + c[v]`, breaking ties by node index. The list is directional because the destination costs differ. An undirected edge {u, v} is a candidate if v belongs to the nearest list of u OR u belongs to the nearest list of v. Store the union in both endpoints' adjacency lists, without duplicates or self-loops. Reverse incidence also covers candidate edges proposed by a currently unselected node.

```text
BUILD_CANDIDATES(k):
    A = empty symmetric adjacency lists
    for u in all nodes:
        C[u] = k smallest v != u by (d(u, v) + c[v], v)
        for v in C[u]:
            add v to A[u] and u to A[v], without duplicates
    return A
```

The primary setting is k = 10, as specified in the assignment. Settings k = 5 and k = 20 show the time-quality tradeoff. The undirected union can give a node more than k incident candidate edges; k always denotes the original directional list length.

### Generating the two moves for an edge

An inter-route move replaces one selected node by an unselected node. A 2-opt move removes two nonadjacent cycle edges and reverses the segment between them. All positions, predecessors, and successors below are cyclic, including the closing edge. An edge-cut index identifies the edge starting at that position.

```text
CANDIDATE_MOVES(S, A):
    pos[v] = position of v in S, or -1 if unselected
    for position i in S:
        u = S[i]
        for v in A[u]:
            if pos[v] == -1:
                emit INTER(prev(i), v)
                emit INTER(next(i), v)
            else if u < v:                 // visit selected pair once
                j = pos[v]
                emit TWO_OPT(i, j)         // cut after u and v
                emit TWO_OPT(prev(i), prev(j)) // cut before u and v
            // Skip equal or adjacent cuts in both TWO_OPT cases.
```

For inter-route moves, u stays in the cycle and either neighbor of u is replaced by v, so the new edge {u, v} is actually introduced. Replacing u itself by one of its nearest nodes would not guarantee this condition. For 2-opt, cutting after both endpoints or before both endpoints gives the two reconnections introducing {u, v}. Invalid cuts sharing a node are skipped. A move can be emitted twice if both newly introduced edges are candidates; this only repeats a delta evaluation and does not change the neighborhood or result.

### Move deltas and steepest search

No neighbor solution is constructed to evaluate a move. Internal reversed edges have equal costs because distances are symmetric.

```text
DELTA_INTER(S, p, v):
    out = S[p]; a = S[prev(p)]; b = S[next(p)]
    return d(a,v) + d(v,b) - d(a,out) - d(out,b) + c[v] - c[out]

DELTA_TWO_OPT(S, i, j):
    a = S[i]; b = S[next(i)]; c = S[j]; e = S[next(j)]
    return d(a,c) + d(b,e) - d(a,b) - d(c,e)

CANDIDATE_STEEPEST(S, A):
    value = F(S)
    loop:
        best = NONE; bestDelta = 0
        for move in CANDIDATE_MOVES(S, A):
            delta = DELTA(S, move)
            if delta < bestDelta: best = move; bestDelta = delta
            // Equal negative deltas: use the baseline's move order.
        if best == NONE: return S, value
        APPLY(S, best)
        value += bestDelta
```

Ties between improving moves are resolved by type (inter-route first), then the two descriptor indices, matching lab 3. The full baseline examines all `m(n-m) + m(m-3)/2 = 14850` moves per iteration. The candidate version loops only over selected nodes and incident candidate lists; it never scans the full neighborhood to filter it. There are at most nk undirected candidate edges, so generation and delta evaluation per iteration take O(m + nk), instead of O(m(n-m) + m^2). Candidate preprocessing uses partial sorting in O(n^2 log k) time, plus O(n^2) to materialize the symmetric lists. The implementation uses an O(n^2) temporary adjacency matrix during preprocessing. Iteration counts can differ because restricting the neighborhood changes the search path.

### Starting solutions

Each of the four methods was run 200 times on TSPA and 200 times on TSPB: 1600 searches in total. A `std::mt19937` generator with seed 20261031 produces permutations of all 200 nodes; the first 100 form each starting cycle. The generator is reset before each method, so all methods use the same sequence of starting cycles. The seed reproduces starts with the same C++ standard library; `std::shuffle` need not give identical permutations across different library implementations.

The baseline calls the unchanged `steepestLocalSearch` from lab 3 with edge exchange. The shared `runExperiment` function performs all runs, records statistics and CSV results, and measures random-start construction plus local search with `std::chrono::steady_clock`. Distance matrices and candidate lists are built once before the runs and are outside the measured interval. The supplied results use the Makefile's optimized C++20 build through WSL.

## Results

Each of the four methods was run 200 times on each instance. Results of labs 1-3 are copied from their current summaries and marked with the lab number; methods measured in lab 4 are in bold. The lab 4 baseline and the historical lab 3 result are shown separately because they use different samples of random starts.

Objective values use the format **average (minimum – maximum)**; running times are averages per run in milliseconds. Lower objective values are better. The lowest minimum within each lab and instance is in bold.

### Objective function values

| Method | TSPA | TSPB |
|---|---:|---:|
| **Steepest Edges Random (baseline)** | 76126.85 (**73288** – 79682) | 52712.36 (49816 – 55429) |
| **Candidate Edges k5 Random** | 76993.97 (74191 – 80983) | 52818.47 (50722 – 56889) |
| **Candidate Edges k10 Random** | 76278.36 (73966 – 79184) | 52640.37 (50362 – 56836) |
| **Candidate Edges k20 Random** | 76095.42 (**73288** – 80182) | 52675.29 (**49459** – 55512) |
| Steepest Nodes Random (lab 3) | 90292.47 (84621 – 99661) | 65902.04 (60136 – 75295) |
| Steepest Nodes Greedy (lab 3) | 73021.71 (**71955** – 74861) | 54292.07 (49978 – 61265) |
| Steepest Edges Random (lab 3) | 76108.17 (73719 – 79105) | 52640.92 (50335 – 55286) |
| Steepest Edges Greedy (lab 3) | 73003.80 (**71955** – 74861) | 53091.28 (**49346** – 60354) |
| Greedy Nodes Random (lab 3) | 88266.88 (82357 – 98469) | 63746.16 (59205 – 70900) |
| Greedy Nodes Greedy (lab 3) | 73019.87 (**71955** – 74877) | 54310.27 (49913 – 61265) |
| Greedy Edges Random (lab 3) | 76299.05 (73468 – 80279) | 53038.72 (50575 – 55602) |
| Greedy Edges Greedy (lab 3) | 72984.73 (**71955** – 74861) | 53251.93 (49660 – 60266) |
| Greedy Cycle 2-regret heuristics (lab 2) | 120378.77 (112806 – 128089) | 72484.84 (68150 – 77274) |
| Greedy Cycle heuristics with a weighted sum criterion (lab 2) | 73353.51 (**72011** – 75532) | 57866.33 (52731 – 63370) |
| NN heuristics 2-regret heuristics (lab 2) | 121360.29 (110950 – 135771) | 73649.84 (68761 – 79756) |
| NN heuristics with a weighted sum criterion (lab 2) | 75561.20 (72419 – 78504) | 55698.34 (**50485** – 61406) |
| Random (lab 1) | 261559.68 (234022 – 287462) | 205914.49 (183676 – 233336) |
| Nearest Node End (lab 1) | 87476.63 (84362 – 90075) | 59397.34 (56007 – 63166) |
| Nearest Node Any (lab 1) | 74306.53 (**72328** – 77022) | 59476.23 (**52915** – 66164) |
| Greedy Cycle (lab 1) | 73743.73 (72590 – 75281) | 59650.81 (55655 – 63734) |

### Running times (ms)

Total times cover the complete run: creating the starting solution and performing local search. Candidate lists are built once per instance and method, outside the measured runs. Starting-solution times for lab 3 are copied from its current report. Empty cells mean that starting-solution time was not measured separately (lab 4) or that there is no separate starting-solution stage (labs 1-2).

Labs 1-3 retain their original measurements. Lab 4 was measured separately, so speedups are calculated against the baseline rerun in lab 4, using the same starts and environment as the candidate methods.

| Method | TSPA: total | TSPA: starting solution | TSPB: total | TSPB: starting solution |
|---|---:|---:|---:|---:|
| **Steepest Edges Random (baseline)** | 11.449964 |  | 11.400661 |  |
| **Candidate Edges k5 Random** | 1.594667 |  | 1.306085 |  |
| **Candidate Edges k10 Random** | 2.821714 |  | 2.459391 |  |
| **Candidate Edges k20 Random** | 5.448459 |  | 4.453391 |  |
| Steepest Nodes Random (lab 3) | 67.694814 | 0.003531 | 66.661623 | 0.003519 |
| Steepest Nodes Greedy (lab 3) | 5.657000 | 4.066111 | 8.942153 | 4.111100 |
| Steepest Edges Random (lab 3) | 35.005239 | 0.003531 | 35.416348 | 0.003519 |
| Steepest Edges Greedy (lab 3) | 4.856945 | 4.066111 | 9.898119 | 4.111100 |
| Greedy Nodes Random (lab 3) | 28.357479 | 0.003531 | 28.458643 | 0.003519 |
| Greedy Nodes Greedy (lab 3) | 5.509622 | 4.066111 | 6.848713 | 4.111100 |
| Greedy Edges Random (lab 3) | 24.942397 | 0.003531 | 24.829678 | 0.003519 |
| Greedy Edges Greedy (lab 3) | 5.153622 | 4.066111 | 8.615719 | 4.111100 |
| Greedy Cycle 2-regret heuristics (lab 2) | 4.517217 |  | 3.915432 |  |
| Greedy Cycle heuristics with a weighted sum criterion (lab 2) | 4.066111 |  | 3.760381 |  |
| NN heuristics 2-regret heuristics (lab 2) | 4.025403 |  | 4.062423 |  |
| NN heuristics with a weighted sum criterion (lab 2) | 4.148715 |  | 4.111100 |  |
| Random (lab 1) | 0.030866 |  | 0.011238 |  |
| Nearest Node End (lab 1) | 0.142488 |  | 0.078278 |  |
| Nearest Node Any (lab 1) | 4.214506 |  | 3.637342 |  |
| Greedy Cycle (lab 1) | 3.036610 |  | 2.781263 |  |

## Best solutions and visualizations

Node color represents selection cost; the compact horizontal scale below each plot uses the same cost range for all methods on an instance. Gray nodes are not selected, blue segments form the closed tour, and the red star marks the first node in the displayed sequence. Lists below show ten node indices per row; read left to right, then top to bottom to follow the tour. Only methods measured in lab 4 are visualized; historical results from labs 1-3 appear only in the Results tables.

### TSPA

#### Steepest Edges Random

Objective: **73288**.

![TSPA: Steepest Edges Random](generated/TSPA_Steepest%20Edges%20Random.png)

**Solution (tour order):**

```text
 84 134 176 150 106  43 113  89  42 151
138 182  57 107  88  78 193 153 170 159
130  47  93  50   3 169   1  59 178 101
 29 136 186 164  85 174   8  54   9 143
 33 131  36 177  52 179  53 140 144  67
 16  51 139 112  71 157  91  80  48  31
 60 108 152  49  11  63 149 116 168  97
127 161  30 160  83 123  90 132  76   4
156  35 185 102  28 180 141 187 171   2
189  87  45  73 135 114 181 192 158  58
```

#### Candidate Edges k5 Random

Objective: **74191**.

![TSPA: Candidate Edges k5 Random](generated/TSPA_Candidate%20Edges%20k5%20Random.png)

**Solution (tour order):**

```text
136  29 178 184 164  85  93  50   3 169
  1 147  47 130 159 146 170 153 193  78
 88 107  89 106 150 151  57 182 138 158
192 181 114 135  73  58  84 134 131  36
177 179  53 140 144  67  45  87 141 189
  2 171 104 129  69 127  97 168 116 149
 63  11  49 152 108  60  82  31  48  80
 91 157  71  38   4  76 132  90 123  83
160 161 187  30 180  28 102 185  35 156
 51  16  52  33   9  54 176 174   8 186
```

#### Candidate Edges k10 Random

Objective: **73966**.

![TSPA: Candidate Edges k10 Random](generated/TSPA_Candidate%20Edges%20k10%20Random.png)

**Solution (tour order):**

```text
 80  48  31  60 116 149  63 168  97 127
 69 171   2 187  30 141  87  28 180 156
 35 185  45  73 135 181  58 192 158 111
138 182  57 107  88  78 193 153 170 146
159 130  47  93  85   3  50 169   1 178
 29 136 186 184 164 142 174 150 106  43
113  89  42 151 176  72 134  84 131   8
194  54   9  33  36 177  52 179  53 140
144  67  16  51 139 112   5 115 157  91
 71   4  76 132  90 123 160  49 108 152
```

#### Candidate Edges k20 Random

Objective: **73288**.

![TSPA: Candidate Edges k20 Random](generated/TSPA_Candidate%20Edges%20k20%20Random.png)

**Solution (tour order):**

```text
 84 134 176 150 106  43 113  89  42 151
138 182  57 107  88  78 193 153 170 159
130  47  93  50   3 169   1  59 178 101
 29 136 186 164  85 174   8  54   9 143
 33 131  36 177  52 179  53 140 144  67
 16  51 139 112  71 157  91  80  48  31
 60 108 152  49  11  63 149 116 168  97
127 161  30 160  83 123  90 132  76   4
156  35 185 102  28 180 141 187 171   2
189  87  45  73 135 114 181 192 158  58
```

### TSPB

#### Steepest Edges Random

Objective: **49816**.

![TSPB: Steepest Edges Random](generated/TSPB_Steepest%20Edges%20Random.png)

**Solution (tour order):**

```text
 94  81 187  70 190  57  89 156  48  96
198 121  42 147 116  37 149  28 145 158
 26 125 177 170 115   6  29 132 197 175
134  45 157  60  40  71  97 154 140  47
 38  21  30 130 183 172 160  69 151   3
184 117   8 136 133 120  72  46  86  75
135  76 185 104 162 159  54 192  84  66
 67  24  34 152 181 167  73  59  85  51
179  82  87  88  99 171  74  20   2  14
153  90 129  80 127  10 114 196  61 105
```

#### Candidate Edges k5 Random

Objective: **50722**.

![TSPB: Candidate Edges k5 Random](generated/TSPB_Candidate%20Edges%20k5%20Random.png)

**Solution (tour order):**

```text
145  28 149  13 146  37 116 147 121 198
 96  48 156  89  57  76 104 190  70 187
196 114  10  54 162 192 127 129  90  52
 80 150 182 153  14   2  20  74 171  99
 87  82 179  51  85  59  73 167 181 152
 34  24  67   3 184 151 122  69 160 172
136   8 117  46  86  72 120 133 189 183
 30  21  38  47 140 154 125 170 115  97
155  71 141  40  60  45 134 175  62 108
174   1 132  29 197   6 178  65 138 158
```

#### Candidate Edges k10 Random

Objective: **50362**.

![TSPB: Candidate Edges k10 Random](generated/TSPB_Candidate%20Edges%20k10%20Random.png)

**Solution (tour order):**

```text
162 104  57 185  76 135  75  86  46  72
 89 156  48  96 198 121  42 147 116  37
146 149  28 145 158 125 170 115 180   6
 29 132   1 174 197  36 175 134  45 157
 60  40  71 155  97 154 140  47  38  21
172 136 133 120 117 160  69 122 184   3
151  73  59  85  51 167 181 152  34  24
 11  66  67 179  82  87  88  99 171  74
  2  14  20 153  80 127 129  90  10 148
114 196  61 105  94  81 190  70 187  54
```

#### Candidate Edges k20 Random

Objective: **49459**.

![TSPB: Candidate Edges k20 Random](generated/TSPB_Candidate%20Edges%20k20%20Random.png)

**Solution (tour order):**

```text
 99 171  17  74  20   2  14 153  90 129
 80 127  10 143 148 114 196 139  61 105
 94  81 190  70 187  54 192 162 104  76
185  57  89 156  48  96 198 121 147 116
 37 149  28 145  65 178 132  29   6 197
175 134  45 157  60  40  71 155 115 170
125  26 154 140  47  38  21 183  30 130
120 133 136 172  69 160   8 117  72  46
184   3 173 122 151  27  66  67  24  34
152 181 167  59  85  51  82  87 179  88
```

## Solution checking

All 1600 exported solutions were independently checked in Python: exactly 100 distinct node indices in 0-199, and recomputed rounded-distance objectives equal the incremental C++ objectives. All CSV minima, maxima, and means were recomputed. All eight plotted best solutions match the summary minima.

## Source code

Repository: [PiotrFoltyniewicz/Evolutionary-Computation](https://github.com/PiotrFoltyniewicz/Evolutionary-Computation). The implementation and exported evidence are included in this project:

- [Candidate lists, move generation, deltas, and steepest search](../src/candidate_search.cpp)
- [Experiment runner](../src/lab4_experiment.cpp)
- [Unchanged full-neighborhood baseline](../../lab3/src/local_search_methods.cpp)
- [Validation and report generator](../src/create_report.py)
- [All runs](generated/results.csv)
- [Summary](generated/summary.csv)
- [Best solutions](generated/best_solutions.csv)

- [Lab 3 report](../../lab3/out/report.md)
- [Lab 3 summary](../../lab3/out/generated/summary.csv)
- [Lab 2 summary](../../lab2/out/generated/summary.csv)
- [Lab 1 summary](../../lab1/out/generated/summary.csv)

## Conclusions

On TSPA, k = 10 reduces average total time from 11.450 to 2.822 ms (4.06x speedup). The mean objective changes from 76126.85 to 76278.36 (+0.199%).

On TSPB, k = 10 reduces average total time from 11.401 to 2.459 ms (4.64x speedup). The mean objective changes from 52712.36 to 52640.37 (-0.137%).

On TSPA, Candidate Edges k5 Random is the fastest tested candidate method; Candidate Edges k20 Random gives the lowest candidate mean (76095.42, versus 76126.85 for the full baseline).

The best candidate mean on TSPA is 76095.42; the best mean from earlier labs is 72984.73 (Greedy Edges Greedy, lab 3).

On TSPB, Candidate Edges k5 Random is the fastest tested candidate method; Candidate Edges k10 Random gives the lowest candidate mean (52640.37, versus 52712.36 for the full baseline).

The best candidate mean on TSPB is 52640.37; the best mean from earlier labs is 52640.92 (Steepest Edges Random, lab 3).

Increasing k raises the number of candidate moves and does not guarantee a better local optimum in every run, because the steepest move can lead to a different search trajectory. These observations describe this sample of starts, not a guarantee that restricted search dominates full search.

The required k = 10 setting gives a substantial speedup with a small change in mean quality. Restricting the moves changes the stopping condition: a candidate-local optimum may still admit an improving non-candidate move. The results support candidate lists as an effective time-quality tradeoff for these instances.
