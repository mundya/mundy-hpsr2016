import argparse
import common
from collections import defaultdict
from rig.routing_table import RoutingTableEntry, table_is_subset_of
from rig.routing_table.remove_default_routes import minimise as rde_minimise
from six import iteritems
import subprocess
import sys
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
        if bit in "01":
            mask |= (1 << i)

            if bit == '1':
                key |= (1 << i)

    return key, mask


def use_espresso(table, provide_offset=True):
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
            if provide_offset:
                f.write(b".i 32\n.o 1\n.type fr\n")
            else:
                f.write(b".i 32\n.o 1\n.type f\n")

            # Write the "on-set"
            for key, mask in entries:
                f.write(key_mask_to_espresso(key, mask) + b" 1\n")

            # Write the offset
            if provide_offset:
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
                        key, mask = espresso_to_key_mask(
                            line.decode("utf-8").strip().split()[0])
                        new_table.append(RoutingTableEntry(route, key, mask))

    return new_table


def use_espresso_on_entire_table(table, provide_offset):
    """Call Espresso with appropriate arguments to minimise a routing table."""
    # Begin by breaking entries up into sets of unique routes
    route_indices = dict()
    bits_to_route = dict()
    for entry in table:
        if entry.route not in route_indices:
            route_indices[entry.route] = 1 << len(route_indices)
            bits_to_route[route_indices[entry.route]] = entry.route

    # Prepare to create a new table
    new_table = list()

    # Minimise the table, using the route indices as the function output
    with tempfile.NamedTemporaryFile() as f:
        if provide_offset:
            f.write(b".i 32\n.o %u\n.type fr\n" % len(route_indices))
        else:
            f.write(b".i 32\n.o %u\n.type f\n" % len(route_indices))

        # Write the "on-set"
        for entry in table:
            f.write(
                key_mask_to_espresso(entry.key, entry.mask) +
                " {1:0{0}b}\n".format(
                    len(route_indices),
                    route_indices[entry.route]).encode("utf-8")
            )

        f.write(b".e")
        f.flush()

        # Perform the minimisation and read back the result
        with tempfile.TemporaryFile() as g:
            subprocess.call(["espresso", f.name], stdout=g)

            # Read back from g()
            g.seek(0)
            for line in g:
                if b'.' not in line:
                    keymask, route_str = \
                        line.decode("utf-8").strip().split(" ", 1)
                    key, mask = espresso_to_key_mask(keymask)
                    route = bits_to_route[int(route_str, base=2)]
                    new_table.append(RoutingTableEntry(route, key, mask))

    return new_table


def my_minimize(chip, table, whole_table, provide_offset, remove_default_entries):
    sys.stdout.write("({:3d}, {:3d})\t{:4d}\t".format(
        chip[0], chip[1], len(table)))
    sys.stdout.flush()

    table_ = table

    if remove_default_entries:
        table_ = rde_minimise(table, None)

    if whole_table:
        new_table = use_espresso_on_entire_table(table_, provide_offset)
    else:
        new_table = use_espresso(table_, provide_offset)

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
    parser.add_argument("--whole-table", action="store_true", default=False)
    parser.add_argument("--no-off-set", action="store_true", default=False)
    parser.add_argument("--remove-default-entries", action="store_true", default=False)
    args = parser.parse_args()

    # Load and minimise all routing tables
    print("Loading routing tables...")
    with open(args.routing_table, "rb") as f:
        uncompressed = common.read_routing_tables(f)

    print("Minimising routing tables...")
    compressed = dict(
        my_minimize(chip, table, args.whole_table, not args.no_off_set, args.remove_default_entries) for
        chip, table in iteritems(uncompressed)
    )

    fn = args.out
    print("Dumping minimised routing tables to {}...".format(fn))
    with open(fn, "wb+") as f:
        common.dump_routing_tables(f, compressed)
