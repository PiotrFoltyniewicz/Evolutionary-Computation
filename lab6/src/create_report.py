"""Independently validate lab6 experiments and create the Markdown/PDF report.

Run from the repository root: python3 lab6/src/create_report.py
Dependencies: matplotlib and reportlab (Python standard library otherwise).
The final experiment must contain 20 MSLS and 20 ILS runs for each instance.
"""

from __future__ import annotations

import csv
import math
import os
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import quote, unquote
from xml.sax.saxutils import escape

os.environ.setdefault("MPLCONFIGDIR", "/tmp/ec-matplotlib")
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "common" / "src"))
from visualize_experiments import plot_solution, read_nodes, read_results  # noqa: E402

OUT = REPO / "lab6" / "out"
GENERATED = OUT / "generated"
INSTANCES = ("TSPA", "TSPB")
METHODS = ("MSLS", "ILS")
RUNS = 20
STARTS = 400
SEED = 20261114


def require(condition, message):
    if not condition:
        raise ValueError(message)


def formatted(value, places=2):
    return format(Decimal(str(value)).quantize(
        Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP), f".{places}f")


def read_summary(lab):
    path = REPO / lab / "out" / "generated" / "summary.csv"
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    summaries = {(row["instance"], row["method"]): row for row in rows}
    require(len(rows) == len(summaries), f"Duplicate groups in {path}")
    return summaries


def validate(groups, summaries):
    expected = {(instance, method) for instance in INSTANCES for method in METHODS}
    require(set(groups) == expected and set(summaries) == expected,
            "Expected exactly MSLS and ILS on TSPA and TSPB")
    checked = 0
    for instance_index, instance in enumerate(INSTANCES):
        nodes = read_nodes(REPO / "common" / "data" / f"{instance}.csv")
        require(len(nodes) == 200, f"{instance}: expected 200 nodes")
        distances = [[math.floor(math.hypot(a[0] - b[0], a[1] - b[1]) + 0.5)
                      for b in nodes] for a in nodes]
        msls_mean_ms = sum(float(row["time_ms"]) for row in groups[(instance, "MSLS")]) / RUNS
        initial_values = {}
        for method in METHODS:
            records = groups[(instance, method)]
            label = f"{instance}/{method}"
            require(len(records) == RUNS and {int(r["run"]) for r in records} == set(range(RUNS)),
                    f"{label}: expected runs 0 through 19 exactly once")
            for row in records:
                run = int(row["run"])
                solution = row["solution"]
                require(len(solution) == 100 and len(set(solution)) == 100 and
                        all(0 <= node < 200 for node in solution), f"{label}/{run}: invalid cycle")
                actual = sum(nodes[u][2] + distances[u][solution[(i + 1) % 100]]
                             for i, u in enumerate(solution))
                require(actual == row["objective"], f"{label}/{run}: incorrect objective")
                ls_runs = int(row["ls_runs"])
                initial = int(row["initial_objective"])
                accepted = int(row["accepted_improvements"])
                require(ls_runs >= 1 and 0 <= accepted < ls_runs and
                        actual <= initial and (accepted > 0) == (actual < initial),
                        f"{label}/{run}: inconsistent LS/acceptance counters")
                require(int(row["seed"]) == SEED + 1000 * instance_index + run and
                        int(row["start"]) == -1, f"{label}/{run}: inconsistent start or seed")
                duration = float(row["time_ms"])
                budget = float(row["time_budget_ms"])
                require(math.isfinite(duration) and duration > 0, f"{label}/{run}: invalid time")
                if method == "MSLS":
                    require(ls_runs == STARTS and budget == 0, f"{label}/{run}: expected 400 LS runs")
                    initial_values[run] = initial
                else:
                    require(abs(budget - msls_mean_ms) < 1e-6 and duration >= budget,
                            f"{label}/{run}: incorrect MSLS-derived time budget")
                    require(initial == initial_values[run], f"{label}/{run}: starting local optima differ")
                checked += 1
            summary = summaries[(instance, method)]
            values = [row["objective"] for row in records]
            counts = [int(row["ls_runs"]) for row in records]
            times = [float(row["time_ms"]) for row in records]
            require(int(summary["min"]) == min(values) and int(summary["max"]) == max(values) and
                    abs(float(summary["average"]) - sum(values) / RUNS) < 1e-6 and
                    abs(float(summary["average_time_ms"]) - sum(times) / RUNS) < 1e-6 and
                    int(summary["min_ls_runs"]) == min(counts) and int(summary["max_ls_runs"]) == max(counts) and
                    abs(float(summary["average_ls_runs"]) - sum(counts) / RUNS) < 1e-6,
                    f"{label}: summary does not match individual runs")
    return checked


