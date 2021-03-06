from common import read_table_lengths
from matplotlib import pyplot as plt
import numpy as np
import seaborn as sns


nets = ("gaussian", "centroid")
net_titles = ("Locally-connected", "Centroid")


def plot_wide(datasets, axs, n_highlighted=0):
    axs[0].spines['left'].set_position(('outward', 5))
    axs[0].set_ylabel("Table size")
    axs[1].spines['left'].set_color('none')

    y_min = 2000
    y_max = 0

    for model, ax, title in zip(nets, axs, net_titles):
        ax.set_title(title)
        ax.grid(False)
        ax.hlines(1024, -.5, len(datasets) * 2 + 1.5, linewidth=.5, colors=[(.5, )*3], zorder=0)
        ax.spines['top'].set_color('none')
        ax.spines['right'].set_color('none')
        ax.spines['bottom'].set_color('none')

        data = np.zeros((len(datasets), 144))

        # Read all the data
        for i, (_, fn) in enumerate(datasets):
            fn = "{}{}_12_12_xyp.bin".format(fn, model)
            with open(fn, "rb") as f:
                data[i, :] = np.array(list(read_table_lengths(f).values()))

        xs = np.arange(len(datasets))*2
        elems = ax.violinplot(data.T, xs, showextrema=False)
        for b in elems["bodies"][:-n_highlighted]:
            b.set_alpha(.3)
            b.set_facecolor((.85, .85, .85))
            b.set_edgecolor((0, 0, 0))
            b.set_linewidth(1)

        # The last 2 elements should be slightly highlighted
        for b in elems["bodies"][-n_highlighted:]:
            b.set_alpha(.8)
            b.set_facecolor((.85, .85, .85))
            b.set_edgecolor((0, 0, 0))
            b.set_linewidth(1)

        y_min = min(y_min, np.min(data))
        y_max = max(y_max, np.max(data))

        ax.set_xlim(-.5, max(xs) + .5)

        titles = (t for t, _ in datasets)
        ax.set_xticks(xs)
        ax.set_xticklabels(titles)

    axs[0].set_ylim(y_min, y_max)
    axs[0].set_yticks([y_min, 1024, y_max])


if __name__ == "__main__":
    sns.set(context="paper", style="whitegrid", font="Times New Roman")

    methods = ("esp_tables_no_offset", )
    method_titles = ("Espresso", )

    # Prepare the figures
    fig, axs = plt.subplots(1, 2, sharey=True, figsize=(3.5, 1.5))

    axs[0].spines['left'].set_position(('outward', 5))
    axs[0].set_ylabel("Table size")
    axs[1].spines['left'].set_color('none')

    y_min = 2000
    y_max = 0

    for model, ax, title in zip(nets, axs, net_titles):
        ax.set_title(title)
        ax.grid(False)
        ax.hlines(1024, -.5, 8.5, linewidth=.5, colors=[(.5, )*3], zorder=0)
        ax.spines['top'].set_color('none')
        ax.spines['right'].set_color('none')
        ax.spines['bottom'].set_color('none')

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

        elems = ax.violinplot(data.T, np.arange(len(methods) + 2)*2, showextrema=False)
        for b in elems["bodies"]:
            b.set_alpha(.75)
            b.set_facecolor((.85, .85, .85))
            b.set_edgecolor((0, 0, 0))
            b.set_linewidth(1)

        y_min = min(y_min, np.min(data))
        y_max = max(y_max, np.max(data))

        ax.set_xlim(-.5, (len(methods) + 1)*2 + .5)

        ax.set_xticks(np.arange(len(methods) + 2)*2)
        ax.set_xticklabels(("Original", "With default\nrouting") + method_titles)

    axs[0].set_ylim(y_min, y_max)
    axs[0].set_yticks([y_min, 1024, y_max])

    plt.tight_layout(pad=0)
    plt.savefig("results_no_dc.pdf")


if __name__ == "__main__":
    sns.set(context="paper", style="whitegrid", font="Times New Roman")

    methods = ("esp_tables_no_offset", "esp_subtables_full")
    method_titles = ("Espresso", "Order-\nexploiting\nEspresso")

    # Prepare the figures
    fig, axs = plt.subplots(1, 2, sharey=True, figsize=(3.5, 1.7))

    axs[0].spines['left'].set_position(('outward', 5))
    axs[0].set_ylabel("Table size")
    axs[1].spines['left'].set_color('none')

    y_min = 2000
    y_max = 0

    for model, ax, title in zip(nets, axs, net_titles):
        ax.set_title(title)
        ax.grid(False)
        ax.hlines(1024, -.5, 8.5, linewidth=.5, colors=[(.5, )*3], zorder=0)
        ax.spines['top'].set_color('none')
        ax.spines['right'].set_color('none')
        ax.spines['bottom'].set_color('none')

        data = np.zeros((len(methods) + 1, 144))

        # Read all the data
        fn = "uncompressed/{}_12_12_xyp.bin".format(model)
        with open(fn, "rb") as f:
            data[0, :] = np.array(list(read_table_lengths(f).values()))

        for j, method in enumerate(methods):
            fn = "compressed/{}_{}_12_12_xyp.bin".format(method, model)
            with open(fn, "rb") as f:
                data[j+1, :] = np.array(list(read_table_lengths(f).values()))

        elems = ax.violinplot(data.T, np.arange(len(methods) + 1)*2, showextrema=False)
        for b in elems["bodies"]:
            b.set_alpha(.75)
            b.set_facecolor((.85, .85, .85))
            b.set_edgecolor((0, 0, 0))
            b.set_linewidth(1)

        # The last element should be slightly highlighted to indicate that it is new
        b.set_linewidth(1.5)

        y_min = min(y_min, np.min(data))
        y_max = max(y_max, np.max(data))

        ax.set_xlim(-.5, len(methods)*2 + .5)

        ax.set_xticks(np.arange(len(methods) + 1)*2)
        ax.set_xticklabels(("Original", ) + method_titles)
        ax.get_xticklabels()[-1].set_fontweight(1000)

    axs[0].set_ylim(y_min, y_max)
    axs[0].set_yticks([y_min, 1024, y_max])

    plt.tight_layout(pad=0)
    plt.savefig("results_with_dc.pdf")


if __name__ == "__main__":
    sns.set(context="paper", style="whitegrid", font="Times New Roman")

    datasets = (("Original", "uncompressed/"),
                ("With default\nrouting", "compressed/remove_default_"),
                ("Espresso", "compressed/esp_tables_no_offset_"),
                ("Order-\nexploiting\nEspresso", "compressed/esp_subtables_full_"),
                ("m-Trie", "compressed/mtrie_"))

    # Prepare the figures
    fig, axs = plt.subplots(1, 2, sharey=True, figsize=(7, 1.75))

    plot_wide(datasets, axs, 2)

    plt.tight_layout(pad=0, w_pad=1.5)
    plt.savefig("results_with_esp_dc_and_mtrie.pdf")

    datasets += (("Ordered-\nCovering", "compressed/oc_spinnaker_"), )

    # Prepare the figures
    fig, axs = plt.subplots(1, 2, sharey=True, figsize=(7, 1.75))

    plot_wide(datasets, axs, 6)

    plt.tight_layout(pad=0, w_pad=1.5)
    plt.savefig("results_esp_and_oc.pdf")
