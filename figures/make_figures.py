#!/usr/bin/env python3
"""Generate every figure of the Decision Coprocessor paper.

Outputs SVG + PDF into paper/figures/. Run with:

    uv run --with matplotlib --no-project python figures/make_figures.py

All plotted numbers come from docs/10-results-reference.md (frozen snapshot).
"""
from __future__ import annotations

import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

# consistent palette
C_BLUE = "#2F6FBE"
C_BG = "#EDF3FB"
C_GREEN = "#2E8B57"
C_GREEN_BG = "#E7F4EC"
C_ORANGE = "#C97B2E"
C_ORANGE_BG = "#FBF0E2"
C_RED = "#B03A3A"
C_RED_BG = "#F8E9E9"
C_GREY = "#6B7280"
C_GREY_BG = "#F1F2F4"
C_PURPLE = "#6A4FA3"
C_PURPLE_BG = "#F0ECF9"


def new_canvas(w=12.0, h=6.6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, *, fc=C_BG, ec=C_BLUE, fs=9.5, weight="normal", radius=1.6, lw=1.4, align="center"):
    p = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.4,rounding_size={radius}",
        linewidth=lw, edgecolor=ec, facecolor=fc, zorder=2,
    )
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, weight=weight, color="#1F2937", zorder=3, linespacing=1.45)
    return (x, y, w, h)


def arrow(ax, x1, y1, x2, y2, *, color=C_GREY, style="-|>", lw=1.4, ls="-", rad=0.0):
    a = FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle=style, mutation_scale=14,
        linewidth=lw, color=color, linestyle=ls, zorder=1,
        connectionstyle=f"arc3,rad={rad}",
    )
    ax.add_patch(a)


def title(ax, text, sub=None):
    ax.text(50, 96.5, text, ha="center", va="center", fontsize=13, weight="bold", color="#111827")
    if sub:
        ax.text(50, 91.5, sub, ha="center", va="center", fontsize=9.5, color=C_GREY)


