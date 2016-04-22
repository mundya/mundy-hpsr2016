# Benchmarks and Experiments

## Benchmarks

### Format of benchmark files

Benchmark routing tables (and their minimized equivalents) are located in the
`uncompressed` and `compressed` directories. `common.py` contains utility
methods for reading and dumping files of this format (`read_routing_tables` and
`dump_routing_tables`).

The file format is as follows: Each routing table in the file begins with
2-bytes indicating the `x` and `y` co-ordinates of the chip with which it is
associated and a short (a 2-byte integer) indicating the number of entries in
the table. The entries follow immediately after this short header; each entry
consists of 4 words (32-bit values) representing the key, mask, source and
route (following the
[Rig convention for routing table entries](http://rig.readthedocs.org/en/stable/routing_table_tools_doctest.html#routingtableentry-and-routes-routing-table-data-structures)).

An additional utility method (`read_table_lengths`) may be used to extract a
dictionary mapping chip co-ordinates to the length of the table for that chip.

### Existing benchmarks

The `uncompressed` directory contains benchmark routing tables. Files beginning
`gaussian_` represent tables belonging to the "locally-connected" model in the
paper; files beginning `centroid_` belong to the centroid model from the paper.
The suffix on the file represents different key allocations; in the paper we
only use `xyp` keys.

The others are:

 - `hilbert` - a Hilbert Curve is fitted to the machine and each chip is
   assigned an ID related to its position on the curve.
 - `xyzp` - the hexagonal co-ordinates of a chip are used to assign keys.
 - `rnd` - a unique 12-bit random number is assigned to each core (12-bits because
   `ceil(log_2(144*17)) = 12`

### Compressed benchmarks

The `compressed` directory contains the results of minimising benchmarks from
the `uncompressed` directory.

 - `esp_tables_no_offset` indicates that non-order-exploiting Espresso was used
   to minimise the tables.
 - `esp_subtables_full` indicates that order-exploiting Espresso was used to
   minimise the tables.
 - `mtrie` indicates that m-Trie was used.
 - `oc_spinnaker` indicates that the SpiNNaker implementation of
   Ordered-Covering was used to minimise the routing tables.
 - `remove_default` is the original benchmarks with any entries which could be
   handled by default routing removed.

### Generating new benchmark routing tables

The script `make_gaussian.py` may be used to generate new routing tables for
the "locally-connected" model from the paper.
Likewise, `make_centroid.py` will generate new routing tables for the centroid
model.

## Minimizing routing tables

### Using Espresso

`espresso.py` can be used to minimize routing tables with Espresso (which must
be installed and available on the path).
Different arguments may be used to use order-exploiting or non-order-exploiting
minimization:

 - Order-exploiting: `python espresso.py [in_table] [out_table]`
 - Non-order-exploiting: `python espresso.py [in] [out] --whole-table --no-off-set --remove-default-entries`

### Using m-Trie

`mtrie.py` can be used to minimize routing tables using the m-Trie method. Usage:
`python mtrie.py in out`.

### Using Ordered-Covering on SpiNNaker

To use Ordered-Covering on SpiNNaker first download and build
[the SpiNNaker implementation of Ordered-Covering](https://github.com/project-rig/rig_routing_tables)
and copy the resulting `*.aplx` files to this directory.

Next use `spinnaker.py` with `python spinnaker.py [in] [out]`. This script will
assume that a booted 144-chip SpiNNaker system is available on `192.168.1.1`;
you may modify the script to change the IP address.

A memory profile may be generated with
`python spinnaker.py in out --memory-profile filename`. The resulting memory
profile can be read back with the `read_memory_profile` method in `common.py`.

### Using Ordered-Covering on-host

The Python implementation of ordered-covering may be used with `ordered_covering_minimise.py` as:
`python ordered_covering_minimize.py in out`.

## Utilities

`test_table.py` can be used to check that one benchmark file is a superset of another.
Usage: `python test_table.py original minimised`.
