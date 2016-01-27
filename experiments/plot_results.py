from common import read_table_lengths
from matplotlib import pyplot as plt
import numpy as np
import seaborn as sns


types = ("xyp", "xyzp", "hilbert")
methods = ("esp_tables_no_offset", "esp_subtables_full", "oc", "pyoc")


if __name__ == "__main__":
    sns.set(style="whitegrid", font="Times New Roman")

    # Prepare the figures
    fig, (ax0, ax1) = plt.subplots(2, sharex=True)

    # Label the x-axis now
    xlabels = ["Original", "Remove Default Entries"]

    for model, ax in (("gaussian", ax0), ("centroid", ax1)):
        ax.grid(False)

        max_x = 2.5 + len(types)*len(methods) + .25
        ax.set_xlim(-0.25, max_x)
        ax.set_ylim(800, 1200)
        ax.hlines(1024, -.25, max_x, linewidth=1, colors=[(.75, )*3])

        with open("uncompressed/{}_12_12_xyp.bin".format(model), "rb") as f:
            data = np.array(list(read_table_lengths(f).values()))
            ax.violinplot(data, positions=[0], showextrema=False)

        with open("compressed/remove_default_{}_12_12_xyp.bin".format(model), "rb") as f:
            data = np.array(list(read_table_lengths(f).values()))
            ax.violinplot(data, positions=[1], showextrema=False)

        for i, t in enumerate(types):
            for j, method in enumerate(methods):
                try:
                    fn = "compressed/{}_{}_12_12_{}.bin".format(method, model, t)
                    pos = [2.5 + i*(len(methods) + .5) + j]
                    with open(fn, "rb") as f:
                        data = np.array(list(read_table_lengths(f).values()))
                        ax.violinplot(data, positions=pos, showextrema=False)
                except FileNotFoundError:
                    pass

    for ax in (ax0, ax1):
        ax.spines['top'].set_color('none')
        ax.spines['right'].set_color('none')
        ax.spines['left'].set_position(('outward', 10))

    ax0.spines['bottom'].set_color('none')
    ax1.spines['bottom'].set_position(('outward', 10))

    plt.show()