def save(fig, name):
    for ext in ("svg", "pdf"):
        fig.savefig(OUT / f"{name}.{ext}", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", name)


# ---------------------------------------------------------------------------
# Figure 1 — V1 architecture
# ---------------------------------------------------------------------------
def fig01_v1_architecture():
    fig, ax = new_canvas(12.5, 6.8)
    title(ax, "V1 — frozen backbone + direct head + latent recurrent sidecar")

    box(ax, 2, 38, 17, 18,
        "Problem (text)\nstate · question\n2–16 candidates", fc=C_GREY_BG, ec=C_GREY)
    box(ax, 25, 38, 18, 18,
        "Qwen3-0.6B\nfrozen · bf16\nH ∈ B×L×1024", fc=C_BG, ec=C_BLUE, weight="bold")
    box(ax, 50, 63, 20, 15,
        "Direct head B2\nq, c_i → [q, c_i, q⊙c_i, |q−c_i|]\n1,054,209 params",
        fc=C_PURPLE_BG, ec=C_PURPLE)
    box(ax, 51, 30, 20, 22,
        "Latent sidecar R (k = 1/2/4)\n8 slots · d=256 · 1 shared block\n"
        "cross-attn(H) + self-attn + FFN\n2,110,465 params",
        fc=C_GREEN_BG, ec=C_GREEN)
    box(ax, 77, 55, 18, 12, "logits₀ = MLP(features)", fc="#FFFFFF", ec=C_PURPLE)
    box(ax, 77, 25, 18, 12, "Δ = CorrectionHead\n[q, c_i, r_i]", fc="#FFFFFF", ec=C_GREEN)
    box(ax, 77, 41, 18, 9, "logits_k = logits₀ + Δ", fc=C_ORANGE_BG, ec=C_ORANGE, weight="bold")

    arrow(ax, 19, 47, 25, 47)
    arrow(ax, 43, 50, 50, 68)
    arrow(ax, 43, 42, 51, 36)
    arrow(ax, 70, 70, 77, 62)
    arrow(ax, 71, 41, 77, 33)
    arrow(ax, 86, 55, 86, 50)
    arrow(ax, 86, 37, 86, 41)

    ax.text(37, 27, "one backbone pass per example\nwhatever k", fontsize=8.5, color=C_GREY, ha="center")
    ax.text(50, 18, "budget 0 → exact direct logits (bypass)",
            fontsize=8.5, color=C_RED, ha="left")
    ax.text(50, 13.5, "shortcut found by the audit: Δ head sees q and c_i directly → can bypass Z_k",
            fontsize=8.5, color=C_RED, ha="left", style="italic")
    save(fig, "fig01-v1-architecture")


# ---------------------------------------------------------------------------
# Figure 2 — V2 executor
# ---------------------------------------------------------------------------
def fig02_v2_executor():
    fig, ax = new_canvas(12.5, 6.4)
    title(ax, "V2 stage S — supervised transition executor (92,802 params, CPU)",
          "state s_t = (h_t, p_t) · one shared transition F · anti-shortcut readout")

    # graph nodes
    xs = [12, 26, 40, 54]
    labels = ["start\nq3x", "b2w", "r9d", "terminal\nk7m"]
    for i, (x, lab) in enumerate(zip(xs, labels)):
        fc = C_ORANGE_BG if i == 3 else C_BG
        ec = C_ORANGE if i == 3 else C_BLUE
        box(ax, x, 68, 12, 11, f"h_{i}\n{lab}", fc=fc, ec=ec, fs=8.5)
        if i:
            arrow(ax, xs[i - 1] + 12, 73.5, x, 73.5)

    # pointer wavefront
    for i, x in enumerate(xs):
        ax.text(x + 6, 62.5, ["p=1", "0", "0", "0"][i], ha="center", fontsize=8.5,
                color=C_RED if i == 0 else C_GREY, weight="bold" if i == 0 else "normal")

    box(ax, 5, 40, 40, 15,
        "Shared transition F (applied 16×)\nm_i = Σ_j p_j φ(h_j, h_i, rel_ji) / Σ_j p_j\n"
        "h_i ← GRUCell([m_i, question, p_i], h_i)",
        fc=C_GREEN_BG, ec=C_GREEN, fs=9)
    box(ax, 50, 40, 18, 15,
        "PointerHead\np_t = softmax(W h_t)\nterminal absorbing", fc=C_BG, ec=C_BLUE, fs=9)
    box(ax, 72, 40, 23, 15,
        "Readout (shared, anti-shortcut)\nscore_c = MLP([Σ p_T h_T,\nRAW candidate features])",
        fc=C_PURPLE_BG, ec=C_PURPLE, fs=9)
    box(ax, 72, 60, 23, 10,
        "answer = terminal pointed at\n(option id)", fc=C_ORANGE_BG, ec=C_ORANGE, weight="bold")
    box(ax, 5, 18, 40, 12,
        "Loss = CE(answer) + α · Σ_t w_t CE(state_t, exact trace_t),  α = 0.5",
        fc="#FFFFFF", ec=C_GREY, fs=9)
    box(ax, 50, 18, 45, 12,
        "Readout excludes: question · contextualised candidates · private depth\n"
        "p₀ = one-hot(start) · terminal is public · budget 16 fixed",
        fc=C_RED_BG, ec=C_RED, fs=8.5)

    arrow(ax, 25, 68, 25, 55)
    arrow(ax, 45, 47.5, 50, 47.5)
    arrow(ax, 68, 47.5, 72, 47.5)
    arrow(ax, 83.5, 55, 83.5, 60)
    arrow(ax, 25, 40, 25, 30, color=C_GREY)
    ax.text(26.5, 34.5, "state CE\n(per slot)", fontsize=7.5, color=C_GREY, ha="left", va="center")
    save(fig, "fig02-v2-executor")


# ---------------------------------------------------------------------------
# Figure 3 — V2 pipeline and cells
# ---------------------------------------------------------------------------
def fig03_v2_pipeline():
    fig, ax = new_canvas(12.5, 6.4)
    title(ax, "V2 stage T — decomposed pipeline vs direct path, under equal adaptation (F1)")

    box(ax, 2, 60, 16, 14, "French text\nstate + question\n+ options", fc=C_GREY_BG, ec=C_GREY)
    box(ax, 23, 60, 20, 14, "Reader LoRA\nedge F1 0.928\nvalidity 0.917", fc=C_GREEN_BG, ec=C_GREEN)
    box(ax, 48, 60, 18, 14, "Predicted graph\ntransition matrix A", fc=C_BG, ec=C_BLUE)
    box(ax, 71, 60, 27, 14, "Executor S (frozen)\n(c) discretisation or\npropagation p_T = p_0 A^T",
        fc=C_PURPLE_BG, ec=C_PURPLE)
    box(ax, 23, 38, 43, 12, "Exact solver (b)  ·  learned executor (c)  ·  naked (cn)",
        fc="#FFFFFF", ec=C_GREY, fs=9)
    box(ax, 71, 38, 27, 12, "Adapted direct (d)\ntext → answer · 1.000 dev",
        fc=C_ORANGE_BG, ec=C_ORANGE, weight="bold", fs=9)

    arrow(ax, 18, 67, 23, 67)
    arrow(ax, 43, 67, 48, 67)
    arrow(ax, 66, 67, 71, 67)
    arrow(ax, 60, 60, 60, 50, rad=0.0)

    # direct path routed below the solver row
    ax.plot([10, 10, 84.5], [60, 24, 24], color=C_ORANGE, lw=1.5, zorder=1)
    arrow(ax, 84.5, 24, 84.5, 38, color=C_ORANGE)

    ax.text(48, 53.5, "×", fontsize=13, color=C_RED, ha="center", va="center", weight="bold")
    ax.text(3, 16, "Pipeline cells: (a) exact memory + executor = 1.000 anchor  ·  (b) = (c) = 0.762  ·  (cn) = 0.820",
            fontsize=8.6, color="#1F2937", ha="left")
    ax.text(3, 11.5, "Δ(c − d) = −23.84 pts [−28.33; −19.60] → experience stop on short chains",
            fontsize=9, color=C_RED, ha="left", weight="bold")
    save(fig, "fig03-v2-pipeline")


# ---------------------------------------------------------------------------
# Figure 4 — depth curves (V2.1)
# ---------------------------------------------------------------------------
def fig04_depth_curves():
    depths = [1, 2, 3, 4, 6, 8, 10]
    direct = [1.00, 0.97, 0.91, 0.87, 0.53, 0.28, 0.31]
    pipeline = [0.92, 0.81, 0.76, 0.71, 0.67, 0.60, 0.56]
    cprop = 0.85
    a2 = 0.9975

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.4, 4.6))

    x = np.arange(len(depths))
    ax1.plot(x, direct, "-o", color=C_ORANGE, lw=2.2, ms=6, label="direct (d), frozen")
    ax1.plot(x, pipeline, "-s", color=C_BLUE, lw=2.2, ms=6, label="pipeline (c), frozen")
    ax1.plot(x, [a2] * len(depths), "-", color=C_GREEN, lw=2.4,
             label="A2 distributional (0.995–1.000, invariant)")
    ax1.axhline(cprop, color=C_GREEN, ls="--", lw=1.6, alpha=0.7,
                label="A1-bis propagation ≈ 0.85 (zero training)")
    ax1.axhline(0.95, color=C_GREY, ls=":", lw=1.3, label="deterministic parser ceiling 0.95")
    ax1.axvspan(2.5, 4.0, color="#F6F6F6", zorder=0)
    ax1.text(3.25, 0.42, "crossing\n4→6", ha="center", fontsize=8.5, color=C_GREY)
    ax1.set_xticks(x, [str(d) for d in depths])
    ax1.set_xlabel("chain depth")
    ax1.set_ylabel("accuracy (all-in, n=400/bench)")
    ax1.set_ylim(0, 1.05)
    ax1.set_title("V2.1/V2.2 on frozen + repaired checkpoints")
    ax1.grid(alpha=0.25)
    ax1.legend(fontsize=7.8, loc="lower left")

    variants = ["B2 direct", "B3 non-rec.", "B4 unshared", "R4 sidecar", "R1 (k=1)"]
    acc = [0.3418, 0.3343, 0.3382, 0.3359, 0.3361]
    err = [0.006, 0.006, 0.006, 0.006, 0.006]
    colors = [C_ORANGE, C_GREY, C_GREY, C_GREEN, C_GREEN]
    ax2.bar(variants, acc, yerr=err, color=colors, alpha=0.9, capsize=4)
    ax2.set_ylim(0.30, 0.36)
    ax2.set_ylabel("macro A/B/C depth accuracy")
    ax2.set_title("V1 reserved depth test (3 seeds): no sidecar advantage")
    ax2.grid(alpha=0.25, axis="y")
    for i, v in enumerate(acc):
        ax2.text(i, v + 0.002, f"{v:.3f}", ha="center", fontsize=8.5)
    ax2.tick_params(axis="x", labelsize=8.5)

    fig.tight_layout()
    save(fig, "fig04-depth-curves")


