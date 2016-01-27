"""Use a SpiNNaker implementation of Ordered Covering to minimise routing
tables.
"""
import argparse
import common
from rig.machine_control import MachineController
from rig.routing_table import RoutingTableEntry, Routes
from six import iteritems, iterkeys, itervalues
import struct
import time


def pack_table(table, target_length):
    """Pack a routing table into the form required for dumping into SDRAM."""
    data = bytearray(2*4 + len(table)*3*4)

    # Pack the header
    struct.pack_into("<2I", data, 0, len(table), target_length)

    # Pack in the entries
    offset = 8
    for entry in table:
        pack_rte_into(entry, data, offset)
        offset += 12

    return data


def pack_rte_into(rte, buf, offset):
    """Pack a routing table entry into a buffer."""
    # Construct the route integer
    route = 0x0
    for r in rte.route:
        route |= 1 << r

    # Pack
    struct.pack_into("<3I", buf, offset, rte.key, rte.mask, route)


def unpack_table(data):
    # Unpack the header
    length, _ = struct.unpack_from("<2I", data)

    # Unpack the table
    table = [None for _ in range(length)]
    for i in range(length):
        key, mask, route = struct.unpack_from("<3I", data, i*12 + 8)
        routes = {r for r in Routes if (1 << r) & route}
        table[i] = RoutingTableEntry(routes, key, mask)

    return table


if __name__ == "__main__":
    # Parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("routing_table")
    parser.add_argument("out_file")
    parser.add_argument("target_length", type=int, default=0, nargs='?')
    args = parser.parse_args()

    # Load and minimise all routing tables
    print("Reading routing tables...")
    with open(args.routing_table, "rb") as f:
        uncompressed = common.read_routing_tables(f)

    # Talk to the machine
    mc = MachineController("192.168.1.1")
    mc.send_signal("stop")

    # Convert the tables into the appropriate formats
    chip_data = {chip: pack_table(table, args.target_length) for chip, table in
                 iteritems(uncompressed)}

    # Allocate memory on the machine
    chip_mem = {
        (x, y): mc.sdram_alloc_as_filelike(len(data), x=x, y=y, tag=1) for
        (x, y), data in iteritems(chip_data)
    }

    # Build the targets dictionary
    targets = {chip: {1} for chip in iterkeys(chip_mem)}

    # Load the data
    print("Loading data...")
    t = time.clock()
    for chip, mem in iteritems(chip_mem):
        mem.write(chip_data[chip])
    load_time = time.clock() - t
    print("... took {:.3f} s".format(load_time))

    # Load the application
    print("Loading application...")
    mc.load_application("./ordered_covering.aplx", targets)
    t = time.clock()

    # Wait until this does something interesting
    print("Minimising...")
    ready = mc.wait_for_cores_to_reach_state("exit", len(uncompressed), timeout=60.0)
    if ready < len(uncompressed):
        raise Exception("Something didn't work...")
    run_time = time.clock() - t
    print("... took ~{:.3f} s".format(run_time))

    # Read back the routing tables
    print("Reading back results...")
    for mem in itervalues(chip_mem):
        mem.seek(0)

    compressed = {chip: unpack_table(mem.read()) for chip, mem in
                  iteritems(chip_mem)}

    # Dump to file
    with open(args.out_file, "wb+") as f:
        common.dump_routing_tables(f, compressed)

    print({chip: len(table) for chip, table in iteritems(compressed)})

    # Tidy up
    mc.send_signal("stop")
