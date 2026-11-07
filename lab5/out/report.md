# Lab 5: Reusing move evaluations in local search

Authors: Piotr Foltyniewicz 160295, Jakub Adamski 160291

## Problem description

Select 100 distinct nodes from 200 and order them into a closed cycle. Input rows contain `x;y;cost`; node IDs are zero-based row indices. Minimize selected-node costs plus Euclidean edge lengths rounded to the nearest integer, including the closing edge.

```text
F(S) = sum(cost[S[i]] + dist(S[i], S[(i+1) mod m]), i=0..m-1)
```

## Pseudocode

Use the lab 3 edge-exchange neighborhood: selected/unselected node replacement and intra-route 2-opt. No candidate lists are used. The baseline recomputes every applicable delta after each accepted move. LM uses the assignment's alternative algorithm: reuse saved deltas until no saved move applies, then rebuild the list.

### Representation and starting solutions

`n = 200`, `m = 100`; indices are cyclic. `pos[v]` is the current position of node v, or -1 if unselected. A saved move stores `(delta, type, a, b, c, d)` using node IDs. `INTER` replaces b by d with neighbors a,c; `EDGES` removes (a,b),(c,d) and adds (a,c),(b,d). LM is a min-priority queue ordered by `(delta, type, a, b, c, d)`, with INTER before EDGES.

```text
POSITIONS(S):
    pos[0..n-1] = -1
    for i = 0..m-1: pos[S[i]] = i
    return pos

EXPERIMENT(instance):
    read nodes; precompute rounded symmetric distances
    for method in [BASELINE, MOVE_LIST]:
        rng = mt19937(seed=20261107)
        repeat 200 times:
            start timer
            S = first m nodes of shuffle([0..n-1], rng)
            S, value = method(S)
            stop timer; export value and S
        export minimum, maximum, mean value and mean elapsed time
```

Both methods receive identical random starts within each instance. Reproducibility of `std::shuffle` requires the same standard-library implementation.

### Generate improving moves

```text
GENERATE(S, pos, includeInverted):
    moves = []
    for i = 0..m-1:
        a = S[(i-1) mod m]; b = S[i]; c = S[(i+1) mod m]
        for d = 0..n-1 where pos[d] == -1:
            delta = dist(a,d) + dist(d,c) - dist(a,b) - dist(b,c)
                    + cost[d] - cost[b]
            if delta < 0: append (delta, INTER, a,b,c,d)
    for i = 0..m-1:
        for j = i+2..m-1:
            if i == 0 and j == m-1: continue  // closing-edge adjacency
            a = S[i]; b = S[(i+1) mod m]
            c = S[j]; d = S[(j+1) mod m]
            removed = dist(a,b) + dist(c,d)
            delta = dist(a,c) + dist(b,d) - removed
            if delta < 0: append (delta, EDGES, a,b,c,d)
            if includeInverted:
                delta = dist(a,d) + dist(b,c) - removed
                if delta < 0: append (delta, EDGES, a,b,d,c)
    return moves
```

The inverted descriptor is initially deferred. Both orientations are evaluated during initialization and every rebuild. Symmetric distances make the cached delta valid when both defining edges reverse.

### Check saved moves

```text
EDGE_DIRECTION(S, pos, a, b):
    if pos[a] == -1 or pos[b] == -1: return MISSING
    if S[(pos[a]+1) mod m] == b: return FORWARD
    if S[(pos[b]+1) mod m] == a: return REVERSED
    return MISSING

STATUS(S, pos, move):
    (_, type, a,b,c,d) = move
    if type == INTER:
        if pos[d] != -1 or pos[b] == -1: return INVALID
        if EDGE_DIRECTION(S,pos,a,b) == MISSING: return INVALID
        if EDGE_DIRECTION(S,pos,b,c) == MISSING: return INVALID
        return APPLICABLE  // same neighbors in either order
    first = EDGE_DIRECTION(S,pos,a,b)
    second = EDGE_DIRECTION(S,pos,c,d)
    if first == MISSING or second == MISSING: return INVALID
    if first == second: return APPLICABLE  // also both reversed
    return DEFERRED  // opposite relative directions; keep for later

TAKE_APPLICABLE(LM, S, pos):
    deferred = []; chosen = NONE
    while LM is not empty:
        move = pop minimum from LM
        status = STATUS(S,pos,move)
        if status == APPLICABLE:
            chosen = move
            break
        if status == DEFERRED: append move to deferred
        // INVALID moves are discarded
    reinsert all deferred moves into LM
    return chosen
```