# ---------------------------------------------------------------------------
# Figure 5 — V1 main results (macro A/B/C by split)
# ---------------------------------------------------------------------------
def fig05_v1_main():
    splits = ["IID", "Depth", "Composition", "Simple (D)"]
    data = {
        "B2 direct": ([0.4884, 0.3418, 0.4081, 0.7473], C_ORANGE),
        "R4 sidecar": ([0.4908, 0.3359, 0.4073, 0.7473], C_GREEN),
        "B3 non-rec.": ([0.4918, 0.3343, 0.4070, 0.7477], C_GREY),
        "B4 unshared": ([0.4930, 0.3382, 0.4062, 0.7468], "#9AA0A6"),
    }
    x = np.arange(len(splits))
    width = 0.19
    fig, ax = plt.subplots(figsize=(10.6, 4.6))
    for i, (name, (vals, color)) in enumerate(data.items()):
        ax.bar(x + (i - 1.5) * width, vals, width, label=name, color=color, alpha=0.9)
    for i, s in enumerate(splits):
        ax.text(i, 0.02, "", ha="center")
    ax.axhline(0.25, color=C_RED, ls=":", lw=1.2)
    ax.text(3.42, 0.255, "chance", fontsize=8, color=C_RED, ha="right")
    ax.set_xticks(x, splits)
    ax.set_ylabel("macro A/B/C accuracy")
    ax.set_ylim(0, 0.85)
    ax.set_title("V1 reserved test (mean of 3 seeds) — controls match or beat the sidecar")
    ax.legend(fontsize=9, ncol=4, loc="upper left")
    ax.grid(alpha=0.25, axis="y")
    fig.tight_layout()
    save(fig, "fig05-v1-main")


