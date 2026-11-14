import json
import glob
import os
import matplotlib.pyplot as plt

# 1. Locate your latest Baseline (bfs) and Improved (adaptive) log files
bfs_files = glob.glob("logs/game24/*_bfs_*.json")
ada_files = glob.glob("logs/game24/*_adaptive_*.json")

if not bfs_files or not ada_files:
    all_gemini = sorted(glob.glob("logs/game24/gemini-*.json"), key=os.path.getmtime)
    bfs_log, ada_log = all_gemini[-2], all_gemini[-1]
else:
    bfs_log = max(bfs_files, key=os.path.getmtime)
    ada_log = max(ada_files, key=os.path.getmtime)

print(f"Baseline Log: {bfs_log}")
print(f"Improved Log: {ada_log}")

with open(bfs_log) as f:
    bfs_data = json.load(f)[0]
with open(ada_log) as f:
    ada_data = json.load(f)[0]

def plot_tree_on_ax(ax, run_data, title):
    steps = run_data["steps"]
    problem = steps[0]["x"]
    ax.axis("off")
    ax.set_title(f"{title}\nInput: [{problem}] | Steps Explored: {len(steps)}", fontsize=11, fontweight="bold", pad=12)

    root_x, root_y = 0.5, 0.92
    ax.text(root_x, root_y, f"START\n{problem}", ha="center", va="center", fontsize=9, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#D0E8FF", edgecolor="#2B6CB0", linewidth=1.8))
    prev_nodes = [(root_x, root_y)]

    total_nodes = 0
    for step_idx, step in enumerate(steps):
        candidates = step.get("new_ys", [])
        values = step.get("values", [])
        if not candidates:
            continue
        total_nodes += len(candidates)
        y = 0.92 - (step_idx + 1) * 0.22
        xs = [(i + 1) / (len(candidates) + 1) for i in range(len(candidates))]
        next_nodes = []

        for i, (cand, x) in enumerate(zip(candidates, xs)):
            val = values[i] if i < len(values) else 0
            lines = [l.strip() for l in cand.strip().split("\n") if "Possible next steps" not in l and l.strip()]
            label = (lines[-1] if lines else cand.strip())[:24]

            if val >= 20:
                color, edge, tag = "#C6F6D5", "#2F855A", "SURE"
            elif val >= 1.0:
                color, edge, tag = "#FEFCBF", "#B7791F", "KEPT"
            else:
                color, edge, tag = "#FED7D7", "#C53030", "PRUNED"

            px, py = prev_nodes[min(i // max(1, (len(candidates) // len(prev_nodes))), len(prev_nodes) - 1)]
            ax.plot([px, x], [py - 0.04, y + 0.04], color="#A0AEC0", linewidth=1.1, zorder=1)
            ax.text(x, y, f"{label}\n[{tag}: {val}]", ha="center", va="center", fontsize=7.5,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor=color, edgecolor=edge, linewidth=1.3), zorder=2)

            if val >= 1.0:
                next_nodes.append((x, y))
        if next_nodes:
            prev_nodes = next_nodes
    return total_nodes, len(steps)

# --- FIGURE 1: Side-by-Side Search Tree Comparison ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
bfs_nodes, bfs_steps = plot_tree_on_ax(ax1, bfs_data, "Original Paper: Fixed-Width BFS")
ada_nodes, ada_steps = plot_tree_on_ax(ax2, ada_data, "Our Method: Adaptive Beam + Early Exit")

fig.suptitle("Comparison of Search Tree Exploration & Pruning", fontsize=14, fontweight="bold")
plt.figtext(0.5, 0.02, "Green = Sure (High Confidence)   |   Yellow = Kept Branch   |   Red = Pruned Dead End",
            ha="center", fontsize=9.5, bbox=dict(boxstyle="round,pad=0.4", facecolor="#EDF2F7", edgecolor="#CBD5E0"))
plt.tight_layout(rect=[0, 0.05, 1, 0.94])
plt.savefig("tree_comparison.png", dpi=300)
print("Saved Figure 1: tree_comparison.png")

# --- FIGURE 2: Quantitative Efficiency Bar Chart ---
bfs_usage = bfs_data.get("usage_so_far", {})
ada_usage = ada_data.get("usage_so_far", {})
bfs_tokens = bfs_usage.get("prompt_tokens", 0) + bfs_usage.get("completion_tokens", 0)
ada_tokens = ada_usage.get("prompt_tokens", 0) + ada_usage.get("completion_tokens", 0)

fig2, (bx1, bx2) = plt.subplots(1, 2, figsize=(10, 4.5))
methods = ["Original ToT\n(Fixed BFS)", "Improved ToT\n(Adaptive + Early Exit)"]
colors = ["#718096", "#3182CE"]

bx1.bar(methods, [bfs_nodes, ada_nodes], color=colors, width=0.5)
bx1.set_title("Candidate Nodes Evaluated", fontweight="bold")
bx1.set_ylabel("Number of Thought Nodes")
for idx, val in enumerate([bfs_nodes, ada_nodes]):
    bx1.text(idx, val + 0.2, str(val), ha="center", fontweight="bold")

bx2.bar(methods, [bfs_tokens, ada_tokens], color=colors, width=0.5)
bx2.set_title("Total LLM Tokens Consumed", fontweight="bold")
bx2.set_ylabel("Tokens (Prompt + Completion)")
for idx, val in enumerate([bfs_tokens, ada_tokens]):
    bx2.text(idx, val + max(bfs_tokens, ada_tokens, 1) * 0.02, str(val), ha="center", fontweight="bold")

fig2.suptitle("Efficiency Gains: Original Baseline vs. Adaptive ToT", fontsize=13, fontweight="bold")
plt.tight_layout(rect=[0, 0, 1, 0.92])
plt.savefig("efficiency_chart.png", dpi=300)
print("Saved Figure 2: efficiency_chart.png")
plt.show()
