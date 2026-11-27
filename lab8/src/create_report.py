"""Calculate similarity correlations and create the lab 8 report."""

import csv
import sys
from collections import Counter
from dataclasses import dataclass
from math import floor, hypot
from pathlib import Path
from statistics import correlation

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Table, TableStyle

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "lab8/out"
GENERATED = OUT / "generated"
sys.path.insert(0, str(ROOT / "common/src"))
from visualize_experiments import read_nodes, read_results

INSTANCES = ("TSPA", "TSPB")
METHOD = "Greedy Edges Random"
COMPARISONS = {
    "average": "Average similarity",
    "best_local": "Similarity to the best of 1000",
    "best_method": "Similarity to ILS (lab 6)",
}
MEASURES = {"edges": "Common edges", "nodes": "Common selected nodes"}
TITLE = "Lab 8 - Global convexity"
AUTHORS = "Authors - Piotr Foltyniewicz 160295, Jakub Adamski 160291"
DESCRIPTION = (
    "Select 100 distinct nodes from 200 and arrange them in a closed cycle. Minimize selected-node "
    "costs plus rounded Euclidean edge lengths, including the closing edge.",
    "For each instance, generate 1000 random solutions and apply greedy local search from lab 3. "
    "The neighborhood consists of selected-node replacements and edge exchanges (2-opt). "
    "Apply the first improving move in random order until no improving move remains.",
)
PSEUDOCODE = """for each instance:
    optima = 1000 runs of GREEDY_LS(RANDOM_SOLUTION())
    best = first optimum with the lowest objective
    ils = best ILS cycle from lab 6
    for each optimum S in optima:
        for each measure in [common edges, common selected nodes]:
            average = sum(COMMON(S, T) for the other 999 runs) / 999
            save (F(S), average) for the average similarity chart
            for each reference in [best, ils]:
                if S and reference have different edge sets:
                    save (F(S), COMMON(S, reference)) for its chart
    calculate Pearson's r for the points in each chart"""
SIMILARITY_NOTE = (
    "Edges are undirected and include the closing edge. The average compares each run with the "
    "other 999 runs. For a single reference, any occurrence of its cycle is excluded from both "
    "charts. Reversing or rotating the cycle leaves its edge set unchanged."
)
SOURCES = (
    ("Experiment runner", "../src/lab8_experiment.cpp"),
    ("Greedy local search", "../../lab3/src/local_search_methods.cpp"),
    ("ILS reference cycles", "../../lab6/out/generated/best_solutions.csv"),
    ("Similarity calculations and report generator", "../src/create_report.py"),
)


@dataclass(frozen=True)
class Chart:
    instance: str
    comparison: str
    measure: str
    points: int
    coefficient: float

    @property
    def filename(self):
        return f"{self.instance}_{self.comparison}_{self.measure}.png"


def cycle_edges(cycle):
    return {tuple(sorted((a, b))) for a, b in zip(cycle, cycle[1:] + cycle[:1])}


def average_similarities(features):
    counts = Counter(feature for solution in features for feature in solution)
    return [sum(counts[feature] - 1 for feature in solution) / (len(features) - 1)
            for solution in features]


def ils_references():
    path = ROOT / "lab6/out/generated/best_solutions.csv"
    with path.open(newline="", encoding="utf-8") as stream:
        references = {row["instance"]: row for row in csv.DictReader(stream) if row["method"] == "ILS"}
    for instance in INSTANCES:
        reference = references[instance]
        nodes = read_nodes(ROOT / f"common/data/{instance}.csv")
        cycle = [int(node) for node in reference["solution"].split()]
        if len(cycle) != 100 or len(set(cycle)) != 100 or min(cycle) < 0 or max(cycle) >= len(nodes):
            raise ValueError(f"Invalid ILS cycle for {instance}")
        objective = sum(nodes[node][2] for node in cycle) + sum(
            floor(hypot(nodes[a][0] - nodes[b][0], nodes[a][1] - nodes[b][1]) + 0.5)
            for a, b in cycle_edges(cycle)
        )
        if objective != int(reference["objective"]):
            raise ValueError(f"Invalid ILS objective for {instance}")
        references[instance] = (cycle, objective)
    return references


