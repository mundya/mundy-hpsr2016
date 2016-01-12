"""Constructs routing tables for a SpiNNaker 3-board toroid that simulates
all-to-all connections between cores.

Three sets of routing tables are produced for the same network:
    * With keys assigned using a Hilbert Curve (this will tend to ensure that
      similar keys originated in physical proximal chips)
    * With keys assigned using the (x, y, p) of each core - a common SpiNNaker
      approach
    * With keys assigned using the (x, y, z, p) of each core

Routing is performed by the NER algorithm, as implemented in Rig.
"""
import math
from rig.netlist import Net
from rig.geometry import to_xyz, minimise_xyz
from rig.place_and_route import Cores, Machine
from rig.place_and_route.place.hilbert import hilbert_chip_order
from rig.place_and_route.route.ner import route
from rig.routing_table import routing_tree_to_tables
from six import iteritems, itervalues

from common import dump_routing_tables


def make_routing_tables():
    # Create a perfect SpiNNaker machine to build against
    machine = Machine(12, 12)

    # Assign a vertex to each of the 17 application cores on each chip
    vertices = {(x, y, p): object() for x, y in machine for p in range(1, 18)}

    # Generate the vertex resources, placements and allocations (required for
    # routing)
    vertices_resources = {vertex: {Cores: 1} for vertex in
                          itervalues(vertices)}
    placements = {vertex: (x, y) for (x, y, p), vertex in iteritems(vertices)}
    allocations = {vertex: {Cores: slice(p, p+1)} for (x, y, p), vertex in
                   iteritems(vertices)}

    # Make the nets, each vertex is connected to itself and all other vertices
    nets = {(x, y, p): Net(source, list(itervalues(vertices))) for
            (x, y, p), source in iteritems(vertices)}
    rig_nets = list(itervalues(nets))  # Just the nets

    # Determine how many bits to use in the keys
    x_bits = int(math.ceil(math.log(machine.width, 2)))
    y_bits = int(math.ceil(math.log(machine.height, 2)))
    z_bits = max(x_bits, y_bits)
    hilbert_bits = int(math.ceil(
        math.log(max(machine.width, machine.height)**2, 2)))
    p_bits = 5

    # Construct the masks
    xyp_bits = x_bits + y_bits + p_bits
    xyp_shift = 32 - xyp_bits
    xyp_mask = ((1 << (xyp_bits)) - 1) << xyp_shift

    xyzp_bits = xyp_bits + z_bits
    xyzp_shift = 32 - xyzp_bits
    xyzp_mask = ((1 << (xyzp_bits)) - 1) << xyzp_shift

    hilbert_shift = 32 - (hilbert_bits + p_bits)
    hilbert_mask = ((1 << (hilbert_bits + p_bits)) - 1) << hilbert_shift

    # Generate the routing keys
    net_keys_xyp = dict()
    net_keys_xyzp = dict()
    net_keys_hilbert = dict()
    for i, (x, y) in enumerate(chip for chip in hilbert_chip_order(machine) if
                               chip in machine):
        # Add the key for each net from each processor
        for p in range(1, 18):
            # Get the net
            net = nets[(x, y, p)]

            # Construct the xyp key/mask
            xyp_key = ((((x << y_bits) | y) << p_bits) | p) << xyp_shift
            net_keys_xyp[net] = (xyp_key, xyp_mask)

            # Construct the xyzp mask
            x_, y_, z_ = minimise_xyz(to_xyz((x, y)))
            z_ = abs(z_)
            xyzp_key = ((((((x_ << y_bits) | y_) << z_bits) | z_) << p_bits) |
                        p) << xyzp_shift
            net_keys_xyzp[net] = (xyzp_key, xyzp_mask)

            # Construct the Hilbert key/mask
            hilbert_key = ((i << p_bits) | p) << hilbert_shift
            net_keys_hilbert[net] = (hilbert_key, hilbert_mask)

    # Route the network and then generate the routing tables
    constraints = list()
    print("Routing...")
    routing_tree = route(vertices_resources, rig_nets, machine, constraints,
                         placements, allocations, radius=0)

    # Write the routing tables to file
    for keys, desc in ((net_keys_xyp, "xyp"),
                       (net_keys_xyzp, "xyzp"),
                       (net_keys_hilbert, "hilbert")):
        print("Constructing routing tables for {}...".format(desc))
        tables = routing_tree_to_tables(routing_tree, keys)

        print("Writing to file...")
        fn = "uncompressed/all_to_all_{}_{}_{}.bin".format(
            machine.width, machine.height, desc)
        with open(fn, "wb+") as f:
            dump_routing_tables(f, tables)

if __name__ == "__main__":
    make_routing_tables()
