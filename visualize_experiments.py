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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path("output/greedy_results.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("output/generated"))
    parser.add_argument("--instances-dir", type=Path, default=Path("."))
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    groups = read_results(args.results)
    report = ["# Lab 1 visualizations", "", "| Instance | Method | Min | Max | Average |", "|---|---|---:|---:|---:|"]
    for (instance, method), records in sorted(groups.items()):
        best = min(records, key=lambda row: (row["objective"], int(row["run"])))
        values = [int(row["objective"]) for row in records]
        image = f"{Path(instance).stem}_{method}.png"
        plot_solution(read_nodes(args.instances_dir / instance), best, args.output_dir / image, f"{instance}: {method}")
        report.append(f"| {instance} | {method} | {min(values)} | {max(values)} | {sum(values) / len(values):.2f} |")
        report.append(f"\nBest `{method}` for `{instance}`: objective `{best['objective']}`, nodes `{best['solution']}`; [visualization]({image}).")
    report.extend(["", "The exported objective values were calculated by the C++ `assessSolution` function. A separate solution checker is not present in the current codebase.", "", "Source: [`visualize_experiments.py`](../../visualize_experiments.py)."])
    (args.output_dir / "greedy_final_result.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote visualizations and report to {args.output_dir}")


if __name__ == "__main__":
    main()