### Apply moves and run the searches

```text
APPLY(S, pos, move):
    (_, type, a,b,c,d) = move
    if type == INTER:
        S[pos[b]] = d
    else:
        forward = EDGE_DIRECTION(S,pos,a,b) == FORWARD
        i = pos[a] if forward else pos[b]
        j = pos[c] if forward else pos[d]
        if i > j: swap(i,j)
        reverse S[i+1 .. j]  // inclusive endpoints

BASELINE(S):
    value = F(S)
    loop:
        pos = POSITIONS(S)
        moves = GENERATE(S,pos,false)  // all currently applicable improvements
        if moves is empty: return S,value
        move = minimum-delta move, keeping first generated on ties
        APPLY(S,pos,move)
        value += move.delta

MOVE_LIST(S):
    value = F(S); pos = POSITIONS(S)
    LM = heapify(GENERATE(S,pos,true))
    loop:
        move = TAKE_APPLICABLE(LM,S,pos)
        if move == NONE:
            LM = heapify(GENERATE(S,pos,true))
            move = TAKE_APPLICABLE(LM,S,pos)
            if move == NONE: return S,value
        APPLY(S,pos,move)
        value += move.delta
        pos = POSITIONS(S)
```

The baseline implementation scans all moves and retains only the best; the pseudocode's temporary list expresses the same selection. It breaks ties by generation order; LM breaks ties by stored node IDs. Rebuilding LM regenerates surviving deferred descriptors and avoids duplicates. Stop when a fresh list has no applicable improvement, even if it still contains deferred moves. This guarantees a full-neighborhood local optimum. Between rebuilds, LM chooses the best applicable cached move; newly created improvements wait until the next rebuild.

A baseline iteration evaluates 14,850 moves. An LM rebuild evaluates 19,700 descriptors, including inverted edge pairs. Applicability checks take O(1); heap operations take O(log L) for L saved moves. Rebuilding positions takes O(n+m), and reversing a segment takes O(m). Deferred entries may be revisited, so a speedup is measured rather than guaranteed.

## Results

Each method runs 200 times per instance: 800 searches in total. Lab 5 methods are bold; **Steepest Edges Random** is this lab's baseline. Available historical summaries are marked by lab number. Objectives are **average (minimum - maximum)**, with the lowest minimum per lab and instance in bold. Lower values are better.

### Objective function values

