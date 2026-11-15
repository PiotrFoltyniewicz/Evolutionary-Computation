"""Validate lab4 exports, plot best cycles, and rebuild the Markdown report."""

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

OUT = REPO / "lab4" / "out"
GENERATED = OUT / "generated"
BASELINE = "Steepest Edges Random"


def read_summary(lab):
    with (REPO / lab / "out" / "generated" / "summary.csv").open(newline="", encoding="utf-8") as stream:
        return {(row["instance"], row["method"]): row for row in csv.DictReader(stream)}


def formatted(value, places=2):
    return format(Decimal(str(value)).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP), f".{places}f")


def lab3_starting_times():
    report = (REPO / "lab3" / "out" / "report.md").read_text(encoding="utf-8")
    section = report.split("### Running times (ms)", 1)[1].split("\n## ", 1)[0]
    times = {}
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip().replace("**", "") for cell in line.strip("|").split("|")]
        if len(cells) == 5 and cells[2] and cells[4] and cells[0] != "Method":
            if cells[2].replace(".", "").isdigit() and cells[4].replace(".", "").isdigit():
                times[("TSPA", cells[0])] = cells[2]
                times[("TSPB", cells[0])] = cells[4]
    return times


def results_tables(summaries, previous):
    # Keep the same method ordering and two-instance columns as the lab3 report.
    labs = [(4, summaries), *[(lab, previous[lab]) for lab in (3, 2, 1)]]
    rows = []
    for lab, data in labs:
        methods = list(dict.fromkeys(method for _, method in data))
        minima = {instance: min(int(row["min"]) for (name, _), row in data.items() if name == instance)
                  for instance in ("TSPA", "TSPB")}
        for method in methods:
            label = f"**{method}{' (baseline)' if method == BASELINE else ''}**" if lab == 4 else f"{method} (lab {lab})"
            values = []
            for instance in ("TSPA", "TSPB"):
                row = data[(instance, method)]
                minimum = f"**{row['min']}**" if int(row["min"]) == minima[instance] else row["min"]
                values.append(f"{formatted(row['average'])} ({minimum} – {row['max']})")
            rows.append((lab, method, label, data, values))
    lines = ["### Objective function values", "", "| Method | TSPA | TSPB |", "|---|---:|---:|"]
    for _, _, label, _, values in rows:
        lines.append(f"| {label} | {values[0]} | {values[1]} |")
    lines.extend(["", "### Running times (ms)", "",
                  "Total times cover the complete run: creating the starting solution and performing local search. Candidate lists are built once per instance and method, outside the measured runs. Starting-solution times for lab 3 are copied from its current report. Empty cells mean that starting-solution time was not measured separately (lab 4) or that there is no separate starting-solution stage (labs 1-2).", "",
                  "Labs 1-3 retain their original measurements. Lab 4 was measured separately, so speedups are calculated against the baseline rerun in lab 4, using the same starts and environment as the candidate methods.", "",
                  "| Method | TSPA: total | TSPA: starting solution | TSPB: total | TSPB: starting solution |",
                  "|---|---:|---:|---:|---:|"])
    starting_times = lab3_starting_times()
    for lab, method, label, data, _ in rows:
        values = []
        for instance in ("TSPA", "TSPB"):
            row = data[(instance, method)]
            values.append(formatted(row["average_time_ms"], 6))
            if lab == 3:
                values.append(starting_times[(instance, method)])
            else:
                values.append("")
        lines.append(f"| {label} | {' | '.join(values)} |")
    return lines + [""]


def validate(groups, summaries):
    checked = 0
    for instance in sorted({key[0] for key in groups}):
        nodes = read_nodes(REPO / "common" / "data" / f"{instance}.csv")
        distances = [[math.floor(math.hypot(a[0] - b[0], a[1] - b[1]) + 0.5)
                      for b in nodes] for a in nodes]
        for (name, method), records in groups.items():
            if name != instance:
                continue
            assert len(records) == 200 and {int(row["run"]) for row in records} == set(range(200))
            for row in records:
                solution = row["solution"]
                assert len(solution) == (len(nodes) + 1) // 2
                assert len(set(solution)) == len(solution) and all(0 <= u < len(nodes) for u in solution)
                actual = sum(nodes[u][2] + distances[u][solution[(i + 1) % len(solution)]]
                             for i, u in enumerate(solution))
                assert actual == row["objective"]
                checked += 1
            summary = summaries[(instance, method)]
            values = [row["objective"] for row in records]
            assert min(values) == int(summary["min"]) and max(values) == int(summary["max"])
            assert abs(sum(values) / len(values) - float(summary["average"])) < 1e-6
    return checked


