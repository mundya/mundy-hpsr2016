from common import read_table_lengths
from matplotlib import pyplot as plt
import numpy as np
import seaborn as sns


nets = ("gaussian", "centroid")

methods = ("esp_tables_no_offset", "esp_subtables_full", "oc_spinnaker")
method_titles = ("Espresso\nno DC set", "Espresso", "Ordered\nCovering")


if __name__ == "__main__":
    sns.set(context="paper", style="whitegrid", font="Times New Roman")

    # Prepare the figures
    for model in nets:
        fig, ax = plt.subplots(figsize=(3.5, 1.5))

        ax.grid(False)
        ax.hlines(1024, -.5, 8.5, linewidth=.5, colors=[(.5, )*3], zorder=0)
        ax.spines['top'].set_color('none')
        ax.spines['right'].set_color('none')
        ax.spines['bottom'].set_color('none')
        ax.spines['left'].set_position(('outward', 5))
        ax.set_ylabel("Table size")

        data = np.zeros((len(methods) + 2, 144))

        # Read all the data
        fn = "uncompressed/{}_12_12_xyp.bin".format(model)
        with open(fn, "rb") as f:
            data[0, :] = np.array(list(read_table_lengths(f).values()))

        fn = "compressed/remove_default_{}_12_12_xyp.bin".format(model)
        with open(fn, "rb") as f:
            data[1, :] = np.array(list(read_table_lengths(f).values()))

        for j, method in enumerate(methods):
            fn = "compressed/{}_{}_12_12_xyp.bin".format(method, model)
            with open(fn, "rb") as f:
                data[j+2, :] = np.array(list(read_table_lengths(f).values()))

        elems = ax.violinplot(data.T, np.arange(5)*2, showextrema=False)
        for b in elems["bodies"]:
            b.set_alpha(.75)
            b.set_facecolor((.85, .85, .85))
            b.set_edgecolor((0, 0, 0))
            b.set_linewidth(1)

        y_min = np.min(data)
        y_max = np.max(data)
        ax.set_ylim(y_min, y_max)
        ax.set_yticks([y_min, 1024, y_max])

        ax.set_xlim(-.5, 8.5)

        ax.set_xticks(np.arange(5)*2)
        ax.set_xticklabels(("Original", "With default\nrouting") + method_titles)

        plt.tight_layout(pad=0)
        plt.savefig("results_{}.pdf".format(model))