| Method | TSPA | TSPB |
|---|---:|---:|
| **Steepest Edges Random (baseline)** | 76282.22 (73825 - 80885) | 52617.19 (**50056** - 55057) |
| **Move List Edges Random** | 76245.98 (**73815** - 80002) | 52471.51 (50420 - 55821) |
| Steepest Edges Random (lab 4) | 76126.85 (**73288** - 79682) | 52712.36 (49816 - 55429) |
| Candidate Edges k5 Random (lab 4) | 76993.97 (74191 - 80983) | 52818.47 (50722 - 56889) |
| Candidate Edges k10 Random (lab 4) | 76278.36 (73966 - 79184) | 52640.37 (50362 - 56836) |
| Candidate Edges k20 Random (lab 4) | 76095.42 (**73288** - 80182) | 52675.29 (**49459** - 55512) |
| Steepest Nodes Random (lab 3) | 90017.03 (82067 - 97807) | 65860.14 (58859 - 72495) |
| Steepest Nodes Greedy (lab 3) | 73021.71 (**71955** - 74861) | 54292.07 (49978 - 61265) |
| Steepest Edges Random (lab 3) | 76234.49 (73409 - 79907) | 52513.55 (50126 - 55265) |
| Steepest Edges Greedy (lab 3) | 73003.80 (**71955** - 74861) | 53091.28 (**49346** - 60354) |
| Greedy Nodes Random (lab 3) | 88281.52 (83276 - 97988) | 63685.80 (57875 - 70381) |
| Greedy Nodes Greedy (lab 3) | 73021.00 (**71955** - 74861) | 54258.15 (49978 - 61265) |
| Greedy Edges Random (lab 3) | 76362.62 (74427 - 78668) | 52948.87 (50667 - 56093) |
| Greedy Edges Greedy (lab 3) | 72983.31 (**71955** - 74877) | 53151.86 (49546 - 60357) |
| Greedy Cycle 2-regret heuristics (lab 2) | 120378.77 (112806 - 128089) | 72484.84 (68150 - 77274) |
| Greedy Cycle heuristics with a weighted sum criterion (lab 2) | 73353.51 (**72011** - 75532) | 57866.33 (52731 - 63370) |
| NN heuristics 2-regret heuristics (lab 2) | 121360.29 (110950 - 135771) | 73649.84 (68761 - 79756) |
| NN heuristics with a weighted sum criterion (lab 2) | 75561.20 (72419 - 78504) | 55698.34 (**50485** - 61406) |
| Random (lab 1) | 262009.64 (234223 - 288919) | 206071.06 (181689 - 230681) |
| Nearest Node End (lab 1) | 87476.63 (84362 - 90075) | 59397.34 (56007 - 63166) |
| Nearest Node Any (lab 1) | 74306.53 (**72328** - 77022) | 59476.23 (**52915** - 66164) |
| Greedy Cycle (lab 1) | 73743.73 (72590 - 75281) | 59650.81 (55655 - 63734) |

### Running times (ms)

Mean total time per run, including random-start construction and search. LM initialization and rebuilds are included; distance preprocessing is excluded. Starting-solution time is not measured separately in lab 5. Historical times are shown for context; speed ratios use only the baseline rerun in lab 5.

| Method | TSPA | TSPB |
|---|---:|---:|
| **Steepest Edges Random (baseline)** | 21.588618 | 21.747047 |
| **Move List Edges Random** | 2.059028 | 1.866873 |
| Steepest Edges Random (lab 4) | 33.799286 | 34.286283 |
| Candidate Edges k5 Random (lab 4) | 4.173085 | 3.818066 |
| Candidate Edges k10 Random (lab 4) | 7.909238 | 6.727505 |
| Candidate Edges k20 Random (lab 4) | 14.563482 | 12.108440 |
| Steepest Nodes Random (lab 3) | 66.795616 | 66.738804 |
| Steepest Nodes Greedy (lab 3) | 5.276252 | 8.437412 |
| Steepest Edges Random (lab 3) | 34.488630 | 35.122619 |
| Steepest Edges Greedy (lab 3) | 4.453417 | 7.405829 |
| Greedy Nodes Random (lab 3) | 27.378438 | 29.323703 |
| Greedy Nodes Greedy (lab 3) | 5.271248 | 7.354972 |
| Greedy Edges Random (lab 3) | 24.915344 | 25.450824 |
| Greedy Edges Greedy (lab 3) | 4.911828 | 7.588654 |
| Greedy Cycle 2-regret heuristics (lab 2) | 3.767999 | 3.729813 |
| Greedy Cycle heuristics with a weighted sum criterion (lab 2) | 3.722352 | 3.621625 |
| NN heuristics 2-regret heuristics (lab 2) | 3.826779 | 3.824544 |
| NN heuristics with a weighted sum criterion (lab 2) | 3.893400 | 4.053285 |
| Random (lab 1) | 0.032951 | 0.013712 |
| Nearest Node End (lab 1) | 0.256396 | 0.118587 |
| Nearest Node Any (lab 1) | 3.829626 | 3.895479 |
| Greedy Cycle (lab 1) | 2.859520 | 3.091238 |

## Best solutions and visualizations

Node color indicates selection cost; gray nodes are unselected. Blue edges form the cycle and the red star marks its first listed node. Read node IDs left to right, then top to bottom.

### TSPA

#### Steepest Edges Random (baseline)

Objective: **73825**.

![TSPA: Steepest Edges Random](generated/TSPA_Steepest%20Edges%20Random.png)

