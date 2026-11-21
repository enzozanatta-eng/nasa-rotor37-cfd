"""Plot the CFX monitor history (exported from CFX-Solver Manager) and print
the convergence statistics used in the report.

Usage: python plot_monitors.py ../data/monitor_history.csv ../images/monitors.png
"""

import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def read_blocks(path):
    """CFX 'User Points' export: [Name] / [Data] blocks of x, y pairs."""
    blocks, name, rows = {}, None, None
    for line in open(path, encoding="utf-8"):
        s = line.strip()
        if s.startswith('"User Points'):
            name = s.split("Monitor Point:")[1].split(",")[0].strip()
        elif s == "[Data]":
            rows = []
            blocks[name] = rows
        elif rows is not None and s and s[0].isdigit():
            x, y = s.split(",")
            rows.append((float(x), float(y)))
    return {k: np.array(v) for k, v in blocks.items()}


def main(src, dst):
    m = read_blocks(src)
    last = 50
    print(f"{'monitor':10s} {'final':>10s} {'mean(last50)':>13s} {'range(last50) %':>16s}")
    for k, v in m.items():
        y = v[-last:, 1]
        print(f"{k:10s} {v[-1, 1]:10.4f} {y.mean():13.4f} {100 * np.ptp(y) / y.mean():16.3f}")

    fig, axes = plt.subplots(3, 1, figsize=(8, 8), sharex=True)
    spec = [("mon_mdot", "Mass flow, full annulus [kg/s]", "#1f77b4", (19.5, 21.5)),
            ("mon_PR", "Total pressure ratio [-]", "#d62728", (1.2, 1.9)),
            ("mon_eta", "Isentropic efficiency [-]", "#2ca02c", (0.45, 0.9))]
    for ax, (key, label, color, lim) in zip(axes, spec):
        v = m[key]
        ax.plot(v[:, 0], v[:, 1], color=color, lw=1.8)
        ax.set_ylabel(label)
        ax.set_ylim(*lim)
        ax.grid(alpha=0.3)
    axes[0].axhline(20.93, color="k", ls="--", lw=1)
    axes[0].text(2, 21.0, "NASA measured choke mass flow, 20.93 kg/s", fontsize=9)
    axes[-1].set_xlabel("Iteration")
    fig.suptitle("Monitor history, outlet static pressure 95 kPa", fontsize=12)
    fig.tight_layout()
    fig.savefig(dst, dpi=200)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
