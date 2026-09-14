import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import pearsonr

# ==========================================
# LOAD FILES
# ==========================================

# social neuron metrics file
social_file = r"C:\Users\YKassem\Documents\kilosort_for_phy\M5_19122025_waveforms\Neurons\epoch_firing_rates.csv"

# conditioning metrics file
conditioning_file = r"C:\Users\YKassem\Documents\kilosort_for_phy\M5_19122025_waveforms\Neurons\PSTHs\neuron_LED_response_classification.csv"

social_df = pd.read_csv(social_file)
cond_df = pd.read_csv(conditioning_file)

social_df["Neuron"] = social_df["Neuron"].str.replace(".npy", "", regex=False)
cond_df["Neuron"] = cond_df["Neuron"].str.replace(".npy", "", regex=False)

# ==========================================
# MERGE ON NEURON NAME
# ==========================================

# assumes both files contain a column called "Neuron"

df = pd.merge(
    social_df,
    cond_df,
    on="Neuron",
    how="inner"
)

# -----------------------------
# TOP PLOT
# Social vs Cue/Conditioning
# -----------------------------

x1 = df["SocialDelta"]
y1 = df["Delta"]

r1, p1 = pearsonr(x1, y1)

# -----------------------------
# BOTTOM PLOT
# Social vs LED OFF response
# -----------------------------

x2 = df["SocialDelta"]
y2 = df["off_post_mean"]


r2, p2 = pearsonr(x2, y2)

# ==========================================
# COLOR BY SOCIAL CLASS
# ==========================================

colors = []

for label in df["SocialClass"]:

    if label == "Social+":
        colors.append("red")

    elif label == "Social-":
        colors.append("blue")

    else:
        colors.append("gray")

# =============================
# FIGURE
# =============================

fig, (ax1, ax2) = plt.subplots(
    2, 1,
    figsize=(6, 8)
)

# =====================================
# TOP: SOCIAL vs CONDITIONING
# =====================================

ax1.scatter(x1, y1)

# regression line
m1, b1 = np.polyfit(x1, y1, 1)
ax1.plot(x1, m1*x1 + b1)

ax1.axhline(0, linestyle='--')
ax1.axvline(0, linestyle='--')

ax1.set_xlabel("Mean social response (z-score)")
ax1.set_ylabel("Mean cue-evoked response (z-score)")

ax1.set_title(
    f"Social vs Conditioning Responses\n"
    f"r = {r1:.3f}, p = {p1:.5f}"
)

# =====================================
# BOTTOM: SOCIAL vs POST-LED RESPONSE
# =====================================

ax2.scatter(x2, y2)

# regression line
m2, b2 = np.polyfit(x2, y2, 1)
ax2.plot(x2, m2*x2 + b2)

ax2.axhline(0, linestyle='--')
ax2.axvline(0, linestyle='--')

ax2.set_xlabel("Mean social response (z-score)")
ax2.set_ylabel("Mean post-LED response (z-score)")

ax2.set_title(
    f"Social vs Post-LED Responses\n"
    f"r = {r2:.3f}, p = {p2:.5f}"
)

plt.tight_layout()
plt.show()