"""
Population epoch selectivity analysis for Neuropixels social-memory data

INPUTS
------
activity : np.ndarray
    Shape = (n_neurons, n_timepoints)
    Z-scored firing rates or binned firing rates

time : np.ndarray
    Shape = (n_timepoints,)
    Time vector in seconds

epochs : dict
    Example:
    epochs = {
        "baseline": (0, 300),
        "E1_novel": (300, 700),
        "E2_familiar": (1300, 1700),
        "E3_familiar": (2300, 2700),
        "E4_familiar": (3300, 3700),
        "E5_novel": (4300, 4700)
    }

WHAT THIS SCRIPT DOES
---------------------
1. Computes mean activity per epoch
2. Performs one-way ANOVA per neuron
3. Computes permutation significance
4. Computes selectivity indices
5. Computes ROC AUC discrimination
6. Classifies neurons:
      - social-memory selective
      - familiar selective
      - novel selective
      - sustained responder
      - transient responder

"""

import numpy as np
import pandas as pd
from scipy.stats import f_oneway
from scipy.stats import zscore
from sklearn.metrics import roc_auc_score
from sklearn.utils import shuffle
import matplotlib.pyplot as plt
import os
import glob
from scipy.ndimage import gaussian_filter1d

# ============================================================
# LOAD DATA
# ============================================================

neuron_folder = r"C:\Users\YKassem\Documents\phy\M3_17122025_g0_waveforms\Neurons"
neuron_files = glob.glob(os.path.join(neuron_folder, "*.npy"))

bin_size = 1.0   # seconds

session_duration = 5000   # seconds
time_bins = np.arange(0, session_duration + bin_size, bin_size)

all_rates = []

for file in neuron_files:
    sp = np.load(file)

    if len(sp) == 0:
        continue

    sp_sec = sp / 1000

    counts, _ = np.histogram(sp_sec, bins=time_bins)
    firing_rate = counts / bin_size

    smoothed = gaussian_filter1d(firing_rate, sigma=1)

    # Match lengths
    if len(smoothed) < len(time_bins) - 1:
        smoothed = np.pad(
            smoothed,
            (0, (len(time_bins)-1) - len(smoothed))
        )

    elif len(smoothed) > len(time_bins) - 1:
        smoothed = smoothed[:len(time_bins)-1]

    all_rates.append(smoothed)

activity = np.array(all_rates)   # neurons x time

# z score each neuron
activity = (
    activity
    - activity.mean(axis=1, keepdims=True)
) / (
    activity.std(axis=1, keepdims=True) + 1e-10
)

# time vector
time = time_bins[:-1]

n_neurons, n_timepoints = activity.shape

print("Activity shape:", activity.shape)
print("Time vector shape:", time.shape)