# ---------------------------------------------------------------------------
# Figure 6 — A1-bis per-bench deltas
# ---------------------------------------------------------------------------
def fig06_a1bis():
    benches = ["B1\nshort", "B5\nsurface", "B6\ndistract", "B7\noptions", "B8\nstart", "B2\ndepth 6", "B3\ndepth 8", "B4\ndepth 10"]
    delta_disc = [5.50, 4.25, 6.00, 5.50, 9.25, 17.00, 25.50, 29.50]
    lo = [1.50, 0.25, 2.25, 1.50, 5.25, 12.50, 20.75, 24.50]
    hi = [9.25, 8.25, 9.75, 9.25, 13.50, 21.50, 30.00, 34.75]
    delta_direct = [-8.25, -8.75, -10.50, -8.50, 1.75, 31.25, 57.25, 54.75]

    x = np.arange(len(benches))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.6, 4.7), sharey=False)

    err = [np.array(delta_disc) - np.array(lo), np.array(hi) - np.array(delta_disc)]
    ax1.bar(x, delta_disc, yerr=err, color=C_GREEN, alpha=0.9, capsize=4)
    ax1.axhline(5.0, color=C_RED, ls="--", lw=1.4)
    ax1.text(0.1, 6.2, "success threshold +5 pts", fontsize=8, color=C_RED, ha="left")
    ax1.set_xticks(x, benches, fontsize=8)
    ax1.set_ylabel("Δ c_prop − c_discret (pts)")
    ax1.set_title("A1-bis vs discretisation (zero training)")
    ax1.grid(alpha=0.25, axis="y")

    colors = [C_RED if v < 0 else C_BLUE for v in delta_direct]
    ax2.bar(x, delta_direct, color=colors, alpha=0.9)
    ax2.axhline(0, color="#374151", lw=1.0)
    ax2.set_xticks(x, benches, fontsize=8)
    ax2.set_ylabel("Δ c_prop − direct (pts)")
    ax2.set_title("A1-bis vs adapted direct path")
    ax2.grid(alpha=0.25, axis="y")
    for i, v in enumerate(delta_direct):
        ax2.text(i, v + (1.5 if v >= 0 else -4), f"{v:+.1f}", ha="center", fontsize=8)

    fig.tight_layout()
    save(fig, "fig06-a1bis")


