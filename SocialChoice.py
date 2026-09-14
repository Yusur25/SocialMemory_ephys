import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import re

basepath = Path(r'Z:\Yusur\SocialChoice')

# # Your desired x-axis labels
# x_labels = ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6 (reduce reward probability in C)", "Day 7 (animals separated for a week)", "Day 8 (no FR)"]

fig, axes = plt.subplots(3, 1, figsize=(12, 12), sharex=True)

ax_choice = axes[0]
ax_rt = axes[1]
ax_rt_initial = axes[2]

# Store data for each animal
animal_data = {
    "C1": [],
    "C2": []
}

full_rt_data = {"C1": [], "C2": []}
full_rt_initial_data = {"C1": [], "C2": []}

processed_groups = set()
# Loop through folders like C1_2026-05-20
for folder in sorted(basepath.iterdir()):

    # Skip anything that isn't a directory
    if not folder.is_dir():
        continue

    # Optional: only keep folders matching pattern
    # e.g. starts with A and contains underscore
    if "_" not in folder.name or "C" not in folder.name:
        continue

    # Path to trials.csv inside folder
    csv_file = folder / "trials.csv"

    # Skip if file doesn't exist
    if not csv_file.exists():
        print(f"Missing: {csv_file}")
        continue

    parts = folder.name.split("_")

    animal = parts[0]  # C1
    date = parts[-1]  # 2026-05-20

    animal_date = f"{animal}_{date}"

    if animal_date in processed_groups:
        continue

    processed_groups.add(animal_date)

    matching_folders = [
        f for f in basepath.iterdir()
        if f.is_dir()
           and f.name.startswith(animal)
           and f.name.endswith(date)
    ]

    # Combine all matching trials.csv files
    dfs = []

    for f in matching_folders:

        f_csv = f / "trials.csv"

        if f_csv.exists():
            dfs.append(pd.read_csv(f_csv))

    # Merge into one dataframe
    df = pd.concat(dfs, ignore_index=True)

    # Skip if neither A nor B exists in port column
    if "port" not in df.columns or not df["port"].isin(["A", "B"]).any():
        print(f"Skipping {csv_file} (no port A or B)")
        continue

    # Clean data
    df = df.dropna(subset=["port"])

    # Keep only needed columns and clean
    df["rt"] = pd.to_numeric(df["rt"], errors="coerce")
    df["rt_initial"] = pd.to_numeric(df["rt_initial"], errors="coerce")

    # Remove extreme RTs above 10 s
    df.loc[df["rt"] > 10, "rt"] = pd.NA

    df = df.sort_values("trial_num")

    animal = folder.name.split("_")[0]

    # split by choice c
    rt_A = df.loc[df["port"] == "A", "rt"]
    rt_B = df.loc[df["port"] == "B", "rt"]

    rt_init_A = df.loc[df["port"] == "A", "rt_initial"]
    rt_init_B = df.loc[df["port"] == "B", "rt_initial"]

    # store
    full_rt_data.setdefault(animal + "_A", []).extend(rt_A.dropna().tolist())
    full_rt_data.setdefault(animal + "_B", []).extend(rt_B.dropna().tolist())

    full_rt_initial_data.setdefault(animal + "_A", []).extend(rt_init_A.dropna().tolist())
    full_rt_initial_data.setdefault(animal + "_B", []).extend(rt_init_B.dropna().tolist())

    # Determine animal (C1 or C2)
    animal = folder.name.split("_")[0]

    # # Calculate % B choices
    # percent_B = (df["port"] == "B").mean() * 100
    #
    # # Store result
    # animal_data[animal].append(percent_B)

    df["port_B"] = (df["port"] == "B").astype(int)

    animal_data[animal].extend(df["port_B"].tolist())

# compute rolling means

window = 20  # adjust (10–50 usually works well)

rolling_rt = {}
rolling_rt_initial = {}
rolling_choice = {}

for animal in ["C1", "C2"]:

    choice_series = pd.Series(animal_data[animal]).dropna()
    rolling_choice[animal] = (
            choice_series.rolling(window, min_periods=1).mean() * 100
    )

for key in ["C1_A", "C1_B", "C2_A", "C2_B"]:

    rt_series = pd.Series(full_rt_data.get(key, [])).dropna()
    rt_init_series = pd.Series(full_rt_initial_data.get(key, [])).dropna()

    rolling_rt[key] = rt_series.rolling(window, min_periods=1).median()
    rolling_rt_initial[key] = rt_init_series.rolling(window, min_periods=1).median()

# # Plot each animal
# for animal, values in animal_data.items():

    # ax_choice.plot(
    #     x_labels[:len(values)],
    #     values,
    #     marker="o",
    #     linestyle="-",
    #     label=animal,
    #     alpha=0.9
    # )


for animal in ["C1", "C2"]:
    ax_choice.plot(
        rolling_choice[animal].values,
        label=f"{animal} choice",
        alpha=0.9
    )

    ax_rt.plot(
        rolling_rt[f"{animal}_A"].values,
        label=f"{animal} RT A",
        alpha=0.9
    )

    ax_rt.plot(
        rolling_rt[f"{animal}_B"].values,
        label=f"{animal} RT B",
        alpha=0.9
    )

    ax_rt_initial.plot(
        rolling_rt_initial[f"{animal}_A"].values,
        label=f"{animal} RT initial A",
        alpha=0.9
    )

    ax_rt_initial.plot(
        rolling_rt_initial[f"{animal}_B"].values,
        label=f"{animal} RT initial B",
        alpha=0.9
    )

ax_choice.set_ylabel("Port B %")
ax_choice.set_title("Social Choice %")
ax_choice.legend()
ax_choice.grid(True, axis="y", alpha=0.3)

ax_rt.set_ylabel("RT")
ax_rt.set_title("Poke Reaction Time")
ax_rt.grid(True, axis="y", alpha=0.3)
ax_rt.legend()

ax_rt_initial.set_ylabel("RT Initial")
ax_rt_initial.set_title("Port A/B Reaction Time")
ax_rt_initial.set_xlabel("Trials (pooled across sessions)")
ax_rt_initial.grid(True, axis="y", alpha=0.3)
ax_rt_initial.legend()

plt.xticks(rotation=20)
plt.tight_layout()
plt.show()

