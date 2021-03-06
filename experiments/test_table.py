import argparse
import common
from rig.routing_table import table_is_subset_of
from six import iteritems
import sys

if __name__ == "__main__":
    # Parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("original_table")
    parser.add_argument("compressed_table")
    args = parser.parse_args()

    # Load and test all routing tables
    print("Loading...")
    with open(args.original_table, "rb") as f:
        original = common.read_routing_tables(f)

    with open(args.compressed_table, "rb") as f:
        compressed = common.read_routing_tables(f)

    print("Testing...")
    for chip, table in iteritems(original):
        print("\t{}".format(chip))
        assert table_is_subset_of(table, compressed[chip])
