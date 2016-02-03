"""
Four sets of routing tables are produced for the same network:
    * With keys assigned using a Hilbert Curve (this will tend to ensure that
      similar keys originated in physical proximal chips)
    * With keys assigned using the (x, y, p) of each core - a common SpiNNaker
      approach
    * With keys assigned using the (x, y, z, p) of each core
    * With 12-bit keys randomly assigned to each core

Routing is performed by the NER algorithm, as implemented in Rig.
"""
from collections import OrderedDict
import random
from rig.bitfield import BitField
from rig.netlist import Net
from rig.geometry import to_xyz, minimise_xyz, shortest_torus_path_length
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
    vertices_resources = OrderedDict(
        (vertex, {Cores: 1}) for vertex in itervalues(vertices)
    )
    placements = OrderedDict(
        (vertex, (x, y)) for (x, y, p), vertex in iteritems(vertices)
    )
    allocations = OrderedDict(
        (vertex, {Cores: slice(p, p+1)}) for (x, y, p), vertex in
        iteritems(vertices)
    )

    # Compute the distance dependent probabilities - this is a geometric
    # distribution such that each core has a 50% chance of being connected to
    # each core on the same chip, 25% on chips one hop away, 12.5% on chips two
    # hops away, etc.
    p = 0.5
    probs = {d: p*(1 - p)**d for d in
             range(max(machine.width, machine.height))}

    p = 0.3
    dprobs = {d: p*(1 - p)**d for d in
              range(max(machine.width, machine.height))}

    # Compute offsets to get to centroids
    vector_centroids = list()
    for d in (5, 6, 7):
        for i in range(d + 1):
            for j in range(d + 1 - i):
                vector_centroids.append((i, j, d - i - j))

    # Make the nets, each vertex is connected with distance dependent
    # probability to other vertices.
    random.seed(123)
    nets = OrderedDict()
    for source_coord, source in iteritems(vertices):
        # Convert source_coord to xyz form
        source_coord_xyz = minimise_xyz(to_xyz(source_coord[:-1]))

        # Add a number of centroids
        x, y, z = source_coord_xyz
        possible_centroids = [minimise_xyz((x + i, y + j, z + k)) for
                              i, j, k in vector_centroids]
        n_centroids = random.choice(17*(0, ) + (1, 1) + (2, ))
        centroids = random.sample(possible_centroids, n_centroids)

        # Construct the sinks list
        sinks = list()
        for sink_coord, sink in iteritems(vertices):
            # Convert sink_coord to xyz form
            sink_coord = minimise_xyz(to_xyz(sink_coord[:-1]))

            # Get the path length to the original source
            dist = shortest_torus_path_length(source_coord_xyz, sink_coord,
                                              machine.width, machine.height)
            if random.random() < probs[dist]:
                sinks.append(sink)
                continue

            # See if the sink is connected to the centre of any of the
            # centroids.
            for coord in centroids:
                dist = shortest_torus_path_length(
                    coord, sink_coord, machine.width, machine.height
                )

                if random.random() < dprobs[dist]:
                    sinks.append(sink)
                    break

        # Add the net
        nets[source_coord] = Net(source, sinks)

    rig_nets = list(itervalues(nets))  # Just the nets

    # Determine how many bits to use in the keys
    xyp_fields = BitField(32)
    xyp_fields.add_field("x", length=8, start_at=24)
    xyp_fields.add_field("y", length=8, start_at=16)
    xyp_fields.add_field("p", length=5, start_at=11)

    xyzp_fields = BitField(32)
    xyzp_fields.add_field("x", length=8, start_at=24)
    xyzp_fields.add_field("y", length=8, start_at=16)
    xyzp_fields.add_field("z", length=8, start_at=8)
    xyzp_fields.add_field("p", length=5, start_at=3)

    hilbert_fields = BitField(32)
    hilbert_fields.add_field("index", length=16, start_at=16)
    hilbert_fields.add_field("p", length=5, start_at=11)

    random.seed(321)
    rnd_fields = BitField(32)
    rnd_fields.add_field("rnd", length=12, start_at=20)
    rnd_seen = set()

    # Generate the routing keys
    net_keys_xyp = OrderedDict()
    net_keys_xyzp = OrderedDict()
    net_keys_hilbert = OrderedDict()
    net_keys_rnd = OrderedDict()
    for i, (x, y) in enumerate(chip for chip in hilbert_chip_order(machine) if
                               chip in machine):
        # Add the key for each net from each processor
        for p in range(1, 18):
            # Get the net
            net = nets[(x, y, p)]

            # Construct the xyp key/mask
            net_keys_xyp[net] = xyp_fields(x=x, y=y, p=p)

            # Construct the xyzp mask
            x_, y_, z_ = minimise_xyz(to_xyz((x, y)))
            net_keys_xyzp[net] = xyzp_fields(x=x_, y=y_, z=abs(z_), p=p)

            # Construct the Hilbert key/mask
            net_keys_hilbert[net] = hilbert_fields(index=i, p=p)

            # Construct the random 12 bit value field
            val = None
            while val is None or val in rnd_seen:
                val = random.getrandbits(12)
            rnd_seen.add(val)
            net_keys_rnd[net] = rnd_fields(rnd=val)

    # Route the network and then generate the routing tables
    constraints = list()
    print("Routing...")
    routing_tree = route(vertices_resources, rig_nets, machine, constraints,
                         placements, allocations)

    # Assign field widths
    xyp_fields.assign_fields()
    xyzp_fields.assign_fields()
    hilbert_fields.assign_fields()

    # Write the routing tables to file
    for fields, desc in ((net_keys_xyp, "xyp"),
                         (net_keys_xyzp, "xyzp"),
                         (net_keys_hilbert, "hilbert"),
                         (net_keys_rnd, "rnd")):
        print("Getting keys and masks...")
        keys = OrderedDict(
            (net, (bf.get_value(), bf.get_mask())) for net, bf in
            iteritems(fields)
        )

        print("Constructing routing tables for {}...".format(desc))
        tables = routing_tree_to_tables(routing_tree, keys)
        print([len(x) for x in itervalues(tables)])

        print("Writing to file...")
        fn = "uncompressed/centroid_{}_{}_{}.bin".format(
            machine.width, machine.height, desc)
        with open(fn, "wb+") as f:
            dump_routing_tables(f, tables)

if __name__ == "__main__":
    make_routing_tables()
