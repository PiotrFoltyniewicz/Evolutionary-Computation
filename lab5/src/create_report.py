"""Validate lab5 exports, plot best cycles, and rebuild the Markdown report.

Run from any directory: python lab5/src/create_report.py
Requires the CSV exports from make run-lab5 and matplotlib.
"""

from __future__ import annotations

import csv
import math
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import quote

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "common" / "src"))
from visualize_experiments import plot_solution, read_nodes, read_results  # noqa: E402

OUT = REPO / "lab5" / "out"
GENERATED = OUT / "generated"
BASELINE = "Steepest Edges Random"
MOVE_LIST = "Move List Edges Random"
METHODS = (BASELINE, MOVE_LIST)
INSTANCES = ("TSPA", "TSPB")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_summary(lab):
    path = REPO / lab / "out" / "generated" / "summary.csv"
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    summaries = {(row["instance"], row["method"]): row for row in rows}
    require(len(rows) == len(summaries), f"Duplicate summary entries in {path}")
    return summaries


def formatted(value, places=2):
    return format(Decimal(str(value)).quantize(
        Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP), f".{places}f")


def validate(groups, summaries):
    expected = {(instance, method) for instance in INSTANCES for method in METHODS}
    require(set(groups) == expected, "Expected both lab5 methods on TSPA and TSPB")
    require(set(summaries) == expected, "Summary groups do not match lab5 methods")
    checked = 0
    for instance in INSTANCES:
        nodes = read_nodes(REPO / "common" / "data" / f"{instance}.csv")
        require(len(nodes) == 200, f"{instance}: expected 200 nodes")
        distances = [[math.floor(math.hypot(a[0] - b[0], a[1] - b[1]) + 0.5)
                      for b in nodes] for a in nodes]
        for method in METHODS:
            records = groups[(instance, method)]
            label = f"{instance}, {method}"
            require(len(records) == 200 and
                    {int(row["run"]) for row in records} == set(range(200)),
                    f"{label}: expected runs 0 through 199 exactly once")
            for row in records:
                solution = row["solution"]
                require(len(solution) == 100 and len(set(solution)) == 100 and
                        all(0 <= node < 200 for node in solution),
                        f"{label}, run {row['run']}: invalid cycle")
                actual = sum(nodes[u][2] + distances[u][solution[(i + 1) % 100]]
                             for i, u in enumerate(solution))
                require(actual == row["objective"],
                        f"{label}, run {row['run']}: objective mismatch")
                checked += 1
            row = summaries[(instance, method)]
            values = [record["objective"] for record in records]
            require(min(values) == int(row["min"]) and max(values) == int(row["max"]) and
                    abs(sum(values) / len(values) - float(row["average"])) < 1e-6,
                    f"{label}: summary does not match results")
            time = float(row["average_time_ms"])
            require(math.isfinite(time) and time > 0, f"{label}: invalid running time")
    return checked


def results_tables(summaries, previous):
    rows = []
    for lab, data in [(5, summaries), *sorted(previous.items(), reverse=True)]:
        methods = METHODS if lab == 5 else list(dict.fromkeys(method for _, method in data))
        minima = {instance: min(int(row["min"]) for (name, _), row in data.items()
                                 if name == instance) for instance in INSTANCES}
        for method in methods:
            label = (f"**{method}{' (baseline)' if method == BASELINE else ''}**"
                     if lab == 5 else f"{method} (lab {lab})")
            values, times = [], []
            for instance in INSTANCES:
                row = data[(instance, method)]
                minimum = f"**{row['min']}**" if int(row["min"]) == minima[instance] else row["min"]
                values.append(f"{formatted(row['average'])} ({minimum} - {row['max']})")
                times.append(formatted(row["average_time_ms"], 6))
            rows.append((label, values, times))
    lines = ["### Objective function values", "", "| Method | TSPA | TSPB |", "|---|---:|---:|"]
    lines.extend(f"| {label} | {' | '.join(values)} |" for label, values, _ in rows)
    lines.extend(["", "### Running times (ms)", "",
                  "Mean total time per run, including random-start construction and search. LM initialization and rebuilds are included; distance preprocessing is excluded. Starting-solution time is not measured separately in lab 5. Historical times are shown for context; speed ratios use only the baseline rerun in lab 5.", "",
                  "| Method | TSPA | TSPB |", "|---|---:|---:|"])
    lines.extend(f"| {label} | {' | '.join(times)} |" for label, _, times in rows)
    return lines + [""]


