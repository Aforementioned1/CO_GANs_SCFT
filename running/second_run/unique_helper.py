#### Most of this code was provided by Sayani :)

# read CSV free energies
import sys
import run_scft
import numpy as np
import matplotlib.pyplot as plt
data = run_scft.read_csv_col(sys.argv[1], "free_energy", lambda text: float(text), debug = False)
names = run_scft.read_csv_col(sys.argv[1], "name", debug = False)

# remove -1 nonconverged free energies
data_fixed = [(name, data) for name, data in zip(names, data) if data != -1]

# ---- Reference phase free energy ----
f_DG = 2.74517041186   #  (here you can consider comparing with double gyroid free energy as it is the most stable network structure)
tol = 1e-5            # numerical tolerance for grouping

# ---- Compute delta free energies ----
delta_f = {}
for name, f in data_fixed:
    if f is not None:
        delta_f[name] = f - f_DG

# delta_f = sorted(delta_f.items(), key = lambda pair: pair[1])
       
# ---- Group identical free energies (within tolerance) ----
groups = []  # each element: [representative_delta_f, [system_numbers]]

# for name, df in sorted(delta_f.items(), key = lambda pair: pair[1]):
for name, df in delta_f.items():
    placed = False
    for g in groups:
        if abs(df - g[0]) < tol:
            g[1].append(name)
            placed = True
            break
    if not placed:
        groups.append([df, [name]])

print("\n--- Degeneracy w.r.t reference phase ---")
for df, systems in sorted(groups, key=lambda x: x[0]):
    print(f"Δf = {df:.6e} : {len(systems)} systems -> {sorted(systems, key=int)}")     

print(f"--- Number of groups: {len(groups)} ---")                                      


# ---- Histogram of Δf ----
dfs = list(delta_f.values())

pops = []

for ind, df in enumerate(dfs):
    # -0.045
    if df > -0.03999 or df < -0.04001:
        pops.append(ind)
        # print("popped!")

for p in reversed(sorted(pops)):
    dfs.pop(p)
    
plt.figure(figsize=(6,4), dpi=500)
plt.xticks(np.arange(-0.04001, -0.03999, 0.000003))
plt.ticklabel_format(style = 'plain', axis = 'both')
plt.hist(dfs, bins=250)
plt.savefig("uniques_final.png")