import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import re
from brokenaxes import brokenaxes

def compress_time(t, excluded):

    shift = 0

    for start, end in excluded:

        if t >= end:
            shift += end - start

        elif start <= t < end:
            shift += t - start
            break

    return t - shift

basepath = Path(r'Z:\Yusur\SocialMemory_May')


for folder in basepath.iterdir():

    if not folder.is_dir():
        continue

    if not re.search(r"2026-05-(22)$", folder.name):
        continue

    if "_" not in folder.name:
        continue

    csv_file = folder / "table_events.csv"
    sensor_file = folder / "sensor_events.csv"

    if not csv_file.exists():
        continue

    df = pd.read_csv(csv_file, header=None)
    sensor = pd.read_csv(sensor_file, header=None)

    # ---------------------------
    # EXCLUDED PERIODS (door closed → open)
    # ---------------------------
    door_events = sensor[sensor[3].isin(["door opened", "door closed"])].sort_values(1)

    excluded = []
    close_time = None

    for _, row in door_events.iterrows():
        t = row[1]
        event = row[3]

        if event == "door closed":
            close_time = t

        elif event == "door opened" and close_time is not None:
            excluded.append((close_time, t))
            close_time = None

    # # --- cumulative sampling ---
    # x = [df[0].iloc[0]]
    # y = [0]
    #
    # cum = 0
    #
    # for _, row in df.iterrows():
    #     start_time = row[0]
    #     end_time = row[1]
    #
    #     x.append(start_time)
    #     y.append(cum)
    #
    #     cum += end_time - start_time
    #
    #     x.append(end_time)
    #     y.append(cum)
    # x_real = []
    x_comp = []
    y = []

    cum = 0

    # x_real.append(df[0].iloc[0])
    # x_comp.append(compress_time(df[0].iloc[0], excluded))
    # y.append(0)

    for _, row in df.iterrows():
        start = row[0]
        end = row[1]

        x_comp.append(compress_time(start, excluded))
        y.append(cum)

        cum += end - start

        x_comp.append(compress_time(end, excluded))
        y.append(cum)

 # --- NEW FIGURE PER ANIMAL ---
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.step(x_comp, y, where="post", label="compressed time")
    ax.set_xlabel("Compressed Time (s) excluding conditoning")
    ax.set_ylabel("Cumulative Sampling Time (s)")
    ax.set_title(f"Cumulative Sampling – {folder.name}")
    ax.grid(True, axis="y", alpha=0.3)

    for start, end in excluded:
        ax.axvspan(
            compress_time(start, excluded),
            compress_time(end, excluded),
            color="grey",
            alpha=0.2
        )

        ax.axvline(compress_time(start, excluded), color="red", linestyle="--", alpha=0.4)
        ax.axvline(compress_time(end, excluded), color="green", linestyle="--", alpha=0.4)

    # # shade excluded periods
    # for start, end in excluded:
    #     plt.axvline(first_open, color="green", linestyle="--", alpha=0.6, label="first door open")
    #     plt.axvspan(start, end, color="grey", alpha=0.2)
    #     plt.axvline(start, color="red", linestyle="--", alpha=0.4)
    #     plt.axvline(end, color="green", linestyle="--", alpha=0.4)

    # plt.xlabel("Time (s)")
    # plt.ylabel("Cumulative Sampling Time (s)")
    # plt.title(f"Cumulative Sampling – {folder.name}")
    # plt.grid(True, axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(folder / f"{folder.name}_cumulative_sampling.png", dpi=300)
    plt.show()



#     # build x-limits (same per dataset)
#     session_end = max(df[1].max(), sensor[1].max())
#
#     current = 0
#     segments = []
#
#     for start, end in excluded:
#         segments.append((current, start))
#         current = end
#
#     segments.append((current, session_end))
#
#     all_xlims.append(segments)
#
#     flat_segments = [seg for session in all_xlims for seg in session]
#
# # --- plot AFTER loop ---
# bax = brokenaxes(xlims=flat_segments, hspace=.05)
#
# for x, y, name, excluded in all_data:
#     bax.step(x, y, where="post", label=name)
#
#     for start, end in excluded:
#         bax.axvline(start, color="red", linestyle="--", alpha=0.4)
#         bax.axvline(end, color="green", linestyle="--", alpha=0.4)
#
# bax.set_xlabel("Time (s)")
# bax.set_ylabel("Cumulative Sampling Time (s)")
# bax.set_title("Cumulative Sampling Across Sessions")

# plt.legend()
# plt.tight_layout()
# plt.show()
