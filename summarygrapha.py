import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import re

basepath = Path(r'Z:\Yusur\SocialMemory_May')

# Your desired x-axis labels
x_labels = ["C1.1", "C1.2", "C1.3", "C1.4", "C2"]

plt.figure(figsize=(12, 6))

# Loop through folders like A1_2026-05-20
for folder in basepath.iterdir():

    # Skip anything that isn't a directory
    if not folder.is_dir():
        continue

    # Only allow folders ending in 2026-05-21 or 2026-05-22
    if not re.search(r"2026-05-(21|22)$", folder.name):
        continue

    # Optional: only keep folders matching pattern
    # e.g. starts with A and contains underscore
    if "_" and "C" not in folder.name:
        continue

    # Path to trials.csv inside folder
    csv_file = folder / "trials.csv"

    # Skip if file doesn't exist
    if not csv_file.exists():
        print(f"Missing: {csv_file}")
        continue

    # Load CSV
    df = pd.read_csv(csv_file)

    # Skip if sampling_time column is missing
    if "sampling_time" not in df.columns:
        print(f"Skipping {csv_file} (no sampling_time column)")
        continue

    # Clean data
    df = df.dropna(subset=["sampling_time"])
    df["sampling_time"] = pd.to_numeric(df["sampling_time"])

    # Sort by trial number
    df = df.sort_values("trial_num")

    # Plot
    plt.plot(
        x_labels,
        df["sampling_time"],
        marker="o",
        linestyle="-",
        label=folder.name,   # uses folder name as legend
        alpha=0.9
    )

plt.xlabel("Condition")
plt.ylabel("Sampling Time (s)")
plt.title("Sampling Time Across Conditions")
plt.legend()
plt.grid(True, axis="y", alpha=0.3)

plt.tight_layout()
plt.show()