epochs = {
    "baseline": (0, 300),
    "E1_novel": (350, 678),
    "E2_familiar": (1285, 1629),
    "E3_familiar": (2284, 2630),
    "E4_familiar": (3253, 3658),
    "E5_novel": (4278, 4710)
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_epoch_data(activity, time, start, end):
    idx = (time >= start) & (time < end)
    return activity[:, idx]

def permutation_test(groups, n_perm=1000):
    """
    Permutation ANOVA
    """
    observed = f_oneway(*groups).statistic

    combined = np.concatenate(groups)
    group_sizes = [len(g) for g in groups]

    perm_stats = []

    for _ in range(n_perm):

        shuffled = shuffle(combined)

        split_groups = []
        start = 0

        for size in group_sizes:
            split_groups.append(shuffled[start:start+size])
            start += size

        stat = f_oneway(*split_groups).statistic
        perm_stats.append(stat)

    perm_stats = np.array(perm_stats)

    p_perm = np.mean(perm_stats >= observed)

    return observed, p_perm

# ============================================================
# EXTRACT EPOCH MATRICES
# ============================================================

epoch_data = {}

for name, (start, end) in epochs.items():
    epoch_data[name] = get_epoch_data(activity, time, start, end)

# ============================================================
# COMPUTE MEAN ACTIVITY PER EPOCH
# ============================================================

mean_activity = pd.DataFrame(index=np.arange(n_neurons))

for epoch_name, data in epoch_data.items():
    mean_activity[epoch_name] = data.mean(axis=1)

print("\nMean activity per epoch:")
print(mean_activity.head())

# ============================================================
# ANOVA + PERMUTATION TEST
# ============================================================

anova_pvals = []
perm_pvals = []

epoch_names = list(epoch_data.keys())

for neuron in range(n_neurons):

    groups = []

    for ep in epoch_names:
        groups.append(epoch_data[ep][neuron])

    # One-way ANOVA
    F, p = f_oneway(*groups)

    # Permutation test
    _, p_perm = permutation_test(groups, n_perm=500)

    anova_pvals.append(p)
    perm_pvals.append(p_perm)

mean_activity["anova_p"] = anova_pvals
mean_activity["perm_p"] = perm_pvals

# ============================================================
# SELECTIVITY INDICES
# ============================================================

# Novel vs Familiar

novel_epochs = ["E1_novel", "E5_novel"]
familiar_epochs = ["E2_familiar", "E3_familiar", "E4_familiar"]

novel_mean = mean_activity[novel_epochs].mean(axis=1)
familiar_mean = mean_activity[familiar_epochs].mean(axis=1)

# Selectivity index
# SI = (A - B) / (A + B)

selectivity_index = (
    (novel_mean - familiar_mean)
    /
    (np.abs(novel_mean) + np.abs(familiar_mean) + 1e-10)
)

mean_activity["selectivity_index"] = selectivity_index

# ============================================================
# ROC ANALYSIS
# ============================================================

roc_auc_values = []

for neuron in range(n_neurons):

    novel_values = []
    familiar_values = []

    for ep in novel_epochs:
        novel_values.extend(epoch_data[ep][neuron])

    for ep in familiar_epochs:
        familiar_values.extend(epoch_data[ep][neuron])

    y_true = np.concatenate([
        np.ones(len(novel_values)),
        np.zeros(len(familiar_values))
    ])

    y_score = np.concatenate([
        novel_values,
        familiar_values
    ])

    auc = roc_auc_score(y_true, y_score)

    roc_auc_values.append(auc)

mean_activity["roc_auc"] = roc_auc_values

# ============================================================
# CLASSIFICATION RULES
# ============================================================

classes = []

NOVEL_THRESHOLD = 0.5
FAMILIAR_THRESHOLD = 0.5

for neuron in range(n_neurons):

    p = mean_activity.loc[neuron, "perm_p"]
    si = mean_activity.loc[neuron, "selectivity_index"]

    # Mean responses
    e1 = mean_activity.loc[neuron, "E1_novel"]
    e5 = mean_activity.loc[neuron, "E5_novel"]

    e2 = mean_activity.loc[neuron, "E2_familiar"]
    e3 = mean_activity.loc[neuron, "E3_familiar"]
    e4 = mean_activity.loc[neuron, "E4_familiar"]

    # ----------------------------------------------------
    # NON-SELECTIVE
    # ----------------------------------------------------

    if p >= 0.05:
        classes.append("non_selective")
        continue

    # ----------------------------------------------------
    # NOVEL SELECTIVE
    # ----------------------------------------------------

    if si > 0.2:

        novel_active = [
            e1 > NOVEL_THRESHOLD,
            e5 > NOVEL_THRESHOLD
        ]

        n_novel_active = np.sum(novel_active)

        if n_novel_active == 2:
            label = "novel_selective_sustained"

        else:
            label = "novel_selective_transient"

    # ----------------------------------------------------
    # FAMILIAR SELECTIVE
    # ----------------------------------------------------

    elif si < -0.2:

        familiar_active = [
            e2 > FAMILIAR_THRESHOLD,
            e3 > FAMILIAR_THRESHOLD,
            e4 > FAMILIAR_THRESHOLD
        ]

        n_familiar_active = np.sum(familiar_active)

        if n_familiar_active >= 2:
            label = "familiar_selective_sustained"

        else:
            label = "familiar_selective_transient"

    # ----------------------------------------------------
    # GENERAL SOCIAL MEMORY
    # ----------------------------------------------------

    else:
        label = "social_memory_selective"

    classes.append(label)

mean_activity["classification"] = classes

# ============================================================
# SUMMARY
# ============================================================

print("\nNeuron classification summary:\n")

print(
    mean_activity["classification"]
    .value_counts()
)

# ============================================================
# EXAMPLE VISUALIZATION
# ============================================================

plt.figure(figsize=(8, 5))

plt.hist(
    mean_activity["selectivity_index"],
    bins=30
)

plt.xlabel("Novel vs Familiar Selectivity Index")
plt.ylabel("Neuron count")
plt.title("Population selectivity distribution")

plt.show()

plt.figure(figsize=(6,5))

plt.hist(mean_activity["roc_auc"], bins=30)

plt.axvline(0.5, linestyle="--")

plt.xlabel("ROC AUC")
plt.ylabel("Neuron count")
plt.title("Novel vs Familiar ROC AUC")

plt.show()

plt.figure(figsize=(6,6))

plt.scatter(
    mean_activity["selectivity_index"],
    mean_activity["roc_auc"],
    alpha=0.7
)

plt.axvline(0, linestyle="--")
plt.axhline(0.5, linestyle="--")

plt.xlabel("Selectivity Index")
plt.ylabel("ROC AUC")
plt.title("Neuron selectivity vs discriminability")

plt.show()

# ============================================================
# SAVE RESULTS
# ============================================================

mean_activity.to_csv("neuron_epoch_selectivity_results.csv")

print("\nSaved:")
print("neuron_epoch_selectivity_results.csv")