"""Validate all lab7 experiments and generate reports, tables and best-cycle plots.

Run from the repository root after make run-lab7:
    python lab7/src/create_report.py
A methodology draft can be generated before experiments:
    python lab7/src/create_report.py --draft
Dependencies: matplotlib and reportlab.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import re
import sys
import tempfile
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import quote, unquote
from xml.sax.saxutils import escape

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "ec-matplotlib"))
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "common" / "src"))
from visualize_experiments import plot_solution, read_nodes, read_results

OUT = REPO / "lab7" / "out"
GENERATED = OUT / "generated"
INSTANCES = ("TSPA", "TSPB")
OPERATORS = ("Random Nodes", "Single Subpath", "Multiple Subpaths")
METHODS = tuple(f"LNS {operator}{suffix}" for operator in OPERATORS for suffix in ("", " + LS"))
RUNS = 20
SEED = 20261117


def require(condition, message):
    if not condition:
        raise ValueError(message)


def formatted(value, places=2):
    return format(Decimal(str(value)).quantize(
        Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP), f".{places}f")


def read_summary(lab):
    path = REPO / lab / "out" / "generated" / "summary.csv"
    with path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    summaries = {(row["instance"], row["method"]): row for row in rows}
    require(len(rows) == len(summaries), f"Duplicate summary groups in {path}")
    return summaries


def historical_comparisons():
    """Keep both per-instance mean winners and the exact steepest LS kernel."""
    path = REPO / "lab6/out/generated/comparison_summary.csv"
    with path.open(newline="", encoding="utf-8-sig") as stream:
        previous = list(csv.DictReader(stream))
    selected = {(5, "Move List Edges Random")}
    for instance in INSTANCES:
        for labs in ((1, 2), (3, 4, 5)):
            choices = [row for row in previous if row["instance"] == instance and int(row["lab"]) in labs]
            winner = min(choices, key=lambda row: (float(row["average"]), int(row["min"]), row["method"]))
            selected.add((int(winner["lab"]), winner["method"]))
    comparisons = {}
    for lab, method in sorted(selected):
        comparisons[f"{method} (lab {lab})"] = {
            instance: next(row for row in previous if int(row["lab"]) == lab and
                           row["instance"] == instance and row["method"] == method)
            for instance in INSTANCES}
    lab6 = read_summary("lab6")
    for method in ("MSLS", "ILS"):
        comparisons[f"{method} (lab 6)"] = {
            instance: dict(lab6[(instance, method)], lab="6") for instance in INSTANCES}
    return comparisons, lab6


def has_improving_move(solution, nodes, distances):
    """Independently check the complete replacement and 2-opt neighborhood."""
    outside = set(range(200)) - set(solution)
    for i, node in enumerate(solution):
        left, right = solution[i - 1], solution[(i + 1) % 100]
        removed = distances[left][node] + distances[node][right] + nodes[node][2]
        if any(distances[left][new] + distances[new][right] + nodes[new][2] < removed
               for new in outside):
            return True
    for i in range(100):
        a, b = solution[i], solution[(i + 1) % 100]
        for j in range(i + 2, 100):
            if i == 0 and j == 99:
                continue
            c, d = solution[j], solution[(j + 1) % 100]
            if distances[a][c] + distances[b][d] < distances[a][b] + distances[c][d]:
                return True
    return False


def validate(groups, summaries, lab6):
    expected = {(instance, method) for instance in INSTANCES for method in METHODS}
    require(set(groups) == expected and set(summaries) == expected,
            "Expected all six LNS variants on TSPA and TSPB")
    previous = read_results(REPO / "lab6/out/generated/results.csv")
    checked = 0
    for instance_index, instance in enumerate(INSTANCES):
        nodes = read_nodes(REPO / "common/data" / f"{instance}.csv")
        require(len(nodes) == 200, f"{instance}: expected 200 nodes")
        distances = [[math.floor(math.hypot(a[0] - b[0], a[1] - b[1]) + 0.5)
                      for b in nodes] for a in nodes]
        msls = previous[(instance, "MSLS")]
        require(len(msls) == RUNS and {int(row["run"]) for row in msls} == set(range(RUNS)),
                f"{instance}: expected 20 historical MSLS records")
        budget = sum(float(row["time_ms"]) for row in msls) / RUNS
        require(math.isfinite(budget) and budget > 0 and
                abs(budget - float(lab6[(instance, "MSLS")]["average_time_ms"])) < 1e-6,
                f"{instance}: lab6 MSLS timing summary is inconsistent")
        initial_values = {}
        for method in METHODS:
            records = groups[(instance, method)]
            label = f"{instance}/{method}"
            require(len(records) == RUNS and {int(row["run"]) for row in records} == set(range(RUNS)),
                    f"{label}: expected runs 0 through 19 exactly once")
            for row in records:
                run = int(row["run"])
                solution = row["solution"]
                require(len(solution) == 100 and len(set(solution)) == 100 and
                        all(0 <= node < 200 for node in solution), f"{label}/{run}: invalid cycle")
                actual = sum(nodes[node][2] + distances[node][solution[(i + 1) % 100]]
                             for i, node in enumerate(solution))
                require(actual == row["objective"], f"{label}/{run}: objective mismatch")
                iterations, calls, accepted, initial = (int(row[key]) for key in
                    ("iterations", "ls_runs", "accepted_improvements", "initial_objective"))
                require(iterations >= 0 and 0 <= accepted <= iterations and actual <= initial and
                        (accepted > 0) == (actual < initial), f"{label}/{run}: inconsistent counters")
                expected_calls = iterations + 1 if method.endswith(" + LS") else 1
                require(calls == expected_calls, f"{label}/{run}: LS count mismatch")
                require(int(row["seed"]) == SEED + 1000 * instance_index + run and
                        int(row["start"]) == -1, f"{label}/{run}: seed/start mismatch")
                duration = float(row["time_ms"])
                require(math.isfinite(duration) and duration >= budget and
                        abs(float(row["time_budget_ms"]) - budget) < 1e-6,
                        f"{label}/{run}: MSLS-derived budget mismatch")
                initial_values.setdefault(run, initial)
                require(initial == initial_values[run], f"{label}/{run}: initial local optima differ")
                if method.endswith(" + LS"):
                    require(not has_improving_move(solution, nodes, distances),
                            f"{label}/{run}: final solution has an improving LS move")
                checked += 1
            summary = summaries[(instance, method)]
            values = [row["objective"] for row in records]
            counts = [int(row["iterations"]) for row in records]
            times = [float(row["time_ms"]) for row in records]
            require(int(summary["min"]) == min(values) and int(summary["max"]) == max(values) and
                    abs(float(summary["average"]) - sum(values) / RUNS) < 1e-6 and
                    abs(float(summary["average_time_ms"]) - sum(times) / RUNS) < 1e-6 and
                    int(summary["min_iterations"]) == min(counts) and
                    int(summary["max_iterations"]) == max(counts) and
                    abs(float(summary["average_iterations"]) - sum(counts) / RUNS) < 1e-6,
                    f"{label}: summary does not match individual runs")
    return checked


DESCRIPTION = """# Lab 7 - Large neighborhood search

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
"""


def table(header, rows):
    return ["| " + " | ".join(header) + " |", "|---|---:|---:|",
            *("| " + " | ".join(row) + " |" for row in rows), ""]


def result_tables(summaries, historical):
    lines = ["## Results", "", "### Objective function values", "",
             "Entries show mean (minimum - maximum). Lower values are better.", ""]
    objective_rows, time_rows = [], []
    for method in METHODS:
        values, times = [], []
        for instance in INSTANCES:
            row = summaries.get((instance, method))
            values.append(f"{formatted(row['average'])} ({row['min']} - {row['max']})" if row else "Pending")
            times.append(formatted(row["average_time_ms"], 6) if row else "Pending")
        objective_rows.append([method, *values])
        time_rows.append([method, *times])
    for method, data in historical.items():
        objective_rows.append([method, *(f"{formatted(data[i]['average'])} ({data[i]['min']} - {data[i]['max']})"
                                       for i in INSTANCES)])
        time_rows.append([method, *(formatted(data[i]["average_time_ms"], 6) for i in INSTANCES)])
    lines += table(["Method", *INSTANCES], objective_rows)
    lines += ["### Running times", "", "Mean milliseconds per complete run.", ""]
    lines += table(["Method", *INSTANCES], time_rows)
    lines += ["### Number of main-loop iterations", "",
              "Entries show mean (minimum - maximum) across 20 runs. Initial local search is excluded.", ""]
    rows = []
    for method in METHODS:
        values = []
        for instance in INSTANCES:
            row = summaries.get((instance, method))
            values.append(f"{formatted(row['average_iterations'])} ({row['min_iterations']} - {row['max_iterations']})"
                          if row else "Pending")
        rows.append([method, *values])
    lines += table(["Method", *INSTANCES], rows)
    return lines


def save_best_and_plots(groups):
    lines = ["## Best solutions and visualizations", ""]
    with (GENERATED / "best_solutions.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["instance", "method", "run", "objective", "solution"])
        for instance in INSTANCES:
            lines += [f"### {instance}", ""]
            nodes = read_nodes(REPO / "common/data" / f"{instance}.csv")
            for method in METHODS:
                best = min(groups[(instance, method)], key=lambda row: (row["objective"], int(row["run"])))
                image_name = f"{instance}_{method}.png"
                plot_solution(nodes, best, GENERATED / image_name, f"{instance} - {method}")
                writer.writerow([instance, method, best["run"], best["objective"],
                                 " ".join(map(str, best["solution"]))])
                lines += [f"#### {method}", "",
                          f"Objective **{best['objective']}**, run **{best['run']}** (zero-based).", "",
                          f"![{instance} - {method}](generated/{quote(image_name)})", "",
                          "**Solution node order**", "", "```text"]
                lines += [" ".join(f"{node:3d}" for node in best["solution"][start:start + 10])
                          for start in range(0, 100, 10)]
                lines += ["```", ""]
    return lines


def conclusions(groups, summaries, lab6):
    lines = ["## Conclusions", ""]
    for instance in INSTANCES:
        winner = min(METHODS, key=lambda method: (float(summaries[(instance, method)]["average"]), method))
        best = summaries[(instance, winner)]
        lines += [f"On {instance}, {winner} has the lowest LNS mean objective of {formatted(best['average'])}, "
                  f"with a best value of {best['min']}. Its mean run completes "
                  f"{formatted(best['average_iterations'])} main-loop iterations.", ""]
        for previous in ("MSLS", "ILS"):
            baseline = lab6[(instance, previous)]
            change = (float(best["average"]) / float(baseline["average"]) - 1) * 100
            direction = "higher" if change > 0 else "lower"
            lines += [f"Its mean is {abs(change):.3f}% {direction} than {previous}'s "
                      f"{formatted(baseline['average'])}. The best {previous} value is {baseline['min']}.", ""]
        for operator in OPERATORS:
            plain, improved = f"LNS {operator}", f"LNS {operator} + LS"
            before, after = (summaries[(instance, method)] for method in (plain, improved))
            paired_plain = sorted(groups[(instance, plain)], key=lambda row: int(row["run"]))
            paired_ls = sorted(groups[(instance, improved)], key=lambda row: int(row["run"]))
            wins = sum(a["objective"] < b["objective"] for a, b in zip(paired_ls, paired_plain))
            ties = sum(a["objective"] == b["objective"] for a, b in zip(paired_ls, paired_plain))
            lines += [f"For {operator} on {instance}, post-repair LS changes the mean from "
                      f"{formatted(before['average'])} to {formatted(after['average'])}. "
                      f"Mean iterations change from {formatted(before['average_iterations'])} to "
                      f"{formatted(after['average_iterations'])}. In 20 comparisons with the same "
                      f"initial local optimum, the + LS variant wins {wins}, ties {ties}, "
                      f"and loses {RUNS - wins - ties}.", ""]
    lines += ["Each LNS variant runs under the same per-instance historical MSLS budget. "
              "Iteration counts measure the search performed within that budget. The two instances "
              "use different repair variants, so comparisons between destroy operators are made within "
              "each instance. These are descriptive results over the measured runs.", ""]
    return lines


def save_tables(summaries, historical):
    with (GENERATED / "iterations.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["instance", "method", "min_iterations", "max_iterations", "average_iterations"])
        for instance in INSTANCES:
            for method in METHODS:
                row = summaries[(instance, method)]
                writer.writerow([instance, method, row["min_iterations"], row["max_iterations"], row["average_iterations"]])
    with (GENERATED / "comparison_summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["lab", "instance", "method", "min", "max", "average", "average_time_ms"])
        for data in historical.values():
            for instance in INSTANCES:
                row = data[instance]
                writer.writerow([row["lab"], instance, row["method"], row["min"], row["max"],
                                 row["average"], row["average_time_ms"]])


def source_links():
    return ["## Source code", "",
            "- [LNS and destroy operators](../src/lns.cpp)",
            "- [Experiment runner](../src/lab7_experiment.cpp)",
            "- [Weighted-regret repair](../../lab2/src/lab2_methods.cpp)",
            "- [Move-list steepest local search](../../lab5/src/move_list_search.cpp)",
            "- [Validation and report generator](../src/create_report.py)",
            "- [Lab6 report and full LS pseudocode](../../lab6/out/report.md)",
            "- [Historical MSLS/ILS results and budgets](../../lab6/out/generated/summary.csv)",
            "- [Historical construction and LS comparisons](../../lab6/out/generated/comparison_summary.csv)", ""]


def render_pdf(markdown, output):
    """Render the report with compact tables and one page per plotted best solution."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import (CondPageBreak, Image, KeepTogether, PageBreak, Paragraph,
                                   Preformatted, SimpleDocTemplate, Table, TableStyle)

    width = 511
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("ReportTitle", parent=styles["Title"], fontSize=22, leading=26, spaceAfter=15))
    styles.add(ParagraphStyle("ReportBody", parent=styles["BodyText"], fontSize=9, leading=12.5, spaceAfter=7))
    styles.add(ParagraphStyle("ReportList", parent=styles["BodyText"], fontSize=8, leading=9.5, spaceAfter=2))
    styles.add(ParagraphStyle("ReportCode", fontName="Courier", fontSize=7.4, leading=9.6,
                              leftIndent=9, borderPadding=8, backColor=colors.HexColor("#f2f5f7"), spaceAfter=10))
    styles.add(ParagraphStyle("ReportCell", fontName="Helvetica", fontSize=7.5, leading=10))
    styles.add(ParagraphStyle("ReportHeadCell", parent=styles["ReportCell"], textColor=colors.white))
    styles.add(ParagraphStyle("ReportCaption", parent=styles["ReportBody"], alignment=TA_CENTER, fontSize=8))
    for name, size in (("Heading1", 15), ("Heading2", 12), ("Heading3", 11)):
        styles[name].fontSize = size
        styles[name].leading = size + 3
        styles[name].spaceBefore = 11
        styles[name].spaceAfter = 7

    def inline(text):
        text = escape(text)
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m:
                      f'<link href="{m.group(2)}" color="#145e96">{m.group(1)}</link>'
                      if m.group(2).startswith("https://") else m.group(1), text)
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        return re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', text)

    story = []
    lines = markdown.splitlines()
    i = 0
    current_instance = ""
    best_section = False
    best_count = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("```"):
            code = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            require(all(len(row) <= 92 for row in code), "PDF code line too long")
            # Keep each algorithm/solution block intact.
            story.append(KeepTogether([Preformatted("\n".join(code), styles["ReportCode"])]))
            i += 1
            continue
        if line.startswith("|"):
            table_rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row = [cell.strip() for cell in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", cell) for cell in row):
                    table_rows.append(row)
                i += 1
            columns = len(table_rows[0])
            col_widths = [235, 138, 138] if columns == 3 else [76, 145, 145, 145]
            cells = [[Paragraph(inline(cell), styles["ReportHeadCell" if r == 0 else "ReportCell"])
                      for cell in row] for r, row in enumerate(table_rows)]
            table = Table(cells, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#173e59")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f7")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#173e59")),
            ]))
            story.append(table)
            continue
        if line.startswith("!["):
            match = re.fullmatch(r"!\[(.*?)\]\((.*?)\)", line)
            path = OUT / unquote(match[2])
            image_width, image_height = ImageReader(str(path)).getSize()
            display_width = min(width, 470)
            story.append(Image(str(path), width=display_width,
                               height=display_width * image_height / image_width))
            i += 1
            continue
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            heading = line[level:].strip()
            section_space = {"Check and select saved moves": 420,
                             "Multiple start local search (MSLS)": 250,
                             "Iterated local search (ILS)": 280}
            if level == 3 and heading in section_space:
                story.append(CondPageBreak(section_space[heading]))
            if level == 2:
                best_section = heading == "Best solutions and visualizations"
                current_instance = ""
                if heading in ("Results", "Best solutions and visualizations", "Solution checking"):
                    # Avoid a blank page if the previous flowable just filled one.
                    story.append(CondPageBreak(700))
            if best_section and level == 3:
                current_instance = heading
                i += 1
                continue
            if best_section and level == 4:
                if best_count:
                    story.append(PageBreak())
                best_count += 1
                heading = f"{current_instance}: {heading}"
                level = 3
            style = "ReportTitle" if level == 1 else f"Heading{min(level - 1, 3)}"
            story.append(Paragraph(inline(heading), styles[style]))
            i += 1
            continue
        paragraph = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "|", "```", "![", "- ")):
            paragraph.append(lines[i].strip())
            i += 1
        text = " ".join(paragraph)
        is_list = text.startswith("- ")
        if is_list:
            text = "&#8226; " + inline(text[2:])
        else:
            text = inline(text)
        story.append(Paragraph(text, styles["ReportList" if is_list else "ReportBody"]))

    def footer(canvas, doc):
        canvas.setStrokeColor(colors.HexColor("#cbd5dc"))
        canvas.line(42, 34, 553, 34)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#526675"))
        canvas.drawString(42, 22, "Evolutionary Computation | Lab 7 | Large neighborhood search")
        canvas.drawRightString(553, 22, str(doc.page))

    document = SimpleDocTemplate(str(output), pagesize=(595, 842), rightMargin=42, leftMargin=42,
                                 topMargin=38, bottomMargin=46,
                                 title="Lab 7: Large neighborhood search",
                                 author="Piotr Foltyniewicz, Jakub Adamski")
    document.build(story, onFirstPage=footer, onLaterPages=footer)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", action="store_true", help="write report_draft.md/pdf with pending results")
    args = parser.parse_args()
    historical, lab6 = historical_comparisons()
    OUT.mkdir(parents=True, exist_ok=True)
    GENERATED.mkdir(parents=True, exist_ok=True)
    if args.draft:
        lines = [DESCRIPTION.split("\n", 1)[0], "",
                 "**DRAFT - Awaiting the 240 LNS experiment records. Numerical LNS results, "
                 "best cycles, validation results and conclusions will be generated after the experiment.**", "",
                 DESCRIPTION.split("\n", 1)[1], *result_tables({}, historical),
                 "## Best solutions and visualizations", "",
                 "Pending experiment results. The final report will include the best cycle for each of the 12 instance/method groups.", "",
                 "## Solution checking", "", "Pending experiment results.", "",
                 *source_links(), "## Conclusions", "", "Pending experiment results.", ""]
        report = "\n".join(lines)
        (OUT / "report_draft.md").write_text(report, encoding="utf-8")
        render_pdf(report, OUT / "report_draft.pdf")
        print("Wrote methodology draft report_draft.md and report_draft.pdf")
        return
    paths = [GENERATED / filename for filename in ("results.csv", "summary.csv")]
    require(all(path.is_file() for path in paths),
            "Lab7 results.csv and summary.csv are required. Run make run-lab7 first, then rerun this command.")
    groups = read_results(paths[0])
    summaries = read_summary("lab7")
    checked = validate(groups, summaries, lab6)
    save_tables(summaries, historical)
    lines = [DESCRIPTION, *result_tables(summaries, historical), *save_best_and_plots(groups),
             "## Solution checking", "",
             f"All {checked} exported cycles contain 100 distinct valid node IDs. Independently recomputed "
             "objectives and summary statistics match the CSV records. Each group contains exactly 20 runs. "
             "Recorded seeds, shared initial local optima, time budgets, elapsed times, accepted improvements "
             "and LS counts are consistent. All 120 final cycles from + LS runs have no improving node "
             "replacement or 2-opt move in the full neighborhood. All 12 plotted cycles attain their group minima.", "",
             *source_links(), "- [All 240 raw results](generated/results.csv)",
             "- [Summary](generated/summary.csv)", "- [Main-loop iterations](generated/iterations.csv)",
             "- [Comparison summaries](generated/comparison_summary.csv)",
             "- [Best solutions](generated/best_solutions.csv)", "",
             *conclusions(groups, summaries, lab6)]
    report = "\n".join(lines)
    (OUT / "report.md").write_text(report, encoding="utf-8")
    (GENERATED / "final_results.txt").write_text(report, encoding="utf-8")
    render_pdf(report, OUT / "report.pdf")
    print(f"Validated {checked} runs. Wrote report.md, report.pdf, 12 plots and supporting tables.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError) as error:
        raise SystemExit(f"lab7 report: {error}") from error