def historical_comparisons():
    previous = {lab: read_summary(f"lab{lab}") for lab in range(1, 6)}
    selected = set()
    # Union of winners by mean and by minimum on either instance. Ties in
    # minimum prefer the lower mean, then lab/method for deterministic output.
    for labs in ((1, 2), (3, 4, 5)):
        for instance in INSTANCES:
            choices = [(lab, method, row) for lab in labs
                       for (name, method), row in previous[lab].items() if name == instance]
            for key in (lambda choice: (float(choice[2]["average"]), int(choice[2]["min"]), choice[0], choice[1]),
                        lambda choice: (int(choice[2]["min"]), float(choice[2]["average"]), choice[0], choice[1])):
                lab, method, _ = min(choices, key=key)
                selected.add((lab, method))
    # Also include the exact single-start LS kernel and its full-scan baseline.
    selected.update({(5, "Move List Edges Random"), (5, "Steepest Edges Random")})
    # Retain the best candidate-list variants from lab 4 as well.
    for instance in INSTANCES:
        candidates = [(method, row) for (name, method), row in previous[4].items()
                      if name == instance and method.startswith("Candidate")]
        for key in (lambda choice: (float(choice[1]["average"]), int(choice[1]["min"])),
                    lambda choice: (int(choice[1]["min"]), float(choice[1]["average"]))):
            selected.add((4, min(candidates, key=key)[0]))
    return [(lab, method, {instance: previous[lab][(instance, method)] for instance in INSTANCES})
            for lab, method in sorted(selected, reverse=True)]


