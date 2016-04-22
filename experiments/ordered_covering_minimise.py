import argparse
import common
from rig.routing_table.ordered_covering import ordered_covering
from six import iteritems
import time

def my_minimize(chip, table):
    print("Minimising {}, {} entries...".format(chip, len(table)))
    t = time.clock()
    table, _ = ordered_covering(table, None)
    total = time.clock() - t
    print("... to {} entries in {} s".format(len(table), total))
    return chip, table

if __name__ == "__main__":
    # Parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("routing_table")
    parser.add_argument("output")
    args = parser.parse_args()

    # Load and minimise all routing tables
    print("Loading routing tables...")
    with open(args.routing_table, "rb") as f:
        uncompressed = common.read_routing_tables(f)

    print("Minimising routing tables...")
    compressed = dict(
        my_minimize(chip, table) for chip, table in iteritems(uncompressed)
    )

    print("Dumping minimised routing tables to {}...".format(args.output))
    with open(args.output, "wb+") as f:
        common.dump_routing_tables(f, compressed)
