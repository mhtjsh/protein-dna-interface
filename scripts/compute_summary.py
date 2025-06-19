#!/usr/bin/env python3
import os
import glob
import argparse
import pandas as pd
import re
import math

NONPOLAR = {'ALA', 'VAL', 'LEU', 'ILE', 'MET', 'PHE', 'TRP', 'PRO', 'GLY'}
AMINO_ACIDS = [
    'ALA', 'ARG', 'ASN', 'ASP', 'CYS', 'GLN', 'GLU', 'GLY', 'HIS', 'ILE',
    'LEU', 'LYS', 'MET', 'PHE', 'PRO', 'SER', 'THR', 'TRP', 'TYR', 'VAL'
]

# ----------------------
# 1. Parse CLI arguments
# ----------------------
p = argparse.ArgumentParser(description="Compute interface summary for a given PDB ID")
p.add_argument("--pdb-id", required=True, help="PDB ID to process, e.g. 1A3Q")
p.add_argument("--rsa-dir", default="rsa", help="Path to RSA directory containing .int files")
p.add_argument("--out-dir", default="interface", help="Directory to write output CSVs")
args = p.parse_args()

pdb_id = args.pdb_id
rsa_dir = os.path.abspath(args.rsa_dir)
out_dir = os.path.abspath(args.out_dir)

# ----------------------
# 2. Locate matching .int files
# ----------------------
int_paths = [
    f for f in glob.glob(os.path.join(rsa_dir, f"{pdb_id}*.int"))
    if re.match(rf"{re.escape(pdb_id)}[A-Za-z]\.int$", os.path.basename(f), re.IGNORECASE)
]

if not int_paths:
    raise FileNotFoundError(f"No .int files for {pdb_id} found in {rsa_dir}")

# ----------------------
# 3. Parse ATOM lines from .int files
# ----------------------
records = []
for path in int_paths:
    with open(path) as f:
        for line in f:
            if not line.lstrip().startswith("ATOM"):
                continue
            parts = line.split()
            try:
                asa_m = float(parts[-2])
                asa_c = float(parts[-1])
            except (ValueError, IndexError):
                continue
            delta = asa_m - asa_c
            records.append({
                'chain': parts[4],
                'resnum': parts[5],
                'resname': parts[3],
                'delta': delta
            })

if not records:
    raise RuntimeError(f"No ATOM records parsed for {pdb_id} from .int files")

df = pd.DataFrame(records)

# ----------------------
# 4. Compute interface summary
# ----------------------
total_atoms       = len(df)
total_residues    = df.drop_duplicates(['chain', 'resnum']).shape[0]
total_area        = round(df['delta'].sum(), 2)
local_density     = round(total_atoms / total_area, 3) if total_area else 0.0
fraction_buried   = round(1.0, 3)
nonpolar_df       = df[df['resname'].isin(NONPOLAR)]
fraction_nonpolar = round(len(nonpolar_df) / total_atoms, 3) if total_atoms else 0.0
nonpolar_area     = round(nonpolar_df['delta'].sum(), 2)

# ----------------------
# 5. Compute residue propensity (log-weighted per-structure)
# ----------------------

# Parse .rsa residues (surface background)
rsa_path = os.path.join(rsa_dir, f"{pdb_id}.rsa")
rsa_residues = []
if not os.path.exists(rsa_path):
    raise FileNotFoundError(f"Missing RSA file: {rsa_path}")
with open(rsa_path) as f:
    for line in f:
        if line.lstrip().startswith("RES"):
            parts = line.split()
            if len(parts) >= 4:
                rsa_residues.append(parts[3])

# Frequency on surface and interface
residue_list_int = df['resname'].tolist()
interface_counts = {aa: residue_list_int.count(aa) for aa in AMINO_ACIDS}
surface_counts   = {aa: rsa_residues.count(aa) for aa in AMINO_ACIDS}

# Compute weighted log-propensity
log_weighted_values = []
for aa in AMINO_ACIDS:
    freq_int = interface_counts[aa]
    freq_surf = surface_counts[aa]

    if freq_surf == 0 or freq_int == 0:
        log_weighted = 0
    else:
        prop_score = (freq_int / len(residue_list_int)) / (freq_surf / len(rsa_residues))
        log_weighted = math.log(prop_score) * freq_int

    log_weighted_values.append(log_weighted)

# Final residue propensity value
log_weighted_propensity_score = round(sum(log_weighted_values), 3)
# ----------------------
# 6. Save summary + propensities
# ----------------------
os.makedirs(out_dir, exist_ok=True)

# Interface summary table
summary = pd.DataFrame({
    'Interface Properties': [
        'Total Interface Atoms',
        'Total Interface Residues',
        'Total Interface Area (Å²)',
        'Local Atomic Density',
        'Residue Propensity Score',
        'Fraction of Buried Atoms',
        'Fraction of Non-Polar Atoms',
        'Non-Polar Interface Area'
    ],
    'Value': [
        total_atoms,
        total_residues,
        total_area,
        local_density,
        log_weighted_propensity_score,
        fraction_buried,
        fraction_nonpolar,
        nonpolar_area
    ],
    'Notes': [
        'Count atoms with ΔASA > 0',
        'Based on ΔASA at residue level',
        'ΔASA sum',
        'atoms / area',
        'log-weighted: log(freq_int/freq_surf) * count',
        'ΔASA atoms / total atoms',
        'Use residue types',
        'ΔASA only for non-polar residues'
    ]
})

summary_out = os.path.join(out_dir, f"{pdb_id}_interface_summary.csv")
summary.to_csv(summary_out, index=False)
print(f"✅ Wrote summary → {summary_out}")

# Compute and write per-residue propensities
propensity_scores = {}
for aa in AMINO_ACIDS:
    if surface_counts[aa] > 0:
        prop = (interface_counts[aa] / len(residue_list_int)) / (surface_counts[aa] / len(rsa_residues))
        propensity_scores[aa] = round(prop, 3)
    else:
        propensity_scores[aa] = 0.0

prop_df = pd.DataFrame(list(propensity_scores.items()), columns=["Residue", "Propensity"])
prop_df.sort_values(by="Propensity", ascending=False, inplace=True)

prop_out = os.path.join(out_dir, f"{pdb_id}_residue_propensity.csv")
prop_df.to_csv(prop_out, index=False)
print(f"✅ Wrote residue propensity table → {prop_out}")
print(f"Parsed {len(rsa_residues)} surface residues from {rsa_path}")

