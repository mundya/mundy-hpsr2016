import argparse
import common
from rig.routing_table.remove_default_routes import minimise
from rig.routing_table import table_is_subset_of
from six import iteritems
import sys


def my_minimize(chip, table):
    sys.stdout.write("({:3d}, {:3d})\t{:4d}\t".format(
        chip[0], chip[1], len(table)))

    new_table = minimise(table, None)
    assert table_is_subset_of(table, new_table)

    sys.stdout.write("\033[{}m{:4d}\033[39m\t{:.2f}%\n".format(
        32 if len(new_table) < 1024 else 31,
        len(new_table),
        100. * float(len(table) - len(new_table)) / len(table)
    ))

    return chip, new_table

if __name__ == "__main__":
    # Parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("routing_table")
    parser.add_argument("out")
    args = parser.parse_args()

    # Load and minimise all routing tables
    print("Loading routing tables...")
    with open(args.routing_table, "rb") as f:
        uncompressed = common.read_routing_tables(f)

    print("Minimising routing tables...")
    compressed = dict(
        my_minimize(chip, table) for chip, table in iteritems(uncompressed)
    )

    fn = args.out
    print("Dumping minimised routing tables to {}...".format(fn))
    with open(fn, "wb+") as f:
        common.dump_routing_tables(f, compressed)
