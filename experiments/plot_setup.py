from matplotlib import pyplot as plt
import numpy as np
import random
from rig.geometry import to_xyz, minimise_xyz, shortest_torus_path_length
import seaborn as sns

random.seed(2801)

sns.set(context="paper", style="whitegrid", font="Times New Roman")

fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(3.5, 1))

# Compute the probability for the Gaussian model
g_prob = np.zeros((12, 12))

home = minimise_xyz(to_xyz((1, 6)))

for x in range(12):
    for y in range(12):
        target = minimise_xyz(to_xyz((x, y)))
        d = shortest_torus_path_length(home, target, 12, 12)
        g_prob[y, x] = d

g_prob = .5 * np.exp(-.65*g_prob)

ax0.set_title("Locally-connected")
ax0.grid(False)
ax0.set_xticklabels([])
ax0.set_yticklabels([])
ax0.matshow(g_prob, vmin=0.0, vmax=1.0, origin='lower')

# For the centroid model
g_centr = np.zeros((12, 12))

# Compute offsets to get to centroids
vector_centroids = list()
for d in (5, 6, 7):
    for i in range(d + 1):
        for j in range(d + 1 - i):
            vector_centroids.append((i, j, d - i - j))

# Convert source_coord to xyz form
source_coord_xyz = minimise_xyz((6, 6, 0))

# Add a number of centroids
x, y, z = source_coord_xyz
possible_centroids = [minimise_xyz((x + i, y + j, z + k)) for
                      i, j, k in vector_centroids]
centroids = random.sample(possible_centroids, 2)
print(centroids)

for x in range(12):
    for y in range(12):
        target = minimise_xyz(to_xyz((x, y)))
        d = shortest_torus_path_length(source_coord_xyz, target, 12, 12)

        g_centr[y, x] = 0.5*(1-0.5)**d

        for c in centroids:
            d = shortest_torus_path_length(c, target, 12, 12)
            g_centr[y, x] += 0.3*(1 - 0.3)**d


ax1.set_title("Centroid")
ax1.grid(False)
ax1.set_xticklabels([])
ax1.set_yticklabels([])
ax1.matshow(g_centr, vmin=0, vmax=1.0, origin='lower')

plt.tight_layout(pad=0)
plt.savefig("experiments.pdf")