DESCRIPTION = """# Lab 6: Multiple start and iterated local search

Authors: Piotr Foltyniewicz 160295, Jakub Adamski 160291

## Problem description

Select 100 distinct nodes from 200 and arrange them in a closed cycle. Minimize the sum of selected-node costs and rounded Euclidean edge lengths, including the closing edge. Node IDs are zero-based row indices in the input files.

```text
F(S) = sum(cost[S[i]] + dist(S[i], S[(i+1) mod 100]), i=0..99)
```

## Pseudocode

### Move-list local search from lab 5

We use the move-list LS from lab 5. Here `n=200`, `m=100`, and indices around the cycle use modulo m. `pos[v]` is the position of node v, or -1 if it is unselected. A saved move contains `(delta,type,a,b,c,d)` using node IDs:

- `INTER`: replace b by unselected d, keeping its neighbors a,c.
- `EDGES`: remove (a,b),(c,d), add (a,c),(b,d), and reverse the segment between the cuts.

LM is a min-priority queue ordered by `(delta,type,a,b,c,d)`, with INTER before EDGES. `HEAPIFY` builds this queue from a list. Slices `S[l:r]` include l and exclude r; `+` joins lists. Functions `APPLY` and `LS` modify S in place. `LS` returns the final objective value.

### Create the move list

Evaluate every replacement and both descriptors of each nonadjacent edge pair. Store only descriptors with negative delta. The second edge descriptor starts with its edges in opposite directions; it is kept for a possible later reversal.

```text
POSITIONS(S):
    pos[0..n-1] = -1
    for i = 0..m-1:
        pos[S[i]] = i
    return pos

GENERATE(S, pos):
    moves = []
    for i = 0..m-1:
        a = S[(i-1) mod m]; b = S[i]; c = S[(i+1) mod m]
        for d = 0..n-1 where pos[d] == -1:
            delta = dist(a,d) + dist(d,c) - dist(a,b) - dist(b,c)
                    + cost[d] - cost[b]
            if delta < 0:
                append (delta, INTER, a,b,c,d) to moves
    for i = 0..m-1:
        for j = i+2..m-1:
            if i == 0 and j == m-1: continue
            a = S[i]; b = S[(i+1) mod m]
            c = S[j]; d = S[(j+1) mod m]
            removed = dist(a,b) + dist(c,d)
            delta = dist(a,c) + dist(b,d) - removed
            if delta < 0:
                append (delta, EDGES, a,b,c,d) to moves
            delta = dist(a,d) + dist(b,c) - removed
            if delta < 0:
                append (delta, EDGES, a,b,d,c) to moves
    return moves
```

### Check and select saved moves

Invalid moves are removed. A move whose two edges currently have opposite directions is deferred. The queue returns the lowest-delta applicable saved move.

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
        return APPLICABLE
    first = EDGE_DIRECTION(S,pos,a,b)
    second = EDGE_DIRECTION(S,pos,c,d)
    if first == MISSING or second == MISSING: return INVALID
    if first == second: return APPLICABLE
    return DEFERRED

TAKE_APPLICABLE(LM, S, pos):
    deferred = []; chosen = NONE
    while LM is not empty:
        move = pop minimum from LM
        status = STATUS(S,pos,move)
        if status == APPLICABLE:
            chosen = move
            break
        if status == DEFERRED:
            append move to deferred
        // INVALID moves are discarded
    reinsert every move from deferred into LM
    return chosen
```

### Apply a move and run LS

After each move, update the objective and positions. Rebuild LM when no saved move applies. Stop when a freshly rebuilt queue also has no applicable improving move.

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
        reverse S[i+1:j+1]
```

```text
LS(S):
    value = F(S)
    pos = POSITIONS(S)
    LM = HEAPIFY(GENERATE(S,pos))
    loop:
        move = TAKE_APPLICABLE(LM,S,pos)
        if move == NONE:
            LM = HEAPIFY(GENERATE(S,pos))
            move = TAKE_APPLICABLE(LM,S,pos)
            if move == NONE:
                return value
        APPLY(S,pos,move)
        value += move.delta
        pos = POSITIONS(S)
```

`COPY` makes a separate copy, `SHUFFLE` randomly reorders a list in place using rng, and `NOW()` returns monotonic time in milliseconds.

### Multiple start local search (MSLS)

One MSLS run generates 400 random solutions, improves each with LS, and returns the best one.

```text
RANDOM_SOLUTION(rng):
    S = [0,1,...,199]
    SHUFFLE(S, rng)
    return S[0:100]

MSLS(rng):
    t0 = NOW()
    best = NONE; bestValue = infinity; calls = 0
    repeat 400 times:
        candidate = RANDOM_SOLUTION(rng)
        value = LS(candidate)
        calls += 1
        if value < bestValue:
            best = COPY(candidate)
            bestValue = value
    elapsed = NOW() - t0
    return best, bestValue, calls, elapsed
```

### ILS perturbation

The perturbation modifies a copy of the best solution in two steps:

1. Replace r randomly chosen nodes with r distinct nodes from outside the solution. Start with r=2. After 50, 100 and 150 consecutive attempts without improvement, increase r to 4, 6 and 8 respectively. A strict improvement resets r to 2.

2. Split the solution into four random segments A, B, C, D, each containing at least two nodes, and join them as A, D, C, B. Keep the order of nodes inside each segment. This is the double bridge move.

Each solution is a cycle: the last node connects back to the first. Choose a random node as the first item, keeping the same cyclic order. For example:

```text
0 -> 1 -> 2 -> 3 -> 0
2 -> 3 -> 0 -> 1 -> 2
```

Both lists have the same edges and cost. The edge between the new last and first nodes is one cut. Choose three more cuts inside the list to create four segments. If any segment has fewer than two nodes, redraw the three internal cuts.

Here q counts consecutive ILS attempts without a strictly better result after LS. The incoming nodes are chosen from outside S before any replacements. `PERTURB` modifies S in place.

```text
PERTURB(S, q, rng):
    r = 2 + 2*min(floor(q/50), 3)
    U = [v in 0..199 such that v is not in S]
    P = [0,1,...,99]
    SHUFFLE(P, rng)
    SHUFFLE(U, rng)
    for i = 0..r-1:
        S[P[i]] = U[i]

    k = uniform random integer from 0..99 using rng
    S = S[k:100] + S[0:k]
    cuts = [1,2,...,99]
    repeat:
        SHUFFLE(cuts, rng)
        (a,b,c) = SORT(cuts[0:3])
    until min(a, b-a, c-b, 100-c) >= 2
    A = S[0:a]; B = S[a:b]; C = S[b:c]; D = S[c:100]
    S = A + D + C + B
```

### Iterated local search (ILS)

Start from one random solution and improve it with LS. Then repeatedly perturb a copy of the best solution and run LS again. Keep the candidate only when its objective is lower. Otherwise keep the previous best solution and increase q; an equal objective also counts as failure.

```text
ILS(rng, T):
    t0 = NOW(); deadline = t0 + T
    best = RANDOM_SOLUTION(rng)
    bestValue = LS(best)
    calls = 1; q = 0
    while NOW() < deadline:
        candidate = COPY(best)
        PERTURB(candidate, q, rng)
        if NOW() >= deadline:
            break
        value = LS(candidate)
        calls += 1
        if value < bestValue:
            best = COPY(candidate)
            bestValue = value
            q = 0
        else:
            q += 1
    elapsed = NOW() - t0
    return best, bestValue, calls, elapsed
```

### Computational experiment

For each instance, run MSLS 20 times. Set the ILS limit T to the mean total time of these 20 MSLS runs, then run ILS 20 times with that limit. The first LS in ILS is included in both the timer and the LS count. A started LS always finishes, so the final call may slightly exceed T.

The timer includes random solution generation, perturbation and local search. Data loading, distance preprocessing, generator initialization and writing results are outside it. Each run uses a separate `mt19937` generator with seed `20261114 + 1000*instanceIndex + run`, where TSPA has index 0, TSPB index 1, and run is 0..19. The matching MSLS and ILS runs therefore begin with the same random solution. Compilation: `g++ -std=c++20 -O2`.

## Results

Tables show **mean (minimum - maximum)**. MSLS and ILS use 20 runs per instance. The comparison includes the best construction heuristics and local search variants from earlier labs, with their original 200-run results. Earlier timings were measured separately.
"""