DESCRIPTION = """# Lab 5: Reusing move evaluations in local search

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
"""


def main():
    groups = read_results(GENERATED / "results.csv")
    summaries = read_summary("lab5")
    checked = validate(groups, summaries)
    previous = {lab: read_summary(f"lab{lab}") for lab in (1, 2, 3, 4)
                if (REPO / f"lab{lab}" / "out" / "generated" / "summary.csv").exists()}
    lines = [DESCRIPTION, *results_tables(summaries, previous),
             "## Best solutions and visualizations", "",
             "Node color indicates selection cost; gray nodes are unselected. Blue edges form the cycle and the red star marks its first listed node. Read node IDs left to right, then top to bottom.", ""]
    best_records = []
    for instance in INSTANCES:
        lines.extend([f"### {instance}", ""])
        for method in METHODS:
            best = min(groups[(instance, method)], key=lambda row: (row["objective"], int(row["run"])))
            image = f"{instance}_{method}.png"
            plot_solution(read_nodes(REPO / "common" / "data" / f"{instance}.csv"), best,
                          GENERATED / image, f"{instance}: {method}")
            solution = best["solution"]
            tour = "\n".join(" ".join(f"{u:3d}" for u in solution[i:i+10])
                             for i in range(0, len(solution), 10))
            lines.extend([f"#### {method}{' (baseline)' if method == BASELINE else ''}", "",
                          f"Objective: **{best['objective']}**.", "",
                          f"![{instance}: {method}](generated/{quote(image)})", "",
                          "**Solution (tour order):**", "", "```text", tour, "```", ""])
            best_records.append({"instance": instance, "method": method, "objective": best["objective"],
                                 "run": best["run"], "solution": " ".join(map(str, solution))})
    with (GENERATED / "best_solutions.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["instance", "method", "objective", "run", "solution"])
        writer.writeheader()
        writer.writerows(best_records)
    lines.extend(["## Solution checking", "",
                  f"All {checked} exported cycles were checked for exactly 100 distinct valid node IDs. Independently recomputed objectives match the exports; summary minima, maxima and means match the 200 runs in each group. The four plotted solutions attain the reported minima. This script checks feasibility and objective consistency, not local optimality or timing accuracy.", "",
                  "## Source code", "",
                  "- [LM search](../src/move_list_search.cpp)",
                  "- [Experiment runner](../src/lab5_experiment.cpp)",
                  "- [Baseline from lab 3](../../lab3/src/local_search_methods.cpp)",
                  "- [Report generator](../src/create_report.py)",
                  "- [All runs](generated/results.csv)",
                  "- [Summary](generated/summary.csv)",
                  "- [Best solutions](generated/best_solutions.csv)", "",
                  "## Conclusions", ""])
    for instance in INSTANCES:
        baseline = summaries[(instance, BASELINE)]
        lm = summaries[(instance, MOVE_LIST)]
        ratio = float(baseline["average_time_ms"]) / float(lm["average_time_ms"])
        change = (float(lm["average"]) / float(baseline["average"]) - 1) * 100
        lines.extend([f"On {instance}, mean time is {formatted(baseline['average_time_ms'], 3)} ms for the baseline and {formatted(lm['average_time_ms'], 3)} ms for LM (baseline/LM time ratio: {ratio:.2f}x; above 1 means LM is faster). Mean objective changes from {formatted(baseline['average'])} to {formatted(lm['average'])} ({change:+.3f}%; negative means improvement).", ""])
    lines.extend(["LM reuses evaluations while preserving the full neighborhood at termination. Its search path can differ from the baseline because new improvements wait for a rebuild and ties use a different order. The observed time and quality differences describe these 200 starts per instance.", ""])
    report = "\n".join(lines)
    (OUT / "report.md").write_text(report, encoding="utf-8")
    (GENERATED / "final_results.txt").write_text(report, encoding="utf-8")
    print(f"Validated {checked} solutions; wrote four plots and {OUT / 'report.md'}")


if __name__ == "__main__":
    main()