def main():
    groups = read_results(GENERATED / "results.csv")
    summaries = read_summary("lab4")
    previous = {lab: read_summary(f"lab{lab}") for lab in (1, 2, 3)}
    checked = validate(groups, summaries)
    lines = ["""# Lab 4: Candidate moves in local search

Authors: Piotr Foltyniewicz 160295, Jakub Adamski 160291

## Problem description

Each instance consists of 200 nodes. A row in the input file contains the node's planar coordinates and selection cost, in the form `x;y;cost`. Node indices are zero-based and correspond to row order. The task is to select exactly 100 distinct nodes (half of the available nodes), order them, and form a closed cycle that minimizes the sum of travel distances and selected-node costs.

Distances are Euclidean, rounded to the nearest integer and precomputed after reading the instance. All algorithms use this distance matrix. The evaluation sums all selected-node costs and all cycle edges, including last -> first. In the pseudocode, `m = 100`, `n = 200`, `c[v]` is node cost, and `d(a, b)` is the precomputed distance. A solution `S` is an ordered list of `m` distinct nodes; `U` denotes the set of nodes not in `S`.

The objective for an ordered selection `S` is:

```text
F(S) = sum(c[S[i]]) + sum(d(S[i], S[(i + 1) mod length(S)]))
```

## Pseudocode

All indices are zero-based. We use steepest search with inter-route replacement and 2-opt. The baseline checks all moves; candidate search checks only moves that add a candidate edge. Moves are evaluated through deltas without constructing neighboring solutions.

### Candidate edges

For each node `u`, choose `k` other nodes minimizing `d(u, v) + c[v]`, breaking ties by node ID. `A[u]` stores candidate neighbors: `v` belongs to it if `u` chose `v` or `v` chose `u`. These lists are built once and remain unchanged during the search. Adding reverse connections can make `A[u]` longer than `k`.

```text
BUILD_CANDIDATES(k):
    A = empty candidate lists
    for u in all nodes:
        C[u] = k smallest v != u by (d(u, v) + c[v], v)
        for v in C[u]:
            add v to A[u] and u to A[v], without duplicates
    return A
```

We use k = 10 and compare it with k = 5 and k = 20.

### Neighborhood and deltas

`S` is the ordered cycle and `A[node]` lists candidates for `node`. `pos[node]` is its position in `S`; `-1` means the node is outside `S`. Indices `i`, `j`, `p`, `q` are cycle positions, and `prev`/`next` refer to their cyclic neighbors.

- `INTER(p, v)`: replace `S[p]` with a node `v` from outside `S`.
- `TWO_OPT(i, j)`: order the cut positions so `i < j`, remove the edges starting there, reconnect the cycle, and reverse `S[i+1..j]`. The cut edges must not share a node.

If `candidate` is outside `S`, replacing either neighbor of `node` creates edge `{node, candidate}`. If both nodes are in `S`, consider the two 2-opt moves: cutting after both nodes or before both nodes. The condition `node < candidate` processes the pair only once, rather than again in the opposite order.

```text
CANDIDATE_MOVES(S, A):
    moves = []
    for node from 0 to n - 1:
        pos[node] = -1
    for i from 0 to m - 1:
        pos[S[i]] = i

    for i from 0 to m - 1:
        node = S[i]
        for candidate in A[node]:
            if pos[candidate] == -1:
                add INTER(prev(i), candidate) to moves
                add INTER(next(i), candidate) to moves
            else if node < candidate:
                j = pos[candidate]
                if edges (S[i], S[next(i)]) and (S[j], S[next(j)]) do not share a node:
                    add TWO_OPT(i, j) to moves

                p = prev(i); q = prev(j)
                if edges (S[p], S[next(p)]) and (S[q], S[next(q)]) do not share a node:
                    add TWO_OPT(p, q) to moves
    return moves

DELTA_INTER(S, p, v):
    out = S[p]; a = S[prev(p)]; b = S[next(p)]
    return d(a,v) + d(v,b) - d(a,out) - d(out,b) + c[v] - c[out]

DELTA_TWO_OPT(S, i, j):
    a = S[i]; b = S[next(i)]; e = S[j]; f = S[next(j)]
    return d(a,e) + d(b,f) - d(a,b) - d(e,f)
```

### Steepest local search

`DELTA` uses the formula for the move type. `APPLY` performs the replacement or reversal. Equal improving deltas prefer inter-route moves, then smaller position and node indices.

```text
CANDIDATE_STEEPEST(S, A):
    value = F(S)
    loop:
        best = NONE; bestDelta = 0
        for move in CANDIDATE_MOVES(S, A):
            delta = DELTA(S, move)
            if delta < bestDelta: best = move; bestDelta = delta
        if best == NONE: return S, value
        APPLY(S, best)
        value += bestDelta
```

### Starting solutions

Random starts contain the first 100 nodes of a shuffled permutation of all 200 nodes. Each method uses the same 200 starting cycles per instance, generated with seed 20261031. Reported times include creating the start and performing local search; candidate lists are built before the measured runs.

## Results

Each of the four methods was run 200 times on each instance. Results of labs 1-3 are copied from their current summaries and marked with the lab number; methods measured in lab 4 are in bold. The lab 4 baseline and the historical lab 3 result are shown separately because they use different samples of random starts.

Objective values use the format **average (minimum – maximum)**; running times are averages per run in milliseconds. Lower objective values are better. The lowest minimum within each lab and instance is in bold.
"""]
    lines.extend(results_tables(summaries, previous))
    conclusions = []
    tradeoffs = []
    for instance in sorted({key[0] for key in groups}):
        rows = [row for (name, _), row in summaries.items() if name == instance]
        baseline = summaries[(instance, BASELINE)]
        primary = summaries[(instance, "Candidate Edges k10 Random")]
        speedup = float(baseline["average_time_ms"]) / float(primary["average_time_ms"])
        change = (float(primary["average"]) / float(baseline["average"]) - 1) * 100
        conclusions.append(f"On {instance}, k = 10 reduces average total time from {float(baseline['average_time_ms']):.3f} to {float(primary['average_time_ms']):.3f} ms ({speedup:.2f}x speedup). The mean objective changes from {formatted(baseline['average'])} to {formatted(primary['average'])} ({change:+.3f}%).")
        candidates = [row for row in rows if row["method"] != BASELINE]
        fastest = min(candidates, key=lambda row: float(row["average_time_ms"]))
        best_mean = min(candidates, key=lambda row: float(row["average"]))
        tradeoffs.append(f"On {instance}, {fastest['method']} is the fastest tested candidate method; {best_mean['method']} gives the lowest candidate mean ({formatted(best_mean['average'])}, versus {formatted(baseline['average'])} for the full baseline).")
        earlier = [(lab, row) for lab, data in previous.items()
                   for (name, _), row in data.items() if name == instance]
        best_lab, best_earlier = min(earlier, key=lambda item: Decimal(item[1]["average"]))
        tradeoffs.append(f"The best candidate mean on {instance} is {formatted(best_mean['average'])}; the best mean from earlier labs is {formatted(best_earlier['average'])} ({best_earlier['method']}, lab {best_lab}).")
    lines.extend(["## Best solutions and visualizations", "",
                  "Node color represents selection cost; the compact horizontal scale below each plot uses the same cost range for all methods on an instance. Gray nodes are not selected, blue segments form the closed tour, and the red star marks the first node in the displayed sequence. Lists below show ten node indices per row; read left to right, then top to bottom to follow the tour. Only methods measured in lab 4 are visualized; historical results from labs 1-3 appear only in the Results tables.", ""])
    best_records = []
    current_instance = None
    for instance, method in summaries:
        records = groups[(instance, method)]
        if instance != current_instance:
            lines.extend([f"### {instance}", ""])
            current_instance = instance
        best = min(records, key=lambda row: (row["objective"], int(row["run"])))
        image = f"{instance}_{method}.png"
        plot_solution(read_nodes(REPO / "common" / "data" / f"{instance}.csv"), best,
                      GENERATED / image, f"{instance}: {method}")
        solution = best["solution"]
        tour = "\n".join(" ".join(f"{u:3d}" for u in solution[i:i+10]) for i in range(0, len(solution), 10))
        lines.extend([f"#### {method}", "",
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
                  f"All {checked} exported solutions were independently checked in Python: exactly 100 distinct node indices in 0-199, and recomputed rounded-distance objectives equal the incremental C++ objectives. All CSV minima, maxima, and means were recomputed. All eight plotted best solutions match the summary minima.", "",
                  "## Source code", "",
                  "Repository: [PiotrFoltyniewicz/Evolutionary-Computation](https://github.com/PiotrFoltyniewicz/Evolutionary-Computation). The implementation and exported evidence are included in this project:", "",
                  "- [Candidate lists, move generation, deltas, and steepest search](../src/candidate_search.cpp)",
                  "- [Experiment runner](../src/lab4_experiment.cpp)",
                  "- [Unchanged full-neighborhood baseline](../../lab3/src/local_search_methods.cpp)",
                  "- [Validation and report generator](../src/create_report.py)",
                  "- [All runs](generated/results.csv)",
                  "- [Summary](generated/summary.csv)",
                  "- [Best solutions](generated/best_solutions.csv)", "",
                  "- [Lab 3 report](../../lab3/out/report.md)",
                  "- [Lab 3 summary](../../lab3/out/generated/summary.csv)",
                  "- [Lab 2 summary](../../lab2/out/generated/summary.csv)",
                  "- [Lab 1 summary](../../lab1/out/generated/summary.csv)", "",
                  "## Conclusions", "", *[paragraph + "\n" for paragraph in conclusions],
                  *[paragraph + "\n" for paragraph in tradeoffs],
                  "Increasing k raises the number of candidate moves and does not guarantee a better local optimum in every run, because the steepest move can lead to a different search trajectory. These observations describe this sample of starts, not a guarantee that restricted search dominates full search.", "",
                  "The required k = 10 setting gives a substantial speedup with a small change in mean quality. Restricting the moves changes the stopping condition: a candidate-local optimum may still admit an improving non-candidate move. The results support candidate lists as an effective time-quality tradeoff for these instances.", ""])
    report = "\n".join(lines)
    (OUT / "report.md").write_text(report, encoding="utf-8")
    (GENERATED / "final_results.txt").write_text(report, encoding="utf-8")
    print(f"Validated {checked} solutions; wrote eight plots and {OUT / 'report.md'}")


if __name__ == "__main__":
    main()