def plot_chart(chart, objectives, similarities, limits):
    figure, axis = plt.subplots(figsize=(4.4, 3.5), layout="constrained")
    axis.scatter(objectives, similarities, s=11, alpha=0.45, color="#245d83", linewidths=0)
    axis.set_title(f"{chart.instance} - {COMPARISONS[chart.comparison]}\n"
                   f"r = {chart.coefficient:.3f}, n = {chart.points}", fontsize=11)
    axis.set_xlabel("Objective function value", fontsize=10)
    ylabel = MEASURES[chart.measure]
    if chart.comparison == "average":
        ylabel = "Average " + ylabel.lower()
    axis.set_ylabel(ylabel, fontsize=10)
    axis.set_xlim(limits)
    axis.xaxis.set_major_locator(MaxNLocator(5, integer=True))
    axis.yaxis.set_major_locator(MaxNLocator(5, integer=chart.comparison != "average"))
    axis.tick_params(labelsize=9)
    axis.set_axisbelow(True)
    axis.grid(color="#dbe3e9", linewidth=0.6)
    figure.savefig(GENERATED / chart.filename, dpi=200)
    plt.close(figure)


def charts_for_instance(instance, runs, ils_cycle):
    cycles = [row["solution"] for row in runs]
    objectives = [row["objective"] for row in runs]
    best = min(range(len(runs)), key=objectives.__getitem__)
    edges = [cycle_edges(cycle) for cycle in cycles]
    ils_edges = cycle_edges(ils_cycle)
    indices = {
        "average": list(range(len(runs))),
        "best_local": [i for i, cycle in enumerate(edges) if cycle != edges[best]],
        "best_method": [i for i, cycle in enumerate(edges) if cycle != ils_edges],
    }
    features = {"edges": (edges, ils_edges), "nodes": ([set(cycle) for cycle in cycles], set(ils_cycle))}
    padding = (max(objectives) - min(objectives)) * 0.04
    limits = (min(objectives) - padding, max(objectives) + padding)
    charts = {}
    for measure, (sets, ils_set) in features.items():
        similarities = {
            "average": average_similarities(sets),
            "best_local": [len(solution & sets[best]) for solution in sets],
            "best_method": [len(solution & ils_set) for solution in sets],
        }
        for comparison, selected in indices.items():
            x = [objectives[i] for i in selected]
            y = [similarities[comparison][i] for i in selected]
            chart = Chart(instance, comparison, measure, len(x), correlation(x, y))
            plot_chart(chart, x, y, limits)
            charts[(instance, comparison, measure)] = chart
    return charts, objectives[best]


def result_tables(charts, best_values, references):
    objectives = [["Reference", *INSTANCES],
                  ["Best of 1000 local optima", *(best_values[i] for i in INSTANCES)],
                  ["ILS (lab 6)", *(references[i][1] for i in INSTANCES)]]
    correlations = [["Comparison", "Measure", *INSTANCES]]
    for comparison, label in COMPARISONS.items():
        for measure, name in MEASURES.items():
            correlations.append([label, name, *(f"{charts[i, comparison, measure].coefficient:.3f}"
                                                 for i in INSTANCES)])
    return objectives, correlations


def conclusions(charts):
    magnitudes = {key: abs(chart.coefficient) for key, chart in charts.items()}
    paragraphs = []
    if all(magnitudes[i, "average", "edges"] > magnitudes[i, "average", "nodes"] for i in INSTANCES):
        paragraphs.append("For average similarity, common edges are more strongly associated with a low "
                          "objective value than common nodes on both instances. Better optima tend to use "
                          "the connections that recur across the sample.")

    reference_findings = []
    if all(magnitudes[i, comparison, "nodes"] > magnitudes[i, comparison, "edges"]
           for i in INSTANCES for comparison in ("best_local", "best_method")):
        reference_findings.append("With either single reference, common nodes have the stronger correlation "
                                  "on both instances. Better optima tend to share more of the reference's "
                                  "selected nodes even when they connect them differently.")
    if all(magnitudes[i, "best_method", m] > magnitudes[i, "best_local", m]
           for i in INSTANCES for m in MEASURES):
        reference_findings.append("The ILS cycle gives a stronger correlation for both measures than the best "
                                  "of the 1000 optima, so the choice of reference matters for this comparison.")
    if reference_findings:
        paragraphs.append(" ".join(reference_findings))

    negative = sum(chart.coefficient < 0 for chart in charts.values())
    direction = ("The negative correlations on both instances support global convexity in the sampled optima."
                 if negative == len(charts)
                 else f"{negative} of the {len(charts)} correlations are negative.")
    paragraphs.append(direction + " The spread in the plots shows that solutions with similar overlap can "
                      "still differ substantially in cost. Similarity indicates promising parts of the "
                      "search space, with the objective needed to rank individual cycles.")
    return paragraphs


def markdown_table(rows):
    lines = [rows[0], ["---"] * len(rows[0]), *rows[1:]]
    return "\n".join("| " + " | ".join(map(str, row)) + " |" for row in lines)