# ---------------------------------------------------------------------------
# Figure 7 — timeline
# ---------------------------------------------------------------------------
def fig07_timeline():
    fig, ax = new_canvas(13.0, 7.2)
    title(ax, "Project timeline — 24–26 September 2026 (~48 h of continuous work, 105 commits)")

    # lanes: (name, y, [(x, label), ...], color)
    lanes = [
        ("V1", 90, [(6, "P0 bootstrap 12:07"), (16, "P1 data 12:41"), (23, "pilot 13:03"),
                    (33, "B2 x3 seeds 15:05"), (50, "R/B3/B4 x3 seeds 20:19"),
                    (60, "gate P5 21:33"), (67, "closed 22:11")], C_ORANGE),
        ("V2-S", 76, [(72, "E0 23:43"), (77, "E1/E2 23:54"), (83, "E3/E4b 00:26")], C_PURPLE),
        ("V2-T", 62, [(74, "E5 prep 01:15"), (78, "bench defective"),
                      (84, "it1-it3 02:24-06:25"), (91, "E5v3-A LoRA"), (96, "closed 10:34")], C_BLUE),
        ("V2.1", 48, [(14, "protocol 11:40"), (34, "8 benches 2205-2212"), (52, "QA recalc 13:53"),
                      (66, "depth reversal")], C_GREEN),
        ("V2.2", 34, [(70, "protocol 14:03"), (74, "A1 FAIL"), (78, "A1-bis PASS"),
                      (83, "A2 PASS 16:32"), (88, "A3 8/8"), (93, "closed 19:06")], C_RED),
        ("Audit #3 + C0/C1", 20, [(78, "audit 19:25"), (84, "C0 errata"),
                                  (88, "C1 attribution 21:39"), (93, "release manifest")], "#6A4FA3"),
        ("C2 (night)", 6, [(80, "protocol 22:20"), (86, "6 trainings overnight"),
                           (93, "C2 closed 10:23"), (97, "QA REG-86 10:37")], "#2E8B57"),
    ]
    for name, y, events, color in lanes:
        ax.plot([4, 98], [y, y], color=color, lw=2.4, alpha=0.65, zorder=1)
        ax.text(2.2, y, name, ha="right", va="center", fontsize=9, weight="bold", color=color)
        for i, (x, label) in enumerate(events):
            ax.plot([x], [y], "o", color=color, ms=6, zorder=3)
            above = (i % 2 == 0)
            ax.text(x, y + (1.9 if above else -1.9), label, ha="center",
                    va="bottom" if above else "top", fontsize=6.8, color="#374151")

    ax.text(50, 0.5, "time, 24/09 12:00 -> 26/09 10:37 (not to scale; lanes compressed)",
            ha="center", fontsize=7.6, color=C_GREY)
    save(fig, "fig07-timeline")


