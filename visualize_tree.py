import json
import glob
import os
import matplotlib.pyplot as plt

# 1. Automatically find your latest Gemini log file
log_files = glob.glob("logs/game24/gemini-*.json")
if not log_files:
    log_files = glob.glob("logs/game24/*.json")
latest_log = max(log_files, key=os.path.getmtime)
print(f"Visualizing: {latest_log}")

with open(latest_log, "r") as f:
    data = json.load(f)

run = data[0]
steps = run["steps"]
problem = steps[0]["x"]

# 2. Set up the figure
fig, ax = plt.subplots(figsize=(14, 8))
ax.axis("off")
ax.set_title(f"Tree of Thoughts Search Diagram\nInput: [{problem}]", fontsize=14, fontweight="bold", pad=20)

# Draw Root Node
root_x, root_y = 0.5, 0.92
ax.text(root_x, root_y, f"START\n{problem}", ha="center", va="center", fontsize=10, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#D0E8FF", edgecolor="#2B6CB0", linewidth=2))

prev_nodes = [(root_x, root_y)]

# 3. Plot each BFS step and color-code by evaluation value
for step_idx, step in enumerate(steps):
    candidates = step.get("new_ys", [])
    values = step.get("values", [])
    if not candidates:
        continue

    y = 0.92 - (step_idx + 1) * 0.22
    num_cands = len(candidates)
    xs = [(i + 1) / (num_cands + 1) for i in range(num_cands)]
    next_nodes = []

    for i, (cand, x) in enumerate(zip(candidates, xs)):
        val = values[i] if i < len(values) else 0
        # Clean text to show only the latest thought line
        lines = [line.strip() for line in cand.strip().split("\n") if "Possible next steps" not in line and line.strip()]
        label = lines[-1] if lines else cand.strip()[:30]
        if len(label) > 35:
            label = label[:32] + "..."

        # Color code: Green = High/Sure, Yellow = Medium/Likely, Red = Pruned/Impossible
        if val >= 20:
            color, edge, status = "#C6F6D5", "#2F855A", "SURE"
        elif val >= 1.0:
            color, edge, status = "#FEFCBF", "#B7791F", "LIKELY"
        else:
            color, edge, status = "#FED7D7", "#C53030", "PRUNED"

        # Connect from parent node
        parent_x, parent_y = prev_nodes[min(i // max(1, (num_cands // len(prev_nodes))), len(prev_nodes) - 1)]
        ax.plot([parent_x, x], [parent_y - 0.04, y + 0.04], color="#A0AEC0", linestyle="-", linewidth=1.2, zorder=1)

        # Draw thought node
        ax.text(x, y, f"{label}\n[{status}: {val}]", ha="center", va="center", fontsize=8.5,
                bbox=dict(boxstyle="round,pad=0.4", facecolor=color, edgecolor=edge, linewidth=1.5), zorder=2)

        if val >= 1.0:
            next_nodes.append((x, y))

    if next_nodes:
        prev_nodes = next_nodes

# Add Legend
legend_text = "Color Key:   Green = Sure (Kept)   |   Yellow = Likely (Kept)   |   Red = Impossible (Pruned)"
ax.text(0.5, 0.03, legend_text, ha="center", va="center", fontsize=9.5,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#EDF2F7", edgecolor="#CBD5E0"))

plt.tight_layout()
output_img = "tot_search_tree.png"
plt.savefig(output_img, dpi=300, bbox_inches="tight")
print(f"Saved diagram to {output_img}!")
plt.show()
