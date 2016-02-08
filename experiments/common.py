"""Common tools for writing and reading routing tables.

Each file may contain multiple routing tables. The 2-bytes of a routing table
are the x and y co-ordinate the table relates to, the following short is the
length of the table. Following the header there are 4 words for each entry:
key, mask, source and route.
"""
import numpy as np
from rig.routing_table import RoutingTableEntry, Routes
from six import iteritems
import struct


def dump_memory_profile(fp, profile):
    """Dump the memory profile to a file.

    File is formatted as entries of::

       x : 1 byte
       y : 1 byte
       padding : 2 bytes
       n_entries : 4 bytes
       memory usage : 4 bytes per entry.
    """
    for (x, y), entries in iteritems(profile):
        fp.write(struct.pack('<2B2xI', x, y, len(entries)))
        fp.write(bytes(entries.data))


def read_memory_profile(fp):
    """Read memory profiles from a file."""
    profile = dict()

    data = fp.read()
    offset = 0
    while offset < len(data):
        x, y, n_entries = struct.unpack_from("<2B2xI", data, offset)
        offset += 8

        # Read the entries into a Numpy array
        profile[(x, y)] = np.ndarray(
            shape=n_entries,
            dtype=np.uint32,
            buffer=data[offset:offset + n_entries*4]
        )
        offset += n_entries * 4

    return profile


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

            source_word = 0x0
            for source in entry.sources:
                if source is not None:
                    source_word |= 1 << source

            fp.write(struct.pack("<4I", entry.key, entry.mask,
                                 source_word, route_word))


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
            key, mask, source_word, route_word = \
                struct.unpack_from("<4I", data, offset)
            offset += 16

            route = {r for r in Routes if route_word & (1 << r)}
            source = {s for s in Routes if source_word & (1 << s)}
            entries[i] = RoutingTableEntry(route, key, mask, source)

        # Store the table
        tables[(x, y)] = entries

    return tables


def read_table_lengths(fp):
    """Read routing table lengths from a file."""
    lengths = dict()

    data = fp.read()
    offset = 0
    while offset < len(data):
        # Read the header
        x, y, n_entries = struct.unpack_from("<2BH", data, offset)
        offset += 4 + n_entries*16

        # Store the length
        lengths[(x, y)] = n_entries

    return lengths