**Solution (tour order):**

```text
  1 101  55  29 178 136 186 164   9  54
 33  52 144  67  16  51 156  35 185  45
 87 102  28 180 141  30 160  83 123  90
100  38 132  76   4  71 157  91  80  48
 31 108 152  49  11  60 116 149  63 168
 95  97 127  69 129 104  92 171   2 187
189  98 114 181 135  73 140  53 179 177
 36 131 134  84  58 192 158 182  57  64
107  88  78 153 170 159 130 113  89  42
151 176 174 150 106  93  47  50   3 169
```

#### Move List Edges Random

Objective: **73815**.

![TSPA: Move List Edges Random](generated/TSPA_Move%20List%20Edges%20Random.png)

**Solution (tour order):**

```text
142   8 174  85   3   1 169  50  93  43
113  89  42 151 106 150 176 134  84 131
 54   9  33  36 177 179  52  67 144  53
140  73 135  45 185  35  16  51 139 112
  4  76 132  71 157  91  38  80  48   7
 31  60 116 149  63 168  49 108 152 100
 90 123  83 160  97 127 171   2 187  30
141 180  28 102  87  98 114 181  58 192
158 182  57  64  88  78 193 153 107 159
130  47 147 101  55  29 178 136 186 164
```

### TSPB

#### Steepest Edges Random (baseline)

Objective: **50056**.

![TSPB: Steepest Edges Random](generated/TSPB_Steepest%20Edges%20Random.png)

**Solution (tour order):**

```text
181 167  59  85  51  82  87 179  88  99
171  74  20  14   2  93 110 153  90 129
 80 127  10 114 196 139  61 105  94  81
 70 187  54 192 162  76 185  57  89 156
 43  48  96 198 121  42 147 116 130  30
183  21  38  47 140 154  97 170 177 125
 26 158 149  28 145  65 178 103 132  29
197   6 115 155  71 175 134  45 157  60
 40  64 124  69 160 172 136 133 120  72
 46  86   3 184 122 151  67  24  34 152
```

#### Move List Edges Random

Objective: **50420**.

![TSPB: Move List Edges Random](generated/TSPB_Move%20List%20Edges%20Random.png)

**Solution (tour order):**

```text
130 191  30 183  21  38 158 149 146  13
 28 145  65 178 103 132  29   6 197  36
 62 175 134  45 157  60  40  71 155 115
170 177 125 154 140  47  64  73  59  85
 51 167 152 181 179  87  99 171  74  20
  2  93 110  14 153  52  90 129  80 127
 78  10 114 196  61 105  94  81  70 187
 54 192 162  66  67  24  34   3 184 151
 69 160 172 136 133   8 117 120  72  46
 86 135  76 185  57  89  48  96 198 121
```

## Solution checking

All 800 exported cycles were checked for exactly 100 distinct valid node IDs. Independently recomputed objectives match the exports; summary minima, maxima and means match the 200 runs in each group. The four plotted solutions attain the reported minima. This script checks feasibility and objective consistency, not local optimality or timing accuracy.

## Source code

- [LM search](../src/move_list_search.cpp)
- [Experiment runner](../src/lab5_experiment.cpp)
- [Baseline from lab 3](../../lab3/src/local_search_methods.cpp)
- [Report generator](../src/create_report.py)
- [All runs](generated/results.csv)
- [Summary](generated/summary.csv)
- [Best solutions](generated/best_solutions.csv)

## Conclusions

On TSPA, mean time is 21.589 ms for the baseline and 2.059 ms for LM (baseline/LM time ratio: 10.48x; above 1 means LM is faster). Mean objective changes from 76282.22 to 76245.98 (-0.048%; negative means improvement).

On TSPB, mean time is 21.747 ms for the baseline and 1.867 ms for LM (baseline/LM time ratio: 11.65x; above 1 means LM is faster). Mean objective changes from 52617.19 to 52471.51 (-0.277%; negative means improvement).

LM reuses evaluations while preserving the full neighborhood at termination. Its search path can differ from the baseline because new improvements wait for a rebuild and ties use a different order. The observed time and quality differences describe these 200 starts per instance.
