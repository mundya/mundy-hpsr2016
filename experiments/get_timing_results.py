from collections import defaultdict
import numpy as np
from six import iterkeys


if __name__ == "__main__":
    # Load the data
    load_times = defaultdict(list)
    run_times = defaultdict(list)

    with open("timing.csv", "r") as f:
        next(f)  # Skip the comment row
        for row in f:
            model, target_length, load_time, run_time = tuple(row.strip().split())
            load_times[(model, target_length)].append(float(load_time))
            run_times[(model, target_length)].append(float(run_time))

    for key in iterkeys(run_times):
        # Compute the means
        mean_load_times = sum(load_times[key]) / len(load_times[key])
        mean_run_times = sum(run_times[key]) / len(run_times[key])

        # Output
        model, target_length = key
        print("{} {} {:.3f} {:.3f}".format(model, target_length,
                                           mean_load_times, mean_run_times))
