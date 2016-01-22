import argparse
import common
from collections import defaultdict
from rig.routing_table import RoutingTableEntry
from six import iteritems
import subprocess
import tempfile


def key_mask_to_espresso(key, mask):
    vals = {(False, False): b'-',
            (False, True): b'0',
            (True, True): b'1'}
    return b''.join(vals[bool(key & bit), bool(mask & bit)] for
                    bit in (1 << i for i in range(32)))


def espresso_to_key_mask(text):
    key = 0x0
    mask = 0x0

    for i, bit in enumerate(text):
        if bit in {ord('0'), ord('1')}:
            mask |= (1 << i)

            if bit == ord('1'):
                key |= (1 << i)

    return key, mask


def use_espresso(table):
    """Call Espresso with appropriate arguments to minimise a routing table."""
    # Begin by breaking entries up into sets of unique routes
    route_entries = defaultdict(set)
    for entry in table:
        route_entries[frozenset(entry.route)].add((entry.key, entry.mask))

    # Sort these groups into ascending order of length
    groups = sorted(route_entries.items(), key=lambda kv: len(kv[1]))

    # Prepare to create a new table
    new_table = list()

    # Minimise each group individually using all the groups later on in the
    # table as the off-set.
    for i, (route, entries) in enumerate(groups):
        with tempfile.NamedTemporaryFile() as f:
            f.write(b".i 32\n.o 1\n.type fr\n")

            # Write the "on-set"
            for key, mask in entries:
                f.write(key_mask_to_espresso(key, mask) + b" 1\n")

            # Write the offset
            for _, entries in groups[i+1:]:
                for key, mask in entries:
                    f.write(key_mask_to_espresso(key, mask) + b" 0\n")

            f.write(b".e")
            f.flush()

            # Perform the minimisation and read back the result
            with tempfile.TemporaryFile() as g:
                subprocess.call(["espresso", f.name], stdout=g)

                # Read back from g()
                g.seek(0)
                for line in g:
                    if b'.' not in line:
                        key, mask = espresso_to_key_mask(line.strip().split()[0])
                        new_table.append(RoutingTableEntry(route, key, mask))

    return new_table


def my_minimize(chip, table):
    print("Minimising {}, {} entries...".format(chip, len(table)))
    table = use_espresso(table)
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

    fn = "espresso" + args.routing_table[12:]
    print("Dumping minimised routing tables to {}...".format(fn))
    with open(fn, "wb+") as f:
        common.dump_routing_tables(f, compressed)