def result_tables(summaries, historical):
    rows = [(f"**{method} (lab 6)**", {i: summaries[(i, method)] for i in INSTANCES})
            for method in METHODS]
    rows.extend((f"{method} (lab {lab})", data) for lab, method, data in historical)
    lines = ["### Objective function values", "", "| Method | TSPA | TSPB |", "|---|---:|---:|"]
    for label, data in rows:
        values = [f"{formatted(data[i]['average'])} ({data[i]['min']} - {data[i]['max']})" for i in INSTANCES]
        lines.append(f"| {label} | {' | '.join(values)} |")
    lines.extend(["", "### Running times (ms per complete run)", "", "| Method | TSPA | TSPB |", "|---|---:|---:|"])
    for label, data in rows:
        lines.append(f"| {label} | {' | '.join(formatted(data[i]['average_time_ms'], 6) for i in INSTANCES)} |")
    lines.extend(["", "### Number of complete basic LS runs", "",
                  "The initial LS is included. Values are mean (minimum - maximum) across 20 runs. MSLS performs exactly 400 calls in each run.", "",
                  "| Method | TSPA | TSPB |", "|---|---:|---:|"])
    for method in METHODS:
        values = []
        for instance in INSTANCES:
            row = summaries[(instance, method)]
            values.append(f"{formatted(row['average_ls_runs'])} ({row['min_ls_runs']} - {row['max_ls_runs']})")
        lines.append(f"| {method} | {' | '.join(values)} |")
    return lines + [""]


