"""Visualize CSV results exported by the C++ experiment executable."""

from __future__ import annotations

import argparse
import csv
import os
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
    figure, axis = plt.subplots(figsize=(8, 5.5), layout="constrained")
    axis.scatter(
        [node[0] for i, node in enumerate(nodes) if i not in selected],
        [node[1] for i, node in enumerate(nodes) if i not in selected],
        color="lightgray",
        s=15,
        label="not selected",
    )
    axis.plot([nodes[i][0] for i in cycle], [nodes[i][1] for i in cycle], color="tab:blue", linewidth=0.8)
    points = axis.scatter(
        [nodes[i][0] for i in solution[1:]],
        [nodes[i][1] for i in solution[1:]],
        c=[nodes[i][2] for i in solution[1:]],
        cmap="viridis",
        vmin=min(node[2] for node in nodes),
        vmax=max(node[2] for node in nodes),
        s=34,
        zorder=3,
    )
    axis.scatter([nodes[solution[0]][0]], [nodes[solution[0]][1]], color="red", marker="*", s=90, zorder=4, label="first node")
    colorbar = figure.colorbar(
        points, ax=axis, orientation="horizontal", shrink=0.65,
        aspect=40, pad=0.08, label="Node cost",
    )
    colorbar.outline.set_visible(False)
    colorbar.ax.tick_params(labelsize=9, length=3)

    axis.set_title(f"{title}\nobjective = {record['objective']}", pad=38)
    axis.set_xlabel("x")
    axis.set_ylabel("y")
    axis.set_aspect("equal", adjustable="box")
    axis.legend(frameon=False, fontsize=9, loc="lower center",
                bbox_to_anchor=(0.5, 1.01), ncol=2)
    axis.spines[["top", "right"]].set_visible(False)
    figure.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    repo_dir = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lab", choices=[f"lab{i}" for i in range(1, 13)])
    args = parser.parse_args()
    out_dir = repo_dir / args.lab / "out" / "generated"
    out_dir.mkdir(parents=True, exist_ok=True)
    groups = read_results(out_dir / "results.csv")
    summaries = read_summary(out_dir / "summary.csv")
    report = [f"# {args.lab.capitalize()} visualizations", "", "| Instance | Method | Min | Max | Average | Avg time (ms) |", "|---|---|---:|---:|---:|---:|"]
    for (instance, method), records in sorted(groups.items()):
        best = min(records, key=lambda row: (row["objective"], int(row["run"])))
        image = f"{Path(instance).stem}_{method}.png"
        plot_solution(read_nodes(repo_dir / "common" / "data" / f"{instance}.csv"), best, out_dir / image, f"{instance}: {method}")
        summary = summaries[(instance, method)]
        report.append(f"| {instance} | {method} | {summary['min']} | {summary['max']} | {summary['average']:.2f} | {summary['average_time_ms']:.6f} |")
        report.append(f"Best `{method}` for `{instance}`: objective `{best['objective']}`; [visualization]({image}).")
        report.extend(["", "```text", "\n".join(str(node) for node in best["solution"]), "```"])
        report.append("")
    source = Path(os.path.relpath(Path(__file__).resolve(), out_dir.resolve())).as_posix()
    report.extend(["", f"Source: [`visualize_experiments.py`]({source})."])
    (out_dir / "final_results.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote visualizations and report to {out_dir}")


if __name__ == "__main__":
    main()
