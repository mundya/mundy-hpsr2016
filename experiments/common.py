"""Common tools for writing and reading routing tables.

Each file may contain multiple routing tables. The 2-bytes of a routing table
are the x and y co-ordinate the table relates to, the following short is the
length of the table. Following the header there are 3 words for each entry:
key, mask and route.
"""
from rig.routing_table import RoutingTableEntry, Routes
from six import iteritems
import struct


def dump_routing_tables(fp, tables):
    """Dump routing tables to file."""
    for (x, y), entries in iteritems(tables):
        # Write the header
        fp.write(struct.pack("<2BH", x, y, len(entries)))

        # Write the entries
        for entry in entries:
            route_word = 0x0
            for route in entry.route:
                route_word |= 1 << route

            fp.write(struct.pack("<3I", entry.key, entry.mask, route_word))


def read_routing_tables(fp):
    """Read routing tables from a file."""
    tables = dict()

    data = fp.read()
    offset = 0
    while offset < len(data):
        # Read the header
        x, y, n_entries = struct.unpack_from("<2BH", data, offset)
        offset += 4

        # Prepare the entries
        entries = [None for _ in range(n_entries)]

        # Read the entries
        for i in range(n_entries):
            key, mask, route_word = struct.unpack_from("<3I", data, offset)
            offset += 12

            route = {r for r in Routes if route_word & (1 << r)}
            entries[i] = RoutingTableEntry(route, key, mask)

        # Store the table
        tables[(x, y)] = entries

    return tables
