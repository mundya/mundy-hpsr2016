"""Constructs a circular-convolution-like network (very large fan-out followed
by very large fan-in) on a 3-board toroid.

Nets are assigned unique IDs based on their order of creation.
"""
import logging

from rig.netlist import Net
from rig.place_and_route import Cores, Machine, place, allocate
from rig.place_and_route.constraints import SameChipConstraint
from rig.place_and_route.route.ner import route
from rig.routing_table import routing_tree_to_tables

from common import dump_routing_tables

logging.basicConfig(level=logging.DEBUG)


def share_list(items, n_shares):
    n_items = len(items) // n_shares
    n_larger = len(items) % n_shares
    n_smaller = n_shares - n_larger

    items = iter(items)
    for _ in range(n_larger):
        values = tuple(next(items) for n in range(n_items + 1))
        yield values

    for _ in range(n_smaller):
        values = tuple(next(items) for n in range(n_items))
        yield values


def make_routing_tables():
    # Construct the vertices
    vertex_a = [object() for _ in range(17*2)]
    vertex_b = [object() for _ in range(2056)]
    vertex_c = [object() for _ in range(17*4)]

    # Construct the nets
    nets = list()

    # Fan out from A
    for a, bs in zip(vertex_a,
                     share_list(vertex_b, len(vertex_a))):
        nets.extend(Net(a, b) for b in bs)

    # Fan in to C
    for c, bs in zip(vertex_c,
                     share_list(vertex_b, len(vertex_c))):
        nets.extend(Net(b, c) for b in bs)

    # Construct constraints that place elements of vertex A together on the
    # same chip
    constraints = list()
    for aa in share_list(vertex_a, 2):
        constraints.append(SameChipConstraint(aa))

    # Add constraints that place elements of vertex C together on the same
    # chip.
    for cs in share_list(vertex_c, 4):
        constraints.append(SameChipConstraint(cs))

    # Each vertex will require 1 core
    vertices_resources = {a: {Cores: 1} for a in vertex_a}
    vertices_resources.update({b: {Cores: 1} for b in vertex_b})
    vertices_resources.update({c: {Cores: 1} for c in vertex_c})

    # Construct a faux-machine on which to place
    machine = Machine(12, 12)

    # Place and route the net
    placements = place(vertices_resources, nets, machine, constraints)
    allocations = allocate(vertices_resources, nets, machine, constraints,
                           placements)
    routes = route(vertices_resources, nets, machine, constraints, placements,
                   allocations)


if __name__ == "__main__":
    make_routing_tables()
