import argparse
import common
from multiprocessing import Pool
from rig.routing_table.ordered_covering import minimise
from six import iteritems

def my_minimize(chip, table):
    return chip, minimise(table, None)

if __name__ == "__main__":
    # Parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("routing_table")
    args = parser.parse_args()

    # Load and minimise all routing tables
    print("Loading routing tables...")
    with open(args.routing_table, "rb") as f:
        uncompressed = common.read_routing_tables(f)

    print("Minimising routing tables...")
    p = Pool(4)
    compressed = dict(p.starmap(my_minimize, iteritems(uncompressed)))

    fn = "ordered_covering" + args.routing_table[12:]
    print("Dumping minimised routing tables to {}...".format(fn))
    with open(fn, "wb+") as f:
        common.dump_routing_tables(f, compressed)