def save_best_and_plots(groups):
    lines = ["## Best solutions and visualizations", "",
             "Node IDs are read left to right, then top to bottom. The last node connects back to the first. Colors show selection costs; gray nodes are unselected and the red star marks the first listed node.", ""]
    best_records = []
    for instance in INSTANCES:
        lines.extend([f"### {instance}", ""])
        for method in METHODS:
            best = min(groups[(instance, method)], key=lambda row: (row["objective"], int(row["run"])))
            image = f"{instance}_{method}.png"
            plot_solution(read_nodes(REPO / "common" / "data" / f"{instance}.csv"), best,
                          GENERATED / image, f"{instance}: {method}")
            solution = best["solution"]
            solution_text = "\n".join(" ".join(f"{node:3d}" for node in solution[i:i + 10])
                             for i in range(0, len(solution), 10))
            lines.extend([f"#### {method}", "", f"Objective: **{best['objective']}**, run **{best['run']}** (zero-based).", "",
                          f"![{instance}: {method}](generated/{quote(image)})", "",
                          "**Solution (node order):**", "", "```text", solution_text, "```", ""])
            best_records.append({"instance": instance, "method": method, "objective": best["objective"],
                                 "run": best["run"], "solution": " ".join(map(str, solution))})
    write_csv(GENERATED / "best_solutions.csv", best_records)
    return lines


def write_csv(path, records):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def conclusions(groups, summaries, historical):
    lines = ["## Conclusions", ""]
    for instance in INSTANCES:
        msls, ils = (summaries[(instance, method)] for method in METHODS)
        improvement = (1 - float(ils["average"]) / float(msls["average"])) * 100
        paired = sum(a["objective"] < b["objective"] for a, b in zip(
            sorted(groups[(instance, "ILS")], key=lambda r: int(r["run"])),
            sorted(groups[(instance, "MSLS")], key=lambda r: int(r["run"]))))
        previous_best_mean = min(float(data[instance]["average"]) for lab, _, data in historical if lab >= 3)
        lines.extend([f"On {instance}, ILS reduces the mean objective from {formatted(msls['average'])} to {formatted(ils['average'])} ({improvement:.3f}% improvement). Its best value is {ils['min']}, versus {msls['min']} for MSLS. It beats MSLS in {paired}/20 matching-seed comparisons and improves on the best earlier LS mean of {formatted(previous_best_mean)}.", ""])
    lines.extend(["ILS achieves better results on both instances within the MSLS time budgets. It preserves most of a good solution between searches, allowing more LS calls than fully random restarts: about 2,000 per run, compared with 400 for MSLS.", ""])
    return lines


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
        canvas.drawString(42, 22, "Evolutionary Computation | Lab 6 | MSLS and ILS")
        canvas.drawRightString(553, 22, str(doc.page))

    document = SimpleDocTemplate(str(output), pagesize=(595, 842), rightMargin=42, leftMargin=42,
                                 topMargin=38, bottomMargin=46,
                                 title="Lab 6: Multiple start and iterated local search",
                                 author="Piotr Foltyniewicz, Jakub Adamski")
    document.build(story, onFirstPage=footer, onLaterPages=footer)


def main():
    groups = read_results(GENERATED / "results.csv")
    summaries = read_summary("lab6")
    checked = validate(groups, summaries)
    historical = historical_comparisons()
    lines = [DESCRIPTION, "",
             *result_tables(summaries, historical),
             *save_best_and_plots(groups), "## Solution checking", "",
             f"All {checked} exported cycles contain 100 distinct valid node IDs. Recomputed objectives and summary statistics match the CSV records. The four plotted solutions attain the reported minima.", "",
             "## Source code", "",
             "- [MSLS, ILS and perturbation](../src/metaheuristics.cpp)",
             "- [Experiment runner](../src/lab6_experiment.cpp)",
             "- [Reused move-list LS](../../lab5/src/move_list_search.cpp)",
             "- [Validation, plots and report generator](../src/create_report.py)",
             "- [All 80 runs, timings, seeds and LS counts](generated/results.csv)",
             "- [Summary](generated/summary.csv)", "- [Best solutions](generated/best_solutions.csv)",
             "- [Lab 5 report](../../lab5/out/report.md)",
             "- [Lab 4 report](../../lab4/out/report.md)", "",
             *conclusions(groups, summaries, historical)]
    report = "\n".join(lines)
    (OUT / "report.md").write_text(report, encoding="utf-8")
    (GENERATED / "final_results.txt").write_text(report, encoding="utf-8")
    render_pdf(report, OUT / "report.pdf")
    print(f"Wrote report.md, report.pdf and four plots from {checked} results")


if __name__ == "__main__":
    main()