# ---------------------------------------------------------------------------
# Figure 8 — E5 reader progression
# ---------------------------------------------------------------------------
def fig08_reader():
    stages = ["it1\nfrozen", "it2\nfrozen", "it3\nfrozen", "E5v3-A\nLoRA"]
    entities = [0.9999, 0.9998, 0.9998, 1.0000]
    edges = [0.3967, 0.7028, 0.7252, 0.9278]
    solve = [0.0625, 0.2044, 0.2482, 0.7616]
    validity = [None, 0.5085, 0.620, 0.917]

    x = np.arange(len(stages))
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.plot(x, edges, "-o", color=C_BLUE, lw=2.2, ms=7, label="edge F1 (≥ 0.65)")
    ax.plot(x, solve, "-s", color=C_GREEN, lw=2.2, ms=7, label="solve all-in (≥ 0.35)")
    ax.plot(x, entities, "-^", color=C_PURPLE, lw=2.0, ms=6, label="entity F1 (≥ 0.85)")
    ax.plot(x, validity, "-d", color=C_ORANGE, lw=2.0, ms=6, label="graph validity (diagnostic)")
    ax.axhline(0.65, color=C_BLUE, ls=":", lw=1.1)
    ax.axhline(0.35, color=C_GREEN, ls=":", lw=1.1)
    ax.set_xticks(x, stages)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("score (dev n = 411)")
    ax.set_title("Reader progression: frozen iterations plateau, LoRA passes all gates")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8.5, loc="center right")
    fig.tight_layout()
    save(fig, "fig08-reader")


# ---------------------------------------------------------------------------
# Figure 9 — V2.2 final: A2 vs A3 vs direct vs discretisation
# ---------------------------------------------------------------------------
def fig09_v22_final():
    benches = ["B1\nshort", "B2\n6", "B3\n8", "B4\n10", "B5\nsurface", "B6\ndistract", "B7\noptions", "B8\nstart"]
    c_disc = [0.8000, 0.6675, 0.5975, 0.5600, 0.8100, 0.7725, 0.8000, 0.7650]
    a1bis = [0.8550, 0.8375, 0.8525, 0.8550, 0.8525, 0.8325, 0.8550, 0.8575]
    a2 = [0.9950, 0.9975, 0.9975, 0.9975, 1.0000, 1.0000, 0.9950, 0.9975]
    a3 = [0.9625, 0.4925, 0.2475, 0.2825, 0.9575, 0.9450, 0.9600, 0.8550]
    direct = [0.9375, 0.5250, 0.2800, 0.3075, 0.9400, 0.9375, 0.9400, 0.8400]
    d_a2_a3 = [3.25, 50.50, 75.00, 71.50, 4.25, 5.50, 3.50, 14.25]
    lo = [1.50, 45.50, 70.50, 66.75, 2.25, 3.49, 1.50, 10.75]
    hi = [5.25, 55.50, 79.01, 75.76, 6.25, 7.75, 5.50, 18.00]

    x = np.arange(len(benches))
    width = 0.2
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.2, 5.0), gridspec_kw={"width_ratios": [1.45, 1]})

    ax1.bar(x - 1.5 * width, c_disc, width, label="discretisation", color="#B8C4D0")
    ax1.bar(x - 0.5 * width, a1bis, width, label="A1-bis (0 training)", color=C_PURPLE, alpha=0.85)
    ax1.bar(x + 0.5 * width, a2, width, label="A2 (distributional)", color=C_GREEN)
    ax1.bar(x + 1.5 * width, a3, width, label="A3 (direct + equal aux.)", color=C_ORANGE)
    ax1.plot(x, direct, "k_", ms=14, mew=2, label="direct V2.1")
    ax1.set_xticks(x, benches, fontsize=8)
    ax1.set_ylim(0, 1.08)
    ax1.set_ylabel("accuracy (n=400/bench)")
    ax1.set_title("V2.2 final — 8 sealed benches: A2 0.995–1.000, depth-invariant")
    ax1.legend(fontsize=7.6, ncol=2, loc="lower left")
    ax1.grid(alpha=0.25, axis="y")

    err = [np.array(d_a2_a3) - np.array(lo), np.array(hi) - np.array(d_a2_a3)]
    ax2.bar(x, d_a2_a3, yerr=err, color=[C_RED if v > 20 else C_BLUE for v in d_a2_a3], capsize=4)
    ax2.set_xticks(x, benches, fontsize=8)
    ax2.set_ylabel("Δ(A2 − A3), pts")
    ax2.set_title("Architectural superiority: CI low > 0 on 8/8")
    ax2.grid(alpha=0.25, axis="y")
    for i, v in enumerate(d_a2_a3):
        ax2.text(i, hi[i] + 2.0, f"{v:+.2f}".rstrip("0").rstrip("."), ha="center", fontsize=8)

    fig.tight_layout()
    save(fig, "fig09-v22-final")


