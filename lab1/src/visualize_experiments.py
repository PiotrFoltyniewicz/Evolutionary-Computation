"""Visualize CSV results exported by the C++ experiment executable."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def read_nodes(path: Path) -> list[tuple[int, int, int]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return [(int(x), int(y), int(cost)) for x, y, cost in csv.reader(stream, delimiter=";")]


def read_results(path: Path) -> dict[tuple[str, str], list[dict[str, object]]]:
    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            row["objective"] = int(row["objective"])
            row["solution"] = [int(index) for index in row["solution"].split()]
            groups[(row["instance"], row["method"])].append(row)
    return groups


def read_summary(path: Path) -> dict[tuple[str, str], dict[str, object]]:
    summaries: dict[tuple[str, str], dict[str, object]] = {}
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            row["min"] = int(row["min"])
            row["max"] = int(row["max"])
            row["average"] = float(row["average"])
            row["average_time_ms"] = float(row["average_time_ms"])
            summaries[(row["instance"], row["method"])] = row
    return summaries


def plot_solution(nodes, record, output: Path, title: str) -> None:
    solution = record["solution"]
    cycle = solution + [solution[0]]
    selected = set(solution)
    figure, axis = plt.subplots(figsize=(9, 7))
    axis.scatter(
        [node[0] for i, node in enumerate(nodes) if i not in selected],
        [node[1] for i, node in enumerate(nodes) if i not in selected],
        color="lightgray",
        s=15,
        label="not selected",
    )
    axis.plot([nodes[i][0] for i in cycle], [nodes[i][1] for i in cycle], color="tab:blue", linewidth=0.8)
    points = axis.scatter(
        [nodes[i][0] for i in solution],
        [nodes[i][1] for i in solution],
        c=[nodes[i][2] for i in solution],
        cmap="viridis",
        s=34,
        zorder=3,
    )
    axis.scatter([nodes[solution[0]][0]], [nodes[solution[0]][1]], color="red", marker="*", s=65, label="start")
    figure.colorbar(points, ax=axis, label="node cost")
    axis.set_title(f"{title}\nobjective = {record['objective']}")
    axis.set_xlabel("x")
    axis.set_ylabel("y")
    axis.set_aspect("equal", adjustable="box")
    axis.legend()
    figure.tight_layout()
    figure.savefig(output, dpi=160)
    plt.close(figure)


def main() -> None:
    repo_dir = Path(__file__).resolve().parents[2]
    out_dir = repo_dir / "lab1" / "out" / "generated"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=out_dir / "greedy_results.csv")
    parser.add_argument("--summary", type=Path, default=out_dir / "greedy_summary.csv")
    parser.add_argument("--output-dir", type=Path, default=out_dir)
    parser.add_argument("--instances-dir", type=Path, default=repo_dir / "common" / "data")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    groups = read_results(args.results)
    summaries = read_summary(args.summary)
    report = ["# Lab 1 visualizations", "", "| Instance | Method | Min | Max | Average | Avg time (ms) |", "|---|---|---:|---:|---:|---:|"]
    for (instance, method), records in sorted(groups.items()):
        best = min(records, key=lambda row: (row["objective"], int(row["run"])))
        image = f"{Path(instance).stem}_{method}.png"
        plot_solution(read_nodes(args.instances_dir / Path(instance).name), best, args.output_dir / image, f"{instance}: {method}")
        summary = summaries[(instance, method)]
        report.append(f"| {instance} | {method} | {summary['min']} | {summary['max']} | {summary['average']:.2f} | {summary['average_time_ms']:.6f} |")
        report.append(f"Best `{method}` for `{instance}`: objective `{best['objective']}`; [visualization]({image}).")
        report.extend(["", "```text", "\n".join(str(node) for node in best["solution"]), "```"])
        report.append("")
    report.extend(["", "The exported objective values were calculated by the C++ `assessSolution` function. A separate solution checker is not present in the current codebase.", "", "Source: [`visualize_experiments.py`](../../src/visualize_experiments.py)."])
    (args.output_dir / "greedy_final_result.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote visualizations and report to {args.output_dir}")


if __name__ == "__main__":
    main()
