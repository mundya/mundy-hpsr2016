import collections
from common import read_table_lengths
import matplotlib
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import seaborn as sns

sns.set(style="white", context="paper")
matplotlib.rc("font", family="sans-serif")

nets_titles = [("gaussian", "Locally-connected"),
               ("centroid", "Centroid")]
methods_titles = [("remove_default", "Default\nRouting"),
                  ("esp_tables_no_offset", "Espresso"),
                  ("esp_subtables_full", "Order-\nexploiting\nEspresso"),
                  ("mtrie", "m-Trie"),
                  ("oc_spinnaker", "Ordered\nCovering")]

# Construct the data to go with the titles
max_ys = dict()
min_ys = dict()
datasets = collections.defaultdict(dict)
for model, _ in nets_titles:
    # Load the original
    data = np.zeros(144, dtype=np.int)
    with open("uncompressed/{}_12_12_xyp.bin".format(model), "rb") as fp:
        data[:] = list(read_table_lengths(fp).values())

    # Update the sizes
    max_ys[model] = np.max(data)
    min_ys[model] = np.min(data)

    # Store the result
    datasets[model]["original"] = data

    # Load the results
    for method, _ in methods_titles:
        # Load the routing table lengths
        data = np.zeros(144, dtype=np.int)
        with open("compressed/{}_{}_12_12_xyp.bin".format(method, model),
                  "rb") as fp:
            data[:] = list(read_table_lengths(fp).values())

        # Update the sizes
        min_ys[model] = min(min_ys[model], np.min(data))

        # Store the result
        datasets[model][method] = data

# Round the mins and maxs
for k in max_ys:
    max_ys[k] //= 10
    max_ys[k] += 1
    max_ys[k] *= 10

for k in min_ys:
    min_ys[k] //= 10
    min_ys[k] *= 10

# Do the plots!
with PdfPages("presentation_plots.pdf") as pdf:
    xs = np.arange(len(methods_titles) + 1)

    for i in range(1, len(methods_titles) + 1):
        # Create the figure and axes
        fig, axs = plt.subplots(2, sharex=True, figsize=(3.5, 3.5))

        for (model, model_title), ax in zip(nets_titles, axs):
            # Set the title for the model
            ax.set_ylabel(model_title)

            # Add each violin
            for x, method in zip(xs, ["original"] + [m for m, _ in methods_titles[:i]]):
                elems = ax.violinplot(datasets[model][method].T, [x], showextrema=False)

                for b in elems["bodies"]:
                    b.set_alpha(.8)
                    b.set_facecolor(".85")
                    b.set_edgecolor("k")
                    b.set_linewidth(1)

            titles = ["Original"] + [t for _, t in methods_titles[:i]]
            ax.set_xticks(xs[:i+1])
            ax.set_xticklabels(titles[:i+1])
            ax.set_xlim(-.5, max(xs) + .5)

            ax.set_ylim(min_ys[model], max_ys[model])
            ax.set_yticks([min_ys[model], 1024, max_ys[model]])
            ax.axhline(1024, c='.5', zorder=-1, linewidth=.5)

            sns.despine(ax=ax, bottom=True)

        fig.tight_layout(pad=0, h_pad=.5)
        pdf.savefig(fig)
