"""Implementation of m-Tries for routing table minimisation.

Ahmand, S.; Mahapatra, R., "M-trie: an efficient approach to on-chip logic
minimization," in Computer Aided Design, 2004. ICCAD-2004. IEEE/ACM
International Conference on , vol., no., pp.428-435, 7-11 Nov. 2004
"""
import argparse
from collections import defaultdict
import common
from rig.routing_table import RoutingTableEntry, table_is_subset_of
from rig.routing_table.remove_default_routes import minimise as rde_minimise
from six import iteritems
import sys


def my_minimize(chip, table):
    sys.stdout.write("({:3d}, {:3d})\t{:4d}\t".format(
        chip[0], chip[1], len(table)))
    sys.stdout.flush()

    new_table = minimise(table)

    assert table_is_subset_of(table, new_table)

    sys.stdout.write("\033[{}m{:4d}\033[39m\t{:.2f}%\n".format(
        32 if len(new_table) < 1024 else 31,
        len(new_table),
        100. * float(len(table) - len(new_table)) / len(table)
    ))

    return chip, new_table


def minimise(table):
    """Minimise a routing table."""
    # Remove default entries
    table_ = rde_minimise(table, None)

    # Split the table into sub-tables with the same route.
    subtables = defaultdict(list)
    for entry in table_:
        subtables[entry.route].append((entry.key, entry.mask))

    # Minimise each subtable in turn
    mintables = dict()
    for i, (route, keymasks) in enumerate(iteritems(subtables)):
        trie = Node()

        for key, mask in keymasks:
            insert(trie, key, mask)

        mintables[route] = list(trie.get_keys_and_masks())

    # Return to routing table form
    return [
        RoutingTableEntry(r, k, m) for r, kms in iteritems(mintables) for
        k, m in kms
    ]


def insert(root, key, mask):
    """Add a new key and mask pair to a trie."""
    # Traverse the trie to add elements, store the queue of Nodes that we need
    # to process later to ensue the trie is valid.
    queue = root.traverse(key, mask)
    next(queue)  # We don't care about the leaf

    # Visit each Node in the queue to minimise the trie
    for node in queue:
        # If there are any intersections between the paths beginning 0... and
        # 1... then those paths should be untraversed and replaced by a path
        # beginning X...
        for path in node.get_paths_from_0() & node.get_paths_from_1():
            node.untraverse_from_0(*path)
            node.untraverse_from_1(*path)
            next(node.traverse(*path))  # Finish the traversal

        # If there are any intersections between the paths beginning 0... or
        # 1... and X... then the paths beginning 0... or 1... should be
        # removed.
        for path in node.get_paths_from_X() & node.get_paths_from_0():
            node.untraverse_from_0(*path)

        for path in node.get_paths_from_X() & node.get_paths_from_1():
            node.untraverse_from_1(*path)


class Node(object):
    def __init__(self, bit=31):
        """Create an m-Trie Node which will inspect a bit of the keys and masks
        during insertion.

        Parameters
        ----------
        bit : int
            Index of the bit that should be inspected by this Node. If negative
            then the Node is assumed to be a leaf Node.
        """
        self.bit = bit

        if not self.is_leaf:
            self.mask = (1 << bit)  # Mask applied to keys and masks
        else:
            self.mask = 0x0

        self.children = dict()  # Children of the Node

    @property
    def is_leaf(self):
        """Return if the Node is a leaf."""
        return self.bit < 0

    def get_keys_and_masks(self, _key=0, _mask=0):
        """Retrieve minimised keys and masks from the trie.

        Yield
        -----
        (key, mask)
            Minimised keys and masks.
        """
        if self.is_leaf:
            # If we are a leaf we just yield the key and mask as we receive
            # them
            yield (_key, _mask)
        else:
            # Otherwise we pass on the key and mask to the children after
            # combining them with the keys and masks that lead to that child.
            for (k, m), child in iteritems(self.children):
                for keymask in child.get_keys_and_masks(_key | k, _mask | m):
                    yield keymask

    def get_paths_from_X(self):
        return self.get_paths_from((0, 0))

    def get_paths_from_0(self):
        return self.get_paths_from((0, self.mask))

    def get_paths_from_1(self):
        return self.get_paths_from((self.mask, self.mask))

    def get_paths_from(self, child):
        if child in self.children:
            return set(self.children[child].get_keys_and_masks())
        else:
            return set()

    def traverse(self, key, mask):
        """Traverse the tree adding new Nodes when necessary.

        Yield
        -----
        Node
            Nodes along the path, yielded in order from leaf to root.
        """
        if self.is_leaf:
            yield self
        else:
            # Otherwise we determine to which child the path leads and add that
            # child if it doesn't already exist before then calling the child
            # to continue inserting the path.
            child = (key & self.mask, mask & self.mask)

            if child not in self.children:
                # Add the child and instruct it to inspect the bit one less
                # significant than the bit we inspect.
                self.children[child] = Node(self.bit - 1)

            # Insert this path into the child
            for n in self.children[child].traverse(key, mask):
                yield n
            yield self

    def untraverse(self, key, mask):
        """Remove a key and mask from the trie.

        Return
        ------
        bool
            True if the child should be removed, otherwise False
        """
        if self.is_leaf:
            # If this is a leaf then indicate that it is no longer needed
            return True  # True indicates that the child should be removed
        else:
            # Otherwise we find the child that this path leads to and call on
            # them to untraverse the path. If after doing so they should be
            # removed we remove them.
            child = (key & self.mask, mask & self.mask)
            if self.children[child].untraverse(key, mask):
                # Remove the child
                self.children.pop(child)

                # If we have no children left we should also be removed
                return bool(self.children)

    def untraverse_from_0(self, key, mask):
        self.untraverse(key, mask | self.mask)

    def untraverse_from_1(self, key, mask):
        self.untraverse(key | self.mask, mask | self.mask)


if __name__ == "__main__":
    # Parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("output_file")
    args = parser.parse_args()

    # Load and minimise all routing tables
    print("Loading routing tables...")
    with open(args.input_file, "rb") as f:
        uncompressed = common.read_routing_tables(f)

    print("Minimising routing tables...")
    compressed = dict(
        my_minimize(chip, table) for chip, table in iteritems(uncompressed)
    )

    fn = args.output_file
    print("Dumping minimised routing tables to {}...".format(fn))
    with open(fn, "wb+") as f:
        common.dump_routing_tables(f, compressed)