def write_markdown(charts, objectives, correlations, conclusion_paragraphs):
    sections = [f"# {TITLE}", AUTHORS, "## Problem description", *DESCRIPTION, "## Pseudocode",
                SIMILARITY_NOTE, f"```text\n{PSEUDOCODE}\n```", "## Results",
                "### Objective function values", markdown_table(objectives),
                "### Pearson correlation coefficients", markdown_table(correlations), "## Visualizations"]
    for instance in INSTANCES:
        sections.append(f"### {instance}")
        for comparison, label in COMPARISONS.items():
            sections.append(f"#### {label}")
            for measure, name in MEASURES.items():
                chart = charts[instance, comparison, measure]
                sections.append(f"![{instance} - {label} - {name}](generated/{chart.filename})")
    links = "\n".join(f"- [{label}]({path})" for label, path in SOURCES)
    sections.extend(["## Conclusions", *conclusion_paragraphs, "## Source code", links])
    (OUT / "report.md").write_text("\n\n".join(sections) + "\n", encoding="utf-8")


def write_pdf(charts, objectives, correlations, conclusion_paragraphs):
    styles = getSampleStyleSheet()
    styles["Code"].fontSize = 8
    styles["Code"].leading = 10
    styles["Code"].backColor = colors.HexColor("#f2f5f7")
    styles["Code"].borderPadding = 6
    styles["Code"].spaceBefore = 10
    styles["Code"].spaceAfter = 7
    styles["BodyText"].spaceAfter = 4
    header_color = colors.HexColor("#173e59")
    document = SimpleDocTemplate(str(OUT / "report.pdf"), pagesize=A4, leftMargin=42,
                                 rightMargin=42, topMargin=38, bottomMargin=46,
                                 title=TITLE, author="Piotr Foltyniewicz, Jakub Adamski")

    def paragraph(text, style="BodyText"):
        return Paragraph(text, styles[style])

    def table(rows, widths):
        return Table(rows, colWidths=widths, hAlign="LEFT", style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), header_color),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (-2, 0), (-1, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f7")]),
        ]))

    def footer(canvas, doc):
        canvas.setStrokeColor(colors.HexColor("#cbd5dc"))
        canvas.line(42, 34, A4[0] - 42, 34)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#526675"))
        canvas.drawString(42, 22, "Evolutionary Computation | Lab 8 | Global convexity")
        canvas.drawRightString(A4[0] - 42, 22, str(doc.page))

    story = [paragraph(TITLE, "Title"), paragraph(AUTHORS), paragraph("Problem description", "Heading1"),
             *(paragraph(text) for text in DESCRIPTION), paragraph("Pseudocode", "Heading1"),
             paragraph(SIMILARITY_NOTE), Preformatted(PSEUDOCODE, styles["Code"]),
             paragraph("Results", "Heading1"), paragraph("Objective function values", "Heading2"),
             table(objectives, [327, 86, 86]), paragraph("Pearson correlation coefficients", "Heading2"),
             table(correlations, [185, 142, 86, 86])]
    for instance in INSTANCES:
        story.extend([PageBreak(), paragraph(f"Visualizations - {instance}", "Heading1")])
        images = [[Image(str(GENERATED / charts[instance, comparison, measure].filename),
                         width=244, height=244 * 3.5 / 4.4) for measure in MEASURES]
                  for comparison in COMPARISONS]
        story.append(Table(images, colWidths=[249.5, 249.5], hAlign="LEFT", style=TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ])))
    story.extend([PageBreak(), paragraph("Conclusions", "Heading1"),
                  *(paragraph(text) for text in conclusion_paragraphs),
                  paragraph("Source code", "Heading1"),
                  *(paragraph(f"{label} ({path})") for label, path in SOURCES)])
    document.build(story, onFirstPage=footer, onLaterPages=footer)


def main():
    groups = read_results(GENERATED / "results.csv")
    references = ils_references()
    best_values = {}
    charts = {}
    for instance in INSTANCES:
        runs = sorted(groups[instance, METHOD], key=lambda row: int(row["run"]))
        if [int(row["run"]) for row in runs] != list(range(1000)):
            raise ValueError(f"Expected 1000 runs for {instance}")
        instance_charts, best_values[instance] = charts_for_instance(instance, runs, references[instance][0])
        charts.update(instance_charts)

    with (GENERATED / "summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["instance", "comparison", "measure", "points", "pearson_r"])
        for instance in INSTANCES:
            for comparison in COMPARISONS:
                for measure in MEASURES:
                    chart = charts[instance, comparison, measure]
                    writer.writerow([instance, comparison, measure, chart.points, chart.coefficient])
    objectives, correlations = result_tables(charts, best_values, references)
    conclusion_paragraphs = conclusions(charts)
    write_markdown(charts, objectives, correlations, conclusion_paragraphs)
    write_pdf(charts, objectives, correlations, conclusion_paragraphs)


if __name__ == "__main__":
    main()