# ---------------------------------------------------------------------------
# Figure 10 — Confirmation programme: C1 attribution + C2 confirmation/blind
# ---------------------------------------------------------------------------
def fig10_confirmation():
    benches = ["B1\nshort", "B2\n6", "B3\n8", "B4\n10", "B5\nsurface", "B6\ndistract", "B7\noptions", "B8\nstart"]
    r0_hard = [0.8100, 0.6650, 0.5775, 0.5500, 0.8175, 0.8100, 0.8100, 0.7850]
    r0_soft = [0.8550, 0.8375, 0.8525, 0.8550, 0.8525, 0.8325, 0.8550, 0.8575]
    r1_hard = [0.8750, 0.7850, 0.8450, 0.8425, 0.8875, 0.8550, 0.8750, 0.8300]
    r1_soft = [0.9950, 0.9975, 0.9975, 0.9975, 1.0000, 1.0000, 0.9950, 0.9975]

    x = np.arange(len(benches))
    width = 0.2
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.4, 5.0), gridspec_kw={"width_ratios": [1.5, 1]})

    ax1.bar(x - 1.5 * width, r0_hard, width, label="R0 hard (frozen reader, discret.)", color="#B8C4D0")
    ax1.bar(x - 0.5 * width, r0_soft, width, label="R0 soft (propagation)", color=C_PURPLE, alpha=0.85)
    ax1.bar(x + 0.5 * width, r1_hard, width, label="R1 hard (A2 reader, discret.)", color=C_ORANGE, alpha=0.85)
    ax1.bar(x + 1.5 * width, r1_soft, width, label="R1 soft (A2 + propagation)", color=C_GREEN)
    ax1.set_xticks(x, benches, fontsize=8)
    ax1.set_ylim(0, 1.08)
    ax1.set_ylabel("accuracy (n=400/bench)")
    ax1.set_title("C1 same-reader 2×2: both factors contribute (soft > hard; R1 > R0)")
    ax1.legend(fontsize=7.4, ncol=2, loc="lower left")
    ax1.grid(alpha=0.25, axis="y")

    seeds = ["s17", "s18", "s19", "blind s20"]
    a2_deep = [0.9950, 0.9983, 0.9983, 0.9867]
    a3_deep = [0.3419, 0.3578, 0.3169, 0.2710]
    xs = np.arange(len(seeds))
    ax2.bar(xs - 0.19, a2_deep, 0.36, label="A2 (propagation)", color=C_GREEN)
    ax2.bar(xs + 0.19, a3_deep, 0.36, label="A3 (direct + equal aux.)", color=C_ORANGE)
    ax2.axhline(0.90, color=C_RED, ls="--", lw=1.3)
    ax2.text(3.45, 0.91, "blind criterion ≥ 0.90", fontsize=7.5, color=C_RED, ha="right")
    for i, (a, b) in enumerate(zip(a2_deep, a3_deep)):
        ax2.text(i, a + 0.015, f"{a:.4f}", ha="center", fontsize=7.6)
        ax2.text(i, b + 0.015, f"{b:.4f}", ha="center", fontsize=7.6)
        ax2.text(i, 0.50, f"Δ +{(a-b)*100:.1f}", ha="center", fontsize=8, weight="bold", color="#374151")
    ax2.set_xticks(xs, seeds, fontsize=8.5)
    ax2.set_ylim(0, 1.08)
    ax2.set_ylabel("pooled deep accuracy (6+8+10)")
    ax2.set_title("C2: 3-seed confirmation + blind extrapolation")
    ax2.legend(fontsize=8, loc="center left")
    ax2.grid(alpha=0.25, axis="y")

    fig.tight_layout()
    save(fig, "fig10-confirmation")


if __name__ == "__main__":
    fig01_v1_architecture()
    fig02_v2_executor()
    fig03_v2_pipeline()
    fig04_depth_curves()
    fig05_v1_main()
    fig06_a1bis()
    fig07_timeline()
    fig08_reader()
    fig09_v22_final()
    fig10_confirmation()
    print("all figures written to", OUT)
