from common import read_memory_profile
import numpy as np
from six import itervalues


if __name__ == "__main__":
    for title, x in (("Gaussian", "gaussian"),
                     ("Centroid", "centroid")):
        with open("memory_profiles/{}_12_12_xyp.bin".format(x), "rb") as f:
            max_usage = 0
            of_which_table = 0

            for usage in itervalues(read_memory_profile(f)):
                if np.max(usage) > max_usage:
                    max_usage = np.max(usage)
                    of_which_table = usage[1]

            print("{}: {} bytes of which {} bytes is the table".format(title, max_usage, of_which_table))
