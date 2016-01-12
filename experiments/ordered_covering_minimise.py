import argparse
import common
from rig.routing_table.ordered_covering import ordered_covering
from six import iteritems

def my_minimize(chip, table):
    print("Minimising {}, {} entries...".format(chip, len(table)))
    table, _ = ordered_covering(table, None)
    print("... to {} entries".format(len(table)))
    return chip, table

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
    compressed = dict(
        my_minimize(chip, table) for chip, table in iteritems(uncompressed)
    )

    fn = "ordered_covering" + args.routing_table[12:]
    print("Dumping minimised routing tables to {}...".format(fn))
    with open(fn, "wb+") as f:
        common.dump_routing_tables(f, compressed)
